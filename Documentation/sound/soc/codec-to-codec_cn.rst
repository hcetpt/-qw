==============================
创建ALSA DAPM中的Codec到Codec的DAI链路
==============================

音频流通常总是从CPU流向Codec，因此您的系统看起来如下：
::

   ---------          ---------
  |         |  dai   |         |
      CPU    ------->    codec
  |         |        |         |
   ---------          ---------

如果您的系统如下所示：
::

                       ---------
                      |         |
                        codec-2
                      |         |
                      ---------
                           |
                         dai-2
                           |
   ----------          ---------
  |          |  dai-1 |         |
      CPU     ------->  codec-1
  |          |        |         |
   ----------          ---------
                           |
                         dai-3
                           |
                       ---------
                      |         |
                        codec-3
                      |         |
                       ---------

假设codec-2是一个蓝牙芯片，而codec-3连接到了一个扬声器，并且有以下场景：codec-2接收音频数据，用户希望不通过CPU将这些音频播放出来。这种情况下，应该使用Codec到Codec连接。

在您的机器文件中，DAI链路应该如下所示：
::

 /*
  * 此PCM流仅支持24位、2声道和48k采样率
*/
 static const struct snd_soc_pcm_stream dsp_codec_params = {
        .formats = SNDRV_PCM_FMTBIT_S24_LE,
        .rate_min = 48000,
        .rate_max = 48000,
        .channels_min = 2,
        .channels_max = 2,
 };

 {
    .name = "CPU-DSP",
    .stream_name = "CPU-DSP",
    .cpu_dai_name = "samsung-i2s.0",
    .codec_name = "codec-2",
    .codec_dai_name = "codec-2-dai_name",
    .platform_name = "samsung-i2s.0",
    .dai_fmt = SND_SOC_DAIFMT_I2S | SND_SOC_DAIFMT_NB_NF
            | SND_SOC_DAIFMT_CBM_CFM,
    .ignore_suspend = 1,
    .c2c_params = &dsp_codec_params,
    .num_c2c_params = 1,
 },
 {
    .name = "DSP-CODEC",
    .stream_name = "DSP-CODEC",
    .cpu_dai_name = "wm0010-sdi2",
    .codec_name = "codec-3",
    .codec_dai_name = "codec-3-dai_name",
    .dai_fmt = SND_SOC_DAIFMT_I2S | SND_SOC_DAIFMT_NB_NF
            | SND_SOC_DAIFMT_CBM_CFM,
    .ignore_suspend = 1,
    .c2c_params = &dsp_codec_params,
    .num_c2c_params = 1,
 };

以上代码片段来自sound/soc/samsung/speyside.c。请注意“c2c_params”回调，它告诉DAPM此DAI链路是Codec到Codec连接。
在DAPM核心中，为播放路径创建了一个从cpu_dai播放小部件到codec_dai捕捉小部件的路由，反之亦然适用于捕捉路径。为了使上述路由被触发，DAPM需要找到一个有效的端点，该端点可以是对应于播放和捕捉路径的sink或source小部件。
为了触发此DAI链路小部件，可以创建一个薄型Codec驱动程序，例如wm8727.c文件中所示，即使设备不需要控制，它也会设置适当的约束。
请确保相应地命名您的CPU和Codec播放和捕捉DAI名称，分别以“Playback”和“Capture”结尾，因为DAPM核心会根据名称链接并供电这些DAI。
在一个“simple-audio-card”中的DAI链路，当链路上的所有DAI都属于Codec组件时，会自动检测为Codec到Codec连接。
DAI链路将使用链路上所有DAI支持的流参数子集（通道数、格式、采样率）进行初始化。由于无法在设备树中提供这些参数，这主要适用于与简单的固定功能Codec通信，如蓝牙控制器或蜂窝调制解调器。
