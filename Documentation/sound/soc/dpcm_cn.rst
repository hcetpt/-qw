动态PCM
========

描述
====

动态PCM允许ALSA PCM设备在其PCM流运行期间将数字音频路由到各种数字端点。例如，PCM0可以将数字音频路由到I2S DAI0、I2S DAI1或PDM DAI2。这对于在SoC上基于DSP的驱动程序非常有用，这些驱动程序暴露了多个ALSA PCM，并且可以路由到多个DAI。动态PCM的运行时路由由ALSA混音器设置确定，就像ASoC编解码器驱动程序中的模拟信号路由一样。动态PCM使用一个DAPM图来表示DSP内部音频路径，并利用混音器设置来确定每个ALSA PCM使用的路径。动态PCM无需对现有的组件编解码器、平台和DAI驱动程序进行任何修改即可重用它们。

基于SoC的DSP电话音频系统
------------------------------

考虑以下电话音频子系统。本文档中所有示例都将使用它：
```
| 前端PCM         |  SoC DSP  | 后端DAI      | 音频设备     |

                     *************
 PCM0 <------------> *           * <----DAI0-----> 编码器耳机
                     *           *
 PCM1 <------------> *           * <----DAI1-----> 编码器扬声器
                     *   DSP     *
 PCM2 <------------> *           * <----DAI2-----> MODEM
                     *           *
 PCM3 <------------> *           * <----DAI3-----> 蓝牙(BT)
                     *           *
                     *           * <----DAI4-----> 数字麦克风(DMIC)
                     *           *
                     *           * <----DAI5-----> FM
                     *************
```

此图显示了一个简单的智能手机音频子系统。它支持蓝牙、FM数字广播、扬声器、耳机插孔、数字麦克风和蜂窝调制解调器。这个声卡暴露了4个基于DSP的前端（FE）ALSA PCM设备，并支持6个后端（BE）DAI。每个FE PCM都可以将音频数据数字路由到任意的BE DAI。FE PCM设备还可以将音频路由到一个以上的BE DAI。

示例 - 动态PCM从DAI0切换播放到DAI1
---------------------------------------

音频正在通过耳机播放。过了一会儿，用户取下耳机，音频继续通过扬声器播放。
PCM0通过耳机播放的声音看起来像这样：
```
                     *************
 PCM0 <============> *           * <====DAI0=====> 编码器耳机
                     *           *
 PCM1 <------------> *           * <----DAI1-----> 编码器扬声器
                     *   DSP     *
 PCM2 <------------> *           * <----DAI2-----> MODEM
                     *           *
 PCM3 <------------> *           * <----DAI3-----> 蓝牙(BT)
                     *           *
                     *           * <----DAI4-----> 数字麦克风(DMIC)
                     *           *
                     *           * <----DAI5-----> FM
                     *************
```

用户取下了耳机插孔，因此现在必须使用扬声器：
```
                     *************
 PCM0 <============> *           * <----DAI0-----> 编码器耳机
                     *           *
 PCM1 <------------> *           * <====DAI1=====> 编码器扬声器
                     *   DSP     *
 PCM2 <------------> *           * <----DAI2-----> MODEM
                     *           *
 PCM3 <------------> *           * <----DAI3-----> 蓝牙(BT)
                     *           *
                     *           * <----DAI4-----> 数字麦克风(DMIC)
                     *           *
                     *           * <----DAI5-----> FM
                     *************
```

音频驱动程序处理如下：

1. 机器驱动程序接收到耳机拔出事件。
2. 机器驱动程序或音频HAL禁用耳机路径。
3. 动态PCM在DAI0（耳机）上执行PCM触发（停止）、hw_free()和shutdown()操作，因为路径已被禁用。
4. 机器驱动程序或音频HAL启用扬声器路径。
5. 动态PCM为DAI1扬声器执行PCM启动、hw_params()、prepare()和触发（开始）操作，因为路径已启用。
在这个例子中，机器驱动或用户空间音频HAL可以更改路由，随后DPCM将负责管理DAI PCM操作以启动或停止链路。在此过渡期间音频播放不会停止。
DPCM机器驱动
=============

启用DPCM的ASoC机器驱动与常规机器驱动类似，只是我们还需要：

1. 定义前端（FE）和后端（BE）DAI链接
2. 定义任何FE/BE PCM操作
3. 定义小部件图连接
前端和后端DAI链接
-------------------
::

  | 前端PCM    |  SoC DSP  | 后端DAI | 音频设备 |
  
                      *************
  PCM0 <------------> *           * <----DAI0-----> 编码器耳机
                      *           *
  PCM1 <------------> *           * <----DAI1-----> 编码器扬声器
                      *   DSP     *
  PCM2 <------------> *           * <----DAI2-----> MODEM
                      *           *
  PCM3 <------------> *           * <----DAI3-----> 蓝牙(BT)
                      *           *
                      *           * <----DAI4-----> 数字麦克风(DMIC)
                      *           *
                      *           * <----DAI5-----> FM
                      *************

对于上面的例子，我们需要定义4个前端DAI链接和6个后端DAI链接。前端DAI链接定义如下：
::

  static struct snd_soc_dai_link machine_dais[] = {
	{
		.name = "PCM0 系统",
		.stream_name = "系统播放",
		.cpu_dai_name = "系统针脚",
		.platform_name = "dsp-audio",
		.codec_name = "snd-soc-dummy",
		.codec_dai_name = "snd-soc-dummy-dai",
		.dynamic = 1,
		.trigger = {SND_SOC_DPCM_TRIGGER_POST, SND_SOC_DPCM_TRIGGER_POST},
		.dpcm_playback = 1,
	},
	.....< 其他前端和后端DAI链接在这里 >
  };

这个前端DAI链接与常规DAI链接非常相似，除了我们还设置了DAI链接为一个动态DPCM前端，并使用`dynamic = 1`。应使用`dpcm_playback`和`dpcm_capture`标志设置支持的前端流方向。还有一个选项来指定每个前端触发调用的顺序。这允许ASoC核心在其他组件之前或之后触发DSP（因为某些DSP对DAI/DSP开始和停止序列的顺序有严格要求）。
上面的前端DAI将编解码器和编解码DAI设置为虚拟设备，因为后端是动态的，并且会根据运行时配置变化。
后端DAI配置如下：
::

  static struct snd_soc_dai_link machine_dais[] = {
	.....< 前端DAI链接在这里 >
	{
		.name = "编码器耳机",
		.cpu_dai_name = "ssp-dai.0",
		.platform_name = "snd-soc-dummy",
		.no_pcm = 1,
		.codec_name = "rt5640.0-001c",
		.codec_dai_name = "rt5640-aif1",
		.ignore_suspend = 1,
		.ignore_pmdown_time = 1,
		.be_hw_params_fixup = hswult_ssp0_fixup,
		.ops = &haswell_ops,
		.dpcm_playback = 1,
		.dpcm_capture = 1,
	},
	.....< 其他后端DAI链接在这里 >
  };

这个后端DAI链接将DAI0连接到编解码器（本例中RT5640 AIF1）。它设置了`no_pcm`标志以标记其为后端，并使用`dpcm_playback`和`dpcm_capture`设置支持的流方向。
后端还设置了忽略挂起和PM关机时间的标志。这使得后端可以在无主机模式下工作，其中主机CPU没有传输数据，例如蓝牙电话呼叫：
::

                      *************
  PCM0 <------------> *           * <----DAI0-----> 编码器耳机
                      *           *
  PCM1 <------------> *           * <----DAI1-----> 编码器扬声器
                      *   DSP     *
  PCM2 <------------> *           * <====DAI2=====> MODEM
                      *           *
  PCM3 <------------> *           * <====DAI3=====> 蓝牙(BT)
                      *           *
                      *           * <----DAI4-----> 数字麦克风(DMIC)
                      *           *
                      *           * <----DAI5-----> FM
                      *************

这使得主机CPU可以在DSP、MODEM DAI和蓝牙DAI仍在运行时休眠。
如果编解码器是由外部管理的设备，则后端DAI链接也可以将编解码器设置为虚拟设备。
同样，如果CPU DAI由DSP固件管理，则后端DAI也可以设置虚拟CPU DAI。
FE/BE PCM 操作
--------------

上述的 BE 还导出了某些 PCM 操作和一个 `修正` 回调。该修正回调被机器驱动程序用于（重新）配置 DAI，基于 FE 的硬件参数。例如，DSP 可能会在 FE 到 BE 之间执行重采样 (SRC) 或异步采样率转换 (ASRC)。
例如，DSP 可能把所有 FE 硬件参数转换为以固定速率 48kHz、16 位、立体声运行，针对 DAI0。这意味着对于 DAI0 来说，所有 FE 硬件参数都必须在机器驱动程序中固定，以便 DAI 在所需的配置下运行，而不管 FE 配置如何。

```c
static int dai0_fixup(struct snd_soc_pcm_runtime *rtd,
                      struct snd_pcm_hw_params *params)
{
    struct snd_interval *rate = hw_param_interval(params,
                                                   SNDRV_PCM_HW_PARAM_RATE);
    struct snd_interval *channels = hw_param_interval(params,
                                                      SNDRV_PCM_HW_PARAM_CHANNELS);

    /* DSP 将把 FE 速率转换为 48kHz，立体声 */
    rate->min = rate->max = 48000;
    channels->min = channels->max = 2;

    /* 设置 DAI0 为 16 位 */
    params_set_format(params, SNDRV_PCM_FORMAT_S16_LE);
    return 0;
}
```

