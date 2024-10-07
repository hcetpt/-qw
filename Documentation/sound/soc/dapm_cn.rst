动态音频电源管理便携式设备
================================

描述
====

动态音频电源管理（DAPM）旨在允许便携式Linux设备在音频子系统中始终使用最低的电量。它独立于其他内核电源管理框架，因此可以轻松共存。DAPM对所有用户空间应用程序是完全透明的，因为所有的电源切换都在ASoC核心内部完成。用户空间应用程序不需要任何代码更改或重新编译。DAPM根据设备中的任何音频流（捕捉/播放）活动和音频混音器设置来做出电源切换决策。DAPM基于两个基本元素，称为小部件和路径：

* 一个**小部件**是音频硬件的每一个部分，可以在使用时通过软件启用，在不使用时禁用以节省电力。
* 一个**路径**是在小部件之间存在的互连，当声音可以从一个小部件流向另一个小部件时。

所有DAPM电源切换决策都是通过咨询音频路由图自动做出的。这个图是针对每张声卡特定的，并覆盖整个声卡，因此一些DAPM路径连接属于不同组件的两个小部件（例如，CODEC的LINE OUT引脚和放大器的输入引脚）。

STM32MP1-DK1声卡的图如下所示：

.. kernel-figure:: dapm-graph.svg
    :alt:   示例DAPM图
    :align: center

DAPM电源域
==========

DAPM中有4个电源域：

Codec偏置域
      VREF, VMID（核心codec和音频电源）

      通常在codec探测/移除以及挂起/恢复时控制，尽管如果不需要为侧音等供电，也可以在流时间内设定。
平台/机器域
      物理连接的输入和输出

      具体取决于平台/机器和用户操作，由机器驱动程序配置并响应异步事件，例如当耳机插入时。
路径域
      音频子系统的信号路径

      当用户改变混音器和多路复用器设置时自动设置，例如alsamixer, amixer。
流域
      DACs和ADCs
      在启动和停止流播放/捕捉时启用和禁用，例如aplay, arecord。

DAPM小部件
==========

音频DAPM小部件分为几种类型：

混音器
     将多个模拟信号混合成单一模拟信号。
多路复用器
     一种模拟开关，仅输出多个输入中的一个。
PGA
可编程增益放大器或衰减部件

ADC
模数转换器

DAC
数模转换器

Switch
模拟开关

Input
编解码器输入引脚

Output
编解码器输出引脚

Headphone
耳机（及可选插孔）

Mic
麦克风（及可选插孔）

Line
线路输入/输出（及可选插孔）

Speaker
扬声器

Supply
为其他部件提供电源或时钟的部件

Regulator
为音频部件供电的外部稳压器

Clock
为音频部件提供时钟的外部时钟

AIF IN
音频接口输入（带有TDM槽掩码）

AIF OUT
音频接口输出（带有TDM槽掩码）

Siggen
信号发生器

DAI IN
数字音频接口输入

DAI OUT
数字音频接口输出

DAI Link
两个DAI结构之间的DAI链接

Pre
特殊的PRE部件（在所有其他部件之前执行）

Post
特殊的POST部件（在所有其他部件之后执行）

Buffer
DSP内部部件间的音频数据缓冲区
调度器  
DSP内部调度器，用于调度组件/管道的处理工作

效果  
执行音频处理效果的小部件

SRC  
DSP或CODEC内的采样率转换器

ASRC  
DSP或CODEC内的异步采样率转换器

编码器  
将音频数据从一种格式（通常是PCM）编码为另一种通常更压缩的格式的小部件

解码器  
将音频数据从压缩格式解码为非压缩格式（如PCM）的小部件

（小部件在include/sound/soc-dapm.h中定义）

任何类型的组件驱动程序都可以向声卡添加小部件
soc-dapm.h中定义了一些方便的宏，可以快速构建CODEC和机器DAPM小部件列表
大多数小部件都有名称、寄存器、位移和反转。一些小部件还有额外的参数，例如流名称和kcontrols

流域小部件
------------------------------

流小部件与流电源域相关，仅包含ADC（模拟到数字转换器）、DAC（数字到模拟转换器）、AIF IN 和 AIF OUT
流小部件的格式如下：
::

  SND_SOC_DAPM_DAC(name, stream name, reg, shift, invert),
  SND_SOC_DAPM_AIF_IN(name, stream, slot, reg, shift, invert)

注意：流名称必须与您的CODEC中的相应流名称匹配
snd_soc_dai_driver
例如，HiFi播放和捕获的流小部件
::

  SND_SOC_DAPM_DAC("HiFi DAC", "HiFi Playback", REG, 3, 1),
  SND_SOC_DAPM_ADC("HiFi ADC", "HiFi Capture", REG, 2, 1),

