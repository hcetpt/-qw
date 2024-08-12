VFIO - “虚拟功能 I/O” [1]_
=============================

许多现代系统现在提供了DMA和中断重映射设施，以帮助确保I/O设备在其分配的边界内行为。这包括具有AMD-Vi和Intel VT-d的x86硬件、具有可分区端点(PEs)的POWER系统以及如Freescale PAMU等嵌入式PowerPC系统。VFIO驱动程序是一个IOMMU/设备无关的框架，用于在安全、IOMMU保护的环境中向用户空间暴露直接设备访问权限。换句话说，这允许安全[2]_、非特权用户空间驱动程序。
为什么我们需要这样做？当为获得尽可能高的I/O性能而配置时，虚拟机通常会利用直接设备访问（“设备分配”）。从设备和主机的角度来看，这仅仅将VM转换为一个用户空间驱动程序，具有显著降低延迟、提高带宽和直接使用裸金属设备驱动程序[3]_的优点。
一些应用程序，特别是在高性能计算领域，也受益于低开销的用户空间中的直接设备访问。示例包括网络适配器（通常是基于非TCP/IP的）和计算加速器。在VFIO出现之前，这些驱动程序必须要么经历完整的开发周期成为适当的上游驱动程序，要么在树外维护，或者使用UIO框架，该框架没有IOMMU保护的概念，有限的中断支持，并且需要根权限来访问诸如PCI配置空间之类的东西。
VFIO驱动程序框架旨在统一这些，取代特定于KVM PCI的设备分配代码，并提供比UIO更安全、功能更丰富的用户空间驱动程序环境。
组、设备和IOMMUs
-----------------

设备是任何I/O驱动程序的主要目标。设备通常创建一个由I/O访问、中断和DMA组成的编程接口。不深入讨论这些细节，DMA是维护安全环境最关键的因素，因为允许设备对系统内存进行读写访问对整个系统的完整性构成了最大的风险。
为了帮助减轻这种风险，许多现代IOMMUs现在在其接口中结合了隔离特性，在许多情况下，这些接口仅用于翻译（即解决有限地址空间设备的寻址问题）。通过这种方式，现在可以将设备彼此隔离，并与任意内存访问隔离，从而允许将设备安全地直接分配到虚拟机中。
但是，这种隔离并不总是在单个设备的粒度级别上。即使当IOMMU能够做到这一点时，设备属性、互连和IOMMU拓扑结构中的每个因素都可能减少这种隔离。
例如，单个设备可能是更大多功能封装的一部分。虽然IOMMU可能能够区分封装内的设备，但封装可能不需要设备之间的交易到达IOMMU。这可以从具有功能间后门的多功能PCI设备到不具备PCI-ACS（访问控制服务）能力的桥接允许重定向而不必到达IOMMU的例子。拓扑也可以在隐藏设备方面发挥作用。PCIe-to-PCI桥接掩盖了其后面的设备，使交易看起来像是来自桥接本身。显然，IOMMU设计也是一个主要因素。
因此，尽管在大多数情况下IOMMU可能具有设备级别的粒度，但任何系统都可能遭受粒度的减少。因此，IOMMU API支持IOMMU组的概念。组是一组设备，这些设备与其他系统中的所有其他设备隔离。因此，组是VFIO使用的所有权单位。
虽然组是最小的必须用于确保安全用户访问的粒度，但它不一定是最优选的粒度。在使用页表的IOMMUs中，可能可以在不同的组之间共享一组页表，减少了平台（减少TLB冲突，减少重复页表）和用户（仅编程一组转换）的开销。出于这个原因，VFIO使用容器类，它可以容纳一个或多个组。通过简单打开/dev/vfio/vfio字符设备即可创建容器。
单独来看，容器本身提供的功能非常有限，除了几个版本和扩展查询接口外，其他都被锁定。用户需要在容器中添加一个组以实现更高级别的功能。为此，用户首先需要确定与所需设备关联的组。这可以通过下面示例中描述的`sysfs`链接来完成。通过将设备从主机驱动程序解绑定并绑定到VFIO驱动程序，一个新的VFIO组将为该组出现在`/dev/vfio/$GROUP`的位置，其中`$GROUP`是该设备所属的IOMMU组编号。如果IOMMU组包含多个设备，则每个设备都需要绑定到VFIO驱动程序才能允许对VFIO组的操作（如果没有可用的VFIO驱动程序，仅将设备从主机驱动程序解绑定也是足够的；这将使组变得可用，但不是那个特定的设备）。待定 - 禁用驱动程序探测/锁定设备的接口。

