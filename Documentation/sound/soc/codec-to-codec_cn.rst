为ALSA DAPM创建编解码器到编解码器的DAI链接

音频流通常总是从CPU流向编解码器，因此您的系统看起来如下所示：
::

   ---------          ---------
  |         |  dai   |         |
      CPU    ------->    codec
  |         |        |         |
   ---------          ---------

如果您的系统看起来像下面这样：
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

假设codec-2是一个蓝牙芯片，而codec-3连接到了一个扬声器，并且存在以下情况：
codec-2接收到音频数据，用户希望不通过CPU直接通过codec-3播放这些音频。上述情况正是使用编解码器到编解码器连接的理想案例。
在您的机器文件中，您的dai_link应该如下所示：
::

 /*
  * 此PCM流仅支持24位、2声道和
  * 48k采样率
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

以上代码片段参考自sound/soc/samsung/speyside.c
请注意“c2c_params”回调，它告诉DAPM这是编解码器到编解码器的链接。
在DAPM核心中，会为播放路径在CPU_DAI播放小部件和codec_DAI捕获小部件之间创建一条路径，反之亦然对于捕获路径。为了触发这条路径，DAPM需要找到一个有效的终点，这个终点可以是与播放和捕获路径相对应的接收或源小部件。
为了触发此dai_link小部件，可以为扬声器放大器创建一个简单的编解码器驱动程序，如wm8727.c文件中所演示，即使不需要控制也可以设置适当的设备约束。
确保您相应的CPU和编解码器的播放和捕获DAI名称分别以“Playback”和“Capture”结尾，因为DAPM核心将根据名称链接并为这些DAI供电。
在一个“simple-audio-card”中的dai_link如果所有链路上的DAI都属于编解码器组件，则会被自动识别为编解码器到编解码器链接。
dai_link将以所有链路上DAI支持的流参数子集（通道数、格式、采样率）进行初始化。由于无法在设备树中提供这些参数，这主要适用于与简单的固定功能编解码器通信，例如蓝牙控制器或蜂窝调制解调器。
