模式设置助手函数
=============================

DRM 子系统旨在实现核心代码与辅助库之间的强分离。核心代码负责一般性的初始化和清理工作，并将用户空间请求解码为内核内部对象。其他所有工作由一组大型的辅助库处理，这些库可以自由组合，以便每个驱动程序选择适合的部分，并在需要特殊行为时避免使用共享代码。
这种核心代码与辅助库的区别在模式设置代码中尤其明显，因为所有驱动程序都共享一个用户空间 ABI。这与渲染端形成对比，渲染端几乎所有的内容（除少数例外）都可以视为可选的辅助代码。
这些辅助函数可以分为几个领域：

* 实现模式设置的辅助函数。这里重要的是一组原子辅助函数。旧驱动程序仍然经常使用传统的 CRTC 辅助函数。它们都共享同一组通用辅助虚函数表。对于非常简单的驱动程序（任何适合已弃用的 fbdev 子系统的设备），还有简单的显示管道辅助函数。
* 处理输出的大量辅助函数。首先是处理编码器和转码器 IP 块的通用桥接辅助函数。其次是处理面板相关的信息和逻辑的面板辅助函数。此外还有一大套用于各种接收标准（如 DisplayPort、HDMI、MIPI DSI）的辅助函数。最后还有一些通用辅助函数用于处理输出探测和处理 EDID。
* 最后一组辅助函数关注显示管道前端：平面、用于可见性检查和剪裁的矩形处理、翻页队列及其他相关内容。

模式设置辅助参考 - 公共虚函数表
===========================================

概述
------
.. kernel-doc:: include/drm/drm_modeset_helper_vtables.h
   :doc: overview

内部
------
.. kernel-doc:: include/drm/drm_modeset_helper_vtables.h
   :internal:

原子模式设置辅助函数参考
=========================================

概述
------
.. kernel-doc:: drivers/gpu/drm/drm_atomic_helper.c
   :doc: overview

实现异步原子提交
----------------------
.. kernel-doc:: drivers/gpu/drm/drm_atomic_helper.c
   :doc: implementing nonblocking commit

辅助函数参考
----------------------
.. kernel-doc:: include/drm/drm_atomic_helper.h
   :internal:

.. kernel-doc:: drivers/gpu/drm/drm_atomic_helper.c
   :export:

原子状态重置和初始化
----------------------
.. kernel-doc:: drivers/gpu/drm/drm_atomic_state_helper.c
   :doc: atomic state reset and initialization

原子状态辅助参考
----------------------
.. kernel-doc:: drivers/gpu/drm/drm_atomic_state_helper.c
   :export:

GEM 原子辅助参考
---------------------------
.. kernel-doc:: drivers/gpu/drm/drm_gem_atomic_helper.c
   :doc: overview

.. kernel-doc:: include/drm/drm_gem_atomic_helper.h
   :internal:

.. kernel-doc:: drivers/gpu/drm/drm_gem_atomic_helper.c
   :export:

简单 KMS 辅助参考
===========================
.. kernel-doc:: drivers/gpu/drm/drm_simple_kms_helper.c
   :doc: overview

.. kernel-doc:: include/drm/drm_simple_kms_helper.h
   :internal:

.. kernel-doc:: drivers/gpu/drm/drm_simple_kms_helper.c
   :export:

fbdev 辅助函数参考
======================
.. kernel-doc:: drivers/gpu/drm/drm_fb_helper.c
   :doc: fbdev helpers

.. kernel-doc:: drivers/gpu/drm/drm_fbdev_dma.c
   :export:

.. kernel-doc:: drivers/gpu/drm/drm_fbdev_shmem.c
   :export:

.. kernel-doc:: drivers/gpu/drm/drm_fbdev_ttm.c
   :export:

.. kernel-doc:: include/drm/drm_fb_helper.h
   :internal:

.. kernel-doc:: drivers/gpu/drm/drm_fb_helper.c
   :export:

格式辅助函数参考
======================
.. kernel-doc:: drivers/gpu/drm/drm_format_helper.c
   :export:

帧缓冲 DMA 辅助函数参考
==========================================
.. kernel-doc:: drivers/gpu/drm/drm_fb_dma_helper.c
   :doc: framebuffer dma helper functions

.. kernel-doc:: drivers/gpu/drm/drm_fb_dma_helper.c
   :export:

帧缓冲 GEM 辅助参考
======================
.. kernel-doc:: drivers/gpu/drm/drm_gem_framebuffer_helper.c
   :doc: overview

