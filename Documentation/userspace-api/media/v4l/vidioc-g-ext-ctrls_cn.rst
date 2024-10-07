SPDX 许可声明标识符: GFDL-1.1-no-invariants-or-later
.. c:namespace:: V4L

.. _VIDIOC_G_EXT_CTRLS:

******************************************************************
ioctl VIDIOC_G_EXT_CTRLS, VIDIOC_S_EXT_CTRLS, VIDIOC_TRY_EXT_CTRLS
******************************************************************

名称
====

VIDIOC_G_EXT_CTRLS - VIDIOC_S_EXT_CTRLS - VIDIOC_TRY_EXT_CTRLS - 获取或设置多个控制值，尝试控制值

概要
========

.. c:macro:: VIDIOC_G_EXT_CTRLS

``int ioctl(int fd, VIDIOC_G_EXT_CTRLS, struct v4l2_ext_controls *argp)``

.. c:macro:: VIDIOC_S_EXT_CTRLS

``int ioctl(int fd, VIDIOC_S_EXT_CTRLS, struct v4l2_ext_controls *argp)``

.. c:macro:: VIDIOC_TRY_EXT_CTRLS

``int ioctl(int fd, VIDIOC_TRY_EXT_CTRLS, struct v4l2_ext_controls *argp)``

参数
=========

``fd``
    由 :c:func:`open()` 返回的文件描述符
``argp``
    指向结构体 :c:type:`v4l2_ext_controls` 的指针

描述
===========

这些 ioctl 函数允许调用者原子地获取或设置多个控制值。控制 ID 被分组为控制类（参见 :ref:`ctrl-class`），并且控制数组中的所有控制必须属于同一控制类。
应用程序必须始终填充结构体 :c:type:`v4l2_ext_controls` 的 ``count``、``which``、``controls`` 和 ``reserved`` 字段，并初始化由 ``controls`` 字段指向的 :c:type:`v4l2_ext_control` 数组。
为了获取一组控制的当前值，应用程序需要初始化每个结构体 :c:type:`v4l2_ext_control` 的 ``id``、``size`` 和 ``reserved2`` 字段，并调用 :ref:`VIDIOC_G_EXT_CTRLS <VIDIOC_G_EXT_CTRLS>` ioctl。字符串控制还必须设置 ``string`` 字段。复合类型控制（`V4L2_CTRL_FLAG_HAS_PAYLOAD` 标志被设置）必须设置 ``ptr`` 字段。
如果 ``size`` 太小无法接收控制结果（仅对字符串等指针类型控制相关），则驱动程序将设置 ``size`` 为有效值并返回 ``ENOSPC`` 错误码。你应该重新分配内存到这个新大小并重试。对于字符串类型，如果字符串在此期间增长，可能会再次出现相同的问题。建议先调用 :ref:`VIDIOC_QUERYCTRL` 并使用 ``maximum``+1 作为新的 ``size`` 值。可以保证这是足够的内存。
多维数组按行设置和检索。你不能设置部分数组，所有元素都必须设置或检索。总大小计算为 ``elems`` * ``elem_size``。这些值可以通过调用 :ref:`VIDIOC_QUERY_EXT_CTRL <VIDIOC_QUERYCTRL>` 获得。
为了更改一组控制的值，应用程序需要初始化每个结构体 :c:type:`v4l2_ext_control` 的 ``id``、``size``、``reserved2`` 和 ``value/value64/string/ptr`` 字段，并调用 :ref:`VIDIOC_S_EXT_CTRLS <VIDIOC_G_EXT_CTRLS>` ioctl。只有当所有控制值均有效时才会设置控制值。
为了检查一组控制是否有正确的值，应用程序需要初始化每个结构体 :c:type:`v4l2_ext_control` 的 ``id``、``size``、``reserved2`` 和 ``value/value64/string/ptr`` 字段，并调用 :ref:`VIDIOC_TRY_EXT_CTRLS <VIDIOC_G_EXT_CTRLS>` ioctl。驱动程序可以选择自动调整错误值为有效值或返回错误。
当 ``id`` 或 ``which`` 无效时，驱动程序返回 ``EINVAL`` 错误码。当值超出范围时，驱动程序可以选择取最近的有效值或返回 ``ERANGE`` 错误码，取决于哪种更合适。在第一种情况下，新值将设置在结构体 :c:type:`v4l2_ext_control` 中。如果新控制值不适当（例如给定的菜单索引不受菜单控制支持），这也会导致 ``EINVAL`` 错误码。
如果 `request_fd` 设置为一个尚未入队的 :ref:`请求 <media-request-api>` 文件描述符，并且 `which` 设置为 `V4L2_CTRL_WHICH_REQUEST_VAL`，则在调用 :ref:`VIDIOC_S_EXT_CTRLS <VIDIOC_G_EXT_CTRLS>` 时，控制操作不会立即应用，而是由驱动程序在与同一请求关联的缓冲区中应用。

