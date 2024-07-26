### SPDX 许可证标识符: GPL-2.0

===================
ICE Devlink 支持
===================

本文档描述了由 `ice` 设备驱动程序实现的 Devlink 功能。

参数
==========

.. list-table:: 实现的通用参数
   :widths: 5 5 90

   * - 名称
     - 模式
     - 注释
   * - `enable_roce`
     - 运行时
     - 与 `enable_iwarp` 互斥
   * - `enable_iwarp`
     - 运行时
     - 与 `enable_roce` 互斥
   * - `tx_scheduling_layers`
     - 永久
     - ICE 硬件使用分层调度来处理发送（Tx），调度树中有固定的层数。每一层都是一个决策点。根节点代表端口，而所有叶节点代表队列。这种配置发送调度器的方式允许 DCB 或 devlink-rate（如下文所述）配置分配给特定队列或队列组的带宽量，从而实现精细控制，因为可以在树中的任何一层配置调度参数。
默认的九层树拓扑被认为最适合大多数工作负载，因为它提供了性能与可配置性的最佳比率。然而，在某些特殊情况下，这种九层拓扑可能不适用。
例如，向不是8的倍数的队列发送流量。因为在九层拓扑中，最大基数被限制为8，因此第九个队列与其他队列有不同的父节点，并且会获得更多的带宽积分。当系统向9个队列发送流量时，这会导致问题：

       | tx_queue_0_packets: 24163396
       | tx_queue_1_packets: 24164623
       | tx_queue_2_packets: 24163188
       | tx_queue_3_packets: 24163701
       | tx_queue_4_packets: 24163683
       | tx_queue_5_packets: 24164668
       | tx_queue_6_packets: 23327200
       | tx_queue_7_packets: 24163853
       | tx_queue_8_packets: 91101417 < 从第9个队列发送过多流量

为了解决这一需求，可以切换到五层拓扑，这将最大拓扑基数改为512。通过这一改进，所有队列都可以在树中分配到相同的父节点，因此性能特征相同。这种解决方案的一个明显缺点是树的配置深度较低。
使用 `tx_scheduling_layers` 参数与 Devlink 命令更改发送调度器拓扑。要使用五层拓扑，请使用值5。例如：
       $ devlink dev param set pci/0000:16:00.0 name tx_scheduling_layers
       value 5 cmode permanent
       使用值9将其设置回默认值。
必须进行 PCI 插槽电源循环以使选定的拓扑生效。
要验证该值是否已设置：
       $ devlink dev param show pci/0000:16:00.0 name tx_scheduling_layers
.. list-table:: 实现的驱动程序特定参数
    :widths: 5 5 90

    * - 名称
      - 模式
      - 描述
    * - `local_forwarding`
      - 运行时
      - 通过调整调度带宽来控制环回行为
它影响所有类型的函数：物理、虚拟和子函数
支持的值为：

        `enabled` - 允许在端口上进行环回流量

        `disabled` - 不允许在此端口上进行环回流量

        `prioritized` - 在此端口上优先处理环回流量

        `local_forwarding` 参数的默认值为 `enabled`
`prioritized` 提供了调整环回流量速率的能力，以增加一个端口的容量为代价减少另一个端口的容量。用户需要禁用其中一个端口上的本地转发，以便在 `prioritized` 端口上获得更高的容量。
信息版本
=============

`ice` 驱动程序报告了以下版本信息：

.. list-table:: devlink 信息实现的版本
    :widths: 5 5 5 90

    * - 名称
      - 类型
      - 示例
      - 描述
    * - `board.id`
      - 固定
      - K65390-000
      - 板卡的产品板组件（PBA）标识符
    * - `cgu.id`
      - 固定
      - 36
      - 时钟生成单元（CGU）硬件修订版标识符
    * - `fw.mgmt`
      - 运行中
      - 2.1.7
      - 设备上嵌入式管理处理器运行的管理固件的三位版本号。它控制物理层（PHY）、链路、访问设备资源等。Intel 文档将其称为 EMP 固件
    * - `fw.mgmt.api`
      - 运行中
      - 1.5.1
      - 管理固件通过 AdminQ 导出的 API 的三位版本号（主版本.次版本.修订版）。驱动程序用此来识别哪些命令被支持。历史内核版本仅显示两位版本号（主版本.次版本）
    * - `fw.mgmt.build`
      - 运行中
      - 0x305d955f
      - 管理固件源代码的唯一标识符
    * - `fw.undi`
      - 运行中
      - 1.2581.0
      - 包含 UEFI 驱动的 Option ROM 的版本。该版本采用 `主版本.次版本.修订版` 格式表示。当发生重大破坏性变更或次版本号溢出时，主版本号递增；对于非破坏性更改，次版本号递增，并在主版本号递增时重置为 1；修订版本通常为 0，但在对旧基础 Option ROM 交付修复补丁时会递增
    * - `fw.psid.api`
      - 运行中
      - 0.80
      - 定义闪存内容格式的版本
    * - `fw.bundle_id`
      - 运行中
      - 0x80002ec0
      - 加载到设备上的固件映像文件的唯一标识符。也称为 NVM 的 EETRACK 标识符
    * - `fw.app.name`
      - 运行中
      - ICE OS 默认包
      - 设备上激活的 DDP 包名称。DDP 包由驱动程序在初始化过程中加载。每个 DDP 包变体都有一个唯一的名称
    * - `fw.app`
      - 运行中
      - 1.3.1.0
      - 设备上激活的 DDP 包版本。请注意，要唯一地标识该包，需要同时提供名称（如 `fw.app.name` 报告所示）和版本号
