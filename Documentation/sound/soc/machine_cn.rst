ASoC 机器驱动程序
==================

ASoC 机器（或主板）驱动程序是将所有组件驱动程序（例如编解码器、平台和数字音频接口（DAI））组合在一起的代码。它还描述了各组件之间的关系，包括音频路径、GPIO、中断、时钟、耳机插孔和电压调节器。

机器驱动程序可以包含特定于编解码器和平台的代码。它以平台设备的形式向内核注册音频子系统，并由以下结构体表示： 
```
/* SoC 音频卡 */
struct snd_soc_card {
	char *name;

	..

	int (*probe)(struct platform_device *pdev);
	int (*remove)(struct platform_device *pdev);

	/* 在编解码器和 DAI 进行电源管理之前和之后执行任何电源管理工作 */
	int (*suspend_pre)(struct platform_device *pdev, pm_message_t state);
	int (*suspend_post)(struct platform_device *pdev, pm_message_t state);
	int (*resume_pre)(struct platform_device *pdev);
	int (*resume_post)(struct platform_device *pdev);

	..

	/* CPU <-> 编码器 DAI 链接 */
	struct snd_soc_dai_link *dai_link;
	int num_links;

	..

};
```

`probe()/remove()`
------------------
`probe` 和 `remove` 是可选的。在此处执行任何特定于机器的操作。

`suspend()/resume()`
--------------------
机器驱动程序具有 `suspend` 和 `resume` 的前处理和后处理版本，以便在编解码器、DAI 和 DMA 暂停和恢复之前和之后执行任何特定于机器的音频任务。这些操作是可选的。

机器 DAI 配置
----------------
机器 DAI 配置将所有的编解码器和 CPU DAI 组件连接在一起。还可以用于设置 DAI 系统时钟和进行任何与机器相关的 DAI 初始化，例如，机器音频映射可以连接到编解码器音频映射，未连接的编解码器引脚可以被设置为未连接状态。
使用 `struct snd_soc_dai_link` 来设置您机器中的每个 DAI。例如：
```
/* corgi 数字音频接口 - 连接编解码器 <-> CPU */
static struct snd_soc_dai_link corgi_dai = {
	.name = "WM8731",
	.stream_name = "WM8731",
	.cpu_dai_name = "pxa-is2-dai",
	.codec_dai_name = "wm8731-hifi",
	.platform_name = "pxa-pcm-audio",
	.codec_name = "wm8713-codec.0-001a",
	.init = corgi_wm8731_init,
	.ops = &corgi_ops,
};
```
然后，`struct snd_soc_card` 设置了带有其 DAI 的机器。例如：
```
/* corgi 音频机器驱动程序 */
static struct snd_soc_card snd_soc_corgi = {
	.name = "Corgi",
	.dai_link = &corgi_dai,
	.num_links = 1,
};
```

机器电源映射
----------------
机器驱动程序可以选择扩展编解码器电源映射，成为音频子系统的电源映射。这允许自动控制扬声器/耳机放大器等的电源开关。可以在机器初始化函数中将编解码器引脚连接到机器的耳机插孔插座。
机器控制
---------
可以在DAI初始化函数中添加特定于机器的音频混音器控制。
