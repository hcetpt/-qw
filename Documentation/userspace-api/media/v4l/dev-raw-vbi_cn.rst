SPDX 许可声明标识符: GFDL-1.1-no-invariants-or-later
.. c:namespace:: V4L

.. _raw-vbi:

**************************
原始 VBI 数据接口
**************************

VBI 是垂直消隐间隔 (Vertical Blanking Interval) 的缩写，它是模拟视频信号中的一段线序列中的间隙。在 VBI 期间不传输图像信息，这允许电子束返回到阴极射线管电视屏幕顶部所需的时间。使用示波器，您会在这里发现垂直同步脉冲和调制到视频信号上的短数据包的幅度键控（ASK）[#f1]_。这些是诸如字幕或隐藏字幕等服务的传输。

此接口类型的主题是原始 VBI 数据，即从视频信号采样获得的数据或将要添加到输出信号中的数据。数据格式类似于未压缩的视频图像，即多行乘以每行的样本数，我们称之为 VBI 图像。
按照惯例，V4L2 VBI 设备通过名为 `/dev/vbi` 和 `/dev/vbi0` 到 `/dev/vbi31` 的字符设备特殊文件访问，主设备号为 81，次设备号为 224 到 255。`/dev/vbi` 通常是首选 VBI 设备的符号链接。这一约定适用于输入和输出设备。

为了解决查找相关视频和 VBI 设备的问题，VBI 捕获和输出也可以作为 `/dev/video` 下的功能提供。应用程序必须调用 :ref:`VIDIOC_S_FMT <VIDIOC_G_FMT>` ioctl 来捕获或输出原始 VBI 数据。
当作为 `/dev/vbi` 访问时，默认设备功能是原始 VBI 捕获或输出。

查询能力
==================

支持原始 VBI 捕获或输出 API 的设备会在由 :ref:`VIDIOC_QUERYCAP` ioctl 返回的 `v4l2_capability` 结构的 `capabilities` 字段中设置 `V4L2_CAP_VBI_CAPTURE` 或 `V4L2_CAP_VBI_OUTPUT` 标志。至少需要支持读写或流式 I/O 方法之一。VBI 设备可能有也可能没有调谐器或调制器。

辅助功能
==================

VBI 设备应根据需要支持 :ref:`视频输入或输出 <video>`、:ref:`调谐器或调制器 <tuner>` 和 :ref:`控制 <control>` ioctl。:ref:`视频标准 <standard>` ioctl 提供了编程 VBI 设备所需的关键信息，因此必须支持。

原始 VBI 格式协商
==================

原始 VBI 采样能力可能会有所不同，特别是采样频率。为了正确解释数据，V4L2 规定了一个 ioctl 用于查询采样参数。此外，为了允许某些灵活性，应用程序也可以建议不同的参数。
通常，这些参数不会在调用 `open()` 时重置，以便 Unix 工具链可以将设备编程并像普通文件一样读取它。良好的 V4L2 应用程序应始终确保它们确实得到了想要的结果，请求合理的参数，并检查实际参数是否合适。
要查询当前的原始 VBI 捕获参数，应用程序将 `v4l2_format` 结构的 `type` 字段设置为 `V4L2_BUF_TYPE_VBI_CAPTURE` 或 `V4L2_BUF_TYPE_VBI_OUTPUT`，并通过指向该结构的指针调用 :ref:`VIDIOC_G_FMT <VIDIOC_G_FMT>` ioctl。驱动程序填充 `v4l2_vbi_format` 结构的 `fmt` 联合中的 `vbi` 成员。
为了请求不同的参数设置，请将 `struct` 类型的 `v4l2_format` 的 `type` 字段设置为相应的值，并初始化 `struct` 类型的 `v4l2_vbi_format` 中 `fmt` 联合体的 `vbi` 成员的所有字段，或者更好地是修改 `VIDIOC_G_FMT` 的结果，并使用指向该结构的指针调用 `VIDIOC_S_FMT` ioctl。驱动程序仅在给定的参数存在歧义时返回 `EINVAL` 错误代码，否则它们会根据硬件能力调整参数并返回实际参数。当驱动程序在这个阶段分配资源时，它可能会返回 `EBUSY` 错误代码以表示返回的参数有效但所需的资源当前不可用。例如，当视频和 VBI 区域重叠，或驱动程序支持多个打开并且另一个进程已经请求 VBI 捕获或输出时，就可能发生这种情况。无论如何，应用程序必须预期其他资源分配点可能返回 `EBUSY`，例如在 `VIDIOC_STREAMON` ioctl 和第一次 `read()`、`write()` 和 `select()` 调用中。

VBI 设备必须实现 `VIDIOC_G_FMT` 和 `VIDIOC_S_FMT` ioctl，即使 `VIDIOC_S_FMT` 忽略所有请求并始终像 `VIDIOC_G_FMT` 那样返回默认参数。`VIDIOC_TRY_FMT` 是可选的。

.. tabularcolumns:: |p{1.6cm}|p{4.2cm}|p{11.5cm}|

.. c:type:: v4l2_vbi_format

.. cssclass:: longtable

.. flat-table:: struct v4l2_vbi_format
    :header-rows:  0
    :stub-columns: 0
    :widths:       1 1 2

    * - __u32
      - ``sampling_rate``
      - 每秒采样数，即单位为 1 Hz。
    * - __u32
      - ``offset``
      - VBI 图像相对于行同步脉冲前沿的水平偏移量，以采样计数：VBI 图像中的第一个采样将在前沿之后 `offset` / `sampling_rate` 秒处。参见 :ref:`vbi-hsync`。
    * - __u32
      - ``samples_per_line``
      - 
    * - __u32
      - ``sample_format``
      - 定义采样格式，类似于 :ref:`pixfmt` 的四字符码。[#f2]_ 通常这是 `V4L2_PIX_FMT_GREY`，即每个采样包含 8 位，较低值朝向黑色电平。不要假设值与信号电平之间有任何其他相关性。例如，MSB 并不一定指示信号是“高”还是“低”，因为 128 可能不是信号的中间值。驱动程序不应通过软件转换采样格式。
    * - __u32
      - ``start``\ [#f2]_
      - 这是与 VBI 图像第一行相关的扫描系统行号，分别对应于第一场和第二场。参见 :ref:`vbi-525` 和 :ref:`vbi-625` 以获取有效的值。`V4L2_VBI_ITU_525_F1_START`、`V4L2_VBI_ITU_525_F2_START`、`V4L2_VBI_ITU_625_F1_START` 和 `V4L2_VBI_ITU_625_F2_START` 定义了每种 525 或 625 行格式每一场的起始行号作为便利。
不要忘记 ITU 行编号从 1 开始，而不是从 0 开始。如果硬件无法可靠识别扫描线，VBI 输入驱动程序可以返回起始值 0；VBI 获取可能不需要此信息。
    * - __u32
      - ``count``\ [#f2]_
      - 第一场和第二场图像的行数。
    * - :cspan:`2`

        驱动程序应尽可能灵活。例如，可能扩展或移动 VBI 捕获窗口到图片区域，实现“全场模式”以捕获嵌入在图片中的数据服务传输。
一个应用程序可以将第一个或第二个 `count` 值设置为零，如果不需要从相应字段获取数据；`count`\[1\] 如果扫描系统是逐行的（即非交错的）。相应的起始值应被应用程序和驱动程序忽略。无论如何，驱动程序可能不支持单场捕获，并且返回两个非零的 `count` 值。

两个 `count` 值都设置为零，或者行号超出所示范围\ [#f4]_，或者一个场图像覆盖了两个场的行，这些都是无效的，并且不应由驱动程序返回。

为了初始化 `start` 和 `count` 字段，应用程序必须首先确定当前选择的视频标准。可以评估 :ref:`v4l2_std_id <v4l2-std-id>` 或者 struct :c:type:`v4l2_standard` 的 `framelines` 字段来实现此目的。

* - __u32
      - `flags`
      - 参见下面的 :ref:`vbifmt-flags`。目前只有驱动程序设置标志，应用程序必须将此字段设置为零。
* - __u32
      - `reserved`\ [#f2]_
      - 此数组保留用于未来的扩展。驱动程序和应用程序必须将其设置为零。

.. tabularcolumns:: |p{4.4cm}|p{1.5cm}|p{11.4cm}|

.. _vbifmt-flags:

.. flat-table:: 原始 VBI 格式标志
    :header-rows:  0
    :stub-columns: 0
    :widths:       3 1 4

    * - `V4L2_VBI_UNSYNC`
      - 0x0001
      - 此标志表示硬件无法正确区分场。通常 VBI 图像在内存中先存储第一场（较低的扫描行号）。这可能是顶部场或底部场，取决于视频标准。当此标志被设置时，第一场或第二场可能会先存储，但场仍然按正确的顺序排列，较旧的场先存储在内存中。\[#f3]_
    * - `V4L2_VBI_INTERLACED`
      - 0x0002
      - 默认情况下，两个场图像将顺序传递；首先是第一场的所有行，然后是第二场的所有行（参见 :ref:`field-order` `V4L2_FIELD_SEQ_TB` 和 `V4L2_FIELD_SEQ_BT`，顶部场或底部场先存储在内存中取决于视频标准）。当此标志被设置时，两个场是交错的（参见 `V4L2_FIELD_INTERLACED`）。首先是第一场的第一行，接着是第二场的第一行，然后是两场的第二行，依此类推。当硬件被编程为捕获或输出交错视频图像，并且无法同时分离场进行 VBI 捕获时，这种布局可能是必要的。为了简化，设置此标志意味着两个 `count` 值相等且非零。

.. _vbi-hsync:

.. kernel-figure:: vbi_hsync.svg
    :alt:   vbi_hsync.svg
    :align: center

    **图 4.1. 行同步**

.. _vbi-525:

.. kernel-figure:: vbi_525.svg
    :alt:   vbi_525.svg
    :align: center

    **图 4.2. ITU-R 525 行编号（M/NTSC 和 M/PAL）**

.. _vbi-625:

.. kernel-figure:: vbi_625.svg
    :alt:   vbi_625.svg
    :align: center

    **图 4.3. ITU-R 625 行编号**

请记住，VBI 图像格式取决于所选的视频标准，因此应用程序必须首先选择一个新的标准或查询当前的标准。尝试在格式协商之前或在切换视频标准之后读取或写入数据（这可能会使协商的 VBI 参数无效），应被驱动程序拒绝。在活动 I/O 期间更改格式是不允许的。

读取和写入 VBI 图像
============================

为了保证与场号同步并便于实现，每次传递的最小数据单元是一帧，包含两个紧接着存储在内存中的 VBI 图像场。

一帧的总大小计算如下：

.. code-block:: c

    (count[0] + count[1]) * samples_per_line * 样本大小（字节）

样本大小很可能总是为一个字节，但应用程序必须检查 `sample_format` 字段以确保与其他驱动程序正常工作。

VBI 设备可能支持 :ref:`读/写 <rw>` 和/或流式传输 (:ref:`内存映射 <mmap>` 或 :ref:`用户指针 <userp>`) I/O。
后者通过使用缓冲区时间戳来同步视频和垂直空白间隔（VBI）数据成为可能。

记得 `VIDIOC_STREAMON <VIDIOC_STREAMON>` ioctl 以及第一个 `read()`、`write()` 和 `select()` 函数调用可以作为资源分配点。如果所需的硬件资源暂时不可用（例如设备已被另一个进程占用），这些调用可能会返回一个 `EBUSY` 错误码。

.. [#f1]
   ASK：幅度键控（Amplitude-Shift Keying）。高信号电平表示 '1' 比特，低信号电平表示 '0' 比特。

.. [#f2]
   一些设备可能无法采样 VBI 数据，但可以将视频捕获窗口扩展到 VBI 区域。

.. [#f3]
   大多数 VBI 服务在两个场中都进行传输，但有些服务根据场号有不同的语义。当设置 `V4L2_VBI_UNSYNC` 时，这些服务无法可靠地解码或编码。

.. [#f4]
   合法的值在 :ref:`vbi-525` 和 :ref:`vbi-625` 中给出。
