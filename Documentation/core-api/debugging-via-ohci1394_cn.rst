使用OHCI-1394火线控制器提供的物理DMA进行调试
===========================================================================

简介
------------

基本上，今天使用的所有火线控制器都遵循OHCI-1394规范，该规范定义了控制器为一个PCI总线主控器，通过DMA卸载数据传输以减轻CPU负担，并且具有一个“物理响应单元”，该单元在应用由OHCI-1394驱动程序定义的过滤器后，通过执行PCI总线主控器DMA来执行特定请求。一旦配置妥当，远程机器可以发送这些请求让OHCI-1394控制器对物理系统内存执行读取和写入操作，并且对于读取请求，将物理内存读取的结果发回给请求者。
利用这种方式，可以通过读取诸如打印内核信息缓冲区(printk buffer)或进程表等感兴趣的内存位置来调试问题。通过火线接口获取整个系统的内存转储也是可能的，其数据传输速率可达每秒10MB或更高。
对于大多数火线控制器而言，内存访问被限制在低4GB的物理地址空间内。这对于那些主要内存位于此限制之上的机器来说可能是个问题，但在更常见的硬件平台上（如x86、x86-64和PowerPC）这通常不是问题。
至少已知LSI FW643e和FW643e2控制器支持访问4GB以上的物理地址，但目前Linux中尚未启用这一功能。
结合OHCI-1394控制器的早期初始化用于调试目的，这种机制已被证明对于检查打印内核信息缓冲区中的长调试日志非常有用，特别是在像ACPI这样的领域中，系统无法启动，而其他调试手段（例如串行端口）要么不可用（笔记本电脑），要么对于大量调试信息来说太慢。

驱动程序
--------

drivers/firewire下的firewire-ohci驱动默认使用经过过滤的物理DMA，虽然更安全，但不适合远程调试。
向驱动程序传递remote_dma=1参数以获得未经过滤的物理DMA。
由于firewire-ohci驱动依赖于PCI枚举完成，因此已经为x86实现了一个相当早的初始化例程。这个例程运行得比console_init()调用要早得多，即在打印内核信息缓冲区出现在控制台上之前。
要激活它，请启用 CONFIG_PROVIDE_OHCI1394_DMA_INIT（内核调试菜单：在启动早期通过FireWire进行远程调试），并在启动时向重新编译的内核传递参数 "ohci1394_dma=early"。

工具
----

firescope - 最初由Benjamin Herrenschmidt开发，Andi Kleen将其从PowerPC移植到x86和x86_64，并增加了功能。现在可以使用firescope查看远程机器的printk缓冲区，甚至支持实时更新。
Bernhard Kaindl改进了firescope以支持从32位firescope访问64位机器以及反过来的操作：
- http://v3.sk/~lkundrak/firescope/

他还实现了快速系统转储（Alpha版本 - 请阅读README.txt）：
- http://halobates.de/firewire/firedump-0.1.tar.bz2

还有一个gdb代理用于FireWire，允许使用gdb访问数据，这些数据可以从gdb在vmlinux中找到的符号中引用：
- http://halobates.de/firewire/fireproxy-0.33.tar.bz2

这个gdb代理的最新版本（fireproxy-0.34）可以与kgdb通过基于内存的通信模块（kgdbom）进行通信（尚未稳定）。

入门
----

OHCI-1394规范规定，OHCI-1394控制器必须在每次总线重置时禁用所有物理DMA。
这意味着如果你想要在一个中断被禁用且没有对OHCI-1394控制器进行总线重置轮询的状态下调试问题，你必须在系统进入这种状态之前建立任何FireWire电缆连接并完全初始化所有FireWire硬件。
使用带有早期OHCI初始化的firescope的逐步说明：

1) 验证你的硬件是否受支持：

   加载firewire-ohci模块并检查你的内核日志。
你应该会看到一条类似下面的信息显示在加载驱动程序时：
```
firewire_ohci 0000:15:00.1: added OHCI v1.0 device as card 2, 4 IR + 4 IT ... contexts, quirks 0x11
```
如果没有支持的控制器，许多PCI、CardBus甚至是某些符合OHCI-1394规范的Express卡都是可用的。如果它不需要Windows操作系统的驱动程序，则很可能符合要求。只有专业商店才有不符合规范的卡，它们基于TI PCILynx芯片并需要Windows操作系统的驱动程序。
上面提到的内核日志消息包含字符串 "physUB"，如果控制器实现了一个可写的Physical Upper Bound寄存器。这需要用于超过4GB的物理DMA（但目前Linux尚未利用它）。
2) 建立一个有效的FireWire电缆连接：

   只要提供电气上和机械上稳定的连接并且具有匹配的连接器（有小型4针和大型6针的FireWire端口）的任何FireWire电缆都可以。
如果两个机器上都有驱动程序运行，当插入电缆并连接两台机器时，你应该会在两个机器的内核日志中看到一条类似的信息：
```
firewire_core 0000:15:00.1: created device fw1: GUID 00061b0020105917, S400
```
3) 使用 firescope 测试物理 DMA：

   在调试主机上，确保可以访问 /dev/fw*，
   然后启动 firescope:

	$ firescope
	端口 0 (/dev/fw1) 已打开，检测到 2 个节点

	FireScope
	---------
	目标 : <未指定>
	代 : 1
	[Ctrl-T] 选择目标
	[Ctrl-H] 此菜单
	[Ctrl-Q] 退出

    ------> 现在按下 Ctrl-T，输出应该类似如下：

	有 2 个可用节点，本地节点为：0
	 0: ffc0, UUID: 00000000 00000000 [LOCAL]
	 1: ffc1, UUID: 00279000 ba4bb801

   除了 [LOCAL] 节点外，还必须显示另一个节点且无错误消息。
4) 为带有早期 OHCI-1394 初始化的调试做准备：

   4.1) 在调试目标上进行内核编译和安装

   使用 CONFIG_PROVIDE_OHCI1394_DMA_INIT
   （内核开发：提供用于在启动时早期通过 FireWire 启用 DMA 的代码）
   编译要调试的内核，并将其安装在要调试的机器（调试目标）上。
4.2) 将被调试内核的 System.map 文件传输到调试主机

   将要调试的内核的 System.map 文件复制到调试主机（与通过 FireWire 连接的被调试机器相连的主机）
5) 获取 printk 缓冲区内容：

   在连接了 FireWire 线缆的情况下，加载了调试主机上的 OHCI-1394 驱动程序后，重启被调试机器，并使用带有 CONFIG_PROVIDE_OHCI1394_DMA_INIT 的内核启动，选项为 ohci1394_dma=early
然后，在调试主机上运行 firescope，例如使用 -A 命令：

	firescope -A 被调试目标内核的System.map文件路径

   注意：-A 自动连接到第一个非本地节点。只有当仅通过 FireWire 连接两台机器时它才可靠工作。
在连接到调试目标后，按下 Ctrl-D 查看完整的 printk 缓冲区或按下 Ctrl-U 进入自动更新模式并获取最近记录在调试目标上的内核消息的实时更新视图
输入 "firescope -h" 以获得更多有关 firescope 选项的信息。
备注
-----

文档和技术规范：http://halobates.de/firewire/

FireWire 是 Apple Inc. 的商标 — 更多信息请参考：
https://en.wikipedia.org/wiki/FireWire
