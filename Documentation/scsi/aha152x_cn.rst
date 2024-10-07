```
SPDX 许可证标识符: GPL-2.0
包含文件: <isonum.txt>

=====================================================
适用于 Linux 的 Adaptec AHA-1520/1522 SCSI 驱动程序 (aha152x)
=====================================================

版权所有 © 1993-1999 Jürgen Fischer <fischer@norbit.de>

TC1550 补丁由 Luuk van Dijk (ldz@xs4all.nl) 提供


在修订版 2 中，驱动程序进行了大量修改（特别是底部处理程序 complete()）
现在的驱动程序更干净了，并且支持 2.3 版本中的新错误处理代码，产生的 CPU 负载更少（减少了轮询循环），吞吐量略高（至少在我的老旧测试机上；一台 i486/33MHz/20MB）
配置参数
=======================

============  ========================================  ======================
IOPORT        基础 I/O 地址                             (0x340/0x140)
IRQ           中断级别                                 (9-12；默认 11)
SCSI_ID       控制器的 SCSI ID                         (0-7；默认 7)
RECONNECT     允许目标从总线断开连接                    (0/1；默认 1 [开启])
PARITY        启用奇偶校验                              (0/1；默认 1 [开启])
SYNCHRONOUS   启用同步传输                              (0/1；默认 1 [开启])
DELAY:        总线重置延迟                              (默认 100)
EXT_TRANS:    启用扩展转换                              (0/1：默认 0 [关闭])
              （参见注意事项）
============  ========================================  ======================

编译时配置
==========================

（进入 drivers/scsi/Makefile 中的 AHA152X）：

- DAUTOCONF
    使用控制器报告的配置（仅限 AHA-152x）

- DSKIP_BIOSTEST
    不检测 BIOS 签名（AHA-1510 或禁用的 BIOS）

- DSETUP0="{ IOPORT, IRQ, SCSI_ID, RECONNECT, PARITY, SYNCHRONOUS, DELAY, EXT_TRANS }"
    第一个控制器的覆盖配置

- DSETUP1="{ IOPORT, IRQ, SCSI_ID, RECONNECT, PARITY, SYNCHRONOUS, DELAY, EXT_TRANS }"
    第二个控制器的覆盖配置

- DAHA152X_DEBUG
    启用调试输出

- DAHA152X_STAT
    启用一些统计信息


LILO 命令行选项
=========================

::

    aha152x=<IOPORT>[,<IRQ>[,<SCSI-ID>[,<RECONNECT>[,<PARITY>[,<SYNCHRONOUS>[,<DELAY> [,<EXT_TRANS]]]]]]]

通过指定命令行可以覆盖常规配置
当您这样做时，将跳过 BIOS 测试。输入的值必须是有效的（已知的）。不要使用在正常操作中不支持的值。如果您认为需要其他值，请联系我。
对于两个控制器，请两次使用 aha152x 语句
模块配置符号
================================

选择两种替代方案之一：

1. 指定所有内容（旧方法）::

    aha152x=IOPORT,IRQ,SCSI_ID,RECONNECT,PARITY,SYNCHRONOUS,DELAY,EXT_TRANS

  第一个控制器的配置覆盖

  ::

    aha152x1=IOPORT,IRQ,SCSI_ID,RECONNECT,PARITY,SYNCHRONOUS,DELAY,EXT_TRANS

  第二个控制器的配置覆盖

2. 只指定所需的内容（需要 irq 或 io；新方法）

io=IOPORT0[,IOPORT1]
  第一个和第二个控制器的 IOPORT

irq=IRQ0[,IRQ1]
  第一个和第二个控制器的 IRQ

scsiid=SCSIID0[,SCSIID1]
  第一个和第二个控制器的 SCSIID

reconnect=RECONNECT0[,RECONNECT1]
  第一个和第二个控制器允许目标断开连接

parity=PAR0[PAR1]
  第一个和第二个控制器使用奇偶校验

sync=SYNCHRONOUS0[,SYNCHRONOUS1]
  第一个和第二个控制器启用同步传输

delay=DELAY0[,DELAY1]
  第一个和第二个控制器的重置延迟

exttrans=EXTTRANS0[,EXTTRANS1]
  第一个和第二个控制器启用扩展转换

如果同时使用这两种替代方案，则采用第一种方案
关于 EXT_TRANS 的说明
==================

SCSI 使用块号来寻址设备上的块/扇区
BIOS 使用柱面/磁头/扇区寻址方案（C/H/S）
DOS 需要一个理解这种 C/H/S 寻址的 BIOS 或驱动程序
柱面数/磁头数/扇区数称为几何参数，并作为 C/H/S 寻址请求的基础。SCSI 只知道磁盘的总容量（以块为单位）
因此，SCSI BIOS/DOS 驱动程序必须计算一个逻辑/虚拟几何参数，以便能够支持这种寻址方案。SCSI BIOS 返回的几何参数只是一个计算结果，与磁盘的实际/物理几何参数无关（通常情况下这并不重要）
```
基本上，这对 Linux 没有任何影响，因为它也使用块地址而不是柱面/磁头/扇区（C/H/S）地址。不幸的是，C/H/S 地址也被用于分区表中，因此每个操作系统都需要知道正确的几何参数才能解释它。

此外，C/H/S 地址方案有一定的限制，即地址空间最多限制为 255 个磁头、63 个扇区和最多 1023 个柱面。
AHA-1522 BIOS 通过将磁头数量固定为 64，扇区数量固定为 32，并通过将磁盘报告的容量除以 64*32（1 MB）来计算柱面数量来确定几何参数。这被认为是默认的转换方式。
对于使用 C/H/S 的 1023 个柱面的限制，你只能在分区表中寻址磁盘的第一个 GB。因此，基于 AIC-6260/6360 控制器的一些较新的 BIOS 支持扩展转换。这意味着当 BIOS 看到大于 1 GB 的磁盘时，它会将磁头数设为 255，扇区数设为 63，然后将磁盘的容量除以 255*63（约 8 MB）。这导致分区表中最大可寻址的磁盘空间约为 8 GB（但现在已经有了更大的磁盘）。
为了使事情更加复杂，在某些 BIOS 设置中，转换模式可能可以配置也可能不可以配置。
该驱动程序进行了一些或多或少安全的猜测，以便在大多数情况下正确获取几何参数：

- 对于小于 1 GB 的磁盘：使用默认转换（C/32/64）

- 对于大于 1 GB 的磁盘：

  - 从分区表中获取当前几何参数（使用 scsicam_bios_param 并且只接受‘有效’的几何参数，即要么是（C/32/64），要么是（C/63/255）。这可能是扩展转换，即使在驱动程序中未启用也是如此）
  - 如果这失败了，则如果由覆盖、内核或模块参数启用，则采用扩展转换，否则采用默认转换并请求用户验证。这可能会在尚未分区的磁盘上发生

参考文献
========

"AIC-6260 SCSI Chip Specification", Adaptec Corporation
"SCSI COMPUTER SYSTEM INTERFACE - 2 (SCSI-2)", X3T9.2/86-109 rev. 10h

"Writing a SCSI device driver for Linux", Rik Faith (faith@cs.unc.edu)

"Kernel Hacker's Guide", Michael K. Johnson (johnsonm@sunsite.unc.edu)

"Adaptec 1520/1522 User's Guide", Adaptec Corporation
迈克尔·K·约翰逊 (johnsonm@sunsite.unc.edu)

德鲁·埃克哈特 (drew@cs.colorado.edu)

埃里克·杨格代尔 (eric@andante.org)

特别感谢埃里克·杨格代尔免费提供芯片文档！
