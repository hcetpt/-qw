SPDX 许可证标识符: GPL-2.0

.. _devlink_port:

============
Devlink 端口
============

``devlink-port`` 是设备上存在的一个端口。它在逻辑上有独立的入站/出站点。一个 devlink 端口可以是多种类型之一。devlink 端口类型加上端口属性描述了端口代表的内容。打算发布 devlink 端口的设备驱动程序需要设置 devlink 端口属性并注册该端口。下面列出了 devlink 端口类型：

.. list-table:: Devlink 端口类型列表
   :widths: 33 90

   * - 类型
     - 描述
   * - ``DEVLINK_PORT_FLAVOUR_PHYSICAL``
     - 任何类型的物理端口。这可以是一个交换机物理端口或其他设备上的物理端口。
   * - ``DEVLINK_PORT_FLAVOUR_DSA``
     - 表示 DSA 互连端口。
   * - ``DEVLINK_PORT_FLAVOUR_CPU``
     - 表示仅适用于 DSA 的 CPU 端口。
   * - ``DEVLINK_PORT_FLAVOUR_PCI_PF``
     - 表示代表 PCI 物理功能（PF）端口的交换机端口。
   * - ``DEVLINK_PORT_FLAVOUR_PCI_VF``
     - 表示代表 PCI 虚拟功能（VF）端口的交换机端口。
   * - ``DEVLINK_PORT_FLAVOUR_PCI_SF``
     - 表示代表 PCI 子功能（SF）端口的交换机端口。
   * - ``DEVLINK_PORT_FLAVOUR_VIRTUAL``
     - 表示 PCI 虚拟功能的虚拟端口。
Devlink 端口可以根据下面描述的链路层有不同的类型。

.. list-table:: Devlink 端口类型列表
   :widths: 23 90

   * - 类型
     - 描述
   * - ``DEVLINK_PORT_TYPE_ETH``
     - 当端口的链路层为以太网时，驱动程序应设置此端口类型。
   * - ``DEVLINK_PORT_TYPE_IB``
     - 当端口的链路层为 InfiniBand 时，驱动程序应设置此端口类型。
   * - ``DEVLINK_PORT_TYPE_AUTO``
     - 当驱动程序需要自动检测端口类型时，该类型由用户指示。

PCI 控制器
----------
在大多数情况下，一个 PCI 设备只有一个控制器。一个控制器可能包含多个物理功能、虚拟功能和子功能。一个功能由一个或多个端口组成。这些端口由 devlink eswitch 端口表示。

然而，连接到多个 CPU 或多个 PCI 根复合体或智能网卡（SmartNIC）的 PCI 设备可能有多个控制器。对于具有多个控制器的设备，每个控制器通过唯一的控制器编号来区分。

eswitch 位于支持多个控制器端口的 PCI 设备上。

下面是一个具有两个控制器系统的示例图：

```
                 ---------------------------------------------------------
                 |                                                       |
                 |           --------- ---------         ------- ------- |
    -----------  |           | vf(s) | | sf(s) |         |vf(s)| |sf(s)| |
    | server  |  | -------   ----/---- ---/----- ------- ---/--- ---/--- |
    | pci rc  |=== | pf0 |______/________/       | pf1 |___/_______/     |
    | connect |  | -------                       -------                 |
    -----------  |     | controller_num=1 (no eswitch)                   |
                 ------|--------------------------------------------------
                 (internal wire)
                       |
                 ---------------------------------------------------------
                 | devlink eswitch ports and reps                        |
                 | ----------------------------------------------------- |
                 | |ctrl-0 | ctrl-0 | ctrl-0 | ctrl-0 | ctrl-0 |ctrl-0 | |
                 | |pf0    | pf0vfN | pf0sfN | pf1    | pf1vfN |pf1sfN | |
                 | ----------------------------------------------------- |
                 | |ctrl-1 | ctrl-1 | ctrl-1 | ctrl-1 | ctrl-1 |ctrl-1 | |
                 | |pf0    | pf0vfN | pf0sfN | pf1    | pf1vfN |pf1sfN | |
                 | ----------------------------------------------------- |
                 |                                                       |
                 |                                                       |
    -----------  |           --------- ---------         ------- ------- |
    | smartNIC|  |           | vf(s) | | sf(s) |         |vf(s)| |sf(s)| |
    | pci rc  |==| -------   ----/---- ---/----- ------- ---/--- ---/--- |
    | connect |  | | pf0 |______/________/       | pf1 |___/_______/     |
    -----------  | -------                       -------                 |
                 |                                                       |
                 |  local controller_num=0 (eswitch)                     |
                 ---------------------------------------------------------
```

