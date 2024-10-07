SPDX 许可证标识符: GPL-2.0

.. _解码器:

*************************************************
内存到内存的有状态视频解码器接口
*************************************************

一个有状态的视频解码器接收完整的字节流块（例如，Annex-B H.264/HEVC 流、原始的 VP8/9 流），并按显示顺序将它们解码为原始视频帧。期望该解码器在处理这些缓冲区时不需要客户端提供任何额外信息。强烈不建议在驱动程序中进行软件解析、处理等操作以支持此接口。如果确实需要此类操作，则强烈建议使用无状态视频解码器接口（正在开发中）。

本文档中使用的约定和符号
===============================================

1. 如果本文件未另行规定，则适用通用的 V4L2 API 规则。
2. “必须”、“可以”、“应该”等词语的含义遵循 RFC 2119 的定义：<https://tools.ietf.org/html/rfc2119>
3. 所有未标记为“可选”的步骤都是必需的。
4. 除非另有说明，否则 :c:func:`VIDIOC_G_EXT_CTRLS` 和 :c:func:`VIDIOC_S_EXT_CTRLS` 可以与 :c:func:`VIDIOC_G_CTRL` 和 :c:func:`VIDIOC_S_CTRL` 互换使用。
5. 除非另有说明，根据解码器功能和遵循通用的 V4L2 指南，单平面 API（见 :ref:`planar-apis`）及其相关结构可以与多平面 API 互换使用。
6. i = [a..b]：从 a 到 b（包括 b）的整数序列，即 i = [0..2]：i = 0, 1, 2。
7. 给定一个“OUTPUT”缓冲区 A，则 A' 表示包含处理缓冲区 A 后生成数据的“CAPTURE”队列中的缓冲区。

.. _解码器术语表:

术语表
========

CAPTURE
   目标缓冲区队列；对于解码器，包含解码后的帧的缓冲区队列；对于编码器，包含已编码字节流的缓冲区队列；`V4L2_BUF_TYPE_VIDEO_CAPTURE` 或 `V4L2_BUF_TYPE_VIDEO_CAPTURE_MPLANE`；数据从硬件捕获到“CAPTURE”缓冲区中。
客户端（Client）
与实现此接口的解码器或编码器进行通信的应用程序。

编码格式（Coded format）
编码/压缩后的视频字节流格式（例如H.264、VP8等）；参见：原始格式（Raw format）。

编码高度（Coded height）
给定编码分辨率下的高度。

编码分辨率（Coded resolution）
符合编解码器和硬件要求的流分辨率，通常是可见分辨率向上取整到完整宏块；参见：可见分辨率（Visible resolution）。

编码宽度（Coded width）
给定编码分辨率下的宽度。

编码树单元（Coding tree unit）
HEVC编解码器的处理单元（在H.264、VP8、VP9中对应于宏块单元），可以使用最大64×64像素的块结构。擅长将图像细分为可变大小的结构。

解码顺序（Decode order）
帧被解码的顺序；如果编码格式包含帧重排序功能，则可能与显示顺序不同。对于解码器，“OUTPUT”缓冲区必须由客户端按照解码顺序排队；对于编码器，“CAPTURE”缓冲区必须由编码器按照解码顺序返回。

目标（Destination）
解码过程产生的数据；参见“CAPTURE”。

显示顺序（Display order）
帧必须显示的顺序；对于编码器，“OUTPUT”缓冲区必须由客户端按照显示顺序排队；对于解码器，“CAPTURE”缓冲区必须由解码器按照显示顺序返回。
DPB  
解码图像缓冲区；在 H.264/HEVC 中用于存储已解码的原始帧以供后续解码步骤参考的缓冲区

EOS  
流结束

IDR  
即时解码器刷新；在 H.264/HEVC 编码流中的一种关键帧，它会清除之前的所有参考帧（DPB）

关键帧  
一个不引用之前已解码帧的编码帧，即可以完全独立解码的帧

宏块  
基于线性块变换的图像和视频压缩格式中的处理单元（例如 H.264、VP8、VP9）；虽然编解码器特定，但对于大多数流行的编解码器，其大小为 16x16 像素。HEVC 编码器使用一个稍微更灵活的处理单元，称为编码树单元（CTU）

输出  
源缓冲队列；对于解码器，包含编码字节流的缓冲队列；对于编码器，包含原始帧的缓冲队列；`V4L2_BUF_TYPE_VIDEO_OUTPUT` 或 `V4L2_BUF_TYPE_VIDEO_OUTPUT_MPLANE`；硬件从 `输出` 缓冲区获取数据

PPS  
图像参数集；H.264/HEVC 字节流中的一种元数据实体

原始格式  
包含原始像素数据（例如 YUV、RGB 格式）的未压缩格式

恢复点  
字节流中的一个点，从此点开始/继续解码，无需任何先前的状态/数据，例如：关键帧（VP8/VP9）或 SPS/PPS/IDR 序列（H.264/HEVC）；恢复点是开始解码新流或在跳转后恢复解码所必需的
### 源数据
源数据
   提供给解码器或编码器的数据；详见“输出”

源高度
   给定源分辨率下的像素高度；仅对编码器相关

源分辨率
   源帧的像素分辨率，这些帧被输入到编码器，并且可能会进一步裁剪以适应可见分辨率的范围；仅对编码器相关

源宽度
   给定源分辨率下的像素宽度；仅对编码器相关

SPS
   序列参数集；H.264/HEVC字节流中的一种元数据类型

流元数据
   编码字节流中包含的附加（非视觉）信息；例如：编码分辨率、可见分辨率、编解码器配置文件

