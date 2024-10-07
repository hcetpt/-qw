============================
ALSA PCM 通道映射 API
============================

Takashi Iwai <tiwai@suse.de>

概述
=====

通道映射 API 允许用户查询可能的通道映射和当前的通道映射，也可以选择性地修改当前流的通道映射。
一个通道映射是一个每个 PCM 通道的位置数组。
通常，一个立体声 PCM 流有一个通道映射为
``{ front_left, front_right }``
而一个 4.0 环绕声 PCM 流有一个通道映射为
``{ front_left, front_right, rear_left, rear_right }``。

到目前为止的问题是，我们没有一个标准的通道映射，应用程序也没有办法知道哪个通道对应于哪个（扬声器）位置。因此，应用程序在 5.1 输出时使用了错误的通道，你会突然听到后方发出奇怪的声音。或者，一些设备秘密地假设中心/LFE 是第三/第四通道，而其他设备则认为 C/LFE 是第五/第六通道。此外，像 HDMI 这样的设备即使在总通道数相同的情况下也可以配置不同的扬声器位置。然而，由于缺乏通道映射规范，没有办法指定这一点。这些都是引入新的通道映射 API 的主要动机。
设计
=====

实际上，“通道映射 API”在内核/用户空间 ABI 方面并没有引入任何新内容。它只使用现有的控制元素特性。
作为基础设计，每个 PCM 子流可以包含一个提供通道映射信息和配置的控制元素。这个元素由以下参数指定：

* iface = SNDRV_CTL_ELEM_IFACE_PCM
* 名称 = “Playback Channel Map” 或 “Capture Channel Map”
* 设备 = 被分配给 PCM 子流的相同设备编号
* 索引 = 被分配给 PCM 子流的相同索引编号

请注意，名称根据 PCM 子流的方向不同而不同。
每个控制元素至少提供 TLV 读操作和读操作。可选地，可以提供写操作以允许用户动态更改通道映射。
TLV
---

TLV 操作提供可用通道映射的列表。一个通道映射列表项通常是 TLV 形式
``type data-bytes ch0 ch1 ch2...``
其中 type 是 TLV 类型值，第二个参数是通道值的总字节数（而不是数量），其余的是每个通道的位置值。
作为 TLV 类型，可以使用 ``SNDRV_CTL_TLVT_CHMAP_FIXED``、``SNDRV_CTL_TLV_CHMAP_VAR`` 或 ``SNDRV_CTL_TLVT_CHMAP_PAIRED``。
``_FIXED`` 类型适用于具有固定通道位置的通道映射，而后两种类型适用于灵活的通道位置。``_VAR`` 类型适用于所有通道都可以自由交换的通道映射，而 ``_PAIRED`` 类型适用于成对交换通道。例如，当你有 {FL/FR/RL/RR} 通道映射时，``_PAIRED`` 类型只允许你交换 {RL/RR/FL/FR}，而 ``_VAR`` 类型甚至允许交换 FL 和 RR。
这些新的TLV类型定义在 `sound/tlv.h` 中。可用的声道位置值定义在 `sound/asound.h` 中，以下是摘录：

::

  /* 声道位置 */
  枚举 {
    SNDRV_CHMAP_UNKNOWN = 0,
    SNDRV_CHMAP_NA,      /* 不适用，静音 */
    SNDRV_CHMAP_MONO,    /* 单声道流 */
    /* 以下遵循alsa-lib混音器声道值+3 */
    SNDRV_CHMAP_FL,      /* 前左 */
    SNDRV_CHMAP_FR,      /* 前右 */
    SNDRV_CHMAP_RL,      /* 后左 */
    SNDRV_CHMAP_RR,      /* 后右 */
    SNDRV_CHMAP_FC,      /* 前中 */
    SNDRV_CHMAP_LFE,     /* LFE */
    SNDRV_CHMAP_SL,      /* 侧左 */
    SNDRV_CHMAP_SR,      /* 侧右 */
    SNDRV_CHMAP_RC,      /* 后中 */
    /* 新定义 */
    SNDRV_CHMAP_FLC,     /* 前左中 */
    SNDRV_CHMAP_FRC,     /* 前右中 */
    SNDRV_CHMAP_RLC,     /* 后左中 */
    SNDRV_CHMAP_RRC,     /* 后右中 */
    SNDRV_CHMAP_FLW,     /* 前左宽 */
    SNDRV_CHMAP_FRW,     /* 前右宽 */
    SNDRV_CHMAP_FLH,     /* 前左高 */
    SNDRV_CHMAP_FCH,     /* 前中高 */
    SNDRV_CHMAP_FRH,     /* 前右高 */
    SNDRV_CHMAP_TC,      /* 顶中 */
    SNDRV_CHMAP_TFL,     /* 顶前左 */
    SNDRV_CHMAP_TFR,     /* 顶前右 */
    SNDRV_CHMAP_TFC,     /* 顶前中 */
    SNDRV_CHMAP_TRL,     /* 顶后左 */
    SNDRV_CHMAP_TRR,     /* 顶后右 */
    SNDRV_CHMAP_TRC,     /* 顶后中 */
    SNDRV_CHMAP_LAST = SNDRV_CHMAP_TRC,
  };

当PCM流可以提供多个声道映射时，可以在一个TLV容器类型中提供多个声道映射。返回的TLV数据将包含如下内容：
::

    SNDRV_CTL_TLVT_CONTAINER 96
        SNDRV_CTL_TLVT_CHMAP_FIXED 4 SNDRV_CHMAP_FC
        SNDRV_CTL_TLVT_CHMAP_FIXED 8 SNDRV_CHMAP_FL SNDRV_CHMAP_FR
        SNDRV_CTL_TLVT_CHMAP_FIXED 16 SNDRV_CHMAP_FL SNDRV_CHMAP_FR \
            SNDRV_CHMAP_RL SNDRV_CHMAP_RR

声道位置提供在最低16位。高位用于位标志
::

    #define SNDRV_CHMAP_POSITION_MASK       0xffff
    #define SNDRV_CHMAP_PHASE_INVERSE       (0x01 << 16)
    #define SNDRV_CHMAP_DRIVER_SPEC         (0x02 << 16)

`SNDRV_CHMAP_PHASE_INVERSE` 表示声道相位反转（因此左声道和右声道相加几乎为静音）。一些数字麦克风设备有这种情况。
当设置了 `SNDRV_CHMAP_DRIVER_SPEC` 时，所有声道位置值不遵循上述标准定义，而是遵循驱动程序特定的定义。

读取操作
----------

控制读取操作用于提供给定流的当前声道映射。控制元素返回一个整数数组，包含每个声道的位置。
当在指定通道数量之前执行此操作（即设置hw_params），应返回所有通道设置为 `UNKNOWN`。

写入操作
----------

控制写入操作是可选的，仅适用于能够即时更改声道配置的设备，如HDMI。用户需要传递一个整数值，该值包含分配的PCM子流中所有声道的有效位置。
此操作仅在PCM PREPARED状态下允许。在其他状态下调用时，应当返回错误。
