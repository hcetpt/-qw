SPDX 许可证标识符: GPL-2.0

=====================================
异步传输/转换 API
=====================================

.. 目录

  1. 引言

  2. 演变历史

  3. 使用方法
  3.1 API 的一般格式
  3.2 支持的操作
  3.3 描述符管理
  3.4 操作何时执行？
  3.5 操作何时完成？
  3.6 约束条件
  3.7 示例

  4. DMAENGINE 驱动开发者注意事项
  4.1 符合性要点
  4.2 "我的应用程序需要对硬件通道的独占控制"

  5. 来源

1. 引言
===============

异步传输（async_tx）API 提供了描述一系列异步批量内存传输/转换的方法，并支持跨事务依赖。它作为一个 dmaengine 客户端实现，以平滑处理不同硬件卸载引擎实现的细节。编写给该 API 的代码可以优化异步操作，而 API 将把操作链适配到可用的卸载资源。

2. 演变历史
===========

该 API 最初是为了使用 Intel(R) Xscale 系列 I/O 处理器中的卸载引擎来卸载 md-raid5 驱动程序中的内存复制和异或校验计算设计的。它还基于为使用 Intel(R) I/OAT 引擎在网络堆栈中卸载内存复制而开发的“dmaengine”层。以下设计特性因此浮现：

1. 隐式同步路径：API 用户无需知道他们正在运行的平台是否具有卸载能力。当有引擎可用时，操作将被卸载，否则将在软件中执行。
2. 跨通道依赖链：API 允许提交一系列相互依赖的操作，例如 raid5 中的 xor->copy->xor。API 自动处理从一个操作到另一个操作的过渡所隐含的硬件通道切换情况。
3. 扩展 dmaengine 以支持多个客户端和除了 'memcpy' 之外的操作类型。

3. 使用方法
========

3.1 API 的一般格式
-------------------

::

  struct dma_async_tx_descriptor *
  async_<operation>(<特定于操作的参数>, struct async_submit_ctl *submit)

3.2 支持的操作
------------------------

========  ====================================================================
memcpy    在源缓冲区和目标缓冲区之间进行内存复制
memset    用字节值填充目标缓冲区
xor       对一系列源缓冲区进行异或运算，并将结果写入目标缓冲区
xor_val   对一系列源缓冲区进行异或运算，并设置标志位判断结果是否为零。实现尝试防止内存写入
pq        从一系列源缓冲区生成 p+q (raid6 综合症)
pq_val    验证 p 和/或 q 缓冲区是否与给定的一系列源同步
datap     (raid6_datap_recov) 从给定的源恢复 raid6 数据块和 p 块
2data     (raid6_2data_recov) 从给定的源恢复 2 个 raid6 数据块
========  ====================================================================

3.3 描述符管理
-------------------------

当操作已被排队以异步执行时，返回值非 NULL 并指向一个“描述符”。描述符是循环利用的资源，由卸载引擎驱动程序控制，在操作完成后重复使用。当应用程序需要提交一系列操作时，必须保证在提交依赖关系之前不会自动回收描述符。这意味着所有描述符都必须在允许卸载引擎驱动程序回收（或释放）描述符之前被应用程序确认。可以通过以下方法之一确认描述符：

1. 如果没有子操作要提交，则设置 ASYNC_TX_ACK 标志。
2. 提交未确认的描述符作为另一个 async_tx 调用的依赖项会隐式地设置已确认状态。
3. 调用 async_tx_ack() 函数确认描述符。
3.4 操作何时执行？
------------------------------------

在从 async_<operation> 调用返回后，操作不会立即发出。卸载引擎驱动程序通过批处理操作来提高性能，减少管理通道所需的 MMIO 周期数。一旦达到特定于驱动程序的阈值，驱动程序会自动发出待处理的操作。应用程序可以通过调用 async_tx_issue_pending_all() 来强制触发这一事件。这适用于所有通道，因为应用程序不知道通道与操作之间的映射。
3.5 操作何时完成？
-------------------------------------

应用程序有两种方法来了解操作的完成情况：
1. 调用 dma_wait_for_async_tx()。此调用会使 CPU 旋转等待，直到轮询到操作完成。它处理依赖关系链并触发待处理的操作。
2. 指定完成回调。如果卸载引擎驱动程序支持中断，则回调例程会在任务上下文中运行；如果操作是在软件中同步执行的，则在应用程序上下文中调用。可以在调用 async_<operation> 时设置回调，或者当应用程序需要提交未知长度的操作链时，可以使用 async_trigger_callback() 函数在链的末尾设置完成中断/回调。
3.6 约束条件
---------------

