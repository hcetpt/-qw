物理层抽象层 (PHY Abstraction Layer)
====================================

目的
====

大多数网络设备包含一组寄存器，这些寄存器为介质访问控制层（MAC 层）提供接口，MAC 层通过物理层（PHY）与物理连接进行通信。PHY 负责与网络另一端的对等实体协商链路参数（通常是一根以太网线），并提供寄存器接口让驱动程序能够确定所选设置，并配置允许使用的设置。尽管这些设备与网络设备本身是分开的，并且它们的寄存器遵循一个标准布局，但通常的做法是将 PHY 管理代码集成到网络驱动程序中。这导致了大量的重复代码。此外，在具有多个（有时非常不同）以太网控制器并通过同一管理总线连接的嵌入式系统上，很难确保该总线的安全使用。

由于 PHY 是设备，而用于访问它们的管理总线实际上也是总线，因此物理层抽象层（PHY Abstraction Layer，PAL）将它们作为这样的设备处理。这样做有以下目标：

1. 提高代码复用率。
2. 增加整体代码可维护性。
3. 加快新网络驱动程序和新系统的开发时间。

基本上，这一层旨在为 PHY 设备提供一个接口，使网络驱动程序编写者能够尽可能少地编写代码，同时仍然提供完整的功能集。

MDIO 总线
=========

大多数网络设备通过管理总线与 PHY 相连。
不同的设备使用不同的总线（虽然有些共享共同的接口）。
为了利用 PAL，每个总线接口都需要注册为一个独立的设备。

1. 必须实现读写函数。其原型如下所示：

   ```c
   int write(struct mii_bus *bus, int mii_id, int regnum, u16 value);
   int read(struct mii_bus *bus, int mii_id, int regnum);
   ```

   `mii_id` 是总线上 PHY 的地址，`regnum` 是寄存器编号。这些函数被保证不会在中断时间内调用，因此它们可以安全地阻塞，等待中断信号表明操作已完成。

2. 重置函数是可选的。这个函数用于将总线恢复到初始化状态。
3. 需要一个探测函数。此函数应设置总线驱动程序所需的一切，配置 `mii_bus` 结构体，并使用 `mdiobus_register` 注册到 PAL。类似地，还有一个移除函数来撤销所有这些操作（使用 `mdiobus_unregister`）。
4. 和任何驱动程序一样，必须配置 `device_driver` 结构，并使用初始化和退出函数来注册驱动程序。
### 总线作为设备的声明与注册

总线也必须在某处被声明为一个设备，并进行注册。作为司机实现MDIO总线驱动的一个例子，可以参见`drivers/net/ethernet/freescale/fsl_pq_mdio.c`以及相关的DTS文件之一（例如，可以在PowerPC架构的DTS目录中通过`git grep fsl,.*-mdio arch/powerpc/boot/dts/`命令找到）。

### （RG）MII/电气接口考虑因素

**缩减型千兆介质独立接口（RGMII）**是一个使用同步125MHz时钟信号和多条数据线的12针电气信号接口。由于这个设计决策，需要在时钟线（RXC或TXC）和数据线之间添加1.5至2纳秒的延迟，以便让物理层设备（时钟接收端）有足够的建立时间和保持时间来正确地采样数据线。物理层库提供了不同类型的`PHY_INTERFACE_MODE_RGMII*`值，以允许物理层驱动程序和可选的媒体接入控制（MAC）驱动程序实现所需的延迟。`phy_interface_t`的值必须从物理层设备自身的角度理解，具体如下：

* `PHY_INTERFACE_MODE_RGMII`：物理层设备本身不负责插入任何内部延迟，它假设以太网MAC（如果具备能力）或者印刷电路板（PCB）布线已经插入了正确的1.5到2纳秒的延迟。
* `PHY_INTERFACE_MODE_RGMII_TXID`：物理层应该为经由物理层处理的发送数据线（TXD[3:0]）插入内部延迟。
* `PHY_INTERFACE_MODE_RGMII_RXID`：物理层应该为经由物理层处理的接收数据线（RXD[3:0]）插入内部延迟。
* `PHY_INTERFACE_MODE_RGMII_ID`：物理层应该为来自/到物理层设备的发送和接收数据线都插入内部延迟。

