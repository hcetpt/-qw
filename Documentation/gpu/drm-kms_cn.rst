核模式设置 (KMS)
=========================

驱动程序必须通过调用 drmm_mode_config_init() 来初始化 DRM 设备的模式设置核心。该函数初始化 :c:type:`struct drm_device <drm_device>` 的 mode_config 字段，并且从不失败。一旦完成，需要通过初始化以下字段来设置模式配置：
-  int min_width, min_height; int max_width, max_height;
   帧缓冲区的最小和最大宽度和高度（以像素为单位）
-  struct drm_mode_config_funcs \*funcs;
   模式设置函数
概述
========

.. kernel-render:: DOT
   :alt: KMS 显示管道
   :caption: KMS 显示管道概览

   digraph "KMS" {
      node [shape=box]

      subgraph cluster_static {
          style=dashed
          label="静态对象"

          node [bgcolor=grey style=filled]
          "drm_plane A" -> "drm_crtc"
          "drm_plane B" -> "drm_crtc"
          "drm_crtc" -> "drm_encoder A"
          "drm_crtc" -> "drm_encoder B"
      }

      subgraph cluster_user_created {
          style=dashed
          label="用户空间创建的对象"

          node [shape=oval]
          "drm_framebuffer 1" -> "drm_plane A"
          "drm_framebuffer 2" -> "drm_plane B"
      }

      subgraph cluster_connector {
          style=dashed
          label="热插拔"

          "drm_encoder A" -> "drm_connector A"
          "drm_encoder B" -> "drm_connector B"
      }
   }

KMS 向用户空间呈现的基本对象结构非常简单：帧缓冲区（由 :c:type:`struct drm_framebuffer <drm_framebuffer>` 表示，参见 `帧缓冲抽象`_）流入平面。平面由 :c:type:`struct drm_plane <drm_plane>` 表示，更多细节请参见 `平面抽象`_。一个或多个（甚至没有）平面将其像素数据送入 CRTC（由 :c:type:`struct drm_crtc <drm_crtc>` 表示，参见 `CRTC 抽象`_）进行混合。具体的混合步骤在 `平面组合属性`_ 及相关章节中有更详细的解释。
对于输出路由的第一步是编码器（由 :c:type:`struct drm_encoder <drm_encoder>` 表示，参见 `编码器抽象`_）。这些实际上是用于实现 KMS 驱动程序的帮助库中的内部工件。除此之外，它们使用户空间难以确定哪些 CRTC 和连接器之间的连接是可能的，以及支持哪种类型的克隆，它们在用户空间 API 中没有用途。
不幸的是，编码器已被暴露给用户空间，因此目前无法移除它们。此外，驱动程序经常错误地设置了暴露的限制，并且在许多情况下这些限制不足以表达实际的限制。
一个 CRTC 可以连接到多个编码器，而对于活动的 CRTC 必须至少有一个编码器。
显示链中的最终、真正的终点是连接器（由 :c:type:`struct drm_connector <drm_connector>` 表示，参见 `连接器抽象`_）。连接器可以有不同的可能编码器，但内核驱动程序选择每个连接器使用的编码器。使用场景是 DVI，它可以在这之间切换模拟和数字编码器。编码器也可以驱动多个不同的连接器。每个活动编码器都有一个确切的活动连接器。
内部输出管道稍微复杂一些，并且更接近今天的硬件：