如果设备不支持请求，则会返回 `EACCES` 错误。

如果支持请求但提供了无效的请求文件描述符，则会返回 `EINVAL` 错误。

尝试对已经入队的请求调用 :ref:`VIDIOC_S_EXT_CTRLS <VIDIOC_G_EXT_CTRLS>` 将导致 `EBUSY` 错误。

如果指定了 `request_fd` 并且在调用 :ref:`VIDIOC_G_EXT_CTRLS <VIDIOC_G_EXT_CTRLS>` 时将 `which` 设置为 `V4L2_CTRL_WHICH_REQUEST_VAL`，则它将返回请求完成时的控制值。

如果请求尚未完成，则会导致 `EACCES` 错误。

只有在所有控制值都正确的情况下，驱动程序才会设置/获取这些控制值。这可以防止仅部分控制被设置/获取的情况。只有低级错误（例如失败的 I2C 命令）仍可能导致这种情况。

.. tabularcolumns:: |p{6.8cm}|p{4.0cm}|p{6.5cm}|

.. c:type:: v4l2_ext_control

.. raw:: latex

   \footnotesize

.. cssclass:: longtable

.. flat-table:: struct v4l2_ext_control
    :header-rows:  0
    :stub-columns: 0
    :widths:       1 1 2

    * - __u32
      - ``id``
      - 标识控制项，由应用程序设置
* - __u32
      - ``size``
      - 该控制的有效载荷总大小（字节）
* - :cspan:`2` `size` 字段通常为 0，但对于指针控制，应将其设置为包含有效载荷或接收有效载荷的内存大小
如果 :ref:`VIDIOC_G_EXT_CTRLS <VIDIOC_G_EXT_CTRLS>` 发现该值小于存储有效负载结果所需的值，则将其设置为足够大的值以存储有效负载结果，并返回 ``ENOSPC``。

.. note::

   对于字符串控件，这个 ``size`` 字段不应与字符串的长度混淆。此字段指的是包含字符串的内存大小。实际的字符串 *长度* 可能要小得多。

* - __u32
      - ``reserved2``\[1\]
      - 保留用于将来扩展。驱动程序和应用程序必须将数组设为零
