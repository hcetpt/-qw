SPDX 许可声明标识符: GFDL-1.1-no-invariants-or-later
.. c:namespace:: V4L

.. _VIDIOC_REQBUFS:

********************
ioctl VIDIOC_REQBUFS
********************

名称
====

VIDIOC_REQBUFS - 初始化内存映射、用户指针 I/O 或 DMA 缓冲区 I/O

概述
========

.. c:macro:: VIDIOC_REQBUFS

``int ioctl(int fd, VIDIOC_REQBUFS, struct v4l2_requestbuffers *argp)``

参数
=========

``fd``
    由 :c:func:`open()` 返回的文件描述符
``argp``
    指向结构体 :c:type:`v4l2_requestbuffers` 的指针
描述
===========

此 ioctl 用于初始化 :ref:`内存映射<mmap>`、:ref:`用户指针<userp>` 或 :ref:`DMABUF<dmabuf>` 基于的 I/O。
内存映射缓冲区位于设备内存中，必须通过此 ioctl 进行分配，才能将其映射到应用程序的地址空间。用户缓冲区由应用程序自行分配，此 ioctl 仅用于将驱动程序切换到用户指针 I/O 模式并设置一些内部结构。同样地，DMABUF 缓冲区由应用程序通过设备驱动程序分配，此 ioctl 只配置驱动程序为 DMABUF I/O 模式，并不执行任何直接分配。

为了分配设备缓冲区，应用程序需要初始化结构体 :c:type:`v4l2_requestbuffers` 的所有字段。他们将 ``type`` 字段设置为相应的流或缓冲区类型，将 ``count`` 字段设置为所需的缓冲区数量，“memory” 必须设置为请求的 I/O 方法，并且 “reserved” 数组必须清零。当通过指向此结构体的指针调用 ioctl 时，驱动程序将尝试分配请求的缓冲区数量，并在 ``count`` 字段中存储实际分配的数量。这个数字可能小于请求的数量，甚至可以是零，当驱动程序内存不足时。如果驱动程序需要更多缓冲区以正常工作，也可能分配更多的数量。例如，视频输出至少需要两个缓冲区，一个正在显示，另一个由应用程序填充。

如果 I/O 方法不受支持，ioctl 将返回 ``EINVAL`` 错误代码。

应用程序可以再次调用 :ref:`VIDIOC_REQBUFS` 来更改缓冲区的数量。请注意，如果仍有任何缓冲区被映射或通过 DMABUF 导出，则 :ref:`VIDIOC_REQBUFS` 只有在设置了 ``V4L2_BUF_CAP_SUPPORTS_ORPHANED_BUFS`` 能力的情况下才能成功。否则 :ref:`VIDIOC_REQBUFS` 将返回 ``EBUSY`` 错误代码。

如果设置了 ``V4L2_BUF_CAP_SUPPORTS_ORPHANED_BUFS``，则这些缓冲区将被遗弃，并在它们被取消映射或导出的 DMABUF 文件描述符被关闭时释放。“count” 值为零会释放或遗弃所有缓冲区，在中止或完成任何正在进行的 DMA 后，隐式调用 :ref:`VIDIOC_STREAMOFF <VIDIOC_STREAMON>`。

.. c:type:: v4l2_requestbuffers

.. tabularcolumns:: |p{4.4cm}|p{4.4cm}|p{8.5cm}|

.. flat-table:: struct v4l2_requestbuffers
    :header-rows:  0
    :stub-columns: 0
    :widths:       1 1 2

    * - __u32
      - ``count``
      - 请求或授予的缓冲区数量
* - __u32
      - ``type``
      - 流或缓冲区的类型，这与结构体 :c:type:`v4l2_format` 的 ``type`` 字段相同。请参阅 :c:type:`v4l2_buf_type` 以获取有效值
* - `__u32`
      - `memory`
      - 应用程序将此字段设置为 `V4L2_MEMORY_MMAP`、`V4L2_MEMORY_DMABUF` 或 `V4L2_MEMORY_USERPTR`。参见 :c:type:`v4l2_memory`
