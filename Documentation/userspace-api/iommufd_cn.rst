SPDX 许可证标识符: GPL-2.0+

=======
IOMMUFD
=======

:作者: Jason Gunthorpe
:作者: Kevin Tian

概述
========

IOMMUFD 是用户 API，用于控制与从用户空间管理 I/O 页表相关的 IOMMU 子系统。其目的是通用的，并且任何希望向用户空间暴露 DMA 的驱动程序都可以使用它。这些驱动程序最终将废弃它们可能已经实现或历史上实现的任何内部 IOMMU 逻辑（例如 vfio_iommu_type1.c）。至少，iommufd 提供了对所有 IOMMU 的 I/O 地址空间和 I/O 页表管理的普遍支持，并且在设计中留有空间来添加针对特定硬件功能的非通用特性。在此上下文中，大写的 IOMMUFD 指的是子系统，而小写的 iommufd 则指的是通过 /dev/iommu 创建的文件描述符，供用户空间使用。

关键概念
============

用户可见对象
--------------------

以下 IOMMUFD 对象被暴露给用户空间：

- IOMMUFD_OBJ_IOAS，表示一个 I/O 地址空间（IOAS），允许将用户空间内存映射到 I/O 虚拟地址（IOVA）范围内
  IOAS 是 VFIO 容器的功能替代品，类似于 VFIO 容器，它将 IOVA 映射复制到其内部持有的 iommu_domain 列表中
- IOMMUFD_OBJ_DEVICE，表示一个由外部驱动程序绑定到 iommufd 的设备
- IOMMUFD_OBJ_HW_PAGETABLE，表示一个由 iommu 驱动程序管理的实际硬件 I/O 页表（即单个 struct iommu_domain）
  IOAS 包含共享相同 IOVA 映射的 HW_PAGETABLE 列表，并且会与其每个成员 HW_PAGETABLE 同步其映射
所有用户可见的对象都通过 IOMMU_DESTROY uAPI 销毁
下图展示了用户可见对象与内核数据结构（外部于 iommufd）之间的关系，数字表示创建对象及其链接的操作：

```
_________________________________________________________
|                          iommufd                       |
|       [1]                                              |
|  ______________________                                 |
| |                      |                                |
| |                      |                                |
| |                      |                                |
| |                      |                                |
| |                      |                                |
| |                      |                                |
| |                      |     [3]                [2]     |
| |                      |  _____________         ______ |
| |      IOAS           |<--|            |<------|       | |
| |                      |  |HW_PAGETABLE|       |DEVICE | |
| |                      |  |____________|       |_______| |
| |                      |        |                  |      |
| |                      |        |                  |      |
| |                      |        |                  |      |
| |                      |        |                  |      |
| |                      |        |                  |      |
| |______________________|        |                  |      |
|         |                  |                  |      |
|_________|__________________|__________________|______|
           |                  |                  |
           |              _____v______      _______v_____
           | PFN 存储 |            |    |             |
           |---------->|iommu_domain|    |struct device|
                             |____________|    |___________|
```

1. IOMMUFD_OBJ_IOAS 通过 IOMMU_IOAS_ALLOC uAPI 创建。一个 iommufd 可以持有多个 IOAS 对象。IOAS 是最通用的对象，不暴露特定于单一 IOMMU 驱动程序的接口。对 IOAS 的所有操作必须对其内部的每个 iommu_domain 平等处理。
2. 当外部驱动程序调用IOMMUFD内核API将设备绑定到iommufd时，会创建IOMMUFD_OBJ_DEVICE。驱动程序需要实现一组ioctl接口，以便用户空间能够发起绑定操作。此操作成功完成后，即可建立对设备所需的DMA所有权。驱动程序还必须设置driver_managed_dma标志，并且在该操作成功之前不得访问设备。

3. 当外部驱动程序调用IOMMUFD内核API将已绑定的设备附加到IOAS时，会创建IOMMUFD_OBJ_HW_PAGETABLE。同样地，外部驱动程序的用户空间API允许用户空间发起附加操作。如果存在兼容的页表，则会重用该页表进行附加。否则，将创建一个新的页表对象和iommu_domain。此操作成功完成后，会在IOAS、设备和iommu_domain之间建立连接。一旦完成，设备就可以执行DMA操作。
每个IOAS中的iommu_domain也会以HW_PAGETABLE对象的形式呈现给用户空间。

