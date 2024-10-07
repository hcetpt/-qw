.. SPDX许可证标识符: GPL-2.0 或 GFDL-1.1-无不变或更高

.. _编码器:

*************************************************
内存到内存状态化视频编码器接口
*************************************************

状态化的视频编码器接收按显示顺序排列的原始视频帧并将其编码为字节流。它生成字节流的完整块，包括所有元数据、头部等。生成的字节流不需要客户端进行任何进一步的后处理。
在驱动程序中执行软件流处理、头文件生成等操作以支持此接口是强烈不建议的。如果需要此类操作，则强烈建议使用无状态视频编码器接口（正在开发中）。

本文件中使用的约定和符号
===============================================

1. 如果本文件未另行规定，则通常适用V4L2 API规则
2. “必须”、“可以”、“应该”等词汇的意义遵循 `RFC 2119 <https://tools.ietf.org/html/rfc2119>`_
3. 所有未标记为“可选”的步骤都是必需的
4. 除非另有说明，否则:c:func:`VIDIOC_G_EXT_CTRLS` 和 :c:func:`VIDIOC_S_EXT_CTRLS` 可与 :c:func:`VIDIOC_G_CTRL` 和 :c:func:`VIDIOC_S_CTRL` 互换使用
5. 除非另有说明，否则可以根据编码器的能力并遵循一般的V4L2指南，单平面API（参见 :ref:`planar-apis`）及其相关结构可以与多平面API互换使用
6. i = [a..b]：从a到b（包含）的整数序列，例如i = [0..2]：i = 0, 1, 2
7. 给定一个“OUTPUT”缓冲区A，那么A'表示一个在“CAPTURE”队列中的缓冲区，其中包含处理缓冲区A后得到的数据

术语表
========

参考 :ref:`decoder-glossary`
状态机
=============

.. kernel-render:: DOT
   :alt: 编码器状态机的DOT有向图
   :caption: 编码器状态机

   digraph encoder_state_machine {
       node [shape = doublecircle, label="编码"] 编码;

       node [shape = circle, label="初始化"] 初始化;
       node [shape = circle, label="停止"] 停止;
       node [shape = circle, label="排空"] 排空;
       node [shape = circle, label="重置"] 重置;

       node [shape = point]; qi
       qi -> 初始化 [ label = "open()" ];

       初始化 -> 编码 [ label = "两个队列都在流传输" ];

       编码 -> 排空 [ label = "V4L2_ENC_CMD_STOP" ];
       编码 -> 重置 [ label = "VIDIOC_STREAMOFF(CAPTURE)" ];
       编码 -> 停止 [ label = "VIDIOC_STREAMOFF(OUTPUT)" ];
       编码 -> 编码;

       排空 -> 停止 [ label = "所有CAPTURE缓冲区已出队\n或\nVIDIOC_STREAMOFF(OUTPUT)" ];
       排空 -> 重置 [ label = "VIDIOC_STREAMOFF(CAPTURE)" ];

       重置 -> 编码 [ label = "VIDIOC_STREAMON(CAPTURE)" ];
       重置 -> 初始化 [ label = "VIDIOC_REQBUFS(OUTPUT, 0)" ];

       停止 -> 编码 [ label = "V4L2_ENC_CMD_START\n或\nVIDIOC_STREAMON(OUTPUT)" ];
       停止 -> 重置 [ label = "VIDIOC_STREAMOFF(CAPTURE)" ];
   }

查询功能
=====================

1. 要枚举编码器支持的编码格式集，客户端可以调用 :c:func:`VIDIOC_ENUM_FMT` 在 ``CAPTURE`` 上
   * 不管 ``OUTPUT`` 上设置的格式是什么，都会返回支持的所有格式
2. 要枚举支持的原始格式集，客户端可以调用 :c:func:`VIDIOC_ENUM_FMT` 在 ``OUTPUT`` 上
   * 只会返回当前在 ``CAPTURE`` 上激活的格式所支持的格式
   * 为了枚举给定编码格式支持的原始格式，客户端必须首先在 ``CAPTURE`` 上设置该编码格式，然后枚举 ``OUTPUT`` 上的格式
