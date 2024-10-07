SPDX 许可声明标识符: GFDL-1.1-no-invariants-or-later
.. c:namespace:: V4L

.. _VIDIOC_G_SELECTION:

********************************************
ioctl VIDIOC_G_SELECTION, VIDIOC_S_SELECTION
********************************************

名称
====

VIDIOC_G_SELECTION - VIDIOC_S_SELECTION - 获取或设置选择矩形之一

概要
========

.. c:macro:: VIDIOC_G_SELECTION

``int ioctl(int fd, VIDIOC_G_SELECTION, struct v4l2_selection *argp)``

.. c:macro:: VIDIOC_S_SELECTION

``int ioctl(int fd, VIDIOC_S_SELECTION, struct v4l2_selection *argp)``

参数
=========

``fd``
    由 :c:func:`open()` 返回的文件描述符
``argp``
    指向结构体 :c:type:`v4l2_selection` 的指针

描述
===========

这些 ioctl 用于查询和配置选择矩形。为了查询裁剪（组合）矩形，需要将结构体 :c:type:`v4l2_selection` 的 ``type`` 字段设置为相应的缓冲区类型。下一步是将结构体 :c:type:`v4l2_selection` 的 ``target`` 字段设置为 ``V4L2_SEL_TGT_CROP``（``V4L2_SEL_TGT_COMPOSE``）。请参阅表 :ref:`v4l2-selections-common` 或 :ref:`selection-api` 获取其他目标。结构体 :c:type:`v4l2_selection` 的 ``flags`` 和 ``reserved`` 字段会被忽略，并且必须用零填充。如果使用了不正确的缓冲区类型或目标，则驱动程序会填写其余部分或者返回 EINVAL 错误码。如果不支持裁剪（组合），则活动矩形不可更改，并且始终等于边界矩形。最后，结构体 :c:type:`v4l2_rect` 的 ``r`` 矩形将被填充当前裁剪（组合）坐标。坐标以驱动程序依赖的单位表示。唯一例外是原始格式图像的矩形，其坐标始终以像素为单位。

为了更改裁剪（组合）矩形，需要将结构体 :c:type:`v4l2_selection` 的 ``type`` 字段设置为相应的缓冲区类型。下一步是将结构体 :c:type:`v4l2_selection` 的 ``target`` 设置为 ``V4L2_SEL_TGT_CROP``（``V4L2_SEL_TGT_COMPOSE``）。请参阅表 :ref:`v4l2-selections-common` 或 :ref:`selection-api` 获取其他目标。结构体 :c:type:`v4l2_rect` 的 ``r`` 矩形需要设置为所需的活动区域。结构体 :c:type:`v4l2_selection` 的 ``reserved`` 字段被忽略，并且必须用零填充。驱动程序可能会调整请求矩形的坐标。应用程序可以引入约束来控制舍入行为。结构体 :c:type:`v4l2_selection` 的 ``flags`` 字段必须设置为以下之一：

-  ``0`` - 驱动程序可以自由调整矩形大小，并应选择尽可能接近请求的裁剪/组合矩形
-  ``V4L2_SEL_FLAG_GE`` - 驱动程序不允许缩小矩形。原始矩形必须位于调整后的矩形内
-  ``V4L2_SEL_FLAG_LE`` - 驱动程序不允许扩大矩形。调整后的矩形必须位于原始矩形内
-  ``V4L2_SEL_FLAG_GE | V4L2_SEL_FLAG_LE`` - 驱动程序必须选择与请求矩形完全相同的大小
请参阅 :ref:`sel-const-adjust`

驱动程序可能需要根据硬件限制和其他管道部分（例如捕获/输出窗口或电视显示）调整请求的尺寸。根据以下优先级选择尽可能接近的水平和垂直偏移量和尺寸：

1. 满足结构体 :c:type:`v4l2_selection` 中 ``flags`` 的约束
2. 调整宽度、高度、左边界和顶边界以符合硬件限制和对齐要求。
3. 尽可能保持调整后的矩形中心与原始矩形中心接近。
4. 尽可能保持宽度和高度接近原始值。
5. 尽可能保持水平和垂直偏移接近原始值。

成功时，结构体 :c:type:`v4l2_rect` 的 ``r`` 字段将包含调整后的矩形。如果参数不合适，应用程序可以修改裁剪（组合）或图像参数，并重复此过程直到协商出满意的参数。如果必须违反约束标志，则返回 ``ERANGE``。该错误表示 *不存在满足这些约束的矩形*。

选择目标和标志在 :ref:`v4l2-selections-common` 中有详细说明。

.. _sel-const-adjust:

.. kernel-figure:: constraints.svg
    :alt: constraints.svg
    :align: center

    带有约束标志的尺寸调整
不同约束标志下矩形调整的行为

.. c:type:: v4l2_selection

.. tabularcolumns:: |p{4.4cm}|p{4.4cm}|p{8.5cm}|

.. flat-table:: struct v4l2_selection
    :header-rows: 0
    :stub-columns: 0
    :widths: 1 1 2

    * - __u32
      - ``type``
      - 缓冲区类型（来自枚举 :c:type:`v4l2_buf_type`）
    * - __u32
      - ``target``
      - 用于选择裁剪和组合矩形之间的区别（参见 :ref:`v4l2-selections-common`）
* - `__u32`
  - `flags`
  - 控制选择矩形调整的标志，参考 :ref:`选择标志 <v4l2-selection-flags>`
* - `struct :c:type:'v4l2_rect'`
  - `r`
  - 选择矩形
* - `__u32`
  - `reserved[9]`
  - 保留字段，供将来使用。驱动程序和应用程序必须将此数组清零

.. note::
   不幸的是，在多平面缓冲类型（如 `V4L2_BUF_TYPE_VIDEO_CAPTURE_MPLANE` 和 `V4L2_BUF_TYPE_VIDEO_OUTPUT_MPLANE`）的情况下，关于如何填写 :c:type:`v4l2_selection` 的 `type` 字段，API 出现了混乱。一些驱动程序只接受 `_MPLANE` 缓冲类型，而其他驱动程序只接受非多平面缓冲类型（即不包含 `_MPLANE` 的类型）。
   
   从内核 4.13 开始，两种变体都被允许。

返回值
======
成功时返回 0，失败时返回 -1，并设置 `errno` 变量。通用错误代码在 :ref:`通用错误代码 <gen-errors>` 章节中描述。

EINVAL
  给定的缓冲类型 `type` 或选择目标 `target` 不被支持，或者 `flags` 参数无效
ERANGE
  无法调整 `struct :c:type:'v4l2_rect'` 的 `r` 矩形以满足 `flags` 参数中给定的所有约束条件
ENODATA
  对于此输入或输出不支持选择
EBUSY
  当前无法应用选择矩形的更改。通常是因为流正在进行中
当然，请提供您需要翻译的文本。
