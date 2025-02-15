```SPDX 许可证标识符: GPL-2.0

.. _开发链接端口:

=================
开发链接端口(Devlink Port)
=================

``devlink-port`` 是存在于设备上的端口。它具有设备上逻辑上独立的输入/输出点。一个开发链接端口可以有多种类型。开发链接端口的类型加上端口属性描述了端口所代表的内容。
打算发布开发链接端口的设备驱动程序设置开发链接端口属性并注册开发链接端口。
下面列出了开发链接端口的类型。

.. list-table:: 开发链接端口类型的列表
   :widths: 33 90

   * - 类型
     - 描述
   * - ``DEVLINK_PORT_FLAVOUR_PHYSICAL``
     - 任何类型的物理端口。这可以是交换机的物理端口或设备上的其他物理端口。
   * - ``DEVLINK_PORT_FLAVOUR_DSA``
     - 表示DSA互连端口。
   * - ``DEVLINK_PORT_FLAVOUR_CPU``
     - 表示仅适用于DSA的CPU端口。
   * - ``DEVLINK_PORT_FLAVOUR_PCI_PF``
     - 表示PCI物理功能(PF)端口的交换机端口。
   * - ``DEVLINK_PORT_FLAVOUR_PCI_VF``
     - 表示PCI虚拟功能(VF)端口的交换机端口。
   * - ``DEVLINK_PORT_FLAVOUR_PCI_SF``
     - 表示PCI子功能(SF)端口的交换机端口。
   * - ``DEVLINK_PORT_FLAVOUR_VIRTUAL``
     - 表示PCI虚拟功能的虚拟端口。
```

请注意，上述翻译保持了原文的技术性和专业性，并进行了适当的调整以适应中文语境。
根据链接层的不同，Devlink端口可能具有不同的类型，如下表所示：

.. list-table:: Devlink端口类型列表
   :widths: 23 90

   * - 类型
     - 描述
   * - ``DEVLINK_PORT_TYPE_ETH``
     - 当端口的链接层为以太网时，驱动程序应设置此端口类型。
   * - ``DEVLINK_PORT_TYPE_IB``
     - 当端口的链接层为InfiniBand时，驱动程序应设置此端口类型。
   * - ``DEVLINK_PORT_TYPE_AUTO``
     - 当驱动程序需要自动检测端口类型时，该类型由用户指示。

PCI控制器
----------
在大多数情况下，一个PCI设备只有一个控制器。一个控制器可能包含多个物理、虚拟功能和子功能。一个功能由一个或多个端口组成。这些端口由Devlink交换机端口表示。
然而，连接到多个CPU、多个PCI根复合体或智能网络接口卡(SmartNIC)的PCI设备可能有多个控制器。对于拥有多个控制器的设备，每个控制器通过唯一的控制器编号来区分。
支持多个控制器端口的交换机位于PCI设备上。
以下是一个拥有两个控制器的系统示例图：

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
                 | Devlink交换机端口和代表端口                        |
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

在上述示例中，外部控制器（标识符为控制器编号=1）没有Devlink交换机。本地控制器（标识符为控制器编号=0）拥有Devlink交换机。本地控制器上的Devlink实例为两个控制器提供了Devlink交换机端口。

功能配置
=========

用户可以在枚举PCI功能之前配置一个或多个功能属性。通常这意味着，在为功能创建特定于总线的设备之前，用户应该配置功能属性。但是，当启用SRIOV时，虚拟功能设备将在PCI总线上创建。因此，在将虚拟功能设备绑定到驱动程序之前，应该配置功能属性。对于子功能来说，这意味着用户应在激活端口功能之前配置端口功能属性。
用户可以使用 `devlink port function set hw_addr` 命令设置功能的硬件地址。对于以太网端口功能，这意味着设置一个 MAC 地址。
用户也可以使用 `devlink port function set roce` 命令设置功能的 RoCE 能力。
用户还可以使用 `devlink port function set migratable` 命令将功能设置为可迁移的。
用户还可以使用 `devlink port function set ipsec_crypto` 命令设置功能的 IPsec 加密能力。
用户还可以使用 `devlink port function set ipsec_packet` 命令设置功能的 IPsec 数据包处理能力。
用户还可以使用 `devlink port function set max_io_eqs` 命令设置功能的最大 I/O 事件队列。

### 功能属性

#### MAC 地址设置

配置的 PCI VF/SF 的 MAC 地址将被用于创建 PCI VF/SF 的网络设备和 RDMA 设备。
- 获取由其唯一的 devlink 端口索引标识的 VF 的 MAC 地址：

    ```shell
    $ devlink port show pci/0000:06:00.0/2
    pci/0000:06:00.0/2: 类型 eth 网络设备 enp6s0pf0vf1 风格 pcivf pfnum 0 vfnum 1
      功能:
        hw_addr 00:00:00:00:00:00
    ```

