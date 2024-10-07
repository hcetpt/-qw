.. SPDX 许可证标识符: GFDL-1.1-no-invariants-or-later
.. c:namespace:: V4L

.. _VIDIOC_ENUMINPUT:

**********************
ioctl VIDIOC_ENUMINPUT
**********************

名称
====

VIDIOC_ENUMINPUT - 列出视频输入

概要
====

.. c:macro:: VIDIOC_ENUMINPUT

``int ioctl(int fd, VIDIOC_ENUMINPUT, struct v4l2_input *argp)``

参数
====

``fd``
    由 :c:func:`open()` 返回的文件描述符
``argp``
    指向 :c:type:`v4l2_input` 结构体的指针
描述
====

为了查询视频输入的属性，应用程序需要初始化结构体 :c:type:`v4l2_input` 的 ``index`` 字段，并通过指向该结构体的指针调用 :ref:`VIDIOC_ENUMINPUT`。驱动程序会填充结构体的其余部分，或者当索引超出范围时返回一个 ``EINVAL`` 错误码。为了列出所有输入，应用程序应当从索引 0 开始逐个递增，直到驱动程序返回 ``EINVAL``。

.. tabularcolumns:: |p{3.0cm}|p{3.5cm}|p{10.8cm}|

.. c:type:: v4l2_input

.. flat-table:: struct v4l2_input
    :header-rows:  0
    :stub-columns: 0
    :widths:       1 1 2

    * - __u32
      - ``index``
      - 标识输入，由应用程序设置
    * - __u8
      - ``name``\[32\]
      - 视频输入的名称，是一个以 NUL 结尾的 ASCII 字符串，例如："Vin (Composite 2)"。此信息旨在供用户查看，最好是设备上的连接器标签
    * - __u32
      - ``type``
      - 输入类型，参见 :ref:`input-type`
    * - __u32
      - ``audioset``
      - 驱动程序可以枚举最多 32 个视频和音频输入。此字段显示如果当前选择了该视频输入，则可以选择哪些音频输入作为音频源。这是一个位掩码。最低有效位（LSB）对应音频输入 0，最高有效位（MSB）对应输入 31。可以设置任意数量的位，也可以不设置任何位。
      当驱动程序不枚举音频输入时，不应设置任何位。应用程序不应将此解释为缺乏音频支持。一些驱动程序自动选择音频源，并且由于没有选择余地而不枚举它们。
      有关音频输入及其选择方式的详细信息，请参见 :ref:`audio`
    * - __u32
      - ``tuner``
      - 捕获设备可以有零个或多个调谐器（射频解调器）
当 `类型` 设置为 `V4L2_INPUT_TYPE_TUNER` 时，这是一个 RF 连接器，并且此字段标识调谐器。它对应于结构体 `v4l2_tuner` 中的字段 `index`。有关调谐器的详细信息，请参阅 :ref:`tuner`。

* - :ref:`v4l2_std_id <v4l2-std-id>`
  - `std`
  - 每个视频输入支持一种或多种不同的视频标准。此字段是一组所有支持的标准。有关视频标准及其切换方式的详细信息，请参阅 :ref:`standard`。
* - __u32
  - `status`
  - 此字段提供关于输入的状态信息。请参阅 :ref:`input-status` 了解标志。除了传感器方向位之外，只有在当前输入时 `status` 才有效。
* - __u32
  - `capabilities`
  - 此字段提供输入的功能。请参阅 :ref:`input-capabilities` 了解标志。
* - __u32
  - `reserved`[3]
  - 保留用于将来扩展。驱动程序必须将数组设置为零。

.. tabularcolumns:: |p{6.6cm}|p{1.0cm}|p{9.7cm}|

.. _input-type:

.. flat-table:: 输入类型
    :header-rows:  0
    :stub-columns: 0
    :widths:       3 1 4

    * - `V4L2_INPUT_TYPE_TUNER`
      - 1
      - 此输入使用一个调谐器（RF 解调器）
* - `V4L2_INPUT_TYPE_CAMERA`
      - 2
      - 任何非调谐器视频输入，例如复合视频、S-Video、HDMI、相机传感器。将其命名为 `_TYPE_CAMERA` 是历史遗留，今天我们会称之为 `_TYPE_VIDEO`。
