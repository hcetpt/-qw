SPDX 许可证标识符: GFDL-1.1-no-invariants-or-later
C 命名空间:: V4L

.. _buffer:

*******
缓冲区
*******

缓冲区包含应用程序和驱动程序之间使用流式 I/O 方法交换的数据。在多平面 API 中，数据存储在平面上，而缓冲区结构则作为这些平面的容器。仅交换对缓冲区（平面）的指针，而不复制实际数据。这些指针以及时间戳或场奇偶性等元信息存储在 `v4l2_buffer` 结构体中，该结构体是 `VIDIOC_QUERYBUF`、`VIDIOC_QBUF <VIDIOC_QBUF>` 和 `VIDIOC_DQBUF <VIDIOC_QBUF>` ioctl 的参数。在多平面 API 中，一些特定于平面的成员（如每个平面的指针和大小）存储在 `v4l2_plane` 结构体中。在这种情况下，`v4l2_buffer` 结构体包含一个平面结构数组。从队列中取出的视频缓冲区带有时间戳。驱动程序决定在帧的哪个部分以及用哪个时钟来获取时间戳。请参阅 `V4L2_BUF_FLAG_TIMESTAMP_MASK` 和 `V4L2_BUF_FLAG_TSTAMP_SRC_MASK` 中的标志（见：:ref:`buffer-flags`）。这些标志在整个视频流过程中始终有效且保持不变。然而，这些标志的变化可能会作为 `VIDIOC_S_INPUT <VIDIOC_G_INPUT>` 或 `VIDIOC_S_OUTPUT <VIDIOC_G_OUTPUT>` 的副作用发生。`V4L2_BUF_FLAG_TIMESTAMP_COPY` 时间戳类型是一个例外，例如在内存到内存设备上使用此类型时，时间戳源标志将从输出视频缓冲区复制到捕获视频缓冲区。

格式、控制和缓冲区之间的交互
=================================

V4L2 暴露了一些影响缓冲区大小或数据在缓冲区中的布局的参数。这些参数通过格式和控制暴露。一个这样的控制示例是 `V4L2_CID_ROTATE` 控制，它修改了像素在缓冲区中的存储方向以及所选格式包含行末填充时的缓冲区大小。
所需的一组解释缓冲区内容的信息（例如像素格式、行步长、平铺方向或旋转）在本节中统称为缓冲区布局。
可以修改缓冲区布局的控制应设置 `V4L2_CTRL_FLAG_MODIFY_LAYOUT` 标志。
修改影响缓冲区大小或布局的格式或控制需要停止流。任何试图在流活动期间进行此类修改的操作都会导致设置格式或控制的 ioctl 返回 `EBUSY` 错误代码。在这种情况下，驱动程序还应在调用 `VIDIOC_QUERYCTRL` 或 `VIDIOC_QUERY_EXT_CTRL` 时为该控制设置 `V4L2_CTRL_FLAG_GRABBED` 标志。
.. note::

   `VIDIOC_S_SELECTION` ioctl 可能会根据硬件（例如如果设备不包括缩放器）修改格式，除了选择矩形之外。类似地，`VIDIOC_S_INPUT`、`VIDIOC_S_OUTPUT`、`VIDIOC_S_STD` 和 `VIDIOC_S_DV_TIMINGS` ioctl 也可能修改格式和选择矩形。当这些 ioctl 导致缓冲区大小或布局变化时，驱动程序应像处理 `VIDIOC_S_FMT` ioctl 那样处理这种情况。
仅影响缓冲区布局的控制可以在流停止时随时修改。由于它们不影响缓冲区大小，因此无需特别处理以同步这些控制与缓冲区分配，并且一旦流停止就会清除 `V4L2_CTRL_FLAG_GRABBED` 标志。
影响缓冲区大小的格式和控制与缓冲区分配相互作用。最简单的处理方法是驱动程序始终要求重新分配缓冲区以更改这些格式或控制。在这种情况下，要执行此类更改，用户空间应用程序首先应使用 `VIDIOC_STREAMOFF` ioctl 停止视频流（如果正在运行），并使用 `VIDIOC_REQBUFS` ioctl 释放所有已分配的缓冲区。释放所有缓冲区后，控制的 `V4L2_CTRL_FLAG_GRABBED` 标志被清除。然后可以修改格式或控制，然后重新分配缓冲区并重启流。一个典型的 ioctl 序列如下：

1. VIDIOC_STREAMOFF
2. VIDIOC_REQBUFS(0)
3. VIDIOC_S_EXT_CTRLS
4. VIDIOC_S_FMT
5. VIDIOC_REQBUFS(n)
6. VIDIOC_QBUF
7. VIDIOC_STREAMON