其他的 PCM 操作与常规 DAI 链接相同。根据需要使用。
Widget 图形连接
---------------

通常，BE DAI 链接会在初始化时由 ASoC DAPM 核心连接到图形中。但是，如果 BE 编码器或 BE DAI 是虚拟的，则必须明确地在驱动程序中设置它，如下所示：
```c
/* BE 对于 codec 耳机 -  DAI0 是虚拟的，并且由 DSP 固件管理 */
{"DAI0 CODEC IN", NULL, "AIF1 Capture"},
{"AIF1 Playback", NULL, "DAI0 CODEC OUT"},
```

编写 DPCM DSP 驱动程序
=====================

DPCM DSP 驱动程序看起来很像标准平台类 ASoC 驱动程序，结合了编码器类驱动程序的一些元素。DSP 平台驱动程序必须实现以下几点：

1. 前端 PCM DAI - 即 struct snd_soc_dai_driver
2. DAPM 图形，展示从 FE DAIs 到 BEs 的 DSP 音频路由
3. DSP 图形中的 DAPM Widgets
4. 用于增益、路由等的混音器
5. DMA 配置
6. BE AIF Widgets

第 6 点对于将音频路由到 DSP 外部非常重要。每个 BE 和每个流方向都需要定义 AIF。例如，对于上面的 BE DAI0，我们会有：
```c
SND_SOC_DAPM_AIF_IN("DAI0 RX", NULL, 0, SND_SOC_NOPM, 0, 0),
SND_SOC_DAPM_AIF_OUT("DAI0 TX", NULL, 0, SND_SOC_NOPM, 0, 0),
```

BE AIF 用于将 DSP 图形连接到其他组件驱动程序（例如，codec 图形）的图形中。
无主机PCM流
=============

无主机PCM流是指不通过主机CPU路由的流。一个例子是手机到调制解调器的电话通话：
```
                      *************
  PCM0 <------------> *           * <----DAI0-----> 编码器耳机
                      *           *
  PCM1 <------------> *           * <====DAI1=====> 编码器扬声器/麦克风
                      *   DSP     *
  PCM2 <------------> *           * <====DAI2=====> 调制解调器
                      *           *
  PCM3 <------------> *           * <----DAI3-----> 蓝牙(BT)
                      *           *
                      *           * <----DAI4-----> 数字麦克风(DMIC)
                      *           *
                      *           * <----DAI5-----> FM
                      *************
```

在这种情况下，PCM数据通过DSP进行路由。在该用例中，主机CPU仅用于控制，并且在流运行期间可以休眠。
主机可以通过以下方式之一来控制无主机链接：

1. 将链接配置为编码器<->编码器样式的链接。在这种情况下，链接的启用或禁用由DAPM图的状态决定。这通常意味着存在一个混音器控制，可用于连接或断开两个DAI之间的路径。
2. 无主机前端(FE)。此FE与DAPM图上的后端(BE)DAI链接具有虚拟连接。然后通过FE作为常规PCM操作来执行控制。
这种方法对DAI链接提供了更多的控制，但需要更多的用户空间代码来控制链接。建议除非您的硬件需要更精细的PCM操作序列，否则使用编码器<->编码器。

### 编码器<->编码器链接
----------------------

当DAPM检测到DAPM图中有一个有效路径时，此DAI链接被启用。
机器驱动程序会向DAI链接设置一些额外参数，例如：
```c
  static const struct snd_soc_pcm_stream dai_params = {
	.formats = SNDRV_PCM_FMTBIT_S32_LE,
	.rate_min = 8000,
	.rate_max = 8000,
	.channels_min = 2,
	.channels_max = 2,
  };

  static struct snd_soc_dai_link dais[] = {
	< ... 更多DAI链接在此之上 ... >
	{
		.name = "MODEM",
		.stream_name = "MODEM",
		.cpu_dai_name = "dai2",
		.codec_dai_name = "modem-aif1",
		.codec_name = "modem",
		.dai_fmt = SND_SOC_DAIFMT_I2S | SND_SOC_DAIFMT_NB_NF
				| SND_SOC_DAIFMT_CBM_CFM,
		.c2c_params = &dai_params,
		.num_c2c_params = 1,
	}
	< ... 更多DAI链接在此之下 ... >
```

当DAPM检测到有效路径并调用PCM操作以启动链接时，这些参数将用于配置DAI的hw_params()。当路径不再有效时，DAPM也会调用适当的PCM操作来禁用DAI。

### 无主机前端(FE)
------------------

DAI链接由一个不读取或写入任何PCM数据的前端启用
这意味着创建一个新的前端，它与两个DAI链接通过虚拟路径相连。当FE PCM启动时，DAI链接也将启动；当FE PCM停止时，DAI链接也将停止。请注意，在这种配置下，FE PCM无法读取或写入数据。
您没有提供需要翻译的文本。请提供需要翻译成中文的英文或其他语言的文本。