一旦组准备就绪，就可以通过打开VFIO组字符设备（`/dev/vfio/$GROUP`）并使用VFIO_GROUP_SET_CONTAINER ioctl，并传递之前打开的容器文件的文件描述符，将其添加到容器中。如果希望并且如果IOMMU驱动程序支持在组之间共享IOMMU上下文，则可以将多个组设置为相同的容器。如果一个组无法设置到已有组的容器中，则需要使用一个新的空容器。

有了附加到容器中的组（或多个组），剩下的ioctl命令便可用，从而能够访问VFIO IOMMU接口。此外，现在可以使用VFIO组文件描述符上的ioctl命令获取组内每个设备的文件描述符。VFIO设备API包括用于描述设备、I/O区域及其在设备描述符上的读写/mmap偏移量的ioctl命令，以及用于描述和注册中断通知的机制。

### VFIO 使用示例

假设用户想要访问PCI设备0000:06:0d.0：

```
$ readlink /sys/bus/pci/devices/0000:06:0d.0/iommu_group
../../../../kernel/iommu_groups/26
```

因此这个设备位于IOMMU组26中。此设备在PCI总线上，因此用户将利用vfio-pci来管理这个组：

```
# modprobe vfio-pci
```

将这个设备绑定到vfio-pci驱动程序会为这个组创建VFIO组字符设备：

```
$ lspci -n -s 0000:06:0d.0
06:0d.0 0401: 1102:0002 (rev 08)
# echo 0000:06:0d.0 > /sys/bus/pci/devices/0000:06:0d.0/driver/unbind
# echo 1102 0002 > /sys/bus/pci/drivers/vfio-pci/new_id
```

现在我们需要查看组内还有哪些其他的设备以便释放它们供VFIO使用：

```
$ ls -l /sys/bus/pci/devices/0000:06:0d.0/iommu_group/devices
total 0
lrwxrwxrwx. 1 root root 0 Apr 23 16:13 0000:00:1e.0 ->
	../../../../devices/pci0000:00/0000:00:1e.0
lrwxrwxrwx. 1 root root 0 Apr 23 16:13 0000:06:0d.0 ->
	../../../../devices/pci0000:00/0000:00:1e.0/0000:06:0d.0
lrwxrwxrwx. 1 root root 0 Apr 23 16:13 0000:06:0d.1 ->
	../../../../devices/pci0000:00/0000:00:1e.0/0000:06:0d.1
```

这个设备后面有一个PCIe-to-PCI桥接器[4]，因此我们还需要按照上述相同的过程将设备0000:06:0d.1添加到组中。设备0000:00:1e.0是一个桥接器，当前没有主机驱动程序，因此不需要将这个设备绑定到vfio-pci驱动程序（目前vfio-pci不支持PCI桥接器）。
最后一步是在需要非特权操作时向用户提供对组的访问权限（注意`/dev/vfio/vfio`本身不具备任何能力，因此系统预期将其设置为模式0666）：

```
# chown user:user /dev/vfio/26
```

现在用户可以完全访问该组的所有设备和IOMMU，并可以如下方式访问它们：

