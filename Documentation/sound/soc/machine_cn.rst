===================
ASoC 机器驱动
===================

ASoC 机器（或板级）驱动是将所有组件驱动程序（例如编解码器、平台和DAI）连接在一起的代码。它还描述了各组件之间的关系，包括音频路径、GPIO、中断、时钟、耳机插孔和电压调节器。机器驱动可以包含特定于编解码器和平台的代码。它将音频子系统作为平台设备注册到内核，并由以下结构表示：-
::

  /* SoC 机器 */
  struct snd_soc_card {
	char *name;

	..
	int (*probe)(struct platform_device *pdev);
	int (*remove)(struct platform_device *pdev);

	/* 预处理和后处理PM函数用于在编解码器和DAI执行任何PM工作之前和之后完成任何PM工作。 */
	int (*suspend_pre)(struct platform_device *pdev, pm_message_t state);
	int (*suspend_post)(struct platform_device *pdev, pm_message_t state);
	int (*resume_pre)(struct platform_device *pdev);
	int (*resume_post)(struct platform_device *pdev);

	..
/* CPU <--> 编解码器 DAI 链接  */
	struct snd_soc_dai_link *dai_link;
	int num_links;

	..
};

probe()/remove()
----------------
probe/remove 是可选的。在这里执行任何特定于机器的初始化操作。
suspend()/resume()
------------------
机器驱动有预处理和后处理的挂起和恢复版本，以处理在编解码器、DAI和DMA挂起和恢复之前或之后必须执行的任何机器音频任务。可选
机器 DAI 配置
-------------------------
机器 DAI 配置将所有编解码器和 CPU DAI 连接在一起。它还可以用于设置 DAI 系统时钟和任何与机器相关的 DAI 初始化，例如机器音频映射可以连接到编解码器音频映射，未连接的编解码器引脚可以被设置为未连接状态。
使用 struct snd_soc_dai_link 来设置你的机器中的每个 DAI。例如：
::

  /* corgi 数字音频接口粘合 - 连接编解码器 <--> CPU */
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

然后，使用 struct snd_soc_card 设置带有其 DAI 的机器。例如：
::

  /* corgi 音频机器驱动 */
  static struct snd_soc_card snd_soc_corgi = {
	.name = "Corgi",
	.dai_link = &corgi_dai,
	.num_links = 1,
  };

机器电源映射
-----------------

机器驱动可以选择扩展编解码器电源映射，并成为音频子系统的音频电源映射。这允许自动控制扬声器/耳机放大器等的上电/下电。可以在机器初始化函数中将编解码器引脚连接到机器的耳机插座。
机器控制
----------------

可以在DAI初始化函数中添加特定于机器的音频混音器控制。