可见高度
   给定可见分辨率下的高度；显示高度

可见分辨率
   用于显示目的的可见图像的像素分辨率；必须小于或等于编码分辨率；显示分辨率

可见宽度
   给定可见分辨率下的宽度；显示宽度

状态机
=============

.. kernel-render:: DOT
   :alt: 解码器状态机的DOT图
   :caption: 解码器状态机

   digraph decoder_state_machine {
       node [shape = doublecircle, label="解码"] 解码;

       node [shape = circle, label="初始化"] 初始化;
       node [shape = circle, label="捕获\n设置"] 捕获设置;
       node [shape = circle, label="动态\n分辨率\n变化"] 分辨率变化;
       node [shape = circle, label="停止"] 停止;
       node [shape = circle, label="排空"] 排空;
       node [shape = circle, label="寻找"] 寻找;
       node [shape = circle, label="流结束"] 流结束;

       node [shape = point]; qi
       qi -> 初始化 [ label = "open()" ];

       初始化 -> 捕获设置 [ label = "CAPTURE\n格式\n建立" ];

       捕获设置 -> 停止 [ label = "CAPTURE\n缓冲区\n就绪" ];

       解码 -> 分辨率变化 [ label = "流\n分辨率\n变化" ];
       解码 -> 排空 [ label = "V4L2_DEC_CMD_STOP" ];
       解码 -> 流结束 [ label = "流中的\nEoS标记" ];
       解码 -> 寻找 [ label = "VIDIOC_STREAMOFF(OUTPUT)" ];
       解码 -> 停止 [ label = "VIDIOC_STREAMOFF(CAPTURE)" ];
       解码 -> 解码;

       分辨率变化 -> 捕获设置 [ label = "CAPTURE\n格式\n建立" ];
       分辨率变化 -> 寻找 [ label = "VIDIOC_STREAMOFF(OUTPUT)" ];

       流结束 -> 排空 [ label = "隐式\n排空" ];

       排空 -> 停止 [ label = "所有CAPTURE\n缓冲区已出队\n或\nVIDIOC_STREAMOFF(CAPTURE)" ];
       排空 -> 寻找 [ label = "VIDIOC_STREAMOFF(OUTPUT)" ];

       寻找 -> 解码 [ label = "VIDIOC_STREAMON(OUTPUT)" ];
       寻找 -> 初始化 [ label = "VIDIOC_REQBUFS(OUTPUT, 0)" ];

       停止 -> 解码 [ label = "V4L2_DEC_CMD_START\n或\nVIDIOC_STREAMON(CAPTURE)" ];
       停止 -> 寻找 [ label = "VIDIOC_STREAMOFF(OUTPUT)" ];
   }

查询功能
=====================

1. 要枚举解码器支持的编码格式集，客户端可以调用 :c:func:`VIDIOC_ENUM_FMT` 在 ``OUTPUT`` 上执行操作
* 无论 ``CAPTURE`` 上设置的格式如何，都会返回所有支持的格式。
* 有关解码器对每种编码格式能力的更多信息，请检查 :c:type:`v4l2_fmtdesc` 的 flags 字段，特别是解码器是否具有完整的字节流解析器以及是否支持动态分辨率变化。
2. 要枚举支持的原始格式集，客户端可以对 ``CAPTURE`` 调用 :c:func:`VIDIOC_ENUM_FMT`。
* 只会返回当前在 ``OUTPUT`` 上激活的格式所支持的格式。
* 为了枚举由特定编码格式支持的原始格式，客户端必须首先在 ``OUTPUT`` 上设置该编码格式，然后在 ``CAPTURE`` 上枚举格式。
3. 客户端可以使用 :c:func:`VIDIOC_ENUM_FRAMESIZES` 来检测给定格式支持的分辨率，通过在 :c:type:`v4l2_frmsizeenum` 中传递所需的像素格式。
* 对于编码像素格式，:c:func:`VIDIOC_ENUM_FRAMESIZES` 返回的值将包括解码器对于给定编码像素格式支持的所有可能编码分辨率。
* 对于原始像素格式，:c:func:`VIDIOC_ENUM_FRAMESIZES` 返回的值将包括解码器对于给定原始像素格式和当前在 ``OUTPUT`` 上设置的编码格式支持的所有可能帧缓冲分辨率。
4. 如果适用，可以通过各自的控件使用 :c:func:`VIDIOC_QUERYCTRL` 查询当前在 ``OUTPUT`` 上设置的编码格式所支持的配置文件和级别。
初始化
==============

1. 通过 :c:func:`VIDIOC_S_FMT` 设置 ``OUTPUT`` 的编码格式
* **必需字段：**

     ``type``
         一个适用于 ``OUTPUT`` 的 ``V4L2_BUF_TYPE_*`` 枚举值
``pixelformat``
         一种编码像素格式
``width``, ``height``
         流的编码分辨率；仅在无法从给定的编码格式中解析时才需要；否则解码器将使用此分辨率为占位符分辨率，一旦能够从流中解析实际的编码分辨率，该分辨率可能会发生变化
``sizeimage``
         ``OUTPUT`` 缓冲区的期望大小；解码器可能会根据硬件需求调整这个值
其他字段
         遵循标准语义
* **返回字段：**

     ``sizeimage``
         调整后的 ``OUTPUT`` 缓冲区大小