- 设置由其唯一的 devlink 端口索引标识的 VF 的 MAC 地址：

    ```shell
    $ devlink port function set pci/0000:06:00.0/2 hw_addr 00:11:22:33:44:55
    
    $ devlink port show pci/0000:06:00.0/2
    pci/0000:06:00.0/2: 类型 eth 网络设备 enp6s0pf0vf1 风格 pcivf pfnum 0 vfnum 1
      功能:
        hw_addr 00:11:22:33:44:55
    ```

- 获取由其唯一的 devlink 端口索引标识的 SF 的 MAC 地址：

    ```shell
    $ devlink port show pci/0000:06:00.0/32768
    pci/0000:06:00.0/32768: 类型 eth 网络设备 enp6s0pf0sf88 风格 pcisf pfnum 0 sfnum 88
      功能:
        hw_addr 00:00:00:00:00:00
    ```

- 设置由其唯一的 devlink 端口索引标识的 SF 的 MAC 地址：

    ```shell
    $ devlink port function set pci/0000:06:00.0/32768 hw_addr 00:00:00:00:88:88
    
    $ devlink port show pci/0000:06:00.0/32768
    pci/0000:06:00.0/32768: 类型 eth 网络设备 enp6s0pf0sf88 风格 pcisf pfnum 0 sfnum 88
      功能:
        hw_addr 00:00:00:00:88:88
    ```

#### RoCE 能力设置

并非所有的 PCI VF/SF 都需要 RoCE 能力。
当禁用 RoCE 能力时，可以节省每个 PCI VF/SF 所占用的系统内存。
当用户为 VF/SF 禁用 RoCE 能力时，用户的应用程序不能通过该 VF/SF 发送或接收任何 RoCE 数据包，并且此 PCI 的 RoCE GID 表将为空。
当使用端口功能属性在设备中禁用RoCE能力时，
VF/SF驱动程序无法覆盖这一设置。
- 获取VF设备的RoCE能力：

    $ devlink port show pci/0000:06:00.0/2
    pci/0000:06:00.0/2: 类型 eth 网卡 enp6s0pf0vf1 风味 pcivf pfnum 0 vfnum 1
        功能:
            硬件地址 00:00:00:00:00:00 RoCE 启用

- 设置VF设备的RoCE能力：

    $ devlink port function set pci/0000:06:00.0/2 roce disable

    $ devlink port show pci/0000:06:00.0/2
    pci/0000:06:00.0/2: 类型 eth 网卡 enp6s0pf0vf1 风味 pcivf pfnum 0 vfnum 1
        功能:
            硬件地址 00:00:00:00:00:00 RoCE 禁用

可迁移能力设置
-----------------
实时迁移是指将正在运行中的虚拟机从一个物理主机转移到另一个物理主机，而不会中断其正常操作的过程。
希望PCI VF能够执行实时迁移的用户需要明确启用VF的可迁移能力。
当用户为VF启用了可迁移能力，并且HV将VF绑定到支持迁移的VFIO驱动程序时，用户就可以将带有此VF的VM从一个HV迁移到另一个不同的HV上。
然而，当启用了可迁移能力时，设备将会禁用那些无法迁移的功能。因此，可迁移能力可能会对VF施加限制，这就需要用户来决定是否启用。
以下是具有可迁移功能配置的实时迁移示例：
- 获取VF设备的可迁移能力：

    $ devlink port show pci/0000:06:00.0/2
    pci/0000:06:00.0/2: 类型 eth 网卡 enp6s0pf0vf1 风味 pcivf pfnum 0 vfnum 1
        功能:
            硬件地址 00:00:00:00:00:00 可迁移 禁用

- 设置VF设备的可迁移能力：

    $ devlink port function set pci/0000:06:00.0/2 migratable enable

    $ devlink port show pci/0000:06:00.0/2
    pci/0000:06:00.0/2: 类型 eth 网卡 enp6s0pf0vf1 风味 pcivf pfnum 0 vfnum 1
        功能:
            硬件地址 00:00:00:00:00:00 可迁移 启用

- 将VF绑定到支持迁移的VFIO驱动程序：

    $ echo <pci_id> > /sys/bus/pci/devices/0000:08:00.0/driver/unbind
    $ echo mlx5_vfio_pci > /sys/bus/pci/devices/0000:08:00.0/driver_override
    $ echo <pci_id> > /sys/bus/pci/devices/0000:08:00.0/driver/bind

