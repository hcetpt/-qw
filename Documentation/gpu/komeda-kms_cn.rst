SPDX 许可证标识符: GPL-2.0

==============================
drm/komeda Arm 显示驱动
==============================

drm/komeda 驱动支持 Arm 显示处理器 D71 及其后续产品。本文档简要概述了驱动设计：它是如何工作的以及为什么这样设计。
D71 类显示 IP 的概述
================================

从 D71 开始，Arm 显示 IP 开始采用灵活且模块化的架构。一个显示流水线由多个独立的功能阶段组成，这些阶段称为组件，每个组件具有特定的能力，可以对流入的像素数据进行特定处理。
典型的 D71 组件：

层（Layer）
-----
层是第一个流水线阶段，它为下一个阶段准备像素数据。它从内存中获取像素，如果需要的话解码 AFBC 数据，旋转源图像，将 YUV 像素解包或转换为设备内部的 RGB 像素，然后根据需要调整像素的颜色空间。

缩放器（Scaler）
------
如其名称所示，缩放器负责缩放，并且 D71 还支持通过缩放器进行图像增强。
缩放器的使用非常灵活，可以连接到层的输出进行层缩放，或者连接到合成器并缩放整个显示帧，然后将输出数据送入写回层（wb_layer），再将其写入内存。

合成器（Compositor）
-------------------
合成器将多个层或像素数据流合并成一个单一的显示帧。它的输出帧可以送入后图像处理器以在显示器上显示，也可以送入写回层并同时写入内存。
用户还可以在合成器和写回层之间插入一个缩放器来先缩小显示帧，然后再写入内存。

写回层（Writeback Layer）
--------------------------
写回层与层的操作相反，它连接到合成器并将合成结果写回内存。

后图像处理器（Post Image Processor）
-----------------------------
后图像处理器调整帧数据以适应显示器的要求，例如调整伽玛和颜色空间。

时序控制器（Timing Controller）
--------------------------------
显示流水线的最后阶段，时序控制器不是用于处理像素，而是仅用于控制显示时序。
合并器
------
D71缩放器主要仅具有与图层相比一半的水平输入/输出能力。例如，如果图层支持4K输入尺寸，则缩放器在同一时间只能支持2K输入/输出。为了实现全帧缩放，D71引入了图层分割（Layer Split），它将整个图像分成两个半部分，并分别发送给两个图层A和B进行独立缩放。缩放后需要将结果发送到合并器以将两部分图像合并在一起，然后输出合并后的结果到合成引擎。

分割器
------
类似于图层分割，但分割器用于写回，它将合成引擎的结果分成两部分，然后发送给两个缩放器。

可能的D71管道使用方式
===========================
得益于模块化架构，D71管道可以轻松调整以适应不同的用途。并且D71有两个管道，支持两种工作模式：

- 双显示模式：两个管道独立且分别驱动两个显示输出。
- 单显示模式：两个管道共同驱动一个显示输出。在此模式下，管道B不独立工作，而是将其合成结果输出到管道A中，并且其像素时序也从管道A的时序控制器派生出来。管道B的工作就像管道A（主）的一个“从属”。

单个管道数据流
-------------------------
.. kernel-render:: DOT
   :alt: 单个管道有向图
   :caption: 单个管道数据流

   digraph single_ppl {
      rankdir=LR;

      subgraph {
         "内存";
         "监视器";
      }

      subgraph cluster_pipeline {
          style=dashed
          node [shape=box]
          {
              node [bgcolor=grey style=dashed]
              "缩放器-0";
              "缩放器-1";
              "缩放器-0/1"
          }

         node [bgcolor=grey style=filled]
         "图层-0" -> "缩放器-0"
         "图层-1" -> "缩放器-0"
         "图层-2" -> "缩放器-1"
         "图层-3" -> "缩放器-1"

         "图层-0" -> "合成引擎"
         "图层-1" -> "合成引擎"
         "图层-2" -> "合成引擎"
         "图层-3" -> "合成引擎"
         "缩放器-0" -> "合成引擎"
         "缩放器-1" -> "合成引擎"

         "合成引擎" -> "缩放器-0/1" -> "写回层"
         "合成引擎" -> "图像处理" -> "时序控制器"
      }

      "写回层" -> "内存"
      "时序控制器" -> "监视器"
   }

