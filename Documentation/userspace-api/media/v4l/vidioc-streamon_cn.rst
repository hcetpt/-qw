.. SPDX-License-Identifier: GFDL-1.1-no-invariants-or-later
.. c:namespace:: V4L

.. _VIDIOC_STREAMON:

***************************************
ioctl VIDIOC_STREAMON, VIDIOC_STREAMOFF
***************************************

名称
====

VIDIOC_STREAMON - VIDIOC_STREAMOFF - 启动或停止流式I/O

概要
====

.. c:macro:: VIDIOC_STREAMON

``int ioctl(int fd, VIDIOC_STREAMON, const int *argp)``

.. c:macro:: VIDIOC_STREAMOFF

``int ioctl(int fd, VIDIOC_STREAMOFF, const int *argp)``

参数
====

``fd``
    由 :c:func:`open()` 返回的文件描述符
``argp``
    指向一个整数的指针

描述
====

``VIDIOC_STREAMON`` 和 ``VIDIOC_STREAMOFF`` ioctl 分别用于启动和停止流式传输过程中的捕获或输出（例如，内存映射 `<mmap>`_，用户指针 `<userp>`_ 或直接内存访问缓冲区 `<dmabuf>`_）。
在调用 ``VIDIOC_STREAMON`` 之前，捕获硬件处于禁用状态，并且不会填充输入缓冲区（如果有空闲缓冲区在队列中）。同样，在调用 ``VIDIOC_STREAMON`` 之前，输出硬件也处于禁用状态，并且不会生成视频信号。
对于内存到内存设备，需要在捕获和输出流类型上都调用 ``VIDIOC_STREAMON`` 才会开始工作。
如果 ``VIDIOC_STREAMON`` 失败，则任何已经排队的缓冲区仍将保持排队状态。
``VIDIOC_STREAMOFF`` ioctl 不仅会终止或完成任何正在进行的DMA操作，还会解锁所有锁定在物理内存中的用户指针缓冲区，并从输入和输出队列中移除所有缓冲区。这意味着所有已捕获但尚未出队的图像将丢失，同样，所有已入队但尚未传输的输出图像也会丢失。I/O 将回到调用 :ref:`VIDIOC_REQBUFS` 之后的状态，并可以相应地重新启动。
如果使用 :ref:`VIDIOC_QBUF` 队列化了缓冲区，并且在从未调用过 ``VIDIOC_STREAMON`` 的情况下调用了 ``VIDIOC_STREAMOFF``，那么这些已排队的缓冲区也将从输入队列中移除，并全部返回到调用 :ref:`VIDIOC_REQBUFS` 之后的状态，并可以相应地重新启动。
这两个 ioctl 均接受一个指向整数的指针，该整数表示所需的缓冲区或流类型。这与结构 :c:type:`v4l2_requestbuffers` 中的 `type` 字段相同。
如果在流式传输已经进行时调用 ``VIDIOC_STREAMON``，或者在流式传输已经停止时调用 ``VIDIOC_STREAMOFF``，则返回 0。在这种情况下，``VIDIOC_STREAMON`` 不会发生任何操作，而 ``VIDIOC_STREAMOFF`` 将按上述方式将排队的缓冲区恢复到初始状态。

.. _<mmap>: #mmap
.. _<userp>: #userp
.. _<dmabuf>: #dmabuf
.. 注意::

   应用程序可能在 ``VIDIOC_STREAMON`` 或 ``VIDIOC_STREAMOFF`` 调用之前或之后被抢占，且持续时间未知。没有“立即”开始或停止的概念。可以使用缓冲区时间戳与其他事件进行同步。

返回值
======

成功时返回0，失败时返回-1，并且设置 ``errno`` 变量为适当的错误码。通用错误码的描述请参见《通用错误码 <gen-errors>`_》章节。

EINVAL
    缓冲区 ``type`` 不受支持，或者尚未分配（内存映射）或入队（输出）任何缓冲区。
EPIPE
    驱动程序实现了 :ref:`pad 级别的格式配置 <pad-level-formats>`，且管道配置无效。
ENOLINK
    驱动程序实现了媒体控制器接口，且管道链接配置无效。
