SPDX 许可证标识符：GPL-2.0

=========================================================
BusLogic MultiMaster 和 FlashPoint SCSI 驱动程序（适用于 Linux）
=========================================================

			 版本 2.0.15（适用于 Linux 2.0）

			 版本 2.1.15（适用于 Linux 2.1）

			      正式发布

				1998年8月17日

			       Leonard N. Zubkoff

			       Dandelion Digital

			       lnz@dandelion.com

	 版权所有 1995-1998 Leonard N. Zubkoff <lnz@dandelion.com>

简介
====

BusLogic, Inc. 设计并制造了多种高性能的 SCSI 主适配器，这些适配器通过其 MultiMaster ASIC 技术，在各种不同的总线架构上共享一个通用编程接口。BusLogic 在 1996 年 2 月被 Mylex Corporation 收购，但支持这些产品的驱动程序最初是在 BusLogic 名下开发的，因此在源代码和文档中保留了该名称。

此驱动程序支持所有当前的 BusLogic MultiMaster 主适配器，并且几乎不需要或不需要任何修改即可支持未来的 MultiMaster 设计。最近，BusLogic 推出了 FlashPoint 主适配器，这些适配器成本较低，并依赖主机 CPU 而不是内置处理器。尽管没有内置 CPU，FlashPoint 主适配器的性能非常好，命令延迟非常低。BusLogic 最近向我提供了 FlashPoint 驱动开发者工具包，其中包括 FlashPoint SCCB 管理器的文档和可自由分发的源代码。SCCB 管理器是运行在主机 CPU 上的一组代码库，执行与 MultiMaster 主适配器固件类似的功能。由于他们提供了 SCCB 管理器，此驱动程序现在也支持 FlashPoint 主适配器。

编写这个全新的 BusLogic 驱动程序的主要目标是实现 BusLogic SCSI 主适配器和现代 SCSI 外设所能达到的全部性能，并提供一个高度可靠的驱动程序，可以用于高性能的关键任务应用。所有主要的性能特性都可以从 Linux 内核命令行或模块初始化时进行配置，使每个安装可以根据特定需求调整驱动程序性能和错误恢复。

有关 BusLogic SCSI 主适配器 Linux 支持的最新信息，以及此驱动程序的最新版本和 BT-948/958/958D 的最新固件，都可以在我的 Linux 主页上找到，网址为 "http://sourceforge.net/projects/dandelion/"。错误报告应通过电子邮件发送至 "lnz@dandelion.com"。请随错误报告附上启动时驱动程序和 SCSI 子系统报告的完整配置消息，以及与 SCSI 操作相关的后续系统消息，并详细描述您的硬件配置。

Mylex 是一家优秀的公司，我强烈推荐他们的产品给 Linux 社区。1995 年 11 月，我有机会成为他们最新 MultiMaster 产品 BT-948 PCI Ultra SCSI 主适配器的测试站点，然后在 1996 年 1 月又成为了 BT-958 PCI Wide Ultra SCSI 主适配器的测试站点。这种合作是互利的，因为 Mylex 获得了其测试团队难以实现的测试程度和类型，而 Linux 社区则可以在产品上市之前获得经过良好测试的高性能主适配器。这种关系还让我有机会直接与他们的技术团队互动，更好地了解他们产品的内部运作，并反过来教育他们关于 Linux 社区的需求和潜力。

最近，Mylex 重申了公司对支持 Linux 社区的兴趣，我现在正在开发适用于 DAC960 PCI RAID 控制器的 Linux 驱动程序。Mylex 的兴趣和支持备受赞赏。

与其他一些供应商不同的是，如果您联系 Mylex 技术支持时遇到问题并且正在使用 Linux，他们不会告诉您您的产品使用不受支持。他们最新的产品营销文献甚至声明 “Mylex SCSI 主适配器兼容所有主要操作系统，包括：... Linux ...”。
Mylex 公司位于美国加利福尼亚州弗里蒙特市 Ardenwood 大道 34551 号，邮编 94555，电话为 510/796-6100，或通过万维网访问 http://www.mylex.com。Mylex HBA 技术支持可以通过电子邮件 techsup@mylex.com、电话 510/608-2400 或传真 510/745-7715 联系。欧洲和日本办事处的联系方式可在网站上找到。