.. 注意::

      未来的IOMMUFD更新将提供直接创建和操作HW_PAGETABLE的API。
一个设备只能通过DMA所有权声明绑定到一个iommufd，并且最多只能附加到一个IOAS对象（目前不支持PASID）。

### 内核数据结构

用户可见的对象由以下数据结构支持：

- iommufd_ioas 对应于 IOMMUFD_OBJ_IOAS
- iommufd_device 对应于 IOMMUFD_OBJ_DEVICE
- iommufd_hw_pagetable 对应于 IOMMUFD_OBJ_HW_PAGETABLE

查看这些数据结构时的一些术语：

- 自动域：指在将设备附加到IOAS对象时自动创建的iommu域。这与VFIO Type 1的语义相兼容。
- 手动域：指由用户指定为设备附加目标页表的iommu域。尽管目前没有直接创建此类域的用户空间API，但数据结构和算法已经准备好处理这种用例。
内核用户 - 指的是像使用VFIO mdev这样利用IOMMUFD访问接口来访问IOAS的情况。这开始于创建一个与物理设备绑定域类似的iommufd_access对象。该访问对象允许将IOVA范围转换为struct page *列表，或者直接对IOVA进行读写。

iommufd_ioas作为元数据结构用于管理IOVA范围如何映射到内存页，它由以下部分组成：

- struct io_pagetable 持有IOVA映射
- struct iopt_area 表示已填充的IOVA部分
- struct iopt_pages 表示PFN存储
- struct iommu_domain 表示IOMMU中的IO页表
- struct iopt_pages_access 表示内核中使用PFN的用户
- struct xarray pinned_pfns 保存由内核用户固定的一系列页

每个iopt_pages代表一个逻辑线性数组的完整PFN。这些PFN最终通过mm_struct从用户空间的VA派生而来。一旦它们被固定，PFN就会存储在iommu_domain的IOPTE中或如果通过iommufd_access固定，则存储在pinned_pfns xarray中。

PFN需要在所有组合的存储位置之间复制，具体取决于存在哪些域以及存在何种类型的内核“软件访问”用户。该机制确保页面只被固定一次。

io_pagetable由指向iopt_pages的iopt_area和镜像IOVA到PFN映射的iommu_domains列表组成。

多个io_pagetable通过其iopt_area可以共享单个iopt_pages，从而避免了多固定和重复计算页面消耗。

iommufd_ioas可以在子系统之间共享，例如VFIO和VDPA，前提是不同子系统管理的设备绑定到同一个iommufd。

IOMMUFD用户API
===============

.. kernel-doc:: include/uapi/linux/iommufd.h

IOMMUFD内核API
===============

IOMMUFD内核API是以设备为中心的，并在后台管理与组相关的技巧。这使得外部驱动程序调用此类kAPI时可以实现一个简单的以设备为中心的uAPI，用于将其设备连接到iommufd，而不是像VFIO那样在其uAPI中显式地强加组语义。
.. kernel-doc:: drivers/iommu/iommufd/device.c
   :export:

.. kernel-doc:: drivers/iommu/iommufd/main.c
   :export:

VFIO与IOMMUFD
---------------

将VFIO设备连接到iommufd可以通过两种方式实现：
第一种是通过直接实现/dev/vfio/vfio容器的IOCTLs，将其映射到io_pagetable操作，使其与VFIO兼容。这样做可以通过将/dev/vfio/vfio符号链接到/dev/iommufd或将VFIO扩展到使用iommufd而非容器fd来设置容器，从而使iommufd在传统的VFIO应用程序中使用。
第二种方法是直接扩展VFIO以支持基于上述IOMMUFD内核API的新的一套以设备为中心的用户API。尽管需要用户空间的变化，但这种方法更符合IOMMUFD API语义，并且相较于第一种方法更容易支持新的iommufd特性。
目前这两种方法仍在开发中。仍有一些问题需要解决，以便赶上VFIO Type 1，具体问题记录在iommufd_vfio_check_extension()函数中。
未来的待办事项
===============

目前IOMMUFD仅支持内核管理的I/O页表，类似于VFIO Type 1。正在关注的新功能包括：

- 将iommu_domain绑定到PASID/SSID
- 为ARM、x86和S390提供用户空间页表
- 内核绕过用户页表的无效化
- 在IOMMU中重用KVM页表
- 在IOMMU中进行脏页跟踪
- 运行时增加或减少IOPTE大小
- 支持PRI，并在用户空间中处理错误
