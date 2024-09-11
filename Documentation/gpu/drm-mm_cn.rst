### DRM 内存管理

现代 Linux 系统需要大量的图形内存来存储帧缓冲区、纹理、顶点和其他与图形相关的数据。鉴于这些数据的动态特性，高效地管理图形内存对于图形堆栈至关重要，并且在 DRM（直接渲染管理器）基础设施中扮演着核心角色。

DRM 核心包括两个内存管理器：Translation Table Manager (TTM) 和 Graphics Execution Manager (GEM)。TTM 是第一个开发的 DRM 内存管理器，试图提供一个通用解决方案。它提供了一个用户空间 API 来满足所有硬件的需求，支持统一内存架构 (UMA) 设备和具有专用视频 RAM 的设备（即大多数独立显卡）。这导致了一个庞大而复杂的代码库，在驱动程序开发中难以使用。

GEM 是英特尔赞助的一个项目，作为对 TTM 复杂性的回应。它的设计理念完全不同：GEM 不是为了解决所有与图形内存相关的问题，而是识别了驱动程序之间的共同代码并创建了一个支持库来共享这些代码。GEM 比 TTM 具有更简单的初始化和执行要求，但没有视频 RAM 管理能力，因此仅限于 UMA 设备。

### Translation Table Manager (TTM)

#### .. kernel-doc:: drivers/gpu/drm/ttm/ttm_module.c
   :doc: TTM

#### .. kernel-doc:: include/drm/ttm/ttm_caching.h
   :internal:

##### TTM 设备对象引用

###### .. kernel-doc:: include/drm/ttm/ttm_device.h
       :internal:

###### .. kernel-doc:: drivers/gpu/drm/ttm/ttm_device.c
       :export:

##### TTM 资源放置引用

###### .. kernel-doc:: include/drm/ttm/ttm_placement.h
       :internal:

##### TTM 资源对象引用

###### .. kernel-doc:: include/drm/ttm/ttm_resource.h
       :internal:

###### .. kernel-doc:: drivers/gpu/drm/ttm/ttm_resource.c
       :export:

##### TTM TT 对象引用

###### .. kernel-doc:: include/drm/ttm/ttm_tt.h
       :internal:

###### .. kernel-doc:: drivers/gpu/drm/ttm/ttm_tt.c
       :export:

##### TTM 页面池引用

###### .. kernel-doc:: include/drm/ttm/ttm_pool.h
       :internal:

###### .. kernel-doc:: drivers/gpu/drm/ttm/ttm_pool.c
       :export:

### Graphics Execution Manager (GEM)

GEM 的设计方法导致了一个内存管理器，其用户空间或内核 API 并未完全覆盖所有（甚至所有常见）用例。GEM 向用户空间暴露了一组标准的内存相关操作，并向驱动程序提供了一组辅助函数，允许驱动程序通过自己的私有 API 实现硬件特定的操作。

GEM 用户空间 API 在 LWN 的《GEM - 图形执行管理器》文章中有描述。尽管稍显过时，该文档提供了 GEM API 原则的良好概述。缓冲区分配和读写操作，作为 GEM 公共 API 的一部分，目前是通过驱动程序特定的 ioctl 实现的。

GEM 是数据无关的。它管理抽象的缓冲区对象，而不关心各个缓冲区的内容。需要知道缓冲区内容或用途的 API，例如缓冲区分配或同步原语，超出了 GEM 的范围，必须通过驱动程序特定的 ioctl 实现。

从基本层面来看，GEM 涉及以下几个操作：

- 内存分配和释放
- 命令执行
- 命令执行时的孔径管理

缓冲区对象分配相对简单，主要由 Linux 的 shmem 层提供，用于支持每个对象的内存。

特定设备的操作，如命令执行、固定、缓冲区读写、映射和域所有权转移等，留给了驱动程序特定的 ioctl。

#### GEM 初始化