* ``CAPTURE`` 格式会立即根据 :c:func:`VIDIOC_S_FMT` 返回的宽度和高度更新适当的帧缓冲区分辨率
但是，对于包含流分辨率信息的编码格式，在解码器完成从流中解析信息后，它将用新值更新 ``CAPTURE`` 格式，并触发源变更事件，无论这些值是否与客户端设置的值匹配
.. 重要提示::

      更改 ``OUTPUT`` 格式可能会更改当前设置的 ``CAPTURE`` 格式。新的 ``CAPTURE`` 格式如何确定取决于解码器，客户端必须确保其符合自身需求。
2. 通过 `VIDIOC_REQBUFS` 在 ``OUTPUT`` 上分配源（字节流）缓冲区
* **必需字段：**

      ``count``
          请求分配的缓冲区数量；必须大于零
``type``
          适用于 ``OUTPUT`` 的 ``V4L2_BUF_TYPE_*`` 枚举值
``memory``
          遵循标准语义

* **返回字段：**

      ``count``
          实际分配的缓冲区数量

.. warning::

       实际分配的缓冲区数量可能与给定的 ``count`` 不同。客户端必须在函数调用返回后检查更新后的 ``count`` 值。

或者，可以在 ``OUTPUT`` 队列上使用 `VIDIOC_CREATE_BUFS` 来更精细地控制缓冲区分配。
* **必需字段：**

      ``count``
          请求分配的缓冲区数量；必须大于零
``type``
          适用于 ``OUTPUT`` 的 ``V4L2_BUF_TYPE_*`` 枚举值
``memory``
          遵循标准语义
``format``
遵循标准语义
* **返回字段：**

      ``count``
          调整为分配的缓冲区数量
.. warning::

       实际分配的缓冲区数量可能与给定的 ``count`` 不同。客户端必须在调用返回后检查更新后的 ``count`` 值。
3.  通过 :c:func:`VIDIOC_STREAMON` 开始在 ``OUTPUT`` 队列上进行流传输
4.  **此步骤仅适用于包含流中分辨率信息的编码格式。** 继续通过 :c:func:`VIDIOC_QBUF` 和 :c:func:`VIDIOC_DQBUF` 在 ``OUTPUT`` 队列上排队/取消排队字节流缓冲区。这些缓冲区将按顺序处理并返回给客户端，直到找到配置 ``CAPTURE`` 队列所需的元数据。这通过解码器发送一个带有 ``changes`` 设置为 ``V4L2_EVENT_SRC_CH_RESOLUTION`` 的 ``V4L2_EVENT_SOURCE_CHANGE`` 事件来指示。
* 如果第一个缓冲区没有足够的数据使这种情况发生，并不是错误。只要还需要更多数据，缓冲区的处理将继续进行。
* 如果触发事件的缓冲区中的数据需要用于解码第一帧，则在初始化序列完成并且帧被解码之前，不会将其返回给客户端。
* 如果客户端没有自行设置流的编码分辨率，在 ``CAPTURE`` 队列上调用 :c:func:`VIDIOC_G_FMT`、:c:func:`VIDIOC_S_FMT`、:c:func:`VIDIOC_TRY_FMT` 或 :c:func:`VIDIOC_REQBUFS` 将不会返回流的实际值，直到发出带有 ``changes`` 设置为 ``V4L2_EVENT_SRC_CH_RESOLUTION`` 的 ``V4L2_EVENT_SOURCE_CHANGE`` 事件为止。
.. important::

       解码器排队事件后发出的任何客户端查询都将返回适用于刚刚解析的流的值，包括队列格式、选择矩形和控制项。
.. note::

       能够从字节流中自行获取流参数的客户端可以尝试将 ``OUTPUT`` 格式的宽度和高度设置为匹配流编码大小的非零值，跳过此步骤，并继续执行“捕获设置”序列。然而，它不应依赖于任何有关流参数（如选择矩形和控制项）的驱动程序查询，因为解码器尚未从流中解析这些参数。如果客户端配置的值与解码器解析的值不匹配，将触发“动态分辨率更改”以重新配置它们。
.. note::

       在此阶段不会生成任何解码帧。

5.  继续执行 `Capture Setup` 序列。

Capture Setup
=============

1.  在 ``CAPTURE`` 队列上调用 :c:func:`VIDIOC_G_FMT`，以获取从字节流中解析/解码的目标缓冲区的格式。
* **必需字段：**

      ``type``
          一个适用于 ``CAPTURE`` 的 ``V4L2_BUF_TYPE_*`` 枚举值。
* **返回字段：**

      ``width``, ``height``
          解码帧的缓冲区分辨率。
``pixelformat``
          解码帧的像素格式。
``num_planes``（仅对于 _MPLANE 类型）
          像素格式的平面数。
``sizeimage``, ``bytesperline``
          按标准语义；匹配帧缓冲区格式。

.. note::

       ``pixelformat`` 的值可以是解码器当前流支持的任何像素格式。解码器应选择一个首选/最优格式作为默认配置。例如，如果需要额外的转换步骤，则可能更偏好 YUV 格式而不是 RGB 格式。

2.  **可选。** 通过 :c:func:`VIDIOC_G_SELECTION` 获取可见分辨率。
* **必填字段：**

      ``type``
          一个适用于 ``CAPTURE`` 的 ``V4L2_BUF_TYPE_*`` 枚举值
``target``
          设置为 ``V4L2_SEL_TGT_COMPOSE``

* **返回字段：**

      ``r.left``, ``r.top``, ``r.width``, ``r.height``
          可见矩形；必须适合由 :c:func:`VIDIOC_G_FMT` 在 ``CAPTURE`` 上返回的帧缓冲分辨率

* 以下选择目标在 ``CAPTURE`` 上受支持：

      ``V4L2_SEL_TGT_CROP_BOUNDS``
          对应于流的编码分辨率
``V4L2_SEL_TGT_CROP_DEFAULT``
          覆盖 ``CAPTURE`` 缓冲区中包含有意义图像数据（可见区域）的部分的矩形；宽度和高度将等于流的可见分辨率
``V4L2_SEL_TGT_CROP``
          在编码分辨率内输出到 ``CAPTURE`` 的矩形；默认为 ``V4L2_SEL_TGT_CROP_DEFAULT``；在没有额外组合/缩放功能的硬件上是只读的
``V4L2_SEL_TGT_COMPOSE_BOUNDS``
          被裁剪的帧可以组合进 ``CAPTURE`` 缓冲区的最大矩形；如果硬件不支持组合/缩放，则等于 ``V4L2_SEL_TGT_CROP``
``V4L2_SEL_TGT_COMPOSE_DEFAULT``
          等于 ``V4L2_SEL_TGT_CROP``
``V4L2_SEL_TGT_COMPOSE``
          被裁剪的帧写入 ``CAPTURE`` 缓冲区内的矩形；默认为 ``V4L2_SEL_TGT_COMPOSE_DEFAULT``；在没有额外组合/缩放功能的硬件上是只读的
``V4L2_SEL_TGT_COMPOSE_PADDED``
          被硬件覆盖的 ``CAPTURE`` 缓冲区内的矩形；如果硬件不写填充像素，则等于 ``V4L2_SEL_TGT_COMPOSE``
.. 警告::

       在解码器成功解析流元数据之前，这些值是无法保证有意义的。客户端在解析完成之前不应依赖这些查询。

3.  **可选。** 通过 :c:func:`VIDIOC_ENUM_FMT` 列出 ``CAPTURE`` 队列上的格式。一旦流信息被解析并已知，客户端可以使用此 ioctl 发现给定流支持哪些原始格式，并通过 :c:func:`VIDIOC_S_FMT` 选择其中一个格式。
.. 重要::

       解码器仅返回在此初始化序列中解析的 ``OUTPUT`` 格式和/或流元数据所支持的当前建立的编码格式，即使解码器通常可能支持更多格式。换句话说，返回的集合将是 `查询功能` 部分提到的初始查询的一个子集。
例如，一个解码器可能支持 1920x1088 及以下分辨率的 YUV 和 RGB 格式，但更高分辨率时仅支持 YUV（由于硬件限制）。解析 1920x1088 或更低分辨率后，:c:func:`VIDIOC_ENUM_FMT` 可能返回一组 YUV 和 RGB 像素格式，但在解析高于 1920x1088 的分辨率后，解码器将不会返回不支持该分辨率的 RGB 格式。
然而，在发现同一流中的分辨率变化后触发的后续分辨率更改事件可能会将流切换到较低分辨率，在这种情况下 :c:func:`VIDIOC_ENUM_FMT` 将再次返回 RGB 格式。

4.  **可选。** 通过 :c:func:`VIDIOC_S_FMT` 设置 ``CAPTURE`` 队列上的格式。客户端可以选择与解码器在 :c:func:`VIDIOC_G_FMT` 中选择/建议的不同格式。

* **必需字段：**

      ``type``
          一个适用于 ``CAPTURE`` 的 ``V4L2_BUF_TYPE_*`` 枚举值。
``pixelformat``
          一种原始像素格式。
``width``, ``height``
         解码流的帧缓冲区分辨率；通常与 :c:func:`VIDIOC_G_FMT` 返回的值相同，但如果硬件支持合成和/或缩放，则可能会有所不同。

* 设置 ``CAPTURE`` 格式会将组合选择矩形重置为基于新分辨率的默认值，如前一步所述。
5. **可选。** 如果需要并且解码器具有组合和/或缩放功能，可以通过 :c:func:`VIDIOC_S_SELECTION` 设置 `CAPTURE` 队列上的组合矩形。
* **必需字段：**

     ``type``
         一个适用于 `CAPTURE` 的 `V4L2_BUF_TYPE_*` 枚举值。
``target``
         设置为 `V4L2_SEL_TGT_COMPOSE`。
``r.left``, ``r.top``, ``r.width``, ``r.height``
         写入裁剪帧的 `CAPTURE` 缓冲区内的矩形；默认值为 `V4L2_SEL_TGT_COMPOSE_DEFAULT`；在没有额外组合/缩放功能的硬件上是只读的。
* **返回字段：**

     ``r.left``, ``r.top``, ``r.width``, ``r.height``
         可见矩形；它必须适应由 :c:func:`VIDIOC_G_FMT` 在 `CAPTURE` 上返回的帧缓冲区分辨率。
.. 注意::

      解码器可能会根据编解码器和硬件要求调整组合矩形到最接近的支持值。客户端需要检查由 :c:func:`VIDIOC_S_SELECTION` 返回的调整后的矩形。

6. 如果以下所有条件都满足，客户端可以立即恢复解码：
    
    * 新格式的 ``sizeimage``（在前面步骤中确定）小于或等于当前分配缓冲区的大小，
    
    * 当前分配的缓冲区数量大于或等于在前面步骤中获取的最小缓冲区数量。为了满足此要求，客户端可以使用 :c:func:`VIDIOC_CREATE_BUFS` 添加新的缓冲区。
在这种情况下，剩下的步骤不适用，并且客户端可以通过以下任意一种操作恢复解码：

    * 如果 `CAPTURE` 队列正在流传输，调用 :c:func:`VIDIOC_DECODER_CMD` 并使用 `V4L2_DEC_CMD_START` 命令，
    
    * 如果 `CAPTURE` 队列未进行流传输，调用 :c:func:`VIDIOC_STREAMON` 在 `CAPTURE` 队列上。
