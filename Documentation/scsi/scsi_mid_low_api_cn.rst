SPDX 许可证标识符: GPL-2.0

=============================================
SCSI 中间层与底层驱动接口
=============================================

简介
============
本文档概述了Linux SCSI中间层与SCSI底层驱动之间的接口。底层驱动（LLD）通常被称为主机总线适配器（HBA）驱动或主机驱动（HD）。在本文档中，“主机”是指计算机IO总线（例如PCI或ISA）与SCSI传输中的单个SCSI启动端口之间的桥接器。“启动”端口（SCSI术语，详见SAM-3规范http://www.t10.org）向“目标”SCSI端口（例如磁盘）发送SCSI命令。在一个运行的系统中可以有多个LLD，但每种硬件类型只能有一个。大多数LLD可以控制一个或多个SCSI HBA。有些HBA包含多个主机。

在某些情况下，SCSI传输是一个已经存在于Linux中的外部总线（例如USB和IEEE1394）。在这种情况下，SCSI子系统的LLD是一个到其他驱动子系统的软件桥接器。例如，usb-storage驱动（位于drivers/usb/storage目录下）和ieee1394/sbp2驱动（位于drivers/ieee1394目录下）。

例如，aic7xxx LLD控制基于Adaptec公司7xxx芯片系列的并行SCSI接口控制器。aic7xxx LLD可以构建到内核中或作为模块加载。在Linux系统中只能运行一个aic7xxx LLD，但它可能控制多个HBA。这些HBA可能是PCI扩展卡上的或者是主板内置的（或者两者都有）。一些基于aic7xxx的HBA是双控制器，因此代表两个主机。像大多数现代HBA一样，每个aic7xxx主机都有自己的PCI设备地址。（SCSI主机与PCI设备的一对一对应关系很常见，但不是必需的，例如ISA适配器。）

SCSI中间层将LLD与其他层（如SCSI上层驱动和块层）隔离。

本文档版本大致对应于Linux内核版本2.6.8。

文档
=============
内核源码树中有一个SCSI文档目录，通常位于Documentation/scsi目录下。大多数文档采用reStructuredText格式。本文档名为scsi_mid_low_api.rst，可以在该目录下找到。更近期的版本可以在https://docs.kernel.org/scsi/scsi_mid_low_api.html找到。许多LLD在Documentation/scsi目录中有文档（例如aic7xxx.rst）。SCSI中间层在scsi.rst中简要描述，其中包含描述Linux内核2.4系列SCSI子系统的文档URL。有两个上层驱动在该目录中有文档：st.rst（SCSI磁带驱动）和scsi-generic.rst（用于sg驱动）。

一些LLD的文档（或URL）可以在C源代码或C源代码所在目录中找到。例如，要找到关于USB存储驱动的URL，请查看/usr/src/linux/drivers/usb/storage目录。

驱动结构
================
传统上，SCSI子系统的LLD至少包括drivers/scsi目录下的两个文件。例如，一个名为“xyz”的驱动有头文件“xyz.h”和源文件“xyz.c”。[实际上没有理由不能将所有内容放在一个文件中；头文件是多余的。]一些移植到多个操作系统的驱动有超过两个文件。例如，aic7xxx驱动有通用代码和操作系统特定代码的分离文件（例如FreeBSD和Linux）。这样的驱动倾向于在drivers/scsi目录下有自己的子目录。

当添加一个新的LLD到Linux时，以下文件（位于drivers/scsi目录下）需要关注：Makefile和Kconfig。

最好研究现有LLD是如何组织的。
随着2.5系列开发内核演变为2.6系列生产内核，此接口中引入了一些变化。一个例子是驱动初始化代码，现在有2种模型可供选择。较旧的模型类似于LK 2.4系列中的模型，基于在HBA驱动加载时检测到的主机。这将被称为“被动”初始化模型。较新的模型允许HBAs在LLD生命周期中热插拔（和拔出），这将被称为“热插拔”初始化模型。较新的模型更受青睐，因为它可以处理传统上永久连接的SCSI设备以及现代的“SCSI”设备（例如通过USB或IEEE 1394连接的数码相机）的热插拔。以下各节将讨论这两种初始化模型。

LLD以多种方式与SCSI子系统进行交互：

a) 直接调用由中层提供的函数。
b) 将一组函数指针传递给由中层提供的注册函数。中层将在未来的某个时刻调用这些函数。LLD将提供这些函数的实现。
c) 直接访问中层维护的已知数据结构实例。

属于a组的那些函数列在下面名为“中层提供的函数”的部分中。
属于b组的那些函数列在下面名为“接口函数”的部分中。它们的函数指针被放置在`struct scsi_host_template`的成员中，该结构的一个实例被传递给`scsi_host_alloc()`。对于LLD不希望提供的接口函数，应在`struct scsi_host_template`相应成员中放置NULL。在文件作用域定义`struct scsi_host_template`的实例时，未显式初始化的函数指针成员将被设置为NULL。
对于c组中的那些使用情况应谨慎处理，特别是在“热插拔”环境中。LLD应意识到与中层和其他层共享的实例的生命周期。

LLD内定义的所有函数和文件作用域内定义的所有数据都应为静态。例如，在名为“xxx”的LLD中，`slave_alloc()`函数可以这样定义：
```c
static int xxx_slave_alloc(struct scsi_device *sdev) {
    /* 代码 */
}
```