.. kernel-doc:: drivers/gpu/drm/drm_gem_framebuffer_helper.c
   :export:

桥接
=======

概述
------
.. kernel-doc:: drivers/gpu/drm/drm_bridge.c
   :doc: overview

显示驱动集成
----------------------
.. kernel-doc:: drivers/gpu/drm/drm_bridge.c
   :doc: display driver integration

对 MIPI-DSI 桥接的特别注意
----------------------
.. kernel-doc:: drivers/gpu/drm/drm_bridge.c
   :doc: special care dsi

桥接操作
----------------------
.. kernel-doc:: drivers/gpu/drm/drm_bridge.c
   :doc: bridge operations

桥接连接器辅助
----------------------
.. kernel-doc:: drivers/gpu/drm/drm_bridge_connector.c
   :doc: overview

桥接辅助参考
----------------------
.. kernel-doc:: include/drm/drm_bridge.h
   :internal:

.. kernel-doc:: drivers/gpu/drm/drm_bridge.c
   :export:

MIPI-DSI 桥接操作
----------------------
.. kernel-doc:: drivers/gpu/drm/drm_bridge.c
   :doc: dsi bridge operations

桥接连接器辅助参考
----------------------
.. kernel-doc:: drivers/gpu/drm/drm_bridge_connector.c
   :export:

面板-桥接辅助参考
----------------------
.. kernel-doc:: drivers/gpu/drm/bridge/panel.c
   :export:

面板辅助参考
======================
.. kernel-doc:: drivers/gpu/drm/drm_panel.c
   :doc: drm panel

.. kernel-doc:: include/drm/drm_panel.h
   :internal:

.. kernel-doc:: drivers/gpu/drm/drm_panel.c
   :export:

.. kernel-doc:: drivers/gpu/drm/drm_panel_orientation_quirks.c
   :export:

面板自刷新辅助参考
======================
.. kernel-doc:: drivers/gpu/drm/drm_self_refresh_helper.c
   :doc: overview

.. kernel-doc:: drivers/gpu/drm/drm_self_refresh_helper.c
   :export:

HDCP 辅助函数参考
======================
.. kernel-doc:: drivers/gpu/drm/display/drm_hdcp_helper.c
   :export:

显示端口辅助函数参考
======================
.. kernel-doc:: drivers/gpu/drm/display/drm_dp_helper.c
   :doc: dp helpers

.. kernel-doc:: include/drm/display/drm_dp.h
   :internal:

.. kernel-doc:: include/drm/display/drm_dp_helper.h
   :internal:

.. kernel-doc:: drivers/gpu/drm/display/drm_dp_helper.c
   :export:

显示端口 CEC 辅助函数参考
======================
.. kernel-doc:: drivers/gpu/drm/display/drm_dp_cec.c
   :doc: dp cec helpers

.. kernel-doc:: drivers/gpu/drm/display/drm_dp_cec.c
   :export:

显示端口双模适配器辅助函数参考
======================
.. kernel-doc:: drivers/gpu/drm/display/drm_dp_dual_mode_helper.c
   :doc: dp dual mode helpers

.. kernel-doc:: include/drm/display/drm_dp_dual_mode_helper.h
   :internal:

.. kernel-doc:: drivers/gpu/drm/display/drm_dp_dual_mode_helper.c
   :export:

显示端口 MST 辅助
======================

概述
------
.. kernel-doc:: drivers/gpu/drm/display/drm_dp_mst_topology.c
   :doc: dp mst helper

.. kernel-doc:: drivers/gpu/drm/display/drm_dp_mst_topology.c
   :doc: Branch device and port refcounting

函数参考
----------------------
.. kernel-doc:: include/drm/display/drm_dp_mst_helper.h
   :internal:

.. kernel-doc:: drivers/gpu/drm/display/drm_dp_mst_topology.c
   :export:

拓扑生命周期内部
----------------------
这些函数不导出给驱动程序，但在这里进行文档说明以帮助理解 MST 拓扑辅助函数

.. kernel-doc:: drivers/gpu/drm/display/drm_dp_mst_topology.c
   :functions: drm_dp_mst_topology_try_get_mstb drm_dp_mst_topology_get_mstb
               drm_dp_mst_topology_put_mstb
               drm_dp_mst_topology_try_get_port drm_dp_mst_topology_get_port
               drm_dp_mst_topology_put_port
               drm_dp_mst_get_mstb_malloc drm_dp_mst_put_mstb_malloc

