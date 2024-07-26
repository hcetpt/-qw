ASoC Codec 类驱动
=======================

Codec 类驱动包含了配置 codec、FM、MODEM、BT 或外部 DSP 以提供音频捕获和播放的通用且与硬件无关的代码。
它不应包含任何针对目标平台或机器特有的代码。所有平台和机器特定的代码应分别添加到平台和机器驱动中。
每个 codec 类驱动**必须**提供以下特性： 

1. Codec DAI 和 PCM 配置
2. 使用 RegMap API 的 Codec 控制 IO
3. 混音器和音频控制
4. Codec 音频操作
5. DAPM 描述
6. DAPM 事件处理器
可选地，codec 驱动还可以提供：

7. DAC 数字静音控制
最好是将本指南与 `sound/soc/codecs/` 目录下现有的 codec 驱动代码一起使用。

ASoC Codec 驱动分解
===========================

Codec DAI 和 PCM 配置
-------------------------------
每个 codec 驱动都必须有一个 `struct snd_soc_dai_driver` 来定义其 DAI 和 PCM 能力和操作。这个结构体需要被导出，以便你的机器驱动可以将其注册给内核。
例如：
::

  static struct snd_soc_dai_ops wm8731_dai_ops = {
	.prepare	= wm8731_pcm_prepare,
	.hw_params	= wm8731_hw_params,
	.shutdown	= wm8731_shutdown,
	.mute_stream	= wm8731_mute,
	.set_sysclk	= wm8731_set_dai_sysclk,
	.set_fmt	= wm8731_set_dai_fmt,
  };

  static struct snd_soc_dai_driver wm8731_dai = {
	.name = "wm8731-hifi",
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

Codec 控制 IO
----------------
通常可以通过 I2C 或 SPI 样式的接口来控制 codec（AC97 将控制与数据结合在 DAI 中）。codec 驱动应该使用 Regmap API 进行所有的 codec IO。请参阅 `include/linux/regmap.h` 和现有 codec 驱动以了解如何使用 regmap。
混音器和音频控制
-------------------------
所有 codec 的混音器和音频控制都可以使用在 `soc.h` 中定义的便利宏来定义。
以下是提供的代码注释和描述的中文翻译：

定义单一控制：
```c
#define SOC_SINGLE(xname, reg, shift, mask, invert)
```
定义一个单一控制，如下所示：
```
xname = 控制名称，例如："播放音量"
reg = 编解码器寄存器
shift = 寄存器中控制位的偏移
mask = 控制位的大小，例如：掩码为7表示3个比特
invert = 控制是否被反转
```

其他宏包括：
```c
#define SOC_DOUBLE(xname, reg, shift_left, shift_right, mask, invert)
```
立体声控制
```c
#define SOC_DOUBLE_R(xname, reg_left, reg_right, shift, mask, invert)
```
跨越两个寄存器的立体声控制
```c
#define SOC_ENUM_SINGLE(xreg, xshift, xmask, xtexts)
```
定义一个枚举类型的单一控制，如下所示：
```
xreg = 寄存器
xshift = 寄存器中控制位的偏移
xmask = 控制位的大小
xtexts = 指向字符串数组的指针，每个字符串描述一个设置
```
```c
#define SOC_ENUM_DOUBLE(xreg, xshift_l, xshift_r, xmask, xtexts)
```
定义一个立体声的枚举类型控制

编解码器音频操作
-----------------
编解码器驱动还支持以下ALSA PCM操作：
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

有关详细信息，请参阅ALSA驱动PCM文档：
https://www.kernel.org/doc/html/latest/sound/kernel-api/writing-an-alsa-driver.html

DAPM 描述
---------
动态音频电源管理(DAPM)描述了编解码器电源组件及其与ASoC核心之间的关系以及相关的寄存器。请阅读 `dapm.rst` 以了解构建描述的详情。您也可以查看其他编解码器驱动中的示例。

DAPM事件处理器
---------------
此函数是一个回调，用于处理编解码器域PM调用和系统域PM调用（例如挂起和恢复）。它用于在不使用时使编解码器进入睡眠状态。
电源状态：
```
SNDRV_CTL_POWER_D0: /* 全开 */
/* vref/mid、时钟和振荡器开启，活动状态 */

SNDRV_CTL_POWER_D1: /* 部分开启 */
SNDRV_CTL_POWER_D2: /* 部分开启 */

SNDRV_CTL_POWER_D3hot: /* 关闭，但有供电 */
/* 除了vref/vmid外所有都关闭，非活动状态 */

SNDRV_CTL_POWER_D3cold: /* 完全关闭，无供电 */
```

编解码器DAC数字静音控制
-----------------------
大多数编解码器都有一个位于DAC之前的数字静音功能，可以用来最小化任何系统噪声。静音会阻止任何数字数据进入DAC。
可以创建一个回调函数，在应用或解除静音时由内核调用，针对每个编解码器DAI。
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
