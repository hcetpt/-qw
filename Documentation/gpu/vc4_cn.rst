=====================================
drm/vc4 Broadcom VC4 图形驱动程序
=====================================

.. kernel-doc:: drivers/gpu/drm/vc4/vc4_drv.c
   :doc: Broadcom VC4 图形驱动程序

显示硬件处理
=========================

本节涵盖与显示硬件相关的一切内容，包括模式设置基础设施、平面、精灵和光标处理以及显示输出探测等相关主题。
像素阀（DRM CRTC）
----------------------

.. kernel-doc:: drivers/gpu/drm/vc4/vc4_crtc.c
   :doc: VC4 CRTC 模块

HVS
---

.. kernel-doc:: drivers/gpu/drm/vc4/vc4_hvs.c
   :doc: VC4 HVS 模块

HVS 平面
----------

.. kernel-doc:: drivers/gpu/drm/vc4/vc4_plane.c
   :doc: VC4 平面模块

HDMI 编码器
------------

.. kernel-doc:: drivers/gpu/drm/vc4/vc4_hdmi.c
   :doc: VC4 Falcon HDMI 模块

DSI 编码器
-----------

.. kernel-doc:: drivers/gpu/drm/vc4/vc4_dsi.c
   :doc: VC4 DSI0/DSI1 模块

DPI 编码器
-----------

.. kernel-doc:: drivers/gpu/drm/vc4/vc4_dpi.c
   :doc: VC4 DPI 模块

VEC（复合电视输出）编码器
------------------------------

.. kernel-doc:: drivers/gpu/drm/vc4/vc4_vec.c
   :doc: VC4 SDTV 模块

KUnit 测试
===========

VC4 驱动程序使用 KUnit 进行特定于驱动程序的单元测试和集成测试。
这些测试使用了一个模拟驱动程序，并且可以在以下命令中运行，支持 arm 或 arm64 架构，

.. code-block:: bash

	$ ./tools/testing/kunit/kunit.py run \
		--kunitconfig=drivers/gpu/drm/vc4/tests/.kunitconfig \
		--cross_compile aarch64-linux-gnu- --arch arm64

目前由测试覆盖的驱动程序部分包括：
 * HVS 到 PixelValve 的动态 FIFO 分配，适用于 BCM2835-7 和 BCM2711
内存管理和 3D 命令提交
===========================================

本节涵盖 vc4 驱动程序中的 GEM 实现。
GPU 缓冲对象（BO）管理
---------------------------------

.. kernel-doc:: drivers/gpu/drm/vc4/vc4_bo.c
   :doc: VC4 GEM BO 管理支持

V3D 二值化命令列表（BCL）验证
----------------------------------------

.. kernel-doc:: drivers/gpu/drm/vc4/vc4_validate.c
   :doc: VC4 命令列表验证器

V3D 渲染命令列表（RCL）生成
----------------------------------------

.. kernel-doc:: drivers/gpu/drm/vc4/vc4_render_cl.c
   :doc: 渲染命令列表生成

VC4 着色器验证器
---------------------------

.. kernel-doc:: drivers/gpu/drm/vc4/vc4_validate_shaders.c
   :doc: VC4 着色器验证器

V3D 中断
--------------

.. kernel-doc:: drivers/gpu/drm/vc4/vc4_irq.c
   :doc: V3D 引擎中断管理
