SPDX 许可声明标识符：GPL-2.0 或 Linux-OpenIB
.. include:: <isonum.txt>

=====
Switchdev
=====

:版权所有: |copy| 2023，NVIDIA CORPORATION 及其关联公司。保留所有权利。
.. _mlx5_bridge_offload:

桥接卸载
==========

mlx5 驱动程序在 switchdev 模式下实现了对桥接规则的卸载支持。当 mlx5 switchdev 的表示器连接到桥接时，Linux 桥接 FDB（转发数据库）会自动卸载。
- 更改设备为 switchdev 模式:

    ```
    $ devlink dev eswitch set pci/0000:06:00.0 mode switchdev
    ```

- 将 mlx5 switchdev 表示器 'enp8s0f0' 连接到桥接网络设备 'bridge1':

    ```
    $ ip link set enp8s0f0 master bridge1
    ```

VLAN
----

mlx5 支持以下桥接 VLAN 功能：

- VLAN 过滤（包括每个端口的多个 VLAN）:

    ```
    $ ip link set bridge1 type bridge vlan_filtering 1
    $ bridge vlan add dev enp8s0f0 vid 2-3
    ```

- 在桥接入口时进行 VLAN 推送:

    ```
    $ bridge vlan add dev enp8s0f0 vid 3 pvid
    ```

- 在桥接出口时进行 VLAN 剥离:

    ```
    $ bridge vlan add dev enp8s0f0 vid 3 untagged
    ```

子功能
======

在 E-switch 上生成的子功能仅通过 devlink 设备创建，默认情况下所有子功能辅助设备都是禁用的。
这将允许用户在子功能完全探测之前配置子功能，从而节省时间。
使用示例：

- 创建子功能 (SF):

    ```
    $ devlink port add pci/0000:08:00.0 flavour pcisf pfnum 0 sfnum 11
    $ devlink port function set pci/0000:08:00.0/32768 hw_addr 00:00:00:00:00:11 state active
    ```

- 启用 ETH 辅助设备:

    ```
    $ devlink dev param set auxiliary/mlx5_core.sf.1 name enable_eth value true cmode driverinit
    ```

- 现在，为了完全探测子功能，请使用 devlink 重载命令:

    ```
    $ devlink dev reload auxiliary/mlx5_core.sf.1
    ```

mlx5 支持 ETH、RDMA 和 VDPA (vnet) 辅助设备的 devlink 参数 (参见 :ref:`Documentation/networking/devlink/devlink-params.rst <devlink_params_generic>`).
mlx5 支持使用 devlink 端口接口管理子功能 (参见 :ref:`Documentation/networking/devlink/devlink-port.rst <devlink_port>`).
一个子功能有自己的功能能力和自己的资源。这意味着子功能拥有自己专用的队列（发送队列 txq、接收队列 rxq、完成队列 cq、事件队列 eq）。这些队列既不共享也不从父 PCI 功能中窃取。
当子功能具备 RDMA 能力时，它拥有自己的 QP1（队列对）、GID 表和 RDMA 资源，这些资源既不共享也不从父 PCI 功能中窃取。
子功能在 PCI BAR 空间中有一个专用窗口，该窗口与其它子功能或父 PCI 功能不共享。这确保了子功能的所有设备（如网络设备、RDMA 设备、VDPA 设备等）仅访问分配给它的 PCI BAR 空间。
子功能支持通过 eswitch 表示器来实现 tc 卸载。用户可以配置 eswitch 以便向/从子功能端口发送/接收数据包。
子功能共享 PCI 级别资源，例如 PCI MSI-X 中断请求（IRQ），与其他子功能和/或与其父 PCI 功能共享。
以下是 mlx5 软件、系统和设备视图的一个例子：

       _______
      | 管理  |
      | 用户  |----------
      |_______|         |
          |             |
      ____|____       __|______            _________________
     |         |     |         |          |                 |
     | devlink |     | tc 工具 |          |    用户         |
     | 工具    |     |_________|          | 应用程序    |
     |_________|         |                |_________________|
           |             |                   |          |
           |             |                   |          |         用户空间
 +---------|-------------|-------------------|----------|--------------------+
           |             |           +----------+   +----------+   内核
           |             |           |  网络设备  |   | RDMA 设备 |
           |             |           +----------+   +----------+
   (devlink 端口添加/删除 |              ^               ^
    端口功能设置)   |              |               |
           |             |              +---------------|
      _____|___          |              |        _______|_______
     |         |         |              |       | mlx5 类    |
     | devlink |   +------------+       |       |   驱动程序     |
     | 内核  |   | 代表网络设备 |       |       |(mlx5_core,ib) |
     |_________|   +------------+       |       |_______________|
           |             |              |               ^
   (devlink 操作)         |              |          (加载/卸载)
  _________|________     |              |           ____|________
 | 子功能      |    |     +---------------+   | 子功能 |
 | 管理驱动程序|-----     | 子功能   |---|  主机驱动程序 |
 | (mlx5_core)      |          | 辅助设备 |   | (mlx5_core) |
 |__________________|          +---------------+   |_____________|
           |                                            ^
  (添加/删除子功能, vhca 事件)                             |
           |                                      (添加/删除设备)
      _____|____                                    ____|________
     |          |                                  | 子功能 |
     |  PCI NIC |--- 激活/停用事件--->| 主机驱动程序 |
     |__________|                                  | (mlx5_core) |
                                                   |_____________|

