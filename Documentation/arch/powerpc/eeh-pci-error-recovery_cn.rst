==========================
PCI 总线 EEH 错误恢复
==========================

林纳斯·韦普斯塔 <linas@austin.ibm.com>

2005 年 1 月 12 日


概述：
---------
基于 IBM POWER 的 pSeries 和 iSeries 计算机包含具有扩展功能的 PCI 总线控制器芯片，这些扩展功能可以检测和报告多种 PCI 总线错误情况。这些特性被称为“EEH”，即“增强型错误处理”。EEH 硬件特性允许清除 PCI 总线错误并重新启动 PCI 卡，而无需重启操作系统。
这与传统的 PCI 错误处理方式不同，在传统方式中，PCI 芯片直接连接到 CPU，错误会导致 CPU 机器检查/停止运行的情况，使整个 CPU 停止工作。
另一种“传统”方法是忽略这些错误，这可能导致用户数据或内核数据损坏、适配器挂起/无响应或系统崩溃/锁定。因此，EEH 的理念是通过保护操作系统免受 PCI 错误的影响，并赋予操作系统“重启”/恢复单个 PCI 设备的能力来提高其可靠性和健壮性。
未来基于 PCI-E 规范的其他供应商系统可能也具备类似的功能。

EEH 错误的原因：
--------------------
最初设计 EEH 是为了防止硬件故障，例如由于高温、湿度、灰尘、振动和不良电气连接导致 PCI 卡失效。在实际使用中观察到的绝大多数 EEH 错误是由安装不当的 PCI 卡或者不幸的是，由设备驱动程序错误、设备固件错误以及有时 PCI 卡硬件错误引起的。
最常见的软件错误是导致设备尝试向系统内存中未为此卡预留 DMA 访问权限的位置进行 DMA 操作。这是一个强大的特性，因为它阻止了由错误的 DMA 导致的静默内存损坏。在过去几年中，已经通过这种方式发现了许多设备驱动程序错误并进行了修复。其他可能导致 EEH 错误的原因包括数据或地址线奇偶校验错误（例如，由于安装不当的卡导致的不良电气连接）以及 PCI-X 分割完成错误（由于软件、设备固件或设备 PCI 硬件错误）。
大多数“真正的硬件故障”可以通过物理移除和重新安装 PCI 卡来解决。

检测与恢复：
----------------------
以下将提供一个关于如何检测和从 EEH 错误中恢复的一般性概述，随后会概述当前 Linux 内核实现的方式。实际实现可能会发生变化，一些细节仍在讨论之中。如果其他架构实现了类似功能，这些讨论可能会受到影响。
当 PCI 主机桥接器（PHB，连接 PCI 总线到系统 CPU 电子组件的总线控制器）检测到 PCI 错误时，它会“隔离”受影响的 PCI 卡。隔离将阻止所有写操作（无论是从系统到卡还是从卡到系统），并且会使所有读取返回全 ff 的值（对于 8/16/32 位读取分别为 0xff、0xffff 和 0xffffffff）。
选择这个值是因为如果设备从插槽中物理拔出，你也会得到同样的值。
这包括访问 PCI 内存、I/O 空间以及 PCI 配置空间。然而，中断将继续被传递。
检测和恢复工作借助 ppc64 固件完成。Linux 内核与固件之间的编程接口被称为 RTAS（运行时抽象服务）。Linux 内核不应该直接访问 PCI 芯片组中的 EEH 功能，主要是因为市面上有多种不同的芯片组，每种都有其特定的接口和特性。固件提供了一个统一的抽象层，可以兼容所有 pSeries 和 iSeries 硬件，并保持向前兼容性。
如果操作系统或设备驱动程序怀疑某个 PCI 插槽已被 EEH 隔离，可以通过调用固件来确认这种情况。如果是这样，那么设备驱动程序应该将自己置于一个一致的状态（因为它无法完成任何挂起的工作），并开始恢复该卡。通常的恢复过程包括重置 PCI 设备（将 PCI #RST 线保持高位两秒），接着设置设备配置空间（例如基址寄存器（BAR）、延迟计时器、缓存行大小、中断线等）。之后是设备驱动程序的重新初始化。在最坏的情况下，可以切换插槽的电源（至少对于支持热插拔的插槽）。原则上，设备驱动程序之上的层级可能不需要知道 PCI 卡已通过这种方式“重启”；理想情况下，当卡片正在重置时，以太网/磁盘/USB 的 I/O 操作最多只会暂停。
如果经过三到四次重置后仍无法恢复卡片，内核/设备驱动程序应假设最坏的情况，即卡片完全损坏，并向系统管理员报告此错误。
此外，错误信息会通过 RTAS 报告，并通过 syslogd（/var/log/messages）通知系统管理员发生了 PCI 重置。
处理故障适配器的正确方法是使用标准的 PCI 热插拔工具移除并替换死卡。