* - ``fw.app.bundle_id``
      - 运行中
      - 0xc0000001
      - 加载在设备中的DDP包的唯一标识符。也被称为DDP跟踪ID。可用于唯一地标识特定的DDP包。
* - ``fw.netlist``
      - 运行中
      - 1.1.2000-6.7.0
      - 网络列表模块的版本。该模块定义了设备的以太网能力和默认设置，并被管理固件用于管理链路和设备连接性的一部分。
* - ``fw.netlist.build``
      - 运行中
      - 0xee16ced7
      - 网络列表模块内容哈希值的前4个字节。
* - ``fw.cgu``
      - 运行中
      - 8032.16973825.6021
      - 时钟生成单元（CGU）的版本。格式：<CGU类型>.<配置版本>.<固件版本>

### 闪存更新

`ice`驱动实现了通过`devlink-flash`接口支持闪存更新。它支持使用包含`fw.mgmt`、`fw.undi`和`fw.netlist`组件的组合闪存映像来更新设备闪存。

#### 支持的覆盖模式列表
| 比特位 | 行为 |
|--------|------|
| `DEVLINK_FLASH_OVERWRITE_SETTINGS` | 不保留正在更新的闪存组件中存储的设置。这包括覆盖确定设备将初始化的物理功能数量的端口配置。 |
| `DEVLINK_FLASH_OVERWRITE_SETTINGS` 和 `DEVLINK_FLASH_OVERWRITE_IDENTIFIERS` | 不保留任何设置或标识符。用提供的映像内容覆盖闪存中的所有内容，不执行任何保留。这包括覆盖诸如MAC地址、VPD区域和设备序列号等设备识别字段。预期这种组合与为特定设备定制的映像一起使用。 |

`ice`硬件不支持仅覆盖标识符同时保留设置，因此单独的`DEVLINK_FLASH_OVERWRITE_IDENTIFIERS`将被拒绝。如果没有提供覆盖掩码，则固件将在更新时被指示保留所有设置和识别字段。

### 重启

`ice`驱动支持在闪存更新后使用`DEVLINK_CMD_RELOAD`和`DEVLINK_RELOAD_ACTION_FW_ACTIVATE`动作激活新固件。

```shell
$ devlink dev reload pci/0000:01:00.0 reload action fw_activate
```

新固件通过发出特定于设备的嵌入式管理处理器重置命令来激活，该命令请求设备重置并重新加载EMP固件映像。
目前该驱动程序不支持通过`DEVLINK_RELOAD_ACTION_DRIVER_REINIT`重新加载驱动程序。
端口分割
========

`ice`驱动程序仅支持对端口0进行分割，因为固件为整个设备预定义了一组可用的端口分割选项。要应用端口分割，需要系统重启。以下命令将选择包含4个端口的端口分割选项：

.. code:: shell

    $ devlink port split pci/0000:16:00.0/0 count 4

每次执行`split`和`unsplit`命令后，所有可用的端口选项都会被打印到动态调试中。第一个选项是默认选项。
.. code:: shell

    ice 0000:16:00.0: 可用的端口分割选项及其最大端口速度 (Gbps):
    ice 0000:16:00.0: 状态  分割数     四分之一0        四分之一1
    ice 0000:16:00.0:         数量  L0  L1  L2  L3  L4  L5  L6  L7
    ice 0000:16:00.0: 激活  2     100   -   -   - 100   -   -   -
    ice 0000:16:00.0:         2      50   -  50   -   -   -   -   -
    ice 0000:16:00.0: 待定  4      25  25  25  25   -   -   -   -
    ice 0000:16:00.0:         4      25  25   -   -  25  25   -   -
    ice 0000:16:00.0:         8      10  10  10  10  10  10  10  10
    ice 0000:16:00.0:         1     100   -   -   -   -   -   -   -