使用 devlink 端口接口创建子功能
- 更改设备为 switchdev 模式:

    $ devlink dev eswitch set pci/0000:06:00.0 mode switchdev

- 添加一个子功能风味的 devlink 端口:

    $ devlink port add pci/0000:06:00.0 flavour pcisf pfnum 0 sfnum 88
    pci/0000:06:00.0/32768: 类型 eth 网络设备 eth6 风味 pcisf 控制器 0 pfnum 0 sfnum 88 外部 false 不可分割 false
      功能:
        hw_addr 00:00:00:00:00:00 状态 inactive 运行状态 detached

- 显示子功能的 devlink 端口:

    $ devlink port show pci/0000:06:00.0/32768
    pci/0000:06:00.0/32768: 类型 eth 网络设备 enp6s0pf0sf88 风味 pcisf pfnum 0 sfnum 88
      功能:
        hw_addr 00:00:00:00:00:00 状态 inactive 运行状态 detached

- 删除已使用的子功能 devlink 端口:

    $ devlink port del pci/0000:06:00.0/32768

功能属性
========

mlx5 驱动程序提供了一种统一的方式来设置 PCI VF/SF 功能属性，适用于 SmartNIC 和非 SmartNIC。
这仅在 eswitch 模式设置为 switchdev 时才支持。可以通过 devlink eswitch 端口配置 PCI VF/SF 的端口功能。
应该在驱动程序枚举 PCI VF/SF 之前设置端口功能属性。

MAC 地址设置
-------------

mlx5 驱动程序支持 devlink 端口功能属性机制来设置 MAC 地址。（参见文档/网络/devlink/devlink-port.rst）

RoCE 能力设置
~~~~~~~~~~~~~~

并非所有 mlx5 PCI 设备/子功能都需要 RoCE 能力。
当禁用 RoCE 能力时，可以节省每台 PCI 设备/子功能 1 MB 的系统内存。
mlx5 驱动程序支持 devlink 端口功能属性机制来设置 RoCE 能力。（参见文档/网络/devlink/devlink-port.rst）

可迁移能力设置
~~~~~~~~~~~~~~~

希望 mlx5 PCI VF 能够进行实时迁移的用户需要显式启用 VF 的可迁移能力。
mlx5 驱动程序支持 devlink 端口功能属性机制来设置可迁移能力。（参见文档/网络/devlink/devlink-port.rst）

IPsec 加密能力设置
~~~~~~~~~~~~~~~~~~~

希望 mlx5 PCI VF 能够执行 IPsec 加密卸载的用户需要显式启用 VF 的 ipsec_crypto 能力。
从 ConnectX6dx 设备及更高版本开始支持为 VF 启用 IPsec 能力。当一个 VF 启用了 IPsec 能力后，在 PF 上的任何 IPsec 卸载都会被阻止。
mlx5 驱动程序支持 devlink 端口功能属性机制来设置 ipsec_crypto 能力。（参见文档/网络/devlink/devlink-port.rst）

