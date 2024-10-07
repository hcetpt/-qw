SPDX 许可声明标识符: GFDL-1.1-no-invariants-or-later
C 命名空间:: V4L

.. _output:

**********************
视频输出接口
**********************

视频输出设备将静态图像或图像序列编码为模拟视频信号。通过此接口，应用程序可以控制编码过程，并将图像从用户空间传输到驱动程序。传统上，V4L2 视频输出设备通过名为 `/dev/video` 和 `/dev/video0` 到 `/dev/video63` 的字符设备特殊文件访问，主设备号为 81，次设备号为 0 至 63。`/dev/video` 通常是一个指向首选视频设备的符号链接。
.. 注意:: 同样的设备文件名称也用于视频捕获设备
查询功能
=====================

支持视频输出接口的设备会在由 `VIDIOC_QUERYCAP` ioctl 返回的 `v4l2_capability` 结构体（:c:type:`v4l2_capability`）中的 `capabilities` 字段设置 `V4L2_CAP_VIDEO_OUTPUT` 或 `V4L2_CAP_VIDEO_OUTPUT_MPLANE` 标志。作为次要设备功能，它们还可以支持原始垂直消隐（VBI）输出 (`V4L2_CAP_VBI_OUTPUT`) 接口。必须至少支持读/写或流式 I/O 方法之一。调制器和音频输出是可选的。
补充功能
======================

视频输出设备应根据需要支持音频输出 (:ref:`audio`)、调制器 (:ref:`tuner`)、控制 (:ref:`control`)、裁剪和缩放 (:ref:`crop`) 以及流参数 (:ref:`streaming-par`) 的 ioctl。所有视频输出设备都必须支持视频输出 (:ref:`video`) 的 ioctl。
图像格式协商
========================

输出由裁剪和图像格式参数决定。前者选择视频画面中图像出现的区域，后者定义图像在内存中的存储方式，即 RGB 或 YUV 格式、每像素位数或宽度和高度。它们共同决定了图像在处理过程中的缩放方式。
如常，这些参数在调用 `open()` 时 *不会* 重置，以允许 Unix 工具链，先编程设备然后像普通文件一样写入。良好的 V4L2 应用程序确保它们确实得到了所期望的结果，包括裁剪和缩放。
裁剪初始化至少需要将参数重置为默认值。具体示例见 :ref:`crop`。
要查询当前图像格式，应用程序需将一个 `v4l2_format` 结构体（:c:type:`v4l2_format`）的 `type` 字段设置为 `V4L2_BUF_TYPE_VIDEO_OUTPUT` 或 `V4L2_BUF_TYPE_VIDEO_OUTPUT_MPLANE`，并使用指向该结构体的指针调用 `VIDIOC_G_FMT <VIDIOC_G_FMT>` ioctl。驱动程序会填充 `fmt` 联合中的 `v4l2_pix_format` “pix” 或 `v4l2_pix_format_mplane` “pix_mp” 成员。
为了请求不同的参数设置，请将 `struct` 类型的 `v4l2_format` 中的 ``type`` 字段设置为上述值，并初始化 `struct` 类型的 `v4l2_pix_format` 中的 ``vbi`` 成员（位于 ``fmt`` 联合体中），或者更好的做法是修改 :ref:`VIDIOC_G_FMT <VIDIOC_G_FMT>` 的结果，然后使用指向该结构体的指针调用 :ref:`VIDIOC_S_FMT <VIDIOC_G_FMT>` ioctl。驱动程序可能会调整这些参数，并最终像 :ref:`VIDIOC_G_FMT <VIDIOC_G_FMT>` 一样返回实际参数。

与 :ref:`VIDIOC_S_FMT <VIDIOC_G_FMT>` 类似，:ref:`VIDIOC_TRY_FMT <VIDIOC_G_FMT>` ioctl 可以用来了解硬件限制，而无需禁用 I/O 或可能耗时的硬件准备。

关于 `struct` 类型的 `v4l2_pix_format` 和 `v4l2_pix_format_mplane` 的内容在 :ref:`pixfmt` 中有详细讨论。详见 :ref:`VIDIOC_G_FMT <VIDIOC_G_FMT>`、:ref:`VIDIOC_S_FMT <VIDIOC_G_FMT>` 和 :ref:`VIDIOC_TRY_FMT <VIDIOC_G_FMT>` ioctl 的规范以获取更多细节。视频输出设备必须实现 :ref:`VIDIOC_G_FMT <VIDIOC_G_FMT>` 和 :ref:`VIDIOC_S_FMT <VIDIOC_G_FMT>` ioctl，即使 :ref:`VIDIOC_S_FMT <VIDIOC_G_FMT>` 忽略所有请求并始终返回默认参数（如同 :ref:`VIDIOC_G_FMT <VIDIOC_G_FMT>` 所做的一样）。:ref:`VIDIOC_TRY_FMT <VIDIOC_G_FMT>` 是可选的。

### 写入图像

视频输出设备可能支持 :ref:`write() 函数 <rw>` 和/或流式传输（:ref:`内存映射 <mmap>` 或 :ref:`用户指针 <userp>`）I/O。具体细节请参见 :ref:`io`。