3. 客户端可以使用 :c:func:`VIDIOC_ENUM_FRAMESIZES` 来检测给定格式支持的分辨率，在 :c:type:`v4l2_frmsizeenum` 的 ``pixel_format`` 中传递所需的像素格式
   * 对于编码像素格式，:c:func:`VIDIOC_ENUM_FRAMESIZES` 返回的值将包括编码器对该编码像素格式支持的所有可能编码分辨率
   * 对于原始像素格式，:c:func:`VIDIOC_ENUM_FRAMESIZES` 返回的值将包括编码器对给定原始像素格式和当前在 ``CAPTURE`` 上设置的编码格式支持的所有可能帧缓冲分辨率
4. 客户端可以使用 :c:func:`VIDIOC_ENUM_FRAMEINTERVALS` 来检测给定格式和分辨率支持的帧间隔，在 :c:type:`v4l2_frmivalenum` 的 ``pixel_format`` 中传递所需的像素格式，并在 :c:type:`v4l2_frmivalenum` 的 ``width`` 和 ``height`` 中传递分辨率
   * 对于编码像素格式和编码分辨率，:c:func:`VIDIOC_ENUM_FRAMEINTERVALS` 返回的值将包括编码器对该编码像素格式和分辨率支持的所有可能帧间隔
* 通过 :c:func:`VIDIOC_ENUM_FRAMEINTERVALS` 返回的值，对于原始像素格式和分辨率，将包括编码器对给定原始像素格式和分辨率支持的所有可能帧间隔，以及当前在 ``CAPTURE`` 上设置的编码格式、编码分辨率和编码帧间隔。
* 对于 :c:func:`VIDIOC_ENUM_FRAMEINTERVALS` 的支持是可选的。如果没有实现，则除了编解码器本身的限制之外没有其他特殊限制。
* 如果适用，可以使用各自的控件通过 :c:func:`VIDIOC_QUERYCTRL` 查询当前在 ``CAPTURE`` 上设置的编码格式所支持的配置文件和级别。
* 可以通过查询各自的控件来发现任何额外的编码器功能。

初始化
======

1. 通过 :c:func:`VIDIOC_S_FMT` 设置 ``CAPTURE`` 队列上的编码格式。
* **必需字段：**

    ``type``
        一个适用于 ``CAPTURE`` 的 ``V4L2_BUF_TYPE_*`` 枚举。
    ``pixelformat``
        要生成的编码格式。
    ``sizeimage``
        所需的 ``CAPTURE`` 缓冲区大小；编码器可能会根据硬件需求调整它。
    ``width``, ``height``
        忽略（只读）。
    其他字段
        遵循标准语义。
* **返回字段：**

     ``sizeimage``
         调整后的 ``CAPTURE`` 缓冲区大小
``width``, ``height``
         编码器根据当前状态选择的编码尺寸，例如 ``OUTPUT`` 格式、选择的矩形区域等（只读）
.. 重要提示::

      更改 ``CAPTURE`` 格式可能会更改当前设置的 ``OUTPUT`` 格式。新的 ``OUTPUT`` 格式如何确定取决于编码器，客户端必须确保其符合需求。
2. **可选。** 通过 :c:func:`VIDIOC_ENUM_FMT` 列出选定编码格式支持的 ``OUTPUT`` 格式（源的原始格式）
* **必需字段：**

     ``type``
         一个适用于 ``OUTPUT`` 的 ``V4L2_BUF_TYPE_*`` 枚举值
其他字段
         遵循标准语义
* **返回字段：**

     ``pixelformat``
         当前选定编码格式下 ``CAPTURE`` 队列支持的原始格式
其他字段
         遵循标准语义
3. 通过 :c:func:`VIDIOC_S_FMT` 设置 ``OUTPUT`` 队列上的原始源格式
* **必填字段：**

     ``type``
         一个适用于 ``OUTPUT`` 的 ``V4L2_BUF_TYPE_*`` 枚举值
``pixelformat``
         源的原始格式
``width``, ``height``
         源的分辨率
其他字段
         遵循标准语义

* **返回字段：**

     ``width``, ``height``
         可能会根据当前选定格式的要求进行调整，以满足编码器的最小值、最大值和对齐要求，如 :c:func:`VIDIOC_ENUM_FRAMESIZES` 所报告的