驱动程序功能
==============

配置报告与测试
-------------------

在系统初始化期间，驱动程序会详细报告主机适配器硬件配置，包括与每个目标设备协商的同步传输参数。对于每个目标设备，将报告 AutoSCSI 设置中的同步协商、宽带协商以及断开/重新连接设置，以及标记队列的状态。如果所有目标设备都使用相同的设置，则使用一个单词或短语表示；否则，将为每个目标设备提供一个字母以指示其单独状态。以下示例应该能澄清这种报告格式：

同步协商：Ultra

同步协商对所有目标设备均启用，并且主机适配器将尝试协商每秒 20.0 兆次传输。

同步协商：Fast

同步协商对所有目标设备均启用，并且主机适配器将尝试协商每秒 10.0 兆次传输。

同步协商：Slow

同步协商对所有目标设备均启用，并且主机适配器将尝试协商每秒 5.0 兆次传输。

同步协商：Disabled

同步协商已禁用，所有目标设备仅限于异步操作。

同步协商：UFSNUUU#UUUUUUUU

同步协商至 Ultra 速度对目标设备 0 和 4 至 15 启用，至 Fast 速度对目标设备 1 启用，至 Slow 速度对目标设备 2 启用，并且对目标设备 3 不允许。主机适配器的 SCSI ID 由“#”表示。

宽带协商、断开/重新连接及标记队列的状态将被报告为“启用”、“禁用”，或一系列“Y”和“N”字母。

性能功能
-------------

BusLogic SCSI 主机适配器直接实现了 SCSI-2 标记队列，因此驱动程序中包含了利用标记队列的功能，以便与报告具有标记队列能力的任何目标设备一起使用。标记队列允许向每个目标设备或逻辑单元发出多个待处理命令，并且可以显著提高 I/O 性能。此外，BusLogic 的严格轮询模式用于优化主机适配器性能，并且分散/聚集 I/O 支持尽可能多的段数，这些段数可被 Linux I/O 子系统有效使用。通过内核命令行或模块初始化时提供的驱动程序选项，可以控制每个目标设备是否使用标记队列以及选择标记队列深度。默认情况下，队列深度根据主机适配器的总队列深度以及发现的目标设备的数量、类型、速度和能力自动确定。此外，当主机适配器固件版本已知不正确实现标记队列时，或选择标记队列深度为 1 时，标记队列将自动禁用。如果禁用了目标设备的断开/重新连接，则也会禁用该设备的标记队列。
### 强健性特性
-------------------

驱动程序实现了广泛的错误恢复程序。当SCSI子系统的高层部分请求重置超时命令时，将根据SCSI子系统的建议选择全主机适配器硬重置和SCSI总线重置，还是向单个目标设备发送总线设备重置消息。错误恢复策略可以通过驱动选项为每个目标设备单独选择，并且包括向与被重置的命令相关的特定目标设备发送总线设备重置消息，以及完全抑制错误恢复以避免干扰故障设备。如果选择了总线设备重置错误恢复策略，并且发送总线设备重置无法恢复正确操作，则下一个被重置的命令将强制执行全主机适配器硬重置和SCSI总线重置。由其他设备引起的并被主机适配器检测到的SCSI总线重置也将通过向主机适配器发出软重置并重新初始化来处理。最后，如果标记队列处于活动状态，并且在10分钟内发生多次命令重置，或者在运行的前10分钟内发生命令重置，则将禁用该目标设备上的标记队列。这些错误恢复选项通过防止个别故障设备导致整个系统锁定或崩溃，从而允许在移除问题组件后进行干净的关机和重启，从而提高了整体系统的强健性。