```c
int container, group, device, i;
struct vfio_group_status group_status =
					{ .argsz = sizeof(group_status) };
struct vfio_iommu_type1_info iommu_info = { .argsz = sizeof(iommu_info) };
struct vfio_iommu_type1_dma_map dma_map = { .argsz = sizeof(dma_map) };
struct vfio_device_info device_info = { .argsz = sizeof(device_info) };

/* 创建一个新的容器 */
container = open("/dev/vfio/vfio", O_RDWR);

if (ioctl(container, VFIO_GET_API_VERSION) != VFIO_API_VERSION)
	/* 未知API版本 */

if (!ioctl(container, VFIO_CHECK_EXTENSION, VFIO_TYPE1_IOMMU))
	/* 不支持我们想要的IOMMU驱动程序。 */

/* 打开组 */
group = open("/dev/vfio/26", O_RDWR);

/* 测试组是否可行且可用 */
ioctl(group, VFIO_GROUP_GET_STATUS, &group_status);

if (!(group_status.flags & VFIO_GROUP_FLAGS_VIABLE))
	/* 组不可行（即，不是所有设备都已绑定给vfio） */

/* 将组添加到容器 */
ioctl(group, VFIO_GROUP_SET_CONTAINER, &container);

/* 启用我们想要的IOMMU模型 */
ioctl(container, VFIO_SET_IOMMU, VFIO_TYPE1_IOMMU);

/* 获取额外的IOMMU信息 */
ioctl(container, VFIO_IOMMU_GET_INFO, &iommu_info);

/* 分配一些空间并设置DMA映射 */
dma_map.vaddr = mmap(0, 1024 * 1024, PROT_READ | PROT_WRITE,
			     MAP_PRIVATE | MAP_ANONYMOUS, 0, 0);
dma_map.size = 1024 * 1024;
dma_map.iova = 0; /* 1MB从设备视图开始于0x0 */
dma_map.flags = VFIO_DMA_MAP_FLAG_READ | VFIO_DMA_MAP_FLAG_WRITE;

ioctl(container, VFIO_IOMMU_MAP_DMA, &dma_map);

/* 获取设备的文件描述符 */
device = ioctl(group, VFIO_GROUP_GET_DEVICE_FD, "0000:06:0d.0");

/* 测试和设置设备 */
ioctl(device, VFIO_DEVICE_GET_INFO, &device_info);

for (i = 0; i < device_info.num_regions; i++) {
    struct vfio_region_info reg = { .argsz = sizeof(reg) };

    reg.index = i;

    ioctl(device, VFIO_DEVICE_GET_REGION_INFO, &reg);

    /* 设置映射... 读写偏移量，mmaps
     * 对于PCI设备，配置空间是一个区域 */
}

for (i = 0; i < device_info.num_irqs; i++) {
    struct vfio_irq_info irq = { .argsz = sizeof(irq) };

    irq.index = i;

    ioctl(device, VFIO_DEVICE_GET_IRQ_INFO, &irq);

    /* 设置IRQs... eventfds, VFIO_DEVICE_SET_IRQS */
}

/* 重置设备并启动... */
ioctl(device, VFIO_DEVICE_RESET);
```

### IOMMUFD 和 vfio_iommu_type1

IOMMUFD是新的用户API，用于从用户空间管理I/O页表。它旨在成为提供先进的用户空间DMA特性（如嵌套转换[5]、PASID[6]等）的门户，同时也为现有的VFIO_TYPE1v2_IOMMU用例提供向后兼容的接口。最终，vfio_iommu_type1驱动程序以及过时的vfio容器和组模型预计将被弃用。
IOMMUFD向后兼容接口可以通过两种方式启用：
第一种方法是通过`CONFIG_IOMMUFD_VFIO_CONTAINER`配置内核，在这种情况下，IOMMUFD子系统透明地提供了VFIO容器和IOMMU后端接口所需的全部基础设施。另一种方式是如果简单地将VFIO容器接口（即`/dev/vfio/vfio`）符号链接到`/dev/iommu`。请注意，在撰写本文时，兼容模式相对于`VFIO_TYPE1v2_IOMMU`并非完全具备所有功能（例如DMA映射MMIO），并且不尝试提供与`VFIO_SPAPR_TCE_IOMMU`接口的兼容性。因此，目前一般不建议从原生VFIO实现切换到IOMMUFD的兼容接口。
长远来看，VFIO用户应迁移到通过下面描述的cdev接口访问设备，并通过IOMMUFD提供的接口进行原生访问。