将VF附加到VM
启动VM
执行实时迁移
IPsec加密能力设置
-------------------
当用户为VF启用了IPsec加密能力时，用户应用程序可以将XFRM状态加密/解密操作卸载到这个VF上。
当VF的IPsec加密能力被禁用（默认）时，XFRM状态则由内核在软件中处理。
### IPsec 加密能力查询与设置
展示VF设备的IPsec加密能力：

    $ devlink port show pci/0000:06:00.0/2
    pci/0000:06:00.0/2: 类型 eth 网络设备 enp6s0pf0vf1 风味 pcivf pf编号 0 vf编号 1
        功能:
            硬件地址 00:00:00:00:00:00 IPsec加密 禁用

设置VF设备的IPsec加密能力：

    $ devlink port function set pci/0000:06:00.0/2 ipsec_crypto enable

    $ devlink port show pci/0000:06:00.0/2
    pci/0000:06:00.0/2: 类型 eth 网络设备 enp6s0pf0vf1 风味 pcivf pf编号 0 vf编号 1
        功能:
            硬件地址 00:00:00:00:00:00 IPsec加密 启用

### IPsec 数据包能力设置
当用户为VF启用IPsec数据包能力时，用户的应用程序可以将XFRM状态和策略加密操作（加密/解密）卸载到该VF上，同时也能处理IPsec封装。
当IPsec数据包能力被禁用（默认状态）时，XFRM状态和策略由内核在软件中处理。
- 查询VF设备的IPsec数据包能力：

    $ devlink port show pci/0000:06:00.0/2
    pci/0000:06:00.0/2: 类型 eth 网络设备 enp6s0pf0vf1 风味 pcivf pf编号 0 vf编号 1
        功能:
            硬件地址 00:00:00:00:00:00 IPsec数据包 禁用

- 设置VF设备的IPsec数据包能力：

    $ devlink port function set pci/0000:06:00.0/2 ipsec_packet enable

    $ devlink port show pci/0000:06:00.0/2
    pci/0000:06:00.0/2: 类型 eth 网络设备 enp6s0pf0vf1 风味 pcivf pf编号 0 vf编号 1
        功能:
            硬件地址 00:00:00:00:00:00 IPsec数据包 启用

### 最大IO事件队列设置
当用户为SF或VF设置了最大数量的IO事件队列时，相关的功能驱动程序只能使用设定数量的IO事件队列。
IO事件队列传递与IO队列相关的事件，包括网络设备的发送和接收队列(txq 和 rxq)以及RDMA队列对(QPs)。
例如，网络设备通道的数量和RDMA设备完成向量是由功能的IO事件队列衍生出来的。通常情况下，驱动程序消耗的中断向量的数量受到每个设备的IO事件队列数量的限制，因为每个IO事件队列都连接到一个中断向量。
- 查询VF设备的最大IO事件队列数：

    $ devlink port show pci/0000:06:00.0/2
    pci/0000:06:00.0/2: 类型 eth 网络设备 enp6s0pf0vf1 风味 pcivf pf编号 0 vf编号 1
        功能:
            硬件地址 00:00:00:00:00:00 IPsec数据包 禁用 最大IO事件队列 10

- 设置VF设备的最大IO事件队列数：

    $ devlink port function set pci/0000:06:00.0/2 max_io_eqs 32

    $ devlink port show pci/0000:06:00.0/2
    pci/0000:06:00.0/2: 类型 eth 网络设备 enp6s0pf0vf1 风味 pcivf pf编号 0 vf编号 1
        功能:
            硬件地址 00:00:00:00:00:00 IPsec数据包 禁用 最大IO事件队列 32

### 子功能
#### 概述
子功能是一个轻量级的功能，它部署在其父PCI功能之上。子功能以单位1创建。与SRIOV虚拟功能(VF)不同的是，子功能不需要自己的PCI虚拟功能。
子功能通过其父PCI功能与硬件通信。
为了使用子功能，需要遵循以下三个步骤的设置序列：
1) 创建 - 创建子功能；
2) 配置 - 配置子功能属性；
3) 部署 - 部署子功能；

子功能管理是通过devlink端口用户界面进行的。
用户在子功能管理设备上执行设置。
#### 创建
子功能通过devlink端口接口创建。用户通过添加子功能风味的devlink端口来增加子功能。devlink内核代码调用子功能管理驱动（devlink ops），并要求它创建一个子功能devlink端口。然后，驱动程序实例化子功能端口及其关联的对象，如健康报告器和代表网络设备。
### (2) 配置
--------------
创建了一个子功能端口，但尚未激活。这意味着在devlink侧创建了实体，e-switch端口代表已创建，但子功能设备本身尚未创建。用户可以使用e-switch端口代表来进行设置，将其放入网桥中、添加TC规则等。在子功能处于非活动状态时，用户还可以配置子功能的硬件地址（如MAC地址）。