然而，如果客户端打算更改缓冲区集以减少内存使用或出于其他原因，则可以通过以下步骤实现。
7. **如果** `CAPTURE` **队列正在进行流传输，** 在 `CAPTURE` 队列上继续排队和出队缓冲区，直到出队一个带有 `V4L2_BUF_FLAG_LAST` 标志的缓冲区。
8. **如果** ``CAPTURE`` **队列正在流传输，** 则在 ``CAPTURE`` 队列上调用 :c:func:`VIDIOC_STREAMOFF` 来停止流传输。

.. warning::
   
       ``OUTPUT`` 队列必须保持流传输状态。在其上调用 :c:func:`VIDIOC_STREAMOFF` 将会中断序列并触发寻址。

9. **如果** ``CAPTURE`` **队列已分配了缓冲区，** 使用 :c:func:`VIDIOC_REQBUFS` 释放 ``CAPTURE`` 缓冲区。

* **必需的字段：**

      ``count``
          设置为 0
``type``
          一个适用于 ``CAPTURE`` 的 ``V4L2_BUF_TYPE_*`` 枚举值
``memory``
          遵循标准语义

10. 通过在 ``CAPTURE`` 队列上调用 :c:func:`VIDIOC_REQBUFS` 分配 ``CAPTURE`` 缓冲区。

* **必需的字段：**

      ``count``
          请求分配的缓冲区数量；大于零
``type``
          一个适用于 ``CAPTURE`` 的 ``V4L2_BUF_TYPE_*`` 枚举值
``memory``
          遵循标准语义
* **返回字段：**

      ``count``
          实际分配的缓冲区数量

.. warning::
   
   实际分配的缓冲区数量可能与给定的 ``count`` 不同。客户端必须在调用返回后检查更新后的 ``count`` 值。

.. note::

   为了分配超过最小数量的缓冲区（用于流水线深度），客户端可以查询 ``V4L2_CID_MIN_BUFFERS_FOR_CAPTURE`` 控制以获取所需的最小缓冲区数量，并将该值加上所需额外缓冲区的数量作为 ``count`` 字段传递给 :c:func:`VIDIOC_REQBUFS`。
   
   另外，可以在 ``CAPTURE`` 队列上使用 :c:func:`VIDIOC_CREATE_BUFS` 来获得对缓冲区分配更多的控制。例如，通过分配比当前 ``CAPTURE`` 格式更大的缓冲区，可以适应未来的分辨率变化。

* **必需字段：**

      ``count``
          请求分配的缓冲区数量；必须大于零
      
      ``type``
          适用于 ``CAPTURE`` 的 ``V4L2_BUF_TYPE_*`` 枚举类型
      
      ``memory``
          符合标准语义
      
      ``format``
          表示新分配的缓冲区需要适应的最大帧缓冲区分辨率的格式

* **返回字段：**

      ``count``
          调整为实际分配的缓冲区数量

.. warning::

   实际分配的缓冲区数量可能与给定的 ``count`` 不同。客户端必须在调用返回后检查更新后的 ``count`` 值。
.. 注意::

   要为与从流元数据中解析的不同格式分配缓冲区，客户端必须在开始元数据解析之前执行以下操作：

   * 将 ``OUTPUT`` 格式的宽度和高度设置为所需的编码分辨率，以便解码器能够适当地配置 ``CAPTURE`` 格式，

   * 使用 :c:func:`VIDIOC_G_FMT` 查询 ``CAPTURE`` 格式，并保存该格式直到此步骤完成。
通过此查询获得的格式可以在本步骤中与 :c:func:`VIDIOC_CREATE_BUFS` 一起使用以分配缓冲区。

11. 在 ``CAPTURE`` 队列上调用 :c:func:`VIDIOC_STREAMON` 以开始解码帧。

解码
=====

当 `Capture Setup` 序列成功完成后，系统进入此状态。在此状态下，客户端通过 :c:func:`VIDIOC_QBUF` 和 :c:func:`VIDIOC_DQBUF` 向两个队列排队和出队缓冲区，遵循标准语义。源 ``OUTPUT`` 缓冲区的内容取决于活动的编码像素格式，并可能受特定编解码器扩展控制的影响，具体请参见每种格式的文档。两个队列独立运行，遵循 V4L2 缓冲区队列和内存到内存设备的标准行为。此外，由于所选编码格式的特性（例如帧重排序），从 ``CAPTURE`` 队列出队的解码帧顺序可能与向 ``OUTPUT`` 队列排队的编码帧顺序不同。客户端不应假设 ``CAPTURE`` 和 ``OUTPUT`` 缓冲区之间有任何直接关系以及缓冲区可出队的具体时间。具体来说：

* 向 ``OUTPUT`` 排队的一个缓冲区可能导致没有在 ``CAPTURE`` 上生成任何缓冲区（例如，如果它不包含编码数据，或者仅包含其中的元数据语法结构）；

* 向 ``OUTPUT`` 排队的一个缓冲区可能导致在 ``CAPTURE`` 上生成多个缓冲区（如果编码数据包含多个帧，或者返回一个解码帧允许解码器返回一个在其解码顺序上先于它但在显示顺序上晚于它的帧）；

* 向 ``OUTPUT`` 排队的一个缓冲区可能导致在解码过程中更晚生成一个 ``CAPTURE`` 缓冲区，或在处理进一步的 ``OUTPUT`` 缓冲区之后生成，或者以错序方式返回（例如，如果使用了显示重排序）；

