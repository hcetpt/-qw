=======================
ASoC Codec 类驱动程序
=======================

Codec 类驱动程序是通用且与硬件无关的代码，用于配置 codec、FM、MODEM、BT 或外部 DSP，以提供音频采集和回放功能。它不应包含任何针对目标平台或机器的具体代码。所有特定于平台和机器的代码应分别添加到平台和机器驱动程序中。每个 codec 类驱动程序必须提供以下功能： 

1. Codec DAI 和 PCM 配置
2. Codec 控制 IO - 使用 RegMap API
3. 混音器和音频控制
4. Codec 音频操作
5. DAPM 描述
6. DAPM 事件处理程序
可选地，codec 驱动程序还可以提供：

7. DAC 数字静音控制

最好结合现有的 codec 驱动代码（位于 sound/soc/codecs/ 目录下）使用本指南。

ASoC Codec 驱动程序分解
===========================

Codec DAI 和 PCM 配置
-------------------------------
每个 codec 驱动程序必须有一个 `struct snd_soc_dai_driver` 来定义其 DAI 和 PCM 能力和操作。此结构体被导出以便通过您的机器驱动程序进行注册。
例如：
```
static struct snd_soc_dai_ops wm8731_dai_ops = {
	.prepare       = wm8731_pcm_prepare,
	.hw_params     = wm8731_hw_params,
	.shutdown      = wm8731_shutdown,
	.mute_stream   = wm8731_mute,
	.set_sysclk    = wm8731_set_dai_sysclk,
	.set_fmt       = wm8731_set_dai_fmt,
};

static struct snd_soc_dai_driver wm8731_dai = {
	.name          = "wm8731-hifi",
	.playback = {
		.stream_name = "Playback",
		.channels_min = 1,
		.channels_max = 2,
		.rates = WM8731_RATES,
		.formats = WM8731_FORMATS,},
	.capture = {
		.stream_name = "Capture",
		.channels_min = 1,
		.channels_max = 2,
		.rates = WM8731_RATES,
		.formats = WM8731_FORMATS,},
	.ops = &wm8731_dai_ops,
	.symmetric_rate = 1,
};
```

Codec 控制 IO
----------------
通常可以通过 I2C 或 SPI 风格的接口来控制 codec（AC97 在 DAI 中将控制与数据结合起来）。codec 驱动程序应使用 Regmap API 进行所有 codec 的 IO 操作。请参阅 `include/linux/regmap.h` 和现有 codec 驱动程序中的示例以了解如何使用 Regmap。

混音器和音频控制
-------------------------
所有 codec 混音器和音频控制都可以使用 `soc.h` 中定义的便利宏来定义。
```c
#define SOC_SINGLE(xname, reg, shift, mask, invert)
```

定义一个单声道控制，如下所示：
```
xname = 控制名称（例如："播放音量"）
reg = 编解码器寄存器
shift = 寄存器中控制位的偏移量
mask = 控制位大小（例如：掩码为7表示3个比特位）
invert = 控制位是否反转
```

其他宏包括：
```c
#define SOC_DOUBLE(xname, reg, shift_left, shift_right, mask, invert)
```

立体声控制。
```c
#define SOC_DOUBLE_R(xname, reg_left, reg_right, shift, mask, invert)
```

跨越两个寄存器的立体声控制。
```c
#define SOC_ENUM_SINGLE(xreg, xshift, xmask, xtexts)
```

定义一个枚举类型的单声道控制，如下所示：
```
xreg = 寄存器
xshift = 寄存器中控制位的偏移量
xmask = 控制位大小
xtexts = 指向描述每个设置的字符串数组指针
```
```c
#define SOC_ENUM_DOUBLE(xreg, xshift_l, xshift_r, xmask, xtexts)
```

定义一个枚举类型的立体声控制。

编解码器音频操作
----------------------
编解码器驱动程序还支持以下ALSA PCM操作：
```c
/* SoC 音频操作 */
struct snd_soc_ops {
	int (*startup)(struct snd_pcm_substream *);
	void (*shutdown)(struct snd_pcm_substream *);
	int (*hw_params)(struct snd_pcm_substream *, struct snd_pcm_hw_params *);
	int (*hw_free)(struct snd_pcm_substream *);
	int (*prepare)(struct snd_pcm_substream *);
};
```

详情请参阅ALSA驱动PCM文档：
https://www.kernel.org/doc/html/latest/sound/kernel-api/writing-an-alsa-driver.html

DAPM描述
----------------
动态音频电源管理（DAPM）描述了编解码器电源组件及其与ASoC核心的关系和寄存器。请阅读dapm.rst以了解构建描述的详细信息。请同时参考其他编解码器驱动程序中的示例。

DAPM事件处理程序
------------------
此函数是一个回调函数，用于处理编解码器域PM调用和系统域PM调用（例如挂起和恢复）。当不使用时，它用于将编解码器置于休眠状态。
电源状态：
```
SNDRV_CTL_POWER_D0: /* 全开 */
/* vref/mid, 时钟和振荡器开启，活动状态 */

SNDRV_CTL_POWER_D1: /* 部分开启 */
SNDRV_CTL_POWER_D2: /* 部分开启 */

SNDRV_CTL_POWER_D3hot: /* 关闭，带电 */
/* 除了vref/vmid外，所有都关闭，非活动状态 */

SNDRV_CTL_POWER_D3cold: /* 完全关闭，无电 */
```

编解码器DAC数字静音控制
------------------------------
大多数编解码器在DAC之前都有一个数字静音功能，可以用来最小化任何系统噪声。静音会阻止任何数字数据进入DAC。
可以在核心为每个编解码器DAI创建一个回调函数，在应用或解除静音时被调用。
例如：
```c
static int wm8974_mute(struct snd_soc_dai *dai, int mute, int direction)
{
	struct snd_soc_component *component = dai->component;
	u16 mute_reg = snd_soc_component_read(component, WM8974_DAC) & 0xffbf;

	if (mute)
		snd_soc_component_write(component, WM8974_DAC, mute_reg | 0x40);
	else
		snd_soc_component_write(component, WM8974_DAC, mute_reg);
	return 0;
}
```