尽可能使用物理层侧的RGMII延迟，原因如下：

* 物理层设备可能提供亚纳秒级别的精度来设置接收器/发射器侧的延迟（例如：0.5、1.0、1.5纳秒），这种精度可能是为了弥补PCB布线长度差异所需。
* 物理层设备通常适用于广泛的场景（工业、医疗、汽车等），并在温度、压力、电压范围变化时提供一致且可靠的延迟。
* 物理层库中的物理层设备驱动程序本质上是可重用的，能够正确配置指定的延迟使得具有类似延迟要求的设计能够正确运行。

对于物理层无法提供延迟但以太网MAC驱动程序可以的情况，正确的`phy_interface_t`值应为`PHY_INTERFACE_MODE_RGMII`，并且以太网MAC驱动程序应该正确配置以从物理层的角度提供所需的发送和/或接收侧延迟。相反，如果以太网MAC驱动程序查看`phy_interface_t`值，对于除了`PHY_INTERFACE_MODE_RGMII`之外的任何模式，它应该确保MAC级的延迟被禁用。

如果既不是以太网MAC也不是物理层能够提供根据RGMII标准定义的所需延迟，可能会有以下几种选项：

* 某些系统级芯片（SoC）可能提供一个引脚垫/多路复用器/控制器，能够配置一组给定引脚的强度、延迟和电压；这可能是一个合适的选项来插入预期的2纳秒RGMII延迟。
* 修改PCB设计以包含固定延迟（例如：使用特别设计的蛇形走线），这可能不需要软件配置。

### RGMII延迟不匹配的常见问题

当以太网MAC和物理层之间的RGMII延迟不匹配时，这很可能导致时钟和数据线信号不稳定，当物理层或MAC对这些信号进行快照并将其转换为逻辑1或0状态以重建传输/接收的数据时。典型症状包括：

* 发送/接收部分工作，经常或偶尔出现数据包丢失。
* 以太网MAC可能报告一些或所有进入的数据包带有FCS/CRC错误，或者直接丢弃它们。
* 切换到较低的速度如10/100Mbps会使问题消失（因为在这种情况下有足够的建立/保持时间）。

### 连接到物理层

在启动过程中的某个时刻，网络驱动程序需要在物理层设备和网络设备之间建立连接。此时，物理层的总线和驱动程序都应该已经加载完毕，准备好进行连接。

此时有几种方式可以连接到物理层：

1. 物理层抽象层（PAL）处理一切，并仅在网络链接状态发生变化时调用网络驱动程序，以便它可以做出反应。
2. 物理层抽象层处理一切，除了中断（通常是控制器拥有中断寄存器）。
3. 物理层抽象层处理一切，但每秒与驱动程序检查一次，使网络驱动程序能够在物理层抽象层之前对任何变化做出反应。
4. 物理层抽象层仅作为一个函数库，网络设备手动调用函数来更新状态和配置物理层。

### 让物理层抽象层处理一切

如果你选择第一种方案（希望每个驱动程序都能做到，但仍对不能做到的驱动程序有用），连接到物理层很简单：

首先，你需要一个函数来响应链接状态的变化。此函数遵循以下协议：

```c
static void adjust_link(struct net_device *dev);
```

接下来，你需要知道连接到该设备的物理层设备名称。名称看起来像“0:00”，其中第一个数字是总线ID，第二个数字是该总线上的物理层地址。通常，总线负责使其ID唯一。
现在，要进行连接，只需调用以下函数：

    phydev = phy_connect(dev, phy_name, &adjust_link, interface);

