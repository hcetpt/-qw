SPDX 许可证标识符：GFDL-1.1-no-invariants-or-later

.. _tuner:

*********************
调谐器和调制器
*********************

调谐器
======

视频输入设备可以有一个或多个调谐器来解调射频（RF）信号。每个调谐器与一个或多个视频输入相关联，具体取决于调谐器上的射频连接器数量。通过 `VIDIOC_ENUMINPUT` ioctl 返回的结构体 :c:type:`v4l2_input` 的 `type` 字段设置为 `V4L2_INPUT_TYPE_TUNER`，其 `tuner` 字段包含调谐器的索引号。
无线电输入设备只有一个索引为零的调谐器，并且没有视频输入。

为了查询和更改调谐器属性，应用程序使用 `VIDIOC_G_TUNER <VIDIOC_G_TUNER>` 和 `VIDIOC_S_TUNER <VIDIOC_G_TUNER>` ioctl。由 `VIDIOC_G_TUNER <VIDIOC_G_TUNER>` 返回的结构体 :c:type:`v4l2_tuner` 还包含当前视频或无线电输入所查询的调谐器的信号状态信息。
.. note::

    `VIDIOC_S_TUNER <VIDIOC_G_TUNER>` 不会在存在多个调谐器时切换当前调谐器。调谐器仅由当前视频输入确定。驱动程序必须支持这两个 ioctl，并在设备具有一个或多个调谐器时，在通过 `VIDIOC_QUERYCAP` ioctl 返回的结构体 :c:type:`v4l2_capability` 中设置 `V4L2_CAP_TUNER` 标志。

调制器
======

视频输出设备可以有一个或多个调制器，用于调制视频信号以辐射或连接到电视机或录像机的天线输入端口。每个调制器与一个或多个视频输出相关联，具体取决于调制器上的射频连接器数量。通过 `VIDIOC_ENUMOUTPUT` ioctl 返回的结构体 :c:type:`v4l2_output` 的 `type` 字段设置为 `V4L2_OUTPUT_TYPE_MODULATOR`，其 `modulator` 字段包含调制器的索引号。
无线电输出设备只有一个索引为零的调制器，并且没有视频输出。

视频或无线电设备不能同时支持调谐器和调制器。对于这样的硬件，需要使用两个独立的设备节点，一个支持调谐器功能，另一个支持调制器功能。原因是 `VIDIOC_S_FREQUENCY <VIDIOC_G_FREQUENCY>` ioctl 存在一个限制，无法指定频率是用于调谐器还是调制器。
为了查询和更改调制器属性，应用程序使用 `VIDIOC_G_MODULATOR <VIDIOC_G_MODULATOR>` 和 `VIDIOC_S_MODULATOR <VIDIOC_G_MODULATOR>` ioctl。请注意，`VIDIOC_S_MODULATOR <VIDIOC_G_MODULATOR>` 不会在存在多个调制器时切换当前调制器。调制器仅由当前视频输出确定。驱动程序必须支持这两个 ioctl，并在设备具有一个或多个调制器时，在通过 `VIDIOC_QUERYCAP` ioctl 返回的结构体 :c:type:`v4l2_capability` 中设置 `V4L2_CAP_MODULATOR` 标志。

射频
====

为了获取和设置调谐器或调制器的射频频段，应用程序使用 `VIDIOC_G_FREQUENCY <VIDIOC_G_FREQUENCY>` 和 `VIDIOC_S_FREQUENCY <VIDIOC_G_FREQUENCY>` ioctl，这两个 ioctl 都接受指向结构体 :c:type:`v4l2_frequency` 的指针。这些 ioctl 适用于电视和无线电设备。当支持调谐器或调制器 ioctl 或者设备是一个无线电设备时，驱动程序必须支持这两个 ioctl。
