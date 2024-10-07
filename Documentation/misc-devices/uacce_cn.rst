### SPDX 许可证标识符: GPL-2.0

#### Uacce 的介绍
---------------------

Uacce（统一/用户空间访问加速器框架）旨在提供加速器和进程之间的共享虚拟寻址（SVA）。因此，加速器可以访问主 CPU 的任何数据结构。这不同于 CPU 和 I/O 设备之间的数据共享，后者仅共享数据内容而不是地址。

由于统一的地址，硬件和进程的用户空间可以在通信中共享相同的虚拟地址。Uacce 将硬件加速器视为一个异构处理器，而 IOMMU 共享相同的 CPU 页表，从而实现相同的从虚拟地址到物理地址的转换。

```
         __________________________       __________________________
        |                          |     |                          |
        |  User application (CPU)  |     |   Hardware Accelerator   |
        |__________________________|     |__________________________|

                     |                                 |
                     | va                              | va
                     V                                 V
                 __________                        __________
                |          |                      |          |
                |   MMU    |                      |  IOMMU   |
                |__________|                      |__________|
                     |                                 |
                     |                                 |
                     V pa                              V pa
                 _______________________________________
                |                                       |
                |              Memory                   |
                |_______________________________________|
```

#### 架构
------------

Uacce 是内核模块，负责 IOMMU 和地址共享。用户驱动程序和库称为 WarpDrive。Uacce 设备基于 IOMMU SVA API 构建，可以访问多个地址空间，包括没有 PASID 的地址空间。为了通信，引入了一个虚拟概念——队列，它提供了一个类似于 FIFO 的接口，并在应用程序和所有相关硬件之间保持统一的地址空间。

```
                             ___________________                  ________________
                            |                   |   user API     |                |
                            | WarpDrive library | ------------>  |  user driver   |
                            |___________________|                |________________|
                                     |                                    |
                                     |                                    |
                                     | queue fd                           |
                                     |                                    |
                                     |                                    |
                                     v                                    |
     ___________________         _________                                |
    |                   |       |         |                               | mmap memory
    | Other framework   |       |  uacce  |                               | r/w interface
    | crypto/nic/others |       |_________|                               |
    |___________________|                                                 |
             |                       |                                    |
             | register              | register                           |
             |                       |                                    |
             |                       |                                    |
             |                _________________       __________          |
             |               |                 |     |          |         |
              -------------  |  Device Driver  |     |  IOMMU   |         |
                             |_________________|     |__________|         |
                                     |                                    |
                                     |                                    V
                                     |                            ___________________
                                     |                           |                   |
                                     --------------------------  |  Device(Hardware) |
                                                                 |___________________|
```

#### 工作原理
----------------

Uacce 使用 `mmap` 和 IOMMU 来实现这一功能。
Uacce 为每个注册的设备创建一个字符设备（chrdev）。当用户应用程序打开 chrdev 时，会创建一个新的队列。文件描述符用作队列的用户句柄。

加速器设备以 Uacce 对象的形式呈现，并向用户空间导出为一个字符设备。用户应用程序通过 ioctl（作为控制路径）或共享内存（作为数据路径）与硬件通信。

硬件的控制路径是通过文件操作实现的，而数据路径则是通过队列文件描述符的 mmap 空间实现的。

队列文件地址空间如下：

```c
/**
 * enum uacce_qfrt: 队列区域类型
 * @UACCE_QFRT_MMIO: 设备 MMIO 区域
 * @UACCE_QFRT_DUS: 设备用户共享区域
 */
enum uacce_qfrt {
        UACCE_QFRT_MMIO = 0,
        UACCE_QFRT_DUS = 1,
};
```

所有区域都是可选的，并且根据设备类型有所不同。
每个区域只能映射一次，否则返回 -EEXIST。
设备 MMIO 区域映射到硬件的 MMIO 空间。通常用于门铃或其他通知硬件的方式。它不够快，不能作为数据通道。
设备用户共享区域用于用户进程和设备之间的数据缓冲共享。

Uacce 注册 API
----------------------

注册 API 定义在 uacce.h 中：

```c
struct uacce_interface {
    char name[UACCE_MAX_NAME_SIZE];
    unsigned int flags;
    const struct uacce_ops *ops;
};
```

根据 IOMMU 能力，`uacce_interface` 的 `flags` 可以是：

```c
/**
 * UACCE 设备标志：
 * UACCE_DEV_SVA：共享虚拟地址
 *              支持 PASID
 *              支持设备页故障（PCI PRI 或 SMMU 停滞）
 */
#define UACCE_DEV_SVA               BIT(0)
```

相关函数定义如下：

```c
struct uacce_device *uacce_alloc(struct device *parent,
                                 struct uacce_interface *interface);
int uacce_register(struct uacce_device *uacce);
void uacce_remove(struct uacce_device *uacce);
```

`uacce_register` 的结果可以是：

a. 如果 Uacce 模块未编译，则返回 `ERR_PTR(-ENODEV)`。

b. 成功并带有期望的标志位。

c. 成功但带有协商后的标志位，例如：

  `uacce_interface.flags = UACCE_DEV_SVA` 但 `uacce->flags = ~UACCE_DEV_SVA`

  因此，用户驱动需要检查返回值以及协商后的 `uacce->flags`。

用户驱动
--------------

队列文件的 mmap 空间需要一个用户驱动来封装通信协议。Uacce 在 sysfs 中提供了一些属性供用户驱动匹配相应的加速器。
更多细节请参见文档/ABI/测试/sysfs-driver-uacce

（注意：这里的“文档/ABI/测试”是假设原文中的“Documentation/ABI/testing”是指某个目录路径，如果你需要更准确的翻译，请提供更多的上下文信息。）
