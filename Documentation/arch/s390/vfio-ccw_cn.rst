vfio-ccw：基本架构
==================

简介
----

此处我们描述了针对 Linux/s390 的 I/O 子通道设备的 vfio 支持。vfio-ccw 的动机是将子通道传递给虚拟机，而 vfio 是实现这一目标的方法。
与其它硬件架构不同，s390 定义了一种统一的 I/O 访问方法，即所谓的 Channel I/O。它具有其独特的访问模式：

- 通道程序在单独的（协）处理器上异步运行。
- 通道子系统将直接访问由调用者在通道程序中指定的任何内存，即不涉及 iommu。
因此，当我们为这些设备引入 vfio 支持时，我们通过中介设备 (mdev) 实现来实现它。vfio mdev 将被添加到 iommu 组，以便能够被 vfio 框架管理。并且我们为特殊 vfio I/O 区域添加读写回调函数，以将通道程序从 mdev 传递给其父设备（实际的 I/O 子通道设备），进行进一步的地址转换和执行 I/O 指令。

本文档无意详尽解释 s390 的 I/O 架构。更多信息/参考资料可在此处找到：

- 了解 Channel I/O 的良好起点：
  https://en.wikipedia.org/wiki/Channel_I/O
- s390 架构：
  s390 原理操作手册 (IBM 表号 SA22-7832)
- 现有的 QEMU 代码实现了简单的模拟通道子系统，也可以作为很好的参考。这使得更容易跟踪流程：
  qemu/hw/s390x/css.c

对于 vfio 中介设备框架：
- 文档/driver-api/vfio-mediated-device.rst

vfio-ccw 的动机
----------------

通常情况下，在 s390 上通过 QEMU/KVM 虚拟化的来宾仅能看到通过“Virtio Over Channel I/O (virtio-ccw)”传输的准虚拟化 virtio 设备。这使得 virtio 设备可以通过操作系统处理通道设备的标准算法发现。
然而这还不够。对于 s390 大多数使用标准 Channel I/O 机制的设备，我们还需要提供将它们传递给 QEMU 虚拟机的功能。
这包括没有 virtio 替代品的设备（例如磁带驱动器）或具有来宾希望利用的特定特性的设备。
为了将一个设备传递给来宾，我们希望使用与其他人相同接口，即 vfio。我们通过 vfio 中介设备框架以及子通道设备驱动程序 "vfio_ccw" 来实现对通道设备的这种 vfio 支持。

CCW 设备的访问模式
-------------------

s390 架构实现了所谓的通道子系统，为物理连接到系统的设备提供了统一视图。尽管 s390 硬件平台知道多种多样的外围附件，如磁盘设备（又称 DASD）、磁带、通信控制器等，但它们都可以通过一种明确定义的访问方式访问，并且以统一的方式呈现 I/O 完成：I/O 中断。
所有I/O操作都需要使用通道命令字（CCW）。CCW是对专门的I/O通道处理器的指令。一个通道程序是一系列由I/O通道子系统执行的CCW序列。要向通道子系统发出一个通道程序，需要构建一个操作请求块（ORB），它可以用来指示CCW的格式和其他控制信息给系统。操作系统通过SSCH（启动子通道）指令来通知I/O通道子系统开始执行该通道程序。然后，中央处理器就可以自由地执行非I/O指令，直到被中断。I/O完成的结果将通过中断响应块（IRB）的形式被中断处理程序接收。

回到vfio-ccw上，简而言之：

- ORB和通道程序在客户机内核中构建（使用客户机物理地址）
- ORB和通道程序传递给主机内核
- 主机内核将客户机物理地址转换为实际地址，并通过发出特权通道I/O指令（例如SSCH）开始I/O操作
- 通道程序在一个单独的处理器上异步运行
- I/O完成时，会通过I/O中断向主机发出信号
- 并且它将以IRB的形式复制到用户空间，再传递回给客户机

物理vfio-ccw设备及其子mdev设备
-----------------------------------

