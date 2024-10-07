SPDX许可证标识符: GPL-2.0

=========================
3Com Vortex 设备驱动程序
=========================

Andrew Morton

2000年4月30日

本文档描述了Linux下3Com "Vortex"设备驱动程序3c59x.c的使用方法和注意事项。该驱动程序由Donald Becker <becker@scyld.com>编写。

Don不再是此版本驱动程序的主要维护者。
请将问题报告给以下人员之一：

- Andrew Morton
- Netdev邮件列表 <netdev@vger.kernel.org>
- Linux内核邮件列表 <linux-kernel@vger.kernel.org>

请注意文档末尾的“报告和诊断问题”部分。
自内核2.3.99-pre6起，该驱动程序已经包含了原先由3c575_cb.c处理的3c575系列Cardbus卡的支持。
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
- 3c920B-EMB-WNM（ATI Radeon 9100 IGP）
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
- 3c982 Hydra 双端口 A
- 3c982 Hydra 双端口 B
- 3c905B-T4
- 3c920B-EMB-WNM Tornado

模块参数
========

加载驱动程序模块时可以提供几个参数。这些参数通常放在`/etc/modprobe.d/*.conf`配置文件中。例如：
```
options 3c59x debug=3 rx_copybreak=300
```

如果您正在使用PCMCIA工具（如cardmgr），则可以在`/etc/pcmcia/config.opts`中放置选项：
```
module "3c59x" opts "debug=3 rx_copybreak=300"
```

支持的参数如下：

debug=N

  其中N是从0到7的一个数字。任何大于3的值都会在系统日志中产生大量输出。默认值为debug=1。
options=N1,N2,N3,...

  列表中的每个数字都提供了相应网络卡的一个选项。例如，如果您有两个3c905，并且希望为它们提供选项0x204，则应使用：
  ```
  options=0x204,0x204
  ```

  各个选项由多个位字段组成，其含义如下：

  可能的媒体类型设置

  ==  ==================================
  0   10baseT
  1   10Mbps AUI
  2   未定义
  3   10base2（BNC）
  4   100base-TX
  5   100base-FX
  6   MII（Media Independent Interface）
  7   使用EEPROM中的默认设置
  8   自动协商
  9   外部MII
  10  使用EEPROM中的默认设置
  ==  ==================================

  在生成`options`设置值时，上述媒体选择值可以与以下值进行逻辑或运算（或相加）：

  ======  =============================================
  0x8000  将驱动调试级别设置为7
  0x4000  将驱动调试级别设置为2
  0x0400  启用Wake-on-LAN
  0x0200  强制全双工模式
  0x0010  总线主控使能位（仅限旧版Vortex卡）
  ======  =============================================

  例如：
  ```
  insmod 3c59x options=0x204
  ```

  将强制全双工100base-TX模式，而不是允许通常的自动协商。
global_options=N

  为机器中的所有3c59x NIC设置`options`参数。
`options`数组中的条目将覆盖任何此设置。
```plaintext
full_duplex=N1,N2,N3...
与 'options' 中的第9位类似。强制将对应的网卡设置为全双工模式。请优先使用此参数而不是 'options' 参数。
事实上，请不要使用这个参数！您最好确保自动协商功能正常工作。

global_full_duplex=N1
为机器中的所有 3c59x 网卡设置全双工模式。上面的 "full_duplex" 数组中的条目将覆盖此设置。

flow_ctrl=N1,N2,N3...
使用 802.3x MAC 层流量控制。3Com 网卡仅支持 PAUSE 命令，这意味着如果它们从链路对端接收到 PAUSE 帧，则会停止发送数据包一段时间。
驱动程序仅允许在全双工模式下运行的链路上进行流量控制。
此功能似乎不适用于 3c905 网卡——仅测试了 3c905B 和 3c905C。
3Com 网卡似乎只响应发送到保留目标地址 01:80:c2:00:00:01 的 PAUSE 帧。它们不响应发送到站点 MAC 地址的 PAUSE 帧。

rx_copybreak=M
驱动程序预分配了 32 个全尺寸（1536 字节）网络缓冲区用于接收。当数据包到达时，驱动程序需要决定是将数据包保留在其全尺寸缓冲区中，还是分配一个较小的缓冲区并将数据包复制到其中。
```
这是一个速度/空间的权衡。
`rx_copybreak` 的值用于决定何时进行数据复制。
如果数据包大小小于 `rx_copybreak`，则会复制该数据包。
`rx_copybreak` 的默认值是 200 字节。
`max_interrupt_work=N`

  驱动程序的中断服务程序可以在一次调用中处理许多接收和发送的数据包。它通过循环实现这一点。