*phydev* 是指向表示 PHY 的 `phy_device` 结构的指针。如果 `phy_connect` 调用成功，它将返回该指针。这里的 *dev* 是指向你的 `net_device` 的指针。调用此函数后，它将启动 PHY 的软件状态机，并为 PHY 的中断（如果有的话）注册。*phydev* 结构将填充有关当前状态的信息，不过此时 PHY 还未完全运行起来。

在调用 `phy_connect()` 之前，应该设置 PHY 特定的标志到 `phydev->dev_flags` 中，这样底层的 PHY 驱动可以检查这些标志并基于它们执行特定的操作。这对于系统对 PHY/控制器施加了硬件限制的情况很有用，这些限制是 PHY 需要知道的。

*interface* 是一个 u32 类型的值，用于指定控制器与 PHY 之间的连接类型。例如 GMII、MII、RGMII 和 SGMII。有关完整列表，请参阅 `include/linux/phy.h` 中的 "PHY 接口模式" 部分。

接下来，确保从 `phydev->supported` 和 `phydev->advertising` 中删除任何对于你的控制器没有意义的值（例如，一个 10/100 控制器可能连接到了千兆以太网 PHY，因此你需要屏蔽掉 `SUPPORTED_1000baseT*`）。这些位字段的定义可以在 `include/linux/ethtool.h` 中找到。请注意，除了 `SUPPORTED_Pause` 和 `SUPPORTED_AsymPause` 位之外，你不应该设置任何其他位，否则可能会导致 PHY 处于不受支持的状态。

最后，一旦控制器准备好处理网络流量，你就可以调用 `phy_start(phydev)`。这告诉平台抽象层（PAL）你已准备就绪，并配置 PHY 连接到网络。如果你的网络驱动程序中的 MAC 中断也处理 PHY 状态变化，只需在调用 `phy_start` 之前将 `phydev->irq` 设置为 `PHY_MAC_INTERRUPT`，然后从网络驱动程序中使用 `phy_mac_interrupt()`。如果不打算使用中断，则将 `phydev->irq` 设置为 `PHY_POLL`。`phy_start()` 启用 PHY 中断（如果适用），并启动 phylib 状态机。

当你想要从网络断开连接时（即使只是短暂断开），可以调用 `phy_stop(phydev)`。此函数也会停止 phylib 状态机并禁用 PHY 中断。

### PHY 接口模式

在 `phy_connect()` 函数族中提供的 PHY 接口模式定义了 PHY 接口的初始工作模式。这不保证保持不变；有些 PHY 可能会根据协商结果动态更改其接口模式，而无需软件交互。
下面描述了一些接口模式：

``PHY_INTERFACE_MODE_SMII``
    这是串行 MII，时钟频率为 125MHz，支持 100M 和 10M 速度。
一些详细信息可以在以下链接中找到:
https://opencores.org/ocsvn/smii/smii/trunk/doc/SMII.pdf

``PHY_INTERFACE_MODE_1000BASEX``
这定义了由802.3标准第36节规定的1000BASE-X单通道SerDes链路。该链路以固定比特率1.25Gbaud运行，采用10B/8B编码方案，从而产生1Gbps的基本数据速率。数据流中嵌入了一个16位的控制字，用于与远端协商全双工和暂停模式。这不包括“上时钟”变体，例如2.5Gbps的速度（见下文）。

``PHY_INTERFACE_MODE_2500BASEX``
这定义了一种1000BASE-X的变体，其时钟速度是802.3标准的2.5倍，从而获得一个固定的比特率3.125Gbaud。

``PHY_INTERFACE_MODE_SGMII``
这是用于Cisco SGMII的接口模式，它是根据802.3标准对1000BASE-X的一种修改。SGMII链路由一个以1.25Gbaud固定比特率运行、采用10B/8B编码的单通道SerDes组成。基本数据速率是1Gbps，而较低速度如100Mbps和10Mbps则是通过每个数据符号的重复实现的。802.3控制字被重新利用来向MAC发送协商的速度和全双工信息，并让MAC确认接收。这不包括“上时钟”变体，例如2.5Gbps的速度。
注意：在某些情况下，SGMII与1000BASE-X配置不匹配的链路可能会成功传输数据，但是16位的控制字将不能被正确解析，这可能导致全双工、暂停或其他设置的不匹配。这种情况取决于MAC和/或PHY的行为。