其他字段
         遵循标准语义

* 设置 ``OUTPUT`` 格式将会重置选择矩形到它们的默认值，基于新的分辨率，具体描述如下一步所示。

4. 通过 :c:func:`VIDIOC_S_PARM` 设置 ``OUTPUT`` 队列上的原始帧间隔。这也设置了 ``CAPTURE`` 队列上的编码帧间隔为相同的值。

* **必填字段：**

     ``type``
         一个适用于 ``OUTPUT`` 的 ``V4L2_BUF_TYPE_*`` 枚举值
``parm.output``
         将除 ``parm.output.timeperframe`` 之外的所有字段设置为 0
``parm.output.timeperframe``
期望的帧间隔；编码器可能会根据硬件需求进行调整

* **返回字段：**

    ``parm.output.timeperframe``
调整后的帧间隔

..重要提示::

   更改``OUTPUT``帧间隔也会设置编码器用于编码视频的帧率。因此，将帧间隔设置为1/24（或每秒24帧）将生成可以以该速度播放的编码视频流。“OUTPUT”队列的帧间隔只是一个提示，应用程序可以以不同的速率提供原始帧。驱动程序可以利用它来帮助调度并行运行的多个编码器。

在下一步中，可选地将“CAPTURE”帧间隔更改为其他值。这在离线编码时很有用，因为编码帧间隔可以与提供的原始帧速率不同。

..重要提示::

   ``timeperframe``处理的是*帧*，而不是场。因此对于隔行格式而言，这是两个场的时间，因为一帧包含一个顶场和一个底场。

..注意::

   由于历史原因，更改``OUTPUT``帧间隔也会更改``CAPTURE``队列上的编码帧间隔。理想情况下这些应该是独立的设置，但那样会破坏现有的API。

5. **可选**通过:c:func:`VIDIOC_S_PARM`设置``CAPTURE``队列上的编码帧间隔。只有当编码帧间隔与原始帧间隔不同时才需要这样做，这通常是离线编码的情况。此功能的支持由格式标志:ref:`V4L2_FMT_FLAG_ENC_CAP_FRAME_INTERVAL <fmtdesc-flags>`表示

* **必需字段：**

    ``type``
适用于``CAPTURE``的``V4L2_BUF_TYPE_*``枚举类型
``parm.capture``
除了``parm.capture.timeperframe``之外的所有字段均设为0
``parm.capture.timeperframe``
期望的编码帧间隔；编码器可能会根据硬件需求进行调整
* **返回字段：**

    ``parm.capture.timeperframe``
	调整后的帧间隔

.. 重要::

      更改 ``CAPTURE`` 帧间隔会设置编码视频的帧率。但这 *不会* 设置 ``CAPTURE`` 队列中缓冲区到达的速率，这取决于编码器的速度以及原始帧在 ``OUTPUT`` 队列中的排队速度。
      
.. 重要::

      ``timeperframe`` 处理的是 *帧*，而不是场。因此对于交错格式来说，这是两个场的时间，因为一帧包含一个顶部场和一个底部场。

.. 注意::

      并非所有驱动程序都支持此功能，在这种情况下只需为 ``OUTPUT`` 队列设置所需的编码帧间隔即可。
然而，能够根据 ``OUTPUT`` 帧间隔调度多个编码器的驱动程序必须支持此可选功能。

6. **可选。** 如果希望流元数据的可见分辨率与完整的 OUTPUT 分辨率不同，则可以通过对 ``OUTPUT`` 队列调用 :c:func:`VIDIOC_S_SELECTION` 来设置可见分辨率。

* **必需字段：**

    ``type``
         适用于 ``OUTPUT`` 的 ``V4L2_BUF_TYPE_*`` 枚举值
         
    ``target``
         设置为 ``V4L2_SEL_TGT_CROP``
         
    ``r.left``, ``r.top``, ``r.width``, ``r.height``
         可见矩形；这必须适合在 `V4L2_SEL_TGT_CROP_BOUNDS` 矩形内，并且可能会根据编解码器和硬件约束进行调整。