### PCI配置支持
-------------------------

在编译了包含PCI BIOS支持的内核的PCI系统上，此驱动程序将查询PCI配置空间，并使用系统BIOS分配的I/O端口地址，而不是ISA兼容的I/O端口地址。然后，驱动程序会禁用ISA兼容的I/O端口地址。在PCI系统中，还建议使用AutoSCSI工具完全禁用ISA兼容的I/O端口，因为这并不是必要的。在BT-948/958/958D上，默认情况下禁用ISA兼容的I/O端口。

### `/proc`文件系统支持
-------------------------

主机适配器配置信息的副本以及更新的数据传输和错误恢复统计信息可通过`/proc/scsi/BusLogic/<N>`接口获取。

### 共享中断支持
-------------------------

在支持共享中断的系统上，任何数量的BusLogic主机适配器可以共享同一个中断请求通道。

### 支持的主机适配器
=======================

以下列表包含了截至本文档发布日期所支持的BusLogic SCSI主机适配器。建议任何购买不在下表中的BusLogic主机适配器的人事先联系作者以确认其是否受支持或即将受支持。

**FlashPoint 系列 PCI 主机适配器：**

| 型号 | 描述 |
|------|------|
| FlashPoint LT (BT-930) | Ultra SCSI-3 |
| FlashPoint LT (BT-930R) | Ultra SCSI-3 with RAIDPlus |
| FlashPoint LT (BT-920) | Ultra SCSI-3 (BT-930 without BIOS) |
| FlashPoint DL (BT-932) | Dual Channel Ultra SCSI-3 |
| FlashPoint DL (BT-932R) | Dual Channel Ultra SCSI-3 with RAIDPlus |
| FlashPoint LW (BT-950) | Wide Ultra SCSI-3 |
| FlashPoint LW (BT-950R) | Wide Ultra SCSI-3 with RAIDPlus |
| FlashPoint DW (BT-952) | Dual Channel Wide Ultra SCSI-3 |
| FlashPoint DW (BT-952R) | Dual Channel Wide Ultra SCSI-3 with RAIDPlus |

**MultiMaster "W" 系列主机适配器：**

| 型号 | 接口 | 描述 |
|------|------|------|
| BT-948 | PCI | Ultra SCSI-3 |
| BT-958 | PCI | Wide Ultra SCSI-3 |
| BT-958D | PCI | Wide Differential Ultra SCSI-3 |

**MultiMaster "C" 系列主机适配器：**

| 型号 | 接口 | 描述 |
|------|------|------|
| BT-946C | PCI | Fast SCSI-2 |
| BT-956C | PCI | Wide Fast SCSI-2 |
| BT-956CD | PCI | Wide Differential Fast SCSI-2 |
| BT-445C | VLB | Fast SCSI-2 |
| BT-747C | EISA | Fast SCSI-2 |
| BT-757C | EISA | Wide Fast SCSI-2 |
| BT-757CD | EISA | Wide Differential Fast SCSI-2 |

**MultiMaster "S" 系列主机适配器：**

| 型号 | 接口 | 描述 |
|------|------|------|
| BT-445S | VLB | Fast SCSI-2 |
| BT-747S | EISA | Fast SCSI-2 |
| BT-747D | EISA | Differential Fast SCSI-2 |
| BT-757S | EISA | Wide Fast SCSI-2 |
| BT-757D | EISA | Wide Differential Fast SCSI-2 |
| BT-742A | EISA | SCSI-2 (742A revision H) |

**MultiMaster "A" 系列主机适配器：**

| 型号 | 接口 | 描述 |
|------|------|------|
| BT-742A | EISA | SCSI-2 (742A revisions A - G) |

真正是BusLogic MultiMaster克隆的AMI FastDisk主机适配器也受到此驱动程序的支持。

BusLogic SCSI主机适配器既可作为裸板出售，也可作为零售套装出售。上面列出的BT-型号是指裸板包装。零售套装的型号是将上述列表中的BT-替换为KT-。零售套装包括裸板、手册以及未随裸板提供的电缆、驱动介质和文档。
FlashPoint 安装说明
=============================

