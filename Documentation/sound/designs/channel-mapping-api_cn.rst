============= 
ALSA PCM 通道映射 API
============= 

田井 宏司 <tiwai@suse.de>

概述
=====

该通道映射API允许用户查询可能的通道映射和当前的通道映射，并且可选地修改当前流的通道映射。一个通道映射是一个PCM通道每个位置的数组。通常，一个立体声PCM流具有如下的通道映射：``{ 前左, 前右 }``；而一个4.0环绕声PCM流则有如下的通道映射：``{ 前左, 前右, 后左, 后右 }``。

迄今为止存在的问题是，我们没有一个明确的标准通道映射，应用程序无法知道哪个通道对应于哪个（扬声器）位置。因此，应用程序在5.1输出时应用了错误的通道，你会突然从后面听到奇怪的声音。或者，一些设备秘密假设中心/LFE是第三个/第四个通道，而其他设备则将C/LFE作为第五个/第六个通道。此外，像HDMI这样的设备即使具有相同数量的总通道，也可以配置为不同的扬声器位置。但由于缺乏通道映射规范，没有办法指定这些信息。这就是新的通道映射API的主要动机。
设计
=====

实际上，“通道映射API”在内核/用户空间ABI的角度并没有引入任何新特性。它仅使用现有的控制元素特性。作为一种基本的设计，每个PCM子流可以包含一个提供通道映射信息和配置的控制元素。这个元素由以下内容定义：

* iface = SNDRV_CTL_ELEM_IFACE_PCM
* 名称 = “播放通道映射”或“捕捉通道映射”
* 设备 = 分配给PCM子流的相同设备编号
* 索引 = 分配给PCM子流的相同索引编号

请注意，名称会根据PCM子流的方向有所不同。
每个控制元素至少提供TLV读取操作和读取操作。可选地，写入操作可以被提供以允许用户动态更改通道映射。
TLV
---

TLV操作提供了可用通道映射列表。一个通道映射列表项通常是如下形式的TLV：``类型 数据字节 ch0 ch1 ch2 ...``，其中类型是TLV类型值，第二个参数是总字节数（不是通道数），其余的是每个通道的位置值。
作为TLV类型，可以使用``SNDRV_CTL_TLVT_CHMAP_FIXED``、``SNDRV_CTL_TLV_CHMAP_VAR``或``SNDRV_CTL_TLVT_CHMAP_PAIRED``。``_FIXED``类型用于具有固定通道位置的通道映射，而后两种类型用于灵活的通道位置。“_VAR”类型适用于所有通道都可以自由交换的通道映射，而“_PAIRED”类型适用于成对的通道可以交换的情况。例如，当您有一个{FL/FR/RL/RR}通道映射时，“_PAIRED”类型只允许您交换{RL/RR/FL/FR}，而“_VAR”类型则允许甚至交换FL和RR。
这些新的TLV类型在 ``sound/tlv.h`` 中定义。
可用的声道位置值在 ``sound/asound.h`` 中定义，以下是一个摘录：

::

  /* 音道位置 */
  枚举 {
	SNDRV_CHMAP_UNKNOWN = 0,
	SNDRV_CHMAP_NA,		/* 不适用，静音 */
	SNDRV_CHMAP_MONO,	/* 单声道流 */
	/* 这些值遵循alsa-lib混音器声道值+3 */
	SNDRV_CHMAP_FL,		/* 前左 */
	SNDRV_CHMAP_FR,		/* 前右 */
	SNDRV_CHMAP_RL,		/* 后左 */
	SNDRV_CHMAP_RR,		/* 后右 */
	SNDRV_CHMAP_FC,		/* 前中 */
	SNDRV_CHMAP_LFE,	/* 低频效果 */
	SNDRV_CHMAP_SL,		/* 侧左 */
	SNDRV_CHMAP_SR,		/* 侧右 */
	SNDRV_CHMAP_RC,		/* 后中 */
	/* 新定义 */
	SNDRV_CHMAP_FLC,	/* 前左中 */
	SNDRV_CHMAP_FRC,	/* 前右中 */
	SNDRV_CHMAP_RLC,	/* 后左中 */
	SNDRV_CHMAP_RRC,	/* 后右中 */
	SNDRV_CHMAP_FLW,	/* 前左宽 */
	SNDRV_CHMAP_FRW,	/* 前右宽 */
	SNDRV_CHMAP_FLH,	/* 前左高 */
	SNDRV_CHMAP_FCH,	/* 前中高 */
	SNDRV_CHMAP_FRH,	/* 前右高 */
	SNDRV_CHMAP_TC,		/* 顶部中 */
	SNDRV_CHMAP_TFL,	/* 顶部前左 */
	SNDRV_CHMAP_TFR,	/* 顶部前右 */
	SNDRV_CHMAP_TFC,	/* 顶部前中 */
	SNDRV_CHMAP_TRL,	/* 顶部后左 */
	SNDRV_CHMAP_TRR,	/* 顶部后右 */
	SNDRV_CHMAP_TRC,	/* 顶部后中 */
	SNDRV_CHMAP_LAST = SNDRV_CHMAP_TRC,
  };

当PCM流可以提供多于一个的声道映射时，你可以在一个TLV容器类型中提供多个声道映射。返回的TLV数据将包含如下内容：
::

	SNDRV_CTL_TLVT_CONTAINER 96
	    SNDRV_CTL_TLVT_CHMAP_FIXED 4 SNDRV_CHMAP_FC
	    SNDRV_CTL_TLVT_CHMAP_FIXED 8 SNDRV_CHMAP_FL SNDRV_CHMAP_FR
	    SNDRV_CTL_TLVT_CHMAP_FIXED 16 SNDRV_CHMAP_FL SNDRV_CHMAP_FR \
		SNDRV_CHMAP_RL SNDRV_CHMAP_RR

声道位置提供在最低16位。高位用于位标志：
::

	#define SNDRV_CHMAP_POSITION_MASK	0xffff
	#define SNDRV_CHMAP_PHASE_INVERSE	(0x01 << 16)
	#define SNDRV_CHMAP_DRIVER_SPEC		(0x02 << 16)

``SNDRV_CHMAP_PHASE_INVERSE`` 表示该声道是反相的，
（因此左和右声道相加几乎会产生静音）
一些数字麦克风设备具有此特性。
当设置了 ``SNDRV_CHMAP_DRIVER_SPEC`` 时，所有声道位置值
不遵循上述标准定义，而是遵循驱动程序特定的定义。

读取操作
--------------

控制读取操作是为了提供给定流当前的声道映射。控制元素返回一个整数数组，
其中包含每个声道的位置。
当在指定声道数量之前执行此操作
（即设置hw_params），它应该返回所有声道设置为
``UNKNOWN``。

写入操作
--------------

控制写入操作是可选的，并且仅适用于能够在运行时改变声道配置的设备，例如HDMI。用户需要传递一个整数值，
该值包含分配给PCM子流的所有声道的有效位置。
此操作仅允许在PCM PREPARED状态下进行。在其他状态下调用时，应当返回错误。
