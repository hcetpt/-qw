SPDX 许可证标识符：GPL-2.0 或 Linux-OpenIB
.. include:: <isonum.txt>

=========
Switchdev
=========

:版权所有: |copy| 2023，NVIDIA CORPORATION 及其附属公司。保留所有权利
.. _mlx5_bridge_offload:

桥接卸载
==============

mlx5 驱动程序在 switchdev 模式下实现了桥接规则的卸载功能。当 mlx5 switchdev 代表端口连接到桥接设备时，Linux 桥接 FDB 会自动卸载。
- 更改设备为 switchdev 模式::

    $ devlink dev eswitch set pci/0000:06:00.0 mode switchdev

- 将 mlx5 switchdev 代表端口 'enp8s0f0' 连接到桥接网络设备 'bridge1'::

    $ ip link set enp8s0f0 master bridge1

VLAN
-----

mlx5 支持以下桥接 VLAN 功能：

- VLAN 过滤（包括每个端口的多个 VLAN）::

    $ ip link set bridge1 type bridge vlan_filtering 1
    $ bridge vlan add dev enp8s0f0 vid 2-3

- 在桥接入站时推送 VLAN 标签::

    $ bridge vlan add dev enp8s0f0 vid 3 pvid

- 在桥接出站时移除 VLAN 标签::

    $ bridge vlan add dev enp8s0f0 vid 3 untagged

子功能
===========

在 E-switch 上生成的子功能仅通过 devlink 设备创建，默认情况下所有子功能辅助设备均处于禁用状态。
这将允许用户在子功能完全探测之前进行配置，从而节省时间。
使用示例：

- 创建子功能 (SF) ::

    $ devlink port add pci/0000:08:00.0 flavour pcisf pfnum 0 sfnum 11
    $ devlink port function set pci/0000:08:00.0/32768 hw_addr 00:00:00:00:00:11 state active

- 启用 ETH 辅助设备 ::

    $ devlink dev param set auxiliary/mlx5_core.sf.1 name enable_eth value true cmode driverinit

- 现在，为了完全探测子功能，请使用 devlink 重载命令 ::

    $ devlink dev reload auxiliary/mlx5_core.sf.1

mlx5 支持 ETH、RDMA 和 VDPA（vnet）辅助设备的 devlink 参数（参见 :ref:`Documentation/networking/devlink/devlink-params.rst <devlink_params_generic>`）
mlx5 支持使用 devlink 端口接口进行子功能管理（参见 :ref:`Documentation/networking/devlink/devlink-port.rst <devlink_port>`）
子功能具有自己的功能能力和独立资源。这意味着子功能拥有自己专用的队列（发送队列 txq、接收队列 rxq、完成队列 cq 和事件队列 eq）。这些队列既不共享也不从父 PCI 功能中抢占。
当子功能支持 RDMA 时，它拥有自己专用的 QP1、GID 表和 RDMA 资源，这些资源既不共享也不从父 PCI 功能中抢占。
子功能在 PCI BAR 空间中有自己专用的窗口，该窗口不与其它子功能或父 PCI 功能共享。这确保了子功能的所有设备（如 netdev、rdma、vdpa 等）只能访问分配给它的 PCI BAR 空间。
子功能支持 eswitch 代表端口，通过该端口支持 tc 卸载。用户可以配置 eswitch 以向/从子功能端口发送/接收数据包。
子功能共享 PCI 级别资源，例如 PCI MSI-X 中断与其他子功能和/或其父 PCI 功能共享。
示例：mlx5 软件、系统和设备视图：

```
      _______
     | admin |
     | user  |----------
     |_______|         |
         |             |
     ____|____       __|______            _________________
    |         |     |         |          |                 |
    | devlink |     | tc tool |          |    user         |
    | tool    |     |_________|          | applications    |
    |_________|         |                |_________________|
             |             |                   |          |
             |             |                   |          |         用户空间
 +---------|-------------|-------------------|----------|--------------------+
             |             |           +----------+   +----------+   内核
             |             |           |  netdev  |   | rdma dev |
             |             |           +----------+   +----------+
   (devlink port add/del |              ^               ^
    port function set)   |              |               |
             |             |              +---------------|
      _____|___          |              |        _______|_______
     |         |         |              |       | mlx5 类    |
     | devlink |   +------------+       |       |   驱动程序   |
     | 内核    |   | rep netdev |       |       |(mlx5_core,ib) |
     |_________|   +------------+       |       |_______________|
             |             |              |               ^
   (devlink 操作)         |              |          (probe/remove)
  _________|________     |              |           ____|________
 | 子功能      |    |     +---------------+   | 子功能 |
 | 管理驱动程序|-----     | 子功能   |---|  驱动程序 |
 | (mlx5_core) |          | 辅助设备 |   | (mlx5_core) |
 |__________________|          +---------------+   |_____________|
             |                                            ^
  (sf add/del, vhca 事件)                             |
             |                                      (设备 add/del)
      _____|____                                    ____|________
     |          |                                  | 子功能 |
     |  PCI NIC |--- 激活/去激活事件 --->| 主机驱动程序 |
     |__________|                                  | (mlx5_core) |
                                                   |_____________|
```

子功能是使用 devlink 端口接口创建的。
- 将设备更改为 switchdev 模式：

    ```
    $ devlink dev eswitch set pci/0000:06:00.0 mode switchdev
    ```

- 添加一个子功能风味的 devlink 端口：

    ```
    $ devlink port add pci/0000:06:00.0 flavour pcisf pfnum 0 sfnum 88
    pci/0000:06:00.0/32768: type eth netdev eth6 flavour pcisf controller 0 pfnum 0 sfnum 88 external false splittable false
      function:
        hw_addr 00:00:00:00:00:00 state inactive opstate detached
    ```

