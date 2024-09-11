AMDgpu 显示管理器
======================

.. contents:: 目录
    :depth: 3

.. kernel-doc:: drivers/gpu/drm/amd/display/amdgpu_dm/amdgpu_dm.c
   :doc: 概览

.. kernel-doc:: drivers/gpu/drm/amd/display/amdgpu_dm/amdgpu_dm.h
   :internal:

生命周期
=========

.. kernel-doc:: drivers/gpu/drm/amd/display/amdgpu_dm/amdgpu_dm.c
   :doc: DM 生命周期

.. kernel-doc:: drivers/gpu/drm/amd/display/amdgpu_dm/amdgpu_dm.c
   :functions: dm_hw_init dm_hw_fini

中断处理
==========

.. kernel-doc:: drivers/gpu/drm/amd/display/amdgpu_dm/amdgpu_dm_irq.c
   :doc: 概览

.. kernel-doc:: drivers/gpu/drm/amd/display/amdgpu_dm/amdgpu_dm_irq.c
   :internal:

.. kernel-doc:: drivers/gpu/drm/amd/display/amdgpu_dm/amdgpu_dm.c
   :functions: register_hpd_handlers dm_crtc_high_irq dm_pflip_high_irq

原子实现
=====================

.. kernel-doc:: drivers/gpu/drm/amd/display/amdgpu_dm/amdgpu_dm.c
   :doc: 原子

.. kernel-doc:: drivers/gpu/drm/amd/display/amdgpu_dm/amdgpu_dm.c
   :functions: amdgpu_dm_atomic_check amdgpu_dm_atomic_commit_tail

颜色管理属性
===========================

.. kernel-doc:: drivers/gpu/drm/amd/display/amdgpu_dm/amdgpu_dm_color.c
   :doc: 概览

.. kernel-doc:: drivers/gpu/drm/amd/display/amdgpu_dm/amdgpu_dm_color.c
   :internal:

DCN 各代之间的 DC 颜色能力
---------------------------------------------

DRM/KMS 框架定义了三个 CRTC 颜色校正属性：degamma、颜色转换矩阵（CTM）和 gamma，以及两个用于 degamma 和 gamma 查找表（LUT）大小的属性。AMD DC 将某些颜色校正功能编程在混合前，但 DRM/KMS 没有每个平面的颜色校正属性。一般来说，DRM CRTC 颜色属性被编程到 DC 中，如下所示：CRTC gamma 在混合后，而 CRTC degamma 在混合前。尽管 CTM 被编程在混合后，但它映射到了 DPP 硬件块（混合前）。其他硬件中可用的颜色能力目前没有通过 DRM 接口暴露，并且被绕过。
.. kernel-doc:: drivers/gpu/drm/amd/display/dc/dc.h
   :doc: color-management-caps

.. kernel-doc:: drivers/gpu/drm/amd/display/dc/dc.h
   :internal:

颜色管道在 DCN 硬件各代之间发生了重大变化。混合前后可以执行的操作取决于硬件能力，如下图所示的 DCN 2.0 和 DCN 3.0 家族的模式：
**DCN 2.0 家族的颜色能力和映射**

.. kernel-figure:: dcn2_cm_drm_current.svg

**DCN 3.0 家族的颜色能力和映射**

.. kernel-figure:: dcn3_cm_drm_current.svg

混合模式属性
=====================

像素混合模式是 :c:type:`drm_plane` 的一个 DRM 平面组合属性，用于描述如何将前景平面（fg）的像素与背景平面（bg）进行组合。在这里，我们介绍 DRM 混合模式的主要概念，以帮助理解此属性是如何映射到 AMD DC 接口的。更多关于此 DRM 属性和 alpha 混合方程的信息，请参阅 :ref:`DRM Plane Composition Properties <plane_composition_properties>`。

基本上，混合模式设置了一个适用于该模式的 alpha 混合方程，其中 alpha 通道影响像素颜色值的状态，因此决定了结果像素颜色。例如，考虑以下 alpha 混合方程的元素：

