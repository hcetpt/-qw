DRM 内部结构
=============

本章记录了与驱动程序作者和开发人员相关的内容，他们致力于为现有驱动程序添加对最新特性的支持。首先，我们介绍一些典型的驱动初始化需求，例如设置命令缓冲区、创建初始输出配置以及初始化核心服务。后续部分将更详细地介绍核心内部结构，并提供实现说明和示例。

DRM 层为图形驱动程序提供了多种服务，其中许多服务是通过 libdrm 库提供的应用程序接口来驱动的，libdrm 包装了大多数 DRM ioctl 调用。这些服务包括垂直同步（vblank）事件处理、内存管理、输出管理、帧缓冲管理、命令提交与围栏机制、挂起/恢复支持以及 DMA 服务。

驱动程序初始化
=====================

每个 DRM 驱动程序的核心都是一个 :c:type:`struct drm_driver <drm_driver>` 结构。驱动程序通常会静态初始化一个 `drm_driver` 结构，并将其传递给 `drm_dev_alloc()` 以分配设备实例。在设备实例完全初始化后，可以使用 `drm_dev_register()` 进行注册（使其可以在用户空间访问）。

:c:type:`struct drm_driver <drm_driver>` 结构包含描述驱动程序及其支持功能的静态信息，以及指向 DRM 核心将调用的方法指针，以实现 DRM API。我们将首先浏览 :c:type:`struct drm_driver <drm_driver>` 的静态信息字段，然后在后面的章节中详细介绍各个操作的使用情况。

驱动程序信息
------------------

主版本号、次版本号和补丁级别
~~~~~~~~~~~~~~~~~~~~~~~~~~~

int major;  
int minor;  
int patchlevel;

DRM 核心通过主版本号、次版本号和补丁级别三元组来识别驱动程序版本。该信息会在初始化时打印到内核日志，并通过 DRM_IOCTL_VERSION ioctl 传递给用户空间。

主版本号和次版本号也用于验证通过 DRM_IOCTL_SET_VERSION ioctl 传递的请求驱动程序 API 版本。当驱动程序 API 在次版本之间发生变化时，应用程序可以调用 DRM_IOCTL_SET_VERSION 选择特定版本的 API。如果请求的主版本号不等于驱动程序的主版本号，或者请求的次版本号大于驱动程序的次版本号，则 DRM_IOCTL_SET_VERSION 调用将返回错误。否则，将调用驱动程序的 set_version() 方法并传入请求的版本号。

名称和描述
~~~~~~~~~~~~~~~~~~~~

char *name;  
char *desc;  
char *date;

驱动程序名称会在初始化时打印到内核日志，用于 IRQ 注册并通过 DRM_IOCTL_VERSION ioctl 传递给用户空间。

驱动程序描述是一个仅供用户空间参考的字符串，并且不会被内核使用。

模块初始化
---------------------

.. kernel-doc:: include/drm/drm_module.h
   :doc: 概览

帧缓冲窗口的所有权管理
----------------------------------------------

.. kernel-doc:: drivers/gpu/drm/drm_aperture.c
   :doc: 概览

.. kernel-doc:: include/drm/drm_aperture.h
   :internal:

.. kernel-doc:: drivers/gpu/drm/drm_aperture.c
   :export:

设备实例和驱动程序处理
-----------------------------------

.. kernel-doc:: drivers/gpu/drm/drm_drv.c
   :doc: 驱动实例概览

.. kernel-doc:: include/drm/drm_device.h
   :internal:

.. kernel-doc:: include/drm/drm_drv.h
   :internal:

.. kernel-doc:: drivers/gpu/drm/drm_drv.c
   :export:

驱动加载
-----------

组件辅助工具使用
~~~~~~~~~~~~~~~~~~~~~~

.. kernel-doc:: drivers/gpu/drm/drm_drv.c
   :doc: 组件辅助工具使用建议

内存管理器初始化
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

每个 DRM 驱动程序都需要一个内存管理器，必须在加载时初始化。目前 DRM 包含两个内存管理器：Translation Table Manager (TTM) 和 Graphics Execution Manager (GEM)。本文档仅描述 GEM 内存管理器的使用。详情请参见？。
杂项设备配置
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