如上所述，我们通过mdev实现来实现vfio-ccw。
由于通道I/O没有IOMMU硬件支持，因此物理vfio-ccw设备没有IOMMU级别的转换或隔离。
子通道I/O指令都是特权指令。在处理I/O指令拦截时，vfio-ccw具有软件层面的监控和转换机制，确保通道程序在发送到硬件之前正确编程。
Within this implementation, we have two drivers for two types of devices:

- **The `vfio_ccw` driver for the physical subchannel device**
  - This is an I/O subchannel driver for the real subchannel device. It implements a set of callbacks and registers with the mdev framework as a parent (physical) device. As a result, mdev provides `vfio_ccw` with a generic interface (sysfs) to create mdev devices. A `vfio` mdev can then be created by `vfio_ccw` and added to the mediated bus. It is the `vfio` device that is added to an IOMMU group and a `vfio` group.
  - `vfio_ccw` also provides an I/O region to accept channel program requests from userspace and store I/O interrupt results for userspace to retrieve. To notify userspace of I/O completion, it offers an interface to set up an eventfd file descriptor for asynchronous signaling.

- **The `vfio_mdev` driver for the mediated `vfio ccw` device**
  - This is provided by the mdev framework. It is a `vfio` device driver for the mdev created by `vfio_ccw`.
  - It implements a set of `vfio` device driver callbacks, adds itself to a `vfio` group, and registers itself with the mdev framework as a mdev driver.
  - It uses a `vfio` IOMMU backend that uses the existing map and unmap `ioctl`s, but instead of programming them into an IOMMU for a device, it simply stores the translations for use by later requests. This means that a device programmed in a VM with guest physical addresses can have the `vfio` kernel convert that address to a process virtual address, pin the page, and program the hardware with the host physical address in one step.
  - For a mdev, the `vfio` IOMMU backend will not pin the pages during the `VFIO_IOMMU_MAP_DMA` `ioctl`. The mdev framework will only maintain a database of the iova<->vaddr mappings in this operation. They export `vfio_pin_pages` and `vfio_unpin_pages` interfaces from the `vfio` IOMMU backend for the physical devices to pin and unpin pages on demand.

Here is a high-level block diagram:

```
+-------------+
|             |
| +---------+ | mdev_register_driver() +--------------+
| |  Mdev   | +<-----------------------+              |
| |  bus    | |                        | vfio_mdev.ko |
| | driver  | +----------------------->+              |<-> VFIO user
| +---------+ |    probe()/remove()    +--------------+    APIs
|             |
|  MDEV CORE  |
|   MODULE    |
|   mdev.ko   |
| +---------+ | mdev_register_parent() +--------------+
| |Physical | +<-----------------------+              |
| | device  | |                        |  vfio_ccw.ko |<-> subchannel
| |interface| +----------------------->+              |     device
| +---------+ |       callback         +--------------+
+-------------+
```

The process of how these work together:
1. `vfio_ccw.ko` drives the physical I/O subchannel, and registers the physical device (with callbacks) with the mdev framework.
当vfio_ccw探测子通道设备时，它会向mdev框架注册设备指针和回调。在sysfs中设备节点下的与mdev相关的文件节点将为子通道设备创建，具体包括“mdev_create”、“mdev_destroy”以及“mdev_supported_types”。

2. 创建一个中介的vfio ccw设备
使用“mdev_create”的sysfs文件，我们需要手动创建一个（在我们的案例中仅需创建一个）中介设备。

3. vfio_mdev.ko驱动程序驱动中介的ccw设备
vfio_mdev也是vfio设备驱动程序。它将会探测mdev，并将其添加到iommu_group和vfio_group中。然后我们就可以将mdev传递给客户机。

VFIO-CCW 区域
--------------

vfio-ccw驱动程序公开MMIO区域以接收来自用户空间的请求并返回结果。
vfio-ccw I/O区域
-------------------

I/O区域用于接收来自用户空间的通道程序请求并存储供用户空间检索的I/O中断结果。该区域的定义如下：

```c
struct ccw_io_region {
  #define ORB_AREA_SIZE 12
          __u8    orb_area[ORB_AREA_SIZE];
  #define SCSW_AREA_SIZE 12
          __u8    scsw_area[SCSW_AREA_SIZE];
  #define IRB_AREA_SIZE 96
          __u8    irb_area[IRB_AREA_SIZE];
          __u32   ret_code;
} __packed__;
```

此区域始终可用。
在开始I/O请求时，orb_area应填充来宾ORB，scsw_area应填充虚拟子通道的SCSW。
irb_area存储I/O结果。
ret_code为每次访问该区域存储一个返回码。可能出现以下值：

``0``
  操作成功
``-EOPNOTSUPP``
  指定的ORB传输模式不受支持，或者SCSW指定了除启动功能之外的功能。
``-EIO``
  在设备未处于可接受请求的状态时发出请求，或者发生了内部错误。
``-EBUSY``
  子通道状态为待处理或忙碌，或者已有请求正在执行中。
``-EAGAIN``
  正在处理一个请求，调用者应重试。
``-EACCES``
  用于I/O操作的通道路径被发现为不可用。
``-ENODEV``
  设备被发现为不可用。
``-EINVAL``
  指定的ORB指定的链比255个ccws长，或者发生了内部错误。

vfio-ccw cmd 区域
-------------------

vfio-ccw cmd 区域用于从用户空间接收异步指令：

  #define VFIO_CCW_ASYNC_CMD_HSCH (1 << 0)
  #define VFIO_CCW_ASYNC_CMD_CSCH (1 << 1)

  struct ccw_cmd_region {
         __u32 command;
         __u32 ret_code;
  } __packed;

此区域通过类型VFIO_REGION_SUBTYPE_CCW_ASYNC_CMD提供。目前，CLEAR SUBCHANNEL 和 HALT SUBCHANNEL 使用了这个区域。`command` 指定了要发出的命令；`ret_code` 存储每次访问该区域的返回代码。可能出现以下值：

``0``
  操作成功。
```-ENODEV```
设备被检测为不可用。

```-EINVAL```
指定了除halt（停止）或clear（清除）之外的命令。

```-EIO```
在设备未处于可以接受请求的状态时发出了请求。

```-EAGAIN```
正在处理一个请求，调用者应重试。

```-EBUSY```
在处理停止请求时，子通道状态为等待或忙。

vfio-ccw schib 区域
----------------------

vfio-ccw schib 区域用于向用户空间返回子通道信息块 (SCHIB) 数据：

```c
  struct ccw_schib_region {
  #define SCHIB_AREA_SIZE 52
         __u8 schib_area[SCHIB_AREA_SIZE];
  } __packed;
```

此区域通过类型 `VFIO_REGION_SUBTYPE_CCW_SCHIB` 的区域暴露。
读取此区域会触发对关联硬件发出 STORE SUBCHANNEL 操作。

vfio-ccw crw 区域
----------------------

vfio-ccw crw 区域用于向用户空间返回通道报告字 (CRW) 数据：

```c
  struct ccw_crw_region {
         __u32 crw;
         __u32 pad;
  } __packed;
```

此区域通过类型 `VFIO_REGION_SUBTYPE_CCW_CRW` 的区域暴露。
读取此区域如果存在与此子通道相关的待处理 CRW（例如报告通道路径状态变化的 CRW），则返回 CRW；否则返回全零。如果有多个 CRW 待处理（可能包括链接的 CRW），再次读取此区域将返回下一个 CRW，直到没有更多待处理的 CRW 并返回全零为止。这类似于 STORE CHANNEL REPORT WORD 的工作方式。

vfio-ccw 操作细节
-----------------------

vfio-ccw 在 s390 平台上沿用了 vfio-pci 的做法，并使用 vfio-iommu-type1 作为 vfio IOMMU 后端。
* CCW 翻译 API
  这是一组以 `cp_` 开头的 API，用于进行 CCW（Channel Command Word）翻译。用户空间程序传递进来的 CCW 按照它们的访客物理内存地址组织起来。这些 API 将把这些 CCW 复制到内核空间，并通过将访客物理地址更新为对应的主机物理地址来组装一个可运行的内核通道程序。
需要注意的是，即使对于直接访问类型的 CCW，我们也必须使用 IDAL（Identifier Address List），因为被引用的内存可能位于任何位置，包括 2GB 以上的地址空间。
* vfio_ccw 设备驱动
  该驱动利用了 CCW 翻译 API 并引入了 vfio_ccw，这是您想要透传的 I/O 子通道设备的驱动程序。
vfio_ccw 实现了以下 vfio 的 ioctl（输入输出控制）命令：

    VFIO_DEVICE_GET_INFO
    VFIO_DEVICE_GET_IRQ_INFO
    VFIO_DEVICE_GET_REGION_INFO
    VFIO_DEVICE_RESET
    VFIO_DEVICE_SET_IRQS

  这提供了一个 I/O 区域，使得用户空间程序可以向内核传递一个通道程序，在将其发送给实际设备之前进行进一步的 CCW 翻译。
此外，它还提供了 SET_IRQ ioctl 命令来设置事件通知器，以便以异步方式通知用户空间程序 I/O 完成的情况。
vfio-ccw 的使用不限于 QEMU，尽管 QEMU 肯定是一个理解这些补丁如何工作的良好示例。以下是 QEMU 客户端触发的 I/O 请求处理流程的更详细说明（不包括错误处理）：
解释：

- Q1-Q7: QEMU 一侧的进程
- K1-K5: 内核一侧的进程
Q1
在初始化期间获取 I/O 区域信息
Q2
设置事件通知器和处理器以处理 I/O 完成

Q3
拦截一个 `ssch` 指令

Q4
编写访客通道程序及ORB，并写入I/O区域

K1
从访客复制到内核

K2
将访客通道程序转换为主机内核空间的通道程序，使其能为真实的设备运行。

K3
利用由 QEMU 传递进来的 orb 中包含的必要信息，向设备发出 ccwchain 指令。

K4
返回 ssch 的 CC 代码。

Q5
将 CC 代码返回给访客。

... ..

K5
中断处理程序获取 I/O 结果，并将结果写入 I/O 区域。
K6
向 QEMU 发送信号以获取结果
Q6
获取信号和事件处理程序从 I/O 区域读取结果
Q7
更新访客的 irb
限制
-----------

当前的 vfio-ccw 实现主要关注支持实现 DASD/ECKD 设备基本块设备功能（读/写）所需的命令。未来可能需要对某些命令进行特殊处理，例如与路径分组相关的任何内容。
DASD 是一种存储设备，而 ECKD 是一种数据记录格式。
关于 DASD 和 ECKD 的更多信息可在此处找到：
https://en.wikipedia.org/wiki/Direct-access_storage_device
https://en.wikipedia.org/wiki/Count_key_data

结合 QEMU 中的相关工作，我们现在可以在访客中启动传递的 DASD/ECKD 设备，并将其用作块设备。
当前代码允许访客通过 START SUBCHANNEL 启动通道程序，并发出 HALT SUBCHANNEL、CLEAR SUBCHANNEL 以及 STORE SUBCHANNEL 指令。
目前，所有的通道程序都会被预取，无论 ORB 中的 p-bit 设置如何。因此，不支持自修改的通道程序。正因为如此，初始程序加载 (IPL) 必须由用户空间/客户机程序作为特殊情况处理；这一点已经在 QEMU 4.1 版本及之后的 s390-ccw BIOS 中实现。
vfio-ccw 只支持经典（命令模式）的通道 I/O。传输模式 (HPF) 不受支持。
目前不支持 QDIO 子通道。除了 DASD/ECKD 之外的经典设备可能可以工作，但尚未经过测试。

参考文献：
---------
1. ESA/s390 操作原理手册 (IBM 表单号：SA22-7832)
2. ESA/390 公共 I/O 设备命令手册 (IBM 表单号：SA22-7204)
3. https://en.wikipedia.org/wiki/Channel_I/O
4. 文档/arch/s390/cds.rst
5. 文档/driver-api/vfio.rst
6. 文档/driver-api/vfio-mediated-device.rst