VFIO 设备 cdev
----------------

传统上，用户通过VFIO_GROUP_GET_DEVICE_FD在VFIO组中获取设备文件描述符(fd)。
当`CONFIG_VFIO_DEVICE_CDEV=y`时，用户现在可以直接通过打开字符设备`/dev/vfio/devices/vfioX`来获取设备fd，其中"X"是由VFIO为注册设备唯一分配的数字。
cdev接口不支持noiommu设备，因此如果需要noiommu，用户应使用传统的组接口。
cdev仅与IOMMUFD一起工作。VFIO驱动程序和应用程序都必须适应新的cdev安全模型，该模型要求在开始实际使用设备之前使用`VFIO_DEVICE_BIND_IOMMUFD`声明DMA所有权。一旦BIND成功，用户就可以完全访问VFIO设备。
VFIO设备cdev不依赖于VFIO组/容器/IOMMU驱动程序。因此，在不存在任何传统VFIO应用的环境中，这些模块可以被完全编译出去。
截至目前，SPAPR尚不支持IOMMUFD。因此，它也无法支持设备cdev。
VFIO 设备 cdev 访问仍然受到 IOMMU 组语义的约束，也就是说，一个组只能有一个 DMA 所有者。属于同一组的设备不能绑定到多个 iommufd_ctx 或在原生内核和 vfio 总线驱动程序或其他支持 driver_managed_dma 标志的驱动程序之间共享。违反此所有权要求将在 VFIO_DEVICE_BIND_IOMMUFD ioctl 失败，该 ioctl 控制对设备的完整访问。

### 设备 cdev 示例

假设用户想要访问 PCI 设备 0000:6a:01.0：

```bash
$ ls /sys/bus/pci/devices/0000:6a:01.0/vfio-dev/
vfio0
```

该设备因此表示为 vfio0。用户可以验证其存在：

```bash
$ ls -l /dev/vfio/devices/vfio0
crw------- 1 root root 511, 0 Feb 16 01:22 /dev/vfio/devices/vfio0
$ cat /sys/bus/pci/devices/0000:6a:01.0/vfio-dev/vfio0/dev
511:0
$ ls -l /dev/char/511\:0
lrwxrwxrwx 1 root root 21 Feb 16 01:22 /dev/char/511:0 -> ../vfio/devices/vfio0
```

如果需要无特权操作，则向用户提供对该设备的访问权限：

```bash
$ chown user:user /dev/vfio/devices/vfio0
```

最后用户可以通过以下方式获取 cdev 文件描述符：

```c
cdev_fd = open("/dev/vfio/devices/vfio0", O_RDWR);
```

打开的 cdev_fd 不给予用户除绑定 cdev_fd 到 iommufd 之外的任何访问设备的权限。之后，设备将完全可访问，包括将其附加到 IOMMUFD IOAS/HWPT 以启用用户空间 DMA：

```c
struct vfio_device_bind_iommufd bind = {
	.argsz = sizeof(bind),
	.flags = 0,
};
struct iommu_ioas_alloc alloc_data  = {
	.size = sizeof(alloc_data),
	.flags = 0,
};
struct vfio_device_attach_iommufd_pt attach_data = {
	.argsz = sizeof(attach_data),
	.flags = 0,
};
struct iommu_ioas_map map = {
	.size = sizeof(map),
	.flags = IOMMU_IOAS_MAP_READABLE |
		 IOMMU_IOAS_MAP_WRITEABLE |
		 IOMMU_IOAS_MAP_FIXED_IOVA,
	.__reserved = 0,
};

iommufd = open("/dev/iommu", O_RDWR);

bind.iommufd = iommufd;
ioctl(cdev_fd, VFIO_DEVICE_BIND_IOMMUFD, &bind);

ioctl(iommufd, IOMMU_IOAS_ALLOC, &alloc_data);
attach_data.pt_id = alloc_data.out_ioas_id;
ioctl(cdev_fd, VFIO_DEVICE_ATTACH_IOMMUFD_PT, &attach_data);

/* 分配一些空间并设置 DMA 映射 */
map.user_va = (int64_t)mmap(0, 1024 * 1024, PROT_READ | PROT_WRITE,
			    MAP_PRIVATE | MAP_ANONYMOUS, 0, 0);
map.iova = 0; /* 从设备视角来看，1MB 从 0x0 开始 */
map.length = 1024 * 1024;
map.ioas_id = alloc_data.out_ioas_id;

ioctl(iommufd, IOMMU_IOAS_MAP, &map);

/* 其他设备操作如 "VFIO 使用示例" 中所述 */
```

