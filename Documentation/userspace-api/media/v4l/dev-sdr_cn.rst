SPDX 许可证标识符: GFDL-1.1-no-invariants-or-later

.. _sdr:

**************************************
软件定义无线电接口 (SDR)
**************************************

SDR 是软件定义无线电的缩写，指的是使用应用程序软件进行调制或解调的无线电设备。此接口旨在控制此类设备的数据流。SDR 设备通过名为 `/dev/swradio0` 到 `/dev/swradio255` 的字符设备特殊文件访问，主设备号为 81，次设备号从 0 到 255 动态分配。

查询能力
=====================

支持 SDR 接收机接口的设备会在由 `VIDIOC_QUERYCAP` ioctl 返回的 `v4l2_capability` 结构体的 `capabilities` 字段中设置 `V4L2_CAP_SDR_CAPTURE` 和 `V4L2_CAP_TUNER` 标志。该标志表示设备具有模数转换器（ADC），这是 SDR 接收机的必需组件。

支持 SDR 发射机接口的设备会在由 `VIDIOC_QUERYCAP` ioctl 返回的 `v4l2_capability` 结构体的 `capabilities` 字段中设置 `V4L2_CAP_SDR_OUTPUT` 和 `V4L2_CAP_MODULATOR` 标志。该标志表示设备具有数模转换器（DAC），这是 SDR 发射机的必需组件。

必须支持至少一种读写或流式 I/O 方法。

辅助功能
======================

SDR 设备可以支持 :ref:`controls <control>`，并且必须支持 :ref:`tuner` ioctl。Tuner ioctl 用于设置 ADC/DAC 采样率（采样频率）和可能的射频（RF）。

`V4L2_TUNER_SDR` 调谐器类型用于设置 SDR 设备的 ADC/DAC 频率，而 `V4L2_TUNER_RF` 调谐器类型用于设置射频。如果存在 RF 调谐器，则其调谐器索引必须紧跟在 SDR 调谐器索引之后。通常 SDR 调谐器是 #0，RF 调谐器是 #1。

不支持 :ref:`VIDIOC_S_HW_FREQ_SEEK` ioctl。

数据格式协商
=======================

SDR 设备使用 :ref:`format` ioctl 来选择捕获和输出格式。采样分辨率和数据流格式都绑定于此可选格式。除了基本的 :ref:`format` ioctl 外，还必须支持 :ref:`VIDIOC_ENUM_FMT` ioctl。

为了使用 :ref:`format` ioctl，应用程序将 `v4l2_format` 结构体的 `type` 字段设置为 `V4L2_BUF_TYPE_SDR_CAPTURE` 或 `V4L2_BUF_TYPE_SDR_OUTPUT`，并根据所需的运行操作使用 `fmt` 联合中的 `v4l2_sdr_format` 结构体的 `sdr` 成员。目前有两个字段，`pixelformat` 和 `buffersize`，在 `v4l2_sdr_format` 结构体中被使用。
``pixelformat`` 的内容是数据格式的 V4L2 FourCC 代码。
``buffersize`` 字段是指数据传输所需的最大缓冲区大小（以字节为单位），由驱动程序设置，以便告知应用程序。
.. c:type:: v4l2_sdr_format

.. tabularcolumns:: |p{4.4cm}|p{4.4cm}|p{8.5cm}|

.. flat-table:: struct v4l2_sdr_format
    :header-rows:  0
    :stub-columns: 0
    :widths:       1 1 2

    * - __u32
      - ``pixelformat``
      - 数据格式或压缩类型，由应用程序设置
这是小端模式的 :ref:`four character code <v4l2-fourcc>`。V4L2 在 :ref:`sdr-formats` 中定义了 SDR 格式
* - __u32
      - ``buffersize``
      - 数据所需的最大字节大小。值由驱动程序设置
* - __u8
      - ``reserved[24]``
      - 此数组保留用于未来的扩展。驱动程序和应用程序必须将其设置为零
SDR 设备可能支持 :ref:`读/写 <rw>` 和/或流式传输（:ref:`内存映射 <mmap>` 或 :ref:`用户指针 <userp>`）I/O