RAIDPlus 支持
----------------

  FlashPoint 主机适配器现在包括了 Mylex 的可引导软件 RAID——RAIDPlus。RAIDPlus 不支持 Linux，并且没有计划支持它。Linux 2.0 中的 MD 驱动程序提供了级联（LINEAR）和条带化（RAID-0）功能，而镜像（RAID-1）、固定奇偶校验（RAID-4）以及分布式奇偶校验（RAID-5）的支持则单独提供。内置的 Linux RAID 支持通常更灵活且预期性能更好，因此在 BusLogic 驱动程序中包含 RAIDPlus 支持的动力不足。

启用 UltraSCSI 传输
----------------------------

  FlashPoint 主机适配器出厂时配置为“工厂默认”设置，这些设置较为保守，不允许进行 UltraSCSI 速度协商。这减少了在系统中安装这些主机适配器时可能出现的问题，特别是在电缆或终止不适用于 UltraSCSI 操作的情况下，或者现有 SCSI 设备不能正确响应 UltraSCSI 速度的同步传输协商。可以使用 AutoSCSI 加载“最佳性能”设置，以允许与所有设备进行 UltraSCSI 速度协商，或者单独启用 UltraSCSI 速度。建议在加载“最佳性能”设置后手动禁用 SCAM。

BT-948/958/958D 安装说明
==================================

BT-948/958/958D PCI Ultra SCSI 主机适配器具有一些可能需要在某些情况下注意的功能，当安装 Linux 时。

PCI I/O 端口分配
------------------------

  当配置为工厂默认设置时，BT-948/958/958D 只会识别主板的 PCI BIOS 分配的 PCI I/O 端口。BT-948/958/958D 不会响应任何先前 BusLogic SCSI 主机适配器响应的 ISA 兼容 I/O 端口。此驱动程序支持 PCI I/O 端口分配，因此这是首选配置。

然而，如果出于某种原因必须使用过时的 BusLogic 驱动程序（例如，在启动内核中尚未使用此驱动程序的 Linux 发行版），BusLogic 提供了一个 AutoSCSI 配置选项来启用一个遗留的 ISA 兼容 I/O 端口。

要启用此向后兼容性选项，请在系统启动时通过 Ctrl-B 调用 AutoSCSI 实用程序并选择“适配器配置”，“查看/修改配置”，然后将“ISA 兼容端口”设置从“禁用”更改为“主”或“备用”。一旦安装了此驱动程序，“ISA 兼容端口”选项应重新设置为“禁用”，以避免将来可能发生的 I/O 端口冲突。较旧的 BT-946C/956C/956CD 也有此配置选项，但工厂默认设置是“主”。

PCI 插槽扫描顺序
-----------------------

  在具有多个 BusLogic PCI 主机适配器的系统中，与 BT-946C/956C/956CD 相比，BT-948/958/958D 的 PCI 插槽扫描顺序可能会出现相反的情况。为了使从 SCSI 磁盘引导能够正常工作，主机适配器的 BIOS 和内核必须对哪个磁盘是引导设备达成一致，这就要求它们识别 PCI 主机适配器的顺序相同。主板的 PCI BIOS 提供了一种标准的方式来枚举 PCI 主机适配器，Linux 内核也使用这种方法。一些 PCI BIOS 实现按照递增的总线编号和设备编号顺序枚举 PCI 插槽，而其他实现则按相反方向枚举。

不幸的是，微软决定 Windows 95 总是以递增的总线编号和设备编号顺序枚举 PCI 插槽，无论 PCI BIOS 枚举顺序如何，并且要求主机适配器的 BIOS 支持其方案才能获得 Windows 95 认证。因此，BT-948/958/958D 的工厂默认设置按照递增的总线编号和设备编号顺序枚举主机适配器。要禁用此功能，请在系统启动时通过 Ctrl-B 调用 AutoSCSI 实用程序并选择“适配器配置”，“查看/修改配置”，按 Ctrl-F10，然后将“使用总线和设备号进行 PCI 扫描序”选项更改为关闭。

