SPDX 许可声明标识符: GFDL-1.1-no-invariants-or-later
.. c:namespace:: V4L

.. _dmabuf:

************************************
流式 I/O（DMA 缓冲区导入）
************************************

DMABUF 框架提供了一种通用的方法，用于在多个设备之间共享缓冲区。支持 DMABUF 的设备驱动程序可以将 DMA 缓冲区导出到用户空间作为一个文件描述符（称为导出角色），使用之前为其他或同一设备导出的文件描述符从用户空间导入 DMA 缓冲区（称为导入角色），或者两者皆可。本节描述了 V4L2 中的 DMABUF 导入角色 API。有关将 V4L2 缓冲区导出为 DMABUF 文件描述符的详细信息，请参阅 :ref:`VIDIOC_EXPBUF`。
输入和输出设备支持流式 I/O 方法时，通过设置由 :ref:`VIDIOC_QUERYCAP <VIDIOC_QUERYCAP>` ioctl 返回的 :c:type:`v4l2_capability` 结构体中 `capabilities` 字段中的 `V4L2_CAP_STREAMING` 标志来实现。是否支持通过 DMABUF 文件描述符导入 DMA 缓冲区是通过调用带有 `V4L2_MEMORY_DMABUF` 内存类型的 :ref:`VIDIOC_REQBUFS <VIDIOC_REQBUFS>` ioctl 来确定的。
此 I/O 方法专门用于在不同设备之间共享 DMA 缓冲区，这些设备可能是 V4L 设备或其他视频相关设备（例如 DRM）。缓冲区（平面）由代表应用程序的一个驱动程序分配。然后，这些缓冲区通过特定于分配器驱动程序的 API 作为文件描述符导出给应用程序。仅交换这样的文件描述符。描述符及其元信息传递给 :c:type:`v4l2_buffer` 结构体（或者在多平面 API 情况下传递给 :c:type:`v4l2_plane` 结构体）。驱动程序必须通过调用 :ref:`VIDIOC_REQBUFS <VIDIOC_REQBUFS>` 并指定所需的缓冲区类型来切换到 DMABUF I/O 模式。

示例：使用 DMABUF 文件描述符启动流式 I/O
==============================================================

.. code-block:: c

    struct v4l2_requestbuffers reqbuf;

    memset(&reqbuf, 0, sizeof(reqbuf));
    reqbuf.type = V4L2_BUF_TYPE_VIDEO_CAPTURE;
    reqbuf.memory = V4L2_MEMORY_DMABUF;
    reqbuf.count = 1;

    if (ioctl(fd, VIDIOC_REQBUFS, &reqbuf) == -1) {
        if (errno == EINVAL)
            printf("不支持视频捕获或 DMABUF 流式传输\n");
        else
            perror("VIDIOC_REQBUFS");

        exit(EXIT_FAILURE);
    }

缓冲区（平面）文件描述符通过 :ref:`VIDIOC_QBUF <VIDIOC_QBUF>` ioctl 在运行时传递。在多平面缓冲区的情况下，每个平面都可以关联不同的 DMABUF 描述符。尽管缓冲区通常会被循环使用，但在每次 :ref:`VIDIOC_QBUF <VIDIOC_QBUF>` 调用时，应用程序可以传递不同的 DMABUF 描述符。

示例：使用单平面 API 排队 DMABUF
===============================================

.. code-block:: c

    int buffer_queue(int v4lfd, int index, int dmafd)
    {
        struct v4l2_buffer buf;

        memset(&buf, 0, sizeof(buf));
        buf.type = V4L2_BUF_TYPE_VIDEO_CAPTURE;
        buf.memory = V4L2_MEMORY_DMABUF;
        buf.index = index;
        buf.m.fd = dmafd;

        if (ioctl(v4lfd, VIDIOC_QBUF, &buf) == -1) {
            perror("VIDIOC_QBUF");
            return -1;
        }

        return 0;
    }

示例 3.6：使用多平面 API 排队 DMABUF
==================================================

.. code-block:: c

    int buffer_queue_mp(int v4lfd, int index, int dmafd[], int n_planes)
    {
        struct v4l2_buffer buf;
        struct v4l2_plane planes[VIDEO_MAX_PLANES];
        int i;

        memset(&buf, 0, sizeof(buf));
        buf.type = V4L2_BUF_TYPE_VIDEO_CAPTURE_MPLANE;
        buf.memory = V4L2_MEMORY_DMABUF;
        buf.index = index;
        buf.m.planes = planes;
        buf.length = n_planes;

        memset(&planes, 0, sizeof(planes));

        for (i = 0; i < n_planes; ++i)
            buf.m.planes[i].m.fd = dmafd[i];

        if (ioctl(v4lfd, VIDIOC_QBUF, &buf) == -1) {
            perror("VIDIOC_QBUF");
            return -1;
        }

        return 0;
    }

被捕获或显示的缓冲区通过 :ref:`VIDIOC_DQBUF <VIDIOC_QBUF>` ioctl 从队列中移除。在 DMA 完成和此 ioctl 调用之间，驱动程序可以随时解锁缓冲区。当调用 :ref:`VIDIOC_STREAMOFF <VIDIOC_STREAMON>`、:ref:`VIDIOC_REQBUFS <VIDIOC_REQBUFS>` 或关闭设备时，内存也会被解锁。
对于捕获应用程序来说，通常会排队一些空缓冲区以开始捕获并进入读取循环。在此，应用程序等待直到一个已填充的缓冲区可以从队列中移除，并在数据不再需要时重新排队该缓冲区。输出应用程序则填充并排队缓冲区，当足够多的缓冲区堆积起来时便开始输出。在写入循环中，当应用程序缺少空缓冲区时，它必须等待直到可以移除一个空缓冲区并重复使用。
有两种方法可以让应用程序暂停执行，直到可以移除一个或多个缓冲区。默认情况下，当队列中没有缓冲区时 :ref:`VIDIOC_DQBUF <VIDIOC_QBUF>` 会阻塞。如果 :c:func:`open()` 函数指定了 `O_NONBLOCK` 标志，则在没有可用缓冲区时 :ref:`VIDIOC_DQBUF <VIDIOC_QBUF>` 立即返回 `EAGAIN` 错误代码。:c:func:`select()` 和 :c:func:`poll()` 函数始终可用。
要开始和停止捕获或显示应用程序，请调用 :ref:`VIDIOC_STREAMON <VIDIOC_STREAMON>` 和 :ref:`VIDIOC_STREAMOFF <VIDIOC_STREAMON>` ioctl。
.. note::

   :ref:`VIDIOC_STREAMOFF <VIDIOC_STREAMON>` 会从两个队列中移除所有缓冲区，并作为副作用解锁所有缓冲区。由于在多任务系统中没有“立即”执行的概念，如果应用程序需要与另一个事件同步，应该检查结构体 :c:type:`v4l2_buffer` 中的 ``timestamp`` 字段，以获取捕获或输出的缓冲区的时间戳。

实现 DMABUF 导入 I/O 的驱动程序必须支持以下 ioctl 操作：:ref:`VIDIOC_REQBUFS <VIDIOC_REQBUFS>`、:ref:`VIDIOC_QBUF <VIDIOC_QBUF>`、:ref:`VIDIOC_DQBUF <VIDIOC_QBUF>`、:ref:`VIDIOC_STREAMON <VIDIOC_STREAMON>` 和 :ref:`VIDIOC_STREAMOFF <VIDIOC_STREAMON>`，以及 :c:func:`select()` 和 :c:func:`poll()` 函数。