* 可能在没有向 ``OUTPUT`` 排队额外缓冲区的情况下有缓冲区出现在 ``CAPTURE`` 队列上（例如，在排空或到达 “EOS” 时），这是由于过去排队的 ``OUTPUT`` 缓冲区的解码结果因解码过程的特性而只有在稍后的时间才可用。

.. 注意::

   为了使解码后的 ``CAPTURE`` 缓冲区与其来源的 ``OUTPUT`` 缓冲区匹配，客户端可以在排队 ``OUTPUT`` 缓冲区时设置 :c:type:`v4l2_buffer` 结构中的 ``timestamp`` 字段。由该 ``OUTPUT`` 缓冲区解码得到的 ``CAPTURE`` 缓冲区在出队时其 ``timestamp`` 字段将被设置为相同的值。

除了一个 ``OUTPUT`` 缓冲区产生一个 ``CAPTURE`` 缓冲区这种简单的情况外，还定义了以下几种情况：

   * 一个 ``OUTPUT`` 缓冲区生成多个 ``CAPTURE`` 缓冲区：相同的 ``OUTPUT`` 时间戳将被复制到多个 ``CAPTURE`` 缓冲区中。
* 多个“OUTPUT”缓冲区生成一个“CAPTURE”缓冲区：排队的第一个“OUTPUT”缓冲区的时间戳将被复制。
* 解码顺序与显示顺序不同（即，“CAPTURE”缓冲区的顺序与“OUTPUT”缓冲区的顺序不一致）：“CAPTURE”时间戳不会保留“OUTPUT”时间戳的顺序。
.. 注意::

   被流用作参考帧的“CAPTURE”缓冲区的底层内存，即使在这些缓冲区出队后仍可能被硬件读取。
因此，在“CAPTURE”队列流过程中，客户端应避免写入该内存。否则可能导致解码帧损坏。
同样地，当使用非“V4L2_MEMORY_MMAP”的内存类型时，客户端应确保每个“CAPTURE”缓冲区在整个“CAPTURE”队列流过程中始终使用相同的底层内存。
这是因为 V4L2 缓冲区索引可以被驱动程序用来标识帧。因此，如果参考帧的底层内存在不同的缓冲区 ID 下提交，驱动程序可能会误识别它，并在它仍在使用时向其中解码新帧，从而导致后续帧的损坏。
在解码过程中，解码器可能会启动以下列出的特殊序列之一。这些序列将导致解码器返回所有来自处理前“OUTPUT”缓冲区的“CAPTURE”缓冲区。最后一个缓冲区将设置“V4L2_BUF_FLAG_LAST”标志。为了确定要遵循的序列，客户端必须检查是否有任何待处理事件，并：

* 如果有一个带有 `V4L2_EVENT_SRC_CH_RESOLUTION` 变更的 `V4L2_EVENT_SOURCE_CHANGE` 事件待处理，则需要遵循 `动态分辨率变更` 序列，

* 如果有一个 `V4L2_EVENT_EOS` 事件待处理，则需要遵循 `流结束` 序列。
某些序列可以相互交织，并且需要根据实际情况进行处理。每个序列的具体操作在文档中有详细说明。
如果发生解码错误，将根据解码器的能力报告给客户端，具体如下：

* 包含失败解码操作结果的“CAPTURE”缓冲区将以“V4L2_BUF_FLAG_ERROR”标志返回，
  
* 如果解码器能够准确报告触发错误的“OUTPUT”缓冲区，则该缓冲区也将以“V4L2_BUF_FLAG_ERROR”标志返回。
如果发生致命故障并且无法继续解码，则对相应解码文件句柄的任何进一步操作将返回 `-EIO` 错误代码。客户端可以选择关闭文件句柄并打开一个新的句柄，或者停止两个队列的流，释放所有缓冲区，并重新执行初始化序列。
Seek
====

Seek 操作由 ``OUTPUT`` 队列控制，因为它是编码数据的来源。Seek 操作不需要对 ``CAPTURE`` 队列进行任何特定的操作，但它可能按照正常的解码操作受到影响。

1. 通过调用 :c:func:`VIDIOC_STREAMOFF` 停止 ``OUTPUT`` 队列以开始寻址序列。
    * **必需字段：**
        - ``type``：一个适用于 ``OUTPUT`` 的 `V4L2_BUF_TYPE_*` 枚举值。
    * 解码器将丢弃所有待处理的 ``OUTPUT`` 缓冲区，并且这些缓冲区必须被视为已返回给客户端（遵循标准语义）。

2. 通过调用 :c:func:`VIDIOC_STREAMON` 重新启动 ``OUTPUT`` 队列。
    * **必需字段：**
        - ``type``：一个适用于 ``OUTPUT`` 的 `V4L2_BUF_TYPE_*` 枚举值。
    * 在该调用返回后，解码器将开始接受新的源字节流缓冲区。

3. 在寻址完成后向 ``OUTPUT`` 队列中排队包含编码数据的缓冲区，直到找到合适的恢复点。
    .. note::
        没有要求从一个确切的恢复点（例如SPS或关键帧）开始排队编码数据。任何排队的 ``OUTPUT`` 缓冲区都将被处理并返回给客户端，直到找到合适的恢复点。在寻找恢复点期间，解码器不应在 ``CAPTURE`` 缓冲区中生成任何解码后的帧。