- *fg.rgb*：前景像素的每个 RGB 组件值
- *fg.alpha*：前景像素的 alpha 组件值
- *bg.rgb*：背景的每个 RGB 组件值
- *plane_alpha*：由 **plane "alpha" 属性** 设置的平面 alpha 值，更多信息请参见 :ref:`DRM Plane Composition Properties <plane_composition_properties>`

在基本的 alpha 混合方程中：

   out.rgb = alpha * fg.rgb + (1 - alpha) * bg.rgb

每个平面中的像素 alpha 通道值被忽略，只有平面 alpha 影响结果像素颜色值。
DRM 有三种混合模式来定义平面组合中的混合公式：

* **None**：忽略像素 alpha 的混合公式
* **预乘**：混合公式假设平面中的像素颜色值在存储前已与其自身的Alpha通道预乘。
* **覆盖率**：混合公式假设像素颜色值未与Alpha通道值预乘。
预乘是默认的像素混合模式，这意味着当没有定义混合模式属性时，DRM认为平面的像素具有预乘的颜色值。在IGT GPU工具中，kms_plane_alpha_blend测试提供了一系列子测试来验证平面Alpha和混合模式属性。

AMDGPU显示管理器（DM）将DRM混合模式及其元素映射到Multiple Pipe/Plane Combined（MPC）的混合配置编程中，如下所示：

.. kernel-doc:: drivers/gpu/drm/amd/display/dc/inc/hw/mpc.h
   :functions: mpcc_blnd_cfg

因此，在MPC树上的单个MPCC实例的混合配置由:c:type:`mpcc_blnd_cfg`定义，其中:c:type:`pre_multiplied_alpha`是用于设置:c:type:`MPCC_ALPHA_MULTIPLIED_MODE`的Alpha预乘模式标志。它控制Alpha是否被乘以（真/假），仅在DRM预乘混合模式下为真。:c:type:`mpcc_alpha_blend_mode`定义了关于像素Alpha和平面Alpha值的Alpha混合模式。它设置了:c:type:`MPCC_ALPHA_BLND_MODE`的三种模式之一，如下所述：
.. kernel-doc:: drivers/gpu/drm/amd/display/dc/inc/hw/mpc.h
   :functions: mpcc_alpha_blend_mode

DM然后将`enum mpcc_alpha_blend_mode`的元素映射到DRM混合公式的元素，如下所示：

* *MPC像素Alpha*匹配*DRM fg.alpha*作为平面像素的Alpha分量值。
* *MPC全局Alpha*匹配*DRM plane_alpha*，当忽略像素Alpha时，因此像素值未预乘。
* *MPC全局增益*假设*MPC全局Alpha*值，当*DRM fg.alpha*和*DRM plane_alpha*都参与混合方程时。

简而言之，通过选择:c:type:`MPCC_ALPHA_BLEND_MODE_GLOBAL_ALPHA`，*fg.alpha*被忽略。另一方面，通过选择:c:type:`MPCC_ALPHA_BLEND_MODE_PER_PIXEL_ALPHA_COMBINED_GLOBAL_GAIN`，(plane_alpha * fg.alpha)分量变得可用。而:c:type:`MPCC_ALPHA_MULTIPLIED_MODE`定义了像素颜色值是否被Alpha预乘。

### 混合配置流程

Alpha混合方程从DRM到DC接口的配置路径如下：

1. 在更新:c:type:`drm_plane_state <drm_plane_state>`时，DM调用:c:type:`amdgpu_dm_plane_fill_blending_from_plane_state()`，该函数将:c:type:`drm_plane_state <drm_plane_state>`属性映射到:c:type:`dc_plane_info <dc_plane_info>`结构，以便在OS无关组件（DC）中处理。
2. 在DC接口上，:c:type:`struct mpcc_blnd_cfg <mpcc_blnd_cfg>`根据来自DPP的:c:type:`dc_plane_info <dc_plane_info>`输入编程MPCC混合配置。