使用 GEM 的驱动程序必须在结构体 :c:type:`struct drm_driver <drm_driver>` 的 driver_features 字段中设置 DRIVER_GEM 位。DRM 核心将在调用加载操作之前自动初始化 GEM 核心。实际上，这将创建一个 DRM 内存管理器对象，为对象分配提供地址空间池。
在KMS配置中，如果硬件需要，驱动程序需要在核心GEM初始化之后分配并初始化命令环形缓冲区。UMA设备通常有一个所谓的“被盗”内存区域，该区域为初始帧缓冲区和设备所需的大型连续内存区域提供空间。这部分空间通常不由GEM管理，必须单独初始化为自己的DRM MM对象。

GEM对象创建
------------

GEM将GEM对象的创建与支持这些对象的内存分配分为两个独立的操作。GEM对象由 `struct drm_gem_object` 类型的一个实例表示。驱动程序通常需要扩展GEM对象以包含私有信息，因此会创建一个嵌入了 `struct drm_gem_object` 实例的特定于驱动程序的GEM对象结构类型。

为了创建一个GEM对象，驱动程序需要为其特定的GEM对象类型分配内存，并通过调用 `drm_gem_object_init()` 函数来初始化嵌入的 `struct drm_gem_object`。此函数接受指向DRM设备、GEM对象以及缓冲对象大小（以字节为单位）的指针。

GEM使用共享内存（shmem）来分配匿名分页内存。`drm_gem_object_init()` 将创建一个指定大小的shmfs文件，并将其存储到 `struct drm_gem_object` 的 `filp` 字段中。该内存用于作为对象的主要存储空间（当图形硬件直接使用系统内存时），或者在其他情况下作为后端存储。

驱动程序负责实际物理页面的分配，通过为每一页调用 `shmem_read_mapping_page_gfp()` 来实现。
需要注意的是，它们可以选择在初始化GEM对象时分配页面，或延迟分配直到内存被需要时（例如，由于用户空间内存访问导致的缺页异常，或驱动程序需要开始涉及内存的DMA传输）。

匿名分页内存分配并不总是必需的，特别是在硬件要求物理连续系统内存的情况下（这在嵌入式设备中很常见）。驱动程序可以通过调用 `drm_gem_private_object_init()` 而不是 `drm_gem_object_init()` 来初始化没有shmfs支持的GEM对象（称为私有GEM对象）。私有GEM对象的存储必须由驱动程序管理。

GEM对象生命周期
-------------------

所有GEM对象都由GEM核心进行引用计数。可以通过调用 `drm_gem_object_get()` 和 `drm_gem_object_put()` 分别获取和释放引用。
当对一个GEM对象的最后一个引用被释放时，GEM核心会调用`:c:type:'struct drm_gem_object_funcs <gem_object_funcs>'`中的`free`操作。这个操作对于启用GEM的驱动程序是强制性的，并且必须释放GEM对象及其所有相关资源。

```c
void (*free)(struct drm_gem_object *obj);
```

驱动程序负责释放所有GEM对象资源。这包括由GEM核心创建的资源，这些资源需要通过`drm_gem_object_release()`来释放。

### GEM对象命名

用户空间和内核之间的通信使用本地句柄、全局名称或最近使用的文件描述符来引用GEM对象。所有这些都是32位整数值；对于文件描述符，通常的Linux内核限制适用。

GEM句柄是针对特定DRM文件的。应用程序通过特定于驱动程序的ioctl获得一个GEM对象的句柄，并可以使用该句柄在其他标准或特定于驱动程序的ioctl中引用GEM对象。关闭一个DRM文件句柄会释放其所有的GEM句柄并取消引用相关的GEM对象。

为了为一个GEM对象创建句柄，驱动程序调用`drm_gem_handle_create()`。该函数接受指向DRM文件和GEM对象的指针，并返回一个本地唯一的句柄。当不再需要句柄时，驱动程序通过调用`drm_gem_handle_delete()`删除它。最后，可以通过调用`drm_gem_object_lookup()`来获取与句柄关联的GEM对象。