双管道带从属启用
----------------------
.. kernel-render:: DOT
   :alt: 带从属的管道有向图
   :caption: 启用从属管道的数据流

   digraph slave_ppl {
      rankdir=LR;

      subgraph {
         "内存";
         "监视器";
      }
      node [shape=box]
      subgraph cluster_pipeline_slave {
          style=dashed
          label="从属管道B"
          node [shape=box]
          {
              node [bgcolor=grey style=dashed]
              "从属.缩放器-0";
              "从属.缩放器-1";
          }

         node [bgcolor=grey style=filled]
         "从属.图层-0" -> "从属.缩放器-0"
         "从属.图层-1" -> "从属.缩放器-0"
         "从属.图层-2" -> "从属.缩放器-1"
         "从属.图层-3" -> "从属.缩放器-1"

         "从属.图层-0" -> "从属.合成引擎"
         "从属.图层-1" -> "从属.合成引擎"
         "从属.图层-2" -> "从属.合成引擎"
         "从属.图层-3" -> "从属.合成引擎"
         "从属.缩放器-0" -> "从属.合成引擎"
         "从属.缩放器-1" -> "从属.合成引擎"
      }

      subgraph cluster_pipeline_master {
          style=dashed
          label="主管道A"
          node [shape=box]
          {
              node [bgcolor=grey style=dashed]
              "缩放器-0";
              "缩放器-1";
              "缩放器-0/1"
          }

         node [bgcolor=grey style=filled]
         "图层-0" -> "缩放器-0"
         "图层-1" -> "缩放器-0"
         "图层-2" -> "缩放器-1"
         "图层-3" -> "缩放器-1"

         "从属.合成引擎" -> "合成引擎"
         "图层-0" -> "合成引擎"
         "图层-1" -> "合成引擎"
         "图层-2" -> "合成引擎"
         "图层-3" -> "合成引擎"
         "缩放器-0" -> "合成引擎"
         "缩放器-1" -> "合成引擎"

         "合成引擎" -> "缩放器-0/1" -> "写回层"
         "合成引擎" -> "图像处理" -> "时序控制器"
      }

      "写回层" -> "内存"
      "时序控制器" -> "监视器"
   }

输入和输出子管道
------------------
一个完整的显示管道可以根据输入/输出用途轻松分为三个子管道：
图层（输入）管道
~~~~~~~~~~~~~~~~~~~~~
.. kernel-render:: DOT
   :alt: 图层数据有向图
   :caption: 图层（输入）数据流

   digraph layer_data_flow {
      rankdir=LR;
      node [shape=box]

      {
         node [bgcolor=grey style=dashed]
           "缩放器-n";
      }

      "图层-n" -> "缩放器-n" -> "合成引擎"
   }

.. kernel-render:: DOT
   :alt: 图层分割有向图
   :caption: 图层分割管道

   digraph layer_data_flow {
      rankdir=LR;
      node [shape=box]

      "图层-0/1" -> "缩放器-0" -> "合并器"
      "图层-2/3" -> "缩放器-1" -> "合并器"
      "合并器" -> "合成引擎"
   }

写回（输出）管道
~~~~~~~~~~~~~~~~~~~~~~~~~~
.. kernel-render:: DOT
   :alt: 写回有向图
   :caption: 写回（输出）数据流

   digraph writeback_data_flow {
      rankdir=LR;
      node [shape=box]

      {
         node [bgcolor=grey style=dashed]
           "缩放器-n";
      }

      "合成引擎" -> "缩放器-n" -> "写回层"
   }