例如，AIF的流小部件
::

  SND_SOC_DAPM_AIF_IN("AIF1RX", "AIF1 Playback", 0, SND_SOC_NOPM, 0, 0),
  SND_SOC_DAPM_AIF_OUT("AIF1TX", "AIF1 Capture", 0, SND_SOC_NOPM, 0, 0),

路径域小部件
------------------------------

路径域小部件具有控制或影响音频子系统内音频信号或音频路径的能力。它们的形式如下：
::

  SND_SOC_DAPM_PGA(name, reg, shift, invert, controls, num_controls)

任何小部件kcontrols都可以使用controls和num_controls成员进行设置
例如：混音器小部件（kcontrols 首先声明）
::

  /* 输出混音器 */
  static const snd_kcontrol_new_t wm8731_output_mixer_controls[] = {
  SOC_DAPM_SINGLE("Line Bypass Switch", WM8731_APANA, 3, 1, 0),
  SOC_DAPM_SINGLE("Mic Sidetone Switch", WM8731_APANA, 5, 1, 0),
  SOC_DAPM_SINGLE("HiFi Playback Switch", WM8731_APANA, 4, 1, 0),
  };

  SND_SOC_DAPM_MIXER("Output Mixer", WM8731_PWR, 4, 1, wm8731_output_mixer_controls,
	ARRAY_SIZE(wm8731_output_mixer_controls)),

如果您不希望混音器元素以混音器小部件的名称为前缀，可以使用 SND_SOC_DAPM_MIXER_NAMED_CTL。参数与 SND_SOC_DAPM_MIXER 相同。

机器域小部件
----------------------

机器小部件与编解码器小部件不同之处在于它们没有关联的编解码器寄存器位。每个可以独立供电的机器音频组件（非编解码器或 DSP）都会分配一个机器小部件。例如：
* 扬声器放大器
* 麦克风偏置
* 插孔连接器

机器小部件可以有一个可选的回调函数。例如，外部麦克风的插孔连接器小部件，在麦克风插入时启用麦克风偏置：
::

  static int spitz_mic_bias(struct snd_soc_dapm_widget* w, int event)
  {
	gpio_set_value(SPITZ_GPIO_MIC_BIAS, SND_SOC_DAPM_EVENT_ON(event));
	return 0;
  }

  SND_SOC_DAPM_MIC("Mic Jack", spitz_mic_bias),

编解码器（偏置）域
-------------------

编解码器偏置电源域没有任何小部件，并由编解码器 DAPM 事件处理器处理。当编解码器电源状态相对于任何流事件或内核 PM 事件发生变化时，会调用此处理器。

虚拟小部件
------------------

有时在编解码器或机器音频图中存在没有对应软电源控制的小部件。在这种情况下，需要创建一个虚拟小部件——一个没有控制位的小部件。例如：
::

  SND_SOC_DAPM_MIXER("AC97 Mixer", SND_SOC_NOPM, 0, 0, NULL, 0),

这可以在软件中用于合并两个信号路径。

注册 DAPM 控制
=========================

