### DMA引擎API指南

#### Vinod Koul <vinod.dot.koul@intel.com>

> **注：** 关于异步传输中DMA引擎的使用，请参见：
> `Documentation/crypto/async-tx-api.rst`

以下是为设备驱动程序编写者提供的关于如何使用DMA引擎的Slave-DMA API的指南。这仅适用于slave DMA的使用。

#### DMA使用概述

Slave DMA使用包含以下步骤：

- 分配一个DMA slave通道
- 设置slave和控制器特定参数
- 获取交易描述符
- 提交交易
- 发出待处理请求并等待回调通知

这些操作的具体细节如下：

1. **分配一个DMA slave通道**

   在slave DMA上下文中，通道分配略有不同，客户端驱动通常只需要从某个特定的DMA控制器获取通道，在某些情况下甚至需要指定某个具体的通道。为了请求一个通道，使用`dma_request_chan()` API。
   
   **接口：**
   
   ```c
   struct dma_chan *dma_request_chan(struct device *dev, const char *name);
   ```
   
   这将查找并返回与'dev'设备关联的名为`name`的DMA通道。这种关联是通过DT、ACPI或基于板级文件的`dma_slave_map`匹配表完成的。
   通过此接口分配的通道对调用者来说是独占的，直到调用`dma_release_channel()`。

2. **设置slave和控制器特定参数**

   下一步总是向DMA驱动传递一些特定的信息。大多数通用信息，slave DMA可以使用的，都在`struct dma_slave_config`结构体中。这允许客户端指定DMA方向、DMA地址、总线宽度、DMA突发长度等外设相关参数。
   如果某些DMA控制器有更多参数需要发送，则应尝试将其控制器特定结构嵌入到`struct dma_slave_config`中。这样就给客户端提供了更多的灵活性以传递额外的参数，如果需要的话。
   
   **接口：**
   
   ```c
   int dmaengine_slave_config(struct dma_chan *chan,
                               struct dma_slave_config *config)
   ```
   
   请参阅`dmaengine.h`中的`dma_slave_config`结构定义，了解结构成员的详细解释。请注意，`direction`成员将被移除，因为它在prepare调用中已经重复给出了方向。

3. **获取交易描述符**

   对于slave使用情况，DMA引擎支持的slave传输模式包括：

   - `slave_sg`: 从/到外设DMA一个scatter gather缓冲列表
   - `dma_cyclic`: 从/到外设执行循环DMA操作，直到该操作被明确停止
   - `interleaved_dma`: 这对于slave以及M2M客户端都是通用的。对于slave，设备的FIFO地址可能已经被驱动所知。
可以通过为`dma_interleaved_template`成员设置适当的值来表达各种类型的DMA操作。如果通道支持，通过设置DMA_PREP_REPEAT传输标志，也可以实现循环交错的DMA传输。
此传输API返回非空值代表给定交易的“描述符”。
接口如下：

  .. code-block:: c

     struct dma_async_tx_descriptor *dmaengine_prep_slave_sg(
		struct dma_chan *chan, struct scatterlist *sgl,
		unsigned int sg_len, enum dma_data_direction direction,
		unsigned long flags);

     struct dma_async_tx_descriptor *dmaengine_prep_dma_cyclic(
		struct dma_chan *chan, dma_addr_t buf_addr, size_t buf_len,
		size_t period_len, enum dma_data_direction direction);

     struct dma_async_tx_descriptor *dmaengine_prep_interleaved_dma(
		struct dma_chan *chan, struct dma_interleaved_template *xt,
		unsigned long flags);

外设驱动程序在调用`dmaengine_prep_slave_sg()`之前应先将scatterlist映射给DMA操作，并且必须保持scatterlist的映射状态直到DMA操作完成。
scatterlist必须使用DMA结构设备进行映射。
如果需要稍后同步映射，也必须使用DMA结构设备调用dma_sync_*_for_*()函数。
因此，正常的设置应如下所示：

  .. code-block:: c

     struct device *dma_dev = dmaengine_get_dma_device(chan);

     nr_sg = dma_map_sg(dma_dev, sgl, sg_len);
	if (nr_sg == 0)
		/* 错误处理 */

	desc = dmaengine_prep_slave_sg(chan, sgl, nr_sg, direction, flags);

