SPDX 许可证标识符: GPL-2.0

=========================
3Com Vortex 设备驱动程序
=========================

安德鲁·莫顿

2000年4月30日

本文档描述了用于 Linux 的 3Com "Vortex" 设备驱动程序 3c59x.c 的使用方法和注意事项。该驱动程序由唐纳德·贝克尔编写 <becker@scyld.com>。

唐纳德不再是此版本驱动程序的主要维护者。
请将问题报告给以下人员之一：

- 安德鲁·莫顿
- Netdev 邮件列表 <netdev@vger.kernel.org>
- Linux 内核邮件列表 <linux-kernel@vger.kernel.org>

请注意文档末尾的“报告和诊断问题”部分。
自从内核 2.3.99-pre6 版本起，此驱动程序已整合对以前由 3c575_cb.c 处理的 3c575 系列 Cardbus 卡的支持。
此驱动程序支持以下硬件：

- 3c590 Vortex 10Mbps
- 3c592 EISA 10Mbps Demon/Vortex
- 3c597 EISA Fast Demon/Vortex
- 3c595 Vortex 100baseTx
- 3c595 Vortex 100baseT4
- 3c595 Vortex 100base-MII
- 3c900 Boomerang 10baseT
- 3c900 Boomerang 10Mbps Combo
- 3c900 Cyclone 10Mbps TPO
- 3c900 Cyclone 10Mbps Combo
- 3c900 Cyclone 10Mbps TPC
- 3c900B-FL Cyclone 10base-FL
- 3c905 Boomerang 100baseTx
- 3c905 Boomerang 100baseT4
- 3c905B Cyclone 100baseTx
- 3c905B Cyclone 10/100/BNC
- 3c905B-FX Cyclone 100baseFx
- 3c905C Tornado
- 3c920B-EMB-WNM (ATI Radeon 9100 IGP)
- 3c980 Cyclone
- 3c980C Python-T
- 3cSOHO100-TX Hurricane
- 3c555 Laptop Hurricane
- 3c556 Laptop Tornado
- 3c556B Laptop Hurricane
- 3c575 [Megahertz] 10/100 LAN CardBus
- 3c575 Boomerang CardBus
- 3CCFE575BT Cyclone CardBus
- 3CCFE575CT Tornado CardBus
- 3CCFE656 Cyclone CardBus
- 3CCFEM656B Cyclone+Winmodem CardBus
- 3CXFEM656C Tornado+Winmodem CardBus
- 3c450 HomePNA Tornado
- 3c920 Tornado
- 3c982 Hydra Dual Port A
- 3c982 Hydra Dual Port B
- 3c905B-T4
- 3c920B-EMB-WNM Tornado

模块参数
=================

加载驱动程序模块时可以提供几个参数。这些参数通常放在 `/etc/modprobe.d/*.conf` 配置文件中。示例如下：

    options 3c59x debug=3 rx_copybreak=300

如果您正在使用 PCMCIA 工具（cardmgr），则可以在 `/etc/pcmcia/config.opts` 中放置选项：

    module "3c59x" opts "debug=3 rx_copybreak=300"

支持的参数包括：

debug=N

  其中 N 是从 0 到 7 的数字。大于 3 的值会在系统日志中产生大量输出。默认值为 debug=1。
options=N1,N2,N3,...

  列表中的每个数字都为相应的网络卡提供一个选项。例如，如果您有两张 3c905 卡，并希望为它们提供选项 0x204，则可以使用：

    options=0x204,0x204

  各个选项由多个位字段组成，其含义如下：

  可能的媒体类型设置

	==	=================================
	0	10baseT
	1	10Mbs AUI
	2	未定义
	3	10base2 (BNC)
	4	100base-TX
	5	100base-FX
	6	MII (Media Independent Interface)
	7	使用 EEPROM 中的默认设置
	8       自动协商
	9       外部 MII
	10      使用 EEPROM 中的默认设置
	==	=================================

  在生成 `options` 设置的值时，可以将上述媒体选择值与以下值进行或运算（或相加）：

  ======  =============================================
  0x8000  将驱动程序调试级别设置为 7
  0x4000  将驱动程序调试级别设置为 2
  0x0400  启用 Wake-on-LAN
  0x0200  强制全双工模式
  0x0010  总线主控启用位（仅适用于旧版 Vortex 卡）
  ======  =============================================

  例如：

    insmod 3c59x options=0x204

  将强制使用全双工 100base-TX 而不是允许常规自动协商。
global_options=N

  为机器中的所有 3c59x 网络接口卡设置 `options` 参数。
在上面的 `options` 数组中的条目将覆盖任何对此的设置。
这段英文描述可以翻译为：

`full_duplex=N1,N2,N3...`
类似于 `options` 中的第9位。此选项强制将对应的网卡设置为全双工模式。建议优先使用这种方式而不是 `options` 参数。
事实上，请尽量不要直接使用这个选项！最好确保自动协商功能能够正常工作。
`global_full_duplex=N1`

对于机器上的所有 3c59x 网卡，设置全双工模式。在上面 `full_duplex` 数组中的任何条目都会覆盖此设置。
`flow_ctrl=N1,N2,N3...`
启用 802.3x MAC 层流控制。3Com 网卡仅支持 PAUSE 命令，这意味着如果它们从链路伙伴接收到 PAUSE 帧时，会暂时停止发送数据包一段时间。
驱动程序只允许在处于全双工模式的链路上进行流控制。
此功能似乎不适用于 3c905 系列，仅测试了 3c905B 和 3c905C。
3Com 网卡似乎仅响应发送到保留的目标地址 01:80:c2:00:00:01 的 PAUSE 帧。它们不会处理发送到站点 MAC 地址的 PAUSE 帧。
`rx_copybreak=M`

驱动程序预分配了 32 个全尺寸（1536 字节）网络缓冲区用于接收数据。当一个数据包到达时，驱动程序需要决定是将数据包保留在其全尺寸缓冲区中，还是分配一个较小的缓冲区并将数据包复制到其中。
这是一种速度/空间的权衡。
`rx_copybreak` 的值用于决定何时进行数据复制；
如果数据包大小小于 `rx_copybreak`，则复制该数据包。
`rx_copybreak` 的默认值是 200 字节。
`max_interrupt_work`=N

驱动程序的中断服务程序可以在单次调用中处理许多接收和发送的数据包。它通过循环实现这一点。
`max_interrupt_work` 的值决定了中断服务程序将循环多少次。默认值为 32 次循环。如果超过这个数值，中断服务程序会放弃并生成警告信息 "eth0: 中断中的工作量过大"。
`hw_checksums`=N1,N2,N3,...

近期的 3Com 网卡能够在硬件层面生成 IPv4、TCP 和 UDP 校验和。
Linux 已经使用了很长一段时间的接收端校验和功能。
计划在 2.4 内核系列中使用的“零拷贝”补丁允许您利用网卡的 DMA 分散/集中（scatter/gather）功能以及发送端校验和。
驱动程序已经设置好，以便当应用零拷贝补丁时，所有 Tornado 和 Cyclone 设备都将使用分散/集中（S/G）功能及发送端校验和。
此模块参数已提供，以便您可以覆盖此决定。如果您认为传输（Tx）校验和导致了问题，您可以通过设置`hw_checksums=0`来禁用该功能。
如果您认为您的网卡（NIC）应该执行传输（Tx）校验和计算而驱动程序没有启用此功能，您可以使用`hw_checksums=1`强制使用硬件传输（Tx）校验和计算。
驱动程序会在日志文件中记录一条消息，指示其是否正在使用硬件分散/聚集（scatter/gather）和硬件传输（Tx）校验和计算。
分散/聚集和硬件校验和计算为`sendfile()`系统调用提供了显著的性能提升，但对`send()`操作有轻微的吞吐量下降。对接收效率没有影响。
compaq_ioaddr=N,
compaq_irq=N,
compaq_device_id=N

  “用于解决Compaq PCI BIOS32问题的变量”...
watchdog=N

  设置在内核判断发送器卡住并需要重置之前的时间持续时长（以毫秒为单位）
这主要用于调试目的，尽管对于碰撞率极高的局域网来说，增加这个值可能是有益的
默认值是5000（5.0秒）
enable_wol=N1,N2,N3,...

为相关接口启用局域网唤醒（Wake-on-LAN）支持。可以使用Donald Becker的“ether-wake”应用程序来唤醒处于挂起状态的机器。
此外，这也启用了网卡的电源管理支持。
global_enable_wol=N

这为机器中的所有 3c59x 网卡设置了启用 WoL（唤醒上网）模式。在上面的 "enable_wol" 数组中的条目将覆盖此设置的任何内容。
媒体选择
--------------

一些较旧的网卡，如 3c590 和 3c900 系列，具有 10base2 和 AUI 接口。
在 2001 年 1 月之前，该驱动程序会在未检测到 10baseT 接口活动时自动选择 10base2 或 AUI 端口。然后它会锁定在 10base2 端口上，并且需要重新加载驱动程序才能切换回 10baseT。这种行为无法通过模块选项覆盖来防止。
后来（当前）版本的驱动程序确实支持锁定媒体类型。因此，如果您使用以下命令加载驱动程序模块：

    modprobe 3c59x options=0

它将永久选择 10baseT 端口。其他媒体类型的自动选择不会发生。
发送错误，Tx 状态寄存器 82
--------------------------------------

这是一个常见的错误，几乎总是由同一网络上的另一台主机处于全双工模式而本机处于半双工模式所导致。您需要找到那台主机并使其运行在半双工模式下，或者修复这台主机以运行在全双工模式下。
作为最后的手段，您可以使用以下命令强制 3c59x 驱动程序进入全双工模式：

    options 3c59x full_duplex=1

但这应被视为对故障网络设备的临时解决方案，并且实际上只应用于那些不能自动协商的设备。
附加资源
------------------

设备驱动实现的详细信息位于源文件的顶部。
更多的文档可以在唐·贝克尔的 Linux 驱动网站上找到：

     http://www.scyld.com/vortex.html

唐·贝克尔的驱动开发网站：

     http://www.scyld.com/network.html

唐·贝克尔的 vortex-diag 程序对于检查网卡的状态非常有用：

     http://www.scyld.com/ethercard_diag.html

唐·贝克尔的 mii-diag 程序可用于检查和操作网卡的介质独立接口子系统：

     http://www.scyld.com/ethercard_diag.html#mii-diag

唐·贝克尔的唤醒上网页面：

     http://www.scyld.com/wakeonlan.html

3Com 的基于 DOS 的应用程序用于设置网卡的 EEPROM：

	ftp://ftp.3com.com/pub/nic/3c90x/3c90xx2.exe


自动协商说明
----------------------

  当链路建立时，驱动程序使用一分钟的心跳周期来适应外部局域网环境的变化；如果链路断开，则使用五秒的心跳周期。
这意味着例如，当一台机器从集线器连接的 10baseT 局域网拔出并插入一个交换式 100baseT 局域网时，在长达六十秒的时间内，吞吐量将会非常糟糕。请耐心等待。
思科互操作性注释，来自 Walter Wong <wcw+@CMU.EDU>：

  顺便说一下，添加 HAS_NWAY 似乎与思科 6509 交换机存在一个问题。具体来说，您需要将机器所连接端口的生成树参数更改为 'portfast' 模式。否则，协商会失败。这是我们已经注意到一段时间但一直没有时间追踪的问题。
思科交换机 (Jeff Busch <jbusch@deja.com>)

    我为直接连接到 PC/服务器的端口设置的标准配置如下：

    接口 FastEthernet0/N
    描述 machinename
    负载间隔 30
    生成树端口快速

    如果自动协商存在问题，您可能还需要指定“速度 100”和“双工全双工”（或“速度 10”和“双工半双工”）
警告：不要将集线器/交换机/网桥连接到这些特殊配置的端口！这样会让交换机变得非常混乱。

报告和诊断问题
-----------------

维护人员发现，准确且完整的故障报告对于解决驱动程序问题极为宝贵。我们常常无法重现问题，必须依靠您的耐心和努力来彻底解决问题。
如果您认为遇到了驱动程序问题，请按照以下步骤操作：

- 这真的是一个驱动程序问题吗？

   排除一些变量：尝试不同的卡、不同的计算机、不同的电缆、交换机/集线器上的不同端口、不同版本的内核或驱动程序等。
- 好的，这确实是一个驱动程序问题
您需要生成一份报告。通常情况下，这是一封发给维护者和/或 netdev@vger.kernel.org 的电子邮件。维护者的电子邮件地址可以在驱动程序源代码或 MAINTAINERS 文件中找到。
- 报告的内容会根据问题的不同而有很大差异。如果是内核崩溃，则应参考 'Documentation/admin-guide/reporting-issues.rst'。
但对于大多数问题，提供以下信息很有帮助：

   - 内核版本、驱动程序版本

   - 驱动程序初始化时生成的横幅消息的副本。例如：

     eth0: 3Com PCI 3c905C Tornado 在 0xa400 处，00:50:da:6a:88:f0，中断请求 19
     8K 字节宽 RAM 5:3 接收:发送分离，自动选择/自动协商接口
在地址 24 处发现 MII 收发器，状态 782d
启用总线主传输和全帧接收。

**注释：**您必须提供`debug=2`的modprobe选项来生成完整的检测消息。请按照以下步骤操作：

```bash
modprobe 3c59x debug=2
```

- 如果它是PCI设备，请提供`lspci -vx`的相关输出，例如：

```plaintext
00:09.0 以太网控制器: 3Com 公司 3c905C-TX [Fast Etherlink] (版本 74)
       子系统: 3Com 公司: 未知设备 9200
       标志: 总线主控, 中等设备选择, 延迟 32, IRQ 19
       I/O 端口位于 a400 [大小=128]
       内存位于 db000000 (32位, 不可预取) [大小=128]
       扩展ROM位于 <未分配> [禁用] [大小=128K]
       功能: [dc] 电源管理版本 2
00: b7 10 00 92 07 00 10 02 74 00 00 02 08 20 00 00
10: 01 a4 00 00 00 00 00 db 00 00 00 00 00 00 00 00
20: 00 00 00 00 00 00 00 00 00 00 00 00 b7 10 00 10
30: 00 00 00 00 dc 00 00 00 00 00 00 00 05 01 0a 0a
```

- 对环境的描述：10baseT？100baseT？全双工/半双工？交换式或集线器连接？

- 您可能向驱动程序提供的任何其他模块参数。
- 产生的任何内核日志。越多越好。
如果这是一个大型文件，并且您正在将报告发送到邮件列表中，请提及您有日志文件，但不要发送它。
如果您直接向维护者报告，则只需发送它即可。
为了确保所有内核日志都可用，请在/etc/syslog.conf中添加以下行：

```bash
kern.* /var/log/messages
```

然后重启syslogd：

```bash
/etc/rc.d/init.d/syslog restart
```

（以上命令可能会有所不同，具体取决于您使用的Linux发行版）
- 如果您的问题可以重现，那就太好了。尝试以下方法：
  
  1) 提高调试级别。通常可以通过以下方式完成：

    a) `modprobe 驱动 debug=7`
    b) 在/etc/modprobe.d/driver.conf中：
       `options 驱动 debug=7`

  2) 使用更高的调试级别重现问题，并将所有日志发送给维护者。
  3) 从唐纳德·贝克尔(Donald Becker)的网站[http://www.scyld.com/ethercard_diag.html](http://www.scyld.com/ethercard_diag.html)下载您网卡的诊断工具。同时下载mii-diag.c。构建这些工具后，
    a) 当网卡正常工作时运行`vortex-diag -aaee`和`mii-diag -v`。保存输出结果。
    b) 当网卡出现故障时运行上述命令。发送两组输出结果。
最后，请保持耐心并准备好进行一些工作。您可能需要花费一周或更长时间来解决这个问题，因为维护者可能会询问更多问题，要求进行更多测试，要求应用补丁等。到最后，问题甚至可能仍然未得到解决。
