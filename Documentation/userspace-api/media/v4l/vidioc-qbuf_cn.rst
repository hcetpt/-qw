SPDX 许可声明标识符: GFDL-1.1-no-invariants-or-later
.. c:namespace:: V4L

.. _VIDIOC_QBUF:

*******************************
ioctl VIDIOC_QBUF, VIDIOC_DQBUF
*******************************

名称
====

VIDIOC_QBUF - VIDIOC_DQBUF - 与驱动程序交换缓冲区

概述
========

.. c:macro:: VIDIOC_QBUF

``int ioctl(int fd, VIDIOC_QBUF, struct v4l2_buffer *argp)``

.. c:macro:: VIDIOC_DQBUF

``int ioctl(int fd, VIDIOC_DQBUF, struct v4l2_buffer *argp)``

参数
=========

``fd``
    由 :c:func:`open()` 返回的文件描述符
``argp``
    指向 struct :c:type:`v4l2_buffer` 的指针
描述
===========

应用程序通过调用 ``VIDIOC_QBUF`` ioctl 将一个空（用于捕获）或已填充（输出）的缓冲区加入到驱动程序的输入队列中。语义取决于所选的I/O方法。

为了将一个缓冲区加入队列，应用程序需要设置 struct :c:type:`v4l2_buffer` 中的 ``type`` 字段为先前在 struct :c:type:`v4l2_format` 的 ``type`` 和 struct :c:type:`v4l2_requestbuffers` 的 ``type`` 中使用的相同的缓冲区类型。应用程序还必须设置 ``index`` 字段。有效的索引号范围是从零到使用 :ref:`VIDIOC_REQBUFS` （struct :c:type:`v4l2_requestbuffers` 的 ``count``）分配的缓冲区数量减一。由 :ref:`VIDIOC_QUERYBUF` ioctl 返回的 struct :c:type:`v4l2_buffer` 内容也可以使用。

当缓冲区用于输出时（``type`` 是 ``V4L2_BUF_TYPE_VIDEO_OUTPUT``、``V4L2_BUF_TYPE_VIDEO_OUTPUT_MPLANE`` 或 ``V4L2_BUF_TYPE_VBI_OUTPUT``），应用程序还必须初始化 ``bytesused``、``field`` 和 ``timestamp`` 字段，详细信息见 :ref:`buffer`。应用程序还必须将 ``flags`` 设置为0。``reserved2`` 和 ``reserved`` 字段也必须设置为0。当使用 :ref:`多平面 API <planar-apis>` 时，``m.planes`` 字段必须包含指向填充好的 struct :c:type:`v4l2_plane` 数组的用户空间指针，并且 ``length`` 字段必须设置为该数组中的元素数量。

为了将一个 :ref:`内存映射 <mmap>` 缓冲区加入队列，应用程序将 ``memory`` 字段设置为 ``V4L2_MEMORY_MMAP``。当调用 ``VIDIOC_QBUF`` 时，如果指向此结构体，驱动程序会设置 ``V4L2_BUF_FLAG_MAPPED`` 和 ``V4L2_BUF_FLAG_QUEUED`` 标志并清除 ``V4L2_BUF_FLAG_DONE`` 标志，或者返回一个 ``EINVAL`` 错误码。

为了将一个 :ref:`用户指针 <userp>` 缓冲区加入队列，应用程序将 ``memory`` 字段设置为 ``V4L2_MEMORY_USERPTR``，``m.userptr`` 字段设置为缓冲区地址，``length`` 设置为其大小。当使用多平面 API 时，传递的 struct :c:type:`v4l2_plane` 数组中的 ``m.userptr`` 和 ``length`` 成员必须被使用。当调用 ``VIDIOC_QBUF`` 时，如果指向此结构体，驱动程序会设置 ``V4L2_BUF_FLAG_QUEUED`` 标志并清除 ``V4L2_BUF_FLAG_MAPPED`` 和 ``V4L2_BUF_FLAG_DONE`` 标志，或者返回一个错误码。此 ioctl 将缓冲区的内存页锁定在物理内存中，它们不能被交换到磁盘。缓冲区保持锁定状态直到被出队列，或者调用 :ref:`VIDIOC_STREAMOFF <VIDIOC_STREAMON>` 或 :ref:`VIDIOC_REQBUFS` ioctl，或者设备关闭。

为了将一个 :ref:`DMABUF <dmabuf>` 缓冲区加入队列，应用程序将 ``memory`` 字段设置为 ``V4L2_MEMORY_DMABUF`` 并且 ``m.fd`` 字段设置为与 DMABUF 缓冲区相关联的文件描述符。当使用多平面 API 时，传递的 struct :c:type:`v4l2_plane` 数组中的 ``m.fd`` 字段必须被使用。当调用 ``VIDIOC_QBUF`` 时，如果指向此结构体，驱动程序会设置 ``V4L2_BUF_FLAG_QUEUED`` 标志并清除 ``V4L2_BUF_FLAG_MAPPED`` 和 ``V4L2_BUF_FLAG_DONE`` 标志，或者返回一个错误码。此 ioctl 将缓冲区锁定。锁定一个缓冲区意味着将其传递给驱动程序以进行硬件访问（通常是DMA）。如果应用程序访问（读/写）一个已锁定的缓冲区，则结果是不确定的。缓冲区保持锁定状态直到被出队列，或者调用 :ref:`VIDIOC_STREAMOFF <VIDIOC_STREAMON>` 或 :ref:`VIDIOC_REQBUFS` ioctl，或者设备关闭。
``request_fd`` 字段可以与 ``VIDIOC_QBUF`` ioctl 一起使用，指定一个请求 (:ref:`media-request-api`) 的文件描述符，如果启用了请求的话。设置它意味着缓冲区不会在请求本身入队之前传递给驱动程序。此外，驱动程序将应用与此缓冲区相关的任何请求设置。除非设置了 ``V4L2_BUF_FLAG_REQUEST_FD`` 标志，否则此字段将被忽略。如果设备不支持请求，则会返回 ``EBADR``。如果支持请求但提供了无效的请求文件描述符，则会返回 ``EINVAL``。