当前 PPC64 Linux EEH 实现
------------------------------
目前，已经实现了一种通用的 EEH 恢复机制，因此无需修改各个设备驱动程序以支持 EEH 恢复。这种通用机制基于 PCI 热插拔基础设施，并将事件向上层用户空间/udev 基础设施传递。以下是实现方式的详细描述：
EEH 必须在引导过程非常早期就在 PHB 中启用，且在 PCI 插槽进行热插拔时启用。前者由 arch/powerpc/platforms/pseries/eeh.c 中的 eeh_init() 完成，后者则通过 drivers/pci/hotplug/pSeries_pci.c 调用 ee.h 的代码实现。
在对 PCI 设备进行扫描之前必须启用 EEH。
当前的 Power5 硬件若不启用 EEH 将无法工作；尽管较旧的 Power4 可以禁用 EEH 运行。实际上，EEH 已经无法被关闭。PCI 设备必须向 EEH 代码注册；EEH 代码需要了解 PCI 设备的 I/O 地址范围以便于检测错误。给定任意地址，pci_get_device_by_addr() 函数将找到与该地址关联的 PCI 设备（如果存在的话）。
默认的 `arch/powerpc/include/asm/io.h` 中的宏 `readb()`、`inb()`、`insb()` 等包含了一个检查，用于判断 I/O 读取操作是否返回了全 `0xff` 的值。如果返回的是全 `0xff`，则这些宏会调用 `eeh_dn_check_failure()` 函数，该函数接着询问固件这些全 `0xff` 的值是否是真正的 EEH（Enhanced Error Handling，增强错误处理）错误的标志。如果不是，则继续正常处理。所有这些误报或“假阳性”事件的总数可以在 `/proc/ppc64/eeh` 文件中查看（此文件的内容可能会发生变化）。通常，这些误报大多发生在启动过程中扫描 PCI 总线时，此时大量的 `0xff` 读取操作是总线扫描过程的一部分。

如果检测到插槽冻结，`arch/powerpc/platforms/pseries/eeh.c` 中的代码会将堆栈跟踪信息打印到系统日志 (`/var/log/messages`)。这种堆栈跟踪对于设备驱动程序作者来说非常有用，因为它可以帮助他们确定 EEH 错误是在何时被检测到的，因为错误本身通常发生在检测之前的一段时间内。

接下来，它使用 Linux 内核的通知器链/工作队列机制来让任何关心的组件了解失败情况。设备驱动程序或其他内核组件可以使用 `eeh_register_notifier(struct notifier_block *)` 来了解有关 EEH 事件的信息。事件将包括指向 PCI 设备的指针、设备节点和一些状态信息。接收方可以根据需要采取行动；本节稍后会进一步描述默认处理程序。

为了帮助设备恢复，`eeh.c` 导出了以下函数：

- `rtas_set_slot_reset()`
  - 断言 PCI #RST 线持续 1/8 秒。
- `rtas_configure_bridge()`
  - 请求固件配置位于 PCI 插槽拓扑下方的所有 PCI 桥接器。
- `eeh_save_bars()` 和 `eeh_restore_bars()`
  - 保存和恢复设备及其下层设备的 PCI 配置空间信息。

在 `drivers/pci/hotplug/pSeries_pci.c` 中实现了一个 EEH 通知器块事件处理器，名为 `handle_eeh_events()`。它首先保存设备的基本地址寄存器 (BAR)，然后调用 `rpaphp_unconfig_pci_adapter()`。这个最后的调用会导致设备驱动程序停止运行，从而触发用户空间中的 uevent 事件。这会触发用户空间脚本执行诸如 "ifdown eth0" 对于以太网卡等命令。之后，处理器会休眠 5 秒，希望给用户空间脚本足够的时间完成其任务。接着重置 PCI 卡，重新配置设备的 BAR，并且重新配置其下的任何桥接器。最后调用 `rpaphp_enable_pci_slot()` 来重启设备驱动程序，并触发更多用户空间事件（例如，对于以太网卡，会调用 "ifup eth0"）。
### 设备关闭与用户空间事件
本节记录了当PCI插槽被取消配置时所发生的情况，重点关注设备驱动程序如何关闭以及事件如何传递给用户空间脚本。

