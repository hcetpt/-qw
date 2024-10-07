SPDX 许可证标识符: GPL-2.0

===================================
BusLogic FlashPoint SCSI 驱动程序
===================================

BusLogic FlashPoint SCSI 主机适配器现在在 Linux 上得到完全支持
下述的升级计划已于 1997 年 3 月 31 日正式终止，因为已不再需要
::

    MYLEX 推出其 BusLogic FlashPoint 系列 SCSI 主机适配器的 Linux 操作系统支持

  加利福尼亚州弗里蒙特 —— 1996 年 10 月 8 日 —— Mylex 公司扩展了其 BusLogic 品牌 FlashPoint Ultra SCSI 主机适配器对 Linux 操作系统的支持。BusLogic 的其他所有 SCSI 主机适配器，包括 MultiMaster 系列，目前也支持 Linux 操作系统。Linux 驱动程序和相关信息将于 10 月 15 日在 http://sourceforge.net/projects/dandelion/ 发布。
“Mylex 致力于支持 Linux 社区，”Mylex 营销副总裁 Peter Shambora 表示。“我们多年来一直支持 Linux 驱动程序的开发，并为我们的主机适配器提供技术支持，很高兴现在能够将我们的 FlashPoint 产品提供给这一用户群体。”

Linux 操作系统
==========================

Linux 是为 Intel x86、Sun SPARC、SGI MIPS、Motorola 68k、Digital Alpha AXP 和 Motorola PowerPC 机器设计的免费分发的 UNIX 实现。它支持广泛的软件，包括 X Window 系统、Emacs 和 TCP/IP 网络。更多信息请访问 http://www.linux.org 和 http://www.ssc.com/
FlashPoint 主机适配器
========================

专为工作站和文件服务器环境设计的 FlashPoint Ultra SCSI 主机适配器系列提供窄带、宽带、双通道和双通道宽带版本。这些适配器采用 SeqEngine 自动化技术，最大限度地减少了 SCSI 命令开销并减少了生成到 CPU 的中断数量。
关于 Mylex
===========

Mylex 公司（纳斯达克代码：MYLX），成立于 1983 年，是 RAID 技术和网络管理产品的领先生产商。该公司生产高性能磁盘阵列（RAID）控制器及配套计算机产品，适用于网络服务器、大规模存储系统、工作站和系统板。通过其广泛的 RAID 控制器和 BusLogic Ultra SCSI 主机适配器产品线，Mylex 提供了增强智能 I/O 技术，增加了网络管理控制，提高了 CPU 利用率，优化了 I/O 性能，并确保了数据的安全性和可用性。产品通过 OEM、主要分销商、VAR 和系统集成商在全球范围内销售。Mylex 公司总部位于加利福尼亚州弗里蒙特市 Ardenwood 大道 34551 号。
联系人：
========

::

  Peter Shambora
  营销副总裁
  Mylex 公司
510/796-6100
  peters@mylex.com


::

			       公告
	       BusLogic FlashPoint LT/BT-948 升级计划
			      1996 年 2 月 1 日

			  进一步公告
	       BusLogic FlashPoint LW/BT-958 升级计划
			       1996 年 6 月 14 日