### VFIO 用户 API

请参阅 `include/uapi/linux/vfio.h` 获取完整的 API 文档。

### VFIO 总线驱动程序 API

VFIO 总线驱动程序（例如 vfio-pci）仅使用少数几个与 VFIO 核心的接口。当设备绑定和解绑到驱动程序时，会调用以下接口：

```c
int vfio_register_group_dev(struct vfio_device *device);
int vfio_register_emulated_iommu_dev(struct vfio_device *device);
void vfio_unregister_group_dev(struct vfio_device *device);
```

驱动程序应在自己的结构中嵌入 vfio_device，并使用 `vfio_alloc_device()` 分配结构，并可以注册 @init/@release 回调来管理围绕 vfio_device 的任何私有状态：

```c
vfio_alloc_device(dev_struct, member, dev, ops);
void vfio_put_device(struct vfio_device *device);
```

`vfio_register_group_dev()` 向核心指示开始跟踪指定 dev 的 iommu_group 并将 dev 注册为由 VFIO 总线驱动程序拥有。一旦 `vfio_register_group_dev()` 返回，用户空间就可能开始访问驱动程序，因此驱动程序应确保在调用它之前完全准备就绪。驱动程序提供了一个类似于文件操作结构的 ops 结构用于回调：

```c
struct vfio_device_ops {
	char	*name;
	int	(*init)(struct vfio_device *vdev);
	void	(*release)(struct vfio_device *vdev);
	int	(*bind_iommufd)(struct vfio_device *vdev,
				 struct iommufd_ctx *ictx, u32 *out_device_id);
	void	(*unbind_iommufd)(struct vfio_device *vdev);
	int	(*attach_ioas)(struct vfio_device *vdev, u32 *pt_id);
	void	(*detach_ioas)(struct vfio_device *vdev);
	int	(*open_device)(struct vfio_device *vdev);
	void	(*close_device)(struct vfio_device *vdev);
	ssize_t	(*read)(struct vfio_device *vdev, char __user *buf,
			 size_t count, loff_t *ppos);
	ssize_t	(*write)(struct vfio_device *vdev, const char __user *buf,
			 size_t count, loff_t *size);
	long	(*ioctl)(struct vfio_device *vdev, unsigned int cmd,
				 unsigned long arg);
	int	(*mmap)(struct vfio_device *vdev, struct vm_area_struct *vma);
	void	(*request)(struct vfio_device *vdev, unsigned int count);
	int	(*match)(struct vfio_device *vdev, char *buf);
	void	(*dma_unmap)(struct vfio_device *vdev, u64 iova, u64 length);
	int	(*device_feature)(struct vfio_device *device, u32 flags,
					  void __user *arg, size_t argsz);
};
```

每个函数都会传递最初在 `vfio_register_group_dev()` 或 `vfio_register_emulated_iommu_dev()` 调用中注册的 vdev。这允许总线驱动程序使用 container_of() 获取其私有数据。