``PHY_INTERFACE_MODE_5GBASER``
这是IEEE 802.3第129条规定的5GBASE-R协议。它与第49条规定的10GBASE-R协议相同，只是运行频率减半。请参考IEEE标准获取详细定义。

``PHY_INTERFACE_MODE_10GBASER``
这是IEEE 802.3第49条规定的10GBASE-R协议，可用于多种不同的介质。请参考IEEE标准获取详细定义。
注意：10GBASE-R只是可以与XFI和SFI一起使用的众多协议之一。XFI和SFI允许多个协议通过单一SerDes通道，并且还规定了主机XFP/SFP连接器插入的合规板信号的电气特性。因此，XFI和SFI本身不是PHY接口类型。

``PHY_INTERFACE_MODE_10GKR``
这是IEEE 802.3第49条规定的10GBASE-R，带有第73条规定的自动协商功能。请参考IEEE标准获取更多信息。
注意：由于历史使用习惯，一些10GBASE-R的应用错误地使用了这个定义。
```PHY_INTERFACE_MODE_25GBASER```
这是IEEE 802.3 PCS子条款107定义的25GBASE-R协议。
PCS与10GBASE-R相同，即采用64B/66B编码，
运行速度提高了2.5倍，从而实现了固定的比特率25.78125 Gbaud。
更多信息请参考IEEE标准。

```PHY_INTERFACE_MODE_100BASEX```
这定义了IEEE 802.3子条款24。链路以固定的数据速率125Mbps运行，
使用4B/5B编码方案，导致基础数据速率为100Mbps。

```PHY_INTERFACE_MODE_QUSGMII```
这定义了Cisco的四通道USGMII模式，它是USGMII（通用SGMII）链路的四通道变体。
它与QSGMII非常相似，但使用包控制头（PCH）而非7字节前导来携带不仅仅是端口ID，
还有所谓的“扩展”。目前为止在规范中唯一记录的扩展是包含时间戳，
用于支持PTP的PHY。此模式与QSGMII不兼容，但在链路速度和协商方面具有相同的功能。

```PHY_INTERFACE_MODE_1000BASEKX```
这是由IEEE 802.3子条款36定义的1000BASE-X，带有子条款73的自动协商功能。
通常，它将与子条款70的PMD一起使用。为了区别于用于子条款38和39 PMD的1000BASE-X PHY模式，
此接口模式具有不同的自动协商功能，并且仅支持全双工操作。

```PHY_INTERFACE_MODE_PSGMII```
这是Penta SGMII模式，它与QSGMII类似，但将5条SGMII线路组合为一个链路，
而QSGMII为4条。

```PHY_INTERFACE_MODE_10G_QXGMII```
代表由Cisco USXGMII多端口铜线接口文档定义的10G-QXGMII PHY-MAC接口。
它支持通过10.3125 GHz SerDes通道实现4个端口，每个端口通过符号复制可达到2.5G / 1G / 100M / 10M的速度。
PCS期望的是标准的USXGMII码字。

暂停帧/流控制
===============

除了确保在MII_ADVERTISE中设置SUPPORTED_Pause和SUPPORTED_AsymPause位，
以向对端指示以太网MAC控制器支持这些特性外，PHY本身并不直接参与流控制/暂停帧的操作。
由于生成流控制/暂停帧涉及以太网MAC驱动程序，因此建议该驱动程序通过正确设置SUPPORTED_Pause和SUPPORTED_AsymPause位来适当地指示这些特性的广告和支持。
这可以在phy_connect()之前或之后进行，或者作为实现ethtool::set_pauseparam功能的结果。

密切关注PAL状态机
==================

