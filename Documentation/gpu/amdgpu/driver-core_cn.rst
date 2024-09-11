============================
核心驱动基础设施
============================

GPU硬件结构
======================

每个ASIC是由多个硬件模块组成的集合。我们称它们为“IP”（知识产权模块）。每个IP封装了特定的功能。IP是分版本的，并且可以互相组合。例如，你可能会有两个不同的ASIC，但它们都有系统DMA（SDMA）5.x IP。

驱动程序按照IP进行组织。有专门的驱动组件来处理每个IP的初始化和操作。还有一些较小的IP，几乎不需要或完全不需要与驱动程序交互，这些IP最终会归类到soc文件中的通用部分。
soc文件（如vi.c、soc15.c、nv.c）包含的是SoC本身方面的代码，而不是特定的IP。例如，GPU重置和寄存器访问函数都是SoC依赖的。
APU不仅包含CPU和GPU，还包含所有平台组件（音频、USB、GPIO等）。此外，许多组件在CPU、平台和GPU之间是共享的（例如，SMU、PSP等）。通常，特定组件（如CPU、GPU等）会有接口来与这些通用组件进行交互。对于S0i3这样的功能，需要在整个组件之间进行大量协调，但这可能超出了本节的范围。

就GPU而言，我们有以下主要IP：

GMC（图形内存控制器）
这是较旧的pre-vega芯片上的专用IP，但在vega及更新的芯片上已变得有些分散。现在，它们为特定的IP或IP组提供了专用的内存中心。然而，在驱动程序中，我们仍然将其视为一个单一组件，因为编程模型仍然非常相似。这是GPU上的不同IP获取内存（VRAM或系统内存）的方式。
它还支持每个进程的GPU虚拟地址空间。
IH（中断处理器）
这是GPU上的中断控制器。所有的IP都会将它们的中断发送给这个IP，它将这些中断聚合为一组环形缓冲区，驱动程序可以解析这些缓冲区以处理来自不同IP的中断。
PSP（平台安全处理器）
这负责SoC的安全策略，执行受信任的应用程序，并验证和加载其他模块的固件。
SMU（系统管理单元）
这是电源管理微控制器。它管理整个SoC。驱动程序与之交互以控制电源管理功能，如时钟、电压、电源轨等。

DCN（显示控制器Next）
这是显示控制器。它处理显示硬件。更多细节见 :ref:`显示核心 <amdgpu-display-core>`。

SDMA（系统DMA）
这是一个多用途的DMA引擎。内核驱动程序使用它进行各种操作，包括分页和GPU页表更新。它也暴露给用户空间供用户模式驱动程序（OpenGL、Vulkan等）使用。

GC（图形和计算）
这是图形和计算引擎，即包含3D流水线和着色器块的部分。这是GPU上最大的一块。3D流水线有很多子块。除此之外，它还包含了CP微控制器（ME、PFP、CE、MEC）和RLC微控制器。它暴露给用户空间供用户模式驱动程序（OpenGL、Vulkan、OpenCL等）使用。

VCN（视频核心Next）
这是多媒体引擎。它处理视频和图像编码和解码。它暴露给用户空间供用户模式驱动程序（VA-API、OpenMAX等）使用。

图形和计算微控制器
---------------------

CP（命令处理器）
这是涵盖GFX/计算流水线前端的硬件块的名称。主要由一些微控制器（PFP、ME、CE、MEC）组成。运行在这些微控制器上的固件提供了驱动程序与GFX/计算引擎交互的接口。

MEC（微引擎计算）
这是控制GFX/计算引擎上计算队列的微控制器。

MES（微引擎调度器）
这是一个新的用于管理队列的引擎。目前未使用。

RLC（运行列表控制器）
这是GFX/计算引擎中的另一个微控制器。它处理GFX/计算引擎内的电源管理相关功能。名字源自旧硬件，最初添加时的名字，现在与引擎的功能关系不大。

驱动结构
================

一般来说，驱动程序有一个特定SoC上所有IP的列表，并且对于初始化/结束/挂起/恢复等操作，基本上遍历该列表并处理每个IP。
一些有用的构造：

KIQ（内核接口队列）
这是内核驱动程序用于管理GFX/计算引擎上的其他图形和计算队列的控制队列。你可以用它来映射/取消映射其他队列等。
IB（间接缓冲区）
----------------

特定引擎的命令缓冲区。与其直接将命令写入队列，你可以将这些命令写入一段内存中，然后将该内存的指针放入队列。

硬件会跟随这个指针执行内存中的命令，然后再返回到环形队列中的其余命令。

.. _amdgpu_memory_domains:

内存域
======

.. kernel-doc:: include/uapi/drm/amdgpu_drm.h
   :doc: 内存域

缓冲对象
========

.. kernel-doc:: drivers/gpu/drm/amd/amdgpu/amdgpu_object.c
   :doc: amdgpu_object

.. kernel-doc:: drivers/gpu/drm/amd/amdgpu/amdgpu_object.c
   :internal:

PRIME 缓冲共享
=============

.. kernel-doc:: drivers/gpu/drm/amd/amdgpu/amdgpu_dma_buf.c
   :doc: PRIME 缓冲共享

.. kernel-doc:: drivers/gpu/drm/amd/amdgpu/amdgpu_dma_buf.c
   :internal:

MMU 通知器
==========

.. kernel-doc:: drivers/gpu/drm/amd/amdgpu/amdgpu_hmm.c
   :doc: MMU 通知器

.. kernel-doc:: drivers/gpu/drm/amd/amdgpu/amdgpu_hmm.c
   :internal:

AMDGPU 虚拟内存
===============

.. kernel-doc:: drivers/gpu/drm/amd/amdgpu/amdgpu_vm.c
   :doc: GPUVM

.. kernel-doc:: drivers/gpu/drm/amd/amdgpu/amdgpu_vm.c
   :internal:

中断处理
========

.. kernel-doc:: drivers/gpu/drm/amd/amdgpu/amdgpu_irq.c
   :doc: 中断处理

.. kernel-doc:: drivers/gpu/drm/amd/amdgpu/amdgpu_irq.c
   :internal:

IP 块
=====

.. kernel-doc:: drivers/gpu/drm/amd/include/amd_shared.h
   :doc: IP 块

.. kernel-doc:: drivers/gpu/drm/amd/include/amd_shared.h
   :identifiers: amd_ip_block_type amd_ip_funcs
