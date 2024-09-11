=============================================
drm/meson AmLogic Meson 视频处理单元
=============================================

.. kernel-doc:: drivers/gpu/drm/meson/meson_drv.c
   :doc: 视频处理单元

视频处理单元
=====================

Amlogic Meson 显示控制器由以下几个组件组成，下面将对这些组件进行说明：

.. code::

  DMC|---------------VPU (视频处理单元)----------------|------HHI------|
     | vd1   _______     _____________    _________________     |               |
  D  |-------|      |----|            |   |                |    |   HDMI PLL    |
  D  | vd2   | VIU  |    | 视频后处理 |   | 视频编码器 |<---|-----VCLK      |
  R  |-------|      |----|            |   |                |    |               |
     | osd2  |      |    |            |---| Enci ----------|----|-----VDAC------|
  R  |-------| CSC  |----| 缩放器    |   | Encp ----------|----|----HDMI-TX----|
  A  | osd1  |      |    | 混合器   |   | Encl ----------|----|---------------|
  M  |-------|______|----|____________|   |________________|    |               |
  ___|__________________________________________________________|_______________|

视频输入单元
================

.. kernel-doc:: drivers/gpu/drm/meson/meson_viu.c
   :doc: 视频输入单元

视频后处理
=====================

.. kernel-doc:: drivers/gpu/drm/meson/meson_vpp.c
   :doc: 视频后处理

视频编码器
=============

.. kernel-doc:: drivers/gpu/drm/meson/meson_venc.c
   :doc: 视频编码器

视频时钟
============

.. kernel-doc:: drivers/gpu/drm/meson/meson_vclk.c
   :doc: 视频时钟

HDMI 视频输出
=================

.. kernel-doc:: drivers/gpu/drm/meson/meson_dw_hdmi.c
   :doc: HDMI 输出