可能PAL内置的状态机需要一点帮助来保持网络设备和PHY同步。如果需要，
你可以在连接到PHY时注册一个辅助函数，该函数将在状态机响应任何变化之前每秒被调用一次。
为此，你需要手动调用phy_attach()和phy_prepare_link()，然后使用第二个参数指向你的特殊处理程序来调用phy_start_machine()。
目前还没有如何使用此功能的例子，因此对其测试有限，因为作者没有使用该功能的驱动程序（它们都使用选项1）。所以请“买者自慎”。
自行处理一切
=====================

有极小的可能性是，PHY层抽象层(PAL)内置的状态机无法追踪PHY与网络设备之间复杂的交互。如果确实如此，您可以仅调用`phy_attach()`，而不调用`phy_start_machine`或`phy_prepare_link()`。这意味着`phydev->state`完全由您来管理（`phy_start`和`phy_stop`会在某些状态间切换，因此您可能需要避开这些函数）。
已经尽力确保即使在状态机不运行的情况下，也可以访问有用的功能，并且这些功能大多数都是从不与复杂状态机交互的函数派生而来的。
然而，再次强调，到目前为止还没有尝试对不使用状态机的情况进行测试，因此使用者请谨慎。
下面是这些函数的简要介绍：

```c
int phy_read(struct phy_device *phydev, u16 regnum);
int phy_write(struct phy_device *phydev, u16 regnum, u16 val);
```

简单的读写原语。它们会调用总线的读写函数指针。

```c
void phy_print_status(struct phy_device *phydev);
```

一个方便的函数，用于以整洁的方式打印出PHY状态。

```c
void phy_request_interrupt(struct phy_device *phydev);
```

请求PHY中断的IRQ。

```c
struct phy_device * phy_attach(struct net_device *dev, const char *phy_id, phy_interface_t interface);
```

将网络设备连接到特定的PHY上，如果没有在总线初始化期间找到合适的驱动程序，则绑定到通用驱动程序。

```c
int phy_start_aneg(struct phy_device *phydev);
```

根据`phydev`结构体内部的变量，要么配置广告信息并重置自动协商，要么禁用自动协商，并配置强制设置。

```c
static inline int phy_read_status(struct phy_device *phydev);
```

使用最新的信息填充`phydev`结构体，反映当前PHY中的设置。
``` 
int phy_ethtool_ksettings_set(struct phy_device *phydev,
                              const struct ethtool_link_ksettings *cmd);
```
Ethtool便捷函数:

```
int phy_mii_ioctl(struct phy_device *phydev,
                  struct mii_ioctl_data *mii_data, int cmd);
```
介质独立接口(MII)的ioctl。请注意，如果您写入如BMCR、BMSR、ADVERTISE等寄存器，此函数可能会完全破坏状态机。最好仅用于写入那些非标准的寄存器，并且不会触发重新协商。

### PHY 设备驱动程序

有了PHY抽象层(PHY Abstraction Layer)，添加对新PHY的支持变得非常容易。在某些情况下，甚至不需要做任何工作！然而，许多PHY需要一些特殊处理才能正常运行。

#### 通用PHY驱动程序

如果所需的PHY没有任何错误修正、特性或特殊功能需要支持，则可能最好不添加支持，而是让PHY抽象层的通用PHY驱动程序完成所有的工作。

#### 编写PHY驱动程序

如果您确实需要编写一个PHY驱动程序，首先要做的是确保它可以与适当的PHY设备匹配。
这通常是在总线初始化期间通过读取设备的UID（存储在寄存器2和3中），然后将其与每个驱动程序的`phy_id`字段进行AND操作，并与每个驱动程序的`phy_id_mask`字段进行比较来完成的。此外，它还需要一个名称。以下是一个示例：

```c
static struct phy_driver dm9161_driver = {
        .phy_id         = 0x0181b880,
        .name           = "Davicom DM9161E",
        .phy_id_mask    = 0x0ffffff0,
        ..
}
```

接下来，您需要指定您的PHY设备及其驱动程序支持哪些特性（如速度、全双工模式、自动协商等）。大多数PHY支持`PHY_BASIC_FEATURES`，但您可以在`include/mii.h`中找到其他特性。