.. kernel-render:: DOT
   :alt: 分割写回有向图
   :caption: 写回（输出）分割数据流

   digraph writeback_data_flow {
      rankdir=LR;
      node [shape=box]

      "合成引擎" -> "分割器"
      "分割器" -> "缩放器-0" -> "合并器"
      "分割器" -> "缩放器-1" -> "合并器"
      "合并器" -> "写回层"
   }

显示输出管道
~~~~~~~~~~~~~~~~~~~~~
.. kernel-render:: DOT
   :alt: 显示有向图
   :caption: 显示输出数据流

   digraph single_ppl {
      rankdir=LR;
      node [shape=box]

      "合成引擎" -> "图像处理" -> "时序控制器"
   }

在接下来的部分中，我们将看到这三个子管道将分别由KMS平面、wb_conn和CRTC来处理。

Komeda资源抽象
===========================
Komeda管道/组件结构体
--------------------------------
为了充分利用并轻松访问/配置硬件，驱动程序端也使用了类似的架构：管道/组件来描述硬件特性和功能，并且特定的组件包括两部分：

- 数据流控制
- 特定组件的功能和特性
因此，驱动程序定义了一个通用的头结构体`komeda_component`来描述数据流控制，并且所有特定组件都是该基础结构的子类。
.. kernel-doc:: drivers/gpu/drm/arm/display/komeda/komeda_pipeline.h
   :internal:

资源发现和初始化
=====================
管道和组件用于描述如何处理像素数据。我们仍然需要一个`@struct komeda_dev`来描述设备的整体视图及其控制能力。
我们有 &komeda_dev、&komeda_pipeline 和 &komeda_component。现在将设备与流水线关联起来。由于 komeda 不仅用于 D71，还计划用于后续产品，因此最好在不同产品之间尽可能共享资源。为了实现这一点，将 komeda 设备拆分为两层：CORE 和 CHIP。

- CORE：处理通用特性和功能
- CHIP：处理寄存器编程和硬件特定的特性（或限制）

CORE 可以通过以下三个芯片功能结构访问 CHIP：

- struct komeda_dev_funcs
- struct komeda_pipeline_funcs
- struct komeda_component_funcs

.. kernel-doc:: drivers/gpu/drm/arm/display/komeda/komeda_dev.h
   :internal:

格式处理
========

.. kernel-doc:: drivers/gpu/drm/arm/display/komeda/komeda_format_caps.h
   :internal:
.. kernel-doc:: drivers/gpu/drm/arm/display/komeda/komeda_framebuffer.h
   :internal:

将 komeda_dev 与 DRM-KMS 关联
==============================

Komeda 通过流水线/组件抽象资源，但 DRM-KMS 使用 crtc/plane/connector。一个 KMS 对象不能仅仅代表一个单一的组件，因为单个 KMS 对象的要求不能简单地由一个组件来满足，通常需要多个组件才能满足这些要求。例如，KMS 的设置模式、伽马、CTM 都针对 CRTC 对象，但 komeda 需要 compiz、improc 和 timing_ctrlr 协同工作才能满足这些要求。而一个 KMS 平面可能需要多个 komeda 资源：layer/scaler/compiz。因此，一个 KMS 对象代表一组 komeda 资源的子流水线：
- 平面：`Layer(input) pipeline`_
- 写回连接器：`Writeback(output) pipeline`_
- 显示输出流水线：`Display output pipeline`_

对于 komeda，我们将 KMS 的 crtc/plane/connector 视为管道和组件的用户，并且在任何时候一个管道/组件只能被一个用户使用。管道/组件将被视为 DRM-KMS 的私有对象；其状态也将由 drm_atomic_state 管理。

如何将平面映射到 Layer(input) 流水线
-----------------------------------------

