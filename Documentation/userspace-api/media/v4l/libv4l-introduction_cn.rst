.. SPDX 许可证标识符: GFDL-1.1-no-invariants-or-later
.. c:命名空间:: V4L

.. _libv4l-introduction:

************
简介
************

libv4l 是一组库，它在 video4linux2 设备之上添加了一层轻量级的抽象层。这个（轻量级）层的目的是让应用程序开发者能够轻松支持多种设备，而无需为同一类别的不同设备编写单独的代码。
一个使用 libv4l 的示例由 :ref:`v4l2grab <v4l2grab-example>` 提供。
libv4l 包含三个不同的库：

libv4lconvert
=============

libv4lconvert 是一个库，可以将 V4L2 驱动程序中发现的多种像素格式转换为几种常见的 RGB 和 YUY 格式。
目前它接受以下 V4L2 驱动格式：
:ref:`V4L2_PIX_FMT_BGR24 <V4L2-PIX-FMT-BGR24>`，
:ref:`V4L2_PIX_FMT_NV12_16L16 <V4L2-PIX-FMT-NV12-16L16>`，
:ref:`V4L2_PIX_FMT_JPEG <V4L2-PIX-FMT-JPEG>`，
:ref:`V4L2_PIX_FMT_MJPEG <V4L2-PIX-FMT-MJPEG>`，
:ref:`V4L2_PIX_FMT_MR97310A <V4L2-PIX-FMT-MR97310A>`，
:ref:`V4L2_PIX_FMT_OV511 <V4L2-PIX-FMT-OV511>`，
:ref:`V4L2_PIX_FMT_OV518 <V4L2-PIX-FMT-OV518>`，
:ref:`V4L2_PIX_FMT_PAC207 <V4L2-PIX-FMT-PAC207>`，
:ref:`V4L2_PIX_FMT_PJPG <V4L2-PIX-FMT-PJPG>`，
:ref:`V4L2_PIX_FMT_RGB24 <V4L2-PIX-FMT-RGB24>`，
:ref:`V4L2_PIX_FMT_SBGGR8 <V4L2-PIX-FMT-SBGGR8>`，
:ref:`V4L2_PIX_FMT_SGBRG8 <V4L2-PIX-FMT-SGBRG8>`，
:ref:`V4L2_PIX_FMT_SGRBG8 <V4L2-PIX-FMT-SGRBG8>`，
:ref:`V4L2_PIX_FMT_SN9C10X <V4L2-PIX-FMT-SN9C10X>`，
:ref:`V4L2_PIX_FMT_SN9C20X_I420 <V4L2-PIX-FMT-SN9C20X-I420>`，
:ref:`V4L2_PIX_FMT_SPCA501 <V4L2-PIX-FMT-SPCA501>`，
:ref:`V4L2_PIX_FMT_SPCA505 <V4L2-PIX-FMT-SPCA505>`，
:ref:`V4L2_PIX_FMT_SPCA508 <V4L2-PIX-FMT-SPCA508>`，
:ref:`V4L2_PIX_FMT_SPCA561 <V4L2-PIX-FMT-SPCA561>`，
:ref:`V4L2_PIX_FMT_SQ905C <V4L2-PIX-FMT-SQ905C>`，
:ref:`V4L2_PIX_FMT_SRGGB8 <V4L2-PIX-FMT-SRGGB8>`，
:ref:`V4L2_PIX_FMT_UYVY <V4L2-PIX-FMT-UYVY>`，
:ref:`V4L2_PIX_FMT_YUV420 <V4L2-PIX-FMT-YUV420>`，
:ref:`V4L2_PIX_FMT_YUYV <V4L2-PIX-FMT-YUYV>`，
:ref:`V4L2_PIX_FMT_YVU420 <V4L2-PIX-FMT-YVU420>`，以及
:ref:`V4L2_PIX_FMT_YVYU <V4L2-PIX-FMT-YVYU>`。

后来，libv4lconvert 扩展了各种视频处理功能以提高网络摄像头视频质量。视频处理分为两部分：libv4lconvert/control 和 libv4lconvert/processing。
控制部分用于提供视频控制功能，这些功能可以用来控制 libv4lconvert/processing 提供的视频处理功能。这些控制通过持久共享内存对象在整个应用范围内存储（直到重启）。
libv4lconvert/processing 提供实际的视频处理功能。

libv4l1
=======

该库提供了可用于使 v4l1 应用程序与 v4l2 设备兼容的功能。这些功能的工作方式与正常的打开/关闭等操作完全相同，只是 libv4l1 在 v4l2 驱动上完全模拟了 v4l1 API；对于 v4l1 驱动，它只会传递调用。
由于这些功能是对旧版 V4L1 API 的模拟，因此不建议在新应用程序中使用。

libv4l2
=======

该库应用于所有现代 V4L2 应用程序。
它提供了调用 V4L2 的 `open`、`ioctl`、`close` 和 `poll` 方法的句柄。与其仅提供设备的原始输出，它通过使用 `libv4lconvert` 来提供更多视频格式并提高图像质量，从而增强了这些调用的功能。

在大多数情况下，`libv4l2` 会直接将调用传递给 v4l2 驱动程序，但在处理以下命令时会拦截它们：
`:ref:`VIDIOC_TRY_FMT <VIDIOC_G_FMT>`，
`:ref:`VIDIOC_G_FMT <VIDIOC_G_FMT>`，
`:ref:`VIDIOC_S_FMT <VIDIOC_G_FMT>`，
`:ref:`VIDIOC_ENUM_FRAMESIZES <VIDIOC_ENUM_FRAMESIZES>` 和
`:ref:`VIDIOC_ENUM_FRAMEINTERVALS <VIDIOC_ENUM_FRAMEINTERVALS>`，
以模拟如果驱动程序中不可用的格式：
`:ref:`V4L2_PIX_FMT_BGR24 <V4L2-PIX-FMT-BGR24>`，
`:ref:`V4L2_PIX_FMT_RGB24 <V4L2-PIX-FMT-RGB24>`，
`:ref:`V4L2_PIX_FMT_YUV420 <V4L2-PIX-FMT-YUV420>`，和
`:ref:`V4L2_PIX_FMT_YVU420 <V4L2-PIX-FMT-YVU420>`。
`:ref:`VIDIOC_ENUM_FMT <VIDIOC_ENUM_FMT>` 仍然枚举硬件支持的格式，并在最后加上 `libv4l` 提供的模拟格式。

.. _libv4l-ops:

Libv4l 设备控制函数
------------------------

常见的文件操作方法由 `libv4l` 提供。这些函数的操作方式类似于 `gcc` 函数 `dup()` 和 V4L2 函数 `open()`、`close()`、`ioctl()`、`read()`、`mmap()` 和 `munmap()`：

.. c:function:: int v4l2_open(const char *file, int oflag, ...)

   操作方式类似于 `c:func::open()` 函数。
.. c:function:: int v4l2_close(int fd)

   操作方式类似于 `c:func::close()` 函数。
.. c:function:: int v4l2_dup(int fd)

   操作方式类似于 `libc` 函数 `dup()`，用于复制文件句柄。
.. c:function:: int v4l2_ioctl (int fd, unsigned long int request, ...)

   操作方式类似于 `c:func::ioctl()` 函数。
.. c:function:: int v4l2_read (int fd, void* buffer, size_t n)

   操作方式类似于 `c:func::read()` 函数。
.. c:function:: void *v4l2_mmap(void *start, size_t length, int prot, int flags, int fd, int64_t offset);

   操作方式类似于 `c:func::mmap()` 函数。
.. c:function:: int v4l2_munmap(void *_start, size_t length);

   操作方式类似于 `c:func::munmap()` 函数。
这些函数提供了额外的控制功能：

.. c:function:: int v4l2_fd_open(int fd, int v4l2_flags)

   为通过 v4l2lib 进一步使用已经打开的文件描述符，并且可能通过 `v4l2_flags` 参数修改 libv4l2 的默认行为。
   目前，`v4l2_flags` 可以设置为 `V4L2_DISABLE_CONVERSION`，以禁用格式转换。

.. c:function:: int v4l2_set_control(int fd, int cid, int value)

   此函数接收一个 0 - 65535 范围内的值，并将其缩放到给定的 v4l 控制 ID 实际范围。如果 cid 存在且未被锁定，则将 cid 设置为缩放后的值。

.. c:function:: int v4l2_get_control(int fd, int cid)

   此函数返回一个 0 - 65535 范围内的值，该值已根据给定的 v4l 控制 ID 实际范围进行缩放。当 cid 不存在、因某种原因无法访问或发生错误时，返回 0。

v4l1compat.so 包装库
=============================

此库拦截对 :c:func:`open()`、:c:func:`close()`、:c:func:`ioctl()`、:c:func:`mmap()` 和 :c:func:`munmap()` 操作的调用，并通过使用 `LD_PRELOAD=/usr/lib/v4l1compat.so` 将它们重定向到 libv4l 的对应函数。它还通过 V4L2 API 模拟 V4L1 调用。
这允许使用仍然没有使用 libv4l 的二进制遗留应用程序。