IPsec 数据包能力设置
~~~~~~~~~~~~~~~~~~~

希望 mlx5 PCI VF 能够执行 IPsec 数据包卸载的用户需要显式启用 VF 的 ipsec_packet 能力。
从 ConnectX6dx 设备及更高版本开始支持为 VF 启用 IPsec 能力。当一个 VF 启用了 IPsec 能力后，在 PF 上的任何 IPsec 卸载都会被阻止。
mlx5驱动支持通过devlink端口功能属性机制来设置ipsec_packet能力。（参考文档：Documentation/networking/devlink/devlink-port.rst）

SF状态设置
--------------

为了使用SF（子功能），用户必须首先激活SF，使用SF功能的状态属性：
- 获取指定devlink端口索引标识的SF的状态：

   ```sh
   $ devlink port show ens2f0npf0sf88
   pci/0000:06:00.0/32768: 类型 eth 网络设备 ens2f0npf0sf88 风格 pcisf 控制器 0 pfnum 0 sfnum 88 外部 false 可分割 false
     功能:
       hw_addr 00:00:00:00:88:88 状态 inactive 操作状态 detached
   ```

- 激活该功能并验证其状态已变为活动状态：

   ```sh
   $ devlink port function set ens2f0npf0sf88 state active

   $ devlink port show ens2f0npf0sf88
   pci/0000:06:00.0/32768: 类型 eth 网络设备 ens2f0npf0sf88 风格 pcisf 控制器 0 pfnum 0 sfnum 88 外部 false 可分割 false
     功能:
       hw_addr 00:00:00:00:88:88 状态 active 操作状态 detached
   ```

当功能被激活时，PF（物理功能）驱动实例会从设备获取事件，表明特定的SF已被激活。这是将设备挂载到总线、探测设备并实例化devlink实例及其特定类辅助设备的信号。
- 显示子功能的辅助设备和端口：

    ```sh
    $ devlink dev show
    devlink dev show auxiliary/mlx5_core.sf.4

    $ devlink port show auxiliary/mlx5_core.sf.4/1
    auxiliary/mlx5_core.sf.4/1: 类型 eth 网络设备 p0sf88 风格 virtual 端口 0 可分割 false

    $ rdma link show mlx5_0/1
    link mlx5_0/1 状态 ACTIVE 物理状态 LINK_UP 网络设备 p0sf88

    $ rdma dev show
    8: rocep6s0f1: 节点类型 ca 固件 16.29.0550 节点GUID 248a:0703:00b3:d113 系统镜像GUID 248a:0703:00b3:d112
    13: mlx5_0: 节点类型 ca 固件 16.29.0550 节点GUID 0000:00ff:fe00:8888 系统镜像GUID 248a:0703:00b3:d112
    ```

- 子功能辅助设备和类设备层次结构：

                 mlx5_core.sf.4
          (子功能辅助设备)
                       /\
                      /  \
                     /    \
                    /      \
                   /        \
      mlx5_core.eth.4     mlx5_core.rdma.4
     (sf 以太网辅助设备)     (sf RDMA 辅助设备)
         |                      |
         |                      |
      p0sf88                  mlx5_0
     (sf 网络设备)          (sf RDMA 设备)

此外，当驱动程序连接到子功能的辅助设备时，SF端口也会接收到事件。这会导致功能的操作状态发生变化。这为用户提供可见性，以便决定何时安全地删除SF端口以优雅地终止子功能。
- 显示SF端口的操作状态：

    ```sh
    $ devlink port show ens2f0npf0sf88
    pci/0000:06:00.0/32768: 类型 eth 网络设备 ens2f0npf0sf88 风格 pcisf 控制器 0 pfnum 0 sfnum 88 外部 false 可分割 false
      功能:
        hw_addr 00:00:00:00:88:88 状态 active 操作状态 attached
    ```
