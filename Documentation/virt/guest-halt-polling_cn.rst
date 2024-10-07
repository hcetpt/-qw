来宾暂停轮询
==================

使用带有 `haltpoll` 管理程序的 `cpuidle_haltpoll` 驱动程序，允许来宾 vCPU 在暂停之前进行一定时间的轮询。这为宿主端轮询带来了以下好处：

1) 在执行轮询时设置 POLL 标志，这使得远程 vCPU 在执行唤醒操作时可以避免发送 IPI（以及处理 IPI 所需的成本）。
2) 可以避免 VM-exit 成本。

来宾端轮询的缺点是即使宿主机上存在其他可运行任务时也会进行轮询。
基本逻辑如下：一个全局值 `guest_halt_poll_ns` 由用户配置，表示允许的最大轮询时间。此值是固定的。
每个 vCPU 都有一个可调整的 `guest_halt_poll_ns`（“每 CPU 的 guest_halt_poll_ns”），该值由算法根据事件进行调整（见下文）。

模块参数
=================

`haltpoll` 管理程序有 5 个可调模块参数：

1) `guest_halt_poll_ns`：
在暂停之前执行轮询的最大时间（纳秒）。
默认值：200000

2) `guest_halt_poll_shrink`：
当唤醒事件发生在全局 `guest_halt_poll_ns` 之后时，用于缩小每 CPU `guest_halt_poll_ns` 的除数因子。
默认值：2

3) `guest_halt_poll_grow`：
当事件发生在每 CPU `guest_halt_poll_ns` 之后但全局 `guest_halt_poll_ns` 之前时，用于增加每 CPU `guest_halt_poll_ns` 的乘数因子。
默认值：2

4) `guest_halt_poll_grow_start`：
在空闲系统中，每 CPU `guest_halt_poll_ns` 最终会达到零。此值设置了增长时的初始每 CPU `guest_halt_poll_ns`。可以通过将此值从 10000 增加来避免初始增长阶段中的错过：
例如：10k、20k、40k……（假设 `guest_halt_poll_grow`=2）。
默认值：50000

5) guest_halt_poll_allow_shrink：

一个布尔参数，允许进行缩减。设置为 N 以避免缩减（每 CPU 的 guest_halt_poll_ns 在达到全局 guest_halt_poll_ns 值后将保持较高）
默认值：Y

这些模块参数可以通过以下 sysfs 文件来设置：

	/sys/module/haltpoll/parameters/

进一步说明
=============

- 设置 guest_halt_poll_ns 参数时应谨慎，因为较大的值可能会导致在一个几乎完全空闲的机器上的 CPU 使用率达到 100%。