### (3) 启用
----------
一旦配置好子功能，用户必须激活它才能使用。在激活时，子功能管理驱动会要求子功能管理设备在特定的PCI功能上实例化子功能设备。
子功能设备在 :ref:`Documentation/driver-api/auxiliary_bus.rst <auxiliary_bus>` 上创建。此时，匹配的子功能驱动程序将绑定到子功能的辅助设备。

### 速率对象管理
======================

Devlink提供了用于管理单个devlink端口或一组端口的发送速率的API。这是通过速率对象实现的，它可以是以下两种类型之一：

- **`leaf`**
  代表单个devlink端口；由驱动程序创建/销毁。由于leaf与其devlink端口是一对一映射，在用户空间中它被引用为**`pci/<bus_addr>/<port_index>`**；
  
- **`node`**
  代表一组速率对象（leafs和/或nodes）；根据用户空间的请求创建/删除；最初为空（没有添加任何速率对象）。在用户空间中，它被引用为**`pci/<bus_addr>/<node_name>`**，其中**`node_name`**可以是任何标识符，除了十进制数字，以避免与leaf冲突。

API允许配置以下速率对象参数：

- **`tx_share`**
  在同一组中的所有其他速率对象之间共享的最小TX速率值，或者如果它是同一组的一部分，则是该组中部分的速率对象之间的最小TX速率值。
  
- **`tx_max`**
  最大TX速率值。
  
- **`tx_priority`**
  允许在同级间使用严格的优先级仲裁器。这种仲裁方案试图在节点保持在其带宽限制内的情况下，基于它们的优先级来调度节点。优先级越高，节点被选中进行调度的概率就越高。
  
- **`tx_weight`**
  允许在同级间使用加权公平排队仲裁方案。此仲裁方案可以与严格优先级同时使用。随着节点配置的速率值增加，相对于其同级而言，它可以获得更多的带宽。这些值是相对的，类似于百分比点，基本上说明了节点相对于其同级应占用多少带宽。
### 翻译

`parent`
父节点名称。父节点的速率限制被视为其所有子节点限制的额外限制。
- `tx_max` 是子节点的上限。
- `tx_share` 是在子节点间分配的总带宽。
- `tx_priority` 和 `tx_weight` 可以同时使用。在这种情况下，具有相同优先级的节点在兄弟组中形成WFQ（加权公平队列）子组，并根据分配的权重进行仲裁。
仲裁流程从高层级开始：

1. 选择一个或一组最高优先级且未超出带宽限制并且未被阻塞的节点。使用 `tx_priority` 作为此仲裁的参数。
2. 如果一组节点具有相同的优先级，则对该子组执行WFQ仲裁。使用 `tx_weight` 作为此仲裁的参数。
3. 选择胜出的节点，并继续在其子节点间进行仲裁流程，直至到达叶子节点并确定胜者。
4. 如果来自最高优先级子组的所有节点都已满足或超额使用了分配给它们的带宽，则转向较低优先级的节点。

驱动实现可以支持这两种或任一类型的速率对象及其参数设置方法。此外，驱动实现还可以导出节点/叶节点及其子父关系。

### 术语与定义

#### 术语与定义

| 术语 | 定义 |
| --- | --- |
| `PCI设备` | 具有一个或多个PCI总线的物理PCI设备，该总线由一个或多个PCI控制器组成。 |
| `PCI控制器` | 控制器可能包含多个物理功能、虚拟功能和子功能。 |
* - ``端口功能`` 
     -  用于管理端口功能的对象
* - ``子功能`` 
     -  一个轻量级的功能，部署在作为其父项的 PCI 功能上
* - ``子功能设备`` 
     -  子功能的总线设备，通常位于辅助总线上
* - ``子功能驱动程序`` 
     -  为子功能辅助设备提供的设备驱动程序
* - ``子功能管理设备`` 
     -  支持子功能管理的 PCI 物理功能
* - ``子功能管理驱动程序`` 
     -  用于支持通过 devlink 端口接口进行子功能管理的 PCI 物理功能的设备驱动程序
* - ``子功能主机驱动程序`` 
     -  为主机上的子功能设备提供支持的 PCI 物理功能的设备驱动程序。大多数情况下，它与子功能管理驱动程序相同。当在外部控制器上使用子功能时，子功能管理和主机驱动程序是不同的