.. kernel-render:: DOT
   :alt: KMS 输出管道
   :caption: KMS 输出管道

   digraph "Output Pipeline" {
      node [shape=box]

      subgraph {
          "drm_crtc" [bgcolor=grey style=filled]
      }

      subgraph cluster_internal {
          style=dashed
          label="内部管道"
          {
              node [bgcolor=grey style=filled]
              "drm_encoder A";
              "drm_encoder B";
              "drm_encoder C";
          }

          {
              node [bgcolor=grey style=filled]
              "drm_encoder B" -> "drm_bridge B"
              "drm_encoder C" -> "drm_bridge C1"
              "drm_bridge C1" -> "drm_bridge C2";
          }
      }

      "drm_crtc" -> "drm_encoder A"
      "drm_crtc" -> "drm_encoder B"
      "drm_crtc" -> "drm_encoder C"


      subgraph cluster_output {
          style=dashed
          label="输出"

          "drm_encoder A" -> "drm_connector A";
          "drm_bridge B" -> "drm_connector B";
          "drm_bridge C2" -> "drm_connector C";

          "drm_panel"
      }
   }

内部有两个额外的帮助对象起作用。首先，为了能够共享编码器的代码（有时在同一 SoC 上，有时在芯片外），一个或多个 :ref:`drm_bridges`（由 :c:type:`struct drm_bridge <drm_bridge>` 表示）可以链接到编码器。这个链接是静态的，不能更改，这意味着如果有的话，交叉开关需要在 CRTC 和任何编码器之间映射。对于具有桥接器的驱动程序，通常在编码器级别没有剩余的代码。原子驱动程序可以省略所有编码器回调，基本上只留下一个虚拟路由对象，这是出于向后兼容性的需要，因为编码器已暴露给用户空间。
第二个对象是面板，由`:c:type:`struct drm_panel `<drm_panel>`表示，详见:ref:`drm_panel_helper`。面板没有固定的绑定点，但通常与嵌入了`:c:type:`struct drm_connector `<drm_connector>`的驱动程序私有结构关联。
请注意，目前桥接链和与连接器及面板的交互仍处于变动中，并未完全理清。

KMS核心结构和函数
==================

.. kernel-doc:: include/drm/drm_mode_config.h
   :internal:

.. kernel-doc:: drivers/gpu/drm/drm_mode_config.c
   :export:

.. _kms_base_object_abstraction:

模式集基础对象抽象
=====================

.. kernel-render:: DOT
   :alt: 模式对象和属性
   :caption: 模式对象和属性

   digraph {
      node [shape=box]

      "drm_property A" -> "drm_mode_object A"
      "drm_property A" -> "drm_mode_object B"
      "drm_property B" -> "drm_mode_object A"
   }

所有KMS对象的基础结构是`:c:type:`struct drm_mode_object `<drm_mode_object>`。它提供的一个基础服务是跟踪属性，这对原子IOCTL（参见`Atomic Mode Setting`_）尤为重要。令人有些意外的是，属性不是直接在每个对象上实例化的，而是独立存在的模式对象，由`:c:type:`struct drm_property `<drm_property>`表示，仅指定属性的类型和值范围。任何给定的属性都可以使用`drm_object_attach_property()`多次附加到不同的对象上。

.. kernel-doc:: include/drm/drm_mode_object.h
   :internal:

.. kernel-doc:: drivers/gpu/drm/drm_mode_object.c
   :export:

原子模式设置
=============

.. kernel-render:: DOT
   :alt: 模式对象和属性
   :caption: 模式对象和属性

   digraph {
      node [shape=box]

      subgraph cluster_state {
          style=dashed
          label="独立状态"

          "drm_atomic_state" -> "duplicated drm_plane_state A"
          "drm_atomic_state" -> "duplicated drm_plane_state B"
          "drm_atomic_state" -> "duplicated drm_crtc_state"
          "drm_atomic_state" -> "duplicated drm_connector_state"
          "drm_atomic_state" -> "duplicated driver private state"
      }

      subgraph cluster_current {
          style=dashed
          label="当前状态"

          "drm_device" -> "drm_plane A"
          "drm_device" -> "drm_plane B"
          "drm_device" -> "drm_crtc"
          "drm_device" -> "drm_connector"
          "drm_device" -> "driver private object"

          "drm_plane A" -> "drm_plane_state A"
          "drm_plane B" -> "drm_plane_state B"
          "drm_crtc" -> "drm_crtc_state"
          "drm_connector" -> "drm_connector_state"
          "driver private object" -> "driver private state"
      }

      "drm_atomic_state" -> "drm_device" [label="atomic_commit"]
      "duplicated drm_plane_state A" -> "drm_device"[style=invis]
   }