每个驱动程序由一系列函数指针组成，这些指针在`include/linux/phy.h`中的`phy_driver`结构体中有文档说明。

其中，只有`config_aneg`和`read_status`必须由驱动程序代码分配。其余的都是可选的。并且，尽可能使用通用PHY驱动程序的这些函数版本：`genphy_read_status`和`genphy_config_aneg`。如果不可以这样做，那么很可能您只需要在这两个函数调用前后执行一些动作，因此您的函数将封装这些通用函数。

您可以自由查看`drivers/net/phy/`目录下的Marvell、Cicada和Davicom驱动程序作为例子（在本文档撰写时，lxt和qsemi驱动程序尚未经过测试）。
PHY的MMD寄存器访问默认由PAL框架处理，但如果需要也可以被特定的PHY驱动程序覆盖。如果PHY在IEEE标准化MMD PHY寄存器定义之前就已投入生产，可能会出现这种情况。大多数现代PHY能够使用通用的PAL框架来访问PHY的MMD寄存器。例如，对节能以太网（Energy Efficient Ethernet）的支持就是通过PAL实现的，这种支持使用PAL来访问MMD寄存器进行EEE查询和配置，前提是PHY支持IEEE标准访问机制；或者如果由特定的PHY驱动程序覆盖，则可以使用PHY特定的访问接口。请参考`drivers/net/phy/`目录下的Micrel驱动程序，了解如何实现这一点。

### 板级修复
有时候平台与PHY之间的具体交互需要特殊处理。例如，改变PHY的时钟输入位置，或者添加延迟来解决数据路径中的延迟问题。为了支持这些特殊情况，PHY层允许平台代码注册修复程序，在PHY启动（或后续重置）时运行。
当PHY层启动一个PHY时，会检查是否有为它注册的修复程序，匹配依据是UID（包含在PHY设备的`phy_id`字段中）和总线标识符（包含在`phydev->dev.bus_id`中）。两者都必须匹配，但提供了两个常量`PHY_ANY_ID`和`PHY_ANY_UID`作为总线ID和UID的通配符。
当找到匹配项时，PHY层将调用与修复程序关联的`run`函数。该函数将传入感兴趣PHY设备的指针，因此应该只对这个PHY操作。
平台代码可以使用`phy_register_fixup()`来注册修复程序：

```c
int phy_register_fixup(const char *phy_id,
                       u32 phy_uid, u32 phy_uid_mask,
                       int (*run)(struct phy_device *));
```

或者使用两个存根`phy_register_fixup_for_uid()`和`phy_register_fixup_for_id()`之一：

```c
int phy_register_fixup_for_uid(u32 phy_uid, u32 phy_uid_mask,
                               int (*run)(struct phy_device *));
int phy_register_fixup_for_id(const char *phy_id,
                              int (*run)(struct phy_device *));
```

存根设置两个匹配条件中的一个，并将另一个设置为匹配任何值。
当在模块加载时调用`phy_register_fixup()`或`\*_for_uid()`/\`\_for_id()`时，需要在卸载模块时取消注册修复程序并释放分配的内存。
在卸载模块前调用以下函数之一：

```c
int phy_unregister_fixup(const char *phy_id, u32 phy_uid, u32 phy_uid_mask);
int phy_unregister_fixup_for_uid(u32 phy_uid, u32 phy_uid_mask);
int phy_unregister_fixup_for_id(const char *phy_id);
```

### 标准
IEEE标准802.3：CSMA/CD访问方法和物理层规范，第二部分：
http://standards.ieee.org/getieee802/download/802.3-2008_section2.pdf

RGMII v1.3:
http://web.archive.org/web/20160303212629/http://www.hp.com/rnd/pdfs/RGMIIv1_3.pdf

RGMII v2.0:
http://web.archive.org/web/20160303171328/http://www.hp.com/rnd/pdfs/RGMIIv2_0_final_hp.pdf