句柄不拥有GEM对象，它们只是引用了对象，在句柄被销毁时这个引用会被取消。为了避免GEM对象泄露，驱动程序必须确保适当地放弃它们拥有的引用（例如，在对象创建时获取的初始引用），而不需要特别考虑句柄。例如，在实现dumb_create操作时，如果GEM对象和句柄是在同一操作中创建的，驱动程序必须在返回句柄之前放弃对GEM对象的初始引用。

GEM名称的目的类似于句柄，但它们不是针对DRM文件的。它们可以在进程间传递以全局引用GEM对象。名称不能直接用于在DRM API中引用对象，应用程序必须使用DRM_IOCTL_GEM_FLINK和DRM_IOCTL_GEM_OPEN ioctl将句柄转换为名称或将名称转换为句柄。这个转换由DRM核心处理，无需任何特定于驱动程序的支持。

GEM还支持通过PRIME和dma-buf文件描述符进行缓冲区共享。基于GEM的驱动程序必须使用提供的辅助函数正确实现导出和导入。详情见？。由于共享文件描述符比容易猜测且全局可见的GEM名称更安全，因此它是首选的缓冲区共享机制。仅支持通过GEM名称共享缓冲区用于遗留用户空间。

此外，PRIME还允许跨设备缓冲区共享，因为它基于dma-buf。
GEM 对象映射
--------------

由于映射操作较为耗时，GEM 优先使用通过驱动程序特定的 ioctl 实现的读/写访问缓冲区的方式，而不是将缓冲区映射到用户空间。然而，在需要随机访问缓冲区（例如执行软件渲染）的情况下，直接访问对象可能更高效。`mmap` 系统调用不能直接用于映射 GEM 对象，因为它们没有自己的文件句柄。目前存在两种方法来将 GEM 对象映射到用户空间。第一种方法使用驱动程序特定的 ioctl 来执行映射操作，并在内部调用 `do_mmap()`。这种方法通常被认为是不可靠的，并且对于新的启用 GEM 的驱动程序来说似乎是不推荐的，因此这里不作描述。

第二种方法使用 DRM 文件句柄上的 `mmap` 系统调用：

```c
void *mmap(void *addr, size_t length, int prot, int flags, int fd, off_t offset);
```

DRM 通过传递给 `mmap` 偏移参数的一个假偏移量来识别要映射的 GEM 对象。在映射之前，必须将一个假偏移量与 GEM 对象关联起来。为此，驱动程序必须在该对象上调用 `drm_gem_create_mmap_offset()`。

一旦分配了假偏移量值，必须以驱动程序特定的方式将其传递给应用程序，并可以作为 `mmap` 偏移参数使用。

GEM 核心提供了一个辅助方法 `drm_gem_mmap()` 来处理对象映射。该方法可以直接设置为 `mmap` 文件操作处理器。它会根据偏移量查找 GEM 对象，并将 VMA 操作设置为 `struct drm_driver` 中的 `gem_vm_ops` 字段。请注意，`drm_gem_mmap()` 不会将内存映射到用户空间，而是依赖于由驱动程序提供的故障处理程序来单独映射页面。

为了使用 `drm_gem_mmap()`，驱动程序必须填充 `struct drm_driver` 中的 `gem_vm_ops` 字段，使其包含指向 VM 操作的指针。

VM 操作是一个 `struct vm_operations_struct`，其中包含多个字段，比较重要的有：

```c
struct vm_operations_struct {
    void (*open)(struct vm_area_struct *area);
    void (*close)(struct vm_area_struct *area);
    vm_fault_t (*fault)(struct vm_fault *vmf);
};
```

`open` 和 `close` 操作必须更新 GEM 对象的引用计数。驱动程序可以使用 `drm_gem_vm_open()` 和 `drm_gem_vm_close()` 辅助函数作为 `open` 和 `close` 处理器。

`fault` 操作处理器负责在发生页错误时将单个页面映射到用户空间。根据内存分配方案，驱动程序可以在发生页错误时分配页面，也可以决定在创建 GEM 对象时为其分配内存。