原子模式设置提供了事务性的模式集（包括平面）更新，但与通常的事务性try-commit和回滚方法有所不同：

- 首先，在提交失败时不允许进行任何硬件更改。这使我们能够实现DRM_MODE_ATOMIC_TEST_ONLY模式，允许用户空间探索某些配置是否可行。
- 这仍然允许仅设置和回滚软件状态，简化现有驱动程序的转换。但是，这使得审核驱动程序中的原子检查代码正确性变得非常困难：在整个数据结构中回滚更改很难做到正确。
- 最后，为了向后兼容和支持所有用例，原子更新需要是增量的，并且能够并行执行。硬件并不总是允许这样做，但在可能的情况下，不同CRTCs上的平面更新不应相互干扰，也不应因不同CRTCs上的输出路由改变而停滞。

综合以上因素，原子设计有两个后果：

- 整体状态被拆分为每个对象的状态结构：对于平面使用`:c:type:`struct drm_plane_state `<drm_plane_state>`，对于CRTCs使用`:c:type:`struct drm_crtc_state `<drm_crtc_state>`，对于连接器使用`:c:type:`struct drm_connector_state `<drm_connector_state>`。这些是唯一具有用户空间可见且可设置状态的对象。对于内部状态，驱动程序可以通过嵌入这些结构或为它们全局共享的硬件功能添加全新的状态结构来子类化这些结构，参见`:c:type:`struct drm_private_state `<drm_private_state>`。
- 原子更新作为完全独立的一堆结构体在`:c:type:`drm_atomic_state `<drm_atomic_state>`容器内组装和验证。驱动程序私有状态结构也在同一结构中跟踪；详见下一章。只有当状态被提交时，才会将其应用到驱动程序和模式集对象上。这样回滚更新就归结为释放内存和解除对对象如帧缓冲区的引用。
原子状态结构的锁定内部使用`:c:type:`struct drm_modeset_lock `<drm_modeset_lock>`。一般而言，不应将锁定暴露给驱动程序，相反，任何复制或查看状态的函数（例如`drm_atomic_get_crtc_state()`）应该自动获取正确的锁。锁定只保护软件数据结构，硬件状态更改的提交顺序则通过`:c:type:`struct drm_crtc_commit `<drm_crtc_commit>`进行排序。
继续阅读本章，以及 :ref:`drm_atomic_helper` 中关于特定主题的详细内容。

处理驱动程序私有状态
---------------------

.. kernel-doc:: drivers/gpu/drm/drm_atomic.c
   :doc: 处理驱动程序私有状态

原子模式设置函数参考
----------------------

.. kernel-doc:: include/drm/drm_atomic.h
   :internal:

.. kernel-doc:: drivers/gpu/drm/drm_atomic.c
   :export:

原子模式设置 IOCTL 和 UAPI 函数
--------------------------------

.. kernel-doc:: drivers/gpu/drm/drm_atomic_uapi.c
   :doc: 概览

.. kernel-doc:: drivers/gpu/drm/drm_atomic_uapi.c
   :export:

CRTC 抽象
=========

.. kernel-doc:: drivers/gpu/drm/drm_crtc.c
   :doc: 概览

CRTC 函数参考
----------------

.. kernel-doc:: include/drm/drm_crtc.h
   :internal:

.. kernel-doc:: drivers/gpu/drm/drm_crtc.c
   :export:

颜色管理函数参考
--------------------

.. kernel-doc:: drivers/gpu/drm/drm_color_mgmt.c
   :export:

.. kernel-doc:: include/drm/drm_color_mgmt.h
   :internal:

帧缓冲抽象
==========