MIPI DBI 辅助函数参考
======================
.. kernel-doc:: drivers/gpu/drm/drm_mipi_dbi.c
   :doc: overview

.. kernel-doc:: include/drm/drm_mipi_dbi.h
   :internal:

.. kernel-doc:: drivers/gpu/drm/drm_mipi_dbi.c
   :export:

MIPI DSI 辅助函数参考
======================
.. kernel-doc:: drivers/gpu/drm/drm_mipi_dsi.c
   :doc: dsi helpers

.. kernel-doc:: include/drm/drm_mipi_dsi.h
   :internal:

.. kernel-doc:: drivers/gpu/drm/drm_mipi_dsi.c
   :export:

显示流压缩辅助函数参考
======================
.. kernel-doc:: drivers/gpu/drm/display/drm_dsc_helper.c
   :doc: dsc helpers

.. kernel-doc:: include/drm/display/drm_dsc.h
   :internal:

.. kernel-doc:: drivers/gpu/drm/display/drm_dsc_helper.c
   :export:

输出探测辅助函数参考
======================
.. kernel-doc:: drivers/gpu/drm/drm_probe_helper.c
   :doc: output probing helper overview

.. kernel-doc:: drivers/gpu/drm/drm_probe_helper.c
   :export:

EDID 辅助函数参考
======================
.. kernel-doc:: include/drm/drm_edid.h
   :internal:

.. kernel-doc:: drivers/gpu/drm/drm_edid.c
   :export:

.. kernel-doc:: include/drm/drm_eld.h
   :internal:

.. kernel-doc:: drivers/gpu/drm/drm_eld.c
   :export:

SCDC 辅助函数参考
======================
.. kernel-doc:: drivers/gpu/drm/display/drm_scdc_helper.c
   :doc: scdc helpers

.. kernel-doc:: include/drm/display/drm_scdc_helper.h
   :internal:

.. kernel-doc:: drivers/gpu/drm/display/drm_scdc_helper.c
   :export:

HDMI Infoframes 辅助参考
======================
严格来说这不是一个 DRM 辅助库，但任何与 HDMI 输出接口的驱动程序（如 v4l 或 alsa 驱动程序）都可以使用它。
但它很好地融入了模式设置辅助库的整体主题，因此也包含在这里。

.. kernel-doc:: include/linux/hdmi.h
   :internal:

.. kernel-doc:: drivers/video/hdmi.c
   :export:

矩形工具参考
======================
.. kernel-doc:: include/drm/drm_rect.h
   :doc: rect utils

.. kernel-doc:: include/drm/drm_rect.h
   :internal:

.. kernel-doc:: drivers/gpu/drm/drm_rect.c
   :export:

翻页工作辅助参考
======================
.. kernel-doc:: include/drm/drm_flip_work.h
   :doc: flip utils

.. kernel-doc:: include/drm/drm_flip_work.h
   :internal:

.. kernel-doc:: drivers/gpu/drm/drm_flip_work.c
   :export:

辅助模式设置助手
======================
.. kernel-doc:: drivers/gpu/drm/drm_modeset_helper.c
   :doc: aux kms helpers

.. kernel-doc:: drivers/gpu/drm/drm_modeset_helper.c
   :export:

OF/DT 辅助
======================
.. kernel-doc:: drivers/gpu/drm/drm_of.c
   :doc: overview

.. kernel-doc:: drivers/gpu/drm/drm_of.c
   :export:

传统平面辅助参考
======================
.. kernel-doc:: drivers/gpu/drm/drm_plane_helper.c
   :doc: overview

.. kernel-doc:: drivers/gpu/drm/drm_plane_helper.c
   :export:

传统 CRTC/模式设置辅助函数参考
======================
.. kernel-doc:: drivers/gpu/drm/drm_crtc_helper.c
   :doc: overview

.. kernel-doc:: drivers/gpu/drm/drm_crtc_helper.c
   :export:

隐私屏类
======================
.. kernel-doc:: drivers/gpu/drm/drm_privacy_screen.c
   :doc: overview

.. kernel-doc:: include/drm/drm_privacy_screen_driver.h
   :internal:

.. kernel-doc:: include/drm/drm_privacy_screen_machine.h
   :internal:

.. kernel-doc:: drivers/gpu/drm/drm_privacy_screen.c
   :export:
