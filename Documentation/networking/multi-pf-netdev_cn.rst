SPDX 许可证标识符: GPL-2.0
.. include:: <isonum.txt>

===============
多 PF 网络设备
===============

目录
========

- `背景`_
- `概述`_
- `mlx5 实现`_
- `通道分配`_
- `可观测性`_
- `流量导向`_
- `互斥特性`_

背景
======

多 PF 网卡技术使一个多插槽服务器内的多个 CPU 能够通过各自专用的 PCIe 接口直接连接到网络。这可以通过一个连接线束将 PCIe 通道分成两个部分，或者将一个 PCIe 插槽分叉为一个单一卡来实现。这样消除了网络流量在插槽之间的内部总线上传输，显著减少了开销和延迟，同时降低了 CPU 利用率并提高了网络吞吐量。

概述
======

该功能支持在一个多 PF 环境下，将同一端口的多个 PF 结合到一个网卡实例中。它是在网卡层实现的。较低层次的实例如 PCI 功能、sysfs 入口和 devlink 保持分离。
通过不同 NUMA 插槽上属于不同设备的流量传递可以节省跨 NUMA 的流量，并允许运行在同一网卡的不同 NUMA 上的应用程序仍能感受到与设备的接近性，并实现性能提升。

mlx5 实现
============

在 mlx5 中，通过将具有相同 NIC 并启用了 socket-direct 属性的 PF 组合在一起实现多 PF 或 Socket-direct。当所有 PF 均被探测后，我们创建一个单一的网卡来表示它们。对称地，在任何一个 PF 被移除时销毁网卡。
网卡的网络通道在所有设备间进行分配，正确的配置会在处理特定应用/CPU 时利用正确的邻近 NUMA 节点。
我们选择一个 PF 作为主设备（领导者），并赋予其特殊角色。其他设备（从属设备）在网络芯片级别上断开连接（设置为静默模式）。在静默模式下，没有南北方向的流量直接通过从属 PF 流动。它需要领导者 PF（东西方向的流量）的帮助才能正常工作。所有的接收/发送流量都通过主设备转发到/来自从属设备。
目前，我们将支持限制在 PF 上，并且最多支持两个 PF（插槽）。

通道分配
============

我们将在不同的 PF 之间分配通道以实现在多个 NUMA 节点上的本地 NUMA 节点性能。
每个组合通道针对一个具体的 PF 工作，并在其上创建所有数据路径队列。我们将通道以循环轮询策略分配给 PF。

::

        例如：2 个 PF 和 5 个通道：
        +--------+--------+
        | 通道索引 | PF 索引 |
        +--------+--------+
        |    0   |    0   |
        |    1   |    1   |
        |    2   |    0   |
        |    3   |    1   |
        |    4   |    0   |
        +--------+--------+

我们选择循环轮询的原因是，它较少受通道数量变化的影响。无论用户配置了多少个通道，通道索引和 PF 之间的映射都是固定的。
### 通道统计

由于通道的统计信息在通道关闭后仍然保持不变，每次更改映射会使累积的统计数据不能准确反映通道的历史。

这是通过在每个通道中使用正确的核心设备实例（mdev）来实现的，而不是所有通道都使用同一个 `priv->mdev` 实例。

### 可观测性

PF、IRQ、NAPI 和队列之间的关系可以通过 netlink 规格进行观察：

```sh
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

这里可以清楚地观察到我们的通道分配策略：

```sh
$ ls /proc/irq/{36,39,40,41,42}/mlx5* -d -1
/proc/irq/36/mlx5_comp1@pci:0000:08:00.0
/proc/irq/39/mlx5_comp1@pci:0000:09:00.0
/proc/irq/40/mlx5_comp2@pci:0000:08:00.0
/proc/irq/41/mlx5_comp2@pci:0000:09:00.0
/proc/irq/42/mlx5_comp3@pci:0000:08:00.0
```

### 转发

次级 PF 设置为“静默”模式，意味着它们与网络断开连接。在接收方向上，转发表属于主 PF，并且它的作用是通过跨 vhca 转发能力将传入流量分配给其他 PF。仍然保留一个默认的 RSS 表，该表能够指向不同 PF 的接收队列。在发送方向上，主 PF 创建一个新的发送流表，次级 PF 会引用它以便通过该表向外发送数据。

此外，我们设置了默认的 XPS 配置，根据 CPU 选择属于同一节点上 PF 的 SQ。

XPS 默认配置示例：

```
NUMA 节点:           2
NUMA 节点0 的 CPU:    0-11
NUMA 节点1 的 CPU:    12-23

PF0 在节点0 上，PF1 在节点1 上
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
```

### 互斥特性

多 PF 环境的本质是不同的通道与不同的 PF 工作，这与在某个 PF 中维护状态的状态化特性相冲突。

例如，在 TLS 设备卸载功能中，为每个连接创建特殊上下文对象并维护在 PF 中。在不同的 RQ/SQ 之间切换会破坏该功能。因此，我们现在禁用这种组合。