* **返回字段：**

     ``r.left``, ``r.top``, ``r.width``, ``r.height``
         经编码器调整后的可见矩形
* 下列选择目标在 ``OUTPUT`` 上受支持：

    ``V4L2_SEL_TGT_CROP_BOUNDS``
        等于完整的源帧，匹配活动的 ``OUTPUT`` 格式
        
    ``V4L2_SEL_TGT_CROP_DEFAULT``
        等于 ``V4L2_SEL_TGT_CROP_BOUNDS``
        
    ``V4L2_SEL_TGT_CROP``
        源缓冲区中要编码到 ``CAPTURE`` 流中的矩形；默认为 ``V4L2_SEL_TGT_CROP_DEFAULT``
.. note::

    这个选择目标的一个常见用例是编码一个分辨率不是宏块倍数的源视频，例如常见的1920x1080分辨率可能需要源缓冲区对齐到1920x1088以适应具有16x16宏块大小的编解码器。为了避免编码填充部分，客户端需要显式地将此选择目标配置为1920x1080。
.. warning::

    编码器可能会调整裁剪/组合矩形以满足编解码器和硬件要求。客户端需要检查由 :c:func:`VIDIOC_S_SELECTION` 返回的调整后的矩形。
7. 通过 :c:func:`VIDIOC_REQBUFS` 分配 ``OUTPUT`` 和 ``CAPTURE`` 的缓冲区。这可以按任意顺序进行。
* **必需字段：**

    ``count``
        请求分配的缓冲区数量；大于零
        
    ``type``
        一个适用于 ``OUTPUT`` 或 ``CAPTURE`` 的 ``V4L2_BUF_TYPE_*`` 枚举值
        
    其他字段
        遵循标准语义
* **返回字段：**

    ``count``
        实际分配的缓冲区数量
.. 警告::

      实际分配的缓冲区数量可能与给定的 ``count`` 不同。客户端必须在函数返回后检查更新后的 ``count`` 值。
.. 注意::

      为了分配超过最小数量的输出缓冲区（用于流水线深度），客户端可以查询 ``V4L2_CID_MIN_BUFFERS_FOR_OUTPUT`` 控制项以获取所需的最小缓冲区数量，并将该值加上所需的额外缓冲区数量作为 ``count`` 字段传递给 :c:func:`VIDIOC_REQBUFS`。
      另外，也可以使用 :c:func:`VIDIOC_CREATE_BUFS` 来更精细地控制缓冲区分配。
* **必需字段：**

     ``count``
         请求分配的缓冲区数量；必须大于零
``type``
         一个适用于 ``OUTPUT`` 的 ``V4L2_BUF_TYPE_*`` 枚举类型
其他字段
         遵循标准语义
* **返回字段：**

     ``count``
         调整为实际分配的缓冲区数量
8. 通过 :c:func:`VIDIOC_STREAMON` 在 ``OUTPUT`` 和 ``CAPTURE`` 队列上开始流传输。这可以在任意顺序下进行。当两个队列都开始流传输时，实际的编码过程才开始。
.. 注意::

   如果客户端在编码过程中停止了 ``CAPTURE`` 队列，然后再重新启动它，编码器将生成一个独立于停止前生成的流的新流。具体的约束取决于编码格式，但可能包括以下影响：

   * 重启后生成的编码帧不应引用任何停止前生成的帧，例如H.264/HEVC中的长期参考帧，

   * 任何需要包含在一个独立流中的头信息必须再次生成，例如H.264/HEVC中的SPS和PPS
编码
======

此状态是在初始化序列成功完成后达到的。在此状态下，客户端通过 :c:func:`VIDIOC_QBUF` 和 :c:func:`VIDIOC_DQBUF` 按照标准语义向两个队列排队和取消排队缓冲区。
编码的 ``CAPTURE`` 缓冲区的内容取决于当前的像素编码格式，并且可能会受到编解码器特定扩展控制的影响，具体说明请参见每种格式的文档。两个队列独立运行，遵循 V4L2 缓冲队列和内存到内存设备的标准行为。此外，从 ``CAPTURE`` 队列中出队的编码帧顺序可能与向 ``OUTPUT`` 队列入队的原始帧顺序不同，这是由于所选编码格式的特性（例如帧重排序）。

