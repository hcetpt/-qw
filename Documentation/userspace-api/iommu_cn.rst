SPDX 许可证标识符: GPL-2.0
iommu:

=====================================
IOMMU 用户空间 API
=====================================

IOMMU 用户空间 API（UAPI）用于虚拟化场景中，需要在物理 IOMMU 驱动程序和虚拟 IOMMU 驱动程序之间进行通信。对于裸机使用，IOMMU 是一个系统设备，不需要直接与用户空间通信。主要用例包括客户机共享虚拟地址（SVA）和客户机 I/O 虚拟地址（IOVA），其中 vIOMMU 实现依赖于物理 IOMMU，因此需要与主机驱动程序交互。

.. contents:: :local:

功能
===============
用户和内核之间的通信涉及两个方向。支持的用户-内核 API 包括：

1. 绑定/解绑客户机 PASID（例如：Intel VT-d）
2. 绑定/解绑客户机 PASID 表（例如：ARM SMMU）
3. 根据客户机请求无效 IOMMU 缓存
4. 向客户机报告错误并处理页面请求

要求
============
IOMMU UAPI 通用且可扩展以满足以下要求：

1. 模拟和准虚拟化的 vIOMMU
2. 多个供应商（Intel VT-d、ARM SMMU 等）
3. 对 UAPI 的扩展不应破坏现有的用户空间

接口
==========
尽管 IOMMU UAPI 中定义的数据结构是自包含的，但没有引入用户 API 函数。相反，IOMMU UAPI 设计为与现有用户驱动框架（如 VFIO 扩展规则和注意事项）协同工作。

当 IOMMU UAPI 进行扩展时，数据结构只能以两种方式修改：

1. 通过重新利用 padding[] 字段添加新字段。不改变大小
2. 在末尾添加新的联合成员。可能会增加结构大小

在可变大小联合之后不能添加任何新字段，因为这会破坏向后兼容性。每当使用任一方法进行更改时，必须引入一个新的标志。IOMMU 驱动程序根据标志处理数据，确保向后兼容性。

版本字段仅在 UAPI 全面升级的不太可能情况下保留。
调用者始终负责通过适当设置 argsz 来指示传递的结构大小。
虽然同时，argsz 是用户提供的数据，不可信。argsz 字段允许用户应用程序指示其提供的数据量；仍然由内核验证它是否正确且足以完成请求的操作。

兼容性检查
----------------------
当 IOMMU UAPI 扩展导致某些结构大小增加时，IOMMU UAPI 代码应处理以下情况：

1. 用户和内核大小完全匹配
2. 使用旧内核头文件（较小的 UAPI 大小）的旧用户在新内核（较大的 UAPI 大小）上运行
3. 使用新内核头文件（较大的 UAPI 大小）的新用户在旧内核上运行
4. 恶意用户传递非法/无效的大小，但仍在范围内。数据可能包含垃圾信息。

特性检查
---------
在使用 vIOMMU 启动客户机时，强烈建议预先检查兼容性，因为在 vIOMMU 运行过程中发生的一些后续错误（如缓存失效失败）无法根据 IOMMU 规范优雅地传递给客户机。这可能会导致用户端出现灾难性的故障。

用户应用程序（如 QEMU）应导入内核 UAPI 头文件。每个特性的向后兼容性由特征标志支持。
例如，较旧版本的 QEMU（带有较旧的内核头文件）可以在较新版本的内核上运行。如果较新版本的 QEMU（带有新的内核头文件）不支持旧内核中的新特征标志，则可能拒绝在较旧内核上初始化。简单地使用新的内核头文件重新编译现有代码通常不会有问题，因为仅使用现有的标志。

IOMMU 供应商驱动程序应向 IOMMU UAPI 消费者（例如通过 VFIO）报告以下特性：
1. IOMMU_NESTING_FEAT_SYSWIDE_PASID
2. IOMMU_NESTING_FEAT_BIND_PGTBL
3. IOMMU_NESTING_FEAT_BIND_PASID_TABLE
4. IOMMU_NESTING_FEAT_CACHE_INVLD
5. IOMMU_NESTING_FEAT_PAGE_REQUEST

