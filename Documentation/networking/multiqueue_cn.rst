SPDX 许可声明标识符：GPL-2.0

===========================================
多队列网络设备支持的使用说明
===========================================

第 1 节：实现多队列支持的基本驱动要求
=======================================================================

介绍：内核对多队列设备的支持
---------------------------------------------------------

内核对多队列设备的支持始终存在。
基本驱动程序需要使用新的 alloc_etherdev_mq() 或 alloc_netdev_mq() 函数为设备分配子队列。底层内核 API 将负责子队列内存的分配和释放，以及配置 netdev 中队列在内存中的位置。
基本驱动程序还需要像管理全局 netdev->queue_lock 那样管理队列。因此，在设备仍处于运行状态时，基本驱动程序应使用 netif_{start|stop|wake}_subqueue() 函数来管理每个队列。当设备上线或完全关闭（例如 unregister_netdev() 等）时，仍然使用 netdev->queue_lock。

第 2 节：多队列设备的 qdisc 支持
===============================================

目前有两个 qdisc 为多队列设备进行了优化。第一个是默认的 pfifo_fast qdisc。此 qdisc 支持每个硬件队列一个 qdisc。
一个新的循环调度器 sch_multiq 也支持多个硬件队列。qdisc 负责分类 skb，并根据 skb->queue_mapping 的值将 skb 分配到相应的队列。基本驱动程序可以使用该字段确定要将 skb 发送到哪个队列。
sch_multiq 已经添加以避免头阻塞。它将循环遍历各队列，并在出队前验证与队列关联的硬件队列是否未停止。
在加载 qdisc 时，队列数量基于硬件上的队列数量。一旦建立了关联，任何设置了 skb->queue_mapping 的 skb 都会被排队到与硬件队列相关的队列中。

第 3 节：使用 MULTIQ 对多队列设备进行简要说明
==========================================================

用户空间命令 'tc' 是 iproute2 包的一部分，用于配置 qdisc。要将 MULTIQ qdisc 添加到您的网络设备，假设设备名为 eth0，请运行以下命令：

    # tc qdisc add dev eth0 root handle 1: multiq

qdisc 将分配的数量等于设备报告的队列数量，并使 qdisc 上线。假设 eth0 有 4 个发送队列，则队列映射如下所示：

    队列 0 => 队列 0
    队列 1 => 队列 1
    队列 2 => 队列 2
    队列 3 => 队列 3

流量将根据 simple_tx_hash 函数或根据定义的 netdev->select_queue() 函数通过各个队列流动。
tc 过滤器的行为保持不变。然而，新增了一个 tc 动作 skbedit。假设您希望将所有发往特定主机（例如 192.168.0.3）的流量通过特定队列发送，您可以使用此动作并设置过滤器，如下所示：

    tc filter add dev eth0 parent 1: protocol ip prio 1 u32 \
	    match ip dst 192.168.0.3 \
	    action skbedit queue_mapping 3

作者：Alexander Duyck <alexander.h.duyck@intel.com>
原始作者：Peter P. Waskiewicz Jr. <peter.p.waskiewicz.jr@intel.com>