* - union {
      - (匿名)
    * - __s32
      - ``value``
      - 新值或当前值。如果此控件不是类型 ``V4L2_CTRL_TYPE_INTEGER64`` 并且未设置 ``V4L2_CTRL_FLAG_HAS_PAYLOAD`` 标志，则该字段有效
* - __s64
      - ``value64``
      - 新值或当前值。如果此控件是类型 ``V4L2_CTRL_TYPE_INTEGER64`` 并且未设置 ``V4L2_CTRL_FLAG_HAS_PAYLOAD`` 标志，则该字段有效
* - char *
      - ``string``
      - 指向字符串的指针。如果此控件是类型 ``V4L2_CTRL_TYPE_STRING``，则该字段有效
* - __u8 *
      - ``p_u8``
      - 指向无符号 8 位值矩阵控件的指针。如果此控件是类型 ``V4L2_CTRL_TYPE_U8``，则该字段有效
* - __u16 *
      - ``p_u16``
      - 指向无符号 16 位值矩阵控件的指针。如果此控件是类型 ``V4L2_CTRL_TYPE_U16``，则该字段有效
* - __u32 *
      - ``p_u32``
      - 指向无符号 32 位值矩阵控件的指针。如果此控件是类型 ``V4L2_CTRL_TYPE_U32``，则该字段有效
* - __s32 *
      - ``p_s32``
      - 指向有符号 32 位值矩阵控件的指针。如果此控件是类型 ``V4L2_CTRL_TYPE_INTEGER`` 并且设置了 ``V4L2_CTRL_FLAG_HAS_PAYLOAD`` 标志，则该字段有效
* - __s64 *
  - ``p_s64``
  - 指向一个由有符号64位值组成的矩阵控制的指针。如果此控制类型为 ``V4L2_CTRL_TYPE_INTEGER64`` 并且设置了 ``V4L2_CTRL_FLAG_HAS_PAYLOAD`` 标志，则该指针有效。
* - struct :c:type:`v4l2_area` *
  - ``p_area``
  - 指向一个 :c:type:`v4l2_area` 结构体的指针。如果此控制类型为 ``V4L2_CTRL_TYPE_AREA``，则该指针有效。
* - struct :c:type:`v4l2_ctrl_h264_sps` *
  - ``p_h264_sps``
  - 指向一个 :c:type:`v4l2_ctrl_h264_sps` 结构体的指针。如果此控制类型为 ``V4L2_CTRL_TYPE_H264_SPS``，则该指针有效。
* - struct :c:type:`v4l2_ctrl_h264_pps` *
  - ``p_h264_pps``
  - 指向一个 :c:type:`v4l2_ctrl_h264_pps` 结构体的指针。如果此控制类型为 ``V4L2_CTRL_TYPE_H264_PPS``，则该指针有效。
* - struct :c:type:`v4l2_ctrl_h264_scaling_matrix` *
  - ``p_h264_scaling_matrix``
  - 指向一个 :c:type:`v4l2_ctrl_h264_scaling_matrix` 结构体的指针。如果此控制类型为 ``V4L2_CTRL_TYPE_H264_SCALING_MATRIX``，则该指针有效。
* - struct :c:type:`v4l2_ctrl_h264_pred_weights` *
  - ``p_h264_pred_weights``
  - 指向一个 :c:type:`v4l2_ctrl_h264_pred_weights` 结构体的指针。如果此控制类型为 ``V4L2_CTRL_TYPE_H264_PRED_WEIGHTS``，则该指针有效。
* - struct :c:type:`v4l2_ctrl_h264_slice_params` *
  - ``p_h264_slice_params``
  - 指向一个 :c:type:`v4l2_ctrl_h264_slice_params` 结构体的指针。如果此控制类型为 ``V4L2_CTRL_TYPE_H264_SLICE_PARAMS``，则该指针有效。
* - struct :c:type:`v4l2_ctrl_h264_decode_params` *
  - ``p_h264_decode_params``
  - 指向一个 :c:type:`v4l2_ctrl_h264_decode_params` 结构体的指针。如果此控制类型为 ``V4L2_CTRL_TYPE_H264_DECODE_PARAMS``，则该指针有效。
* - struct :c:type:`v4l2_ctrl_fwht_params` *
  - ``p_fwht_params``
  - 指向一个 :c:type:`v4l2_ctrl_fwht_params` 结构体的指针。如果此控制类型为 ``V4L2_CTRL_TYPE_FWHT_PARAMS``，则该指针有效。
* - struct :c:type:`v4l2_ctrl_vp8_frame` *
  - ``p_vp8_frame``
  - 指向一个 :c:type:`v4l2_ctrl_vp8_frame` 结构体的指针。如果此控制类型为 ``V4L2_CTRL_TYPE_VP8_FRAME``，则该指针有效。
* - 结构体 :c:type:`v4l2_ctrl_mpeg2_sequence`
  - ``p_mpeg2_sequence``
  - 指向结构体 :c:type:`v4l2_ctrl_mpeg2_sequence` 的指针。如果此控制类型为 ``V4L2_CTRL_TYPE_MPEG2_SEQUENCE`` 则有效。
* - 结构体 :c:type:`v4l2_ctrl_mpeg2_picture`
  - ``p_mpeg2_picture``
  - 指向结构体 :c:type:`v4l2_ctrl_mpeg2_picture` 的指针。如果此控制类型为 ``V4L2_CTRL_TYPE_MPEG2_PICTURE`` 则有效。
* - 结构体 :c:type:`v4l2_ctrl_mpeg2_quantisation`
  - ``p_mpeg2_quantisation``
  - 指向结构体 :c:type:`v4l2_ctrl_mpeg2_quantisation` 的指针。如果此控制类型为 ``V4L2_CTRL_TYPE_MPEG2_QUANTISATION`` 则有效。
* - 结构体 :c:type:`v4l2_ctrl_vp9_compressed_hdr`
  - ``p_vp9_compressed_hdr_probs``
  - 指向结构体 :c:type:`v4l2_ctrl_vp9_compressed_hdr` 的指针。如果此控制类型为 ``V4L2_CTRL_TYPE_VP9_COMPRESSED_HDR`` 则有效。
* - 结构体 :c:type:`v4l2_ctrl_vp9_frame`
  - ``p_vp9_frame``
  - 指向结构体 :c:type:`v4l2_ctrl_vp9_frame` 的指针。如果此控制类型为 ``V4L2_CTRL_TYPE_VP9_FRAME`` 则有效。
* - 结构体 :c:type:`v4l2_ctrl_hdr10_cll_info`
  - ``p_hdr10_cll``
  - 指向结构体 :c:type:`v4l2_ctrl_hdr10_cll_info` 的指针。如果此控制类型为 ``V4L2_CTRL_TYPE_HDR10_CLL_INFO`` 则有效。
* - 结构体 :c:type:`v4l2_ctrl_hdr10_mastering_display`
  - ``p_hdr10_mastering``
  - 指向结构体 :c:type:`v4l2_ctrl_hdr10_mastering_display` 的指针。如果此控制类型为 ``V4L2_CTRL_TYPE_HDR10_MASTERING_DISPLAY`` 则有效。
* - 结构体 :c:type:`v4l2_ctrl_hevc_sps`
  - ``p_hevc_sps``
  - 指向结构体 :c:type:`v4l2_ctrl_hevc_sps` 的指针。如果此控制类型为 ``V4L2_CTRL_TYPE_HEVC_SPS`` 则有效。
* - 结构体 :c:type:`v4l2_ctrl_hevc_pps`
  - ``p_hevc_pps``
  - 指向结构体 :c:type:`v4l2_ctrl_hevc_pps` 的指针。如果此控制类型为 ``V4L2_CTRL_TYPE_HEVC_PPS`` 则有效。
* - 结构体 :c:type:`v4l2_ctrl_hevc_slice_params`
  - ``p_hevc_slice_params``
  - 指向结构体 :c:type:`v4l2_ctrl_hevc_slice_params` 的指针。如果此控制类型为 ``V4L2_CTRL_TYPE_HEVC_SLICE_PARAMS`` 则有效。
```markdown
* - 结构体 :c:type:`v4l2_ctrl_hevc_scaling_matrix`
  - ``p_hevc_scaling_matrix``
  - 指向结构体 :c:type:`v4l2_ctrl_hevc_scaling_matrix` 的指针。如果此控制类型为 ``V4L2_CTRL_TYPE_HEVC_SCALING_MATRIX``，则有效。
* - 结构体 :c:type:`v4l2_ctrl_hevc_decode_params`
  - ``p_hevc_decode_params``
  - 指向结构体 :c:type:`v4l2_ctrl_hevc_decode_params` 的指针。如果此控制类型为 ``V4L2_CTRL_TYPE_HEVC_DECODE_PARAMS``，则有效。
* - 结构体 :c:type:`v4l2_ctrl_av1_sequence`
  - ``p_av1_sequence``
  - 指向结构体 :c:type:`v4l2_ctrl_av1_sequence` 的指针。如果此控制类型为 ``V4L2_CTRL_TYPE_AV1_SEQUENCE``，则有效。
* - 结构体 :c:type:`v4l2_ctrl_av1_tile_group_entry`
  - ``p_av1_tile_group_entry``
  - 指向结构体 :c:type:`v4l2_ctrl_av1_tile_group_entry` 的指针。如果此控制类型为 ``V4L2_CTRL_TYPE_AV1_TILE_GROUP_ENTRY``，则有效。
* - 结构体 :c:type:`v4l2_ctrl_av1_frame`
  - ``p_av1_frame``
  - 指向结构体 :c:type:`v4l2_ctrl_av1_frame` 的指针。如果此控制类型为 ``V4L2_CTRL_TYPE_AV1_FRAME``，则有效。
* - 结构体 :c:type:`v4l2_ctrl_av1_film_grain`
  - ``p_av1_film_grain``
  - 指向结构体 :c:type:`v4l2_ctrl_av1_film_grain` 的指针。如果此控制类型为 ``V4L2_CTRL_TYPE_AV1_FILM_GRAIN``，则有效。
* - 结构体 :c:type:`v4l2_ctrl_hdr10_cll_info`
  - ``p_hdr10_cll_info``
  - 指向结构体 :c:type:`v4l2_ctrl_hdr10_cll_info` 的指针。如果此控制类型为 ``V4L2_CTRL_TYPE_HDR10_CLL_INFO``，则有效。
* - 结构体 :c:type:`v4l2_ctrl_hdr10_mastering_display`
  - ``p_hdr10_mastering_display``
  - 指向结构体 :c:type:`v4l2_ctrl_hdr10_mastering_display` 的指针。如果此控制类型为 ``V4L2_CTRL_TYPE_HDR10_MASTERING_DISPLAY``，则有效。
* - void *
  - ``ptr``
  - 指向复合类型的指针，可以是多维数组和/或复合类型（控制的类型 >= ``V4L2_CTRL_COMPOUND_TYPES``）。如果设置了 ``V4L2_CTRL_FLAG_HAS_PAYLOAD`` 标志，则有效。
* - }
  -

.. raw:: latex

   \normalsize

.. tabularcolumns:: |p{4.0cm}|p{2.5cm}|p{10.8cm}|

.. c:type:: v4l2_ext_controls

.. cssclass:: longtable

.. flat-table:: struct v4l2_ext_controls
    :header-rows:  0
    :stub-columns: 0
    :widths:       1 1 2

    * - union {
      - （匿名）
    * - __u32
      - ``which``
      - 获取/设置/尝试的控制值
```
* - :cspan:`2` `V4L2_CTRL_WHICH_CUR_VAL` 将返回控制项的当前值，`V4L2_CTRL_WHICH_DEF_VAL` 将返回控制项的默认值，而 `V4L2_CTRL_WHICH_REQUEST_VAL` 表示这些控制项需要从请求中获取或为请求尝试/设置。在后一种情况下，`request_fd` 字段包含应使用的请求的文件描述符。如果设备不支持请求，则会返回 `EACCES`。
当使用 `V4L2_CTRL_WHICH_DEF_VAL` 时，请注意只能获取控制项的默认值，不能设置或尝试设置。
为了向后兼容，您也可以在这里使用控制类（参见 :ref:`ctrl-class`）。在这种情况下，所有控制项都必须属于该控制类。这种用法已弃用，建议使用 `V4L2_CTRL_WHICH_CUR_VAL`。有一些非常旧的驱动程序尚不支持 `V4L2_CTRL_WHICH_CUR_VAL` 并且要求在这里使用控制类。可以通过将 `which` 设置为 `V4L2_CTRL_WHICH_CUR_VAL` 并调用 :ref:`VIDIOC_TRY_EXT_CTRLS <VIDIOC_G_EXT_CTRLS>` 来测试此类驱动程序，并将计数设置为 0。
如果调用失败，则表示驱动程序不支持 `V4L2_CTRL_WHICH_CUR_VAL`。

* - __u32
      - `ctrl_class`
      - 保留的废弃名称，用于向后兼容。请改用 `which`。
* - }
      -
    * - __u32
      - `count`
      - 控制项数组中的控制项数量。也可能为零。