客户端不应假定 ``CAPTURE`` 和 ``OUTPUT`` 缓冲区之间有任何直接关系以及缓冲区变为可出队的具体时间。具体来说：

* 向 ``OUTPUT`` 队列入队的一个缓冲区可能导致在 ``CAPTURE`` 上生成多个缓冲区（例如，如果返回一个编码帧允许编码器返回一个显示顺序在其之前但解码顺序在其之后的帧；然而，也可能有其他原因导致这种情况）。

* 向 ``OUTPUT`` 队列入队的一个缓冲区可能在编码过程中较晚时生成 ``CAPTURE`` 缓冲区，或者在处理更多 ``OUTPUT`` 缓冲区后生成，或者以乱序方式返回（例如，如果使用了显示重排序）。

* 在没有额外 ``OUTPUT`` 缓冲区入队的情况下，``CAPTURE`` 队列上可能有缓冲区可用（例如，在清空或 EOS 期间），这是因为过去入队的 ``OUTPUT`` 缓冲区的编码结果直到后来才可用，这取决于编码过程的具体情况。

* 向 ``OUTPUT`` 队列入队的缓冲区在编码为相应的 ``CAPTURE`` 缓冲区后可能不会立即变为可出队，例如，如果编码器需要将该帧用作进一步编码的参考帧。
.. note:: 

   为了使客户端能够匹配编码的 ``CAPTURE`` 缓冲区与其来源的 ``OUTPUT`` 缓冲区，客户端可以在入队 ``OUTPUT`` 缓冲区时设置 :c:type:`v4l2_buffer` 结构体中的 ``timestamp`` 字段。由该 ``OUTPUT`` 缓冲区编码生成的 ``CAPTURE`` 缓冲区将在出队时将其 ``timestamp`` 字段设置为相同的值。

除了一个 ``OUTPUT`` 缓冲区生成一个 ``CAPTURE`` 缓冲区的简单情况外，还定义了以下几种情况：

* 一个 ``OUTPUT`` 缓冲区生成多个 ``CAPTURE`` 缓冲区：相同的 ``OUTPUT`` 时间戳将被复制到多个 ``CAPTURE`` 缓冲区。

* 编码顺序与呈现顺序不同（即 ``CAPTURE`` 缓冲区相对于 ``OUTPUT`` 缓冲区是乱序的）：``CAPTURE`` 时间戳将不保留 ``OUTPUT`` 时间戳的顺序。
.. note:: 

   为了让客户端区分帧类型（关键帧、中间帧；具体的类型列表取决于编码格式），``CAPTURE`` 缓冲区在出队时会在其 :c:type:`v4l2_buffer` 结构体中设置相应的标志位。请参阅 :c:type:`v4l2_buffer` 和每个像素编码格式的文档以获取确切的标志列表及其含义。

如果发生编码错误，将根据编码器的能力详细报告给客户端。具体来说：

* 包含失败编码操作结果的 ``CAPTURE`` 缓冲区（如果有）将以 ``V4L2_BUF_FLAG_ERROR`` 标志位返回，

* 如果编码器能够精确报告触发错误的 ``OUTPUT`` 缓冲区，则这些缓冲区将以 ``V4L2_BUF_FLAG_ERROR`` 标志位返回。
.. note:: 

   如果 ``CAPTURE`` 缓冲区太小，则仅以 ``V4L2_BUF_FLAG_ERROR`` 标志位返回。需要做更多的工作来检测这种错误是否是因为缓冲区太小，并提供支持来释放那些太小的现有缓冲区。

在发生致命故障且无法继续编码的情况下，对相应编码器文件句柄的任何进一步操作将返回 -EIO 错误代码。客户端可以关闭文件句柄并打开一个新的，或者通过停止两个队列的流传输、释放所有缓冲区并重新执行初始化序列来重新初始化实例。

编码参数更改
=============

客户端可以在任何时候使用 :c:func:`VIDIOC_S_CTRL` 来更改编码器参数。参数的可用性取决于编码器，客户端必须查询编码器以找到可用的控制集。
在编码过程中更改每个参数的能力是编码器特有的，遵循V4L2控制接口的标准语义。客户端可以在编码期间尝试设置一个控制项，如果操作失败并返回-EBUSY错误码，则需要停止“CAPTURE”队列以允许配置更改。为此，可以遵循`Drain`序列来避免丢失已经排队/编码的帧。