可能存在多个具有相同端口分割数量的固件端口选项。当再次发出相同的端口分割数量请求时，将选择下一个具有相同端口分割数量的固件端口选项。
`devlink port unsplit`命令将选择分割数量为1的选项。如果没有任何可用的固件选项具有分割数量为1的情况，则会收到错误信息。
区域
====

`ice`驱动程序实现了以下区域以访问内部设备数据：
.. list-table:: 实现的区域
    :widths: 15 85

    * - 名称
      - 描述
    * - `nvm-flash`
      - 整个闪存芯片的内容，有时称为设备的非易失性存储器
    * - `shadow-ram`
      - 影子RAM的内容，它从闪存开始加载。虽然内容主要来自闪存，但这个区域还包含设备启动过程中生成的未存储在闪存中的数据
    * - `device-caps`
      - 设备固件功能缓冲区的内容。用于确定设备当前状态和配置的有用信息
``nvm-flash`` 和 ``shadow-ram`` 区域无需快照即可访问。而 ``device-caps`` 区域需要快照，因为其内容是由固件发送的，并且无法拆分成单独的读取操作。
用户可以通过 ``DEVLINK_CMD_REGION_NEW`` 命令请求对所有三个区域立即捕获快照。
.. code:: shell

    $ devlink region show
    pci/0000:01:00.0/nvm-flash: 大小 10485760 快照 [] 最大 1
    pci/0000:01:00.0/device-caps: 大小 4096 快照 [] 最大 10

    $ devlink region new pci/0000:01:00.0/nvm-flash 快照 1
    $ devlink region dump pci/0000:01:00.0/nvm-flash 快照 1

    $ devlink region dump pci/0000:01:00.0/nvm-flash 快照 1
    0000000000000000 0014 95dc 0014 9514 0035 1670 0034 db30
    0000000000000010 0000 0000 ffff ff04 0029 8c00 0028 8cc8
    0000000000000020 0016 0bb8 0016 1720 0000 0000 c00f 3ffc
    0000000000000030 bada cce5 bada cce5 bada cce5 bada cce5

    $ devlink region read pci/0000:01:00.0/nvm-flash 快照 1 地址 0 长度 16
    0000000000000000 0014 95dc 0014 9514 0035 1670 0034 db30

    $ devlink region delete pci/0000:01:00.0/nvm-flash 快照 1

    $ devlink region new pci/0000:01:00.0/device-caps 快照 1
    $ devlink region dump pci/0000:01:00.0/device-caps 快照 1
    0000000000000000 01 00 01 00 00 00 00 00 01 00 00 00 00 00 00 00
    (此处省略大量输出)
    0000000000000210 00 00 00 00 00 00 00 00 00 00 00 00 00 00 00 00

    $ devlink region delete pci/0000:01:00.0/device-caps 快照 1

Devlink Rate
============

``ice`` 驱动实现了 devlink-rate API。它允许将分层 QoS 卸载到硬件中。它使用户能够以树状结构来分组虚拟功能（Virtual Functions），并为树中的每个节点分配支持的参数：tx_share、tx_max、tx_priority 和 tx_weight。因此，用户实际上获得了控制每个 VF 组所分配带宽的能力。这之后由硬件强制执行。
假设此特性与在固件中执行的 DCB 和 ADQ 或任何触发 QoS 变更的驱动特性（例如新流量类别的创建）是互斥的。如果用户开始使用 devlink-rate API 对节点进行任何更改，驱动程序将阻止 DCB 或 ADQ 的配置。要配置这些特性，必须重新加载驱动程序。
相应地，如果 ADQ 或 DCB 被配置，驱动程序将不会导出层级结构，或者如果这些特性在层级结构被导出后但未进行任何更改前启用，驱动程序会移除未被改动的层级结构。
此特性还依赖于系统中启用的 switchdev 功能。
这是必要的，因为 devlink-rate 需要存在 devlink-port 对象，而这些对象仅在 switchdev 模式下创建。
如果驱动程序设置为 switchdev 模式，则会在创建 VF 时导出内部层级结构。树的根节点始终表示为 node_0。该节点不能被用户删除。叶子节点和有子节点的节点也不能被删除。
.. list-table:: 支持的属性
    :widths: 15 85

    * - 名称
      - 描述
    * - ``tx_max``
      - 树节点可消耗的最大带宽。速率限制是一个绝对数值，指定在一秒钟内节点可以消耗的最大字节数量。速率限制保证链路不会过饱和远程端点的接收方，并且也在订阅者与网络提供商之间实施服务等级协议（SLA）。
    * - ``tx_share``
      - 当树节点未被阻塞时分配给它的最小带宽。
