SPDX 许可声明标识符: GFDL-1.1-no-invariants-or-later
C 命名空间:: V4L

.. _VIDIOC_CREATE_BUFS:

************************
ioctl VIDIOC_CREATE_BUFS
************************

名称
====

VIDIOC_CREATE_BUFS - 创建用于内存映射、用户指针或 DMA 缓冲区 I/O 的缓冲区

概要
========

.. c:macro:: VIDIOC_CREATE_BUFS

``int ioctl(int fd, VIDIOC_CREATE_BUFS, struct v4l2_create_buffers *argp)``

参数
=========

``fd``
    由 :c:func:`open()` 返回的文件描述符
``argp``
    指向结构体 :c:type:`v4l2_create_buffers` 的指针

描述
===========

此 ioctl 用于创建用于 :ref:`内存映射 <mmap>`、:ref:`用户指针 <userp>` 或 :ref:`DMA 缓冲区 <dmabuf>` I/O 的缓冲区。当需要对缓冲区进行更严格的控制时，它可以作为 :ref:`VIDIOC_REQBUFS` ioctl 的替代或补充。此 ioctl 可以多次调用以创建不同大小的缓冲区。

为了分配设备缓冲区，应用程序必须初始化结构体 :c:type:`v4l2_create_buffers` 的相关字段。`count` 字段必须设置为请求的缓冲区数量，`memory` 字段指定请求的 I/O 方法，并且 `reserved` 数组必须清零。

`format` 字段指定了缓冲区必须能够处理的图像格式。应用程序需要填充此结构体 :c:type:`v4l2_format`。通常这将通过使用 :ref:`VIDIOC_TRY_FMT <VIDIOC_G_FMT>` 或 :ref:`VIDIOC_G_FMT <VIDIOC_G_FMT>` ioctl 来确保所请求的格式得到驱动程序的支持。根据格式的 `type` 字段，将使用单平面格式的请求缓冲区大小（或多平面格式的平面大小）来分配缓冲区。

如果硬件不支持请求的大小（通常是由于它们太小），驱动程序可能会返回错误。

通过此 ioctl 创建的缓冲区的最小大小将由 `format.pix.sizeimage` 字段（或其他格式类型的相应字段）定义。通常，如果 `format.pix.sizeimage` 字段小于给定格式所需的最小值，则会返回错误，因为驱动程序通常不允许这样做。如果它更大，则其值将被直接使用。换句话说，驱动程序可能会拒绝请求的大小，但如果接受该大小，驱动程序将保持不变地使用它。

当 ioctl 被调用时，驱动程序将尝试分配最多请求数量的缓冲区，并在 `count` 和 `index` 字段中存储实际分配的数量和起始索引。返回时，`count` 可能小于请求的数量。

.. c:type:: v4l2_create_buffers

.. tabularcolumns:: |p{4.4cm}|p{4.4cm}|p{8.5cm}|

.. flat-table:: struct v4l2_create_buffers
    :header-rows:  0
    :stub-columns: 0
    :widths:       1 1 2

    * - __u32
      - ``index``
      - 驱动程序返回的起始缓冲区索引
    * - __u32
      - ``count``
      - 请求或授予的缓冲区数量。如果 `count` 等于 0，则 :ref:`VIDIOC_CREATE_BUFS` 将 `index` 设置为当前已创建的缓冲区数量，并检查 `memory` 和 `format.type` 的有效性。如果这些无效，返回 -1 并将 `errno` 设置为 `EINVAL` 错误码；否则 :ref:`VIDIOC_CREATE_BUFS` 返回 0。在这种特定情况下，它永远不会将 `errno` 设置为 `EBUSY` 错误码。
* - __u32
      - ``memory``
      - 应用程序将此字段设置为 ``V4L2_MEMORY_MMAP``、``V4L2_MEMORY_DMABUF`` 或 ``V4L2_MEMORY_USERPTR``。参见 :c:type:`v4l2_memory`
    * - struct :c:type:`v4l2_format`
      - ``format``
      - 由应用程序填充，由驱动程序保留
* - __u32
      - ``capabilities``
      - 由驱动程序设置。如果为0，则表示该驱动程序不支持任何功能。在这种情况下，你只知道该驱动程序保证支持 ``V4L2_MEMORY_MMAP``，并且可能支持其他 :c:type:`v4l2_memory` 类型。它不会支持任何其他功能。参见 :ref:`这里 <v4l2-buf-capabilities>` 获取功能列表
如果你想仅查询功能而不做其他更改，则将 ``count`` 设置为0，将 ``memory`` 设置为 ``V4L2_MEMORY_MMAP``，并将 ``format.type`` 设置为缓冲区类型
* - __u32
      - ``flags``
      - 指定额外的缓冲区管理属性。参见 :ref:`memory-flags`
* - __u32
      - ``max_num_buffers``
      - 如果设置了 V4L2_BUF_CAP_SUPPORTS_MAX_NUM_BUFFERS 功能标志，则此字段指示此队列的最大缓冲区数量
* - __u32
      - ``reserved``\[5\]
      - 用于将来扩展的占位符。驱动程序和应用程序必须将数组设置为零

返回值
======

成功时返回0，错误时返回-1，并且根据情况设置 ``errno`` 变量。通用错误代码在 :ref:`通用错误代码 <gen-errors>` 章节中描述
ENOMEM
    为 :ref:`内存映射 <mmap>` I/O 分配缓冲区时没有足够的内存
EINVAL
    缓冲区类型（``format.type`` 字段）、请求的I/O方法（``memory``）或格式（``format`` 字段）无效
当然，请提供你需要翻译的文本。