Komeda 有多个 Layer 输入流水线，详见：
- `Single pipeline data flow`_
- `Dual pipeline with Slave enabled`_

最简单的方法是将一个平面绑定到固定的 Layer 流水线，但考虑到 komeda 的能力：
- Layer 分割，详见 `Layer(input) pipeline`_

    Layer 分割是一个相当复杂的特性，它将一张大图像分割成两个部分，并分别由两个层和两个缩放器处理。但这会在分割后的图像中间引入边缘问题或效果。为了避免这种问题，需要进行复杂的分割计算以及对层和缩放器的一些特殊配置。我们最好将这种与硬件相关的复杂性隐藏在用户模式下。
### 奴隶管道，参见 `Dual pipeline with Slave enabled`

由于Compiz组件不输出Alpha值，因此奴隶管道仅能用于底层合成。Komeda驱动希望向用户隐藏这一限制。实现方法是根据`plane_state->zpos`选择合适的Layer。

对于Komeda而言，KMS平面不代表一个固定的Komeda层管道，而是代表具有相同功能的多个Layer。Komeda将选择一个或多个Layer以满足一个KMS平面的要求。

### 将组件/管道设为drm_private_obj
---------------------------------------------

在`:c:type:` `komeda_component` 和`:c:type:` `komeda_pipeline` 中添加`:c:type:` `drm_private_obj`。

```c
struct komeda_component {
    struct drm_private_obj obj;
    ...
};

struct komeda_pipeline {
    struct drm_private_obj obj;
    ...
};
```

### 通过drm_atomic_state跟踪component_state/pipeline_state
-----------------------------------------------------------

在`:c:type:` `komeda_component_state` 和`:c:type:` `komeda_pipeline_state` 中添加`:c:type:` `drm_private_state` 和用户。

```c
struct komeda_component_state {
    struct drm_private_state obj;
    void *binding_user;
    ...
};

struct komeda_pipeline_state {
    struct drm_private_state obj;
    struct drm_crtc *crtc;
    ...
};
```

### Komeda组件验证
---------------------------

Komeda有多种类型的组件，但验证过程相似，通常包括以下步骤：

```c
int komeda_xxxx_validate(struct komeda_component_xxx xxx_comp,
                         struct komeda_component_output *input_dflow,
                         struct drm_plane/crtc/connector *user,
                         struct drm_plane/crtc/connector_state *user_state)
{
    // Setup 1: 检查组件是否需要，例如缩放器是可选的，取决于用户状态；如果不需要，则返回，调用者将数据流传递到下一阶段
    // Setup 2: 检查用户状态与组件的功能和能力，看是否满足要求；如果不满足，则返回失败
    // Setup 3: 从drm_atomic_state获取组件状态，并尝试将其设置为用户；如果组件已分配给其他用户，则失败
    // Setup 4: 配置组件状态，例如设置其输入组件，将用户状态转换为特定于组件的状态
}
```
### 设置 4：调整 input_dflow 并为下一阶段做准备

#### komeda_kms 抽象

```
.. kernel-doc:: drivers/gpu/drm/arm/display/komeda/komeda_kms.h
   :internal:
```

#### komeda_kms 函数

```
.. kernel-doc:: drivers/gpu/drm/arm/display/komeda/komeda_crtc.c
   :internal:
.. kernel-doc:: drivers/gpu/drm/arm/display/komeda/komeda_plane.c
   :internal:
```

### 构建 komeda 成为一个 Linux 模块驱动

现在我们有两个级别的设备：

-   `komeda_dev`：描述实际的显示硬件
-   `komeda_kms_dev`：将 `komeda_dev` 附加或连接到 DRM-KMS

所有 komeda 操作都是由 `komeda_dev` 或 `komeda_kms_dev` 提供或操作的，模块驱动只是一个简单的包装器，用于将 Linux 命令（如探测、移除、电源管理）传递给 `komeda_dev` 或 `komeda_kms_dev`。
