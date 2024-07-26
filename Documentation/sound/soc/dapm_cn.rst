动态音频电源管理在便携式设备中的应用
===================================================

描述
===========

动态音频电源管理 (DAPM) 是为了使便携式 Linux 设备在音频子系统中始终使用最少的电量而设计的。它独立于其他内核电源管理框架，因此可以与它们轻松共存。DAPM 对所有用户空间应用程序完全透明，因为所有的电源切换都在 ASoC 核心内部完成。对于用户空间应用程序来说不需要任何代码更改或重新编译。DAPM 根据设备内的任何音频流（录音/播放）活动和音频混音器设置来做出电源切换决策。DAPM 基于两个基本元素：小部件和路径：

* **小部件**是音频硬件的每一个部分，可以通过软件在使用时启用，在不使用时禁用以节省电量
* **路径**是在两个小部件之间存在的互连，当声音可以从一个小部件流向另一个小部件时

所有 DAPM 电源切换决策都是通过咨询音频路由图自动做出的。这个图对每张声卡都是特定的，并且跨越整个声卡，因此一些 DAPM 路径连接属于不同组件的两个小部件（例如，CODEC 的 LINE OUT 引脚和放大器的输入引脚）
STM32MP1-DK1 声卡的图如下所示：

.. 内核-图:: dapm-graph.svg
    :alt:   示例 DAPM 图
    :居中:  中心

DAPM 电源域
==================

DAPM 内有 4 个电源域：

Codec 偏置域
      VREF、VMID（核心 codec 和音频功率）

      通常在 codec 探测/移除以及挂起/恢复时控制，尽管如果不需要侧音等电源，则可以在流时间设置
平台/机器域
      物理连接的输入和输出

      依赖于平台/机器和用户操作，由机器驱动程序配置并响应异步事件，例如当耳机插入时

路径域
      音频子系统的信号路径

      当用户改变混音器和多路复用器设置时会自动设置，例如通过 alsamixer、amixer
流域
      DACs 和 ADCs
在开始和停止流播放/录音时启用和禁用。例如 aplay、arecord
DAPM 小部件
============

音频 DAPM 小部件分为几种类型：

混音器
	将几个模拟信号混合成单一模拟信号
多路复用器
	一种模拟开关，仅输出多个输入中的一个
PGA
可编程增益放大器或衰减部件

ADC
模拟到数字转换器

DAC
数字到模拟转换器

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
音频接口输入（带TDM槽掩码）

AIF OUT
音频接口输出（带TDM槽掩码）

Siggen
信号发生器

DAI IN
数字音频接口输入

DAI OUT
数字音频接口输出

DAI Link
两个DAI结构之间的DAI连接

Pre
特殊的PRE部件（在所有其他部件之前执行）

Post
特殊的POST部件（在所有其他部件之后执行）

Buffer
DSP内部部件间的音频数据缓冲区
### 调度器
DSP内部调度器，用于调度组件/管道的处理工作。

### 效果器
执行音频处理效果的控件。

### SRC
DSP或CODEC内的采样率转换器。

### ASRC
DSP或CODEC内的异步采样率转换器。

### 编码器
将音频数据从一种格式（通常是PCM）编码为另一种通常更压缩的格式的控件。

### 解码器
将音频数据从压缩格式解码为非压缩格式（如PCM）的控件。

（控件定义在`include/sound/soc-dapm.h`中）

### 控件
任何类型的组件驱动程序都可以向声卡添加控件。在`soc-dapm.h`中有定义的一些便利宏可以用来快速构建编解码器和机器DAPM控件的列表。大多数控件具有名称、寄存器、移位和反转等属性。一些控件有额外的参数，如流名称和kcontrols。

### 流域控件
---------------------
流控件与流电源域相关，仅包括ADC（模拟到数字转换器）、DAC（数字到模拟转换器）、AIF IN和AIF OUT。
流控件的格式如下：
```
SND_SOC_DAPM_DAC(name, stream name, reg, shift, invert),
SND_SOC_DAPM_AIF_IN(name, stream, slot, reg, shift, invert)
```

**注意**：流名称必须与您的编解码器`snd_soc_dai_driver`中的相应流名称匹配。
例如，针对HiFi播放和捕获的流控件：
```
SND_SOC_DAPM_DAC("HiFi DAC", "HiFi Playback", REG, 3, 1),
SND_SOC_DAPM_ADC("HiFi ADC", "HiFi Capture", REG, 2, 1),
```

例如，针对AIF的流控件：
```
SND_SOC_DAPM_AIF_IN("AIF1RX", "AIF1 Playback", 0, SND_SOC_NOPM, 0, 0),
SND_SOC_DAPM_AIF_OUT("AIF1TX", "AIF1 Capture", 0, SND_SOC_NOPM, 0, 0),
```

