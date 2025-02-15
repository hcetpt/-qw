... SPDX-许可证标识符: GPL-2.0

=========================
基于TC队列的过滤机制
=========================

TC可用于将流量导向一系列队列或单个队列，无论是在发送还是接收端。
在发送端：

1) 使用skbedit优先级操作的TC过滤器可实现将流量导向一系列队列。当使用mqprio配置队列集时，优先级映射到一个流量类别（即一系列队列）。
2) 使用skbedit queue_mapping $tx_qid动作的TC过滤器可将流量导向发送队列。对于发送队列而言，skbedit queue_mapping动作仅在软件中执行，无法卸载。

同样，在接收端，支持以下两种过滤器来选择一系列队列或单个队列：

1) 使用'hw_tc'选项的TC flower过滤器可将传入流量导向一系列队列。
hw_tc $TCID - 指定用于传递匹配数据包的硬件流量类。TCID的范围是0至15。
2) 使用skbedit queue_mapping $rx_qid动作的TC过滤器可选择接收队列。对于接收队列而言，skbedit queue_mapping动作仅在硬件中支持。多个过滤器可能在硬件中竞争队列选择。在这种情况下，硬件管道根据优先级解决冲突。在Intel E810设备上，将流量导向队列的TC过滤器比分配队列的流导向过滤器具有更高的优先级。哈希过滤器具有最低的优先级。