一些硬件在进行非恢复点的寻址操作时可能会处理不当。此类操作可能导致“CAPTURE”队列中出现数量不定的解码错误帧。驱动程序必须确保不会发生致命的解码错误或崩溃，并实现任何必要的硬件问题处理和规避措施。

.. 警告::

   对于H.264/HEVC编解码器，客户端必须注意不要跨越SPS/PPS变化进行寻址。即使目标帧是一个关键帧，在解码器状态中的过期SPS/PPS也会导致解码结果不确定。虽然解码器必须在这种情况下不发生崩溃或致命解码错误，但客户端不应期望得到合理的解码输出。
如果硬件能够检测到这些解码错误帧，则相应的缓冲区将通过设置V4L2_BUF_FLAG_ERROR标志返回给客户端。有关解码错误报告的进一步描述，请参见“解码”部分。
4. 找到恢复点后，解码器将开始返回包含已解码帧的“CAPTURE”缓冲区。
.. 注意::

   寻址操作可能导致“动态分辨率变化”序列被触发，因为寻址目标可能具有与寻址前解码流部分不同的解码参数。该序列必须按照正常的解码器操作来处理。
.. 警告::

   未指定何时开始从“OUTPUT”队列中获取的缓冲区生成包含解码数据的“CAPTURE”队列缓冲区，因为其独立于“OUTPUT”队列运行。
解码器可能会返回一定数量的剩余“CAPTURE”缓冲区，其中包含来自寻址序列执行前排队的“OUTPUT”缓冲区的已解码帧。
“VIDIOC_STREAMOFF”操作会丢弃所有剩余的排队“OUTPUT”缓冲区，这意味着寻址序列前排队的所有“OUTPUT”缓冲区可能不会产生匹配的“CAPTURE”缓冲区。例如，对于以下“OUTPUT”队列的操作序列：

    QBUF(A), QBUF(B), STREAMOFF(), STREAMON(), QBUF(G), QBUF(H),