.. kernel-doc:: drivers/gpu/drm/drm_framebuffer.c
   :doc: 概览

帧缓冲函数参考
----------------

.. kernel-doc:: include/drm/drm_framebuffer.h
   :internal:

.. kernel-doc:: drivers/gpu/drm/drm_framebuffer.c
   :export:

DRM 格式处理
============

.. kernel-doc:: include/uapi/drm/drm_fourcc.h
   :doc: 概览

格式函数参考
-------------

.. kernel-doc:: include/drm/drm_fourcc.h
   :internal:

.. kernel-doc:: drivers/gpu/drm/drm_fourcc.c
   :export:

.. _kms_dumb_buffer_objects:

简单缓冲对象
============

.. kernel-doc:: drivers/gpu/drm/drm_dumb_buffers.c
   :doc: 概览

平面抽象
=========

.. kernel-doc:: drivers/gpu/drm/drm_plane.c
   :doc: 概览

平面函数参考
--------------

.. kernel-doc:: include/drm/drm_plane.h
   :internal:

.. kernel-doc:: drivers/gpu/drm/drm_plane.c
   :export:

平面组合函数参考
---------------------

.. kernel-doc:: drivers/gpu/drm/drm_blend.c
   :export:

平面损坏跟踪函数参考
-------------------------

.. kernel-doc:: drivers/gpu/drm/drm_damage_helper.c
   :export:

.. kernel-doc:: include/drm/drm_damage_helper.h
   :internal:

平面恐慌功能
---------------

.. kernel-doc:: drivers/gpu/drm/drm_panic.c
   :doc: 概览

平面恐慌函数参考
-------------------

.. kernel-doc:: include/drm/drm_panic.h
   :internal:

.. kernel-doc:: drivers/gpu/drm/drm_panic.c
   :export:

显示模式函数参考
==================

.. kernel-doc:: include/drm/drm_modes.h
   :internal:

.. kernel-doc:: drivers/gpu/drm/drm_modes.c
   :export:

连接器抽象
===========

.. kernel-doc:: drivers/gpu/drm/drm_connector.c
   :doc: 概览

连接器函数参考
-----------------

.. kernel-doc:: include/drm/drm_connector.h
   :internal:

.. kernel-doc:: drivers/gpu/drm/drm_connector.c
   :export:

回写连接器
------------

.. kernel-doc:: drivers/gpu/drm/drm_writeback.c
   :doc: 概览

.. kernel-doc:: include/drm/drm_writeback.h
   :internal:

.. kernel-doc:: drivers/gpu/drm/drm_writeback.c
   :export:

编码器抽象
==========

.. kernel-doc:: drivers/gpu/drm/drm_encoder.c
   :doc: 概览

编码器函数参考
----------------

.. kernel-doc:: include/drm/drm_encoder.h
   :internal:

.. kernel-doc:: drivers/gpu/drm/drm_encoder.c
   :export:

KMS 锁定
========

.. kernel-doc:: drivers/gpu/drm/drm_modeset_lock.c
   :doc: KMS 锁定

.. kernel-doc:: include/drm/drm_modeset_lock.h
   :internal:

.. kernel-doc:: drivers/gpu/drm/drm_modeset_lock.c
   :export:

KMS 属性
========

本节文档主要针对用户空间开发者。对于驱动程序 API，请参阅其他部分。
要求
------------

KMS 驱动程序可能需要添加额外的属性以支持新特性。每个在驱动程序中引入的新属性除了满足上述要求外，还需要满足以下要求：

* 必须标准化，并记录以下内容：
  
  * 完整的确切名称字符串；
  * 如果该属性是枚举类型，则所有有效值的名称字符串；
  * 接受哪些值及其含义；
  * 该属性的作用及其使用方法；
  * 该属性与其他现有属性之间的交互方式。
