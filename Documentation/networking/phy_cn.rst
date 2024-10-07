PHY 抽象层
=====================

目的
=======

大多数网络设备包含一组寄存器，这些寄存器为 MAC 层提供接口，MAC 层通过 PHY 与物理连接进行通信。PHY 负责与网络连接另一端的对端设备（通常是以太网线缆）协商链路参数，并提供寄存器接口，使驱动程序能够确定所选择的设置，并配置允许的设置。尽管这些设备与网络设备本身是独立的，并且寄存器遵循标准布局，但通常的做法是将 PHY 管理代码集成到网络驱动中。这导致了大量的冗余代码。此外，在具有多个（有时差异很大）以太网控制器并连接到同一管理总线的嵌入式系统中，确保总线的安全使用变得困难。

由于 PHY 是设备，并且访问它们的管理总线实际上是总线，因此 PHY 抽象层（PAL）将它们作为设备来处理。这样做的目标是：

1. 增加代码复用性。
2. 提高整体代码的可维护性。
3. 加速新网络驱动和新系统的开发时间。

基本上，这一层旨在为 PHY 设备提供一个接口，使得网络驱动开发者可以编写尽可能少的代码，同时仍然提供完整功能集。

MDIO 总线
============

大多数网络设备通过管理总线连接到 PHY。不同的设备使用不同的总线（尽管有些共用相同的接口）。为了利用 PAL，每个总线接口需要注册为一个独立的设备。

1. 必须实现读写函数。其原型如下：
   ```c
   int write(struct mii_bus *bus, int mii_id, int regnum, u16 value);
   int read(struct mii_bus *bus, int mii_id, int regnum);
   ```
   `mii_id` 是总线上 PHY 的地址，`regnum` 是寄存器编号。这些函数不会在中断时被调用，因此可以安全地阻塞，等待中断信号完成操作。

2. 重置函数是可选的。用于将总线恢复到初始化状态。

3. 需要一个探测函数。该函数应设置总线驱动所需的内容、配置 `mii_bus` 结构体，并使用 `mdiobus_register` 注册到 PAL。类似地，还有一个移除函数来撤销所有这些操作（使用 `mdiobus_unregister`）。

4. 像任何驱动一样，必须配置 `device_driver` 结构体，并使用 init 和 exit 函数注册驱动。
#. 总线也必须在某处作为设备进行声明并注册
作为一个驱动程序实现MDIO总线驱动的例子，请参阅 `drivers/net/ethernet/freescale/fsl_pq_mdio.c` 和一个相关的DTS文件中的用户示例。（例如："git grep fsl,.*-mdio arch/powerpc/boot/dts/"）

(RG)MII/电气接口考虑
=============================

简化千兆介质独立接口（Reduced Gigabit Medium Independent Interface，简称RGMII）是一个使用同步125MHz时钟信号和多条数据线的12针电气信号接口。由于这一设计决定，在时钟线（RXC或TXC）与数据线之间必须添加1.5ns到2ns的延迟，以使物理层（PHY，即时钟接收端）有足够的建立时间和保持时间来正确采样数据线。PHY库提供了不同类型的PHY_INTERFACE_MODE_RGMII*值，以便让PHY驱动程序以及可选的MAC驱动程序实现所需的延迟。phy_interface_t的值应从PHY设备自身的角度理解，具体如下：

* PHY_INTERFACE_MODE_RGMII：PHY不负责自行插入任何内部延迟，它假定以太网MAC（如果支持的话）或PCB走线会插入正确的1.5-2ns延迟。

* PHY_INTERFACE_MODE_RGMII_TXID：PHY应该为经过PHY设备处理的发送数据线（TXD[3:0]）插入内部延迟。

* PHY_INTERFACE_MODE_RGMII_RXID：PHY应该为经过PHY设备处理的接收数据线（RXD[3:0]）插入内部延迟。

* PHY_INTERFACE_MODE_RGMII_ID：PHY应该为来自/去往PHY设备的发送和接收数据线都插入内部延迟。

