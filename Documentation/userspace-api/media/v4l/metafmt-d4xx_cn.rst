```
.. SPDX 许可证标识符: GFDL-1.1-no-invariants-or-later

.. _v4l2-meta-fmt-d4xx:

******************************************************
V4L2_META_FMT_D4XX ('D4XX')
******************************************************

Intel D4xx UVC 摄像头元数据

描述
====

Intel D4xx（如 D435、D455 等）摄像头在其 UVC 有效载荷头部包含每帧的元数据，遵循微软（Microsoft®）UVC 扩展提案 [1_]。这意味着私有的 D4XX 元数据在标准 UVC 头部之后以块的形式组织。D4XX 摄像头实现了由微软提议的几种标准块类型以及一些专有类型。支持的标准元数据类型包括 MetadataId_CaptureStats（ID 3）、MetadataId_CameraExtrinsics（ID 4）和 MetadataId_CameraIntrinsics（ID 5）。具体描述见 [1_]。本文档描述了 D4xx 摄像头使用的专有元数据类型。V4L2_META_FMT_D4XX 缓冲区遵循 V4L2_META_FMT_UVC 的元数据缓冲区布局，唯一的不同是它还包括专有的有效载荷头部数据。D4xx 摄像头使用批量传输，并且每帧只发送一个有效载荷，因此它们的头部不能超过 255 字节。本文档实现了 Intel 配置版本 3 [9_]。以下是 D4xx 摄像头使用的专有微软风格元数据类型，所有字段都采用小端字节序：

.. tabularcolumns:: |p{5.0cm}|p{12.5cm}|

.. flat-table:: D4xx 元数据
    :widths: 1 2
    :header-rows: 1
    :stub-columns: 0

    * - **字段**
      - **描述**
    * - :cspan:`1` *深度控制*
    * - __u32 ID
      - 0x80000000
    * - __u32 Size
      - 字节数量，包括 ID（所有协议版本：60）
    * - __u32 Version
      - 此结构的版本号。本文档覆盖了版本 1、2 和 3。当添加新字段时，版本号会递增。
    * - __u32 Flags
      - 标志位掩码：见 [2_] 下面
    * - __u32 Gain
      - 增益值，内部单位，与 V4L2_CID_GAIN 控制相同，用于捕获帧
    * - __u32 Exposure
      - 曝光时间（微秒），用于捕获帧
    * - __u32 Laser power
      - 激光 LED 功率，范围 0-360，用于深度测量
    * - __u32 AE mode
      - 0：手动；1：自动曝光
    * - __u32 Exposure priority
      - 曝光优先级值：0 - 恒定帧率
    * - __u32 AE ROI left
      - AE 区域的兴趣区域左边界（所有 ROI 值以像素为单位，位于 0 到最大宽度或高度之间）
    * - __u32 AE ROI right
      - AE 区域的兴趣区域右边界
    * - __u32 AE ROI top
      - AE 区域的兴趣区域上边界
    * - __u32 AE ROI bottom
      - AE 区域的兴趣区域下边界
    * - __u32 Preset
      - 预设选择器值，默认：0，除非用户更改
    * - __u8 Emitter mode (v3 only) (__u32 Laser mode for v1) [8_]
      - 0：关闭；1：打开，与 __u32 Laser mode for v1 相同
    * - __u8 RFU byte (v3 only)
      - 保留字节，供将来使用
    * - __u16 LED Power (v3 only)
      - LED 功率值 0-360 （F416 SKU）
    * - :cspan:`1` *捕获定时*
    * - __u32 ID
      - 0x80000001
    * - __u32 Size
      - 字节数量，包括 ID（所有协议版本：40）
    * - __u32 Version
      - 此结构的版本号。本文档对应版本 xxx。当添加新字段时，版本号会递增。
    * - __u32 Flags
      - 标志位掩码：见 [3_] 下面
    * - __u32 Frame counter
      - 单调递增计数器
    * - __u32 Optical time
      - 从帧开始到帧中点的时间（微秒）
    * - __u32 Readout time
      - 读取一帧所需的时间（微秒）
    * - __u32 Exposure time
      - 帧曝光时间（微秒）
    * - __u32 Frame interval
      - 微秒 = 1000000 / 帧率
    * - __u32 Pipe latency
      - 从帧开始到 USB 缓冲区中的数据时间（微秒）
    * - :cspan:`1` *配置*
    * - __u32 ID
      - 0x80000002
    * - __u32 Size
      - 字节数量，包括 ID（v1：36，v3：40）
    * - __u32 Version
      - 此结构的版本号。本文档对应版本 xxx。当添加新字段时，版本号会递增。
    * - __u32 Flags
      - 标志位掩码：见 [4_] 下面
    * - __u8 Hardware type
      - 摄像头硬件版本 [5_]
    * - __u8 SKU ID
      - 摄像头硬件配置 [6_]
    * - __u32 Cookie
      - 内部同步
    * - __u16 Format
      - 图像格式代码 [7_]
    * - __u16 Width
      - 宽度（像素）
    * - __u16 Height
      - 高度（像素）
    * - __u16 Framerate
      - 请求的帧率（每秒）
    * - __u16 Trigger
      - 字节 0：位 0：深度和 RGB 同步，位 1：外部触发
    * - __u16 Calibration count (v3 only)
      - 校准计数器，见 [4_] 下面
    * - __u8 GPIO input data (v3 only)
      - GPIO 读取，见 [4_] 下面（从固件 5.12.7.0 开始支持）
    * - __u32 Sub-preset info (v3 only)
      - 子预设信息，见 [4_] 下面
    * - __u8 reserved (v3 only)
      - 保留字节

.. _1:

[1] https://docs.microsoft.com/en-us/windows-hardware/drivers/stream/uvc-extensions-1-5

.. _2:

[2] 深度控制标志指定哪些字段有效：
    0x00000001 Gain
    0x00000002 Exposure
    0x00000004 Laser power
    0x00000008 AE mode
    0x00000010 Exposure priority
    0x00000020 AE ROI
    0x00000040 Preset
    0x00000080 Emitter mode
    0x00000100 LED Power

.. _3:

[3] 捕获定时标志指定哪些字段有效：
    0x00000001 Frame counter
    0x00000002 Optical time
    0x00000004 Readout time
    0x00000008 Exposure time
    0x00000010 Frame interval
    0x00000020 Pipe latency

.. _4:

[4] 配置标志指定哪些字段有效：
    0x00000001 Hardware type
    0x00000002 SKU ID
    0x00000004 Cookie
    0x00000008 Format
    0x00000010 Width
    0x00000020 Height
    0x00000040 Framerate
    0x00000080 Trigger
    0x00000100 Cal count
    0x00000200 GPIO Input Data
    0x00000400 Sub-preset Info

.. _5:

[5] 摄像头型号：
    0 DS5
    1 IVCAM2

.. _6:

[6] 8 位摄像头硬件配置位字段：
    [1:0] depthCamera
        00: 无深度
        01: 标准深度
        10: 宽深度
        11: 保留
    [2] depthIsActive - 是否有激光投影仪
    [3] RGB 存在
    [4] 惯性测量单元（IMU）存在
    [5] projectorType
        0: HPTG
        1: Princeton
    [6] 0: 投影仪，1: LED
    [7] 保留

.. _7:

[7] 视频流接口的图像格式代码：

深度：
    1 Z16
    2 Z

左传感器：
    1 Y8
    2 UYVY
    3 R8L8
    4 Calibration
    5 W10

鱼眼传感器：
    1 RAW8

.. _8:

[8] 版本 3 中，“Laser mode” 被替换为三个不同的字段。“Laser” 已重命名为 “Emitter”，因为有多种相机投影技术。由于我们已经有“Laser Power”的另一个字段，我们引入了“LED Power”来表示额外的发射器。
“Laser mode” __u32 字段被拆分为：
    1 __u8 Emitter mode
    2 __u8 RFU byte
    3 __u16 LED Power

这是版本 1 和版本 3 之间的变化。所有版本 1、2 和 3 都向后兼容相同的数据格式，并且都得到支持。见 [2_] 了解哪些属性有效。
```
[9] LibRealSense SDK 元数据源：
https://github.com/IntelRealSense/librealsense/blob/master/src/metadata.h