* - `__u32`
      - `capabilities`
      - 由驱动程序设置。如果为 0，则表示驱动程序不支持功能。在这种情况下，您只知道该驱动程序保证支持 `V4L2_MEMORY_MMAP` 并且可能支持其他 :c:type:`v4l2_memory` 类型。它不会支持任何其他功能。如果您希望以最小的副作用查询功能，那么可以将 `count` 设置为 0，`memory` 设置为 `V4L2_MEMORY_MMAP`，并将 `type` 设置为缓冲区类型。这会释放之前分配的所有缓冲区，因此这通常会在应用程序启动时完成。
* - `__u8`
      - `flags`
      - 指定额外的缓冲区管理属性。参见 :ref:`memory-flags`
* - `__u8`
      - `reserved`\[3\]
      - 保留用于将来扩展

.. _v4l2-buf-capabilities:
.. _V4L2-BUF-CAP-SUPPORTS-MMAP:
.. _V4L2-BUF-CAP-SUPPORTS-USERPTR:
.. _V4L2-BUF-CAP-SUPPORTS-DMABUF:
.. _V4L2-BUF-CAP-SUPPORTS-REQUESTS:
.. _V4L2-BUF-CAP-SUPPORTS-ORPHANED-BUFS:
.. _V4L2-BUF-CAP-SUPPORTS-M2M-HOLD-CAPTURE-BUF:
.. _V4L2-BUF-CAP-SUPPORTS-MMAP-CACHE-HINTS:
.. _V4L2-BUF-CAP-SUPPORTS-MAX-NUM-BUFFERS:
.. _V4L2-BUF-CAP-SUPPORTS-REMOVE-BUFS:

.. raw:: latex

   \footnotesize

.. tabularcolumns:: |p{8.1cm}|p{2.2cm}|p{7.0cm}|

.. cssclass:: longtable

.. flat-table:: V4L2 缓冲区功能标志
    :header-rows:  0
    :stub-columns: 0
    :widths:       3 1 4

    * - `V4L2_BUF_CAP_SUPPORTS_MMAP`
      - 0x00000001
      - 此缓冲区类型支持 `V4L2_MEMORY_MMAP` 流模式
* - `V4L2_BUF_CAP_SUPPORTS_USERPTR`
      - 0x00000002
      - 此缓冲区类型支持 `V4L2_MEMORY_USERPTR` 流模式
* - `V4L2_BUF_CAP_SUPPORTS_DMABUF`
      - 0x00000004
      - 此缓冲区类型支持 `V4L2_MEMORY_DMABUF` 流模式
* - `V4L2_BUF_CAP_SUPPORTS_REQUESTS`
      - 0x00000008
      - 此缓冲区类型支持 :ref:`requests <media-request-api>`
* - ``V4L2_BUF_CAP_SUPPORTS_ORPHANED_BUFS``
      - 0x00000010
      - 内核允许在缓冲区仍被映射或通过DMABUF导出时调用 :ref:`VIDIOC_REQBUFS`。这些孤立的缓冲区将在它们被取消映射或导出的DMABUF文件描述符被关闭时被释放。
* - ``V4L2_BUF_CAP_SUPPORTS_M2M_HOLD_CAPTURE_BUF``
      - 0x00000020
      - 仅对无状态解码器有效。如果设置，则用户空间可以设置 ``V4L2_BUF_FLAG_M2M_HOLD_CAPTURE_BUF`` 标志，以推迟返回捕获缓冲区，直到OUTPUT时间戳发生变化。
* - ``V4L2_BUF_CAP_SUPPORTS_MMAP_CACHE_HINTS``
      - 0x00000040
      - 此功能由驱动程序设置，表示队列支持缓存和内存管理提示。但是，只有当队列用于 :ref:`内存映射 <mmap>` 流式I/O时才有效。请参阅 :ref:`V4L2_BUF_FLAG_NO_CACHE_INVALIDATE <V4L2-BUF-FLAG-NO-CACHE-INVALIDATE>`、:ref:`V4L2_BUF_FLAG_NO_CACHE_CLEAN <V4L2-BUF-FLAG-NO-CACHE-CLEAN>` 和 :ref:`V4L2_MEMORY_FLAG_NON_COHERENT <V4L2-MEMORY-FLAG-NON-COHERENT>`。

.. raw:: latex

   \normalsize

返回值
======

成功时返回0，失败时返回-1，并且设置 ``errno`` 变量。通用错误代码在 :ref:`通用错误代码 <gen-errors>` 章节中描述。
EINVAL
    缓冲区类型（``type`` 字段）或请求的I/O方法（``memory``）不受支持。
