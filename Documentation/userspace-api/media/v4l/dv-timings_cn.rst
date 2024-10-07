SPDX 许可声明标识符: GFDL-1.1 或更高无不变性条款

.. _dv-timings:

**************************
数字视频（DV）时序
**************************

到目前为止讨论的视频标准主要涉及模拟电视及其对应的视频时序。如今，有许多不同的硬件接口，如高清晰度电视接口（HDMI）、VGA、DVI 连接器等，它们传输视频信号，并且需要扩展API来选择这些接口的视频时序。由于现有的 :ref:`v4l2_std_id <v4l2-std-id>` 位数有限，无法进行扩展，因此增加了一组新的 ioctl 来设置和获取输入和输出的视频时序。

这些 ioctl 处理定义每个视频格式的详细数字视频时序。这包括活动视频宽度和高度、信号极性、前廊、后廊、同步宽度等参数。可以通过使用 ``linux/v4l2-dv-timings.h`` 头文件来获取 :ref:`cea861` 和 :ref:`vesadmt` 标准中的时序。

为了枚举和查询设备支持的 DV 时序属性，应用程序可以使用 :ref:`VIDIOC_ENUM_DV_TIMINGS` 和 :ref:`VIDIOC_DV_TIMINGS_CAP` ioctl。要为设备设置 DV 时序，应用程序使用 :ref:`VIDIOC_S_DV_TIMINGS <VIDIOC_G_DV_TIMINGS>` ioctl；要获取当前的 DV 时序，则使用 :ref:`VIDIOC_G_DV_TIMINGS <VIDIOC_G_DV_TIMINGS>` ioctl。要检测视频接收器看到的 DV 时序，应用程序使用 :ref:`VIDIOC_QUERY_DV_TIMINGS` ioctl。

当硬件检测到视频源发生变化（例如视频信号出现或消失，或者视频分辨率改变）时，它会发出 `V4L2_EVENT_SOURCE_CHANGE` 事件。可以使用 :ref:`ioctl VIDIOC_SUBSCRIBE_EVENT <VIDIOC_SUBSCRIBE_EVENT>` 和 :ref:`VIDIOC_DQEVENT` 来检查是否报告了此事件。

如果视频信号发生了变化，应用程序必须停止流传输，释放所有缓冲区，并调用 :ref:`VIDIOC_QUERY_DV_TIMINGS` 获取新的视频时序，如果这些时序有效，则可以通过调用 :ref:`ioctl VIDIOC_S_DV_TIMINGS <VIDIOC_G_DV_TIMINGS>` 来设置这些时序。这也会更新格式，所以使用 :ref:`ioctl VIDIOC_G_FMT <VIDIOC_G_FMT>` 获取新格式。此时应用程序可以分配新的缓冲区并重新开始流传输。

:ref:`VIDIOC_QUERY_DV_TIMINGS` 只报告硬件检测到的情况，不会更改配置。如果当前设置的时序与实际检测到的时序不同，通常意味着你将无法捕获任何视频。正确的做法是依赖于 `V4L2_EVENT_SOURCE_CHANGE` 事件，以知道何时发生变更。

应用程序可以利用 :ref:`input-capabilities` 和 :ref:`output-capabilities` 标志来确定是否可以在给定的输入或输出上使用数字视频 ioctl。