### 通路域控件
-------------------
通路域控件有能力控制或影响音频子系统内的音频信号或音频路径。它们的形式如下：
```
SND_SOC_DAPM_PGA(name, reg, shift, invert, controls, num_controls)
```

任何控件的kcontrols可以通过controls和num_controls成员设置。
例如，混音器小部件（kcontrols首先声明）：

```c
/* 输出混音器 */
static const snd_kcontrol_new_t wm8731_output_mixer_controls[] = {
  SOC_DAPM_SINGLE("Line Bypass Switch", WM8731_APANA, 3, 1, 0),
  SOC_DAPM_SINGLE("Mic Sidetone Switch", WM8731_APANA, 5, 1, 0),
  SOC_DAPM_SINGLE("HiFi Playback Switch", WM8731_APANA, 4, 1, 0),
};

SND_SOC_DAPM_MIXER("Output Mixer", WM8731_PWR, 4, 1, wm8731_output_mixer_controls,
	ARRAY_SIZE(wm8731_output_mixer_controls)),
```

如果你不想让混音器元素前缀为混音器小部件的名字，你可以使用`SND_SOC_DAPM_MIXER_NAMED_CTL`。参数与`SND_SOC_DAPM_MIXER`相同。

机器域小部件
--------------

机器小部件与编解码器小部件不同之处在于它们没有与之关联的编解码器寄存器位。每个可以独立供电的机器音频组件（非编解码器或DSP）都会分配一个机器小部件。例如：
* 扬声器放大器
* 麦克风偏置
* 插孔连接器

机器小部件可以有一个可选的回调函数。例如，用于外部麦克风的插孔连接器小部件，在插入麦克风时启用麦克风偏置：

```c
static int spitz_mic_bias(struct snd_soc_dapm_widget* w, int event)
{
	gpio_set_value(SPITZ_GPIO_MIC_BIAS, SND_SOC_DAPM_EVENT_ON(event));
	return 0;
}

SND_SOC_DAPM_MIC("Mic Jack", spitz_mic_bias),
```

编解码器（偏置）域
-------------------

编解码器偏置电源域没有小部件，并由编解码器DAPM事件处理器处理。当编解码器的电源状态因任何流事件或内核PM事件而改变时，会调用此处理器。
虚拟小部件
-------------

有时在编解码器或机器音频图中存在没有相应软电源控制的小部件。在这种情况下，需要创建一个虚拟小部件——即没有控制位的小部件。例如：
```c
SND_SOC_DAPM_MIXER("AC97 Mixer", SND_SOC_NOPM, 0, 0, NULL, 0),
```

这可以在软件中用来合并两条信号路径。

注册DAPM控制
==============

在许多情况下，DAPM小部件是静态地在编解码器驱动程序中的`static const struct snd_soc_dapm_widget`数组中实现，并通过`struct snd_soc_component_driver`中的`dapm_widgets`和`num_dapm_widgets`字段简单声明。
同样，连接它们的路由也在一个`static const struct snd_soc_dapm_route`数组中静态实现，并通过同一个结构体中的`dapm_routes`和`num_dapm_routes`字段声明。
有了以上声明，驱动程序注册将负责填充这些内容：

```c
static const struct snd_soc_dapm_widget wm2000_dapm_widgets[] = {
  	SND_SOC_DAPM_OUTPUT("SPKN"),
  	SND_SOC_DAPM_OUTPUT("SPKP"),
  	..
};

/* 目标, 路径, 源 */
static const struct snd_soc_dapm_route wm2000_audio_map[] = {
  	{ "SPKN", NULL, "ANC Engine" },
  	{ "SPKP", NULL, "ANC Engine" },
	..
};
```
下面是给定代码段和描述的中文翻译：

```c
static const struct snd_soc_component_driver soc_component_dev_wm2000 = {
    ...
    .dapm_widgets       = wm2000_dapm_widgets,
    .num_dapm_widgets   = ARRAY_SIZE(wm2000_dapm_widgets),
    .dapm_routes        = wm2000_audio_map,
    .num_dapm_routes    = ARRAY_SIZE(wm2000_audio_map),
    ...
};
```

在更复杂的情况下，DAPM小部件（widgets）列表和/或路径（routes）只能在探测（probe）时确定。例如，当驱动程序支持具有不同特性的不同模型时会发生这种情况。在这种情况下，可以实现特定于案例的小部件和路径数组，并通过调用 `snd_soc_dapm_new_controls()` 和 `snd_soc_dapm_add_routes()` 来程序性地注册这些数组。