在许多情况下，DAPM 小部件在编解码器驱动程序中的 `static const struct snd_soc_dapm_widget` 数组中静态实现，并通过 `struct snd_soc_component_driver` 的 `dapm_widgets` 和 `num_dapm_widgets` 字段简单声明。
同样，连接它们的路由也在 `static const struct snd_soc_dapm_route` 数组中静态实现，并通过同一个结构体的 `dapm_routes` 和 `num_dapm_routes` 字段声明。
有了上述声明，驱动程序注册将负责填充这些内容：
::

  static const struct snd_soc_dapm_widget wm2000_dapm_widgets[] = {
  	SND_SOC_DAPM_OUTPUT("SPKN"),
  	SND_SOC_DAPM_OUTPUT("SPKP"),
  	..
};

  /* 目标，路径，源 */
  static const struct snd_soc_dapm_route wm2000_audio_map[] = {
  	{ "SPKN", NULL, "ANC Engine" },
  	{ "SPKP", NULL, "ANC Engine" },
	..
```c
static const struct snd_soc_component_driver soc_component_dev_wm2000 = {
	...
	.dapm_widgets		= wm2000_dapm_widgets,
	.num_dapm_widgets	= ARRAY_SIZE(wm2000_dapm_widgets),
	.dapm_routes            = wm2000_audio_map,
	.num_dapm_routes        = ARRAY_SIZE(wm2000_audio_map),
	...
};
```

在更复杂的情况下，DAPM 小部件和/或路径列表可能只能在探测时确定。例如，当驱动程序支持具有不同特性的多个模型时就会发生这种情况。在这种情况下，可以使用 `snd_soc_dapm_new_controls()` 和 `snd_soc_dapm_add_routes()` 函数来注册实现特定情况的小部件和路径数组。

### 编解码器/DSP 小部件互连
小部件通过音频路径（称为互连）在编解码器、平台和机器内部相互连接。必须定义每个互连以创建所有小部件之间音频路径的图。这通常通过编解码器或 DSP 的图示（以及机器音频系统的原理图）来完成，因为它需要通过音频信号路径将小部件连接在一起。

例如，WM8731 输出混音器（wm8731.c）有 3 个输入源：

1. 线路旁路输入
2. DAC（高保真播放）
3. 麦克风侧音输入

在这个例子中，每个输入都有一个与其关联的 kcontrol（如上例所示）。这些输入通过它们的 kcontrol 名称与输出混音器相连。现在我们可以将目标小部件（就音频信号而言）与其源小部件连接起来。例如：

```c
/* 输出混音器 */
{"Output Mixer", "Line Bypass Switch", "Line Input"},
{"Output Mixer", "HiFi Playback Switch", "DAC"},
{"Output Mixer", "Mic Sidetone Switch", "Mic Bias"},
```

所以我们有：

* 目标小部件 <=== 路径名称 <=== 源小部件，或者
* 汇聚点，路径，源，或者
* `Output Mixer` 通过 `HiFi Playback Switch` 连接到 `DAC`

当没有路径名称连接小部件（例如直接连接）时，我们传递 NULL 作为路径名称。

互连是通过调用以下函数创建的：

```c
snd_soc_dapm_connect_input(codec, sink, path, source);
```

最后，在所有小部件和互连都已注册到核心之后，必须调用 `snd_soc_dapm_new_widgets()`。这使得核心扫描编解码器和机器，从而使内部 DAPM 状态与机器的实际状态匹配。

### 机器小部件互连
机器小部件互连的创建方式与编解码器相同，并且直接将编解码器引脚连接到机器级别的小部件。
例如，将扬声器输出编解码器引脚连接到内部扬声器。
```c
// 例如，将扬声器输出编解码器引脚连接到内部扬声器
```
```plaintext
/* 外部扬声器连接到编解码器引脚 LOUT2 和 ROUT2 */
{"Ext Spk", NULL, "ROUT2"},
{"Ext Spk", NULL, "LOUT2"},

这允许 DAPM 控制连接（并且在使用中）的引脚的电源开关，以及未连接的引脚分别关闭。
终点小部件
===========
一个终点是一个音频信号在机器内部的起点或终点（小部件），包括编解码器。例如：
* 耳机插孔
* 内置扬声器
* 内置麦克风
* 麦克风插孔
* 编解码器引脚

这些终点会被添加到 DAPM 图形中，以便确定它们的使用情况以节省电力。例如，未使用的编解码器引脚将被关闭，未连接的插孔也可以被关闭。
DAPM 小部件事件
================

需要实现比 DAPM 更复杂行为的小部件可以通过设置函数指针来设置自定义的“事件处理器”。例如，电源供应需要启用一个 GPIO：

```c
static int sof_es8316_speaker_power_event(struct snd_soc_dapm_widget *w,
                                          struct snd_kcontrol *kcontrol, int event)
{
    if (SND_SOC_DAPM_EVENT_ON(event))
        gpiod_set_value_cansleep(gpio_pa, true);
    else
        gpiod_set_value_cansleep(gpio_pa, false);

    return 0;
}

static const struct snd_soc_dapm_widget st_widgets[] = {
    ..
SND_SOC_DAPM_SUPPLY("Speaker Power", SND_SOC_NOPM, 0, 0,
                     sof_es8316_speaker_power_event,
                     SND_SOC_DAPM_PRE_PMD | SND_SOC_DAPM_POST_PMU),
};
```

请参阅 soc-dapm.h 获取支持事件的所有其他小部件。
事件类型
--------

以下事件类型由事件小部件支持：

```c
/* dapm 事件类型 */
#define SND_SOC_DAPM_PRE_PMU		0x1	/* 在小部件上电之前 */
#define SND_SOC_DAPM_POST_PMU		0x2	/* 在小部件上电之后 */
#define SND_SOC_DAPM_PRE_PMD		0x4	/* 在小部件断电之前 */
#define SND_SOC_DAPM_POST_PMD		0x8	/* 在小部件断电之后 */
#define SND_SOC_DAPM_PRE_REG		0x10	/* 在音频路径设置之前 */
#define SND_SOC_DAPM_POST_REG		0x20	/* 在音频路径设置之后 */
#define SND_SOC_DAPM_WILL_PMU		0x40	/* 在序列开始时调用 */
#define SND_SOC_DAPM_WILL_PMD		0x80	/* 在序列开始时调用 */
#define SND_SOC_DAPM_PRE_POST_PMD	(SND_SOC_DAPM_PRE_PMD | SND_SOC_DAPM_POST_PMD)
#define SND_SOC_DAPM_PRE_POST_PMU	(SND_SOC_DAPM_PRE_PMU | SND_SOC_DAPM_POST_PMU)
```
```