它指定了一个绝对带宽（BW）。而 `tx_max` 定义了节点可以消耗的最大带宽，`tx_share` 标记了分配给节点的承诺带宽。
* - `tx_priority`
      - 允许在同级节点间使用严格的优先级仲裁。这种仲裁方案试图在节点保持在其带宽限制内的情况下，根据其优先级进行调度。
        优先级范围为 0-7。优先级为 7 的节点具有最高优先级并会被首先选择，而优先级为 0 的节点则具有最低优先级。具有相同优先级的节点将被平等对待。
* - `tx_weight`
      - 允许在同级节点间使用加权公平排队仲裁方案。该仲裁方案可以与严格优先级同时使用。
        范围为 1-200。对于仲裁而言，只有相对值才重要。
`tx_priority` 和 `tx_weight` 可以同时使用。在这种情况下，具有相同优先级的节点会形成一个加权公平排队（WFQ）子组，并基于分配的权重在这些节点间进行仲裁。

```shell
# 启用 switchdev 模式
$ devlink dev eswitch set pci/0000:4b:00.0 mode switchdev

# 此时驱动程序应导出内部层级结构
$ echo 2 > /sys/class/net/ens785np0/device/sriov_numvfs

$ devlink port function rate show
pci/0000:4b:00.0/node_25: 类型为 node, 父节点为 node_24
pci/0000:4b:00.0/node_24: 类型为 node, 父节点为 node_0
pci/0000:4b:00.0/node_32: 类型为 node, 父节点为 node_31
pci/0000:4b:00.0/node_31: 类型为 node, 父节点为 node_30
pci/0000:4b:00.0/node_30: 类型为 node, 父节点为 node_16
pci/0000:4b:00.0/node_19: 类型为 node, 父节点为 node_18
pci/0000:4b:00.0/node_18: 类型为 node, 父节点为 node_17
pci/0000:4b:00.0/node_17: 类型为 node, 父节点为 node_16
pci/0000:4b:00.0/node_14: 类型为 node, 父节点为 node_5
pci/0000:4b:00.0/node_5: 类型为 node, 父节点为 node_3
pci/0000:4b:00.0/node_13: 类型为 node, 父节点为 node_4
pci/0000:4b:00.0/node_12: 类型为 node, 父节点为 node_4
pci/0000:4b:00.0/node_11: 类型为 node, 父节点为 node_4
pci/0000:4b:00.0/node_10: 类型为 node, 父节点为 node_4
pci/0000:4b:00.0/node_9: 类型为 node, 父节点为 node_4
pci/0000:4b:00.0/node_8: 类型为 node, 父节点为 node_4
pci/0000:4b:00.0/node_7: 类型为 node, 父节点为 node_4
pci/0000:4b:00.0/node_6: 类型为 node, 父节点为 node_4
pci/0000:4b:00.0/node_4: 类型为 node, 父节点为 node_3
pci/0000:4b:00.0/node_3: 类型为 node, 父节点为 node_16
pci/0000:4b:00.0/node_16: 类型为 node, 父节点为 node_15
pci/0000:4b:00.0/node_15: 类型为 node, 父节点为 node_0
pci/0000:4b:00.0/node_2: 类型为 node, 父节点为 node_1
pci/0000:4b:00.0/node_1: 类型为 node, 父节点为 node_0
pci/0000:4b:00.0/node_0: 类型为 node
pci/0000:4b:00.0/1: 类型为 leaf, 父节点为 node_25
pci/0000:4b:00.0/2: 类型为 leaf, 父节点为 node_25

# 创建一些自定义节点
$ devlink port function rate add pci/0000:4b:00.0/node_custom 父节点为 node_0

# 第二个自定义节点
$ devlink port function rate add pci/0000:4b:00.0/node_custom_1 父节点为 node_custom

# 将第二个 VF 重新分配到新创建的分支
$ devlink port function rate set pci/0000:4b:00.0/2 父节点为 node_custom_1

# 为 VF 分配 tx_weight
$ devlink port function rate set pci/0000:4b:00.0/2 tx_weight 5

# 为 VF 分配 tx_share
$ devlink port function rate set pci/0000:4b:00.0/2 tx_share 500Mbps
```
