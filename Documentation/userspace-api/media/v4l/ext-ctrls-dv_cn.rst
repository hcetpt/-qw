SPDX 许可证标识符: GFDL-1.1-no-invariants-or-later

.. _dv-controls:

**************************************
数字视频控制参考
**************************************

数字视频控制类旨在控制用于 `VGA <http://en.wikipedia.org/wiki/Vga>`__、`DVI <http://en.wikipedia.org/wiki/Digital_Visual_Interface>`__（数字视像接口）、HDMI (:ref:`hdmi`) 和 DisplayPort (:ref:`dp`) 的接收器和发射器。这些控制通常仅由实现它们的接收器或发射器子设备私有，因此仅在 ``/dev/v4l-subdev*`` 设备节点上暴露。
.. note::

   注意，这些设备可以有多个输入或输出端口，这些端口连接到例如 HDMI 接口。尽管子设备只会从/向这些端口中的一个接收/传输视频，但在处理 EDID（扩展显示识别数据，:ref:`vesaedid`）和 HDCP（高带宽数字内容保护系统，:ref:`hdcp`）时，其他端口仍然可以是活动状态。这允许设备提前进行相对较慢的 EDID/HDCP 处理，从而实现快速切换。

这些端口以位掩码的形式出现在本节中的几个控制中，每个端口对应一位。位 0 对应端口 0，位 1 对应端口 1，依此类推。控制的最大值是一组有效的端口。
.. _dv-control-id:

数字视频控制 ID
=========================

``V4L2_CID_DV_CLASS (class)``
    数字视频类描述符
``V4L2_CID_DV_TX_HOTPLUG (bitmask)``
    许多接口有一个热插拔引脚，当可以从源设备获取 EDID 信息时该引脚为高电平。此控制显示发射器所看到的热插拔引脚的状态。每个位对应发射器的一个输出端口。如果输出端口没有关联的热插拔引脚，则该端口对应的位将为 0。此只读控制适用于 DVI-D、HDMI 和 DisplayPort 接口。
``V4L2_CID_DV_TX_RXSENSE (bitmask)``
    Rx Sense 是检测 TMDS 时钟线上的上拉。这通常意味着接收端已离开/进入待机模式（即发射器可以感知到接收器已准备好接收视频）。每个位对应发射器的一个输出端口。如果输出端口没有关联的 Rx Sense，则该端口对应的位将为 0。此只读控制适用于 DVI-D 和 HDMI 设备。
``V4L2_CID_DV_TX_EDID_PRESENT (bitmask)``
    当发射器接收到接收器的热插拔信号时，它会尝试读取 EDID。如果设置，则表示发射器至少已经读取了第一个块（= 128 字节）。每个位对应发射器的一个输出端口。如果输出端口不支持 EDID，则该端口对应的位将为 0。此只读控制适用于 VGA、DVI-A/D、HDMI 和 DisplayPort 接口。
``V4L2_CID_DV_TX_MODE``
    (枚举)

    enum v4l2_dv_tx_mode -

    HDMI 发射器可以在 DVI-D 模式（仅视频）或 HDMI 模式（视频+音频+辅助数据）下传输。此控制选择要使用的模式：V4L2_DV_TX_MODE_DVI_D 或 V4L2_DV_TX_MODE_HDMI。

此控制适用于 HDMI 接口。
``V4L2_CID_DV_TX_RGB_RANGE``
    (枚举)

枚举 `v4l2_dv_rgb_range` —
    选择 RGB 输出的量化范围。`V4L2_DV_RANGE_AUTO` 会遵循视频接口标准（例如 HDMI 的 :ref:`cea861`）中指定的 RGB 量化范围。
`V4L2_DV_RANGE_LIMITED` 和 `V4L2_DV_RANGE_FULL` 覆盖了标准，以兼容那些未正确实现标准的接收设备（不幸的是，对于 HDMI 和 DVI-D 来说这种情况相当常见）。
全范围允许使用所有可能的值，而有限范围将范围设置为 `(16 << (N-8)) - (235 << (N-8))`，其中 N 是每个组件的位数。此控制适用于 VGA、DVI-A/D、HDMI 和 DisplayPort 连接器。

``V4L2_CID_DV_TX_IT_CONTENT_TYPE``
    (枚举)

枚举 `v4l2_dv_it_content_type` —
    配置传输视频的 IT 内容类型。这些信息通过 HDMI 和 DisplayPort 连接器作为 AVI InfoFrame 的一部分发送。术语“IT 内容”用于指代来自计算机的内容，而不是来自电视广播或模拟源的内容。枚举 `v4l2_dv_it_content_type` 定义了可能的内容类型：

.. tabularcolumns:: |p{7.3cm}|p{10.2cm}|

.. flat-table::
    :header-rows:  0
    :stub-columns: 0

    * - ``V4L2_DV_IT_CONTENT_TYPE_GRAPHICS``
      - 图形内容。像素数据应未经滤波且不进行模拟重建地传递
    * - ``V4L2_DV_IT_CONTENT_TYPE_PHOTO``
      - 照片内容。内容来源于数字静态图片。内容应尽可能减少缩放和图像增强地传递
    * - ``V4L2_DV_IT_CONTENT_TYPE_CINEMA``
      - 电影内容
    * - ``V4L2_DV_IT_CONTENT_TYPE_GAME``
      - 游戏内容。音频和视频延迟应最小化
    * - ``V4L2_DV_IT_CONTENT_TYPE_NO_ITC``
      - 没有可用的 IT 内容信息，并且 AVI InfoFrame 中的 ITC 位设置为 0

``V4L2_CID_DV_RX_POWER_PRESENT (位掩码)``
    检测接收器是否从源端接收电源（例如
HDMI 在其中一个引脚上承载 5V 电压。这通常用于为包含 EDID 信息的 EEPROM 供电，从而使信号源即使在接收端处于待机/关机状态时也能读取 EDID。每一位对应接收器上的一个输入端口。如果某个输入端口无法检测到是否有电源，则该端口对应的位将为 0。此只读控制适用于 DVI-D、HDMI 和 DisplayPort 连接器。

``V4L2_CID_DV_RX_RGB_RANGE``
（枚举）

枚举 `v4l2_dv_rgb_range` — 选择 RGB 输入的量化范围。`V4L2_DV_RANGE_AUTO` 遵循视频接口标准中规定的 RGB 量化范围（例如 HDMI 的 `cea861`）。`V4L2_DV_RANGE_LIMITED` 和 `V4L2_DV_RANGE_FULL` 覆盖了标准，以兼容那些没有正确实现标准的信号源（不幸的是，这种情况在 HDMI 和 DVI-D 中相当常见）。全范围允许使用所有可能的值，而有限范围则设置为 `(16 << (N-8)) - (235 << (N-8))`，其中 N 是每个组件的位数。此控制适用于 VGA、DVI-A/D、HDMI 和 DisplayPort 连接器。

``V4L2_CID_DV_RX_IT_CONTENT_TYPE``
（枚举）

枚举 `v4l2_dv_it_content_type` — 读取接收到视频的 IT 内容类型。这些信息作为 AVI InfoFrame 的一部分通过 HDMI 和 DisplayPort 连接器发送。术语“IT 内容”是指来自计算机的内容，而不是来自电视广播或模拟源的内容。请参阅 `V4L2_CID_DV_TX_IT_CONTENT_TYPE` 以获取可用的内容类型。