* - __u32
      - `error_idx`
      - 失败控制项的索引。在发生错误时由驱动程序设置。
* - :cspan:`2` 如果错误与特定控制项相关，则 `error_idx` 被设置为该控制项的索引。如果错误与特定控制项无关，或者验证步骤失败（参见下文），则 `error_idx` 被设置为 `count`。如果 ioctl 返回 0（成功），则该值是未定义的。
在从硬件读取或写入控制项之前，会进行一个验证步骤：这一步骤检查列表中的所有控制项是否有效，是否有尝试写入只读控制项或从写入专用控制项读取的行为，以及任何其他可以在不访问硬件的情况下执行的前置检查。此步骤中的确切验证取决于驱动程序，因为某些检查可能需要对某些设备进行硬件访问，从而使其无法提前完成。然而，驱动程序应该尽最大努力尽可能多地执行前置检查。
进行此检查是为了避免由于容易避免的问题而导致硬件处于不一致状态。但这导致了另一个问题：应用程序需要知道错误是来自验证步骤（意味着没有触碰硬件）还是来自实际读取或写入硬件时发生的错误。
事后看来，这是一个相当糟糕的解决方案：如果验证失败，则将 `error_idx` 设置为 `count`。不幸的是，这种方法的一个副作用是无法确定哪个控件未能通过验证。如果验证成功但在访问硬件时发生错误，则 `error_idx` 小于 `count`，并且只有从第一个到 `error_idx-1` 的控件被正确读取或写入，其余控件的状态是不确定的。