* - `V4L2_INPUT_TYPE_TOUCH`
      - 3
      - 此输入是一个用于捕获原始触摸数据的触摸设备

.. tabularcolumns:: |p{5.6cm}|p{2.6cm}|p{9.1cm}|

.. _input-status:

.. flat-table:: 输入状态标志
    :header-rows:  0
    :stub-columns: 0

    * - :cspan:`2` 通用
    * - `V4L2_IN_ST_NO_POWER`
      - 0x00000001
      - 附接的设备已关闭
* - ``V4L2_IN_ST_NO_SIGNAL``
      - 0x00000002
      -
* - ``V4L2_IN_ST_NO_COLOR``
      - 0x00000004
      - 硬件支持颜色解码，但未检测到信号中的颜色调制

* - :cspan:`2` 传感器方向
    * - ``V4L2_IN_ST_HFLIP``
      - 0x00000010
      - 输入连接到了一个产生水平翻转信号的设备，并且在将信号传递给用户空间之前不进行校正
* - ``V4L2_IN_ST_VFLIP``
      - 0x00000020
      - 输入连接到了一个产生垂直翻转信号的设备，并且在将信号传递给用户空间之前不进行校正
.. note:: 180度旋转等同于 HFLIP | VFLIP
    * - :cspan:`2` 模拟视频
    * - ``V4L2_IN_ST_NO_H_LOCK``
      - 0x00000100
      - 无水平同步锁定
* - ``V4L2_IN_ST_COLOR_KILL``
      - 0x00000200
      - 当检测到没有颜色调制时，自动禁用颜色解码。当设置此标志时，表示颜色杀手电路已启用并且关闭了颜色解码
* - ``V4L2_IN_ST_NO_V_LOCK``
      - 0x00000400
      - 无垂直同步锁定
* - ``V4L2_IN_ST_NO_STD_LOCK``
      - 0x00000800
      - 在组件自动检测格式的情况下，无标准格式锁定
* - :cspan:`2` 数字视频
    * - ``V4L2_IN_ST_NO_SYNC``
      - 0x00010000
      - 无同步锁定
* - ``V4L2_IN_ST_NO_EQU``
      - 0x00020000
      - 无均衡器锁定
* - ``V4L2_IN_ST_NO_CARRIER``
      - 0x00040000
      - 载波恢复失败
* - `cspan:2` 视频录制机和机顶盒
    * - ``V4L2_IN_ST_MACROVISION``
      - 0x01000000
      - Macrovision 是一种模拟复制防护系统，通过扭曲视频信号以使录像设备困惑。当设置此标志时，表示已检测到 Macrovision。
    * - ``V4L2_IN_ST_NO_ACCESS``
      - 0x02000000
      - 条件访问被拒绝。
    * - ``V4L2_IN_ST_VTR``
      - 0x04000000
      - VTR 时间常数。[?]

.. tabularcolumns:: |p{6.6cm}|p{2.4cm}|p{8.3cm}|

.. _input-capabilities:

.. flat-table:: 输入功能
    :header-rows:  0
    :stub-columns: 0
    :widths:       3 1 4

    * - ``V4L2_IN_CAP_DV_TIMINGS``
      - 0x00000002
      - 此输入支持通过使用 ``VIDIOC_S_DV_TIMINGS`` 设置视频时序。
    * - ``V4L2_IN_CAP_STD``
      - 0x00000004
      - 此输入支持通过使用 ``VIDIOC_S_STD`` 设置电视标准。
    * - ``V4L2_IN_CAP_NATIVE_SIZE``
      - 0x00000008
      - 此输入支持使用选择目标 ``V4L2_SEL_TGT_NATIVE_SIZE`` 设置原生尺寸，详见 :ref:`v4l2-selections-common`。

返回值
======

成功时返回 0，出错时返回 -1 并且设置 ``errno`` 变量为适当的错误码。通用错误码在 :ref:`Generic Error Codes <gen-errors>` 章节中描述。

EINVAL
    结构体 :c:type:`v4l2_input` 的 ``index`` 超出了范围。