第二次调用 `VIDIOC_REQBUFS` 将根据新的格式和控制值计算要分配的缓冲区大小。应用程序也可以通过调用 `VIDIOC_G_FMT` ioctl 来获取大小（如果需要的话）。
.. note::

   API 并不要求控制（3.）和格式（4.）更改必须按照上述顺序进行。根据设备和使用场景，可以以不同的顺序设置格式和控制，甚至可以交错设置。例如，某些控制可能在不同的像素格式下表现不同，在这种情况下，可能需要先设置格式。

当需要重新分配缓冲区时，任何试图在已分配的缓冲区中修改影响缓冲区大小的格式或控制的操作应当使格式或控制设置 ioctl 返回 ``EBUSY`` 错误。任何试图队列一个对于当前格式或控制来说过小的缓冲区的操作应当使 :c:func:`VIDIOC_QBUF` ioctl 返回 ``EINVAL`` 错误。

缓冲区重新分配是一个昂贵的操作。为了避免这一成本，驱动程序可以（并且被鼓励）允许在已分配的缓冲区中更改影响缓冲区大小的格式或控制。在这种情况下，修改格式和控制的标准 ioctl 序列为：

1. VIDIOC_STREAMOFF
2. VIDIOC_S_EXT_CTRLS
3. VIDIOC_S_FMT
4. VIDIOC_QBUF
5. VIDIOC_STREAMON

为了使此序列正确运行，排队的缓冲区需要足够大以适应新的格式或控制。如果当前排队的缓冲区对于新格式来说过小，驱动程序应返回 ``ENOSPC`` 错误来响应格式更改 (:c:func:`VIDIOC_S_FMT`) 或控制更改 (:c:func:`VIDIOC_S_CTRL` 或 :c:func:`VIDIOC_S_EXT_CTRLS`)。作为简化，如果任何缓冲区当前处于排队状态，而无需检查排队缓冲区的大小，驱动程序允许从这些 ioctl 返回 ``EBUSY`` 错误。

此外，如果排队的缓冲区对于当前格式或控制来说过小，驱动程序应从 :c:func:`VIDIOC_QBUF` ioctl 返回 ``EINVAL`` 错误。这些要求共同确保排队的缓冲区始终足够大以适应配置的格式和控制。

用户空间应用程序可以通过首先设置所需的控制值然后尝试所需格式来查询给定格式和控制所需的缓冲区大小。:c:func:`VIDIOC_TRY_FMT` ioctl 将返回所需的缓冲区大小。

1. VIDIOC_S_EXT_CTRLS(x)
2. VIDIOC_TRY_FMT()
3. VIDIOC_S_EXT_CTRLS(y)
4. VIDIOC_TRY_FMT()

然后可以使用 :c:func:`VIDIOC_CREATE_BUFS` ioctl 基于查询的大小分配缓冲区（例如，通过分配一组足够大的缓冲区以容纳所有所需的格式和控制，或者为每个使用场景分配一组适当大小的缓冲区）。

.. c:type:: v4l2_buffer

struct v4l2_buffer
==================

.. tabularcolumns:: |p{2.9cm}|p{2.4cm}|p{12.0cm}|

.. cssclass:: longtable

.. flat-table:: struct v4l2_buffer
    :header-rows:  0
    :stub-columns: 0
    :widths:       1 2 10

    * - __u32
      - ``index``
      - 缓冲区编号，由应用程序设置，除了调用 :ref:`VIDIOC_DQBUF <VIDIOC_QBUF>` 时，该字段由驱动程序设置。此字段可以从零到通过 :ref:`VIDIOC_REQBUFS` ioctl 分配的缓冲区数量（struct :c:type:`v4l2_requestbuffers` ``count``），加上通过 :ref:`VIDIOC_CREATE_BUFS` 分配的缓冲区数量减一。
    * - __u32
      - ``type``
      - 缓冲区类型，与 struct :c:type:`v4l2_format` ``type`` 或 struct :c:type:`v4l2_requestbuffers` ``type`` 相同，由应用程序设置。参见 :c:type:`v4l2_buf_type`
    * - __u32
      - ``bytesused``
      - 缓冲区中数据占用的字节数。这取决于协商的数据格式，并且对于压缩的可变大小数据（如 JPEG 图像）可能会随着每个缓冲区的变化而变化。当 ``type`` 指向捕获流时，驱动程序必须设置此字段；当指向输出流时，应用程序必须设置此字段。对于多平面格式，此字段被忽略，而是使用 ``planes`` 指针。
    * - __u32
      - ``flags``
      - 由应用程序或驱动程序设置的标志，参见 :ref:`buffer-flags`
    * - __u32
      - ``field``
      - 指示缓冲区中图像的场序，参见 :c:type:`v4l2_field`。当缓冲区包含 VBI 数据时，此字段不使用。当 ``type`` 指向捕获流时，驱动程序必须设置此字段；当指向输出流时，应用程序必须设置此字段。
* - `struct timeval`
  - `timestamp`
  - 对于捕获流，这是第一个数据字节被捕获的时间，由相关时钟ID下的`:c:func:`clock_gettime()`函数返回；参见`:ref:`buffer-flags`中的`V4L2_BUF_FLAG_TIMESTAMP_*`。对于输出流，驱动程序会在`timestamp`字段中存储最后一个数据字节实际发送出去的时间。这允许应用程序监控视频时钟与系统时钟之间的漂移。对于使用`V4L2_BUF_FLAG_TIMESTAMP_COPY`标志的输出流，应用程序需要填充时间戳，该时间戳将由驱动程序复制到捕获流。
* - `struct :c:type:`v4l2_timecode`
  - `timecode`
  - 当`flags`中设置了`V4L2_BUF_FLAG_TIMECODE`标志时，此结构包含一个帧时间码。在`:c:type:`v4L2_FIELD_ALTERNATE <v4l2_field>`模式下，顶场和底场均包含相同的时间码。时间码旨在帮助视频编辑，通常记录在录像带上，但也嵌入在如MPEG等压缩格式中。此字段独立于`timestamp`和`sequence`字段。
* - `__u32`
  - `sequence`
  - 由驱动程序设置，按顺序计数帧（而不是场！）。此字段适用于输入设备和输出设备。
  - 在`:c:type:`V4L2_FIELD_ALTERNATE <v4l2_field>`模式下，顶场和底场均具有相同的序列号。计数从零开始，并包括丢失或重复的帧。一个丢失的帧被输入设备接收但因缺少空闲缓冲区而无法存储。一个重复的帧由于应用程序未能及时传递新数据而被输出设备再次显示。
  - 注意：这可能仅计算通过USB等接收到的帧，而不考虑由于压缩吞吐量或总线带宽限制而导致远程硬件丢弃的帧。这些设备通过不枚举任何视频标准来识别，参见`:ref:`standard`。
* - `__u32`
  - `memory`
  - 此字段必须由应用程序和/或驱动程序根据所选I/O方法进行设置。参见`:c:type:`v4l2_memory`。
* - `union {`
  - `m`
* - `__u32`
  - `offset`
  - 对于单平面API且当`memory`为`V4L2_MEMORY_MMAP`时，这是从设备内存起始位置到缓冲区的偏移量。此值由驱动程序返回，除了作为`:c:func:`mmap()`函数的参数外，对应用程序没有用处。详细信息请参见`:ref:`mmap`。
* - `unsigned long`
  - `userptr`
  - 对于单平面API且当`memory`为`V4L2_MEMORY_USERPTR`时，这是指向虚拟内存中缓冲区的指针（转换为`unsigned long`类型），由应用程序设置。详细信息请参见`:ref:`userp`。
* - `struct v4l2_plane`
  - `*planes`
  - 使用多平面API时，包含一个指向用户空间中的`struct :c:type:`v4l2_plane`数组的指针。数组的大小应放入此`struct :c:type:`v4l2_buffer`结构的`length`字段中。
* - `int`
  - `fd`
  - 对于单平面API且当`memory`为`V4L2_MEMORY_DMABUF`时，这是与DMABUF缓冲区关联的文件描述符。
* - `__u32`
  - `length`
  - 单平面 API 中缓冲区（而非有效载荷）的字节大小。该值由驱动程序根据对 `:ref:VIDIOC_REQBUFS` 和/或 `:ref:VIDIOC_CREATE_BUFS` 的调用设置。对于多平面 API，应用程序将此值设置为 `planes` 数组中的元素数量。驱动程序会填充该数组中实际有效的元素数量。

* - `__u32`
  - `reserved2`
  - 用于未来扩展的预留字段。驱动程序和应用程序必须将其设置为 0。

* - `__u32`
  - `request_fd`
  - 要排队缓冲区的请求的文件描述符。如果设置了标志 `V4L2_BUF_FLAG_REQUEST_FD`，则缓冲区将被排队到此请求。如果未设置此标志，则此字段将被忽略。
  标志 `V4L2_BUF_FLAG_REQUEST_FD` 和此字段仅在 `:ref:ioctl VIDIOC_QBUF <VIDIOC_QBUF>` 中使用，并且在其他接受 `c:type:v4l2_buffer` 参数的 ioctl 中会被忽略。
  应用程序不应在除 `:ref:VIDIOC_QBUF <VIDIOC_QBUF>` 以外的任何 ioctl 中设置 `V4L2_BUF_FLAG_REQUEST_FD`。
  如果设备不支持请求，则会返回 `EBADR`。
  如果支持请求但提供了无效的请求文件描述符，则会返回 `EINVAL`。

.. c:type:: v4l2_plane

`struct v4l2_plane`
==================

.. tabularcolumns:: |p{3.5cm}|p{3.5cm}|p{10.3cm}|

.. cssclass:: longtable

.. flat-table::
    :header-rows:  0
    :stub-columns: 0
    :widths:       1 1 2

    * - `__u32`
      - `bytesused`
      - 平面中数据占用的字节数（其有效载荷）
  驱动程序在 `type` 指向捕获流时必须设置此字段，应用程序在 `type` 指向输出流时设置此字段。

.. note::

   实际图像数据从 `data_offset` 开始，该偏移量可能不为 0。
* - `__u32`
  - `length`
  - 平面的字节大小（而非其有效负载）。这是由驱动程序根据对
  :ref:`VIDIOC_REQBUFS` 和/或
  :ref:`VIDIOC_CREATE_BUFS` 的调用来设置的。
* - union {
  - `m`
* - `__u32`
  - `mem_offset`
  - 当包含的结构体 :c:type:`v4l2_buffer` 中的内存类型为 `V4L2_MEMORY_MMAP` 时，
    这是应传递给 :c:func:`mmap()` 的值，类似于结构体 :c:type:`v4l2_buffer` 中的 `offset` 字段。
* - `unsigned long`
  - `userptr`
  - 当包含的结构体 :c:type:`v4l2_buffer` 中的内存类型为 `V4L2_MEMORY_USERPTR` 时，
    这是一个指向应用程序为此平面分配的内存的用户空间指针。
* - `int`
  - `fd`
  - 当包含的结构体 :c:type:`v4l2_buffer` 中的内存类型为 `V4L2_MEMORY_DMABUF` 时，
    这是一个与 DMABUF 缓冲区关联的文件描述符，类似于结构体 :c:type:`v4l2_buffer` 中的 `fd` 字段。
* - }
  -
* - `__u32`
  - `data_offset`
  - 视频数据在平面中的字节偏移量。当 `type` 指向捕获流时，驱动程序必须设置该字段；
  应用程序在 `type` 指向输出流时设置该字段。
.. note::
   数据偏移量 `data_offset` 包含在 `bytesused` 中。因此，图像在平面上的大小为 `bytesused` 减去 `data_offset`，
   从平面起始位置偏移 `data_offset` 处开始。
* - `__u32`
  - `reserved[11]`
  - 预留供将来使用。驱动程序和应用程序应将其置零。

.. c:type:: v4l2_buf_type

枚举 `v4l2_buf_type`
====================

.. cssclass:: longtable

.. tabularcolumns:: |p{7.8cm}|p{0.6cm}|p{8.9cm}|

.. flat-table::
   :header-rows:  0
   :stub-columns: 0
   :widths:       4 1 9

   * - `V4L2_BUF_TYPE_VIDEO_CAPTURE`
     - 1
     - 单平面视频捕获流的缓冲区，参见 :ref:`capture`
   * - `V4L2_BUF_TYPE_VIDEO_CAPTURE_MPLANE`
     - 9
     - 多平面视频捕获流的缓冲区，参见 :ref:`capture`
   * - `V4L2_BUF_TYPE_VIDEO_OUTPUT`
     - 2
     - 单平面视频输出流的缓冲区，参见 :ref:`output`
* - ``V4L2_BUF_TYPE_VIDEO_OUTPUT_MPLANE``
      - 10
      - 多平面视频输出流的缓冲区，详见 :ref:`output`
* - ``V4L2_BUF_TYPE_VIDEO_OVERLAY``
      - 3
      - 视频覆盖层的缓冲区，详见 :ref:`overlay`
* - ``V4L2_BUF_TYPE_VBI_CAPTURE``
      - 4
      - 原始垂直消隐间隔（VBI）捕获流的缓冲区，详见 :ref:`raw-vbi`
* - ``V4L2_BUF_TYPE_VBI_OUTPUT``
      - 5
      - 原始垂直消隐间隔（VBI）输出流的缓冲区，详见 :ref:`raw-vbi`
* - ``V4L2_BUF_TYPE_SLICED_VBI_CAPTURE``
      - 6
      - 分段垂直消隐间隔（VBI）捕获流的缓冲区，详见 :ref:`sliced`
* - ``V4L2_BUF_TYPE_SLICED_VBI_OUTPUT``
      - 7
      - 分段垂直消隐间隔（VBI）输出流的缓冲区，详见 :ref:`sliced`
* - ``V4L2_BUF_TYPE_VIDEO_OUTPUT_OVERLAY``
      - 8
      - 视频输出覆盖层（OSD）的缓冲区，详见 :ref:`osd`
* - ``V4L2_BUF_TYPE_SDR_CAPTURE``
      - 11
      - 软件定义无线电（SDR）捕获流的缓冲区，详见 :ref:`sdr`
* - ``V4L2_BUF_TYPE_SDR_OUTPUT``
      - 12
      - 软件定义无线电（SDR）输出流的缓冲区，详见 :ref:`sdr`
* - ``V4L2_BUF_TYPE_META_CAPTURE``
      - 13
      - 元数据捕获的缓冲区，详见 :ref:`metadata`
```markdown
* - ``V4L2_BUF_TYPE_META_OUTPUT``
  - 14
  - 用于元数据输出的缓冲区，详见 :ref:`metadata`

.. _buffer-flags:

缓冲区标志
============

.. raw:: latex

    \footnotesize

.. tabularcolumns:: |p{6.5cm}|p{1.8cm}|p{9.0cm}|

.. cssclass:: longtable

.. flat-table::
    :header-rows:  0
    :stub-columns: 0
    :widths:       65 18 70

    * .. _`V4L2-BUF-FLAG-MAPPED`:

      - ``V4L2_BUF_FLAG_MAPPED``
      - 0x00000001
      - 缓冲区位于设备内存中，并已映射到应用程序的地址空间，详细信息请参见 :ref:`mmap`
驱动程序在调用 :ref:`VIDIOC_QUERYBUF`、:ref:`VIDIOC_QBUF` 或 :ref:`VIDIOC_DQBUF <VIDIOC_QBUF>` ioctl 时设置或清除此标志。由驱动程序设置
* .. _`V4L2-BUF-FLAG-QUEUED`:

      - ``V4L2_BUF_FLAG_QUEUED``
      - 0x00000002
      - 驱动程序内部维护两个缓冲区队列：输入队列和输出队列。当此标志被设置时，缓冲区当前位于输入队列。在缓冲区被填充（捕获设备）或显示（输出设备）后，它会自动移动到输出队列。驱动程序在调用 ``VIDIOC_QUERYBUF`` ioctl 时设置或清除此标志。成功调用 ``VIDIOC_QBUF`` ioctl 后，此标志始终被设置；调用 ``VIDIOC_DQBUF`` 后始终被清除
* .. _`V4L2-BUF-FLAG-DONE`:

      - ``V4L2_BUF_FLAG_DONE``
      - 0x00000004
      - 当此标志被设置时，缓冲区当前位于输出队列，准备从驱动程序中出队。驱动程序在调用 ``VIDIOC_QUERYBUF`` ioctl 时设置或清除此标志。调用 ``VIDIOC_QBUF`` 或 ``VIDIOC_DQBUF`` ioctl 后，此标志始终被清除。当然，一个缓冲区不能同时位于两个队列中，``V4L2_BUF_FLAG_QUEUED`` 和 ``V4L2_BUF_FLAG_DONE`` 标志是互斥的。然而，它们可以都被清除，此时缓冲区处于“出队”状态，即在应用程序域内
* .. _`V4L2-BUF-FLAG-ERROR`:

      - ``V4L2_BUF_FLAG_ERROR``
      - 0x00000040
      - 当此标志被设置时，缓冲区已被成功出队，尽管数据可能已被损坏。这是可恢复的，流媒体可以继续正常工作，缓冲区也可以正常重用。驱动程序在调用 ``VIDIOC_DQBUF`` ioctl 时设置此标志
* .. _`V4L2-BUF-FLAG-IN-REQUEST`:

      - ``V4L2_BUF_FLAG_IN_REQUEST``
      - 0x00000080
      - 此缓冲区是尚未排队的请求的一部分
* .. _`V4L2-BUF-FLAG-KEYFRAME`:

      - ``V4L2_BUF_FLAG_KEYFRAME``
      - 0x00000008
      - 驱动程序在调用 ``VIDIOC_DQBUF`` ioctl 时设置或清除此标志。视频捕获设备在缓冲区包含压缩图像且为关键帧（或场）时可能会设置此标志，即可以独立解压缩。也称为 I 帧
应用程序可以在 ``type`` 指向输出流时设置此位
```
* .. _`V4L2-BUF-FLAG-PFRAME`:

      - ``V4L2_BUF_FLAG_PFRAME``
      - 0x00000010
      - 类似于 ``V4L2_BUF_FLAG_KEYFRAME``，此标志表示预测帧或场，仅包含与前一个关键帧的差异。应用程序可以在 ``type`` 指向输出流时设置此位。
* .. _`V4L2-BUF-FLAG-BFRAME`:

      - ``V4L2_BUF_FLAG_BFRAME``
      - 0x00000020
      - 类似于 ``V4L2_BUF_FLAG_KEYFRAME``，此标志表示双向预测帧或场，仅包含当前帧与前后关键帧之间的差异以指定其内容。应用程序可以在 ``type`` 指向输出流时设置此位。
* .. _`V4L2-BUF-FLAG-TIMECODE`:

      - ``V4L2_BUF_FLAG_TIMECODE``
      - 0x00000100
      - 时间码字段有效。驱动程序在调用 ``VIDIOC_DQBUF`` ioctl 时会设置或清除此标志。应用程序可以在 ``type`` 指向输出流时设置此位和相应的时间码结构。
* .. _`V4L2-BUF-FLAG-PREPARED`:

      - ``V4L2_BUF_FLAG_PREPARED``
      - 0x00000400
      - 缓冲区已准备好进行 I/O 操作，并且可以由应用程序排队。驱动程序在调用 :ref:`VIDIOC_QUERYBUF <VIDIOC_QUERYBUF>`、:ref:`VIDIOC_PREPARE_BUF <VIDIOC_QBUF>`、:ref:`VIDIOC_QBUF <VIDIOC_QBUF>` 或 :ref:`VIDIOC_DQBUF <VIDIOC_QBUF>` ioctl 时会设置或清除此标志。
* .. _`V4L2-BUF-FLAG-NO-CACHE-INVALIDATE`:

      - ``V4L2_BUF_FLAG_NO_CACHE_INVALIDATE``
      - 0x00000800
      - 对于此缓冲区不需要使缓存失效。通常，如果缓冲区中的数据不会被 CPU 访问，而是直接传递给 DMA 能力的硬件单元进行进一步处理或输出，则应用程序应使用此标志。除非队列用于 :ref:`内存映射 <mmap>` 流式 I/O 并报告 :ref:`V4L2_BUF_CAP_SUPPORTS_MMAP_CACHE_HINTS <V4L2-BUF-CAP-SUPPORTS-MMAP-CACHE-HINTS>` 能力，否则此标志将被忽略。
* .. _`V4L2-BUF-FLAG-NO-CACHE-CLEAN`:

      - ``V4L2_BUF_FLAG_NO_CACHE_CLEAN``
      - 0x00001000
      - 对于此缓冲区不需要清理缓存。通常，如果此缓冲区中的数据不是由 CPU 创建的，而是由某个 DMA 能力的单元创建的，则应用程序应使用此标志。除非队列用于 :ref:`内存映射 <mmap>` 流式 I/O 并报告 :ref:`V4L2_BUF_CAP_SUPPORTS_MMAP_CACHE_HINTS <V4L2-BUF-CAP-SUPPORTS-MMAP-CACHE-HINTS>` 能力，否则此标志将被忽略。
* .. _`V4L2-BUF-FLAG-M2M-HOLD-CAPTURE-BUF`:

      - ``V4L2_BUF_FLAG_M2M_HOLD_CAPTURE_BUF``
      - 0x00000200
      - 仅当 struct :c:type:`v4l2_requestbuffers` 标志 ``V4L2_BUF_CAP_SUPPORTS_M2M_HOLD_CAPTURE_BUF`` 被设置时有效。通常用于无状态解码器，其中多个输出缓冲区分别解码为解码帧的一个片断。应用程序可以在排队输出缓冲区时设置此标志，以防止驱动程序在输出缓冲区解码后将捕获缓冲区出队（即“保留”捕获缓冲区）。如果此输出缓冲区的时间戳与前一个输出缓冲区不同，则表示新帧的开始，并且之前保留的捕获缓冲区将被出队。
* .. _`V4L2-BUF-FLAG-LAST`:

      - ``V4L2_BUF_FLAG_LAST``
      - 0x00100000
      - 硬件生成的最后一个缓冲区。mem2mem 编码驱动程序在调用 :ref:`VIDIOC_QUERYBUF` 或 :ref:`VIDIOC_DQBUF <VIDIOC_QBUF>` ioctl 时会在捕获队列中为最后一个缓冲区设置此标志。由于硬件限制，最后一个缓冲区可能是空的。在这种情况下，驱动程序会将 ``bytesused`` 字段设置为 0，无论格式如何。任何后续调用 :ref:`VIDIOC_DQBUF <VIDIOC_QBUF>` ioctl 将不再阻塞，而是返回一个 ``EPIPE`` 错误代码。
* .. _`V4L2-BUF-FLAG-REQUEST-FD`:

      - ``V4L2_BUF_FLAG_REQUEST_FD``
      - 0x00800000
      - ``request_fd`` 字段包含一个有效的文件描述符
* .. _`V4L2-BUF-FLAG-TIMESTAMP-MASK`:

      - ``V4L2_BUF_FLAG_TIMESTAMP_MASK``
      - 0x0000e000
      - 时间戳类型的掩码。要测试时间戳类型，可以通过对缓冲区标志和时间戳掩码进行逻辑与操作来屏蔽不属于时间戳类型的部分
* .. _`V4L2-BUF-FLAG-TIMESTAMP-UNKNOWN`:

      - ``V4L2_BUF_FLAG_TIMESTAMP_UNKNOWN``
      - 0x00000000
      - 未知的时间戳类型。此类型在 Linux 3.9 之前的驱动程序中使用，可能是单调时间（见下文）或实时时间（系统时钟）。在嵌入式系统中通常偏好使用单调时钟，而大多数驱动程序则使用实时时钟。这两种类型的时间戳都可以通过 :c:func:`clock_gettime` 使用相应的时钟 ID ``CLOCK_MONOTONIC`` 和 ``CLOCK_REALTIME`` 在用户空间获取
* .. _`V4L2-BUF-FLAG-TIMESTAMP-MONOTONIC`:

      - ``V4L2_BUF_FLAG_TIMESTAMP_MONOTONIC``
      - 0x00002000
      - 缓冲区时间戳是从 ``CLOCK_MONOTONIC`` 时钟获取的。要在 V4L2 外部访问相同的时钟，请使用 :c:func:`clock_gettime`
* .. _`V4L2-BUF-FLAG-TIMESTAMP-COPY`:

      - ``V4L2_BUF_FLAG_TIMESTAMP_COPY``
      - 0x00004000
      - CAPTURE 缓冲区时间戳是从对应的 OUTPUT 缓冲区获取的。此标志仅适用于 mem2mem 设备
* .. _`V4L2-BUF-FLAG-TSTAMP-SRC-MASK`:

      - ``V4L2_BUF_FLAG_TSTAMP_SRC_MASK``
      - 0x00070000
      - 时间戳来源的掩码。时间戳来源定义了相对于帧的时间戳获取点。对 ``flags`` 字段和 ``V4L2_BUF_FLAG_TSTAMP_SRC_MASK`` 进行逻辑与操作会产生时间戳来源的值。当 ``type`` 指向输出流且设置了 ``V4L2_BUF_FLAG_TIMESTAMP_COPY`` 时，应用程序必须设置时间戳来源
* .. _`V4L2-BUF-FLAG-TSTAMP-SRC-EOF`:

      - ``V4L2_BUF_FLAG_TSTAMP_SRC_EOF``
      - 0x00000000
      - 帧结束。缓冲区时间戳是在接收到帧的最后一像素或传输完帧的最后一像素时获取的。实际上，软件生成的时间戳通常会在接收到或传输完最后一像素的一小段时间后从时钟读取，具体取决于系统和其他活动
* .. _`V4L2-BUF-FLAG-TSTAMP-SRC-SOE`:

      - ``V4L2_BUF_FLAG_TSTAMP_SRC_SOE``
      - 0x00010000
      - 曝光开始。缓冲区时间戳是在帧曝光开始时获取的。这仅对 ``V4L2_BUF_TYPE_VIDEO_CAPTURE`` 缓冲区类型有效

.. raw:: latex

    \normalsize

枚举 v4l2_memory
================

.. tabularcolumns:: |p{5.0cm}|p{0.8cm}|p{11.5cm}|

.. flat-table::
    :header-rows:  0
    :stub-columns: 0
    :widths:       3 1 4

    * - ``V4L2_MEMORY_MMAP``
      - 1
      - 缓冲区用于 :ref:`内存映射 <mmap>` I/O
```markdown
* - ``V4L2_MEMORY_USERPTR``
      - 2
      - 缓冲区用于 :ref:`用户指针 <userp>` I/O
* - ``V4L2_MEMORY_OVERLAY``
      - 3
      - [待完成]
* - ``V4L2_MEMORY_DMABUF``
      - 4
      - 缓冲区用于 :ref:`DMA共享缓冲区 <dmabuf>` I/O
.. _memory-flags:

内存一致性标志
-------------------------

.. raw:: latex

    \small

.. tabularcolumns:: |p{7.0cm}|p{2.1cm}|p{8.4cm}|

.. cssclass:: longtable

.. flat-table::
    :header-rows:  0
    :stub-columns: 0
    :widths:       3 1 4

    * .. _`V4L2-MEMORY-FLAG-NON-COHERENT`:

      - ``V4L2_MEMORY_FLAG_NON_COHERENT``
      - 0x00000001
      - 缓冲区分配在一致（它将在CPU和总线之间自动保持一致）或非一致内存中。后者可以提供性能提升，例如如果缓冲区仅由相应的设备访问且CPU不读写该缓冲区，则可以避免CPU缓存同步/刷新操作。然而，这需要驱动程序特别小心——必须通过发出缓存刷新/同步来保证在需要时的一致性。如果设置了此标志，V4L2将尝试将缓冲区分配在非一致内存中。该标志只有在缓冲区用于 :ref:`内存映射 <mmap>` I/O 并且队列报告了 :ref:`V4L2_BUF_CAP_SUPPORTS_MMAP_CACHE_HINTS <V4L2-BUF-CAP-SUPPORTS-MMAP-CACHE-HINTS>` 能力时才生效。
.. raw:: latex

    \normalsize

时间码
=======

:c:type:`v4l2_buffer_timecode` 结构设计用于存储一个 :ref:`smpte12m` 或类似的时间码（:c:type:`timeval` 时间戳存储在结构 :c:type:`v4l2_buffer` 的 ``timestamp`` 字段中）。

.. c:type:: v4l2_timecode

struct v4l2_timecode
--------------------

.. tabularcolumns:: |p{1.4cm}|p{2.8cm}|p{13.1cm}|

.. flat-table::
    :header-rows:  0
    :stub-columns: 0
    :widths:       1 1 2

    * - __u32
      - ``type``
      - 时间码所基于的帧率，见 :ref:`timecode-type`
* - __u32
      - ``flags``
      - 时间码标志，见 :ref:`timecode-flags`
* - __u8
      - ``frames``
      - 帧计数，0...23/24/29/49/59，取决于时间码类型
* - __u8
      - ``seconds``
      - 秒数计数，0...59。这是一个二进制数，不是BCD数
* - __u8
      - ``minutes``
      - 分钟计数，0...59。这是一个二进制数，不是BCD数
* - __u8
      - ``hours``
      - 小时计数，0...29。这是一个二进制数，不是BCD数
```
* - `__u8`
  - `userbits` [4]
  - 时间码中的“用户组”位

.. _timecode-type:

时间码类型
----------

.. flat-table::
    :header-rows:  0
    :stub-columns: 0
    :widths:       3 1 4

    * - ``V4L2_TC_TYPE_24FPS``
      - 1
      - 每秒24帧，即电影
    * - ``V4L2_TC_TYPE_25FPS``
      - 2
      - 每秒25帧，即PAL或SECAM视频
    * - ``V4L2_TC_TYPE_30FPS``
      - 3
      - 每秒30帧，即NTSC视频
    * - ``V4L2_TC_TYPE_50FPS``
      - 4
      -
    * - ``V4L2_TC_TYPE_60FPS``
      - 5
      -

.. _timecode-flags:

时间码标志
----------

.. tabularcolumns:: |p{6.6cm}|p{1.4cm}|p{9.3cm}|

.. flat-table::
    :header-rows:  0
    :stub-columns: 0
    :widths:       3 1 4

    * - ``V4L2_TC_FLAG_DROPFRAME``
      - 0x0001
      - 表示在29.97 fps材料中计数帧的“丢帧”语义。当设置时，除了第0、10、20、30、40和50分钟外，每分钟开头的第0帧和第1帧从计数中省略
    * - ``V4L2_TC_FLAG_COLORFRAME``
      - 0x0002
      - “彩色帧”标志
    * - ``V4L2_TC_USERBITS_field``
      - 0x000C
      - “二进制组标志”的字段掩码
    * - ``V4L2_TC_USERBITS_USERDEFINED``
      - 0x0000
      - 未指定格式
    * - ``V4L2_TC_USERBITS_8BITCHARS``
      - 0x0008
      - 8位ISO字符