由于 :ref:`VIDIOC_TRY_EXT_CTRLS <VIDIOC_G_EXT_CTRLS>` 不会访问硬件，因此在这种情况下也不需要以特殊方式处理验证步骤，所以 `error_idx` 将直接设置为未能通过验证的控件，而不是 `count`。这意味着如果 :ref:`VIDIOC_S_EXT_CTRLS <VIDIOC_G_EXT_CTRLS>` 失败且 `error_idx` 被设置为 `count`，则可以调用 :ref:`VIDIOC_TRY_EXT_CTRLS <VIDIOC_G_EXT_CTRLS>` 来尝试发现实际未能通过验证的控件。不幸的是，对于 :ref:`VIDIOC_G_EXT_CTRLS <VIDIOC_G_EXT_CTRLS>` 没有相应的 `TRY` 等价操作。

* - __s32
  - `request_fd`
  - 用于此操作的请求文件描述符。仅当 `which` 设置为 `V4L2_CTRL_WHICH_REQUEST_VAL` 时有效。
如果设备不支持请求，则返回 `EACCES`。
如果支持请求但提供了无效的请求文件描述符，则返回 `EINVAL`。
* - __u32
  - `reserved`[1]
  - 保留用于未来的扩展。
驱动程序和应用程序必须将数组设置为零。
* - struct :c:type:`v4l2_ext_control` *
  - `controls`
  - 指向 `count` 个 `v4l2_ext_control` 结构数组的指针。
如果 `count` 等于零，则忽略此字段。

.. tabularcolumns:: |p{7.3cm}|p{2.0cm}|p{8.0cm}|

.. cssclass:: longtable

.. _ctrl-class:

.. flat-table:: 控制类别
    :header-rows:  0
    :stub-columns: 0
    :widths:       3 1 4

    * - `V4L2_CTRL_CLASS_USER`
      - 0x980000
      - 包含用户控件的类别。这些控件在 :ref:`control` 中描述。所有可以通过 :ref:`VIDIOC_S_CTRL <VIDIOC_G_CTRL>` 和 :ref:`VIDIOC_G_CTRL <VIDIOC_G_CTRL>` ioctl 设置的控件都属于这个类别。
* - ``V4L2_CTRL_CLASS_CODEC``
      - 0x990000
      - 包含状态化编解码器控制的类别。这些控制在 :ref:`codec-controls` 中描述。
* - ``V4L2_CTRL_CLASS_CAMERA``
      - 0x9a0000
      - 包含摄像头控制的类别。这些控制在 :ref:`camera-controls` 中描述。
* - ``V4L2_CTRL_CLASS_FM_TX``
      - 0x9b0000
      - 包含 FM 发射器（FM TX）控制的类别。这些控制在 :ref:`fm-tx-controls` 中描述。
* - ``V4L2_CTRL_CLASS_FLASH``
      - 0x9c0000
      - 包含闪光设备控制的类别。这些控制在 :ref:`flash-controls` 中描述。
* - ``V4L2_CTRL_CLASS_JPEG``
      - 0x9d0000
      - 包含 JPEG 压缩控制的类别。这些控制在 :ref:`jpeg-controls` 中描述。
* - ``V4L2_CTRL_CLASS_IMAGE_SOURCE``
      - 0x9e0000
      - 包含图像源控制的类别。这些控制在 :ref:`image-source-controls` 中描述。
* - ``V4L2_CTRL_CLASS_IMAGE_PROC``
      - 0x9f0000
      - 包含图像处理控制的类别。这些控制在 :ref:`image-process-controls` 中描述。
* - ``V4L2_CTRL_CLASS_FM_RX``
      - 0xa10000
      - 包含 FM 接收器（FM RX）控制的类别。这些控制在 :ref:`fm-rx-controls` 中描述。
* - ``V4L2_CTRL_CLASS_RF_TUNER``
      - 0xa20000
      - 包含 RF 调谐器控制的类别。这些控制在 :ref:`rf-tuner-controls` 中描述。
* - ``V4L2_CTRL_CLASS_DETECT``
      - 0xa30000
      - 包含运动或物体检测控制的类别。这些控制在 :ref:`detect-controls` 中描述。
* - ``V4L2_CTRL_CLASS_CODEC_STATELESS``
      - 0xa40000
      - 包含无状态编解码器控制的类。这些控制项在 :ref:`codec-stateless-controls` 中描述。
* - ``V4L2_CTRL_CLASS_COLORIMETRY``
      - 0xa50000
      - 包含色度控制的类。这些控制项在 :ref:`colorimetry-controls` 中描述。

返回值
======

成功时返回 0，出错时返回 -1 并且设置相应的 ``errno`` 变量。通用错误代码在 :ref:`Generic Error Codes <gen-errors>` 章节中描述。

EINVAL
    结构体 :c:type:`v4l2_ext_control` 的 ``id`` 无效，或者结构体 :c:type:`v4l2_ext_controls` 的 ``which`` 无效，或者结构体 :c:type:`v4l2_ext_control` 的 ``value`` 不合适（例如给定的菜单索引不被驱动支持），或者 ``which`` 字段设置为 ``V4L2_CTRL_WHICH_REQUEST_VAL`` 但给定的 ``request_fd`` 无效或 ``V4L2_CTRL_WHICH_REQUEST_VAL`` 不被内核支持。
    此错误代码还可能由 :ref:`VIDIOC_S_EXT_CTRLS <VIDIOC_G_EXT_CTRLS>` 和 :ref:`VIDIOC_TRY_EXT_CTRLS <VIDIOC_G_EXT_CTRLS>` ioctl 在两个或多个控制值冲突时返回。

ERANGE
    结构体 :c:type:`v4l2_ext_control` 的 ``value`` 超出了范围。

EBUSY
    控制暂时不可更改，可能是因为另一个应用程序接管了此控制所属设备功能的控制权，或者是（如果 ``which`` 字段设置为 ``V4L2_CTRL_WHICH_REQUEST_VAL``）请求已排队但尚未完成。

ENOSPC
    为控制的有效负载预留的空间不足。字段 ``size`` 设置为足以存储有效负载的值，并返回此错误代码。

EACCES
    尝试尝试或设置只读控制项，或者获取写入专用控制项，或者从尚未完成的请求中获取控制项。
    或者 ``which`` 字段设置为 ``V4L2_CTRL_WHICH_REQUEST_VAL`` 但设备不支持请求。
或者，如果尝试设置一个非活动的控件，而驱动程序无法将新值缓存到该控件再次变为活动状态时为止。