此驱动程序将查询 PCI 扫描序列设置，以便以与主机适配器的 BIOS 枚举相同的顺序识别主机适配器。
启用UltraSCSI传输
----------------------------

BT-948/958/958D出厂时配置设置为“工厂默认”设置，这些设置较为保守，不允许进行UltraSCSI速度协商。这在系统中安装了这些主机适配器，并且电缆或终止不足以支持UltraSCSI操作，或者现有的SCSI设备不能正确响应UltraSCSI速度的同步传输协商时，可以减少问题的发生。可以使用AutoSCSI加载“最佳性能”设置，允许与所有设备进行UltraSCSI速度协商，或者单独启用UltraSCSI速度。建议在加载“最佳性能”设置后手动禁用SCAM。

驱动选项
==============

BusLogic驱动选项可以通过Linux内核命令行或通过可加载内核模块安装工具来指定。多个主机适配器的驱动选项可以通过分号分隔选项字符串，或在命令行上指定多个“BusLogic=”字符串来指定。单个主机适配器的单独选项通过逗号分隔。探测和调试选项适用于所有主机适配器，而其余选项仅适用于所选的主机适配器。
BusLogic驱动探测选项包括以下内容：

NoProbe

  “NoProbe”选项禁用所有探测，因此不会检测到任何BusLogic主机适配器。
NoProbePCI

  “NoProbePCI”选项禁用对PCI配置空间的查询，因此只能检测到ISA多主适配器以及将其ISA兼容I/O端口设置为“主要”或“备用”的PCI多主适配器。
NoSortPCI

  “NoSortPCI”选项强制PCI多主适配器按照PCI BIOS提供的顺序枚举，忽略任何AutoSCSI“使用总线和设备#进行PCI扫描序”的设置。
MultiMasterFirst

  “MultiMasterFirst”选项强制多主适配器在FlashPoint适配器之前进行探测。默认情况下，如果同时存在FlashPoint和PCI多主适配器，除非BIOS的主要磁盘由第一个PCI多主适配器控制，否则该驱动会先探测FlashPoint适配器。
FlashPointFirst

  “FlashPointFirst”选项强制FlashPoint适配器在多主适配器之前进行探测。

BusLogic驱动标签队列选项允许显式指定每个目标设备（假设目标设备支持标签队列）的队列深度以及是否允许标签队列。队列深度是指允许并发执行的SCSI命令的数量（无论是向主机适配器还是目标设备）。请注意，显式启用标签队列可能会导致问题；提供启用或禁用标签队列的选项主要是为了允许在不正确实现标签队列的目标设备上禁用它。可用的选项如下：

QueueDepth:<integer>

  “QueueDepth:”或“QD:”选项指定了支持标签队列的所有目标设备的队列深度，以及不支持标签队列的设备的最大队列深度。如果没有提供队列深度选项，则队列深度将根据主机适配器的总队列深度以及检测到的目标设备的数量、类型、速度和能力自动确定。不支持标签队列的目标设备始终将其队列深度设置为BusLogic_UntaggedQueueDepth或BusLogic_UntaggedQueueDepthBB，除非提供了更低的队列深度选项。队列深度为1会自动禁用标签队列。
QueueDepth:[<integer>,<integer>,...]

  “QueueDepth:[...]”或“QD:[...]”选项分别为每个目标设备指定队列深度。如果省略了<integer>，则相关的目标设备将自动选择其队列深度。
TaggedQueuing:Default

  “TaggedQueuing:Default”或“TQ:Default”选项根据BusLogic主机适配器的固件版本以及队列深度是否允许排队多个命令来允许标签队列。
TaggedQueuing:Enable

  “TaggedQueuing:Enable”或“TQ:Enable”选项为该主机适配器上的所有目标设备启用标记队列，覆盖任何基于主机适配器固件版本的限制。