希望提前映射 GEM 对象而不是处理页错误的驱动程序可以实现自己的 `mmap` 文件操作处理器。

对于没有 MMU 的平台，GEM 核心提供了一个辅助方法 `drm_gem_dma_get_unmapped_area()`。`mmap` 例程会调用此方法以获取建议的映射地址。
为了使用 `drm_gem_dma_get_unmapped_area()`，驱动程序必须在 `struct file_operations` 的 `get_unmapped_area` 字段中填充一个指向 `drm_gem_dma_get_unmapped_area()` 的指针。关于 `get_unmapped_area` 的更详细信息可以在 `Documentation/admin-guide/mm/nommu-mmap.rst` 中找到。

内存一致性
-----------

当对象映射到设备或在命令缓冲区中使用时，其支持页面会被刷新到内存，并标记为写合并（write-combined），以便与 GPU 保持一致。同样地，如果 CPU 在 GPU 完成渲染后访问某个对象，则该对象必须与 CPU 对内存的视图保持一致，通常涉及各种类型的 GPU 缓存刷新。这种核心的 CPU<->GPU 一致性管理由一个设备特定的 ioctl 提供，它评估对象的当前域，并执行任何必要的刷新或同步操作，以将对象置于所需的域（注意，对象可能处于忙碌状态，即活动渲染目标；在这种情况下，设置域会阻止客户端并等待渲染完成后再执行任何必要的刷新操作）。

命令执行
---------

对于 GPU 设备而言，最重要的 GEM 功能之一是向客户端提供命令执行接口。客户端程序构建包含先前分配的内存对象引用的命令缓冲区，然后将其提交给 GEM。此时，GEM 负责将所有对象绑定到 GTT，执行缓冲区，并为访问同一缓冲区的客户端提供必要的同步。这通常涉及从 GTT 中驱逐一些对象并重新绑定其他对象（这是一个相当昂贵的操作），并提供重定位支持，隐藏固定 GTT 偏移量。客户端必须注意不要提交引用的对象数量超过 GTT 容量的命令缓冲区；否则，GEM 将拒绝它们且不会发生渲染。类似地，如果缓冲区中的多个对象需要分配围栏寄存器以正确渲染（例如，在 965 之前的芯片上的 2D 转换），则必须注意不要要求比客户端可用的更多围栏寄存器。这种资源管理应在 libdrm 中抽象化。

GEM 函数参考
------------

.. kernel-doc:: include/drm/drm_gem.h
   :internal:

.. kernel-doc:: drivers/gpu/drm/drm_gem.c
   :export:

GEM DMA 辅助函数参考
--------------------

.. kernel-doc:: drivers/gpu/drm/drm_gem_dma_helper.c
   :doc: dma helpers

.. kernel-doc:: include/drm/drm_gem_dma_helper.h
   :internal:

.. kernel-doc:: drivers/gpu/drm/drm_gem_dma_helper.c
   :export:

GEM SHMEM 辅助函数参考
----------------------

.. kernel-doc:: drivers/gpu/drm/drm_gem_shmem_helper.c
   :doc: overview

.. kernel-doc:: include/drm/drm_gem_shmem_helper.h
   :internal:

.. kernel-doc:: drivers/gpu/drm/drm_gem_shmem_helper.c
   :export:

GEM VRAM 辅助函数参考
--------------------

.. kernel-doc:: drivers/gpu/drm/drm_gem_vram_helper.c
   :doc: overview

.. kernel-doc:: include/drm/drm_gem_vram_helper.h
   :internal:

.. kernel-doc:: drivers/gpu/drm/drm_gem_vram_helper.c
   :export:

GEM TTM 辅助函数参考
--------------------

.. kernel-doc:: drivers/gpu/drm/drm_gem_ttm_helper.c
   :doc: overview

.. kernel-doc:: drivers/gpu/drm/drm_gem_ttm_helper.c
   :export:

VMA 偏移管理器
==============

.. kernel-doc:: drivers/gpu/drm/drm_vma_manager.c
   :doc: vma offset manager

.. kernel-doc:: include/drm/drm_vma_manager.h
   :internal:

.. kernel-doc:: drivers/gpu/drm/drm_vma_manager.c
   :export:

.. _prime_buffer_sharing:

PRIME 缓冲共享
==============

PRIME 是 drm 中的跨设备缓冲共享框架，最初是为了 OPTIMUS 系列多 GPU 平台创建的。对用户空间而言，PRIME 缓冲区是基于 dma-buf 的文件描述符。
概述和生命周期规则
--------------------

.. kernel-doc:: drivers/gpu/drm/drm_prime.c
   :doc: overview and lifetime rules

PRIME 辅助函数
--------------

.. kernel-doc:: drivers/gpu/drm/drm_prime.c
   :doc: PRIME Helpers

PRIME 函数参考
--------------

.. kernel-doc:: include/drm/drm_prime.h
   :internal:

.. kernel-doc:: drivers/gpu/drm/drm_prime.c
   :export:

DRM MM 范围分配器
=================

概述
----

.. kernel-doc:: drivers/gpu/drm/drm_mm.c
   :doc: Overview

LRU 扫描/驱逐支持
-----------------

.. kernel-doc:: drivers/gpu/drm/drm_mm.c
   :doc: lru scan roster

DRM MM 范围分配器函数参考
--------------------------

.. kernel-doc:: include/drm/drm_mm.h
   :internal:

.. kernel-doc:: drivers/gpu/drm/drm_mm.c
   :export:

.. _drm_gpuvm:

DRM GPUVM
=========

概述
----

.. kernel-doc:: drivers/gpu/drm/drm_gpuvm.c
   :doc: Overview

拆分与合并
----------

.. kernel-doc:: drivers/gpu/drm/drm_gpuvm.c
   :doc: Split and Merge

.. _drm_gpuvm_locking:

锁定
----

.. kernel-doc:: drivers/gpu/drm/drm_gpuvm.c
   :doc: Locking

示例
----

.. kernel-doc:: drivers/gpu/drm/drm_gpuvm.c
   :doc: Examples

DRM GPUVM 函数参考
------------------

.. kernel-doc:: include/drm/drm_gpuvm.h
   :internal:

.. kernel-doc:: drivers/gpu/drm/drm_gpuvm.c
   :export:

DRM Buddy 分配器
================

DRM Buddy 函数参考
------------------

.. kernel-doc:: drivers/gpu/drm/drm_buddy.c
   :export:

DRM 缓存处理和快速 WC memcpy()
===============================

.. kernel-doc:: drivers/gpu/drm/drm_cache.c
   :export:

.. _drm_sync_objects:

DRM 同步对象
============

.. kernel-doc:: drivers/gpu/drm/drm_syncobj.c
   :doc: Overview

.. kernel-doc:: include/drm/drm_syncobj.h
   :internal:

.. kernel-doc:: drivers/gpu/drm/drm_syncobj.c
   :export:

DRM 执行上下文
==============

.. kernel-doc:: drivers/gpu/drm/drm_exec.c
   :doc: Overview

.. kernel-doc:: include/drm/drm_exec.h
   :internal:

.. kernel-doc:: drivers/gpu/drm/drm_exec.c
   :export:

GPU 调度器
==========

概述
----

.. kernel-doc:: drivers/gpu/drm/scheduler/sched_main.c
   :doc: Overview

流控制
-------

.. kernel-doc:: drivers/gpu/drm/scheduler/sched_main.c
   :doc: Flow Control

调度器函数参考
---------------

.. kernel-doc:: include/drm/gpu_scheduler.h
   :internal:

.. kernel-doc:: drivers/gpu/drm/scheduler/sched_main.c
   :export:

.. kernel-doc:: drivers/gpu/drm/scheduler/sched_entity.c
   :export:
