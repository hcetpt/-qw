动态PCM
===========

描述
===========

动态PCM允许ALSA PCM设备在PCM流运行期间将其PCM音频数字路由到不同的数字端点。例如，PCM0可以将数字音频路由到I2S DAI0、I2S DAI1或PDM DAI2。这对于那些暴露了多个ALSA PCM并能路由到多个DAI的SoC DSP驱动程序非常有用。DPCM的实时路由由ALSA混音器设置决定，就像ASoC编解码器驱动程序中的模拟信号路由一样。DPCM使用一个表示DSP内部音频路径的DAPM图，并利用混音器设置来确定每个ALSA PCM使用的路径。DPCM无需任何修改即可重用现有的所有组件编解码器、平台和DAI驱动程序。
基于SoC DSP的电话音频系统
-------------------------------------

考虑以下电话音频子系统。本文档中的所有示例均基于此：
::

  | 前端PCM      | SoC DSP  | 后端DAI | 音频设备 |

                     *************
  PCM0 <------------> *           * <----DAI0-----> 编码器耳机
                     *           *
  PCM1 <------------> *           * <----DAI1-----> 编码器扬声器
                     *   DSP      *
  PCM2 <------------> *           * <----DAI2-----> MODEM
                     *           *
  PCM3 <------------> *           * <----DAI3-----> 蓝牙
                     *           *
                     *           * <----DAI4-----> 数字麦克风
                     *           *
                     *           * <----DAI5-----> FM
                     *************

此图显示了一个简单的智能手机音频子系统。它支持蓝牙、FM数字广播、扬声器、耳机插孔、数字麦克风和蜂窝调制解调器。此声卡暴露了4个DSP前端（FE）ALSA PCM设备，并支持6个后端（BE）DAI。每个FE PCM都可以将音频数据数字路由到任意一个BE DAI。FE PCM设备也可以将音频路由到多个BE DAI。

示例 - 从DAI0切换播放到DAI1
---------------------------------------------------

音频正在通过耳机播放。过了一会儿，用户取下了耳机，音频继续通过扬声器播放。
PCM0通过耳机播放音频的情况如下：
::

                     *************
  PCM0 <============> *           * <====DAI0=====> 编码器耳机
                     *           *
  PCM1 <------------> *           * <----DAI1-----> 编码器扬声器
                     *   DSP      *
  PCM2 <------------> *           * <----DAI2-----> MODEM
                     *           *
  PCM3 <------------> *           * <----DAI3-----> 蓝牙
                     *           *
                     *           * <----DAI4-----> 数字麦克风
                     *           *
                     *           * <----DAI5-----> FM
                     *************

用户拔掉了耳机插头，因此现在必须使用扬声器：
::

                     *************
  PCM0 <============> *           * <----DAI0-----> 编码器耳机
                     *           *
  PCM1 <------------> *           * <====DAI1=====> 编码器扬声器
                     *   DSP      *
  PCM2 <------------> *           * <----DAI2-----> MODEM
                     *           *
  PCM3 <------------> *           * <----DAI3-----> 蓝牙
                     *           *
                     *           * <----DAI4-----> 数字麦克风
                     *           *
                     *           * <----DAI5-----> FM
                     *************

音频驱动程序处理这个过程如下：

1. 设备驱动程序接收到耳机拔出事件
2. 设备驱动程序或音频HAL禁用耳机路径
3. DPCM在耳机路径被禁用时对DAI0执行PCM触发（停止）、hw_free()和shutdown()操作
4. 设备驱动程序或音频HAL启用扬声器路径
5. DPCM在扬声器路径启用时为DAI1扬声器执行启动（startup()）、hw_params()、prepare()和触发（start）的PCM操作
在这个示例中，机器驱动或用户空间音频HAL可以改变路由，然后DPCM将负责管理DAI PCM操作以启动或关闭链路。在此转换过程中，音频播放不会停止。

DPCM机器驱动
=============

启用DPCM的ASoC机器驱动与普通机器驱动相似，但还需要：

1. 定义前端（FE）和后端（BE）DAI链接
2. 定义任何FE/BE PCM操作
3. 定义小部件图连接

前端和后端DAI链接
-----------------
::

  | 前端PCMs    |  SoC DSP  | 后端DAIs | 音频设备 |
  
                      *************
  PCM0 <------------> *           * <----DAI0-----> 编解码器耳机
                      *           *
  PCM1 <------------> *           * <----DAI1-----> 编解码器扬声器
                      *   DSP     *
  PCM2 <------------> *           * <----DAI2-----> MODEM
                      *           *
  PCM3 <------------> *           * <----DAI3-----> 蓝牙
                      *           *
                      *           * <----DAI4-----> 数字麦克风
                      *           *
                      *           * <----DAI5-----> FM
                      *************

对于上述示例，我们需要定义4个前端DAI链接和6个后端DAI链接。前端DAI链接定义如下：
::

  static struct snd_soc_dai_link machine_dais[] = {
	{
		.name = "PCM0 System",
		.stream_name = "系统播放",
		.cpu_dai_name = "系统引脚",
		.platform_name = "dsp-audio",
		.codec_name = "snd-soc-dummy",
		.codec_dai_name = "snd-soc-dummy-dai",
		.dynamic = 1,
		.trigger = {SND_SOC_DPCM_TRIGGER_POST, SND_SOC_DPCM_TRIGGER_POST},
		.dpcm_playback = 1,
	},
	.....< 其他前端和后端DAI链接在这里 >
  };

这个前端DAI链接与常规DAI链接非常相似，除了我们还设置DAI链接为动态DPCM前端，并使用`dynamic = 1`。支持的前端流方向也应使用`dpcm_playback`和`dpcm_capture`标志进行设置。还有选项指定每个前端触发调用的顺序。这允许ASoC核心在其他组件之前或之后触发DSP（因为一些DSP对DAI/DSP启动和停止序列有严格的要求）。
上述前端DAI将编解码器和代码DAI设置为虚拟设备，因为后端是动态的，并且会根据运行时配置而变化。
后端DAI配置如下：
::

  static struct snd_soc_dai_link machine_dais[] = {
	.....< 前端DAI链接在这里 >
	{
		.name = "Codec Headset",
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

这个后端DAI链接将DAI0连接到编解码器（在这种情况下为RT5460 AIF1）。它设置了`no_pcm`标志以标记其为后端，并使用上面的`dpcm_playback`和`dpcm_capture`标志设置支持的流方向。
后端还设置了忽略挂起和PM关机时间的标志。这允许后端在无主机模式下工作，即主机CPU不传输数据，例如蓝牙电话通话：
::

                      *************
  PCM0 <------------> *           * <----DAI0-----> 编解码器耳机
                      *           *
  PCM1 <------------> *           * <----DAI1-----> 编解码器扬声器
                      *   DSP     *
  PCM2 <------------> *           * <====DAI2=====> MODEM
                      *           *
  PCM3 <------------> *           * <====DAI3=====> 蓝牙
                      *           *
                      *           * <----DAI4-----> 数字麦克风
                      *           *
                      *           * <----DAI5-----> FM
                      *************

这允许主机CPU休眠，同时DSP、MODEM DAI和蓝牙DAI仍然在运行。
如果编解码器是由外部管理的设备，则后端DAI链接也可以将编解码器设置为虚拟设备。
同样地，如果CPU DAI由DSP固件管理，则后端DAI也可以设置一个虚拟的CPU DAI。
FE/BE PCM操作
--------------------

上述的BE还导出了一些PCM操作和一个“修正”回调。该修正回调由机器驱动程序使用，根据FE硬件参数（重）配置DAI。例如，DSP可能会在FE到BE之间执行SRC或ASRC。例如，DSP将所有FE硬件参数转换为以固定速率48kHz、16位立体声运行，用于DAI0。这意味着对于DAI0，机器驱动程序中的所有FE硬件参数必须固定，以便无论FE配置如何，DAI都能以所需的配置运行。
::

  static int dai0_fixup(struct snd_soc_pcm_runtime *rtd,
			struct snd_pcm_hw_params *params)
  {
    struct snd_interval *rate = hw_param_interval(params,
            SNDRV_PCM_HW_PARAM_RATE);
    struct snd_interval *channels = hw_param_interval(params,
                        SNDRV_PCM_HW_PARAM_CHANNELS);

    /* DSP 将把 FE 采样率转换为 48kHz，立体声 */
    rate->min = rate->max = 48000;
    channels->min = channels->max = 2;

    /* 设置 DAI0 为 16 位 */
    params_set_format(params, SNDRV_PCM_FORMAT_S16_LE);
    return 0;
  }

其他PCM操作与常规DAI链接相同。根据需要使用
Widget图连接
------------------------

BE DAI链接通常会在初始化时由ASoC DAPM核心连接到图中。但是，如果BE编解码器或BE DAI是虚拟的，则必须在驱动程序中显式设置：
::

  /* 编解码器 Headset 的 BE - DAI0 是虚拟的，并由 DSP 固件管理 */
  {"DAI0 CODEC IN", NULL, "AIF1 Capture"},
  {"AIF1 Playback", NULL, "DAI0 CODEC OUT"},

编写DPCM DSP驱动程序
=========================

DPCM DSP驱动程序看起来很像一个标准平台类ASoC驱动程序，结合了编解码器类驱动程序的一些元素。一个DSP平台驱动程序必须实现以下内容：

1. 前端 PCM DAI - 即 struct snd_soc_dai_driver
2. 显示从FE DAI到BE的DSP音频路由的DAPM图
3. 来自DSP图的DAPM小部件
4. 混频器，用于增益、路由等
5. DMA配置
6. BE AIF小部件

第6项对于将音频路由到DSP外部非常重要。每个BE和每个流方向都需要定义AIF。例如，对于上面的BE DAI0，我们将有：
::

  SND_SOC_DAPM_AIF_IN("DAI0 RX", NULL, 0, SND_SOC_NOPM, 0, 0),
  SND_SOC_DAPM_AIF_OUT("DAI0 TX", NULL, 0, SND_SOC_NOPM, 0, 0),

BE AIF用于将DSP图连接到其他组件驱动程序（例如编解码器图）的图。
无主机PCM流
====================

无主机PCM流是指不通过主机CPU进行路由的流。一个例子是手机与调制解调器之间的电话通话：
::

                      *************
  PCM0 <------------> *           * <----DAI0-----> 编码器耳机
                      *           *
  PCM1 <------------> *           * <====DAI1=====> 编码器扬声器/麦克风
                      *   DSP     *
  PCM2 <------------> *           * <====DAI2=====> 调制解调器
                      *           *
  PCM3 <------------> *           * <----DAI3-----> 蓝牙
                      *           *
                      *           * <----DAI4-----> 数字麦克风
                      *           *
                      *           * <----DAI5-----> FM
                      *************

在这种情况下，PCM数据通过DSP进行路由。在该用例中，主机CPU仅用于控制，并且可以在流运行时休眠。主机可以通过以下方式之一控制无主机链路：

1. 将链路配置为编码器<->编码器样式的链路。在这种情况下，链路的启用或禁用由DAPM图的状态控制。这通常意味着有一个混音器控制可以用来连接或断开两个DAI之间的路径。
2. 无主机前端（FE）。此FE在DAPM图上具有到后端（BE）DAI链接的虚拟连接。然后通过FE以常规PCM操作的方式进行控制。
这种方法对DAI链接提供了更多的控制，但需要更多的用户空间代码来控制链路。除非硬件需要更精细的PCM操作序列，否则建议使用编码器<->编码器方式。

编码器<->编码器链路
--------------------

当DAPM检测到DAPM图中有有效路径时，此DAI链路将被启用。机器驱动程序会设置一些额外的参数给DAI链路，例如：
::

  static const struct snd_soc_pcm_stream dai_params = {
	.formats = SNDRV_PCM_FMTBIT_S32_LE,
	.rate_min = 8000,
	.rate_max = 8000,
	.channels_min = 2,
	.channels_max = 2,
  };

  static struct snd_soc_dai_link dais[] = {
	< ... 更多DAI链接在上方 ... >
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
	< ... 更多DAI链接在这里 ... >

这些参数在DAPM检测到有效路径并调用PCM操作以启动链路时用于配置DAI hw_params()。当路径不再有效时，DAPM也会调用适当的PCM操作来禁用DAI。

无主机前端（FE）
----------------

通过一个不读取或写入任何PCM数据的前端（FE）启用DAI链路。这意味着创建一个新的前端，它通过虚拟路径与两个DAI链接相连。当FE PCM启动时，DAI链接也将启动；当FE PCM停止时，DAI链接也将停止。请注意，在这种配置下，FE PCM无法读取或写入数据。
当然，请提供你需要翻译的文本。