在上述示例中，外部控制器（控制器编号 = 1）没有 eswitch。本地控制器（控制器编号 = 0）有 eswitch。本地控制器上的 Devlink 实例为两个控制器都有 eswitch 的 devlink 端口。

功能配置
=========
用户可以在枚举 PCI 功能之前配置一个或多个功能属性。通常这意味着用户应该在创建针对该功能的总线特定设备之前配置功能属性。但是，当启用 SRIOV 时，虚拟功能设备会在 PCI 总线上创建。因此，在将虚拟功能设备绑定到驱动程序之前，应配置功能属性。对于子功能而言，这意味着用户应在激活端口功能之前配置端口功能属性。
用户可以使用`devlink port function set hw_addr`命令设置功能的硬件地址。对于以太网端口功能，这意味着设置一个MAC地址。
用户也可以使用`devlink port function set roce`命令设置功能的RoCE能力。
用户还可以使用`devlink port function set migratable`命令将功能设置为可迁移的。
用户还可以使用`devlink port function set ipsec_crypto`命令设置功能的IPsec加密能力。
用户还可以使用`devlink port function set ipsec_packet`命令设置功能的IPsec数据包能力。
用户还可以使用`devlink port function set max_io_eqs`命令设置功能的最大IO事件队列。

功能属性
========

MAC地址设置
------------
配置的PCI VF/SF的MAC地址将被用于创建的netdevice和rdma设备。
- 获取由其唯一的devlink端口索引标识的VF的MAC地址：

    ```
    $ devlink port show pci/0000:06:00.0/2
    pci/0000:06:00.0/2: type eth netdev enp6s0pf0vf1 flavour pcivf pfnum 0 vfnum 1
      function:
        hw_addr 00:00:00:00:00:00
    ```

- 设置由其唯一的devlink端口索引标识的VF的MAC地址：

    ```
    $ devlink port function set pci/0000:06:00.0/2 hw_addr 00:11:22:33:44:55
    
    $ devlink port show pci/0000:06:00.0/2
    pci/0000:06:00.0/2: type eth netdev enp6s0pf0vf1 flavour pcivf pfnum 0 vfnum 1
      function:
        hw_addr 00:11:22:33:44:55
    ```

- 获取由其唯一的devlink端口索引标识的SF的MAC地址：

    ```
    $ devlink port show pci/0000:06:00.0/32768
    pci/0000:06:00.0/32768: type eth netdev enp6s0pf0sf88 flavour pcisf pfnum 0 sfnum 88
      function:
        hw_addr 00:00:00:00:00:00
    ```

- 设置由其唯一的devlink端口索引标识的SF的MAC地址：

    ```
    $ devlink port function set pci/0000:06:00.0/32768 hw_addr 00:00:00:00:88:88
    
    $ devlink port show pci/0000:06:00.0/32768
    pci/0000:06:00.0/32768: type eth netdev enp6s0pf0sf88 flavour pcisf pfnum 0 sfnum 88
      function:
        hw_addr 00:00:00:00:88:88
    ```

RoCE能力设置
--------------
并非所有的PCI VF/SF都需要RoCE能力。
当禁用RoCE能力时，可以节省每个PCI VF/SF的系统内存。
当用户为某个VF/SF禁用RoCE能力时，用户应用程序不能通过此VF/SF发送或接收任何RoCE数据包，并且该PCI的RoCE GID表将是空的。
当通过端口功能属性禁用设备中的RoCE功能时，VF/SF驱动程序无法覆盖它。