尽可能地使用PHY侧的RGMII延迟，原因如下：

* PHY设备可能提供亚纳秒级的精度来指定接收/发送端的延迟（例如：0.5、1.0、1.5ns），这种精度可能需要补偿PCB走线长度的差异。

* PHY设备通常适用于广泛的领域（工业、医疗、汽车等），并且它们在整个温度/压力/电压范围内提供一致且可靠的延迟。

* 由于PHY设备驱动程序具有重用性，能够正确配置指定的延迟使得更多具有类似延迟要求的设计能够正常运行。

对于PHY无法提供该延迟但以太网MAC驱动程序可以做到的情况，正确的phy_interface_t值应该是PHY_INTERFACE_MODE_RGMII，并且以太网MAC驱动程序应正确配置以从PHY设备的角度提供所需的发送和/或接收端延迟。相反，如果以太网MAC驱动程序查看phy_interface_t值，并且对于除PHY_INTERFACE_MODE_RGMII以外的任何模式，它应确保禁用MAC级别的延迟。
在既不是以太网MAC也不是PHY能够提供所需延迟的情况下，根据RGMII标准定义，有几种选择可能可用：

* 某些SoC可能提供一个引脚垫/复用器/控制器，能够配置一组给定引脚的强度、延迟和电压；这可能是插入预期的2ns RGMII延迟的一个合适选项。
* 修改PCB设计以包含固定延迟（例如：使用专门设计的蛇形走线），这可能不需要软件配置。

RGMII延迟不匹配的常见问题
--------------------------------------

当以太网MAC和PHY之间的RGMII延迟不匹配时，这很可能会导致PHY或MAC在对这些信号进行快照并将其转换为逻辑1或0状态时，时钟和数据线信号变得不稳定。典型症状包括：

* 传输/接收部分工作，频繁或偶尔观察到丢包现象。

* 以太网MAC可能报告一些或所有进入的数据包带有FCS/CRC错误，或者全部丢弃。

* 切换到较低的速度（如10/100Mbps）会使问题消失（因为在这种情况下有足够的建立/保持时间）。

连接到PHY
==================

在启动过程中的某个时刻，网络驱动程序需要在PHY设备和网络设备之间建立连接。此时，PHY的总线和驱动程序都应已加载完毕，准备就绪。这时，有几种方式可以连接到PHY：

1. 物理层抽象层（PAL）处理一切，并在网络链接状态变化时调用网络驱动程序，使其作出反应。
2. 物理层抽象层处理一切，除了中断（通常是因为控制器拥有中断寄存器）。
3. 物理层抽象层处理一切，但每秒检查一次驱动程序，允许网络驱动程序先于PAL对任何变化作出反应。
4. 物理层抽象层仅作为函数库，网络设备手动调用函数来更新状态并配置PHY。

让物理层抽象层处理一切
==============================

如果您选择选项1（希望每个驱动程序都能这样做，但仍对不能这样做的驱动程序有用），连接到PHY很简单：

首先，您需要一个用于响应链接状态变化的函数。此函数遵循以下协议：

```c
static void adjust_link(struct net_device *dev);
```

接下来，您需要知道连接到此设备的PHY设备名称
名称看起来像“0:00”，其中第一个数字是总线ID，第二个数字是该总线上的PHY地址。通常，总线负责使其ID唯一。
现在，要连接，只需调用此函数：

```phydev = phy_connect(dev, phy_name, &adjust_link, interface);```

`phydev` 是一个指向 `phy_device` 结构的指针，该结构表示 PHY。如果 `phy_connect` 调用成功，它将返回该指针。这里的 `dev` 是指向您的 `net_device` 的指针。一旦完成，此函数将启动 PHY 的软件状态机，并为 PHY 的中断进行注册（如果有中断的话）。`phydev` 结构将填充有关当前状态的信息，不过此时 PHY 还没有真正运行。

应在调用 `phy_connect()` 之前设置 `phydev->dev_flags` 中的 PHY 特定标志，以便底层 PHY 驱动程序可以检查这些标志并根据它们执行特定操作。这对于系统对 PHY/控制器施加了硬件限制的情况非常有用，而这些限制是 PHY 需要知道的。

`interface` 是一个 u32 类型的变量，指定了控制器与 PHY 之间使用的连接类型。例如 GMII、MII、RGMII 和 SGMII。请参见下面的“PHY 接口模式”。完整列表请参阅 `include/linux/phy.h`。

接下来，请确保 `phydev->supported` 和 `phydev->advertising` 中没有任何对您的控制器没有意义的值（例如 10/100 控制器可能连接到千兆能力的 PHY，因此您需要屏蔽掉 `SUPPORTED_1000baseT*`）。关于这些位字段的定义，请参阅 `include/linux/ethtool.h`。请注意，除了 `SUPPORTED_Pause` 和 `SUPPORTED_AsymPause` 位（见下文）之外，您不应设置任何其他位，否则 PHY 可能会进入不支持的状态。

最后，在控制器准备好处理网络流量时，调用 `phy_start(phydev)`。这告诉 PAL 您已准备好，并配置 PHY 以连接到网络。如果您网络驱动程序中的 MAC 中断也处理 PHY 状态变化，则在调用 `phy_start` 之前将 `phydev->irq` 设置为 `PHY_MAC_INTERRUPT` 并从网络驱动程序中使用 `phy_mac_interrupt()`。如果您不想使用中断，则将 `phydev->irq` 设置为 `PHY_POLL`。`phy_start()` 启用 PHY 中断（如果适用）并启动 phylib 状态机。

当您想要断开网络连接（即使只是短暂地）时，调用 `phy_stop(phydev)`。此函数还会停止 phylib 状态机并禁用 PHY 中断。

### PHY 接口模式

在 `phy_connect()` 函数族中提供的 PHY 接口模式定义了 PHY 接口的初始工作模式。这不是保证不变的；有些 PHY 会根据协商结果动态改变其接口模式，无需软件干预。

以下是一些接口模式的描述：

``PHY_INTERFACE_MODE_SMII``
    这是串行 MII，时钟频率为 125 MHz，支持 100M 和 10M 速度。
一些细节可以在以下链接中找到：
https://opencores.org/ocsvn/smii/smii/trunk/doc/SMII.pdf

``PHY_INTERFACE_MODE_1000BASEX``
这定义了由802.3标准第36节定义的1000BASE-X单通道SerDes链路。该链路以固定的比特率1.25 Gbaud运行，使用10B/8B编码方案，从而产生1 Gbps的基础数据速率。数据流中嵌入了一个16位控制字，用于与远端协商全双工和暂停模式。这不包括“上时钟”变体（如2.5 Gbps速度，请参见下文）。

``PHY_INTERFACE_MODE_2500BASEX``
这定义了一种1000BASE-X的变体，其时钟频率是802.3标准的2.5倍，提供一个固定的比特率3.125 Gbaud。

``PHY_INTERFACE_MODE_SGMII``
这是用于Cisco SGMII的接口，它是802.3标准定义的1000BASE-X的修改版。SGMII链路由一个以固定比特率1.25 Gbaud运行的单通道SerDes组成，并采用10B/8B编码。基础数据速率为1 Gbps，通过复制每个数据符号来实现较慢的速度（如100 Mbps和10 Mbps）。802.3控制字被重新利用来发送从MAC到MAC的协商速度和全双工信息，并确认接收。这不包括“上时钟”变体（如2.5 Gbps速度）。
注意：在某些情况下，SGMII与1000BASE-X配置不匹配的情况下可以成功传输数据，但16位控制字将无法正确解释，可能会导致全双工、暂停或其他设置的不匹配。这取决于MAC和/或PHY的行为。

``PHY_INTERFACE_MODE_5GBASER``
这是IEEE 802.3第129条定义的5GBASE-R协议。它与第49条定义的10GBASE-R协议相同，只是运行频率减半。请参阅IEEE标准以获取定义。

``PHY_INTERFACE_MODE_10GBASER``
这是IEEE 802.3第49条定义的10GBASE-R协议，用于各种不同的介质。请参阅IEEE标准以获取定义。
注意：10GBASE-R只是可以与XFI和SFI一起使用的协议之一。XFI和SFI允许在一个单通道SerDes链路上使用多种协议，并且还定义了插入主机XFP/SFP连接器的合规板信号的电气特性。因此，XFI和SFI本身不是PHY接口类型。

``PHY_INTERFACE_MODE_10GKR``
这是IEEE 802.3第49条定义的10GBASE-R协议，带有第73条自动协商功能。请参阅IEEE标准以获取更多信息。
注意：由于历史原因，一些10GBASE-R使用情况错误地使用了这个定义。
``PHY_INTERFACE_MODE_25GBASER``
这是由IEEE 802.3 PCS第107条定义的25GBASE-R协议。PCS与10GBASE-R相同，即采用64B/66B编码，速度提高了2.5倍，提供固定的比特率25.78125 Gbaud。更多信息请参考IEEE标准。

``PHY_INTERFACE_MODE_100BASEX``
这定义了IEEE 802.3第24条。链路以固定的数据速率125Mbps运行，并使用4B/5B编码方案，从而产生100Mbps的基础数据速率。

``PHY_INTERFACE_MODE_QUSGMII``
这定义了Cisco的四通道USGMII模式，它是USGMII（通用SGMII）链路的四通道变体。它与QSGMII非常相似，但使用包控制头（PCH）而不是7字节前导码来携带端口ID和其他所谓的“扩展”。目前在规范中唯一记录的扩展是包含时间戳，用于PTP启用的PHY。此模式与QSGMII不兼容，但在链路速度和协商方面提供了相同的功能。

``PHY_INTERFACE_MODE_1000BASEKX``
这是由IEEE 802.3第36条定义的1000BASE-X，并带有第73条自动协商功能。通常，它将与第70条PMD一起使用。为了与用于第38条和39条PMD的1000BASE-X PHY模式进行对比，此接口模式具有不同的自动协商功能，并且仅支持全双工。

``PHY_INTERFACE_MODE_PSGMII``
这是Penta SGMII模式，它类似于QSGMII，但它将5个SGMII线路组合为一个链路，而QSGMII则组合4个。

``PHY_INTERFACE_MODE_10G_QXGMII``
代表由Cisco USXGMII多端口铜缆接口文档定义的10G-QXGMII PHY-MAC接口。它支持通过10.3125GHz SerDes通道实现4个端口，每个端口的速度为2.5G / 1G / 100M / 10M，通过符号复制实现。PCS期望标准的USXGMII码字。

暂停帧 / 流量控制
=================

PHY不会直接参与流量控制/暂停帧，除了确保在MII_ADVERTISE中设置SUPPORTED_Pause和SUPPORTED_AsymPause位，以向链路对端指示以太网MAC控制器支持这些功能。由于生成流量控制/暂停帧涉及以太网MAC驱动程序，因此建议该驱动程序通过相应设置SUPPORTED_Pause和SUPPORTED_AsymPause位来正确指示广告和支持这些功能。这可以在phy_connect()之前或之后完成，或者作为实现ethtool::set_pauseparam功能的结果。

密切关注PAL
=================

可能需要一些帮助才能使PAL内置的状态机保持网络设备和PHY之间的同步。如果是这样，您可以在连接到PHY时注册一个辅助函数，该函数将在状态机对任何更改做出反应之前每秒调用一次。为此，您需要手动调用phy_attach()和phy_prepare_link()，然后调用phy_start_machine()并将第二个参数设置为指向您的特殊处理程序。
目前没有关于如何使用此功能的例子，而且测试也有限，因为作者没有任何使用该功能的驱动程序（它们都使用选项1）。所以，买者自负。