**Codec/DSP 小部件互连**

小部件通过音频路径（称为互连）在 codec、平台和机器内部互相连接。为了创建所有小部件之间的音频路径图，每个互连都必须定义。
这可以通过 codec 或 DSP 的图表（以及机器音频系统的原理图）来最方便地完成，因为它需要通过它们的音频信号路径将小部件连接在一起。
例如，WM8731 输出混音器（wm8731.c）有 3 个输入（源）：

1. 线路旁路输入
2. DAC（高保真播放）
3. 麦克风侧音输入

在这个例子中，每个输入都有一个与之关联的 kcontrol（如上例所示定义），并通过其 kcontrol 名称连接到输出混音器。现在我们可以将目标小部件（就音频信号而言）与其源小部件连接起来。例如：

```plaintext
/* 输出混音器 */
{"Output Mixer", "Line Bypass Switch", "Line Input"},
{"Output Mixer", "HiFi Playback Switch", "DAC"},
{"Output Mixer", "Mic Sidetone Switch", "Mic Bias"},
```

所以，我们有：
- 目标小部件  <=== 路径名称 <=== 源小部件
- 或者
- 汇聚点，路径，源，或者
- ``Output Mixer`` 通过 ``HiFi Playback Switch`` 连接到 ``DAC``

当没有路径名称连接小部件（例如直接连接）时，我们将为路径名称传递 NULL。

互连是通过调用 `snd_soc_dapm_connect_input(codec, sink, path, source);` 创建的。

最后，在所有小部件和互连都已使用核心注册后，必须调用 `snd_soc_dapm_new_widgets()`。这将导致核心扫描 codec 和机器，以便内部 DAPM 状态与机器的物理状态匹配。

**机器小部件互连**
机器小部件互连的创建方式与 codec 中的一样，并且直接将 codec 引脚连接到机器级别的小部件。
例如，可以将扬声器输出 codec 引脚连接到内部扬声器。
```plaintext
/* 外部扬声器连接到编解码器引脚 LOUT2, ROUT2 */
{"Ext Spk", NULL, "ROUT2"},
{"Ext Spk", NULL, "LOUT2"},

这允许 DAPM 控制已连接（且在使用中）的引脚以及未连接（NC）的引脚的电源开关。
终端小部件(Widgets)
==================
一个终端是指机器内部音频信号的起始点或终点（小部件），包括编解码器。例如：
* 耳机插孔
* 内置扬声器
* 内置麦克风
* 麦克风插孔
* 编码器引脚

将终端添加到 DAPM 图表中以便确定其使用情况，从而节省电力。例如，未使用的编解码器引脚会被关闭，未连接的插孔也可以被关闭。
DAPM 小部件事件
==================

对于需要实现比 DAPM 提供功能更复杂行为的小部件，可以通过设置函数指针来指定一个自定义的“事件处理器”。例如，电源供应需要启用 GPIO 的情况：

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
   ...
SND_SOC_DAPM_SUPPLY("Speaker Power", SND_SOC_NOPM, 0, 0,
  			    sof_es8316_speaker_power_event,
  			    SND_SOC_DAPM_PRE_PMD | SND_SOC_DAPM_POST_PMU),
};

请参阅 soc-dapm.h 文件以了解所有其他支持事件的小部件。
事件类型
-----------
以下事件类型由事件小部件支持：

/* DAPM 事件类型 */
#define SND_SOC_DAPM_PRE_PMU		0x1	/* 在小部件上电之前 */
#define SND_SOC_DAPM_POST_PMU		0x2	/* 在小部件上电之后 */
#define SND_SOC_DAPM_PRE_PMD		0x4	/* 在小部件下电之前 */
#define SND_SOC_DAPM_POST_PMD		0x8	/* 在小部件下电之后 */
#define SND_SOC_DAPM_PRE_REG		0x10	/* 在音频路径配置之前 */
#define SND_SOC_DAPM_POST_REG		0x20	/* 在音频路径配置之后 */
#define SND_SOC_DAPM_WILL_PMU		0x40	/* 在序列开始时调用 */
#define SND_SOC_DAPM_WILL_PMD		0x80	/* 在序列开始时调用 */
#define SND_SOC_DAPM_PRE_POST_PMD	(SND_SOC_DAPM_PRE_PMD | SND_SOC_DAPM_POST_PMD)
#define SND_SOC_DAPM_PRE_POST_PMU	(SND_SOC_DAPM_PRE_PMU | SND_SOC_DAPM_POST_PMU)
```
请注意，上述代码示例是直接翻译的，实际使用时可能需要根据具体上下文进行调整。