一旦获得描述符，可以添加回调信息并提交该描述符。某些DMA引擎驱动程序可能在成功的准备和提交之间持有自旋锁，因此这两个操作需要紧密配合。
.. note::

     尽管异步传输API规定完成回调例程不能提交任何新操作，但对于slave/cyclic DMA这并不适用。
对于slave DMA，后续交易可能在回调函数被调用前不可用于提交，因此允许slave DMA回调函数准备并提交新的交易。
对于cyclic DMA，回调函数可能希望通过dmaengine_terminate_async()终止DMA。
因此，重要的是DMA引擎驱动程序在调用可能引起死锁的回调函数之前释放任何锁。
请注意，回调函数总是从DMA引擎的任务中被调用，而不会在中断上下文中被调用。
**可选：每个描述符的元数据**

DMA引擎提供了两种支持元数据的方法：
DESC_METADATA_CLIENT

    元数据缓冲区由客户端驱动程序分配/提供，并将其附加到描述符上。
.. code-block:: c

     int dmaengine_desc_attach_metadata(struct dma_async_tx_descriptor *desc,
				   void *data, size_t len);

DESC_METADATA_ENGINE

    元数据缓冲区由DMA驱动程序分配/管理。客户端驱动程序可以请求元数据的指针、最大大小和当前使用大小，并可以直接更新或读取它。
由于DMA驱动程序管理包含元数据的内存区域，客户端必须确保不在其传输完成回调为描述符运行后尝试访问或获取该指针。
如果没有为传输定义完成回调，则在issue_pending之后不得访问元数据。
换句话说：如果目的是在传输完成后读回元数据，则客户端必须使用完成回调。
.. code-block:: c

     void *dmaengine_desc_get_metadata_ptr(struct dma_async_tx_descriptor *desc,
		size_t *payload_len, size_t *max_len);

     int dmaengine_desc_set_metadata_len(struct dma_async_tx_descriptor *desc,
		size_t payload_len);

客户端驱动程序可以通过以下方式查询是否支持给定模式：

.. code-block:: c

     bool dmaengine_is_metadata_mode_supported(struct dma_chan *chan,
		enum dma_desc_metadata_mode mode);

根据使用的模式，客户端驱动程序必须遵循不同的流程。
DESC_METADATA_CLIENT

    - DMA_MEM_TO_DEV / DEV_MEM_TO_MEM:

      1. 准备描述符（dmaengine_prep_*）
         在客户端的缓冲区中构造元数据
      2. 使用dmaengine_desc_attach_metadata()将缓冲区附加到描述符
      3. 提交传输

    - DMA_DEV_TO_MEM:

      1. 准备描述符（dmaengine_prep_*）
      2. 使用dmaengine_desc_attach_metadata()将缓冲区附加到描述符
      3. 提交传输
      4. 当传输完成后，元数据应出现在已附加的缓冲区中

DESC_METADATA_ENGINE

    - DMA_MEM_TO_DEV / DEV_MEM_TO_MEM:

      1. 准备描述符（dmaengine_prep_*）
      2. 使用dmaengine_desc_get_metadata_ptr()获取指向引擎元数据区域的指针
      3. 更新指针处的元数据
      4. 使用dmaengine_desc_set_metadata_len()告诉DMA引擎客户端放置到元数据缓冲区中的数据量
      5. 提交传输

    - DMA_DEV_TO_MEM:

      1. 准备描述符（dmaengine_prep_*）
      2. 提交传输
      3. 在传输完成后，使用dmaengine_desc_get_metadata_ptr()获取指向引擎元数据区域的指针
      4. 从指针处读出元数据

  .. note::

     当使用DESC_METADATA_ENGINE模式时，在传输完成后描述符的元数据区域不再有效（如果使用了完成回调，则在其返回之前有效）。
不允许混合使用DESC_METADATA_CLIENT / DESC_METADATA_ENGINE，客户端驱动程序必须对每个描述符使用其中一种模式。
### 提交事务

一旦描述符已经准备好并且回调信息也已添加，它必须被放置到DMA引擎驱动程序的待处理队列上。