以 VFIO 为例，在收到 VFIO 用户空间（如 QEMU）的请求时，VFIO 内核代码应查询 IOMMU 供应商驱动程序以获取上述特性的支持情况，并将查询结果返回给用户空间调用者。详细信息可以在 `Documentation/driver-api/vfio.rst` 中找到。

VFIO 数据传递示例
------------------
作为广泛使用的用户空间驱动框架，VFIO 已经具备了 IOMMU 意识，并共享了许多关键概念，如设备模型、组和保护域。其他用户驱动框架也可以扩展以支持 IOMMU UAPI，但这超出了本文档的范围。

在这个紧密集成的 VFIO-IOMMU 接口中，IOMMU UAPI 数据的最终消费者是主机 IOMMU 驱动程序。VFIO 促进了用户-内核传输、能力检查、安全性和进程地址空间 ID（PASID）的生命周期管理。

VFIO 层将数据结构传递到 IOMMU 驱动程序。其模式如下：

```c
struct {
    __u32 argsz;
    __u32 flags;
    __u8 data[];
};
```

这里 `data[]` 包含 IOMMU UAPI 数据结构。VFIO 可以根据自己的标志自由打包和解析数据大小。

为了确定用户数据的大小和特性集，`argsz` 和 `flags`（或等效项）也嵌入到 IOMMU UAPI 数据结构中。
一个名为"`__u32 argsz`"的字段*总是*出现在每个结构体的开头。例如：
::

   struct iommu_cache_invalidate_info {
	__u32 argsz;
	#define IOMMU_CACHE_INVALIDATE_INFO_VERSION_1 1
	__u32 version;
	/* IOMMU 分页结构缓存 */
	#define IOMMU_CACHE_INV_TYPE_IOTLB (1 << 0) /* IOMMU IOTLB */
	#define IOMMU_CACHE_INV_TYPE_DEV_IOTLB (1 << 1) /* 设备 IOTLB */
	#define IOMMU_CACHE_INV_TYPE_PASID (1 << 2) /* PASID 缓存 */
	#define IOMMU_CACHE_INV_TYPE_NR (3)
	__u8 cache;
	__u8 granularity;
	__u8 padding[6];
	union {
		struct iommu_inv_pasid_info pasid_info;
		struct iommu_inv_addr_info addr_info;
	} granu;
   };

VFIO 负责检查自己的 `argsz` 和标志位，并调用适当的 IOMMU 用户空间 API 函数。用户指针被传递给 IOMMU 层进行进一步处理。职责划分如下：

- 通用 IOMMU 层基于当前内核版本中的用户空间 API 数据检查 `argsz` 范围。
- 通用 IOMMU 层检查用户空间 API 数据中的保留位是否为零、标志位中的非零保留位、填充字段和不受支持的版本。这是为了确保将来使用这些字段或标志位时不会破坏用户空间程序。
- 厂商 IOMMU 驱动根据厂商标志检查 `argsz`。根据标志位消费用户空间 API 数据。对于特定于厂商的未来扩展，厂商驱动可以访问未修改的 `argsz` 值。目前，它不执行 `copy_from_user()` 操作。在某些未来场景中，可以在结构定义之外提供厂商数据时提供一个 `__user` 指针。

IOMMU 代码将用户空间 API 数据分为两类：

- 结构体包含厂商数据（示例：iommu_uapi_cache_invalidate()）
- 结构体仅包含通用数据（示例：iommu_uapi_sva_bind_gpasid()）

与内核用户共享用户空间 API
------------------------------
对于与内核用户共享的用户空间 API，提供了一个包装函数来区分调用者。例如，

用户空间调用者 ::

  int iommu_uapi_sva_unbind_gpasid(struct iommu_domain *domain,
                                   struct device *dev,
                                   void __user *udata)

内核调用者 ::

  int iommu_sva_unbind_gpasid(struct iommu_domain *domain,
                              struct device *dev, ioasid_t ioasid);
