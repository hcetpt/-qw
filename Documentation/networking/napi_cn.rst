SPDX 许可证标识符: (GPL-2.0-only 或 BSD-2-Clause)

.. _napi:

====
NAPI
====

NAPI 是 Linux 网络堆栈中使用的事件处理机制。
NAPI 这个名字现在已经不再代表任何特定含义 [#]_ 。
在基本操作中，设备通过中断来通知主机有关新事件的信息。
然后，主机会调度一个 NAPI 实例来处理这些事件。
设备也可以通过 NAPI 检测事件而无需首先接收中断（:ref:`忙轮询<poll>`）。
NAPI 处理通常发生在软件中断上下文中，
但也有选项可以使用 :ref:`独立的内核线程<threaded>` 来进行 NAPI 处理。
总的来说，NAPI 抽象了驱动程序中的事件（数据包接收和发送）处理的上下文和配置。

驱动程序 API
=============

NAPI 的两个最重要的元素是 `struct napi_struct` 和与之关联的轮询方法。
`struct napi_struct` 存储了 NAPI 实例的状态，
而该方法则是驱动程序特有的事件处理器。
该方法通常会释放已传输的 Tx 数据包并处理新接收的数据包。

.. _drv_ctrl:

控制 API
---------

`netif_napi_add()` 和 `netif_napi_del()` 用于向系统添加/移除 NAPI 实例。
实例与作为参数传递的 netdevice 关联（并在 netdevice 注销时自动删除）。
实例是在禁用状态下添加的。
`napi_enable()` 和 `napi_disable()` 用于管理禁用状态。
一个被禁用的 NAPI 无法被调度，且其轮询方法保证不会被调用。`napi_disable()` 等待 NAPI 实例的所有权被释放。

控制 API 并不是幂等的。在并发使用数据路径 API 的情况下，控制 API 调用是安全的，但不正确的控制 API 序列调用可能会导致崩溃、死锁或竞态条件。例如，连续多次调用 `napi_disable()` 将会导致死锁。

### 数据路径 API

`napi_schedule()` 是调度 NAPI 轮询的基本方法。
驱动程序应在它们的中断处理程序中调用此函数（更多信息参见 :ref:`drv_sched`）。成功调用 `napi_schedule()` 将获取 NAPI 实例的所有权。

稍后，在 NAPI 被调度之后，将调用驱动程序的轮询方法来处理事件/数据包。该方法接受一个“预算”参数——驱动程序可以处理任意数量的发送数据包，但只应处理不超过“预算”数量的接收数据包。通常，接收处理的成本更高。

换句话说，对于接收处理，“预算”参数限制了驱动程序在单次轮询中可以处理的数据包数量。当“预算”为 0 时，不能使用任何特定于接收的 API，如页池或 XDP。

无论“预算”如何，都应该进行 skb 发送处理，但如果参数为 0，则驱动程序不能调用任何 XDP（或页池）API。

**警告：**

如果核心试图仅处理 skb 发送完成而不处理接收或 XDP 数据包，则“预算”参数可能为 0。

轮询方法返回已完成的工作量。如果驱动程序仍有待处理的工作（例如，“预算”已耗尽），则轮询方法应返回确切的“预算”。在这种情况下，NAPI 实例将再次被服务/轮询（无需重新调度）。

如果事件处理已完成（所有待处理的数据包已被处理），轮询方法应在返回前调用 `napi_complete_done()`。`napi_complete_done()` 会释放实例的所有权。
警告：

必须谨慎处理完成所有事件并恰好使用 `budget` 的情况。无法向堆栈报告这种（罕见）条件，因此驱动程序要么不调用 napi_complete_done() 并等待再次被调用，要么返回 `budget - 1`。如果 `budget` 为 0，则不应调用 napi_complete_done()。
调用序列
--------

驱动程序不应假设确切的调用顺序。即使驱动程序没有安排实例的调度，也可能调用轮询方法（除非实例被禁用）。同样地，即使 napi_schedule() 成功，也不能保证会调用轮询方法（例如，如果实例被禁用）。如在 :ref:`drv_ctrl` 部分中所述 - napi_disable() 和随后对轮询方法的调用仅等待实例的所有权释放，而不是等待轮询方法退出。这意味着驱动程序在调用 napi_complete_done() 后应避免访问任何数据结构。

.. _drv_sched:

调度和中断屏蔽
----------------

驱动程序应在调度 NAPI 实例后保持中断被屏蔽 —— 直到 NAPI 轮询完成之前，任何进一步的中断都是不必要的。需要显式屏蔽中断的驱动程序（而非通过设备自动屏蔽）应该使用 napi_schedule_prep() 和 __napi_schedule() 调用：

.. code-block:: c

  if (napi_schedule_prep(&v->napi)) {
      mydrv_mask_rxtx_irq(v->idx);
      /* 在屏蔽后进行调度以避免竞态 */
      __napi_schedule(&v->napi);
  }

只有在成功调用 napi_complete_done() 后才能解除中断屏蔽：

.. code-block:: c

  if (budget && napi_complete_done(&v->napi, work_done)) {
    mydrv_unmask_rxtx_irq(v->idx);
    return min(work_done, budget - 1);
  }

napi_schedule_irqoff() 是 napi_schedule() 的一个变体，它利用了在 IRQ 上下文被调用时提供的保证（无需屏蔽中断）。需要注意的是，PREEMPT_RT 强制所有中断都通过线程处理，因此可能需要将中断标记为 `IRQF_NO_THREAD` 以避免在实时内核配置上的问题。
实例与队列映射
----------------

现代设备每个接口通常有多个 NAPI 实例（struct napi_struct）。对于实例如何映射到队列和中断没有严格的要求。NAPI 主要是轮询/处理的抽象层，并没有具体的面向用户的语义。尽管如此，大多数网络设备最终以非常类似的方式使用 NAPI。

NAPI 实例最常与中断和队列对（队列对是指单个接收队列和单个发送队列的组合）以 1:1:1 的比例相对应。

在较少见的情况下，一个 NAPI 实例可能会用于多个队列，或者在单个核心上由不同的 NAPI 实例分别服务接收和发送队列。然而，无论队列分配如何，通常仍然存在 NAPI 实例和中断之间的 1:1 映射。

值得注意的是，ethtool API 使用“通道”术语，其中每个通道可以是 `rx`、`tx` 或 `combined`。通道的确切定义并不明确；推荐的解释是将通道理解为服务特定类型队列的 IRQ/NAPI。例如，1 个 `rx`、1 个 `tx` 和 1 个 `combined` 通道的配置预计会使用 3 个中断，2 个接收队列和 2 个发送队列。
用户 API
========

用户与 NAPI 的交互依赖于 NAPI 实例 ID。实例 ID 仅通过套接字选项 ``SO_INCOMING_NAPI_ID`` 对用户可见。
目前无法查询给定设备使用的 ID。

软件中断合并
-----------------------

NAPI 默认不执行任何明确的事件合并。
在大多数情况下，由于设备完成的中断合并，批量处理得以实现。
有些情况下，软件合并是有帮助的。
NAPI 可以配置为，在所有数据包处理完毕后启动重新轮询定时器而不是解除硬件中断屏蔽。
网络设备的 ``gro_flush_timeout`` sysfs 配置被重用来控制定时器的延迟，
而 ``napi_defer_hard_irqs`` 控制连续空轮询的次数，之后 NAPI 放弃并回到使用硬件中断的状态。

轮询
------------

轮询允许用户进程在设备中断触发之前检查传入的数据包。如同所有轮询一样，它用 CPU 周期换取更低的延迟（NAPI 轮询的实际生产用途尚不为人所熟知）。
可以通过设置选定套接字上的 ``SO_BUSY_POLL`` 或使用全局的 ``net.core.busy_poll`` 和 ``net.core.busy_read`` sysctls 来启用轮询。还存在用于 NAPI 轮询的 io_uring API。

中断缓解
---------------

虽然轮询主要用于低延迟应用，但类似的机制也可用于中断缓解。
极高请求每秒的应用（尤其是路由/转发应用，特别是使用 AF_XDP 套接字的应用）可能希望在其完成处理一个请求或一批数据包前不被打断。
此类应用程序可以向内核保证，它们将定期执行忙轮询操作，并且驱动程序应始终保持设备中断被屏蔽。通过使用 `SO_PREFER_BUSY_POLL` 套接字选项启用该模式。为了避免系统行为异常，如果在没有任何忙轮询调用的情况下 `gro_flush_timeout` 时间过去，该保证将被撤销。
对于忙轮询的 NAPI 预算低于默认值（考虑到正常忙轮询的低延迟意图，这是合理的）。然而，在中断缓解的情况下并非如此，因此可以通过 `SO_BUSY_POLL_BUDGET` 套接字选项调整预算。

-threaded-:

线程化 NAPI
--------------

线程化 NAPI 是一种工作模式，它使用专用的内核线程而不是软件中断上下文来处理 NAPI。
配置是按网络设备进行的，并会影响该设备的所有 NAPI 实例。每个 NAPI 实例将启动一个单独的线程（称为 `napi/${ifc-name}-${napi-id}`）。
建议将每个内核线程绑定到单个 CPU 上，即服务于中断的 CPU。请注意，IRQ 和 NAPI 实例之间的映射可能并不简单（并且依赖于驱动程序）。NAPI 实例 ID 将按照与内核线程进程 ID 相反的顺序分配。
线程化 NAPI 通过向网络设备的 sysfs 目录中的 "threaded" 文件写入 0/1 来控制。

.. _ 脚注

.. [#] NAPI 最初在 2.4 版本的 Linux 中被称为 New API。
