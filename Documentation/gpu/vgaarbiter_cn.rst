VGA 仲裁器
==========

图形设备通过 I/O 或内存空间中的范围进行访问。尽管大多数现代设备允许重新定位这些范围，但一些基于 PCI 的“传统”VGA 设备通常会保留与 ISA 总线上的相同“硬解码”地址。更多细节请参阅“PCI Bus Binding to IEEE Std 1275-1994 Standard for Boot (Initialization Configuration) Firmware Revision 2.1”的第7节：传统设备。
X 服务器内部的资源访问控制（RAC）模块[0]用于处理多个传统 VGA 设备共存时的仲裁任务（除了其他总线管理任务）。但是当这些设备被不同的用户空间客户端尝试访问时（例如并行运行的两个服务器），它们的地址分配会发生冲突。此外，理想情况下，作为用户空间应用，X 服务器不应控制总线资源。因此需要一个位于 X 服务器之外的仲裁方案来控制这些资源的共享。本文档介绍了为 Linux 内核实现的 VGA 仲裁器的操作。

vgaarb 内核/用户空间 ABI
--------------------------

vgaarb 是 Linux 内核的一个模块。当它首次加载时，它会扫描所有 PCI 设备并将 VGA 设备加入到仲裁中。然后，仲裁器会启用或禁用不同 VGA 设备的传统指令解码。不需要使用仲裁器的设备可以通过调用 vga_set_legacy_decoding() 明确告知仲裁器。
内核向客户端导出一个字符设备接口（/dev/vga_arbiter），其语义如下：

open
    打开一个用户的仲裁器实例。默认情况下，它会连接到系统的默认 VGA 设备。
close
    关闭一个用户的实例。释放该用户持有的锁。
read
    返回一个字符串，指示目标的状态，如：

    "<card_ID>,decodes=<io_state>,owns=<io_state>,locks=<io_state> (ic,mc)"

    一个 IO 状态字符串的形式为 {io, mem, io+mem, none}，mc 和 ic 分别是内存和 IO 锁计数（仅用于调试/诊断）。"decodes" 表示当前卡正在解码的内容，"owns" 表示当前已启用的内容，"locks" 表示由该卡锁定的内容。如果卡未插入，则 card_ID 为 "invalid"，并且任何命令都会返回 -ENODEV 错误，直到选择新的卡。
write
    向仲裁器写入命令。命令列表如下：

    target <card_ID>
            将目标切换到卡 <card_ID>（见下文）
    lock <io_state>
            获取目标上的锁（"none" 是无效的 io_state）
    trylock <io_state>
            非阻塞地获取目标上的锁（如果失败则返回 EBUSY）
    unlock <io_state>
            释放目标上的锁
    unlock all
            释放此用户在目标上持有的所有锁（尚未实现）
    decodes <io_state>
            设置卡的传统解码属性

    poll
            如果任何卡（不仅仅是目标卡）发生变化，则产生事件

    card_ID 的形式为 "PCI:domain:bus:dev.fn"。可以设置为 "default" 以回到系统默认卡（待实现）。目前，仅支持 PCI 前缀，但用户空间 API 可能在将来支持其他总线类型，即使当前内核实现不支持。

关于锁的说明：
驱动程序跟踪每个用户在哪个卡上持有哪种锁。它支持堆叠，就像内核中的那样。这使得实现稍微复杂一些，但使仲裁器更能容忍用户空间的问题，并且能够在进程终止时正确清理。
目前，对于给定的用户（文件描述符实例），最多可以同时从用户空间发出针对 16 张卡的锁。
在设备热插拔的情况下，有一个钩子——pci_notify()——用来通知设备添加/移除，并自动在仲裁器中添加/移除。
还有内核中的仲裁器 API，供 DRM、vgacon 或其他驱动程序使用。
内核接口
-------------------

.. kernel-doc:: include/linux/vgaarb.h
   :内部:

.. kernel-doc:: drivers/pci/vgaarb.c
   :导出:

libpciaccess
------------

为了使用VGA仲裁字符设备，在libpciaccess库中实现了一个API。在结构体`pci_device`（系统中的每个设备）中添加了一个字段::

    /* 设备解码的资源类型 */
    int vgaarb_rsrc;

此外，在`pci_system`中添加了以下内容::

    int vgaarb_fd;
    int vga_count;
    struct pci_device *vga_target;
    struct pci_device *vga_default_dev;

`vga_count`用于跟踪正在被仲裁的显卡数量，因此例如，如果只有一个显卡，则可以完全避免仲裁。以下函数为给定显卡获取VGA资源，并将这些资源标记为锁定。如果请求的资源是“正常”（而非传统）资源，仲裁器会首先检查该显卡是否对该类型的资源进行了传统解码。如果是这样，锁会被“转换”为传统资源锁。仲裁器会首先查找所有可能冲突的VGA显卡，并禁用它们的I/O和/或内存访问，包括必要时P2P桥接器上的VGA转发，以便所请求的资源能够被使用。然后，显卡被标记为锁定这些资源，并且其I/O和/或内存访问被启用（包括任何P2P桥接器上的VGA转发）。对于`vga_arb_lock()`函数，如果某个冲突显卡已经锁定了所需资源之一（或不同总线段上的任何资源，因为据我所知P2P桥接器不区分VGA内存和I/O），则该函数将阻塞。如果显卡已经拥有这些资源，则该函数成功。`vga_arb_trylock()`将在阻塞之前返回(-EBUSY)。支持嵌套调用（维护一个每资源计数器）
设置此客户端的目标设备。::

    int  pci_device_vgaarb_set_target   (struct pci_device *dev);

例如，在x86上，如果同一总线上的两个设备想要锁定不同的资源，则两者都会成功（锁定）。如果设备位于不同的总线上并且尝试锁定不同的资源，则只有第一个尝试成功的设备才会成功。::

    int  pci_device_vgaarb_lock         (void);
    int  pci_device_vgaarb_trylock      (void);

解锁设备的资源。::

    int  pci_device_vgaarb_unlock       (void);

指示仲裁器显卡是否解码传统VGA I/O、传统VGA内存、两者或都不解码。所有显卡默认都解码两者，显卡驱动程序（例如fbdev）应告诉仲裁器它是否已禁用传统解码，以便该显卡可以不参与仲裁过程（并且可以在任何时间安全地接受中断）。::

    int  pci_device_vgaarb_decodes      (int new_vgaarb_rsrc);

连接到仲裁器设备并分配结构体。::

    int  pci_device_vgaarb_init         (void);

关闭连接。::

    void pci_device_vgaarb_fini         (void);

xf86VGAArbiter（X服务器实现）
----------------------------------------

X服务器基本上封装了所有以某种方式接触VGA寄存器的功能
参考文献
--------

Benjamin Herrenschmidt（IBM？）在2005年与Xorg社区讨论这种设计时开始了这项工作[1, 2]。2007年底，Paulo Zanoni和Tiago Vignatti（均为C3SL/巴拉那联邦大学）继续他的工作，改进内核代码以适应内核模块，并且还实现了用户空间部分[3]。现在（2009年），Tiago Vignatti和Dave Airlie最终完成了这项工作，并将其提交到了Jesse Barnes的PCI树中。
0) https://cgit.freedesktop.org/xorg/xserver/commit/?id=4b42448a2388d40f257774fbffdccaea87bd0347
1) https://lists.freedesktop.org/archives/xorg/2005-March/006663.html
2) https://lists.freedesktop.org/archives/xorg/2005-March/006745.html
3) https://lists.freedesktop.org/archives/xorg/2007-October/029507.html