“CAPTURE”队列上的任何以下结果都是允许的：

    {A', B', G', H'}, {A', G', H'}, {G', H'}
要确定寻址后第一个解码帧所在的“CAPTURE”缓冲区，客户端可以通过观察时间戳来匹配“CAPTURE”和“OUTPUT”缓冲区，或者使用V4L2_DEC_CMD_STOP和V4L2_DEC_CMD_START来清空解码器。
.. 注意::

   为了实现即时寻址，客户端还可以重新启动“CAPTURE”队列上的流传输以丢弃已解码但尚未出队的缓冲区。
动态分辨率变化
=========================

包含分辨率元数据的流可能需要在解码过程中切换到不同的分辨率。
.. note::

   并非所有解码器都能检测分辨率变化。那些能够检测的解码器会在调用 :c:func:`VIDIOC_ENUM_FMT` 时为编码格式设置 ``V4L2_FMT_FLAG_DYN_RESOLUTION`` 标志。

当解码器检测到一个或多个以下参数与之前确定的参数（通过相应查询反映）不同时，序列开始：

* 编码分辨率（``OUTPUT`` 宽度和高度），
* 可见分辨率（选择矩形），
* 解码所需的最小缓冲区数量，
* 位深度发生变化

每当发生这种情况时，解码器必须按照以下步骤进行：

1. 在流中检测到分辨率变化后，解码器会发送一个带有 ``V4L2_EVENT_SRC_CH_RESOLUTION`` 的 ``V4L2_EVENT_SOURCE_CHANGE`` 事件。
.. important::

       解码器排队事件之后发出的任何客户端查询将返回分辨率变化后的流中的值，包括队列格式、选择矩形和控制信息。
2. 解码器随后处理并解码分辨率变化点之前的剩余所有缓冲区。
* 变化前的最后一个缓冲区必须标记为 ``V4L2_BUF_FLAG_LAST`` 标志，类似于上面的 `Drain` 序列。
.. warning::

       最后一个缓冲区可能是空的（:c:type:`v4l2_buffer` 的 ``bytesused`` = 0），在这种情况下，客户端必须忽略它，因为它不包含解码后的帧。
.. note::

       尝试从标记了 ``V4L2_BUF_FLAG_LAST`` 的缓冲区之后再出队更多 ``CAPTURE`` 缓冲区将导致 :c:func:`VIDIOC_DQBUF` 返回 -EPIPE 错误。

客户端必须按照以下描述继续该序列以继续解码过程。
1. 取出源变更事件
.. important::

       源变更会触发一个隐式的解码器清空操作，类似于显式的 `Drain` 序列。在解码器完成当前任务后会停止。
       必须通过调用 :c:func:`VIDIOC_STREAMOFF` 和 :c:func:`VIDIOC_STREAMON` 函数对 ``CAPTURE`` 队列进行操作，或者调用 :c:func:`VIDIOC_DECODER_CMD` 函数并使用 ``V4L2_DEC_CMD_START`` 命令来恢复解码过程。

2. 继续执行 `Capture Setup` 序列
.. note::

   在分辨率变更序列期间，``OUTPUT`` 队列必须保持流状态。如果在 ``OUTPUT`` 队列上调用 :c:func:`VIDIOC_STREAMOFF` 函数，则会中断序列并触发查找操作。
   从原则上讲，``OUTPUT`` 队列与 ``CAPTURE`` 队列独立运行，并且在整个分辨率变更序列期间也是如此。
   为了获得最佳性能和简化处理，客户端应该继续对 ``OUTPUT`` 队列进行缓冲区的入队/出队操作，即使在处理此序列时也不例外。

清空
=====

为了确保所有已排队的 ``OUTPUT`` 缓冲区已被处理，并且相关的 ``CAPTURE`` 缓冲区已交给客户端，客户端必须遵循以下的清空序列。在清空序列结束后，客户端将接收到所有在序列开始前排队的 ``OUTPUT`` 缓冲区的所有解码帧。
1. 开始清空操作，通过发出 :c:func:`VIDIOC_DECODER_CMD`
* **必需字段：**

     ``cmd``
         设置为 ``V4L2_DEC_CMD_STOP``
``flags``
设置为 0
``pts``
设置为 0

.. warning::

   序列只能在 `OUTPUT` 和 `CAPTURE` 队列都在流式传输时启动。为了兼容性原因，即使任何队列没有流式传输，调用 :c:func:`VIDIOC_DECODER_CMD` 也不会失败，但同时它也不会启动 `Drain` 序列，因此下面描述的步骤将不适用。

2. 在调用 :c:func:`VIDIOC_DECODER_CMD` 之前由客户端排队的所有 `OUTPUT` 缓冲区将被正常处理和解码。客户端必须继续独立处理两个队列，类似于正常的解码操作。这包括：

   * 处理因处理这些缓冲区而触发的任何操作，例如 `Dynamic Resolution Change` 序列，在继续进行排水序列之前，

   * 排队和取消排队 `CAPTURE` 缓冲区，直到取消排队带有 `V4L2_BUF_FLAG_LAST` 标志的缓冲区，

     .. warning::

        最后一个缓冲区可能是空的（带有 :c:type:`v4l2_buffer` 的 `bytesused` = 0），在这种情况下，客户端必须忽略它，因为它不包含已解码的帧。
        
.. note::

        尝试取消排队带有 `V4L2_BUF_FLAG_LAST` 标志之后的更多 `CAPTURE` 缓冲区将导致来自 :c:func:`VIDIOC_DQBUF` 的 -EPIPE 错误。
* 取消排队已处理的 `OUTPUT` 缓冲区，直到所有在 `V4L2_DEC_CMD_STOP` 命令前排队的缓冲区都被取消排队，

   * 如果客户端订阅了该事件，则取消排队 `V4L2_EVENT_EOS` 事件

.. note::

      为了向后兼容，解码器将在解码最后一帧并且所有帧都准备好取消排队时发出 `V4L2_EVENT_EOS` 事件。这是一种过时的行为，客户端不应依赖于此。应使用 `V4L2_BUF_FLAG_LAST` 缓冲标志代替。

3. 一旦所有在 `V4L2_DEC_CMD_STOP` 调用前排队的 `OUTPUT` 缓冲区都被取消排队，并且最后一个 `CAPTURE` 缓冲区也被取消排队，解码器将停止，并且不会处理任何新排队的 `OUTPUT` 缓冲区，直到客户端执行以下操作之一：

   * `V4L2_DEC_CMD_START` - 解码器不会重置，而是会从之前的排水状态中恢复正常操作，

   * 对 `CAPTURE` 队列的一对 :c:func:`VIDIOC_STREAMOFF` 和 :c:func:`VIDIOC_STREAMON` - 解码器将继续正常操作，但是队列中的任何 `CAPTURE` 缓冲区将返回给客户端，

   * 对 `OUTPUT` 队列的一对 :c:func:`VIDIOC_STREAMOFF` 和 :c:func:`VIDIOC_STREAMON` - 任何待处理的源缓冲区将返回给客户端，并触发 `Seek` 序列

.. note::

   一旦启动排水序列，客户端需要按照上述步骤将其完成，除非通过在 `OUTPUT` 或 `CAPTURE` 队列上发出 :c:func:`VIDIOC_STREAMOFF` 来终止该过程。在排水序列进行过程中，客户端不允许再次发出 `V4L2_DEC_CMD_START` 或 `V4L2_DEC_CMD_STOP`，如果尝试则会返回 -EBUSY 错误代码。
虽然不是强制性的，但可以使用 :c:func:`VIDIOC_TRY_DECODER_CMD` 查询解码器命令的可用性。

流结束
=======

如果解码器在流中遇到流结束标记，解码器将启动 `Drain` 序列，客户端必须按照上述方法处理，跳过初始的 :c:func:`VIDIOC_DECODER_CMD`。

提交点
======

设置格式和分配缓冲区会触发解码器行为的变化：
1. 在 ``OUTPUT`` 队列上设置格式可能会改变 ``CAPTURE`` 队列上支持/宣传的格式集。特别是，这也意味着 ``CAPTURE`` 格式可能会重置，客户端不应依赖于先前设置的格式得以保留。
2. 在 ``CAPTURE`` 队列上枚举格式始终只返回当前 ``OUTPUT`` 格式所支持的格式。
3. 在 ``CAPTURE`` 队列上设置格式不会改变 ``OUTPUT`` 队列上的可用格式列表。尝试设置一个不支持当前选定 ``OUTPUT`` 格式的 ``CAPTURE`` 格式会导致解码器调整请求的 ``CAPTURE`` 格式为一个支持的格式。
4. 在 ``OUTPUT`` 队列上枚举格式始终返回完整的支持编码格式集，无论当前的 ``CAPTURE`` 格式如何。
5. 当 ``OUTPUT`` 或 ``CAPTURE`` 队列中的任何缓冲区被分配时，客户端不得更改 ``OUTPUT`` 队列上的格式。驱动程序将对任何此类格式更改尝试返回 -EBUSY 错误代码。

总结来说，设置格式和分配操作必须始终从 ``OUTPUT`` 队列开始，并且 ``OUTPUT`` 队列是控制 ``CAPTURE`` 队列支持格式集的主控。