#### 接口：

```c
dma_cookie_t dmaengine_submit(struct dma_async_tx_descriptor *desc);
```

该函数返回一个可用于通过其他未在本文档中涵盖的DMA引擎调用来检查DMA引擎活动进度的标记（cookie）。

`dmaengine_submit()` 并不会启动DMA操作，它只是将其添加到待处理队列。要启动DMA操作，请参阅步骤5中的 `dma_async_issue_pending`。

**注意：**

调用 `dmaengine_submit()` 后，提交的传输描述符 (`struct dma_async_tx_descriptor`) 就属于DMA引擎了。因此，客户端必须认为对该描述符的指针无效。

### 发起待处理的DMA请求并等待回调通知

待处理队列中的事务可以通过调用issue_pending API来激活。如果通道处于空闲状态，则队列中的第一个事务将开始执行，后续事务则排队等待。

每次DMA操作完成后，队列中的下一个事务会被启动，并触发一个tasklet。如果设置了回调，则此tasklet将会调用客户端驱动程序的完成回调例程以进行通知。

#### 接口：

```c
void dma_async_issue_pending(struct dma_chan *chan);
```

### 其他APIs

#### 终止APIs

```c
int dmaengine_terminate_sync(struct dma_chan *chan);
int dmaengine_terminate_async(struct dma_chan *chan);
int dmaengine_terminate_all(struct dma_chan *chan); // 已废弃
```

这些函数会导致DMA通道的所有活动停止，并可能丢弃尚未完全传输的数据。

对于任何未完成的传输，都不会调用回调函数。

有两种变体可用。
1. `dmaengine_terminate_async()` 可能不会等待直到 DMA 完全停止或任何正在运行的完成回调函数结束。但是，可以从原子上下文或从一个完成回调函数中调用 `dmaengine_terminate_async()`。在安全地释放 DMA 传输访问的内存或从完成回调函数访问的资源之前，必须调用 `dmaengine_synchronize()`。
   
   `dmaengine_terminate_sync()` 在返回前会等待传输和任何正在运行的完成回调函数结束。但是，该函数不应从原子上下文或从一个完成回调函数中调用。
   
   `dmaengine_terminate_all()` 已被废弃，不应在新代码中使用。
   
2. 暂停 API
   
   .. code-block:: c
   
      int dmaengine_pause(struct dma_chan *chan)
   
   这将暂停 DMA 通道的活动而不丢失数据。
3. 恢复 API
   
   .. code-block:: c
   
       int dmaengine_resume(struct dma_chan *chan)
   
   恢复先前已暂停的 DMA 通道。恢复当前未处于暂停状态的通道是无效的。
4. 检查事务完成
   
   .. code-block:: c
   
      enum dma_status dma_async_is_tx_complete(struct dma_chan *chan,
		dma_cookie_t cookie, dma_cookie_t *last, dma_cookie_t *used)
   
   此函数可用于检查通道的状态。请参阅 `include/linux/dmaengine.h` 中的文档以获取此 API 的更完整描述。
   
   可以结合使用 `dma_async_is_complete()` 和从 `dmaengine_submit()` 返回的 cookie 来检查特定 DMA 事务是否完成。
   
   .. note::
   
      并非所有 DMA 引擎驱动程序都能为正在运行的 DMA 通道提供可靠的信息。建议 DMA 引擎用户在使用此 API 前暂停或停止（通过 `dmaengine_terminate_all()`）通道。
5. 终止同步 API
   
   .. code-block:: c
   
      void dmaengine_synchronize(struct dma_chan *chan)
   
   同步 DMA 通道的终止到当前上下文。
   
   该函数应在 `dmaengine_terminate_async()` 之后使用，以同步 DMA 通道的终止到当前上下文。该函数会在返回前等待传输和任何正在运行的完成回调函数结束。
如果使用 `dmaengine_terminate_async()` 来停止 DMA 通道，则在安全地释放之前提交的描述符所访问的内存或释放之前提交的描述符的完成回调中访问的任何资源之前，必须调用此函数。

如果在 `dmaengine_terminate_async()` 和此函数之间调用了 `dma_async_issue_pending()`，则此函数的行为是未定义的。