参数更新的时间点是编码器特有的，遵循V4L2控制接口的标准语义。如果客户端需要在特定帧上精确应用参数，应考虑使用请求API（:ref:`media-request-api`），前提是编码器支持该功能。

Drain
=====

为了确保所有已排队的“OUTPUT”缓冲区都被处理，并且相关的“CAPTURE”缓冲区被交给客户端，客户端必须遵循下面描述的Drain序列。在Drain序列结束后，客户端将接收到所有在序列开始之前排队的“OUTPUT”缓冲区中的已编码帧。

1. 通过调用:c:func:`VIDIOC_ENCODER_CMD`开始Drain序列。
    **必需字段：**
    
        ``cmd``
            设置为``V4L2_ENC_CMD_STOP``
        
        ``flags``
            设置为0
        
        ``pts``
            设置为0
            
    .. warning::
    
        只有当“OUTPUT”和“CAPTURE”队列都在流式传输时，才能启动此序列。出于兼容性原因，即使其中一个队列没有流式传输，调用:c:func:`VIDIOC_ENCODER_CMD`也不会失败，但同时它也不会启动Drain序列，因此以下步骤不适用。
    
2. 在发出:c:func:`VIDIOC_ENCODER_CMD`之前由客户端排队的所有“OUTPUT”缓冲区将被正常处理和编码。客户端必须继续独立处理两个队列，类似于正常的编码操作。这包括：
   
   * 排队和出队“CAPTURE”缓冲区，直到出队带有``V4L2_BUF_FLAG_LAST``标志的缓冲区，
   
     .. warning::
     
        最后一个缓冲区可能是空的（:c:type:`v4l2_buffer`的``bytesused`` = 0），在这种情况下，客户端必须忽略它，因为它不包含编码帧。
       
    .. note::
    
        尝试从带有``V4L2_BUF_FLAG_LAST``标志的缓冲区之后出队更多“CAPTURE”缓冲区会导致:c:func:`VIDIOC_DQBUF`返回-EPIPE错误。
* 取出已处理的 ``OUTPUT`` 缓冲区，直到所有在发出 ``V4L2_ENC_CMD_STOP`` 命令之前排队的缓冲区都被取出，

* 如果客户端订阅了该事件，则取出 ``V4L2_EVENT_EOS`` 事件。
.. note::

      为了向后兼容，编码器会在最后一帧被编码且所有帧都准备好被取出时触发一个 ``V4L2_EVENT_EOS`` 事件。这是一种已弃用的行为，客户端不应依赖于此行为。
      应使用 ``V4L2_BUF_FLAG_LAST`` 缓冲标志。
3. 当所有在 ``V4L2_ENC_CMD_STOP`` 调用之前排队的 ``OUTPUT`` 缓冲区以及最后一个 ``CAPTURE`` 缓冲区都被取出后，编码器将停止，并且不会处理任何新排队的 ``OUTPUT`` 缓冲区，直到客户端执行以下操作之一：

   * 发出 ``V4L2_ENC_CMD_START`` 命令 - 编码器不会重置，并将以停机前的状态继续正常运行，

   * 在 ``CAPTURE`` 队列上执行一对 :c:func:`VIDIOC_STREAMOFF` 和 :c:func:`VIDIOC_STREAMON` 操作 - 编码器会重置（参见 `Reset` 序列），然后恢复编码，

   * 在 ``OUTPUT`` 队列上执行一对 :c:func:`VIDIOC_STREAMOFF` 和 :c:func:`VIDIOC_STREAMON` 操作 - 编码器将恢复正常运行，但在 ``V4L2_ENC_CMD_STOP`` 和 :c:func:`VIDIOC_STREAMOFF` 之间排队的所有源帧将被丢弃。