自去年十月推出以来，BusLogic FlashPoint LT 对 Linux 社区成员来说一直存在问题，因为没有适用于这款新 Ultra SCSI 产品的 Linux 驱动程序。尽管该产品被官方定位为桌面工作站产品，并不太适合像 Linux 这样的高性能多任务操作系统，但计算机系统供应商却将其吹捧为最新产品，并且甚至在其高端系统中也仅配备 FlashPoint LT 而不是较旧的 MultiMaster 产品。这导致许多误以为所有 BusLogic SCSI 主机适配器都支持 Linux 的用户购买了系统后才发现 FlashPoint 不受支持，而且短期内也不会获得支持，甚至可能永远得不到支持。
在发现这个问题后，BusLogic 联系了其主要 OEM 客户，以确保仍会提供 BT-946C/956C MultiMaster 卡，并使误购了 FlashPoint 的 Linux 用户能够升级到 BT-946C。虽然这对许多新系统购买者有所帮助，但这只是部分解决了 FlashPoint 支持 Linux 用户的整体问题。它并没有帮助那些最初为了一个受支持的操作系统购买 FlashPoint 后决定运行 Linux 的用户，或者那些误以为 FlashPoint 受支持而无法退货的用户。
12 月中旬，我请求与 BusLogic 的高级管理层会面，讨论与 Linux 和自由软件支持相关的 FlashPoint 问题。关于 BusLogic 对 Linux 社区态度的各种传言公开流传，我认为最好直接解决这些问题。我在一天晚上 11 点多发了一封电子邮件，并在第二天下午召开了会议。不幸的是，公司的运作有时很慢，特别是在公司被收购期间，因此直到现在才确定所有细节并能够公开声明。
BusLogic 目前尚未准备好发布第三方编写 FlashPoint 驱动程序所需的信息。现有的所有 FlashPoint 驱动程序都是由 BusLogic 工程部直接编写的，并且没有足够详细的文档能让外部开发者在没有大量协助的情况下编写驱动程序。尽管 BusLogic 内部有一些人不愿意公开 FlashPoint 架构的细节，但这一问题尚未得出定论。无论如何，即使今天有可用的文档，要编写一个可用的驱动程序也需要相当长的时间，特别是我不确定这是否值得付出如此多的努力。

然而，BusLogic 依然致力于为 Linux 社区提供高性能的 SCSI 解决方案，并不希望看到任何人因为拥有 FlashPoint LT 而无法运行 Linux。因此，BusLogic 推出了一个直接升级计划，允许全球任何 Linux 用户用他们的 FlashPoint LT 交换新的 BT-948 MultiMaster PCI Ultra SCSI 主机适配器。BT-948 是 BT-946C 的 Ultra SCSI 后继产品，它结合了 BT-946C 和 FlashPoint LT 的最佳特性，包括智能终结和用于轻松固件更新的闪存 PROM，并且当然与当前的 Linux 驱动程序兼容。此次升级的价格定为 45 美元外加运费和手续费，升级计划将通过 BusLogic 技术支持部门进行管理，可以通过电子邮件 techsup@buslogic.com、电话 +1 408 654-0760 或传真 +1 408 492-1542 联系技术支持。

截至 1996 年 6 月 14 日，最初的 BusLogic FlashPoint LT 至 BT-948 升级计划已扩展至涵盖 FlashPoint LW Wide Ultra SCSI 主机适配器。全球任何 Linux 用户都可以用他们的 FlashPoint LW（BT-950）交换 BT-958 MultiMaster PCI Ultra SCSI 主机适配器。此次升级的价格定为 65 美元外加运费和手续费。

我是 BT-948/958 的测试站点之一，我的 BusLogic 驱动程序版本 1.2.1 和 1.3.1 已经包含了对 BT-948/958 的潜在支持。后续版本中增加了对 Ultra SCSI MultiMaster 卡的更多外观支持。由于这种合作测试过程，发现了几个固件错误并进行了修正。我的高负载 Linux 测试系统为测试生产环境中很少使用的错误恢复过程提供了理想的环境，这些过程对于整个系统的稳定性至关重要。能够直接与他们的固件工程师合作，在固件调试环境中展示这些问题非常方便；自从我上次为嵌入式系统工作以来，事情确实有了很大的进展。目前我正在进行一些性能测试，预计不久后会有数据报告。

BusLogic 请求我发送此公告，因为大部分关于 FlashPoint 支持的问题要么直接通过电子邮件发送给我，要么出现在我参与的 Linux 新闻组中。总结一下，BusLogic 为 Linux 用户提供了一项升级服务：从不受支持的 FlashPoint LT（BT-930）升级到受支持的 BT-948，价格为 45 美元外加运费和手续费，或从不受支持的 FlashPoint LW（BT-950）升级到受支持的 BT-958，价格为 65 美元外加运费和手续费。

请联系 BusLogic 技术支持 techsup@buslogic.com 或拨打 +1 408 654-0760 以利用此优惠。

Leonard N. Zubkoff  
lnz@dandelion.com