- 获取VF设备的RoCE功能：

    ```
    $ devlink port show pci/0000:06:00.0/2
    pci/0000:06:00.0/2: type eth netdev enp6s0pf0vf1 flavour pcivf pfnum 0 vfnum 1
        function:
            hw_addr 00:00:00:00:00:00 roce enable
    ```

- 设置VF设备的RoCE功能：

    ```
    $ devlink port function set pci/0000:06:00.0/2 roce disable

    $ devlink port show pci/0000:06:00.0/2
    pci/0000:06:00.0/2: type eth netdev enp6s0pf0vf1 flavour pcivf pfnum 0 vfnum 1
        function:
            hw_addr 00:00:00:00:00:00 roce disable
    ```

可迁移功能设置
---------------------------
实时迁移是指在不中断其正常操作的情况下将一个活动虚拟机从一个物理主机转移到另一个物理主机的过程。
希望PCI VF能够进行实时迁移的用户需要显式启用VF的可迁移功能。
当用户启用了VF的可迁移功能，并且HV（Hypervisor）使用支持迁移的VFIO驱动程序绑定VF时，用户可以将带有该VF的VM从一个HV迁移到另一个不同的HV。
然而，当启用可迁移功能时，设备会禁用那些无法迁移的功能。因此，可迁移功能可能会对VF施加限制，让用户自行决定。
带有可迁移功能配置的实时迁移示例：
- 获取VF设备的可迁移功能：

    ```
    $ devlink port show pci/0000:06:00.0/2
    pci/0000:06:00.0/2: type eth netdev enp6s0pf0vf1 flavour pcivf pfnum 0 vfnum 1
        function:
            hw_addr 00:00:00:00:00:00 migratable disable
    ```

- 设置VF设备的可迁移功能：

    ```
    $ devlink port function set pci/0000:06:00.0/2 migratable enable

    $ devlink port show pci/0000:06:00.0/2
    pci/0000:06:00.0/2: type eth netdev enp6s0pf0vf1 flavour pcivf pfnum 0 vfnum 1
        function:
            hw_addr 00:00:00:00:00:00 migratable enable
    ```

- 将VF绑定到支持迁移的VFIO驱动程序：

    ```
    $ echo <pci_id> > /sys/bus/pci/devices/0000:08:00.0/driver/unbind
    $ echo mlx5_vfio_pci > /sys/bus/pci/devices/0000:08:00.0/driver_override
    $ echo <pci_id> > /sys/bus/pci/devices/0000:08:00.0/driver/bind
    ```

将VF附加到VM
启动VM
执行实时迁移
IPsec加密功能设置
-----------------------------
当用户为VF启用IPsec加密功能时，用户应用程序可以将XFRM状态加密操作（加密/解密）卸载到此VF上。
当VF的IPsec加密功能被禁用（默认情况下）时，XFRM状态由内核在软件中处理。
IPsec加密功能获取
-------------------
```
$ devlink port show pci/0000:06:00.0/2
pci/0000:06:00.0/2: type eth netdev enp6s0pf0vf1 flavour pcivf pfnum 0 vfnum 1
    function:
        hw_addr 00:00:00:00:00:00 ipsec_crypto disabled
```

设置VF设备的IPsec加密功能
-------------------------
```
$ devlink port function set pci/0000:06:00.0/2 ipsec_crypto enable

$ devlink port show pci/0000:06:00.0/2
pci/0000:06:00.0/2: type eth netdev enp6s0pf0vf1 flavour pcivf pfnum 0 vfnum 1
    function:
        hw_addr 00:00:00:00:00:00 ipsec_crypto enabled
```