.. note::

   一旦开始排水序列，客户端需要按上述步骤将其进行到底，除非通过在任一 ``OUTPUT`` 或 ``CAPTURE`` 队列上发出 :c:func:`VIDIOC_STREAMOFF` 来中止此过程。在排水序列进行期间，不允许客户端再次发出 ``V4L2_ENC_CMD_START`` 或 ``V4L2_ENC_CMD_STOP`` 命令，如果尝试这样做将会返回 -EBUSY 错误代码。
作为参考，下面描述了各种特殊情况的处理方法：

   * 如果在发出 ``V4L2_ENC_CMD_STOP`` 命令时 ``OUTPUT`` 队列中没有缓冲区，排水序列将立即完成，并且编码器返回一个带有 ``V4L2_BUF_FLAG_LAST`` 标志的空 ``CAPTURE`` 缓冲区。
   * 如果在排水序列完成时 ``CAPTURE`` 队列中没有缓冲区，则下次客户端排队一个 ``CAPTURE`` 缓冲区时，它将立即作为一个带有 ``V4L2_BUF_FLAG_LAST`` 标志的空缓冲区返回。
   * 如果在排水序列中途调用 :c:func:`VIDIOC_STREAMOFF` 对 ``CAPTURE`` 队列，则排水序列被取消，所有 ``CAPTURE`` 缓冲区将隐式地返回给客户端。
   * 如果在排水序列中途调用 :c:func:`VIDIOC_STREAMOFF` 对 ``OUTPUT`` 队列，则排水序列将立即完成，并且下一个 ``CAPTURE`` 缓冲区将作为带有 ``V4L2_BUF_FLAG_LAST`` 标志的空缓冲区返回。
虽然不是强制性的，但可以使用 :c:func:`VIDIOC_TRY_ENCODER_CMD` 查询编码器命令的可用性。
重置
=====

客户端可能希望请求编码器重新初始化编码，以便后续的流数据与之前的流数据无关。根据编解码格式的不同，这可能意味着：

* 重启后生成的编码帧不应引用任何在停止前生成的帧，例如H.264/HEVC中的长期参考帧，

* 必须在独立流中包含的所有头信息需要再次生成，例如H.264/HEVC中的SPS和PPS。

这可以通过执行以下重置序列来实现：
1. 执行`Drain`序列以确保所有正在进行的编码完成，并相应的缓冲区被出队。
2. 通过调用:c:func:`VIDIOC_STREAMOFF`停止``CAPTURE``队列上的流。这将把当前排队的所有``CAPTURE``缓冲区返回给客户端，但不包含有效的帧数据。
3. 通过调用:c:func:`VIDIOC_STREAMON`启动``CAPTURE``队列上的流，并继续正常的编码序列。从现在开始，在``CAPTURE``缓冲区中生成的编码帧将包含一个可以独立解码的流，无需依赖重置序列之前编码的帧，从发出`V4L2_ENC_CMD_STOP`命令后的第一个``OUTPUT``缓冲区开始。

此序列也可用于那些无法动态更改参数的编码器来更改编码参数。

提交点
=============

设置格式和分配缓冲区会触发编码器行为的变化。
1. 在``CAPTURE``队列上设置格式可能会改变``OUTPUT``队列支持/宣传的格式集。特别是这意味着``OUTPUT``格式可能会被重置，客户端不应依赖于先前设置的格式会被保留。
2. 列举``OUTPUT``队列上的格式总是只返回当前``CAPTURE``格式支持的格式。
3. 在``OUTPUT``队列上设置格式不会改变``CAPTURE``队列可用的格式列表。尝试设置当前选择的``CAPTURE``格式不支持的``OUTPUT``格式将导致编码器调整请求的``OUTPUT``格式为一个支持的格式。
4. 在 ``CAPTURE`` 队列上枚举格式时，始终会返回支持的全部编码格式，无论当前的 ``OUTPUT`` 格式是什么。

5. 当 ``OUTPUT`` 或 ``CAPTURE`` 队列中的任何一个队列分配了缓冲区时，客户端不得更改 ``CAPTURE`` 队列的格式。驱动程序会对任何此类格式更改尝试返回 -EBUSY 错误代码。

总结来说，设置格式和分配缓冲区必须始终从 ``CAPTURE`` 队列开始，并且 ``CAPTURE`` 队列是控制 ``OUTPUT`` 队列支持格式的主控队列。