.. 注意::
   不允许混合使用请求队列和直接队列缓冲区。
   如果第一个缓冲区是直接入队的，然后应用程序尝试入队一个请求，或者反过来，将会返回 ``EBUSY``。关闭文件描述符、调用 :ref:`VIDIOC_STREAMOFF <VIDIOC_STREAMON>` 或调用 :ref:`VIDIOC_REQBUFS` 后，该检查会被重置。

对于 :ref:`memory-to-memory devices <mem2mem>`，您只能为输出缓冲区指定 ``request_fd``，而不能为捕获缓冲区指定。尝试为捕获缓冲区指定此值将导致 ``EBADR`` 错误。

应用程序调用 ``VIDIOC_DQBUF`` ioctl 从驱动程序的出队列中出队已填充（捕获）或显示（输出）的缓冲区。它们只需设置结构体 :c:type:`v4l2_buffer` 中的 ``type``、``memory`` 和 ``reserved`` 字段，当使用指向该结构体的指针调用 ``VIDIOC_DQBUF`` 时，驱动程序将填充所有剩余字段或返回错误代码。驱动程序还可以在 ``flags`` 字段中设置 ``V4L2_BUF_FLAG_ERROR``。这表示一个非关键（可恢复的）流错误。在这种情况下，应用程序可以继续正常工作，但应注意出队缓冲区中的数据可能已被破坏。使用多平面 API 时，必须同时传递平面数组。

如果应用程序将 ``memory`` 字段设置为 ``V4L2_MEMORY_DMABUF`` 以出队一个 :ref:`DMABUF <dmabuf>` 缓冲区，驱动程序会在 ``m.fd`` 字段中填充与入队时提供给 ``VIDIOC_QBUF`` 的文件描述符数值相同的值。在出队时不会创建新的文件描述符，该值仅用于应用程序方便。使用多平面 API 时，传递的结构体数组 :c:type:`v4l2_plane` 的 ``m.fd`` 字段会被填充。

默认情况下，如果没有缓冲区在出队列中，``VIDIOC_DQBUF`` 会阻塞。如果在调用 :c:func:`open()` 函数时提供了 ``O_NONBLOCK`` 标志，则在没有可用缓冲区时 ``VIDIOC_DQBUF`` 会立即返回带有 ``EAGAIN`` 错误代码的结果。

结构体 :c:type:`v4l2_buffer` 在 :ref:`buffer` 中定义。
返回值
============

成功时返回0，错误时返回-1，并且设置 ``errno`` 变量为适当的值。通用错误代码在《<ref>通用错误代码<gen-errors></ref>》章节中描述。

EAGAIN
    使用 `O_NONBLOCK` 启用了非阻塞I/O，并且出站队列中没有缓冲区。
EINVAL
    缓冲区的 `type` 不被支持，或者 `index` 越界，或者尚未分配任何缓冲区，或者 `userptr` 或 `length` 无效，或者设置了 `V4L2_BUF_FLAG_REQUEST_FD` 标志但给定的 `request_fd` 无效，或者 `m.fd` 是一个无效的 DMABUF 文件描述符。
EIO
    `VIDIOC_DQBUF` 因内部错误失败。也可能表示临时问题，例如信号丢失。
.. note::

       驱动程序可能会在返回错误的情况下从队列中移除一个（空）缓冲区，甚至停止捕获。但是，重用这样的缓冲区可能是不安全的，并且其详细信息（如 `index`）也可能不会返回。
建议驱动程序通过设置 `V4L2_BUF_FLAG_ERROR` 并返回0来指示可恢复的错误。在这种情况下，应用程序应该能够安全地重用缓冲区并继续流传输。
EPIPE
    对于 mem2mem 编码器，如果捕获队列为空，并且已经移除了带有 `V4L2_BUF_FLAG_LAST` 标志的缓冲区，并且不期望有新的缓冲区可用，则 `VIDIOC_DQBUF` 返回此错误。
EBADR
    设置了 `V4L2_BUF_FLAG_REQUEST_FD` 标志，但设备不支持给定缓冲区类型的请求，或者未设置 `V4L2_BUF_FLAG_REQUEST_FD` 标志，但设备要求缓冲区必须是请求的一部分。
EBUSY
    第一个缓冲区通过请求排队，但现在应用程序试图直接排队，反之亦然（不允许混合使用这两种API）。