IPsec数据包能力设置
---------------------
当用户为VF启用IPsec数据包能力时，用户的应用程序可以将XFRM状态和策略加密操作（加密/解密）卸载到该VF上，并且还可以进行IPsec封装。如果IPsec数据包能力被禁用（默认），则XFRM状态和策略将由内核在软件中处理。
- 获取VF设备的IPsec数据包能力:
```
$ devlink port show pci/0000:06:00.0/2
pci/0000:06:00.0/2: type eth netdev enp6s0pf0vf1 flavour pcivf pfnum 0 vfnum 1
    function:
        hw_addr 00:00:00:00:00:00 ipsec_packet disabled
```

- 设置VF设备的IPsec数据包能力:
```
$ devlink port function set pci/0000:06:00.0/2 ipsec_packet enable

$ devlink port show pci/0000:06:00.0/2
pci/0000:06:00.0/2: type eth netdev enp6s0pf0vf1 flavour pcivf pfnum 0 vfnum 1
    function:
        hw_addr 00:00:00:00:00:00 ipsec_packet enabled
```

最大I/O事件队列设置
--------------------
当用户设置了SF或VF的最大I/O事件队列数量后，相应的功能驱动程序将仅能使用所强制的数量的I/O事件队列。I/O事件队列传递与I/O队列相关的事件，包括网络设备的发送和接收队列（txq 和 rxq）以及RDMA 队列对（QPs）。例如，网卡通道数和RDMA设备完成向量的数量都是从功能的I/O事件队列派生出来的。通常情况下，驱动程序消耗的中断向量数量受到每个设备的I/O事件队列数量的限制，因为每个I/O事件队列都连接到一个中断向量。
- 获取VF设备的最大I/O事件队列数量:
```
$ devlink port show pci/0000:06:00.0/2
pci/0000:06:00.0/2: type eth netdev enp6s0pf0vf1 flavour pcivf pfnum 0 vfnum 1
    function:
        hw_addr 00:00:00:00:00:00 ipsec_packet disabled max_io_eqs 10
```

- 设置VF设备的最大I/O事件队列数量:
```
$ devlink port function set pci/0000:06:00.0/2 max_io_eqs 32

$ devlink port show pci/0000:06:00.0/2
pci/0000:06:00.0/2: type eth netdev enp6s0pf0vf1 flavour pcivf pfnum 0 vfnum 1
    function:
        hw_addr 00:00:00:00:00:00 ipsec_packet disabled max_io_eqs 32
```

子功能
======
子功能是一个轻量级的功能，它部署在一个父PCI功能上。子功能以单个单位创建和部署。与SRIOV VF不同的是，子功能不需要自己的PCI虚拟功能。子功能通过父PCI功能与硬件通信。要使用子功能，需要遵循三个步骤的设置序列：
1) 创建 - 创建一个子功能；
2) 配置 - 配置子功能属性；
3) 部署 - 部署子功能；

子功能管理是通过devlink端口用户界面完成的。用户在子功能管理设备上执行设置。
(1) 创建
----------
子功能是通过devlink端口接口创建的。用户通过添加一个具有子功能特性的devlink端口来添加子功能。devlink内核代码会调用子功能管理驱动程序（devlink ops）并要求其创建一个子功能devlink端口。然后，驱动程序实例化子功能端口及其相关对象，如健康报告器和代表网卡。
(2) 配置
-------------

创建了一个子功能端口，但还未激活。这意味着在 devlink 一侧已创建了实体，并且创建了 e-switch 端口代表符，但是子功能设备本身尚未创建。用户可以使用 e-switch 端口代表符进行设置，将其放入网桥中、添加 TC 规则等。用户还可以在子功能未激活时配置其硬件地址（如 MAC 地址）。

(3) 部署
--------

配置完子功能后，用户必须激活它才能使用。激活时，子功能管理驱动会请求子功能管理设备在特定的 PCI 功能上实例化子功能设备。子功能设备在 :ref:`Documentation/driver-api/auxiliary_bus.rst <auxiliary_bus>` 中创建。此时，相应的子功能驱动程序将绑定到子功能的辅助设备。