- 初始化/释放回调在 vfio_device 初始化和释放时发出。
- 打开/关闭设备回调在为用户会话创建设备的第一个文件描述符实例（例如通过 VFIO_GROUP_GET_DEVICE_FD）时发出。
- ioctl 回调为某些 VFIO_DEVICE_* ioctl 提供直接传递。
- [un]bind_iommufd 回调在设备绑定到和解绑自 iommufd 时发出。
- [de]attach_ioas 回调在设备附加到和从由绑定的 iommufd 管理的 IOAS 解除时发出。但是，附加的 IOAS 也可以在设备从 iommufd 解绑时自动解除。
- 读取/写入/mmap 回调实现了由设备自身的 VFIO_DEVICE_GET_REGION_INFO ioctl 定义的设备区域访问。
请求回调在设备即将被注销时发出，例如当尝试从vfio总线驱动程序解绑设备时。

DMA取消映射（dma_unmap）回调在容器或由设备附加的IOAS中的一段iov地址空间被取消映射时发出。使用vfio页面固定接口的驱动程序必须实现此回调以解除固定dma_unmap范围内的页面。即使在调用open_device()之前，驱动程序也必须能够容忍此回调。

PPC64 sPAPR 实现说明
-----------------------

此实现具有一些特定之处：

1) 在较旧的系统上（如采用P5IOC2/IODA1的POWER7），每个容器仅支持一个IOMMU组，因为启动时会为每个IOMMU组（即可分区端点（PE）分配一个IOMMU表）分配一个表（PE通常是一个PCI域，但并非总是如此）。
新系统（如采用IODA2的POWER8）改进了硬件设计，可以去除这一限制，并允许在一个VFIO容器中有多个IOMMU组。

2) 硬件支持所谓的DMA窗口——允许进行DMA传输的PCI地址范围。任何试图访问窗口外地址空间的行为将导致整个PE隔离。

3) PPC64虚拟机是半虚拟化的，而非完全模拟。存在用于DMA的页面映射和取消映射的API，通常每次调用映射1至32页，并且目前没有减少调用次数的方法。为了提高速度，在实模式下实现了映射/取消映射处理，提供了出色的性能，但也有一些局限性，例如无法实时进行锁定页面的计数。

4) 根据sPAPR规范，可分区端点（PE）是指可以作为分区和错误恢复目的单元的I/O子树。PE可以是单功能或多功能IOA（I/O适配器）、多功能IOA的功能，或者多个IOA（可能包括位于多个IOA之上的交换和桥接结构）。PPC64虚拟机通过EEH RTAS服务检测并从PCI错误中恢复，这基于额外的ioctl命令实现。
因此，添加了4个额外的ioctl命令：

    VFIO_IOMMU_SPAPR_TCE_GET_INFO
        返回PCI总线上DMA窗口的大小和起始位置
    VFIO_IOMMU_ENABLE
        启用容器。锁定页面的计数在此时完成。这可以让用户首先了解DMA窗口的情况，并在执行实际任务前调整rlimit。
    VFIO_IOMMU_DISABLE
        禁用容器
这段代码描述了如何使用VFIO_EEH_PE_OP接口来设置、检测和恢复错误增强功能（EEH）。以下是翻译成中文的版本：

