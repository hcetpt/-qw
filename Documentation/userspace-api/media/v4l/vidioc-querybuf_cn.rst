SPDX 许可声明标识符: GFDL-1.1-no-invariants-or-later
C 命名空间: V4L

.. _VIDIOC_QUERYBUF:

*********************
ioctl VIDIOC_QUERYBUF
*********************

名称
====

VIDIOC_QUERYBUF - 查询缓冲区的状态

概要
====

.. c:macro:: VIDIOC_QUERYBUF

``int ioctl(int fd, VIDIOC_QUERYBUF, struct v4l2_buffer *argp)``

参数
====

``fd``
    由 :c:func:`open()` 返回的文件描述符
``argp``
    指向结构体 :c:type:`v4l2_buffer` 的指针
描述
====

此 ioctl 是 :ref:`流式传输 <mmap>` I/O 方法的一部分。它可以在使用 :ref:`VIDIOC_REQBUFS` ioctl 分配缓冲区之后随时用于查询缓冲区的状态。
应用程序需要将结构体 :c:type:`v4l2_buffer` 的 ``type`` 字段设置为之前在结构体 :c:type:`v4l2_format` 的 ``type`` 和结构体 :c:type:`v4l2_requestbuffers` 的 ``type`` 中使用的相同缓冲区类型，并设置 ``index`` 字段。有效的索引编号范围是从零到通过 :ref:`VIDIOC_REQBUFS`（结构体 :c:type:`v4l2_requestbuffers` 的 ``count``）分配的缓冲区数量减一。``reserved`` 和 ``reserved2`` 字段必须设置为 0。当使用 :ref:`多平面 API <planar-apis>` 时，``m.planes`` 字段必须包含一个指向结构体数组 :c:type:`v4l2_plane` 的用户空间指针，并且 ``length`` 字段需要设置为该数组中的元素数量。调用 :ref:`VIDIOC_QUERYBUF` 并传入指向该结构体的指针后，驱动程序会返回一个错误代码或填充该结构体的其余部分。在 ``flags`` 字段中，``V4L2_BUF_FLAG_MAPPED``、``V4L2_BUF_FLAG_PREPARED``、``V4L2_BUF_FLAG_QUEUED`` 和 ``V4L2_BUF_FLAG_DONE`` 标志将是有效的。``memory`` 字段将被设置为当前的 I/O 方法。对于单平面 API，``m.offset`` 包含从设备内存开始处到缓冲区的偏移量，``length`` 字段包含其大小。对于多平面 API，则使用 ``m.planes`` 数组元素中的 ``m.mem_offset`` 和 ``length`` 字段，而结构体 :c:type:`v4l2_buffer` 的 ``length`` 字段将设置为已填充数组元素的数量。驱动程序可能会或可能不会设置剩余的字段和标志，在这种情况下它们没有意义。
结构体 :c:type:`v4l2_buffer` 在 :ref:`buffer` 中定义。

返回值
======

成功时返回 0，失败时返回 -1 并且设置 ``errno`` 变量。通用错误代码在 :ref:`通用错误代码 <gen-errors>` 章节中描述。
EINVAL
    缓冲区 ``type`` 不受支持，或者 ``index`` 越界