- 显示子功能的 devlink 端口：

    ```
    $ devlink port show pci/0000:06:00.0/32768
    pci/0000:06:00.0/32768: type eth netdev enp6s0pf0sf88 flavour pcisf pfnum 0 sfnum 88
      function:
        hw_addr 00:00:00:00:00:00 state inactive opstate detached
    ```

- 使用后删除子功能的 devlink 端口：

    ```
    $ devlink port del pci/0000:06:00.0/32768
    ```

功能属性
=========

mlx5 驱动程序提供了一种机制，以统一的方式设置 PCI VF/SF 功能属性，适用于 SmartNIC 和非 SmartNIC。
仅当 eswitch 模式设置为 switchdev 时才支持此功能。通过 devlink eswitch 端口配置 PCI VF/SF 的端口功能。
在驱动程序枚举 PCI VF/SF 之前，应设置端口功能属性。

MAC 地址设置
------------

mlx5 驱动程序支持 devlink 端口功能属性机制来设置 MAC 地址。（参考文档：Documentation/networking/devlink/devlink-port.rst）

RoCE 能力设置
~~~~~~~~~~~~~

并非所有 mlx5 PCI 设备/SF 都需要 RoCE 能力。
当禁用 RoCE 能力时，可以节省每个 PCI 设备/SF 1 MB 的系统内存。
mlx5 驱动程序支持 devlink 端口功能属性机制来设置 RoCE 能力。（参考文档：Documentation/networking/devlink/devlink-port.rst）

可迁移能力设置
~~~~~~~~~~~~~~~

希望 mlx5 PCI VF 能够执行实时迁移的用户需要显式启用 VF 的可迁移能力。
mlx5 驱动程序支持 devlink 端口功能属性机制来设置可迁移能力。（参考文档：Documentation/networking/devlink/devlink-port.rst）

IPsec 加密能力设置
~~~~~~~~~~~~~~~~~~~

希望 mlx5 PCI VF 能够执行 IPsec 加密卸载的用户需要显式启用 VF 的 ipsec_crypto 能力。从 ConnectX6dx 设备开始支持为 VF 启用 IPsec 能力。当 VF 启用了 IPsec 能力时，任何 IPsec 卸载都会被阻止在 PF 上。
mlx5 驱动程序支持 devlink 端口功能属性机制来设置 ipsec_crypto 能力。（参考文档：Documentation/networking/devlink/devlink-port.rst）

IPsec 数据包能力设置
~~~~~~~~~~~~~~~~~~~~~

希望 mlx5 PCI VF 能够执行 IPsec 数据包卸载的用户需要显式启用 VF 的 ipsec_packet 能力。从 ConnectX6dx 设备开始支持为 VF 启用 IPsec 能力。当 VF 启用了 IPsec 能力时，任何 IPsec 卸载都会被阻止在 PF 上。
mlx5 驱动支持通过 devlink 端口功能属性机制来设置 ipsec_packet 能力。（参见 `Documentation/networking/devlink/devlink-port.rst`）

SF 状态设置
--------------

为了使用 SF，用户必须使用 SF 功能状态属性激活 SF
- 获取由其唯一的 devlink 端口索引标识的 SF 的状态：

  ```
  $ devlink port show ens2f0npf0sf88
  pci/0000:06:00.0/32768: type eth netdev ens2f0npf0sf88 flavour pcisf controller 0 pfnum 0 sfnum 88 external false splittable false
    function:
      hw_addr 00:00:00:00:88:88 state inactive opstate detached
  ```

- 激活该功能并验证其状态为活动：

  ```
  $ devlink port function set ens2f0npf0sf88 state active

  $ devlink port show ens2f0npf0sf88
  pci/0000:06:00.0/32768: type eth netdev ens2f0npf0sf88 flavour pcisf controller 0 pfnum 0 sfnum 88 external false splittable false
    function:
      hw_addr 00:00:00:00:88:88 state active opstate detached
  ```

在功能激活后，PF 驱动实例会从设备接收特定 SF 已被激活的事件。这是将设备挂载到总线、探测它并实例化 devlink 实例及其特定类别的辅助设备的提示。
- 显示子功能的辅助设备和端口：

  ```
  $ devlink dev show
  $ devlink dev show auxiliary/mlx5_core.sf.4

  $ devlink port show auxiliary/mlx5_core.sf.4/1
  auxiliary/mlx5_core.sf.4/1: type eth netdev p0sf88 flavour virtual port 0 splittable false

  $ rdma link show mlx5_0/1
  link mlx5_0/1 state ACTIVE physical_state LINK_UP netdev p0sf88

  $ rdma dev show
  8: rocep6s0f1: node_type ca fw 16.29.0550 node_guid 248a:0703:00b3:d113 sys_image_guid 248a:0703:00b3:d112
  13: mlx5_0: node_type ca fw 16.29.0550 node_guid 0000:00ff:fe00:8888 sys_image_guid 248a:0703:00b3:d112
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
     (sf eth 辅助设备)     (sf rdma 辅助设备)
         |                      |
         |                      |
      p0sf88                  mlx5_0
     (sf 网络设备)          (sf rdma 设备)

此外，当驱动程序附加到子功能的辅助设备时，SF 端口也会接收到事件。这会导致功能的操作状态发生变化。这为用户提供可见性以决定何时可以安全地删除 SF 端口以优雅地终止子功能。
- 显示 SF 端口的操作状态：

  ```
  $ devlink port show ens2f0npf0sf88
  pci/0000:06:00.0/32768: type eth netdev ens2f0npf0sf88 flavour pcisf controller 0 pfnum 0 sfnum 88 external false splittable false
    function:
      hw_addr 00:00:00:00:88:88 state active opstate attached
  ```
