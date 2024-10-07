SPDX 许可声明标识符: GFDL-1.1-no-invariants-or-later
.. c:namespace:: V4L

.. _VIDIOC_DQEVENT:

********************
ioctl VIDIOC_DQEVENT
********************

名称
====

VIDIOC_DQEVENT - 取出事件

概要
========

.. c:macro:: VIDIOC_DQEVENT

``int ioctl(int fd, VIDIOC_DQEVENT, struct v4l2_event *argp)``

参数
=========

``fd``
    由 :c:func:`open()` 返回的文件描述符
``argp``
    指向结构体 :c:type:`v4l2_event` 的指针
描述
===========

从视频设备中取出一个事件。此 ioctl 不需要任何输入。所有结构体 :c:type:`v4l2_event` 的字段都由驱动程序填充。文件句柄也会接收异常，应用程序可以通过使用 select 系统调用来获取这些异常。
.. c:type:: v4l2_event

.. tabularcolumns:: |p{3.0cm}|p{3.4cm}|p{10.9cm}|

.. flat-table:: 结构体 v4l2_event
    :header-rows:  0
    :stub-columns: 0
    :widths:       1 1 2

    * - __u32
      - ``type``
      - 事件类型，参见 :ref:`event-type`
    * - union {
      - ``u``
    * - struct :c:type:`v4l2_event_vsync`
      - ``vsync``
      - 事件数据，用于事件 ``V4L2_EVENT_VSYNC``
    * - struct :c:type:`v4l2_event_ctrl`
      - ``ctrl``
      - 事件数据，用于事件 ``V4L2_EVENT_CTRL``
    * - struct :c:type:`v4l2_event_frame_sync`
      - ``frame_sync``
      - 事件数据，用于事件 ``V4L2_EVENT_FRAME_SYNC``
    * - struct :c:type:`v4l2_event_motion_det`
      - ``motion_det``
      - 事件数据，用于事件 ``V4L2_EVENT_MOTION_DET``
    * - struct :c:type:`v4l2_event_src_change`
      - ``src_change``
      - 事件数据，用于事件 ``V4L2_EVENT_SOURCE_CHANGE``
    * - __u8
      - ``data``\ [64]
      - 事件数据。由事件类型定义。联合体应被用于定义易于访问的事件类型。
```markdown
* - __u32
  - ``pending``
  - 待处理事件的数量（不包括当前事件）
* - __u32
  - ``sequence``
  - 事件序列号。每次发生订阅的事件时，序列号会递增。如果序列号不是连续的，则意味着有事件丢失
* - struct timespec
  - ``timestamp``
  - 事件的时间戳。时间戳来自 ``CLOCK_MONOTONIC`` 时钟。要在 V4L2 外部访问相同的时钟，请使用 :c:func:`clock_gettime`
* - u32
  - ``id``
  - 与事件源关联的 ID。如果事件没有关联的 ID（这取决于事件类型），则为 0
* - __u32
  - ``reserved``[8]
  - 预留用于将来扩展。驱动程序必须将数组设置为零

.. tabularcolumns:: |p{6.2cm}|p{2.6cm}|p{8.5cm}|

.. cssclass:: longtable

.. _event-type:

.. flat-table:: 事件类型
    :header-rows:  0
    :stub-columns: 0
    :widths:       3 1 4

    * - ``V4L2_EVENT_ALL``
      - 0
      - 所有事件。V4L2_EVENT_ALL 仅在 VIDIOC_UNSUBSCRIBE_EVENT 中有效，用于一次性取消订阅所有事件
* - ``V4L2_EVENT_VSYNC``
      - 1
      - 此事件在垂直同步时触发。此事件关联一个 struct :c:type:`v4l2_event_vsync`
* - ``V4L2_EVENT_EOS``
      - 2
      - 当达到流的末尾时触发此事件。通常用于 MPEG 解码器，以向应用程序报告 MPEG 流的最后一部分已被解码
* - ``V4L2_EVENT_CTRL``
      - 3
      - 此事件要求 ``id`` 匹配您希望接收事件的控制 ID。当控件的值改变、按钮控件被按下或控件的标志改变时，会触发此事件。此事件关联一个 struct :c:type:`v4l2_event_ctrl`

该结构包含了许多与 struct :ref:`v4l2_queryctrl <v4l2-queryctrl>` 和 struct :c:type:`v4l2_control` 相同的信息
```
如果事件是由调用 :ref:`VIDIOC_S_CTRL <VIDIOC_G_CTRL>` 或 :ref:`VIDIOC_S_EXT_CTRLS <VIDIOC_G_EXT_CTRLS>` 生成的，则该事件 *不会* 发送到调用 ioctl 函数的文件句柄。这样可以防止产生恶性反馈循环。如果您 *确实* 想要获取该事件，请设置 `V4L2_EVENT_SUB_FL_ALLOW_FEEDBACK` 标志。

这种事件类型确保在生成的事件多于内部空间时不会丢失信息。在这种情况下，保留第二个最旧事件的 :c:type:`v4l2_event_ctrl` 结构体，但第二个最旧事件的 `changes` 字段将与最旧事件的 `changes` 字段进行 OR 运算。

* - ``V4L2_EVENT_FRAME_SYNC``
  - 4
  - 当一帧的接收开始时立即触发此事件。
  
  此事件关联了一个 :c:type:`v4l2_event_frame_sync` 结构体。
  
  如果硬件在缓冲区欠溢出的情况下需要停止，则可能无法生成此事件。在这种情况下，:c:type:`v4l2_event_frame_sync` 结构体中的 `frame_sequence` 字段将不会递增。这会导致两个连续的帧序列号之间有 n 倍的帧间隔。
  
* - ``V4L2_EVENT_SOURCE_CHANGE``
  - 5
  - 当视频设备在运行时检测到源参数变化时触发此事件。它可以是视频解码器触发的运行时分辨率变化或输入连接器上的格式变化。此事件要求 `id` 匹配您希望接收事件的输入索引（当用于视频设备节点时）或垫索引（当用于子设备节点时）。
  
  此事件关联了一个 :c:type:`v4l2_event_src_change` 结构体。`changes` 位字段表示所订阅的垫发生了什么变化。如果多个事件在应用程序能够解除队列之前发生，则这些变化将包含所有生成事件的 OR 值。
  
* - ``V4L2_EVENT_MOTION_DET``
  - 6
  - 当一个或多个区域的运动检测状态发生变化时触发此事件。
  
  此事件关联了一个 :c:type:`v4l2_event_motion_det` 结构体。
  
* - ``V4L2_EVENT_PRIVATE_START``
  - 0x08000000
  - 驱动程序私有事件的基础编号。
  
.. tabularcolumns:: |p{4.4cm}|p{4.4cm}|p{8.5cm}|
  
.. c:type:: v4l2_event_vsync
  
.. flat-table:: struct v4l2_event_vsync
    :header-rows:  0
    :stub-columns: 0
    :widths:       1 1 2
    
    * - __u8
      - ``field``
      - 即将到来的场。参见枚举 :c:type:`v4l2_field`
```markdown
.. tabularcolumns:: |p{3.5cm}|p{3.0cm}|p{10.8cm}|

.. c:type:: v4l2_event_ctrl

.. flat-table:: struct v4l2_event_ctrl
    :header-rows:  0
    :stub-columns: 0
    :widths:       1 1 2

    * - __u32
      - ``changes``
      - 一个位标志，表示哪些内容发生了变化。详见
	:ref:`ctrl-changes-flags`
* - __u32
      - ``type``
      - 控制类型。详见枚举
	:c:type:`v4l2_ctrl_type`
* - union {
      - (匿名)
    * - __s32
      - ``value``
      - 对于32位控制类型的32位值。对于字符串控制类型，此值为0，因为无法使用
	:ref:`VIDIOC_DQEVENT` 传递字符串的值
* - __s64
      - ``value64``
      - 对于64位控制类型的64位值
* - }
      -
    * - __u32
      - ``flags``
      - 控制标志。详见 :ref:`control-flags`
* - __s32
      - ``minimum``
      - 控制的最小值。详见结构体
	:ref:`v4l2_queryctrl <v4l2-queryctrl>`
* - __s32
      - ``maximum``
      - 控制的最大值。详见结构体
	:ref:`v4l2_queryctrl <v4l2-queryctrl>`
* - __s32
      - ``step``
      - 控制的步长值。详见结构体
	:ref:`v4l2_queryctrl <v4l2-queryctrl>`
* - __s32
      - ``default_value``
      - 控制的默认值。详见结构体
	:ref:`v4l2_queryctrl <v4l2-queryctrl>`

.. tabularcolumns:: |p{4.4cm}|p{4.4cm}|p{8.5cm}|

.. c:type:: v4l2_event_frame_sync

.. flat-table:: struct v4l2_event_frame_sync
    :header-rows:  0
    :stub-columns: 0
    :widths:       1 1 2

    * - __u32
      - ``frame_sequence``
      - 正在接收的帧的序列号
```
```markdown
.. tabularcolumns:: |p{4.4cm}|p{4.4cm}|p{8.5cm}|

.. c:type:: v4l2_event_src_change

.. flat-table:: 结构体 v4l2_event_src_change
    :header-rows:  0
    :stub-columns: 0
    :widths:       1 1 2

    * - __u32
      - ``changes``
      - 一个位掩码，表示发生了哪些变化。参见 :ref:`src-changes-flags`

.. tabularcolumns:: |p{4.4cm}|p{4.4cm}|p{8.5cm}|

.. c:type:: v4l2_event_motion_det

.. flat-table:: 结构体 v4l2_event_motion_det
    :header-rows:  0
    :stub-columns: 0
    :widths:       1 1 2

    * - __u32
      - ``flags``
      - 目前只有一个标志可用：如果设置了 ``V4L2_EVENT_MD_FL_HAVE_FRAME_SEQ`` 标志，则 ``frame_sequence`` 字段有效，否则该字段应被忽略
    * - __u32
      - ``frame_sequence``
      - 接收到的帧的序列号。仅在设置了 ``V4L2_EVENT_MD_FL_HAVE_FRAME_SEQ`` 标志时有效
    * - __u32
      - ``region_mask``
      - 报告运动的区域的位掩码。至少有一个区域。如果此字段为 0，则表示未检测到任何运动。如果没有 ``V4L2_CID_DETECT_MD_REGION_GRID`` 控制（参见 :ref:`detect-controls`）来为运动检测网格中的每个单元分配不同的区域，则所有单元都会自动分配到默认区域 0

.. tabularcolumns:: |p{6.6cm}|p{2.2cm}|p{8.5cm}|

.. _ctrl-changes-flags:

.. flat-table:: 控制变化
    :header-rows:  0
    :stub-columns: 0
    :widths:       3 1 4

    * - ``V4L2_EVENT_CTRL_CH_VALUE``
      - 0x0001
      - 此控制事件是由控制值的变化触发的。特殊情况：易失性控制不会生成此事件；如果控制具有 ``V4L2_CTRL_FLAG_EXECUTE_ON_WRITE`` 标志，则无论其值如何都会发送此事件
    * - ``V4L2_EVENT_CTRL_CH_FLAGS``
      - 0x0002
      - 此控制事件是由控制标志的变化触发的
    * - ``V4L2_EVENT_CTRL_CH_RANGE``
      - 0x0004
      - 此控制事件是由控制的最小值、最大值、步长或默认值的变化触发的
    * - ``V4L2_EVENT_CTRL_CH_DIMENSIONS``
      - 0x0008
      - 此控制事件是由控制尺寸的变化触发的。请注意，维度的数量保持不变

.. tabularcolumns:: |p{6.6cm}|p{2.2cm}|p{8.5cm}|

.. _src-changes-flags:

.. flat-table:: 源变化
    :header-rows:  0
    :stub-columns: 0
    :widths:       3 1 4

    * - ``V4L2_EVENT_SRC_CH_RESOLUTION``
      - 0x0001
      - 当输入端检测到分辨率变化时会触发此事件。这可能来自输入连接器或视频解码器。应用程序需要查询新的分辨率（如果没有，信号可能已丢失）
对于有状态的解码器，请遵循 :ref:`decoder` 中的指南
```
视频采集设备必须使用 :ref:`VIDIOC_QUERY_DV_TIMINGS` 或 :ref:`VIDIOC_QUERYSTD <VIDIOC_QUERYSTD>` 查询新的时序。

*重要*: 即使新的视频时序看起来与旧的相同，接收到此事件也表明视频信号存在问题，你必须停止并重新开始流传输（:ref:`VIDIOC_STREAMOFF <VIDIOC_STREAMON>` 接着 :ref:`VIDIOC_STREAMON <VIDIOC_STREAMON>`）。原因是许多视频采集设备无法从临时信号丢失中恢复，因此需要重启流I/O操作以使硬件同步到视频信号。

返回值
======

成功时返回0，出错时返回-1，并且设置 ``errno`` 变量为适当的错误码。通用错误码在 :ref:`Generic Error Codes <gen-errors>` 章节中有描述。