TaggedQueuing:Disable

  “TaggedQueuing:Disable”或“TQ:Disable”选项禁用该主机适配器上所有目标设备的标记队列。

TaggedQueuing:<Target-Spec>

  “TaggedQueuing:<Target-Spec>”或“TQ:<Target-Spec>”选项分别控制每个目标设备的标记队列。 <Target-Spec>是一串“Y”，“N”和“X”字符。“Y”启用标记队列，“N”禁用标记队列，“X”根据固件版本接受默认设置。第一个字符指的是目标设备0，第二个字符指的是目标设备1，依此类推；如果“Y”，“N”和“X”字符序列没有涵盖所有目标设备，则假定未指定的字符为“X”。

BusLogic驱动程序的其他选项包括以下内容：

BusSettleTime:<seconds>

  “BusSettleTime:”或“BST:”选项指定了总线稳定时间（以秒为单位）。总线稳定时间是在主机适配器硬复位（触发SCSI总线复位）与发出任何SCSI命令之间等待的时间。如果不指定，默认值为BusLogic_DefaultBusSettleTime。

InhibitTargetInquiry

  “InhibitTargetInquiry”选项禁止在多主控主机适配器上执行查询目标设备或查询已安装设备的命令。对于某些较旧的目标设备，在逻辑单元高于0时不能正确响应时，这可能是必要的。

BusLogic驱动程序的调试选项包括以下内容：

TraceProbe

  “TraceProbe”选项启用主机适配器探测的跟踪。

TraceHardwareReset

  “TraceHardwareReset”选项启用主机适配器硬件复位的跟踪。

TraceConfiguration

  “TraceConfiguration”选项启用主机适配器配置的跟踪。

TraceErrors

  “TraceErrors”选项启用从目标设备返回错误的SCSI命令的跟踪。对于每个失败的SCSI命令，将打印CDB和Sense数据。

Debug

  “Debug”选项启用所有调试选项。
以下示例演示了如何为第一个主机适配器上的目标设备1和2设置队列深度为7和15，为第二个主机适配器上的所有目标设备设置队列深度为31，并将第二个主机适配器的总线稳定时间设置为30秒。

Linux 内核命令行：

```
linux BusLogic=QueueDepth:[,7,15];QueueDepth:31,BusSettleTime:30
```

LILO Linux 引导加载程序（在 `/etc/lilo.conf` 中）：

```
append = "BusLogic=QueueDepth:[,7,15];QueueDepth:31,BusSettleTime:30"
```

INSMOD 可加载内核模块安装工具：

```
insmod BusLogic.o \
    'BusLogic="QueueDepth:[,7,15];QueueDepth:31,BusSettleTime:30"'
```

.. 注意 ::

      需要使用版本2.1.71或更高版本的模块工具来正确解析包含逗号的驱动选项。

驱动安装
========

此发行版是为Linux内核版本2.0.35准备的，但应该与2.0.4或任何后续的2.0系列内核兼容。
为了安装新的BusLogic SCSI驱动，请使用以下命令，并将“/usr/src”替换为你保存Linux内核源代码树的位置：

```
cd /usr/src
tar -xvzf BusLogic-2.0.15.tar.gz
mv README.* LICENSE.* BusLogic.[ch] FlashPoint.c linux/drivers/scsi
patch -p0 < BusLogic.patch （仅适用于2.0.33及更早版本）
cd linux
make config
make zImage
```

然后将“arch/x86/boot/zImage”作为标准内核进行安装，如果需要的话运行lilo并重启。

BusLogic 公告邮件列表
=====================

BusLogic 公告邮件列表提供了一个论坛，用于通知Linux用户有关新驱动发布和其他关于BusLogic SCSI主机适配器Linux支持的公告。要加入邮件列表，请发送一封邮件到 “buslogic-announce-request@dandelion.com”，并在邮件正文中包含一行“subscribe”。