速率对象管理
==============

Devlink 提供了用于管理单个 devlink 端口或一组端口的发送速率的 API。这是通过速率对象实现的，这些对象有两种类型：

``leaf``
  表示一个单独的 devlink 端口；由驱动程序创建和销毁。由于 leaf 与其 devlink 端口之间是一对一的关系，在用户空间中，它被称为 ``pci/<bus_addr>/<port_index>``；

``node``
  表示一组速率对象（leafs 和/或 nodes）；根据用户空间的请求创建或删除；初始为空（没有添加任何速率对象）。在用户空间中，它被称为 ``pci/<bus_addr>/<node_name>``，其中 ``node_name`` 可以是任何标识符，但不能是十进制数字，以避免与 leaf 发生冲突。

API 允许配置以下速率对象参数：

``tx_share``
  在所有其他速率对象之间共享的最小 TX 速率值，或者如果属于同一组，则是在父组中的速率对象之间的共享最小 TX 速率值。

``tx_max``
  最大 TX 速率值。

``tx_priority``
  允许在兄弟节点间使用严格的优先级仲裁机制。这种仲裁方案试图在节点保持在其带宽限制内的情况下基于优先级调度节点。优先级越高，被选中进行调度的可能性就越大。

``tx_weight``
  允许在兄弟节点间使用加权公平队列仲裁方案。这种仲裁方案可以与严格的优先级同时使用。随着节点配置的速率增加，它相对于其兄弟节点获得更多的带宽。这些值是相对的，类似于百分比点，基本上说明了节点相对于其兄弟节点应该占用多少带宽。
``parent``
父节点名称。父节点的速率限制被视为其所有子节点限速的额外限制。“tx_max”是子节点的上限，“tx_share”是分配给子节点的总带宽。
“tx_priority”和“tx_weight”可以同时使用。在这种情况下，具有相同优先级的节点会在兄弟节点组中形成一个WFQ（加权公平队列）子组，并根据分配的权重进行仲裁。
仲裁流程如下：

1. 选择一个节点或一组具有最高优先级且未超出带宽限制且未被阻塞的节点。使用“tx_priority”作为此仲裁的参数。
2. 如果一组节点具有相同的优先级，则在该子组内执行WFQ仲裁。使用“tx_weight”作为此仲裁的参数。
3. 选择胜出的节点，并继续对其子节点进行仲裁，直到达到叶子节点并确定胜者。
4. 如果所有最高优先级子组中的节点都已满足需求或超出了分配的带宽，则转向较低优先级的节点。

驱动程序实现允许支持这两种或任一类型的速率对象及其参数设置方法。此外，驱动程序实现还可以导出节点/叶子及其父子关系。

术语与定义
===========

.. list-table:: 术语与定义
   :widths: 22 90

   * - 术语
     - 定义
   * - ``PCI 设备``
     - 具有一个或多个 PCI 总线的物理 PCI 设备，包含一个或多个 PCI 控制器。
   * - ``PCI 控制器``
     - 一个控制器可能包含多个物理功能、虚拟功能和子功能。
* - ``端口功能 (Port function)``
     -  用于管理端口功能的对象
* - ``子功能 (Subfunction)``
     -  一种轻量级的功能，部署在其上的父PCI功能
* - ``子功能设备 (Subfunction device)``
     -  子功能的总线设备，通常位于辅助总线上
* - ``子功能驱动 (Subfunction driver)``
     -  为子功能辅助设备提供的设备驱动
* - ``子功能管理设备 (Subfunction management device)``
     -  支持子功能管理的PCI物理功能
* - ``子功能管理驱动 (Subfunction management driver)``
     -  用于支持通过devlink端口接口进行子功能管理的PCI物理功能的设备驱动
* - ``子功能主机驱动 (Subfunction host driver)``
     -  为主机子功能设备提供的PCI物理功能的设备驱动。在大多数情况下，它与子功能管理驱动相同。当子功能用于外部控制器时，子功能管理和主机驱动是不同的
