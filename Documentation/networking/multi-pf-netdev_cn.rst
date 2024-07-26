### SPDX 许可证标识符: GPL-2.0
### 包含: <isonum.txt>

#### 多PF网络设备

##### 目录

- [背景](#背景)
- [概述](#概述)
- [mlx5实现](#mlx5实现)
- [通道分配](#通道分配)
- [可观测性](#可观测性)
- [转向](#转向)
- [互斥特性](#互斥特性)

### 背景

多PF NIC技术使一个多插槽服务器内的多个CPU能够通过各自的专用PCIe接口直接连接到网络。这可以通过将PCIe通道在两个卡之间分割的连接架或通过为单个卡分叉一个PCIe插槽来实现。这消除了网络流量穿越内部总线的情况，显著降低了开销和延迟，同时减少了CPU使用率并提高了网络吞吐量。

### 概述

该特性支持在一个多PF环境下将同一端口的多个PF合并到一个netdev实例下。它在netdev层实现。较低层级的实例，如pci func、sysfs入口和devlink保持分离。
通过不同的设备传递属于不同NUMA节点的流量可以节省跨NUMA节点的通信，并允许来自不同NUMA节点的应用程序在同一netdev上运行时仍能感受到接近设备的感觉，并实现更好的性能。

### mlx5实现

在mlx5中，多PF或Socket-direct是通过将属于同一NIC且启用了socket-direct特性的PF组合在一起实现的。一旦所有PF被探测到，我们将创建一个单一的netdev来代表所有的PF。同样地，当任何PF被移除时，我们销毁该netdev。
netdev的网络通道在所有设备之间分配，适当的配置会在处理特定应用/CPU时利用正确的接近的NUMA节点。
我们选择一个PF作为主设备（领导者），它扮演特殊角色。其他设备（次级）在网络芯片级别断开与网络的连接（设置为静默模式）。在静默模式下，没有直接通过次级PF的南北向流量流动。它需要主PF的帮助（东西向流量）才能正常工作。所有Rx/Tx流量都通过主设备从/到次级设备进行引导。
目前，我们仅限于支持PF，并且最多支持两个PF（插槽）。

### 通道分配

我们在不同的PF之间分配通道以实现在多个NUMA节点上的本地NUMA节点性能。
每个组合通道针对一个特定的PF工作，在其上创建所有数据路径队列。我们采用轮询策略分配通道。

```
例如：2个PF和5个通道：
+---------+---------+
| 通道索引 | PF索引  |
+---------+---------+
|    0    |    0    |
|    1    |    1    |
|    2    |    0    |
|    3    |    1    |
|    4    |    0    |
+---------+---------+
```

我们倾向于使用轮询的原因是，它较少受到通道数量变化的影响。无论用户配置多少个通道，通道索引与PF之间的映射都是固定的。
由于通道统计信息在通道关闭后仍然保持不变，每次更改映射会使累积的统计信息变得不能准确代表该通道的历史。
这是通过在每个通道中使用正确的核心设备实例（mdev）实现的，而不是所有通道都使用“priv->mdev”下的同一个实例。
可观测性
=============
PF、IRQ、NAPI和队列之间的关系可以通过netlink规范进行观察：

  ```bash
  $ ./tools/net/ynl/cli.py --spec Documentation/netlink/specs/netdev.yaml --dump queue-get --json='{"ifindex": 13}'
  [{'id': 0, 'ifindex': 13, 'napi-id': 539, 'type': 'rx'},
   {'id': 1, 'ifindex': 13, 'napi-id': 540, 'type': 'rx'},
   {'id': 2, 'ifindex': 13, 'napi-id': 541, 'type': 'rx'},
   {'id': 3, 'ifindex': 13, 'napi-id': 542, 'type': 'rx'},
   {'id': 4, 'ifindex': 13, 'napi-id': 543, 'type': 'rx'},
   {'id': 0, 'ifindex': 13, 'napi-id': 539, 'type': 'tx'},
   {'id': 1, 'ifindex': 13, 'napi-id': 540, 'type': 'tx'},
   {'id': 2, 'ifindex': 13, 'napi-id': 541, 'type': 'tx'},
   {'id': 3, 'ifindex': 13, 'napi-id': 542, 'type': 'tx'},
   {'id': 4, 'ifindex': 13, 'napi-id': 543, 'type': 'tx'}]
  
  $ ./tools/net/ynl/cli.py --spec Documentation/netlink/specs/netdev.yaml --dump napi-get --json='{"ifindex": 13}'
  [{'id': 543, 'ifindex': 13, 'irq': 42},
   {'id': 542, 'ifindex': 13, 'irq': 41},
   {'id': 541, 'ifindex': 13, 'irq': 40},
   {'id': 540, 'ifindex': 13, 'irq': 39},
   {'id': 539, 'ifindex': 13, 'irq': 36}]
  ```

这里可以清楚地看到我们的通道分配策略：

  ```bash
  $ ls /proc/irq/{36,39,40,41,42}/mlx5* -d -1
  /proc/irq/36/mlx5_comp1@pci:0000:08:00.0
  /proc/irq/39/mlx5_comp1@pci:0000:09:00.0
  /proc/irq/40/mlx5_comp2@pci:0000:08:00.0
  /proc/irq/41/mlx5_comp2@pci:0000:09:00.0
  /proc/irq/42/mlx5_comp3@pci:0000:08:00.0
  ```

引导
========
次级PF被设置为“静默”模式，这意味着它们与网络断开连接。
在接收端，引导表仅属于主PF，并且其作用是通过跨vhca引导能力将传入流量分配给其他PF。同时保持一个默认的RSS表，该表能够指向不同PF的接收队列。
在发送端，主PF创建一个新的发送流表，次级PF对此表进行别名处理，以便它们可以通过此表向网络发送数据。
此外，我们设置了默认的XPS配置，根据CPU选择属于同一节点上的PF的SQ。
XPS默认配置示例：

NUMA节点: 2
NUMA节点0的CPU: 0-11
NUMA节点1的CPU: 12-23

PF0位于节点0，PF1位于节点1
- /sys/class/net/eth2/queues/tx-0/xps_cpus:000001
- /sys/class/net/eth2/queues/tx-1/xps_cpus:001000
- /sys/class/net/eth2/queues/tx-2/xps_cpus:000002
- /sys/class/net/eth2/queues/tx-3/xps_cpus:002000
- /sys/class/net/eth2/queues/tx-4/xps_cpus:000004
- /sys/class/net/eth2/queues/tx-5/xps_cpus:004000
- /sys/class/net/eth2/queues/tx-6/xps_cpus:000008
- /sys/class/net/eth2/queues/tx-7/xps_cpus:008000
- /sys/class/net/eth2/queues/tx-8/xps_cpus:000010
- /sys/class/net/eth2/queues/tx-9/xps_cpus:010000
- /sys/class/net/eth2/queues/tx-10/xps_cpus:000020
- /sys/class/net/eth2/queues/tx-11/xps_cpus:020000
- /sys/class/net/eth2/queues/tx-12/xps_cpus:000040
- /sys/class/net/eth2/queues/tx-13/xps_cpus:040000
- /sys/class/net/eth2/queues/tx-14/xps_cpus:000080
- /sys/class/net/eth2/queues/tx-15/xps_cpus:080000
- /sys/class/net/eth2/queues/tx-16/xps_cpus:000100
- /sys/class/net/eth2/queues/tx-17/xps_cpus:100000
- /sys/class/net/eth2/queues/tx-18/xps_cpus:000200
- /sys/class/net/eth2/queues/tx-19/xps_cpus:200000
- /sys/class/net/eth2/queues/tx-20/xps_cpus:000400
- /sys/class/net/eth2/queues/tx-21/xps_cpus:400000
- /sys/class/net/eth2/queues/tx-22/xps_cpus:000800
- /sys/class/net/eth2/queues/tx-23/xps_cpus:800000

互斥特性
===========================

多PF环境的本质在于不同的通道与不同的PF协同工作，这与需要在一个PF中维护状态的状态化特性相冲突。
例如，在TLS卸载功能中，为每个连接创建特殊的上下文对象并由PF维护。在不同的RQ/SQ间切换会破坏这个特性。因此，我们暂时禁用这种组合。