自己动手做
===============

有可能PHY与您的网络设备之间的复杂交互关系无法通过PAL内置的状态机来跟踪。如果确实如此，您可以简单地调用`phy_attach()`，而不调用`phy_start_machine`或`phy_prepare_link()`。这意味着`phydev->state`完全由您自行处理（`phy_start`和`phy_stop`会在某些状态之间切换，因此您可能需要避免使用它们）。

为了确保在不运行状态机的情况下仍能访问有用的功能，大部分这些函数都是从不与复杂状态机交互的函数派生而来的。然而，再次强调，到目前为止还没有进行过不运行状态机的测试，因此使用者需谨慎。

以下是简要的函数说明：

```c
int phy_read(struct phy_device *phydev, u16 regnum);
int phy_write(struct phy_device *phydev, u16 regnum, u16 val);
```

简单的读写原语。它们会调用总线的读写函数指针。

```c
void phy_print_status(struct phy_device *phydev);
```

一个方便的函数，用于以整洁的方式打印PHY状态。

```c
void phy_request_interrupt(struct phy_device *phydev);
```

请求PHY中断的IRQ。

```c
struct phy_device * phy_attach(struct net_device *dev, const char *phy_id,
                               phy_interface_t interface);
```

将一个网络设备连接到特定的PHY，并在总线初始化时未找到驱动程序的情况下将其绑定到一个通用驱动程序。

```c
int phy_start_aneg(struct phy_device *phydev);
```

使用`phydev`结构内的变量，配置广告信息并重置自动协商，或者禁用自动协商并配置强制设置。

```c
static inline int phy_read_status(struct phy_device *phydev);
```

使用当前PHY中的设置信息填充`phydev`结构。
```c
// Ethtool辅助函数
int phy_ethtool_ksettings_set(struct phy_device *phydev,
                              const struct ethtool_link_ksettings *cmd);

int phy_mii_ioctl(struct phy_device *phydev,
                  struct mii_ioctl_data *mii_data, int cmd);

// MII ioctl。请注意，如果你写入像BMCR、BMSR、ADVERTISE等寄存器，这个函数将会完全破坏状态机。最好只用于写入非标准的寄存器，并且不会触发重新协商。

// PHY 设备驱动程序
==================

通过 PHY 抽象层（PHY Abstraction Layer），添加对新 PHY 的支持变得非常容易。在某些情况下，甚至不需要任何工作！然而，许多 PHY 需要一些额外的帮助才能运行起来。

// 通用 PHY 驱动程序
------------------

如果所需的 PHY 没有任何错误修正、特殊功能或需要支持的特性，那么最好不要添加支持，而是让 PHY 抽象层的通用 PHY 驱动程序完成所有的工作。

// 编写一个 PHY 驱动程序
--------------------

如果你确实需要编写一个 PHY 驱动程序，首先要做的是确保它可以与适当的 PHY 设备匹配。
这是在总线初始化期间通过读取设备的 UID（存储在寄存器 2 和 3 中），然后将其与每个驱动程序的 phy_id 字段进行按位与操作来实现的。此外，还需要给它起一个名字。以下是一个示例：

```c
static struct phy_driver dm9161_driver = {
        .phy_id         = 0x0181b880,
        .name           = "Davicom DM9161E",
        .phy_id_mask    = 0x0ffffff0,
        ..
};
```

接下来，你需要指定你的 PHY 设备和驱动程序支持哪些功能（如速度、全双工、自动协商等）。大多数 PHY 支持 PHY_BASIC_FEATURES，但你可以在 `include/mii.h` 中查找其他功能。
每个驱动程序由多个函数指针组成，这些指针在 `include/linux/phy.h` 中的 `phy_driver` 结构体中进行了文档说明。
其中，只有 `config_aneg` 和 `read_status` 是必须由驱动代码分配的。其余的都是可选的。另外，如果可能的话，最好使用通用 PHY 驱动程序版本的这两个函数：`genphy_read_status` 和 `genphy_config_aneg`。如果这不可能，很可能你只需要在这两个函数调用前后执行一些操作，因此你的函数将包装这些通用函数。

请随意查看 `drivers/net/phy/` 目录中的 Marvell、Cicada 和 Davicom 驱动程序作为示例（截至本文撰写时，lxt 和 qsemi 驱动程序尚未经过测试）。
```
PHY 的 MMD 寄存器访问默认由 PAL 框架处理，但如果需要，可以被特定的 PHY 驱动程序覆盖。如果在 IEEE 标准化 MMD PHY 寄存器定义之前 PHY 已经投入生产，就可能出现这种情况。大多数现代 PHY 可以使用通用的 PAL 框架来访问 PHY 的 MMD 寄存器。例如，能源效率以太网（Energy Efficient Ethernet）的支持就是通过 PAL 实现的。这种支持通过 PAL 访问 MMD 寄存器进行 EEE 查询和配置，前提是 PHY 支持 IEEE 标准访问机制；否则，如果被特定的 PHY 驱动程序覆盖，则可以使用 PHY 特定的访问接口。请参见 `drivers/net/phy/` 目录下的 Micrel 驱动程序，了解如何实现这一功能。