1. 不允许在 IRQ 上下文中调用 async_<operation>。其他上下文是可以的，只要不违反第 2 项约束。
### 2. 回调完成例程不能提交新的操作。这会导致同步情况下出现递归，在异步情况下会两次获取spin_lock。

3.7 示例
--------

执行一个xor->复制->xor的操作，其中每个操作都依赖于前一个操作的结果：

```c
#include <linux/async_tx.h>

static void callback(void *param)
{
	complete(param);
}

#define NDISKS  2

static void run_xor_copy_xor(struct page **xor_srcs,
							 struct page *xor_dest,
							 size_t xor_len,
							 struct page *copy_src,
							 struct page *copy_dest,
							 size_t copy_len)
{
	struct dma_async_tx_descriptor *tx;
	struct async_submit_ctl submit;
	addr_conv_t addr_conv[NDISKS];
	struct completion cmp;

	init_async_submit(&submit, ASYNC_TX_XOR_DROP_DST, NULL, NULL, NULL,
						  addr_conv);
	tx = async_xor(xor_dest, xor_srcs, 0, NDISKS, xor_len, &submit);

	submit.depend_tx = tx;
	tx = async_memcpy(copy_dest, copy_src, 0, 0, copy_len, &submit);

	init_completion(&cmp);
	init_async_submit(&submit, ASYNC_TX_XOR_DROP_DST | ASYNC_TX_ACK, tx,
						  callback, &cmp, addr_conv);
	tx = async_xor(xor_dest, xor_srcs, 0, NDISKS, xor_len, &submit);

	async_tx_issue_pending_all();

	wait_for_completion(&cmp);
}
```

有关标志的更多信息，请参阅`include/linux/async_tx.h`。在`drivers/md/raid5.c`中可以找到更多实现示例，如`ops_run_*`和`ops_complete_*`函数。

### 4. 驱动程序开发说明

#### 4.1 符合性要求

为了适应使用async_tx API的应用程序所做的假设，DMA引擎驱动程序需要满足一些符合性要求：

1. 完成回调预期发生在tasklet上下文中。
2. `dma_async_tx_descriptor`字段永远不会在IRQ上下文中被操纵。
3. 在描述符清理路径中使用`async_tx_run_dependencies()`来处理依赖操作的提交。

#### 4.2 “我的应用程序需要对硬件通道的独占控制”

这种需求主要来源于DMA引擎驱动程序用于支持设备到内存操作的情况。出于许多平台特定的原因，进行这些操作的通道不能共享。为此提供了`dma_request_channel()`接口：
```c
struct dma_chan *dma_request_channel(dma_cap_mask_t mask,
									 dma_filter_fn filter_fn,
									 void *filter_param);
```
其中`dma_filter_fn`定义为：
```c
typedef bool (*dma_filter_fn)(struct dma_chan *chan, void *filter_param);
```
当可选的`filter_fn`参数设置为NULL时，`dma_request_channel`仅返回满足能力掩码的第一个通道。否则，当掩码参数不足以指定必要的通道时，可以使用`filter_fn`例程来处置系统中的可用通道。对于系统中的每个空闲通道，都会调用一次`filter_fn`。看到合适的通道时，`filter_fn`返回`DMA_ACK`，标记该通道作为`dma_request_channel`的返回值。通过此接口分配的通道对调用者是独占的，直到调用`dma_release_channel()`。

`DMA_PRIVATE`能力标志用于标记不应由通用分配器使用的DMA设备。如果已知一个通道将始终为私有，则可以在初始化时设置该标志。或者，当`dma_request_channel()`找到一个未使用的“公共”通道时，会设置该标志。

在实现驱动程序和消费者时需要注意以下几点：

1. 一旦通道被私有分配后，即使调用了`dma_release_channel()`，它也不会再被通用分配器考虑。
2. 由于能力是在设备级别指定的，具有多个通道的DMA设备要么所有通道都是公共的，要么所有通道都是私有的。

### 5. 源代码

- `include/linux/dmaengine.h`: DMA驱动程序和API用户的主头文件。
- `drivers/dma/dmaengine.c`: 卸载引擎通道管理例程。
- `drivers/dma/`: 卸载引擎驱动程序的位置。
- `include/linux/async_tx.h`: async_tx API的主头文件。
- `crypto/async_tx/async_tx.c`: async_tx与dmaengine的接口及常用代码。
- `crypto/async_tx/async_memcpy.c`: 复制卸载。
- `crypto/async_tx/async_xor.c`: xor和xor零和卸载。