以下是一个示例事件序列，在EEH重置的第一阶段中触发设备驱动程序的关闭函数调用。下面的序列是pcnet32设备驱动程序的一个例子：

    rpa_php_unconfig_pci_adapter (struct slot *)  // 在rpaphp_pci.c中
    {
      调用
      pci_remove_bus_device (struct pci_dev *) // 在/drivers/pci/remove.c中
      {
        调用
        pci_destroy_dev (struct pci_dev *)
        {
          调用
          device_unregister (&dev->dev) // 在/drivers/base/core.c中
          {
            调用
            device_del (struct device *)
            {
              调用
              bus_remove_device() // 在/drivers/base/bus.c中
              {
                调用
                device_release_driver()
                {
                  调用
                  struct device_driver->remove() 这实际上只是
                  pci_device_remove()  // 在/drivers/pci/pci_driver.c中
                  {
                    调用
                    struct pci_driver->remove() 实际上是
                    pcnet32_remove_one() // 在/drivers/net/pcnet32.c中
                    {
                      调用
                      unregister_netdev() // 在/net/core/dev.c中
                      {
                        调用
                        dev_close()  // 在/net/core/dev.c中
                        {
                           调用 dev->stop();
                           实际上是 pcnet32_close() // 在pcnet32.c中
                           {
                             执行所需的关闭操作
                           }
                        }
                     }
                   清除pcnet32设备驱动程序内存
                }
     }}}}}}

在/drivers/pci/pci_driver.c中，
struct device_driver->remove() 实际上是 pci_device_remove()
它调用 struct pci_driver->remove() 即 pcnet32_remove_one()
它调用 unregister_netdev()  (在net/core/dev.c中)
它调用 dev_close()  (在net/core/dev.c中)
它调用 dev->stop() 实际上是 pcnet32_close()
然后执行适当的关闭操作

---

接下来是当PCI设备被取消配置时发送到用户空间的事件的类似堆栈跟踪：

  rpa_php_unconfig_pci_adapter() {             // 在rpaphp_pci.c中
    调用
    pci_remove_bus_device (struct pci_dev *) { // 在/drivers/pci/remove.c中
      调用
      pci_destroy_dev (struct pci_dev *) {
        调用
        device_unregister (&dev->dev) {        // 在/drivers/base/core.c中
          调用
          device_del(struct device * dev) {    // 在/drivers/base/core.c中
            调用
            kobject_del() {                    // 在/libs/kobject.c中
              调用
              kobject_uevent() {               // 在/libs/kobject.c中
                调用
                kset_uevent() {                // 在/lib/kobject.c中
                  调用
                  kset->uevent_ops->uevent()   实际上是
                  调用
                  dev_uevent() {               // 在/drivers/base/core.c中
                    调用
                    dev->bus->uevent() 实际上是
                    pci_uevent () {            // 在/drivers/pci/hotplug.c中
                      输出设备名称等信息...
}
                 }
                 然后 kobject_uevent() 向用户空间发送一个netlink事件
                 --> 用户空间事件
                 （在早期启动期间，没有监听netlink事件，kobject_uevent()会执行uevent_helper[]，运行事件处理程序/sbin/hotplug）
             }
           }
           kobject_del() 然后调用 sysfs_remove_dir()，这将触发任何监视/sysfs的用户空间守护进程，并注意到删除事件
当前设计的优点和缺点
-----------------------------
当前EEH软件恢复设计存在几个问题，这些问题可能在未来版本中得到解决。但首先需要注意的是，当前设计的最大优点是无需对各个设备驱动程序进行修改，因此该设计具有广泛的适用性。
最大的负面影响是可能会干扰不需要受到干扰的网络守护进程和文件系统：
- 一个较小的问题是重置网络卡会导致用户空间的ifdown/ifup连续中断，这可能会干扰那些甚至不需要知道PCI卡正在重启的网络守护进程。
- 更严重的问题是，对于SCSI设备而言，相同的重置会造成已挂载文件系统的混乱。脚本无法事后卸载文件系统而不刷新待处理缓冲区，但这实际上是不可能的，因为I/O已经停止。因此，理想情况下，重置应该发生在或低于块层，以便文件系统不会受到影响。
Reiserfs不接受从块设备返回的错误。
Ext3fs 看起来具有容忍性，会不断重试读写操作直到成功。这两种情况在此场景下都只是经过了初步测试。

SCSI通用子系统已经内置了执行SCSI设备重置、SCSI总线重置和SCSI主机总线适配器（HBA）重置的代码。如果SCSI命令失败，这些重置会被串联成一系列尝试性的重置操作。这些操作对块层来说是完全透明的。将EEH重置加入这一系列事件中是非常自然的做法。

- 如果根设备发生SCSI错误，除非系统管理员有先见之明使用ramdisk/tmpfs运行/bin、/sbin、/etc、/var等目录，否则一切都会丢失。

结论
------
已经有了向前进展...
