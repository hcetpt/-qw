SPDX 许可声明标识符: GFDL-1.1-no-invariants-or-later
.. c:namespace:: V4L

.. _capture:

**************************
视频捕获接口
**************************

视频捕获设备对模拟视频信号进行采样，并将数字化的图像存储在内存中。如今，几乎所有设备都可以以每秒25或30帧的速度进行全帧捕获。通过这个接口，应用程序可以控制捕获过程，并将图像从驱动程序传输到用户空间。通常，V4L2 视频捕获设备通过名为 `/dev/video` 和 `/dev/video0` 到 `/dev/video63` 的字符设备特殊文件访问，主设备号为81，次设备号为0到63。`/dev/video` 通常是到首选视频设备的符号链接。
.. 注意:: 相同的设备文件名也用于视频输出设备
查询能力
=====================

支持视频捕获接口的设备会在通过 `VIDIOC_QUERYCAP` ioctl 返回的 `v4l2_capability` 结构体的 `capabilities` 字段中设置 `V4L2_CAP_VIDEO_CAPTURE` 或 `V4L2_CAP_VIDEO_CAPTURE_MPLANE` 标志。作为次要设备功能，它们还可能支持视频覆盖 (`V4L2_CAP_VIDEO_OVERLAY`) 和原始垂直消隐间隔 (VBI) 捕获 (`V4L2_CAP_VBI_CAPTURE`) 接口。至少需要支持读写或流式输入/输出方法之一。调谐器和音频输入是可选的。
补充功能
======================

视频捕获设备应按需支持音频输入、调谐器、控制、裁剪与缩放以及流式参数等 ioctl。所有视频捕获设备必须支持视频输入 ioctl。
图像格式协商
========================

捕获操作的结果由裁剪和图像格式参数决定。前者选择要捕获的视频画面区域，后者则定义了图像如何存储在内存中，例如RGB或YUV格式、每个像素的位数或宽度和高度。这些参数共同决定了图像在捕获过程中如何被缩放。
通常，这些参数在打开设备时（即 `open()` 时）不会重置，以便允许Unix工具链像处理普通文件一样编程和读取设备。编写良好的 V4L2 应用程序会确保它们确实得到了想要的结果，包括裁剪和缩放。
裁剪初始化至少要求将参数重置为默认值。具体示例见裁剪部分。
为了查询当前的图像格式，应用程序需要将 `v4l2_format` 结构体中的 `type` 字段设置为 `V4L2_BUF_TYPE_VIDEO_CAPTURE` 或 `V4L2_BUF_TYPE_VIDEO_CAPTURE_MPLANE`，然后通过指向该结构体的指针调用 `VIDIOC_G_FMT` ioctl。驱动程序会填充 `fmt` 联合体中的 `v4l2_pix_format` 结构体的 `pix` 成员或 `v4l2_pix_format_mplane` 结构体的 `pix_mp` 成员。
为了请求不同的参数应用，请设置 `struct` 类型的 `v4l2_format` 的 `type` 字段，如上所述，并初始化 `struct` 类型的 `v4l2_pix_format` 中 `vbi` 成员的所有字段，或者更好的做法是修改 `VIDIOC_G_FMT` 的结果，并使用指向该结构体的指针调用 `VIDIOC_S_FMT` ioctl。驱动程序可能会调整这些参数，并最终返回实际参数，就像 `VIDIOC_G_FMT` 所做的那样。

与 `VIDIOC_S_FMT` 类似，`VIDIOC_TRY_FMT` ioctl 可以用于了解硬件限制，而无需禁用 I/O 或进行可能耗时的硬件准备。

关于 `struct v4l2_pix_format` 和 `struct v4l2_pix_format_mplane` 的内容，请参见 :ref:`pixfmt`。有关详细信息，请参阅 `VIDIOC_G_FMT`、`VIDIOC_S_FMT` 和 `VIDIOC_TRY_FMT` ioctl 的规范。视频捕获设备必须实现 `VIDIOC_G_FMT` 和 `VIDIOC_S_FMT` ioctl，即使 `VIDIOC_S_FMT` 忽略所有请求并始终返回默认参数，就像 `VIDIOC_G_FMT` 所做的那样。`VIDIOC_TRY_FMT` 是可选的。

读取图像
=========

视频捕获设备可能支持 `read()` 函数和/或流式 I/O（内存映射或用户指针）。具体细节请参见 :ref:`io`。