### 板载修复
有时候，平台与 PHY 之间的特定交互需要特殊处理。例如，改变 PHY 的时钟输入位置或添加延迟以解决数据路径中的延迟问题。为了支持这些情况，PHY 层允许平台代码注册修复程序，在 PHY 启动（或后续重置）时运行。

当 PHY 层启动一个 PHY 时，它会检查是否有为该 PHY 注册的修复程序，并根据 UID（包含在 PHY 设备的 `phy_id` 字段中）和总线标识符（包含在 `phydev->dev.bus_id` 中）进行匹配。两者都必须匹配，但是提供了两个常量 `PHY_ANY_ID` 和 `PHY_ANY_UID` 作为总线 ID 和 UID 的通配符。

当找到匹配项时，PHY 层将调用与修复程序关联的 `run` 函数。此函数接收指向感兴趣的 `phy_device` 的指针，因此只能对该 PHY 进行操作。

平台代码可以使用 `phy_register_fixup()` 注册修复程序：

```c
int phy_register_fixup(const char *phy_id,
                       u32 phy_uid, u32 phy_uid_mask,
                       int (*run)(struct phy_device *));
```

或者使用两个辅助函数之一 `phy_register_fixup_for_uid()` 和 `phy_register_fixup_for_id()`：

```c
int phy_register_fixup_for_uid(u32 phy_uid, u32 phy_uid_mask,
                               int (*run)(struct phy_device *));
int phy_register_fixup_for_id(const char *phy_id,
                              int (*run)(struct phy_device *));
```

这些辅助函数设置两个匹配标准之一，并将另一个设置为匹配任何内容。

当在模块加载时调用 `phy_register_fixup()` 或 `*_for_uid()` / `*_for_id()` 时，模块卸载时需要取消注册修复程序并释放分配的内存。

在卸载模块前调用以下函数之一：

```c
int phy_unregister_fixup(const char *phy_id, u32 phy_uid, u32 phy_uid_mask);
int phy_unregister_fixup_for_uid(u32 phy_uid, u32 phy_uid_mask);
int phy_unregister_fixup_for_id(const char *phy_id);
```

### 标准
#### IEEE 标准 802.3：CSMA/CD 接入方法和物理层规范 第二部分：
http://standards.ieee.org/getieee802/download/802.3-2008_section2.pdf

#### RGMII v1.3：
http://web.archive.org/web/20160303212629/http://www.hp.com/rnd/pdfs/RGMIIv1_3.pdf

#### RGMII v2.0：
http://web.archive.org/web/20160303171328/http://www.hp.com/rnd/pdfs/RGMIIv2_0_final_hp.pdf