在配置PCI设备时，另一项可能需要执行的任务是映射视频BIOS。在许多设备上，VBIOS描述了设备配置、LCD面板时序（如果存在），并包含表示设备状态的标志。可以使用pci_map_rom()函数来映射BIOS，这是一个方便的函数，负责实际映射ROM，无论它是已经被影子映射到内存中（通常在地址0xc0000处）还是存在于PCI设备的ROM BAR中。请注意，在ROM被映射并提取了任何必要的信息后，应将其取消映射；在许多设备上，ROM地址解码器与其他BAR共享，因此保持映射可能会导致意外行为，如死机或内存损坏。

管理资源
-----------------

.. kernel-doc:: drivers/gpu/drm/drm_managed.c
   :doc: 管理资源

.. kernel-doc:: drivers/gpu/drm/drm_managed.c
   :export:

.. kernel-doc:: include/drm/drm_managed.h
   :internal:

打开/关闭、文件操作和IOCTLs
======================================

.. _drm_driver_fops:

文件操作
---------------

.. kernel-doc:: drivers/gpu/drm/drm_file.c
   :doc: 文件操作

.. kernel-doc:: include/drm/drm_file.h
   :internal:

.. kernel-doc:: drivers/gpu/drm/drm_file.c
   :export:

杂项工具
==============

打印
-------

.. kernel-doc:: include/drm/drm_print.h
   :doc: 打印

.. kernel-doc:: include/drm/drm_print.h
   :internal:

.. kernel-doc:: drivers/gpu/drm/drm_print.c
   :export:

工具
---------

.. kernel-doc:: include/drm/drm_util.h
   :doc: drm 工具

.. kernel-doc:: include/drm/drm_util.h
   :internal:

单元测试
============

KUnit
-----

KUnit（内核单元测试框架）为Linux内核中的单元测试提供了一个通用框架。本节涵盖了DRM子系统的特定内容。关于KUnit的一般信息，请参阅Documentation/dev-tools/kunit/start.rst。
如何运行测试？
~~~~~~~~~~~~~~~~~~~~~

为了便于运行测试套件，一个配置文件位于`drivers/gpu/drm/tests/.kunitconfig`中。它可以由`kunit.py`如下使用：

.. code-block:: bash

	$ ./tools/testing/kunit/kunit.py run --kunitconfig=drivers/gpu/drm/tests \
		--kconfig_add CONFIG_VIRTIO_UML=y \
		--kconfig_add CONFIG_UML_PCI_OVER_VIRTIO=y

.. note::
	`.kunitconfig`中包含的配置应该尽可能通用。
`CONFIG_VIRTIO_UML`和`CONFIG_UML_PCI_OVER_VIRTIO`未包含在其中，因为它们仅适用于用户模式Linux。

遗留支持代码
===================

本节简要介绍了部分旧的遗留支持代码，这些代码仅被旧的DRM驱动程序使用，这些驱动程序对底层设备进行了所谓的影子附加而不是注册为真正的驱动程序。这也包括一些旧的通用缓冲区管理和命令提交代码。新的现代驱动程序不要使用这些代码。
遗留挂起/恢复
---------------------

DRM核心提供了一些挂起/恢复代码，但希望获得完整挂起/恢复支持的驱动程序应提供save()和restore()函数。这些函数在挂起、休眠或恢复时被调用，并应在挂起或休眠状态下执行所需的任何状态保存或恢复。
int (*suspend)(struct drm_device *, pm_message_t state);  
int (*resume)(struct drm_device *);

这些是遗留的挂起和恢复方法，仅与遗留的影子附加驱动程序注册函数一起工作。新驱动程序应使用其总线类型提供的电源管理接口（通常是通过:c:type:`struct device_driver <device_driver>` dev_pm_ops），并将这些方法设置为NULL。
遗留DMA服务
-------------------

这应该涵盖核心如何支持DMA映射等。这些函数已弃用，不应使用。
当然，请提供你需要翻译的文本。