`max_interrupt_work` 的值决定了中断服务程序将循环多少次。默认值是 32 次循环。如果超过这个值，中断服务程序将会放弃，并生成一条警告信息 “eth0: 中断中的工作量过大”。
`hw_checksums=N1,N2,N3,...`
最近的 3Com 网卡能够在硬件中生成 IPv4、TCP 和 UDP 校验和。
Linux 已经使用了很长时间的接收校验和功能。
计划在 2.4 内核系列中引入的“零拷贝”补丁允许你利用网卡的 DMA 分散/聚合以及发送校验和功能。
驱动程序设置为当应用零拷贝补丁时，所有 Tornado 和 Cyclone 设备都将使用分散/聚合（S/G）和发送校验和（Tx checksums）。
此模块参数已提供，以便您可以覆盖此决定。如果您认为Tx校验和导致了问题，可以通过设置`hw_checksums=0`来禁用该功能。
如果您认为您的网卡应该执行Tx校验和计算而驱动程序没有启用该功能，可以通过设置`hw_checksums=1`来强制使用硬件Tx校验和计算。
驱动程序会在日志文件中记录是否使用了硬件scatter/gather（分散/聚集）和硬件Tx校验和的信息。
分散/聚集和硬件校验和为sendfile()系统调用提供了显著的性能提升，但对于send()系统调用则有轻微的吞吐量下降。对接收效率没有影响。

compaq_ioaddr=N,
compaq_irq=N,
compaq_device_id=N

这些变量用于解决Compaq PCI BIOS32问题...

watchdog=N

设置在内核决定发送器卡住并需要重置之前的时间（以毫秒为单位）
这主要用于调试目的，尽管对于碰撞率非常高的局域网来说，增加这个值可能会有好处
默认值为5000（5.0秒）

enable_wol=N1,N2,N3,...

为相关的接口启用Wake-on-LAN支持。可以使用Donald Becker的`ether-wake`应用程序唤醒挂起的机器。
同时也启用了网卡的电源管理支持
global_enable_wol=N

  为机器中的所有 3c59x 网卡设置 enable_wol 模式。在上面的 `enable_wol` 数组中的条目将覆盖任何该设置
媒体选择
-----------

一些较旧的网卡，如 3c590 和 3c900 系列，具有 10base2 和 AUI 接口。
2001 年 1 月之前，如果未检测到 10baseT 端口上的活动，此驱动程序会自动选择 10base2 或 AUI 端口。然后它会卡在 10base2 端口上，需要重新加载驱动程序才能切换回 10baseT。这种行为无法通过模块选项覆盖来防止。
较新（当前）版本的驱动程序确实支持锁定媒体类型。因此，如果您使用以下命令加载驱动程序模块：

    modprobe 3c59x options=0

它将永久选择 10baseT 端口。其他媒体类型的自动选择不会发生。
发送错误，Tx 状态寄存器 82
-------------------------------------

这是一个常见的错误，几乎总是由同一网络上的另一台主机处于全双工模式，而本机处于半双工模式所引起的。您需要找到那台主机并使其运行在半双工模式下，或者修复本机以运行在全双工模式下。
作为最后手段，您可以使用以下命令强制 3c59x 驱动程序进入全双工模式：

    options 3c59x full_duplex=1

但这应被视为对故障网络设备的临时解决方案，仅应用于那些无法自动协商的设备。
附加资源
--------------------

设备驱动程序实现的详细信息位于源文件的顶部。
额外文档可在 Don Becker 的 Linux Drivers 网站获取：

    http://www.scyld.com/vortex.html

Donald Becker 的驱动程序开发网站：

    http://www.scyld.com/network.html

Donald 的 vortex-diag 程序可用于检查网卡的状态：

    http://www.scyld.com/ethercard_diag.html

Donald 的 mii-diag 程序可用于检查和操作网卡的媒体独立接口子系统：

    http://www.scyld.com/ethercard_diag.html#mii-diag

Donald 的 Wake-on-LAN 页面：

    http://www.scyld.com/wakeonlan.html

3Com 提供的基于 DOS 的应用程序，用于设置网卡的 EEPROM：

    ftp://ftp.3com.com/pub/nic/3c90x/3c90xx2.exe

自动协商说明
---------------------

驱动程序使用一分钟的心跳来适应外部局域网环境的变化，如果链路已连接则使用五秒。
这意味着，例如，当一台机器从一个集线器连接的 10baseT 局域网拔出并插入一个交换的 100baseT 局域网时，在长达六十秒内吞吐量将非常糟糕。请耐心等待。
思科互操作性说明来自 Walter Wong <wcw+@CMU.EDU>：

  顺便说一句，添加 HAS_NWAY 似乎与思科 6509 交换机存在一个问题。具体来说，你需要将机器插入的端口的生成树参数更改为 'portfast' 模式。否则，协商会失败。这是我们注意到一段时间但一直没有时间追踪的问题（Jeff Busch <jbusch@deja.com>）。

    我为直接连接 PC/服务器的端口设置的标准配置如下：

    接口 FastEthernet0/N
    描述 machinename
    负载间隔 30
    生成树 端口快速

    如果自动协商存在问题，你可能还需要指定 "速度 100" 和 "全双工"（或 "速度 10" 和 "半双工"）。
警告：不要将集线器/交换机/桥接到这些特别配置的端口！交换机会变得非常混乱。

问题报告和诊断
-------------------

维护者发现准确且完整的故障报告对于解决驱动程序问题是无价的。我们经常无法重现问题，必须依靠你的耐心和努力来找出问题的根本原因。
如果你认为你遇到了一个驱动程序问题，以下是一些你应该采取的步骤：

- 这真的是一个驱动程序问题吗？

   排除一些变量：尝试不同的卡、不同的计算机、不同的电缆、交换机/集线器上的不同端口、不同版本的内核或驱动程序等。
- 好的，这是一个驱动程序问题
你需要生成一份报告。通常这是一封发给维护者和/或 netdev@vger.kernel.org 的电子邮件。维护者的电子邮件地址将在驱动源代码中或在 MAINTAINERS 文件中找到。
- 报告的内容将根据问题的不同而有很大差异。如果是内核崩溃，则应参阅 'Documentation/admin-guide/reporting-issues.rst'
但对于大多数问题，提供以下内容是有用的：

   - 内核版本，驱动程序版本

   - 驱动程序初始化时生成的横幅消息的副本。例如：

     eth0: 3Com PCI 3c905C Tornado 在 0xa400 处，00:50:da:6a:88:f0，IRQ 19
     8K 字节宽 RAM 5:3 接收:发送 分割，自适应/自动协商接口
MII 收发器在地址 24 处找到，状态 782d
启用总线主控传输和全帧接收

注意：您必须提供 `debug=2` 的 modprobe 选项以生成完整的检测信息。请执行以下操作：

```
modprobe 3c59x debug=2
```

- 如果是 PCI 设备，请提供 `lspci -vx` 的相关输出，例如：

```
00:09.0 以太网控制器: 3Com 公司 3c905C-TX [Fast Etherlink] (版本 74)
    子系统: 3Com 公司: 未知设备 9200
    标志: 总线主控, 中等设备选择, 延迟 32, IRQ 19
    I/O 端口位于 a400 [大小=128]
    内存位于 db000000 (32位, 非预取) [大小=128]
    扩展ROM位于 <未分配> [禁用] [大小=128K]
    能力: [dc] 电源管理版本 2
00: b7 10 00 92 07 00 10 02 74 00 00 02 08 20 00 00
10: 01 a4 00 00 00 00 00 db 00 00 00 00 00 00 00 00
20: 00 00 00 00 00 00 00 00 00 00 00 00 b7 10 00 10
30: 00 00 00 00 dc 00 00 00 00 00 00 00 05 01 0a 0a
```

- 对环境的描述：10baseT？100baseT？全双工/半双工？交换机还是集线器？

- 您可能提供的任何额外模块参数

- 产生的内核日志。越多越好。
如果这是一个大文件，并且您正在将报告发送到邮件列表，请说明您有日志文件，但不要发送它。如果您直接向维护者报告，则只需发送即可。

为了确保所有内核日志都可用，请在 `/etc/syslog.conf` 中添加以下行：

```
kern.* /var/log/messages
```

然后重启 syslogd，使用：

```
/etc/rc.d/init.d/syslog restart
```

（以上步骤可能会有所不同，具体取决于您使用的 Linux 发行版）

- 如果您的问题可以重现，那太好了。尝试以下操作：

  1）增加调试级别。通常通过以下方式完成：

    a）`modprobe 驱动程序 debug=7`
    b）在 `/etc/modprobe.d/驱动程序.conf` 中：
        `options 驱动程序 debug=7`

  2）在更高的调试级别下重现问题，并将所有日志发送给维护者

3）从 Donald Becker 的网站下载您网卡的诊断工具 <http://www.scyld.com/ethercard_diag.html>
   同时下载 mii-diag.c。构建这些工具：

   a）当网卡工作正常时，运行 `vortex-diag -aaee` 和 `mii-diag -v`，并保存输出结果
   b）当网卡出现故障时，再次运行上述命令，并发送两组输出结果
最后，请保持耐心并做好一些工作的准备。你可能会在这个问题上花费一周或更长时间，因为维护者可能会提出更多问题，要求进行更多测试，要求应用补丁等。到最后，问题甚至可能仍然未解决。