* 必须在核心代码中提供一个通用的帮助程序来注册该属性。
* 其内容必须由核心解码，并提供在关联的对象状态结构中。这包括任何驱动程序可能希望预先计算的内容，如 planes 的 `struct drm_clip_rect`。
* 其初始状态必须与引入该属性之前的默认行为相匹配。这可能是硬件固有的固定值，也可能是引导过程中固件遗留的状态。
* 在合理的情况下，必须提交一个 IGT 测试。

由于历史原因，存在一些非标准的、特定于驱动程序的属性。如果一个 KMS 驱动程序想要支持这些属性中的任何一个，新的属性要求尽可能适用。此外，记录的行为必须与现有属性的实际语义相匹配，以确保兼容性。最初添加该属性的驱动程序开发者应帮助完成这些任务，并尽可能确认记录的行为。
属性类型和 Blob 属性支持
----------------------------------------

.. kernel-doc:: drivers/gpu/drm/drm_property.c
   :doc: 概述

.. kernel-doc:: include/drm/drm_property.h
   :内部:

.. kernel-doc:: drivers/gpu/drm/drm_property.c
   :导出:

.. _标准连接器属性:

标准连接器属性
-----------------------------

.. kernel-doc:: drivers/gpu/drm/drm_connector.c
   :doc: 标准连接器属性

HDMI 专用连接器属性
----------------------------------

.. kernel-doc:: drivers/gpu/drm/drm_connector.c
   :doc: HDMI 连接器属性

模拟电视专用连接器属性
---------------------------------------

.. kernel-doc:: drivers/gpu/drm/drm_connector.c
   :doc: 模拟电视连接器属性

标准 CRTC 属性
------------------------

.. kernel-doc:: drivers/gpu/drm/drm_crtc.c
   :doc: 标准 CRTC 属性

标准平面属性
-------------------------

.. kernel-doc:: drivers/gpu/drm/drm_plane.c
   :doc: 标准平面属性

.. _平面合成属性:

平面合成属性
----------------------------

.. kernel-doc:: drivers/gpu/drm/drm_blend.c
   :doc: 概述

.. _损坏跟踪属性:

损坏跟踪属性
--------------------------

.. kernel-doc:: drivers/gpu/drm/drm_plane.c
   :doc: 损坏跟踪

颜色管理属性
---------------------------

.. kernel-doc:: drivers/gpu/drm/drm_color_mgmt.c
   :doc: 概述

瓦片组属性
-------------------

.. kernel-doc:: drivers/gpu/drm/drm_connector.c
   :doc: 瓦片组

显式围栏属性
---------------------------

.. kernel-doc:: drivers/gpu/drm/drm_atomic_uapi.c
   :doc: 显式围栏属性

可变刷新属性
---------------------------

.. kernel-doc:: drivers/gpu/drm/drm_connector.c
   :doc: 可变刷新属性

光标热点属性
---------------------------

.. kernel-doc:: drivers/gpu/drm/drm_plane.c
   :doc: 热点属性

现有 KMS 属性
-----------------------

下表描述了由各种模块/驱动程序公开的 DRM 属性。由于此表非常笨重，请不要在此处添加任何新属性。相反，在上面的部分中记录它们。
.. csv-table::
   :header-rows: 1
   :file: kms-properties.csv

垂直消隐
=================

.. kernel-doc:: drivers/gpu/drm/drm_vblank.c
   :doc: 垂直消隐处理

垂直消隐和中断处理函数参考
------------------------------------------------------------

.. kernel-doc:: include/drm/drm_vblank.h
   :内部:

.. kernel-doc:: drivers/gpu/drm/drm_vblank.c
   :导出:

垂直消隐工作
===================

.. kernel-doc:: drivers/gpu/drm/drm_vblank_work.c
   :doc: 垂直消隐工作

垂直消隐工作函数参考
---------------------------------------

.. kernel-doc:: include/drm/drm_vblank_work.h
   :内部:

.. kernel-doc:: drivers/gpu/drm/drm_vblank_work.c
   :导出:
