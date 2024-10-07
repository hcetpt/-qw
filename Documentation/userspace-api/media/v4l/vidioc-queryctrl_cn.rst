SPDX 许可声明标识符: GFDL-1.1-no-invariants-or-later

.. c:namespace:: V4L

.. _VIDIOC_QUERYCTRL:

*******************************************************************
ioctl 命令 VIDIOC_QUERYCTRL、VIDIOC_QUERY_EXT_CTRL 和 VIDIOC_QUERYMENU
*******************************************************************

名称
====

VIDIOC_QUERYCTRL - VIDIOC_QUERY_EXT_CTRL - VIDIOC_QUERYMENU - 列出控制项和菜单控制项

概要
========

``int ioctl(int fd, int VIDIOC_QUERYCTRL, struct v4l2_queryctrl *argp)``

.. c:macro:: VIDIOC_QUERY_EXT_CTRL

``int ioctl(int fd, VIDIOC_QUERY_EXT_CTRL, struct v4l2_query_ext_ctrl *argp)``

.. c:macro:: VIDIOC_QUERYMENU

``int ioctl(int fd, VIDIOC_QUERYMENU, struct v4l2_querymenu *argp)``

参数
=========

``fd``
    由 :c:func:`open()` 返回的文件描述符
``argp``
    指向结构体 :c:type:`v4l2_queryctrl`、:c:type:`v4l2_query_ext_ctrl` 或 :c:type:`v4l2_querymenu` 的指针（取决于 ioctl）

描述
===========

为了查询一个控制项的属性，应用程序需要设置结构体 :ref:`v4l2_queryctrl <v4l2-queryctrl>` 的 ``id`` 字段，并使用指向该结构体的指针调用 ``VIDIOC_QUERYCTRL`` ioctl。驱动程序会填充结构体的其余部分，如果 ``id`` 无效则返回 ``EINVAL`` 错误码。
可以通过从 ``V4L2_CID_BASE`` 开始递增 ``id`` 直到 ``V4L2_CID_LASTP1``（不包括）来枚举控制项。如果在该范围内某个控制项不受支持，驱动程序可能会返回 ``EINVAL``。此外，应用程序还可以通过从 ``V4L2_CID_PRIVATE_BASE`` 开始递增 ``id`` 直到驱动程序返回 ``EINVAL`` 来枚举私有控制项。
在这两种情况下，当驱动程序在 ``flags`` 字段中设置了 ``V4L2_CTRL_FLAG_DISABLED`` 标志时，表示该控制项被永久禁用，应用程序应忽略它。[#f1]_

当应用程序将 ``id`` 与 ``V4L2_CTRL_FLAG_NEXT_CTRL`` 进行 OR 操作时，驱动程序会返回下一个受支持的非复合控制项，如果没有则返回 ``EINVAL``。此外，可以指定 ``V4L2_CTRL_FLAG_NEXT_COMPOUND`` 标志来枚举所有复合控制项（即类型大于等于 ``V4L2_CTRL_COMPOUND_TYPES`` 的控制项或数组控制项）。同时指定 ``V4L2_CTRL_FLAG_NEXT_CTRL`` 和 ``V4L2_CTRL_FLAG_NEXT_COMPOUND`` 可以枚举所有控制项，无论是否为复合控制项。目前不支持这些标志的驱动程序始终返回 ``EINVAL``。
``VIDIOC_QUERY_EXT_CTRL`` ioctl 的引入是为了更好地支持可以使用复合类型的控制项，并且可以暴露无法通过结构体 :ref:`v4l2_queryctrl <v4l2-queryctrl>` 返回的额外控制信息，因为该结构体已满。
``VIDIOC_QUERY_EXT_CTRL`` 的使用方式与 ``VIDIOC_QUERYCTRL`` 相同，只是需要将 ``reserved`` 数组也置零。
对于菜单控制项，还需要额外的信息：菜单项的名称。为此，应用程序需要设置结构体 :ref:`v4l2_querymenu <v4l2-querymenu>` 的 ``id`` 和 ``index`` 字段，并使用指向该结构体的指针调用 ``VIDIOC_QUERYMENU`` ioctl。驱动程序会填充结构体的其余部分，如果 ``id`` 或 ``index`` 无效则返回 ``EINVAL`` 错误码。通过从结构体 :ref:`v4l2_queryctrl <v4l2-queryctrl>` 的 ``minimum`` 到 ``maximum``（包括）递增 ``index`` 值来枚举菜单项。
.. note::

   在某些情况下，``VIDIOC_QUERYMENU`` 可能会为 ``minimum`` 和 ``maximum`` 之间的某些索引返回 ``EINVAL`` 错误码。在这种情况下，该特定菜单项不受此驱动程序支持。请注意，``minimum`` 值不一定为 0。

参见 :ref:`control` 中的示例。
```markdown
.. tabularcolumns:: |p{1.2cm}|p{3.6cm}|p{12.5cm}|

.. _v4l2-queryctrl:

.. cssclass:: longtable

.. flat-table:: 结构体 v4l2_queryctrl
    :header-rows:  0
    :stub-columns: 0
    :widths:       1 1 2

    * - __u32
      - ``id``
      - 用于标识控制，由应用程序设置。参见 :ref:`control-id` 获取预定义的ID。当ID与V4L2_CTRL_FLAG_NEXT_CTRL进行按位或操作时，驱动程序会清除该标志并返回具有更高ID的第一个控制。不支持此标志的驱动程序将始终返回 ``EINVAL`` 错误代码。
    * - __u32
      - ``type``
      - 控制类型，参见 :c:type:`v4l2_ctrl_type`
    * - __u8
      - ``name``\ [32]
      - 控制名称，一个以NUL结尾的ASCII字符串。此信息旨在供用户使用。
    * - __s32
      - ``minimum``
      - 最小值（包含）。此字段给出了控制的下限。参见枚举 :c:type:`v4l2_ctrl_type` 了解如何为每种可能的控制类型使用最小值。
注意这是一个带符号的32位值。
    * - __s32
      - ``maximum``
      - 最大值（包含）。此字段给出了控制的上限。参见枚举 :c:type:`v4l2_ctrl_type` 了解如何为每种可能的控制类型使用最大值。
注意这是一个带符号的32位值。
    * - __s32
      - ``step``
      - 此字段给出了控制的步长。参见枚举 :c:type:`v4l2_ctrl_type` 了解如何为每种可能的控制类型使用步长值。注意这是一个无符号的32位值。
通常，驱动程序不应缩放硬件控制值。例如，当 ``name`` 或 ``id`` 暗示特定单位而硬件实际上只接受该单位的倍数时，可能需要缩放。如果需要，驱动程序必须确保在缩放时正确舍入值，以免在重复读写周期中累积误差。
此字段给出了实际影响硬件的整数控制的最小变化量。通常在用户通过键盘或GUI按钮而不是滑块更改控制时需要这些信息。例如，当硬件寄存器接受0-511的值而驱动程序报告0-65535时，步长应为128。
```
请注意，尽管有符号，步长值应始终为正。

* - `__s32`
  - ``default_value``
  - `V4L2_CTRL_TYPE_INTEGER`、``_BOOLEAN``、``_BITMASK``、``_MENU`` 或 ``_INTEGER_MENU`` 控制类型的默认值。对其他类型的控制无效。
.. note::
   驱动程序仅在首次加载时将控制重置为其默认值，之后不会重置。
* - `__u32`
  - ``flags``
  - 控制标志，参见 :ref:`control-flags`
* - `__u32`
  - ``reserved``\[2\]
  - 保留以供将来扩展使用。驱动程序必须将数组设置为零。

.. tabularcolumns:: |p{1.2cm}|p{5.5cm}|p{10.6cm}|

.. _v4l2-query-ext-ctrl:

.. cssclass:: longtable

.. flat-table:: struct v4l2_query_ext_ctrl
    :header-rows:  0
    :stub-columns: 0
    :widths:       1 1 2

    * - `__u32`
      - ``id``
      - 标识控制项，由应用程序设置。参见 :ref:`control-id` 获取预定义的ID。当ID与 ``V4L2_CTRL_FLAG_NEXT_CTRL`` 进行OR运算时，驱动程序清除该标志并返回具有更高ID的第一个非复合控制项。当ID与 ``V4L2_CTRL_FLAG_NEXT_COMPOUND`` 进行OR运算时，驱动程序清除该标志并返回具有更高ID的第一个复合控制项。同时设置两者以获取具有更高ID的第一个控制项（复合或非复合）。
* - `__u32`
  - ``type``
  - 控制类型，参见 :c:type:`v4l2_ctrl_type`
* - char
  - ``name``\[32\]
  - 控制名称，一个NUL终止的ASCII字符串。此信息旨在供用户使用。
* - `__s64`
  - ``minimum``
  - 最小值，包含在内。该字段给出了控制的下限。参见枚举 :c:type:`v4l2_ctrl_type` 了解如何为每种可能的控制类型使用最小值。
请注意，这是一个带符号的64位值
* - __s64
      - ``maximum``
      - 最大值（包含）。此字段给出了控制项的上限。参见枚举 :c:type:`v4l2_ctrl_type` 以了解如何为每种可能的控制类型使用最大值。
请注意，这是一个带符号的64位值
* - __u64
      - ``step``
      - 此字段给出了控制项的步长。参见枚举 :c:type:`v4l2_ctrl_type` 以了解如何为每种可能的控制类型使用步长值。请注意，这是一个无符号的64位值。
通常驱动程序不应缩放硬件控制值。例如，当 `name` 或 `id` 暗示了特定单位而硬件实际上只接受该单位的倍数时，可能需要这样做。如果是这样，驱动程序必须在缩放时确保值被正确舍入，以防止在重复读写周期中累积错误。
此字段给出了整数控制项实际影响硬件的最小变化量。当用户通过键盘或图形界面按钮而不是滑块来更改控制项时，通常需要这些信息。例如，如果硬件寄存器接受0到511的值而驱动程序报告0到65535，则步长应为128。
* - __s64
      - ``default_value``
      - `V4L2_CTRL_TYPE_INTEGER`、`_INTEGER64`、`_BOOLEAN`、`_BITMASK`、`_MENU`、`_INTEGER_MENU`、`_U8` 或 `_U16` 控制类型的默认值。对于其他类型的控制无效。
.. note::
   驱动程序仅在首次加载时将控制项重置为其默认值，之后永远不会重置。
* - __u32
      - ``flags``
      - 控制标志，参见 :ref:`control-flags`
* - __u32
      - ``elem_size``
      - 数组中单个元素的字节大小。给定一个指向三维数组的字符指针 `p`，可以通过以下方式找到单元格 `(z, y, x)` 的位置：
      ``p + ((z * dims[1] + y) * dims[0] + x) * elem_size``
``elem_size`` 总是有效的，即使控件不是一个数组。对于字符串控件，``elem_size`` 等于 ``maximum + 1``。

* - __u32
      - ``elems``
      - N 维数组中的元素数量。如果此控件不是一个数组，则 ``elems`` 为 1。``elems`` 字段永远不能为 0。
* - __u32
      - ``nr_of_dims``
      - N 维数组的维度数量。如果此控件不是一个数组，则该字段为 0。
* - __u32
      - ``dims[V4L2_CTRL_MAX_DIMS]``
      - 每个维度的大小。此数组的前 ``nr_of_dims`` 个元素必须非零，所有剩余元素必须为零。
* - __u32
      - ``reserved``[32]
      - 保留用于未来的扩展。应用程序和驱动程序必须将此数组设为零。

.. tabularcolumns:: |p{1.2cm}|p{3.0cm}|p{13.1cm}|

.. _v4l2-querymenu:

.. flat-table:: struct v4l2_querymenu
    :header-rows:  0
    :stub-columns: 0
    :widths:       1 1 2

    * - __u32
      - ``id``
      - 标识控件，由应用程序从相应的 :ref:`v4l2_queryctrl <v4l2-queryctrl>` 的 ``id`` 设置。
* - __u32
      - ``index``
      - 菜单项的索引，从零开始，由应用程序设置。
* - union {
      - (匿名)
    * - __u8
      - ``name``[32]
      - 菜单项的名称，一个以 NUL 结尾的 ASCII 字符串。此信息旨在供用户使用。此字段对 ``V4L2_CTRL_TYPE_MENU`` 类型控件有效。
* - __s64
      - ``value``
      - 整数菜单项的值。此字段对 ``V4L2_CTRL_TYPE_INTEGER_MENU`` 类型控件有效。
* - }
      -
    * - __u32
      - ``reserved``
      - 保留用于未来的扩展。驱动程序必须将此数组设为零。
```markdown
.. c:type:: v4l2_ctrl_type

.. raw:: latex

   \footnotesize

.. tabularcolumns:: |p{6.5cm}|p{1.5cm}|p{1.1cm}|p{1.5cm}|p{6.8cm}|

.. cssclass:: longtable

.. flat-table:: 枚举 v4l2_ctrl_type
    :header-rows:  1
    :stub-columns: 0
    :widths:       30 5 5 5 55

    * - 类型
      - 最小值
      - 步长
      - 最大值
      - 描述
    * - ``V4L2_CTRL_TYPE_INTEGER``
      - 任意
      - 任意
      - 任意
      - 一个整数值的控制，范围从最小值到最大值（包括）。步长值表示值之间的增量。
    * - ``V4L2_CTRL_TYPE_BOOLEAN``
      - 0
      - 1
      - 1
      - 一个布尔值控制。零表示“禁用”，一表示“启用”。
    * - ``V4L2_CTRL_TYPE_MENU``
      - ≥ 0
      - 1
      - N-1
      - 控制具有N个选项的菜单。可以通过 ``VIDIOC_QUERYMENU`` ioctl 列出菜单项名称。
    * - ``V4L2_CTRL_TYPE_INTEGER_MENU``
      - ≥ 0
      - 1
      - N-1
      - 控制具有N个选项的菜单。可以通过 ``VIDIOC_QUERYMENU`` ioctl 列出菜单项的值。这类似于 ``V4L2_CTRL_TYPE_MENU``，不同之处在于菜单项是带符号的64位整数而不是字符串。
    * - ``V4L2_CTRL_TYPE_BITMASK``
      - 0
      - 不适用
      - 任意
      - 一个位字段。最大值是可使用的位集，其他所有位应为0。最大值被解释为 __u32，允许在位掩码中使用第31位。
    * - ``V4L2_CTRL_TYPE_BUTTON``
      - 0
      - 0
      - 0
      - 当设置时执行操作的控制。驱动程序必须忽略通过 ``VIDIOC_S_CTRL`` 传递的值，并在尝试 ``VIDIOC_G_CTRL`` 时返回 ``EACCES`` 错误代码。
    * - ``V4L2_CTRL_TYPE_INTEGER64``
      - 任意
      - 任意
      - 任意
      - 一个64位整数值的控制。最小值、最大值和步长大小不能通过 ``VIDIOC_QUERYCTRL`` 查询。只有 ``VIDIOC_QUERY_EXT_CTRL`` 才能检索64位最小值/最大值/步长值，在使用 ``VIDIOC_QUERYCTRL`` 时应将其视为不适用。
    * - ``V4L2_CTRL_TYPE_STRING``
      - ≥ 0
      - ≥ 1
      - ≥ 0
      - 字符串长度的最小值和最大值。步长大小意味着字符串必须为 (最小值 + N * 步长) 长度，其中 N ≥ 0。这些长度不包括终止零，因此为了将长度为8的字符串传递给 :ref:`VIDIOC_S_EXT_CTRLS <VIDIOC_G_EXT_CTRLS>`，你需要将 ``size`` 字段设置为9。对于 :ref:`VIDIOC_G_EXT_CTRLS <VIDIOC_G_EXT_CTRLS>`，你可以将 ``size`` 字段设置为 ``maximum`` + 1。所使用的字符编码取决于字符串控制本身，并且应该是控制文档的一部分。
    * - ``V4L2_CTRL_TYPE_CTRL_CLASS``
      - 不适用
      - 不适用
      - 不适用
      - 这不是一个控制。当通过等于控制类代码（参见 :ref:`ctrl-class`）+ 1 的控制ID调用 ``VIDIOC_QUERYCTRL`` 时，ioctl 返回控制类的名称和此控制类型。不支持此功能的旧驱动程序会返回 ``EINVAL`` 错误代码。
```
* - ``V4L2_CTRL_TYPE_U8``
      - 任意
      - 任意
      - 任意
      - 一个无符号的8位值控制，范围从最小值到最大值（包括两端）。步长值表示值之间的增量。
* - ``V4L2_CTRL_TYPE_U16``
      - 任意
      - 任意
      - 任意
      - 一个无符号的16位值控制，范围从最小值到最大值（包括两端）。步长值表示值之间的增量。
* - ``V4L2_CTRL_TYPE_U32``
      - 任意
      - 任意
      - 任意
      - 一个无符号的32位值控制，范围从最小值到最大值（包括两端）。步长值表示值之间的增量。
* - ``V4L2_CTRL_TYPE_MPEG2_QUANTISATION``
      - 不适用
      - 不适用
      - 不适用
      - 一个结构体 :c:type:`v4l2_ctrl_mpeg2_quantisation`，包含用于无状态视频解码器的MPEG-2量化矩阵。
* - ``V4L2_CTRL_TYPE_MPEG2_SEQUENCE``
      - 不适用
      - 不适用
      - 不适用
      - 一个结构体 :c:type:`v4l2_ctrl_mpeg2_sequence`，包含用于无状态视频解码器的MPEG-2序列参数。
* - ``V4L2_CTRL_TYPE_MPEG2_PICTURE``
      - 不适用
      - 不适用
      - 不适用
      - 一个结构体 :c:type:`v4l2_ctrl_mpeg2_picture`，包含用于无状态视频解码器的MPEG-2图像参数。
* - ``V4L2_CTRL_TYPE_AREA``
      - 不适用
      - 不适用
      - 不适用
      - 一个结构体 :c:type:`v4l2_area`，包含矩形区域的宽度和高度。单位取决于使用场景。
* - ``V4L2_CTRL_TYPE_H264_SPS``
      - 不适用
      - 不适用
      - 不适用
      - 一个结构体 :c:type:`v4l2_ctrl_h264_sps`，包含用于无状态视频解码器的H264序列参数。
* - ``V4L2_CTRL_TYPE_H264_PPS``
      - 不适用
      - 不适用
      - 不适用
      - 一个结构体 :c:type:`v4l2_ctrl_h264_pps`，包含用于无状态视频解码器的H264图像参数。
* - ``V4L2_CTRL_TYPE_H264_SCALING_MATRIX``
      - 不适用
      - 不适用
      - 不适用
      - 一个结构体 :c:type:`v4l2_ctrl_h264_scaling_matrix`，包含用于无状态视频解码器的H264缩放矩阵。
* - ``V4L2_CTRL_TYPE_H264_SLICE_PARAMS``
      - 无
      - 无
      - 无
      - 一个结构体 :c:type:`v4l2_ctrl_h264_slice_params`，包含用于无状态视频解码器的H264片参数
* - ``V4L2_CTRL_TYPE_H264_DECODE_PARAMS``
      - 无
      - 无
      - 无
      - 一个结构体 :c:type:`v4l2_ctrl_h264_decode_params`，包含用于无状态视频解码器的H264解码参数
* - ``V4L2_CTRL_TYPE_FWHT_PARAMS``
      - 无
      - 无
      - 无
      - 一个结构体 :c:type:`v4l2_ctrl_fwht_params`，包含用于无状态视频解码器的FWHT参数
* - ``V4L2_CTRL_TYPE_HEVC_SPS``
      - 无
      - 无
      - 无
      - 一个结构体 :c:type:`v4l2_ctrl_hevc_sps`，包含用于无状态视频解码器的HEVC序列参数集
* - ``V4L2_CTRL_TYPE_HEVC_PPS``
      - 无
      - 无
      - 无
      - 一个结构体 :c:type:`v4l2_ctrl_hevc_pps`，包含用于无状态视频解码器的HEVC图像参数集
* - ``V4L2_CTRL_TYPE_HEVC_SLICE_PARAMS``
      - 无
      - 无
      - 无
      - 一个结构体 :c:type:`v4l2_ctrl_hevc_slice_params`，包含用于无状态视频解码器的HEVC片参数
* - ``V4L2_CTRL_TYPE_HEVC_SCALING_MATRIX``
      - 无
      - 无
      - 无
      - 一个结构体 :c:type:`v4l2_ctrl_hevc_scaling_matrix`，包含用于无状态视频解码器的HEVC缩放矩阵
* - ``V4L2_CTRL_TYPE_VP8_FRAME``
      - 无
      - 无
      - 无
      - 一个结构体 :c:type:`v4l2_ctrl_vp8_frame`，包含用于无状态视频解码器的VP8帧参数
* - ``V4L2_CTRL_TYPE_HEVC_DECODE_PARAMS``
      - 无
      - 无
      - 无
      - 一个结构体 :c:type:`v4l2_ctrl_hevc_decode_params`，包含用于无状态视频解码器的HEVC解码参数
* - ``V4L2_CTRL_TYPE_VP9_COMPRESSED_HDR``
      - 无
      - 无
      - 无
      - 一个结构体 :c:type:`v4l2_ctrl_vp9_compressed_hdr`，包含用于无状态视频解码器的VP9概率更新信息
* - ``V4L2_CTRL_TYPE_VP9_FRAME``
      - n/a
      - n/a
      - n/a
      - 一个 :c:type:`v4l2_ctrl_vp9_frame` 结构体，包含无状态视频解码器的 VP9 帧解码参数
* - ``V4L2_CTRL_TYPE_AV1_SEQUENCE``
      - n/a
      - n/a
      - n/a
      - 一个 :c:type:`v4l2_ctrl_av1_sequence` 结构体，包含无状态视频解码器的 AV1 序列 OBU 解码参数
* - ``V4L2_CTRL_TYPE_AV1_TILE_GROUP_ENTRY``
      - n/a
      - n/a
      - n/a
      - 一个 :c:type:`v4l2_ctrl_av1_tile_group_entry` 结构体，包含无状态视频解码器的 AV1 Tile Group OBU 解码参数
* - ``V4L2_CTRL_TYPE_AV1_FRAME``
      - n/a
      - n/a
      - n/a
      - 一个 :c:type:`v4l2_ctrl_av1_frame` 结构体，包含无状态视频解码器的 AV1 帧/帧头 OBU 解码参数
* - ``V4L2_CTRL_TYPE_AV1_FILM_GRAIN``
      - n/a
      - n/a
      - n/a
      - 一个 :c:type:`v4l2_ctrl_av1_film_grain` 结构体，包含无状态视频解码器的 AV1 影片颗粒参数

.. raw:: latex

   \normalsize

.. tabularcolumns:: |p{7.3cm}|p{1.8cm}|p{8.2cm}|

.. cssclass:: longtable

.. _control-flags:

.. flat-table:: 控制标志
    :header-rows:  0
    :stub-columns: 0
    :widths:       3 1 4

    * - ``V4L2_CTRL_FLAG_DISABLED``
      - 0x0001
      - 此控制项永久禁用，应用程序应忽略。任何尝试更改此控制项的操作将导致 ``EINVAL`` 错误代码
* - ``V4L2_CTRL_FLAG_GRABBED``
      - 0x0002
      - 此控制项暂时不可更改，例如因为其他应用程序接管了相应资源的控制权
此类控制项可以在用户界面中以特殊方式显示
尝试更改此控制项可能导致 ``EBUSY`` 错误代码
* - ``V4L2_CTRL_FLAG_READ_ONLY``
      - 0x0004
      - 此控制项永久只读。任何尝试更改此控制项的操作将导致 ``EINVAL`` 错误代码
* - ``V4L2_CTRL_FLAG_UPDATE``
      - 0x0008
      - 提示更改此控件可能会影响同一控件类中其他控件的值。应用程序应相应地更新其用户界面。
* - ``V4L2_CTRL_FLAG_INACTIVE``
      - 0x0010
      - 此控件不适用于当前配置，应在用户界面中相应显示。例如，当另一个控件选择了MPEG音频编码级别1时，可以在MPEG音频级别2比特率控件上设置此标志。
* - ``V4L2_CTRL_FLAG_SLIDER``
      - 0x0020
      - 提示此控件最好在用户界面中表示为滑块元素。
* - ``V4L2_CTRL_FLAG_WRITE_ONLY``
      - 0x0040
      - 此控件始终只可写。任何读取该控件的尝试都将导致 ``EACCES`` 错误代码。此标志通常用于相对控件或动作控件，其中写入一个值将导致设备执行某个特定操作（例如电机控制），但无法返回有意义的值。
* - ``V4L2_CTRL_FLAG_VOLATILE``
      - 0x0080
      - 此控件是易变的，这意味着该控件的值会持续变化。一个典型的例子是当设备处于自动增益模式时的当前增益值。在这种情况下，硬件根据光照条件计算增益值，这些条件可能会随时间变化。
.. note::

	   如果未设置
	   :ref:`V4L2_CTRL_FLAG_EXECUTE_ON_WRITE <FLAG_EXECUTE_ON_WRITE>`
	   ，则为易变控件设置新值将被忽略。
	   为易变控件设置新值 *永远不会* 触发
	   :ref:`V4L2_EVENT_CTRL_CH_VALUE <ctrl-changes-flags>` 事件。
* - ``V4L2_CTRL_FLAG_HAS_PAYLOAD``
      - 0x0100
      - 此控件具有指针类型，因此需要使用 `v4l2_ext_control` 结构体中的一个指针字段来访问其值。此标志对于数组、字符串或复合类型的控件设置。
所有情况下都必须设置指向包含控件有效负载的内存的指针。
* .. _FLAG_EXECUTE_ON_WRITE:

      - ``V4L2_CTRL_FLAG_EXECUTE_ON_WRITE``
      - 0x0200
      - 即使控件值保持不变，提供的值也将传递给驱动程序。当控件代表硬件上的操作时需要这样做。例如：清除错误标志或触发闪光灯。所有类型为 ``V4L2_CTRL_TYPE_BUTTON`` 的控件都设置了此标志。
* .. _FLAG_MODIFY_LAYOUT:

      - ``V4L2_CTRL_FLAG_MODIFY_LAYOUT``
      - 0x0400
      - 更改此控制值可能会修改缓冲区（对于视频设备）或媒体总线格式（对于子设备）的布局。
        一个典型的例子是 ``V4L2_CID_ROTATE`` 控制。
        注意，通常具有此标志的控制在分配缓冲区或正在进行流传输时也会设置 ``V4L2_CTRL_FLAG_GRABBED`` 标志，
        因为大多数驱动程序不支持在此情况下更改格式。

* - ``V4L2_CTRL_FLAG_DYNAMIC_ARRAY``
      - 0x0800
      - 此控制是一个动态大小的一维数组。它与普通数组的行为相同，不同之处在于通过 ``elems`` 字段报告的元素数量在 1 到 ``dims[0]`` 之间。
        因此，使用不同大小的数组设置控制后，在查询该控制时 ``elems`` 字段将会改变。

返回值
======

成功时返回 0，失败时返回 -1 并且设置 ``errno`` 变量为适当的错误码。通用错误码在
:ref:`通用错误码 <gen-errors>` 章节中有描述。

EINVAL
    结构 :ref:`v4l2_queryctrl <v4l2-queryctrl>` 的 ``id`` 无效。结构 :ref:`v4l2_querymenu <v4l2-querymenu>` 的 ``id`` 无效或 ``index`` 超出范围（小于 ``minimum`` 或大于 ``maximum``），或者此特定菜单项不受驱动程序支持。

EACCES
    尝试读取只写控制。

.. [#f1]
   ``V4L2_CTRL_FLAG_DISABLED`` 的设计目的是为了实现两个功能：驱动程序可以跳过硬件不支持的预定义控制（尽管返回 ``EINVAL`` 也能达到同样的效果），或者在硬件检测后无需重新排序控制数组和索引即可禁用预定义和私有控制（不能使用 ``EINVAL`` 来跳过私有控制，因为这会导致枚举提前结束）。
