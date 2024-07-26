ASoC 平台驱动程序
====================

ASoC 平台驱动程序类可以分为音频 DMA 驱动程序、SoC DAI 驱动程序和 DSP 驱动程序。平台驱动程序仅针对 SoC CPU，不得包含任何与特定板卡相关的代码。

音频 DMA
=========

平台 DMA 驱动程序可选地支持以下 ALSA 操作：  
::

  /* SoC 音频操作 */
  struct snd_soc_ops {
	int (*startup)(struct snd_pcm_substream *);
	void (*shutdown)(struct snd_pcm_substream *);
	int (*hw_params)(struct snd_pcm_substream *, struct snd_pcm_hw_params *);
	int (*hw_free)(struct snd_pcm_substream *);
	int (*prepare)(struct snd_pcm_substream *);
	int (*trigger)(struct snd_pcm_substream *, int);
  };

平台驱动程序通过 `struct snd_soc_component_driver` 导出其 DMA 功能：  
::

  struct snd_soc_component_driver {
	const char *name;

	..
int (*probe)(struct snd_soc_component *);
	void (*remove)(struct snd_soc_component *);
	int (*suspend)(struct snd_soc_component *);
	int (*resume)(struct snd_soc_component *);

	/* PCM 创建和销毁 */
	int (*pcm_new)(struct snd_soc_pcm_runtime *);
	void (*pcm_free)(struct snd_pcm *);

	..
const struct snd_pcm_ops *ops;
	const struct snd_compr_ops *compr_ops;
	..
};

有关音频 DMA 的详细信息，请参阅 ALSA 驱动文档：
https://www.kernel.org/doc/html/latest/sound/kernel-api/writing-an-alsa-driver.html

一个示例 DMA 驱动程序是 soc/pxa/pxa2xx-pcm.c

SoC DAI 驱动程序
==================

每个 SoC DAI 驱动程序必须提供以下功能：

1. 数字音频接口（DAI）描述
2. 数字音频接口配置
3. PCM 描述
4. SYSCLK 配置
5. 挂起和恢复（可选）

请参阅 codec.rst 获取关于第 1 至 4 项的描述。

SoC DSP 驱动程序
==================

每个 SoC DSP 驱动程序通常提供以下功能：

1. DAPM 图形
2. 混音器控制
3. DMA I/O 到/从 DSP 缓冲区（如果适用）
4. 定义 DSP 前端（FE）PCM 设备

请参阅 DPCM.txt 获取关于第 4 项的描述。