```plaintext
VFIO_EEH_PE_OP 提供了一个API，用于设置EEH、检测错误及恢复。

上面示例中的代码流程应稍作修改如下：

struct vfio_eeh_pe_op pe_op = { .argsz = sizeof(pe_op), .flags = 0 };

...

/* 将设备组添加到容器中 */
ioctl(group, VFIO_GROUP_SET_CONTAINER, &container);

/* 启用所需的IOMMU模型 */
ioctl(container, VFIO_SET_IOMMU, VFIO_SPAPR_TCE_IOMMU);

/* 获取附加的sPAPR IOMMU信息 */
vfio_iommu_spapr_tce_info spapr_iommu_info;
ioctl(container, VFIO_IOMMU_SPAPR_TCE_GET_INFO, &spapr_iommu_info);

if (ioctl(container, VFIO_IOMMU_ENABLE))
    /* 无法启用容器，可能是rlimit较低 */

/* 分配一些空间并设置DMA映射 */
dma_map.vaddr = mmap(0, 1024 * 1024, PROT_READ | PROT_WRITE,
                     MAP_PRIVATE | MAP_ANONYMOUS, 0, 0);

dma_map.size = 1024 * 1024;
dma_map.iova = 0; /* 从设备视角看起始于0x0的1MB */
dma_map.flags = VFIO_DMA_MAP_FLAG_READ | VFIO_DMA_MAP_FLAG_WRITE;

/* 确认.iova/.size是否在spapr_iommu_info的DMA窗口内 */
ioctl(container, VFIO_IOMMU_MAP_DMA, &dma_map);

/* 获取设备的文件描述符 */
device = ioctl(group, VFIO_GROUP_GET_DEVICE_FD, "0000:06:0d.0");

...

/* 重置设备并开始操作 */
ioctl(device, VFIO_DEVICE_RESET);

/* 确保EEH被支持 */
ioctl(container, VFIO_CHECK_EXTENSION, VFIO_EEH);

/* 在设备上启用EEH功能 */
pe_op.op = VFIO_EEH_PE_ENABLE;
ioctl(container, VFIO_EEH_PE_OP, &pe_op);

/* 建议创建额外的数据结构以表示PE，并将属于同一IOMMU组的子设备放入PE实例以备后续参考 */

/* 检查PE的状态并确保其处于功能状态 */
pe_op.op = VFIO_EEH_PE_GET_STATE;
ioctl(container, VFIO_EEH_PE_OP, &pe_op);

/* 使用pci_save_state()保存设备状态
   应当在指定的设备上启用EEH */

...

/* 注入EEH错误，预期是由32位配置加载引起的 */
pe_op.op = VFIO_EEH_PE_INJECT_ERR;
pe_op.err.type = EEH_ERR_TYPE_32;
pe_op.err.func = EEH_ERR_FUNC_LD_CFG_ADDR;
pe_op.err.addr = 0ul;
pe_op.err.mask = 0ul;
ioctl(container, VFIO_EEH_PE_OP, &pe_op);

...

/* 当从读取PCI配置空间或PCI设备的IO BAR时返回0xFF。检查PE的状态以查看是否已被冻结 */
```

以上代码展示了如何通过VFIO_EEH_PE_OP来设置、检测和恢复错误增强功能的过程。
```c
/* 使用ioctl命令对container执行VFIO_EEH_PE_OP操作，并传递pe_op结构 */

/* 等待挂起的PCI事务完成，并且在恢复完成之前不要产生任何更多的PCI流量到受影响的PE */

/* 启用受影响PE的I/O并收集日志。通常，PCI配置空间的标准部分和AER寄存器会被转储为日志以供进一步分析 */
pe_op.op = VFIO_EEH_PE_UNFREEZE_IO;
ioctl(container, VFIO_EEH_PE_OP, &pe_op);

/*
 * 发出PE重置：热重置或根本重置。通常情况下，热重置就足够了。但是，某些PCI适配器的固件可能需要进行根本重置
*/
pe_op.op = VFIO_EEH_PE_RESET_HOT;
ioctl(container, VFIO_EEH_PE_OP, &pe_op);
pe_op.op = VFIO_EEH_PE_RESET_DEACTIVATE;
ioctl(container, VFIO_EEH_PE_OP, &pe_op);

/* 为受影响的PE配置PCI桥接器 */
pe_op.op = VFIO_EEH_PE_CONFIGURE;
ioctl(container, VFIO_EEH_PE_OP, &pe_op);

/* 恢复初始化时保存的状态。pci_restore_state()是一个不错的示例 */

/* 希望错误已成功恢复。现在，您可以继续开始向受影响的PE发送/接收PCI流量 */

...

5) SPAPR TCE IOMMU有v2版本。它废弃了VFIO_IOMMU_ENABLE/
   VFIO_IOMMU_DISABLE，并实现了2个新的ioctl命令：
   VFIO_IOMMU_SPAPR_REGISTER_MEMORY 和 VFIO_IOMMU_SPAPR_UNREGISTER_MEMORY
   （这些在v1 IOMMU中不受支持）
PPC64虚拟化客户机会产生大量的映射/取消映射请求，
   处理这些请求包括固定/解固定页面以及更新mm::locked_vm计数器以确保不超过rlimit
v2 IOMMU将计费和固定拆分为独立的操作：

   - VFIO_IOMMU_SPAPR_REGISTER_MEMORY/VFIO_IOMMU_SPAPR_UNREGISTER_MEMORY ioctl命令
     接收用户空间地址和要固定的内存块大小
不支持二分法，并且期望使用与注册内存块相同的地址和大小调用VFIO_IOMMU_UNREGISTER_MEMORY。
用户空间不经常调用这些函数
```
请注意，这段代码注释已经被翻译成了中文，并保持了原有的格式以便于理解。
范围存储在VFIO容器中的链表中。
- VFIO_IOMMU_MAP_DMA/VFIO_IOMMU_UNMAP_DMA ioctl仅更新实际的IOMMU表，而不执行固定；相反，这些ioctl检查用户空间地址是否来自预先注册的范围。
这种分离有助于优化来宾的DMA操作。
6) sPAPR规范允许来宾在PCI总线上具有一个或多个额外的DMA窗口，并且支持可变页面大小。为此添加了两个ioctl：VFIO_IOMMU_SPAPR_TCE_CREATE和VFIO_IOMMU_SPAPR_TCE_REMOVE。
平台必须支持该功能，否则会向用户空间返回错误。现有硬件最多支持2个DMA窗口，其中一个是2GB长，使用4KB页面，称为“默认32位窗口”；另一个窗口可以与整个RAM一样大，并使用不同的页面大小，它是可选的——如果来宾驱动程序支持64位DMA，则来宾可以在运行时创建这些窗口。
VFIO_IOMMU_SPAPR_TCE_CREATE接收页面移位、DMA窗口大小以及TCE表级别数（如果TCE表足够大以至于内核可能无法分配足够的物理连续内存）。它在可用槽位中创建一个新的窗口，并返回新窗口开始的总线地址。由于硬件限制，用户空间不能选择DMA窗口的位置。
VFIO_IOMMU_SPAPR_TCE_REMOVE接收窗口的总线起始地址并移除该窗口。

------------------------------------------------------------------------

.. [1] VFIO最初是Tom Lyon在Cisco工作期间为其实现时所使用的“Virtual Function I/O”的缩写。自从那时起，我们已经超越了这个缩写的含义，但它依然具有吸引力。
.. [2] “安全”也取决于设备是否“行为良好”。对于多功能设备可能存在后门连接不同功能，甚至对于单功能设备也可能通过MMIO寄存器以其他方式访问如PCI配置空间等。为了防止前者，我们可以在IOMMU驱动程序中增加额外的预防措施来将多功能PCI设备分组在一起（iommu=group_mf）。对于后者，虽然我们无法阻止这种情况发生，但IOMMU仍然应该提供隔离。对于PCI来说，SR-IOV虚拟功能是最能表明“行为良好”的指标，因为它们是为虚拟化使用模型设计的。
.. [3] 虚拟机设备分配始终存在权衡，这些权衡超出了VFIO的范围。预计未来的IOMMU技术将会减少部分，但也许不是全部这样的权衡。
... [4] 在这种情况下，设备位于 PCI 桥接器下方，因此设备的任一功能所产生的交易对 IOMMU 来说都是无法区分的：

	-[0000:00]-+-1e.0-[06]--+-0d.0
				\-0d.1

	00:1e.0 PCI 桥接器: Intel Corporation 82801 PCI 桥接器（修订版 90）

... [5] 嵌套转换是 IOMMU 的一项特性，支持两阶段地址转换。这提高了 IOMMU 虚拟化中的地址转换效率。
... [6] PASID 代表进程地址空间 ID，由 PCI Express 引入。它是共享虚拟寻址（Shared Virtual Addressing, SVA）和可扩展 I/O 虚拟化（Scalable IOV）的前提条件。