.. [#] `scsi_host_alloc()` 函数在大多数情况下替代了名称较为模糊的 `scsi_register()` 函数。

热插拔初始化模型
=================
在此模型中，LLD控制何时将SCSI主机引入和移除出SCSI子系统。主机可以在驱动初始化时尽早引入，并在驱动关闭时尽可能晚地移除。通常，驱动会响应一个sysfs `probe()` 回调，表明检测到了HBA。确认新设备是LLD想要控制的设备后，LLD将初始化HBA并注册一个新的主机到SCSI中层。

在LLD初始化期间，驱动应该向其预期找到HBA的适当IO总线（例如PCI总线）注册自身。这可能通过sysfs完成。任何驱动参数（特别是那些在驱动加载后可写的参数）也可以在这个时候注册到sysfs。当LLD注册其第一个HBA时，SCSI中层第一次了解到该LLD的存在。

在某个时间点，LLD感知到一个HBA，接下来是一个典型的LLD与中层之间的调用序列。
此示例展示了中层扫描新引入的HBA，该HBA包含3个SCSI设备，但只有前两个设备响应：

```
HBA 探测：假设扫描时找到2个SCSI设备
    LLD                   中层                    LLD
    ===-------------------=========--------------------===------
    scsi_host_alloc()  -->
    scsi_add_host()  ---->
    scsi_scan_host()  -------+
			    |
			slave_alloc()
			slave_configure() --> scsi_change_queue_depth()
			    |
			slave_alloc()
			slave_configure()
			    |
			slave_alloc()   ***
			slave_destroy() ***

    *** 对于中层尝试扫描但未响应的SCSI设备，会调用slave_alloc()和slave_destroy()这一对函数
如果LLD希望调整默认队列设置，可以在其slave_configure()例程中调用scsi_change_queue_depth()
当HBA被移除时，可能是作为有序关闭的一部分（例如与LLD模块卸载相关，通过"rmmod"命令）或响应“热插拔”事件（由sysfs()的remove()回调函数指示）。在这两种情况下，顺序相同：
    
	    HBA 移除：假设连接了2个SCSI设备
    LLD                      中层                 LLD
    ===----------------------=========-----------------===------
    scsi_remove_host() ---------+
				|
			slave_destroy()
			slave_destroy()
    scsi_host_put()

对于LLD来说，跟踪struct Scsi_Host实例（由scsi_host_alloc()返回指针）可能有用。这些实例由中层“拥有”。当引用计数变为零时，struct Scsi_Host实例会在scsi_host_put()中被释放。
热插拔控制着正在处理SCSI命令的磁盘的HBA是一个有趣的情况。中层引入了引用计数逻辑来应对许多相关问题。请参阅下面关于引用计数的部分。
热插拔概念可以扩展到SCSI设备。目前，当添加HBA时，scsi_scan_host()函数会扫描HBA上的SCSI传输设备。在较新的SCSI传输中，HBA可能会在扫描完成后才意识到一个新的SCSI设备。

LLD可以使用以下序列使中层意识到一个SCSI设备：

		    SCSI 设备 热插拔
    LLD                   中层                    LLD
    ===-------------------=========--------------------===------
    scsi_add_device()  ------+
			    |
			slave_alloc()
			slave_configure()   [--> scsi_change_queue_depth()]

类似地，LLD可能会发现一个SCSI设备已被移除（断开）或连接已中断。某些现有的SCSI传输（如SPI）可能直到后续的SCSI命令失败才会意识到SCSI设备已被移除，这可能会导致该设备被中层设置为离线。检测到SCSI设备移除的LLD可以通过以下序列从上层启动其移除：

		    SCSI 设备 热拔出
    LLD                      中层                 LLD
    ===----------------------=========-----------------===------
    scsi_remove_device() -------+
				|
			slave_destroy()

对于LLD来说，跟踪struct scsi_device实例（作为参数传递给slave_alloc()和slave_configure()回调函数）可能有用。这些实例由中层“拥有”，在slave_destroy()后会被释放。

引用计数
==================
Scsi_Host结构体增加了引用计数基础设施。
这有效地将struct Scsi_Host实例的所有权分散到使用它们的各种SCSI层。之前这些实例仅由中层拥有。通常LLD不需要直接操作这些引用计数，但在某些情况下可能需要这样做。
与struct Scsi_Host相关的三个引用计数函数如下：

  - scsi_host_alloc()：
    返回一个新的struct Scsi_Host实例指针，并将其引用计数设为1

  - scsi_host_get()：
    将给定实例的引用计数加1

  - scsi_host_put()：
    将给定实例的引用计数减1。如果引用计数变为0，则释放该实例

scsi_device结构体也增加了引用计数基础设施。
这有效地将 `struct scsi_device` 实例的所有权分散到使用它们的各种SCSI层。之前这些实例仅由中间层独占拥有。参见 `include/scsi/scsi_device.h` 文件末尾声明的访问函数。如果低级驱动（LLD）需要保留一个指向 `scsi_device` 实例的指针副本，应使用 `scsi_device_get()` 增加其引用计数。当不再需要该指针时，可以使用 `scsi_device_put()` 减少其引用计数（并可能删除它）。

注意：
`struct Scsi_Host` 实际上有两个引用计数，这些函数会同时操作这两个计数。

约定
====
首先，Linus Torvalds 对C编码风格的看法可以在 `Documentation/process/coding-style.rst` 文件中找到。
此外，在相关GCC编译器支持的情况下，大多数C99增强功能是被鼓励使用的。因此，在适当的情况下，鼓励使用C99风格的结构和数组初始化器。但不要过度使用，因为可变长度数组（VLA）目前还不完全支持。例外情况是使用 `//` 风格的注释；在Linux中仍更偏好使用 `/*...*/` 风格的注释。
编写良好、经过测试且文档齐全的代码无需重新格式化以符合上述约定。例如，aic7xxx驱动程序是从FreeBSD和Adaptec自己的实验室引入到Linux中的。毫无疑问，FreeBSD和Adaptec有它们自己的编码约定。

中间层提供的函数
=================
这些函数由SCSI中间层提供给LLD使用。
这些函数的名字（即入口点）已被导出，以便模块化的LLD能够访问它们。内核将确保SCSI中间层在任何LLD初始化之前加载并初始化。以下列出的函数按字母顺序排列，名称均以 `scsi_` 开头。

概述：

- `scsi_add_device` - 创建新的SCSI设备（逻辑单元）实例
- `scsi_add_host` - 执行sysfs注册并设置传输类
- `scsi_change_queue_depth` - 改变SCSI设备上的队列深度
- `scsi_bios_ptable` - 返回块设备的分区表副本
- `scsi_block_requests` - 阻止进一步的命令排队到指定主机
- `scsi_host_alloc` - 返回一个新的 `scsi_host` 实例，其引用计数为1
- `scsi_host_get` - 增加 `Scsi_Host` 实例的引用计数
- `scsi_host_put` - 减少 `Scsi_Host` 实例的引用计数（若为0则释放）
- `scsi_register` - 创建并注册一个SCSI主机适配器实例
- `scsi_remove_device` - 卸载并移除一个SCSI设备
- `scsi_remove_host` - 卸载并移除属于该主机的所有SCSI设备
- `scsi_report_bus_reset` - 报告SCSI总线重置情况
- `scsi_scan_host` - 扫描SCSI总线
- `scsi_track_queue_full` - 跟踪连续的QUEUE_FULL事件
- `scsi_unblock_requests` - 允许进一步的命令排队到指定主机
- `scsi_unregister` - [调用 `scsi_host_put()`]

详细信息：

```c
/**
* scsi_add_device - 创建新的SCSI设备（逻辑单元）实例
* @shost: 指向SCSI主机实例的指针
* @channel: 通道号（通常为0）
* @id: 目标ID号
* @lun: 逻辑单元号
*
* 返回新的 `struct scsi_device` 实例指针或
* 若出现问题则返回 `ERR_PTR(-ENODEV)` （或其他错误指针）
* （例如，没有逻辑单元响应给定地址）
*
* 可能阻塞：是
*
* 注意：此调用通常在添加HBA期间进行SCSI总线扫描时内部执行（即 `scsi_scan_host()`）。因此，只有在HBA意识到在 `scsi_scan_host()` 完成后有一个新的SCSI设备（逻辑单元）时才应调用它。如果成功，此调用可能会导致调用LLD中的 `slave_alloc()` 和 `slave_configure()` 回调
*
* 定义于：drivers/scsi/scsi_scan.c
**/
struct scsi_device * scsi_add_device(struct Scsi_Host *shost,
					unsigned int channel,
					unsigned int id, unsigned int lun)

/**
* scsi_add_host - 执行sysfs注册并设置传输类
* @shost: 指向SCSI主机实例的指针
* @dev: 指向类型为SCSI类的 `struct device` 的指针
*
* 成功返回0，失败返回负的errno值（如 `-ENOMEM`）
*
* 可能阻塞：否
*
* 注意：仅在成功调用 `scsi_host_alloc()` 后的“热插拔初始化模型”中需要。此函数不会扫描总线；可以通过调用 `scsi_scan_host()` 或其他特定传输方式来完成。LLD必须在调用此函数之前设置传输模板，并且只能在此函数调用之后访问传输类数据
*/
```
```
/**
 * scsi_add_host - 向系统添加一个SCSI主机
 * @shost: 指向要添加的Scsi_Host结构体
 * @dev: 指向相关的设备结构体
 *
 *      返回值：无
 *
 *      可能阻塞：否
 *
 *      注释：定义在：drivers/scsi/hosts.c
 */
int scsi_add_host(struct Scsi_Host *shost, struct device *dev)


/**
 * scsi_change_queue_depth - 允许LLD更改SCSI设备上的队列深度
 * @sdev: 指向要更改队列深度的SCSI设备
 * @tags: 如果启用了标记排队，则允许的最大标签数，或在非标记模式下LLD可以排队的最大命令数（如cmd_per_lun所示）
 *
 *      返回值：无
 *
 *      可能阻塞：否
 *
 *      注释：可以在由该LLD控制的任何SCSI设备上随时调用。[特别是在slave_configure()期间和之后以及slave_destroy()之前。] 可以安全地从中断代码中调用。
 *
 *      定义在：drivers/scsi/scsi.c [参见源代码获取更多注释]
 */
int scsi_change_queue_depth(struct scsi_device *sdev, int tags)


/**
 * scsi_bios_ptable - 返回块设备分区表的副本
 * @dev: 指向块设备
 *
 *      返回值：指向分区表的指针，或者失败时返回NULL
 *
 *      可能阻塞：是
 *
 *      注释：调用者拥有返回的内存（使用kfree()释放）
 *
 *      定义在：drivers/scsi/scsicam.c
 */
unsigned char *scsi_bios_ptable(struct block_device *dev)


/**
 * scsi_block_requests - 阻止进一步的命令被排队到指定的主机
 * @shost: 指向要阻止命令的主机
 *
 *      返回值：无
 *
 *      可能阻塞：否
 *
 *      注释：没有定时器或其他方式来解除请求的阻塞，除非LLD调用scsi_unblock_requests()
 *
 *      定义在：drivers/scsi/scsi_lib.c
 */
void scsi_block_requests(struct Scsi_Host *shost)


/**
 * scsi_host_alloc - 创建一个SCSI主机适配器实例并执行基本初始化
 * @sht: 指向SCSI主机模板
 * @privsize: 在hostdata数组中分配的额外字节数（这是返回的Scsi_Host实例的最后一个成员）
 *
 *      返回值：指向新的Scsi_Host实例或失败时返回NULL
 *
 *      可能阻塞：是
 *
 *      注释：当此调用返回到LLD时，该主机上的SCSI总线扫描尚未完成。
 *      hostdata数组（默认为零长度）是供LLD独占使用的每主机临时存储区。
 *      相关联的引用计数对象的引用计数均设置为1。
 *      完整注册（在sysfs中）和总线扫描将在调用scsi_add_host()和scsi_scan_host()时进行。
 *
 *      定义在：drivers/scsi/hosts.c
 */
struct Scsi_Host *scsi_host_alloc(const struct scsi_host_template *sht, int privsize)


/**
 * scsi_host_get - 增加Scsi_Host实例的引用计数
 * @shost: 指向Scsi_Host实例
 *
 *      返回值：无
 *
 *      可能阻塞：目前可能会阻塞，但可能改为不阻塞
 *
 *      注释：实际上会增加两个子对象中的计数
 *
 *      定义在：drivers/scsi/hosts.c
 */
void scsi_host_get(struct Scsi_Host *shost)


/**
 * scsi_host_put - 减少Scsi_Host实例的引用计数，如果为0则释放
 * @shost: 指向Scsi_Host实例
 *
 *      返回值：无
 *
 *      可能阻塞：目前可能会阻塞，但可能改为不阻塞
 *
 *      注释：实际上会减少两个子对象中的计数。如果后者计数达到0，则释放Scsi_Host实例
 */
void scsi_host_put(struct Scsi_Host *shost)
```
```
/**
 * scsi_host_put - 释放 Scsi_Host 实例的引用计数
 * @shost: 指向 Scsi_Host 实例的指针
 *
 * 无需担心 Scsi_Host 实例何时被释放，只要确保在引用计数平衡后不再访问该实例即可。
 *
 * 定义于：drivers/scsi/hosts.c
 */
void scsi_host_put(struct Scsi_Host *shost)


/**
 * scsi_register - 创建并注册一个 SCSI 主机适配器实例
 * @sht: 指向 SCSI 主机模板的指针
 * @privsize: 在 hostdata 数组中分配的额外字节数（该数组是返回的 Scsi_Host 实例的最后一个成员）
 *
 * 返回新创建的 Scsi_Host 实例的指针，如果失败则返回 NULL
 *
 * 可能阻塞：是
 *
 * 注意：当此调用返回到低级驱动（LLD）时，该主机上的 SCSI 总线扫描尚未完成
 * hostdata 数组（默认长度为零）是为每个主机提供的用于存储 LLD 数据的区域
 *
 * 定义于：drivers/scsi/hosts.c
 */
struct Scsi_Host *scsi_register(struct scsi_host_template *sht, int privsize)


/**
 * scsi_remove_device - 卸载并移除一个 SCSI 设备
 * @sdev: 指向 SCSI 设备实例的指针
 *
 * 成功返回值：0；如果设备未连接，则返回 -EINVAL
 *
 * 可能阻塞：是
 *
 * 注意：如果 LLD 发现某个 SCSI 设备（逻辑单元）已被移除但其主机仍然存在，则可以请求移除该 SCSI 设备。如果成功，此调用将导致 slave_destroy() 回调函数被调用。此调用之后，sdev 指针将变为无效
 *
 * 定义于：drivers/scsi/scsi_sysfs.c
 */
int scsi_remove_device(struct scsi_device *sdev)


/**
 * scsi_remove_host - 卸载并移除属于该主机的所有 SCSI 设备
 * @shost: 指向 SCSI 主机实例的指针
 *
 * 成功返回值：0；失败返回值：1（例如 LLD 忙碌等）
 *
 * 可能阻塞：是
 *
 * 注意：仅在使用“热插拔初始化模型”时才应调用此函数。应在调用 scsi_unregister() 之前调用
 *
 * 定义于：drivers/scsi/hosts.c
 */
int scsi_remove_host(struct Scsi_Host *shost)


/**
 * scsi_report_bus_reset - 报告观察到的 SCSI 总线重置
 * @shost: 涉及的 SCSI 主机指针
 * @channel: 在该主机上发生 SCSI 总线重置的通道
 *
 * 无返回值
 *
 * 可能阻塞：否
 *
 * 注意：只有当重置来自未知位置时才需要调用此函数。由中间层自身发起的重置不需要调用此函数，但这样做也无害。此函数的主要目的是确保 CHECK_CONDITION 被正确处理
 */
void scsi_report_bus_reset(struct Scsi_Host *shost, int channel)
```
```c
/**
 * scsi_report_bus_reset - 报告SCSI总线复位
 * @shost: 指向SCSI主机实例的指针
 * @channel: 通道编号
 *
 * 定义于：drivers/scsi/scsi_error.c
 */
void scsi_report_bus_reset(struct Scsi_Host *shost, int channel)


/**
 * scsi_scan_host - 扫描SCSI总线
 * @shost: 指向SCSI主机实例的指针
 *
 * 可能阻塞：是
 *
 * 注意：应在scsi_add_host()之后调用
 *
 * 定义于：drivers/scsi/scsi_scan.c
 */
void scsi_scan_host(struct Scsi_Host *shost)


/**
 * scsi_track_queue_full - 跟踪给定设备上的连续QUEUE_FULL事件，以确定是否需要调整队列深度
 * @sdev: 指向SCSI设备实例的指针
 * @depth: 当前设备上未完成的SCSI命令数量（不包括返回为QUEUE_FULL的命令）
 *
 * 返回值：
 *      0 - 不需要更改
 *     >0 - 调整队列深度到新的深度
 *     -1 - 回退到使用host->cmd_per_lun作为非标记命令深度的非标记操作
 *
 * 可能阻塞：否
 *
 * 注意：LLD可以在任何时候调用此函数，我们将做“正确的事情”；中断上下文安全
 *
 * 定义于：drivers/scsi/scsi.c
 */
int scsi_track_queue_full(struct scsi_device *sdev, int depth)


/**
 * scsi_unblock_requests - 允许进一步的命令被排队到给定的主机
 * @shost: 指向要解除阻塞命令的主机的指针
 *
 * 返回值：无
 *
 * 可能阻塞：否
 *
 * 定义于：drivers/scsi/scsi_lib.c
 */
void scsi_unblock_requests(struct Scsi_Host *shost)


/**
 * scsi_unregister - 注销并释放主机实例使用的内存
 * @shp: 指向要注销的SCSI主机实例的指针
 *
 * 返回值：无
 *
 * 可能阻塞：否
 *
 * 注意：如果使用“热插拔初始化模型”，则不应调用此函数。在“被动初始化模型”中，由exit_this_scsi_driver()内部调用。因此，LLD无需直接调用此函数
 *
 * 定义于：drivers/scsi/hosts.c
 */
void scsi_unregister(struct Scsi_Host *shp)
```


接口函数
===================
接口函数由LLD提供（定义），并将它们的函数指针放置在一个struct scsi_host_template实例中，该实例传递给scsi_host_alloc() [或scsi_register() / init_this_scsi_driver()]。
```
一些函数是强制性的。接口函数应当声明为静态的。约定的做法是，驱动程序 "xyz" 将其 `slave_configure()` 函数声明如下：

    static int xyz_slave_configure(struct scsi_device *sdev);

以此类推，对于下面列出的所有接口函数。

该函数指针应当放置在 `struct scsi_host_template` 实例的 `slave_configure` 成员中。此类实例的指针应当传递给中间层的 `scsi_host_alloc()`（或 `scsi_register()` / `init_this_scsi_driver()`）。

接口函数也在 `include/scsi/scsi_host.h` 文件中，在它们在 `struct scsi_host_template` 中定义点的上方进行了描述。某些情况下，在 `scsi_host.h` 中提供的细节比下面更多。

接口函数按字母顺序列于下：

总结：

  - `bios_param` - 获取磁盘的磁头、扇区、柱面信息
  - `eh_timed_out` - 通知主机命令定时器已超时
  - `eh_abort_handler` - 终止指定的命令
  - `eh_bus_reset_handler` - 发出 SCSI 总线复位
  - `eh_device_reset_handler` - 发出 SCSI 设备复位
  - `eh_host_reset_handler` - 重置主机（主机总线适配器）
  - `info` - 提供关于指定主机的信息
  - `ioctl` - 驱动可以响应 ioctl 请求
  - `proc_info` - 支持 `/proc/scsi/{driver_name}/{host_no}`
  - `queuecommand` - 排队 SCSI 命令，并在完成时调用 'done'
  - `slave_alloc` - 在向新设备发送任何命令之前
  - `slave_configure` - 设备连接后对驱动进行微调
  - `slave_destroy` - 指定设备即将关闭

详细说明如下：

    /**
    *      `bios_param` - 获取磁盘的磁头、扇区、柱面信息
    *      @sdev: 指向 SCSI 设备上下文（定义在 `include/scsi/scsi_device.h` 中）
    *      @bdev: 指向块设备上下文（定义在 `fs.h` 中）
    *      @capacity: 设备大小（以 512 字节扇区计）
    *      @params: 三元素数组用于输出：
    *              params[0] 磁头数（最大 255）
    *              params[1] 扇区数（最大 63）
    *              params[2] 柱面数
    *
    *      返回值被忽略
    *
    *      锁：无
    *
    *      调用上下文：进程（sd）
    *
    *      注释：如果未提供此函数，则使用任意几何（基于 READ CAPACITY）。params 数组预先初始化了一些假设值，以防此函数不输出任何内容。
    *
    *      可选定义在：LLD
    **/
	int bios_param(struct scsi_device *sdev, struct block_device *bdev,
		       sector_t capacity, int params[3])

    /**
    *      `eh_timed_out` - 命令的定时器刚刚触发
    *      @scp: 标识超时的命令
    *
    *      返回值：
    *
    *      EH_HANDLED: 我已修复错误，请完成命令
    *      EH_RESET_TIMER: 我需要更多时间，请重置定时器并重新开始计数
    *      EH_NOT_HANDLED 开始正常的错误恢复
    *
    *      锁：无
    *
    *      调用上下文：中断
    *
    *      注释：这是为了让低级驱动有机会进行本地恢复。
    *      此恢复仅限于确定挂起的命令是否会完成。您不得在此回调中终止并重新启动命令。
    *
    *      可选定义在：LLD
    **/
	int eh_timed_out(struct scsi_cmnd *scp)

    /**
    *      `eh_abort_handler` - 终止与 scp 关联的命令
    *      @scp: 标识要终止的命令
    *
    *      返回值：成功则返回 SUCCESS，否则返回 FAILED
    *
    *      锁：无
    *
    *      调用上下文：内核线程
    *
    *      注释：如果定义了 'no_async_abort'，此回调将从 scsi_eh 线程调用。其他命令在 eh 期间不会排队到当前主机。
    *      否则，它将在由于命令超时调用 scsi_timeout() 时被调用。
    */
	int eh_abort_handler(struct scsi_cmnd *scp)
```c
/**
 *      eh_abort_handler - 处理SCSI命令中止
 *      @scp: 要中止的SCSI命令
 *
 *      如果命令被中止则返回SUCCESS，否则返回FAILED
 *
 *      锁：无
 *
 *      调用上下文：内核线程
 *
 *      注意：由scsi_eh线程调用。在eh期间当前主机上不会排队其他命令
 *
 *      可选定义于：LLD
 **/
int eh_abort_handler(struct scsi_cmnd *scp)


/**
 *      eh_bus_reset_handler - 发出SCSI总线重置
 *      @scp: 包含该设备的SCSI总线应被重置
 *
 *      如果命令被中止则返回SUCCESS，否则返回FAILED
 *
 *      锁：无
 *
 *      调用上下文：内核线程
 *
 *      注意：由scsi_eh线程调用。在eh期间当前主机上不会排队其他命令
 *
 *      可选定义于：LLD
 **/
int eh_bus_reset_handler(struct scsi_cmnd *scp)


/**
 *      eh_device_reset_handler - 发出SCSI设备重置
 *      @scp: 标识要重置的SCSI设备
 *
 *      如果命令被中止则返回SUCCESS，否则返回FAILED
 *
 *      锁：无
 *
 *      调用上下文：内核线程
 *
 *      注意：由scsi_eh线程调用。在eh期间当前主机上不会排队其他命令
 *
 *      可选定义于：LLD
 **/
int eh_device_reset_handler(struct scsi_cmnd *scp)


/**
 *      eh_host_reset_handler - 重置主机（主机总线适配器）
 *      @scp: 包含该设备的SCSI主机应被重置
 *
 *      如果命令被中止则返回SUCCESS，否则返回FAILED
 *
 *      锁：无
 *
 *      调用上下文：内核线程
 *
 *      注意：由scsi_eh线程调用。在eh期间当前主机上不会排队其他命令
 *      默认eh_strategy下，如果没有定义任何_abort_、_device_reset_、_bus_reset_或此eh处理函数（或它们都返回FAILED），则在调用eh时将使相关设备脱机
 *
 *      可选定义于：LLD
 **/
int eh_host_reset_handler(struct scsi_cmnd *scp)


/**
 *      info - 提供关于给定主机的信息：驱动程序名称加上区分给定主机的数据
 *      @shp: 要提供信息的主机
 *
 *      返回ASCII空终止字符串。[假设此驱动程序管理指向的内存并保持其有效性，通常在整个主机生命周期内。]
 *
 *      锁：无
 *
 *      调用上下文：进程
 *
 *      注意：通常提供PCI或ISA信息，如IO地址和中断编号。如果不提供，则使用struct Scsi_Host::name。假设返回的信息适合一行（即不包含嵌入式换行符）
 *      SCSI_IOCTL_PROBE_HOST ioctl会返回此函数（或struct Scsi_Host::name如果此函数不可用）返回的字符串
 *      类似地，init_this_scsi_driver()会输出注册驱动程序的每个主机的“info”（或name）
 *      如果proc_info()未提供，则使用此函数的输出
 *
 *      可选定义于：LLD
 **/
const char *info(struct Scsi_Host *shp)


/**
 *      ioctl - 驱动程序可以响应ioctl请求
 *      @sdp: 发出ioctl的设备
 *      @cmd: ioctl编号
 *      @arg: 用于读取或写入数据的指针。由于它指向用户空间，应使用适当的内核函数（例如copy_from_user()）。根据Unix风格，此参数也可以被视为无符号长整型
 *
 *      当出现问题时返回负的"errno"值。0或正数值表示成功，并返回给用户空间
 **/
int ioctl(struct scsi_device *sdp, unsigned int cmd, unsigned long arg)
```

希望这个翻译对你有帮助！如果有任何进一步的问题，请告诉我。
```c
/**
 * 锁：无
 *
 * 调用上下文：进程
 *
 * 注释：SCSI 子系统使用一种“逐级传递”的 ioctl 模型。
 * 用户对上层驱动程序发出 ioctl()（例如 /dev/sdc），如果上层驱动程序不识别该 'cmd'，则将其传递给 SCSI 中间层。如果 SCSI 中间层也不识别它，则控制该设备的低层驱动程序会接收到 ioctl。根据最近的 Unix 标准，不支持的 ioctl() 'cmd' 应返回 -ENOTTY。
 *
 * 可选定义在：LLD
 */
int ioctl(struct scsi_device *sdp, int cmd, void *arg)


/**
 * proc_info - 支持 /proc/scsi/{driver_name}/{host_no}
 * @buffer: 输出到（0==writeto1_read0）或从其获取数据的锚点
 * @start: “有趣”数据被写入的位置。当 1==writeto1_read0 时忽略此参数
 * @offset: buffer 内部 0==writeto1_read0 实际感兴趣的偏移量。当 1==writeto1_read0 时忽略此参数
 * @length: buffer 的最大（或实际）长度
 * @host_no: 感兴趣的主机号（struct Scsi_Host::host_no）
 * @writeto1_read0: 1 -> 数据从用户空间流向驱动程序（例如 "echo some_string > /proc/scsi/xyz/2"）
 *                 0 -> 用户从该驱动程序获取数据（例如 "cat /proc/scsi/xyz/2"）
 *
 * 当 1==writeto1_read0 时返回长度。否则返回从偏移量开始写入 buffer 的字符数
 *
 * 锁：无
 *
 * 调用上下文：进程
 *
 * 注释：由 scsi_proc.c 驱动，后者与 proc_fs 接口。现在可以从 SCSI 子系统中配置 proc_fs 支持
 *
 * 可选定义在：LLD
 */
int proc_info(char * buffer, char ** start, off_t offset,
              int length, int host_no, int writeto1_read0)


/**
 * queuecommand - 队列化 SCSI 命令，在完成时调用 scp->scsi_done
 * @shost: 指向 SCSI 主机对象的指针
 * @scp: 指向 SCSI 命令对象的指针
 *
 * 成功时返回 0
 *
 * 如果失败，返回：
 *
 * 如果设备队列已满，则返回 SCSI_MLQUEUE_DEVICE_BUSY，
 * 如果整个主机队列已满，则返回 SCSI_MLQUEUE_HOST_BUSY
 *
 * 在这两种情况下返回时，中间层将重新排队 I/O
 *
 * - 如果返回值为 SCSI_MLQUEUE_DEVICE_BUSY，仅暂停该特定设备，并在命令返回后恢复（或者如果再没有其他待处理命令，则短暂延迟后恢复）。其他设备的命令继续正常处理。
 *
 * - 如果返回值为 SCSI_MLQUEUE_HOST_BUSY，所有主机上的 I/O 将暂停，并在任何命令从主机返回后恢复（或者如果再没有其他待处理命令，则短暂延迟后恢复）。
 */
int queuecommand(struct scsi_host *shost, struct scsi_command *scp)
```
```c
/**
 *  为了与早期版本的queuecommand兼容，任何其他返回值均被视为SCSI_MLQUEUE_HOST_BUSY
 *
 *  立即检测到的其他类型错误可以通过将scp->result设置为适当的值、调用scp->scsi_done回调并从该函数返回0来标记。如果命令没有立即执行（并且LLD正在启动或即将启动给定的命令），则此函数应将0放入scp->result并返回0
 *
 *  命令所有权。如果驱动程序返回零，则它拥有该命令，并必须确保执行scp->scsi_done回调。注意：驱动程序可以在返回零之前调用scp->scsi_done，但在调用scp->scsi_done之后，不得返回除零以外的任何值。如果驱动程序返回非零值，则不得在任何时候执行命令的scsi_done回调
 *
 *  锁：直到2.6.36（包括2.6.36），在进入时持有struct Scsi_Host::host_lock（使用“irqsave”），并期望在返回时仍持有该锁。从2.6.37开始，queuecommand在没有任何锁的情况下被调用
 *
 *  调用上下文：在中断（软IRQ）或进程上下文中
 *
 *  注意：此函数应该相对快速。通常它不会等待IO完成。因此，scp->scsi_done回调将在该函数返回后的某个时间被调用（通常直接从中断服务例程）。在某些情况下（例如制造SCSI INQUIRY响应的伪适配器驱动程序），scp->scsi_done回调可能在此函数返回之前被调用。如果在一定时间内未调用scp->scsi_done回调，SCSI中间层将开始错误处理。如果在调用scp->scsi_done回调时在"result"中放置了CHECK CONDITION状态，则LLD驱动程序应执行自动感应并填充struct scsi_cmnd::sense_buffer数组。在中间层将命令排队到LLD之前，scsi_cmnd::sense_buffer数组会被清零
 *
 *  定义于：LLD
 **/
int queuecommand(struct Scsi_Host *shost, struct scsi_cmnd *scp)


/**
 *  slave_alloc - 在向新设备发送任何命令之前（即扫描之前），会调用此函数
 *  @sdp: 指向新设备（即将被扫描）的指针
 *
 *  如果成功返回0。任何其他返回值均视为错误，并忽略该设备
 *
 *  锁：无
 *
 *  调用上下文：进程
 *
 *  注意：允许驱动程序在设备初始扫描之前分配任何资源。相应的SCSI设备可能存在，但中间层即将对其进行扫描（即发送INQUIRY命令等）。如果找到设备，则slave_configure()将被调用；如果没有找到设备，则调用slave_destroy()
 *  更多详情请参阅include/scsi/scsi_host.h文件
 *
 *  可选定义于：LLD
 **/
int slave_alloc(struct scsi_device *sdp)


/**
 *  slave_configure - 在设备首次扫描后（即它响应了一个INQUIRY）对特定设备进行驱动微调
 *  @sdp: 刚刚连接的设备
 *
 *  如果成功返回0。任何其他返回值均视为错误，并将设备脱机。[脱机设备不会调用slave_destroy()，因此请清理资源。]
 *
 *  锁：无
 *
 *  调用上下文：进程
 *
 *  注意：允许驱动程序检查扫描代码所做的初始INQUIRY的响应，并采取适当措施
 *  更多详情请参阅include/scsi/scsi_host.h文件
 **/
int slave_configure(struct scsi_device *sdp)
```
```c
/**
 * slave_configure - 配置SCSI设备
 * @sdp: 要配置的SCSI设备结构体指针
 *
 * 返回值：无
 *
 * 锁定：无
 *
 * 调用上下文：进程
 *
 * 备注：对于给定设备的中层结构仍然存在，但即将被销毁。由该驱动程序为给定设备分配的任何设备特定资源应该在此时释放。不会再为此sdp实例发送进一步的命令。[然而，该设备将来可能会重新连接，在这种情况下，未来的slave_alloc()和slave_configure()调用将提供一个新的struct scsi_device实例。]
 *
 * 可选定义于：LLD
 **/
int slave_configure(struct scsi_device *sdp)


/**
 * slave_destroy - 给定设备即将关闭。所有活动已停止在该设备上
 * @sdp: 即将关闭的设备指针
 *
 * 返回值：无
 *
 * 锁定：无
 *
 * 调用上下文：进程
 *
 * 备注：对于给定设备的中层结构仍然存在，但即将被销毁。由该驱动程序为给定设备分配的任何设备特定资源应该在此时释放。不会再为此sdp实例发送进一步的命令。[然而，该设备将来可能会重新连接，在这种情况下，未来的slave_alloc()和slave_configure()调用将提供一个新的struct scsi_device实例。]
 *
 * 可选定义于：LLD
 **/
void slave_destroy(struct scsi_device *sdp)


数据结构
===============
struct scsi_host_template
-------------------------
每个LLD有一个“struct scsi_host_template”实例。通常初始化为驱动程序头文件中的文件作用域静态变量。这样未显式初始化的成员将被设置为0或NULL。
感兴趣的成员：

    name
        - 驱动程序名称（可以包含空格，请限制在少于80个字符）

    proc_name
        - 用于“/proc/scsi/<proc_name>/<host_no>”以及sysfs目录之一中的名称。因此“proc_name”应仅包含Unix文件名可接受的字符
``(*queuecommand)()`` 
        - 中层用来向LLD注入SCSI命令的主要回调函数
该结构在include/scsi/scsi_host.h中定义并有注释。

.. [#] 在极端情况下，一个驱动程序可能有多个实例，如果它控制几种不同类型的硬件（例如，处理ISA和PCI卡的LLD，并且每种类型都有一个单独的struct scsi_host_template实例）
struct Scsi_Host
----------------
每个LLD控制的主机（HBA）有一个struct Scsi_Host实例。struct Scsi_Host结构与“struct scsi_host_template”有许多共同的成员。当创建新的struct Scsi_Host实例（在hosts.c中的scsi_host_alloc()中）时，这些共同成员将从驱动程序的struct scsi_host_template实例初始化。感兴趣的成员：

    host_no
        - 用于标识此主机的系统范围内的唯一编号。从0开始按升序分配
can_queue
        - 必须大于0；不要向适配器发送超过can_queue数量的命令
this_id
        - 主机（SCSI启动器）的SCSI ID，或未知时为-1
sg_tablesize
        - 主机允许的最大分散/聚集元素数
设置为SG_ALL或更小以避免链接的SG列表
必须至少为1
```
### max_sectors
- 允许的扇区最大数量（通常为512字节）在单个SCSI命令中。默认值为0，这会导致设置为`SCSI_DEFAULT_MAX_SECTORS`（在`scsi_host.h`中定义），目前该值设置为1024。因此对于一个磁盘，当`max_sectors`未定义时，最大传输大小为512KB。请注意，这个大小可能不足以进行磁盘固件上传。

### cmd_per_lun
- 可以排队到由主机控制的设备上的SCSI命令的最大数量。可以通过LLD对`scsi_change_queue_depth()`的调用来覆盖此值。

### no_async_abort
- 1 => 不支持异步中止。
- 0 => 超时的命令将被异步中止。

### hostt
- 指向生成当前`Scsi_Host`实例的驱动程序中的`struct scsi_host_template`指针。

### hostt->proc_name
- LLD的名字。这是sysfs使用的驱动程序名字。

### transportt
- 指向驱动程序中的`struct scsi_transport_template`实例（如果有）。当前支持FC和SPI传输。

### sh_list
- 所有`struct Scsi_Host`实例的双向链表（目前按`host_no`升序排列）。

### my_devices
- 属于该主机的所有`struct scsi_device`实例的双向链表。

### hostdata[0]
- 在`struct Scsi_Host`末尾为LLD预留的区域。大小由`scsi_host_alloc()`或`scsi_register()`的第二个参数（名为`xtr_bytes`）设置。

### vendor_id
- 一个唯一值，用于标识为`Scsi_Host`提供LLD的供应商。主要用于验证特定供应商的消息请求。该值包含一个标识类型和一个供应商特定的值。详见`scsi_netlink.h`中有效的格式描述。

`scsi_host`结构体定义在`include/scsi/scsi_host.h`中。

### struct scsi_device
- 通常每个主机上的SCSI逻辑单元有一个此类结构的实例。连接到主机的SCSI设备通过通道号、目标ID和逻辑单元号（LUN）唯一标识。该结构定义在`include/scsi/scsi_device.h`中。

### struct scsi_cmnd
- 此类结构的实例传递SCSI命令到LLD，并将响应返回到中间层。SCSI中间层会确保不会超过`scsi_change_queue_depth()`（或`struct Scsi_Host::cmd_per_lun`）指示的数量来排队更多的SCSI命令。每个SCSI设备至少有一个`struct scsi_cmnd`实例。感兴趣的成员：

- `cmnd`
  - 包含SCSI命令的数组。

- `cmnd_len`
  - SCSI命令的长度（以字节为单位）。

- `sc_data_direction`
  - 数据阶段的数据传输方向。详见`include/linux/dma-mapping.h`中的`enum dma_data_direction`。

- `request_bufflen`
  - 要传输的数据字节数（如果没有数据阶段则为0）。

- `use_sg`
  - ==0 -> 没有分散/聚集列表，因此将数据传输到/from `request_buffer`。
  - >0 -> 在`request_buffer`中的分散/聚集列表（实际上是一个数组），具有`use_sg`个元素。

- `request_buffer`
  - 根据`use_sg`的设置，要么包含数据缓冲区，要么包含分散/聚集列表。分散/聚集元素由`include/linux/scatterlist.h`中的`struct scatterlist`定义。
完成
- 函数指针，当 SCSI 命令完成（成功或失败）时应由 LLD 调用。只有在 LLD 接受了该命令（即 queuecommand() 返回或即将返回 0）时才应调用。LLD 可以在 queuecommand() 完成之前调用 'done'。

结果
- 应在 LLD 调用 'done' 之前设置。值为 0 表示命令成功完成（所有数据已传输到或从 SCSI 目标设备）。'result' 是一个 32 位无符号整数，可以视为两个相关字节。SCSI 状态值位于最低有效位 (LSB)。参见 include/scsi/scsi.h 中的 status_byte() 和 host_byte() 宏及其相关常量。

sense_buffer
- 一个数组（最大大小：SCSI_SENSE_BUFFERSIZE 字节），当 SCSI 状态（'result' 的最低有效位）设置为 CHECK_CONDITION（2）时应写入。当 CHECK_CONDITION 设置时，如果 sense_buffer[0] 的高四位是 7，则中层将假定 sense_buffer 数组包含有效的 SCSI 感知缓冲区；否则，中层将发出 REQUEST_SENSE SCSI 命令来检索感知缓冲区。后一种策略在存在命令排队的情况下容易出错，因此 LLD 应始终“自动感知”。

设备
- 指向与此命令关联的 scsi_device 对象的指针。

resid
- LLD 应将此无符号整数设置为请求的传输长度（即'request_bufflen'）减去实际传输的字节数。'resid' 预设为 0，因此如果 LLD 无法检测不足（不应报告溢出），则可以忽略它。LLD 应在调用 'done' 之前设置 'resid'。最有趣的情况是从 SCSI 目标设备的数据传输（例如 READ）出现不足。

不足
- 如果实际传输的字节数少于这个数值，LLD 应将 (DID_ERROR << 16) 放入 'result'。许多 LLD 并未实现此检查，而一些实现了此检查的 LLD 只是将错误消息输出到日志而不是报告 DID_ERROR。LLD 实现 'resid' 更好。

建议 LLD 在从 SCSI 目标设备的数据传输（例如 READ）时设置 'resid'。特别是当这些数据传输具有 MEDIUM ERROR 和 HARDWARE ERROR 感知键（可能还有 RECOVERED ERROR）时，设置 'resid' 尤为重要。在这种情况下，如果 LLD 不确定接收了多少数据，则最安全的做法是指示没有接收到任何字节。例如：要指示没有接收到任何有效数据，LLD 可能会使用以下帮助函数：

    scsi_set_resid(SCpnt, scsi_bufflen(SCpnt));

其中 'SCpnt' 是指向 scsi_cmnd 对象的指针。要指示仅接收到三个 512 字节块，'resid' 可以这样设置：

    scsi_set_resid(SCpnt, scsi_bufflen(SCpnt) - (3 * 512));

scsi_cmnd 结构定义在 include/scsi/scsi_cmnd.h 中。

锁
====
每个 struct Scsi_Host 实例都有一个名为 struct Scsi_Host::default_lock 的自旋锁，在 scsi_host_alloc()（位于 hosts.c 中）中初始化。在同一函数中，struct Scsi_Host::host_lock 指针被初始化为指向 default_lock。此后，中层执行的所有锁定和解锁操作都使用 struct Scsi_Host::host_lock 指针。以前驱动程序可以覆盖 host_lock 指针，但现在不允许这样做。

自动感知
=========
自动感知（或 auto-sense）在 SAM-2 文档中定义为“当发生 CHECK CONDITION 状态时，与 SCSI 命令完成同时自动返回感知数据给应用程序客户端”。LLD 应执行自动感知。当 LLD 检测到 CHECK CONDITION 状态时，可以通过以下方式之一执行自动感知：

    a) 指示 SCSI 协议（例如 SCSI 并行接口 (SPI)）在此类响应上执行额外的数据输入阶段。
    b) 或者，LLD 自身发出 REQUEST SENSE 命令。

无论如何，当中层检测到 CHECK CONDITION 状态时，通过检查 struct scsi_cmnd::sense_buffer[0] 来决定 LLD 是否执行了自动感知。如果此字节的高四位为 7（或 0xf），则假定已执行自动感知。如果其值为其他值（且此字节在每次命令前初始化为 0），则中层将发出 REQUEST SENSE 命令。

在存在排队命令的情况下，“枢纽”可能会不同步，从而保持从失败命令到后续 REQUEST SENSE 的感知缓冲区数据。这就是为什么最好让 LLD 执行自动感知的原因。
自 lk 2.4 系列以来的更改
===========================
`io_request_lock` 已被多个更细粒度的锁所取代。与 LLD 相关的锁是 `struct Scsi_Host::host_lock`，每个 SCSI 主机有一个这样的锁。
旧的错误处理机制已被移除。这意味着 LLD 接口函数 `abort()` 和 `reset()` 已被移除。
`struct scsi_host_template::use_new_eh_code` 标志已被移除。
在 2.4 系列中，SCSI 子系统的配置描述与所有其他 Linux 子系统的配置描述一起汇总在 `Documentation/Configure.help` 文件中。而在 2.6 系列中，SCSI 子系统现在有了自己的（小得多的）`drivers/scsi/Kconfig` 文件，该文件包含了配置和帮助信息。
`struct SHT` 已重命名为 `struct scsi_host_template`。
增加了“热插拔初始化模型”及其许多支持函数。

致谢
=======
以下人员为本文档做出了贡献：

- Mike Anderson <andmike at us dot ibm dot com>
- James Bottomley <James dot Bottomley at hansenpartnership dot com>
- Patrick Mansfield <patmans at us dot ibm dot com>
- Christoph Hellwig <hch at infradead dot org>
- Doug Ledford <dledford at redhat dot com>
- Andries Brouwer <Andries dot Brouwer at cwi dot nl>
- Randy Dunlap <rdunlap at xenotime dot net>
- Alan Stern <stern at rowland dot harvard dot edu>

Douglas Gilbert  
dgilbert at interlog dot com  

2004年9月21日
