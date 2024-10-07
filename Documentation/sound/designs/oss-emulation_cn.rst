关于内核OSS仿真的一些说明
=============================

2004年1月22日  Takashi Iwai <tiwai@suse.de>

模块
===

ALSA 在内核中提供了强大的OSS仿真功能。
PCM、混音器和序列设备的OSS仿真实现为附加的内核模块：snd-pcm-oss、snd-mixer-oss 和 snd-seq-oss。
当你需要访问OSS PCM、混音器或序列设备时，相应的模块需要被加载。
当调用相应服务时，这些模块会自动加载。别名定义为 ``sound-service-x-y``，其中 x 和 y 分别是卡号和次要单元号。通常你不需要自己定义这些别名。
使OSS模块自动加载所需的唯一步骤是在 ``/etc/modprobe.d/alsa.conf`` 中定义卡别名，例如：

	alias sound-slot-0 snd-emu10k1

作为第二张卡，也要定义 ``sound-slot-1``。
请注意，你不能使用别名名称作为目标名称（即 ``alias sound-slot-0 snd-card-0`` 不再像旧版 modutils 那样工作）。
当前可用的OSS配置显示在 /proc/asound/oss/sndstat 中。这与商业OSS驱动程序上的 /dev/sndstat 显示的语法相同。
在ALSA中，你可以将 /dev/sndstat 符号链接到这个 proc 文件。
请注意，此 proc 文件中列出的设备只有在相应的OSS仿真模块被加载后才会出现。即使显示“NOT ENABLED IN CONFIG”也不必担心。
设备映射
==============

ALSA 支持以下的 OSS 设备文件：
::

    PCM:
        /dev/dspX
        /dev/adspX

    混音器:
        /dev/mixerX

    MIDI:
        /dev/midi0X
        /dev/amidi0X

    序列器:
        /dev/sequencer
        /dev/sequencer2（别名 /dev/music）

其中 X 是从 0 到 7 的声卡编号
（注意：某些发行版使用诸如 /dev/midi0 和 /dev/midi1 这样的设备文件。这些文件不是用于 OSS 的，而是用于 tclmidi，这是完全不同的东西。）

与真正的 OSS 不同，ALSA 不能使用超出分配范围的设备文件。例如，第一张声卡只能使用 /dev/dsp0 和 /dev/adsp0，而不能使用 /dev/dsp1 或 /dev/dsp2。如上所述，PCM 和 MIDI 可能有两个设备。通常，第一个 PCM 设备（ALSA 中为 ``hw:0,0``）被映射到 /dev/dsp，第二个设备（``hw:0,1``）被映射到 /dev/adsp（如果可用）。对于 MIDI，则分别映射到 /dev/midi 和 /dev/amidi。

您可以通过 snd-pcm-oss 和 snd-rawmidi 的模块选项来更改这种设备映射。在 PCM 的情况下，snd-pcm-oss 提供了以下选项：

dsp_map
    分配给 /dev/dspX 的 PCM 设备编号
    （默认 = 0）
adsp_map
    分配给 /dev/adspX 的 PCM 设备编号
    （默认 = 1）

例如，要将第三 PCM 设备（``hw:0,2``）映射到 /dev/adsp0，可以这样定义：
::

    options snd-pcm-oss adsp_map=2

这些选项接受数组形式。为了配置第二张声卡，请用逗号分隔两个条目。例如，要将第二张声卡上的第三个 PCM 设备映射到 /dev/adsp1，可以这样定义：
::

    options snd-pcm-oss adsp_map=0,2

要更改 MIDI 设备的映射，snd-rawmidi 提供了以下选项：

midi_map
    分配给 /dev/midi0X 的 MIDI 设备编号
    （默认 = 0）
amidi_map
    分配给 /dev/amidi0X 的 MIDI 设备编号
    （默认 = 1）

例如，要将第一张声卡上的第三个 MIDI 设备映射到 /dev/midi00，可以这样定义：
::

    options snd-rawmidi midi_map=2

PCM 模式
========

默认情况下，ALSA 使用所谓的插件层来模拟 OSS PCM，即当声卡不支持时，尝试自动转换采样格式、速率或声道。
这可能会导致某些应用程序（如 Quake 或 Wine）出现问题，尤其是当它们仅在 MMAP 模式下使用声卡时。
在这种情况下，您可以为每个应用程序通过向 proc 文件写入命令来更改 PCM 的行为。每个 PCM 流都有一个 proc 文件，路径为 `/proc/asound/cardX/pcmY[cp]/oss`，其中 X 是声卡编号（从零开始），Y 是 PCM 设备编号（从零开始），`p` 表示播放，`c` 表示捕获。请注意，此 proc 文件仅在加载 snd-pcm-oss 模块后才存在。
命令序列具有以下语法：
::

    app_name fragments fragment_size [options]

`app_name` 是带有（优先级较高）或不带路径的应用程序名称。
`fragments` 指定片段的数量或没有指定具体数量时为零。
`fragment_size` 是以字节为单位的片段大小或未给出时为零。
`options` 是可选参数。以下选项可用：

disable
    应用程序尝试为此通道打开一个 PCM 设备，但不想使用它。
直接模式  
不使用插件  
阻塞模式  
强制开启阻塞模式  
非阻塞模式  
强制开启非阻塞模式  
部分片段  
也写入部分片段（仅影响播放）  
无静音  
不填充静音以避免咔嗒声

`disable`选项在某个流方向（播放或捕获）未被应用程序正确处理时非常有用，尽管硬件本身支持这两个方向。
`direct`选项用于绕过自动转换，对MMAP应用程序很有用。
例如，为了在不使用插件的情况下播放第一个PCM设备，可以发送如下命令：
::

	% echo "quake 0 0 direct" > /proc/asound/card0/pcm0p/oss

当quake只需要播放时，您可以附加第二个命令通知驱动程序只分配这个方向：
::

	% echo "quake 0 0 disable" > /proc/asound/card0/pcm0c/oss

proc文件的权限取决于snd模块的选项，默认设置为root，因此您可能需要超级用户权限才能发送上述命令。
阻塞和非阻塞选项用于更改打开设备文件的行为。默认情况下，ALSA的行为与原始OSS驱动程序相同，即当设备忙时不会阻塞文件，在这种情况下会返回-EBUSY错误。
可以通过snd-pcm-oss模块选项nonblock_open全局更改此阻塞行为。要将阻塞模式作为OSS设备的默认模式，请定义如下：
::

	options snd-pcm-oss nonblock_open=0

`partial-frag`和`no-silence`命令是最近添加的。这两个命令仅用于优化。前者指定只有在整个片段填满时才调用写入传输。后者停止自动提前写入静音数据。两者默认都是禁用的。
您可以通过读取proc文件来检查当前定义的配置。读取的图像可以再次发送到proc文件，因此您可以保存当前配置：
::

	% cat /proc/asound/card0/pcm0p/oss > /somewhere/oss-cfg

恢复配置如下：
::

	% cat /somewhere/oss-cfg > /proc/asound/card0/pcm0p/oss

要清除所有当前配置，发送`erase`命令如下：
::

	% echo "erase" > /proc/asound/card0/pcm0p/oss

混频器元素
===========

由于ALSA具有完全不同的混频器接口，因此OSS混频器的仿真相对复杂。ALSA基于名称字符串从多个不同的ALSA（混频器）控制中构建一个混频器元素。例如，音量元素SOUND_MIXER_PCM由“PCM Playback Volume”和“PCM Playback Switch”控制组成（对于播放方向），以及“PCM Capture Volume”和“PCM Capture Switch”（如果存在的话）。当OSS的PCM音量发生变化时，上述所有音量和开关控制都会自动调整。
默认情况下，ALSA使用以下控制来处理OSS音量：

====================	=====================	=====
OSS音量		ALSA控制		索引
====================	=====================	=====
SOUND_MIXER_VOLUME 	主控			0
SOUND_MIXER_BASS	低音调节 - 低音	0
SOUND_MIXER_TREBLE	高音调节 - 高音	0
SOUND_MIXER_SYNTH	合成器			0
SOUND_MIXER_PCM		PCM			0
SOUND_MIXER_SPEAKER	PC扬声器		0
SOUND_MIXER_LINE	线路			0
SOUND_MIXER_MIC		麦克风			0
SOUND_MIXER_CD		CD			0
SOUND_MIXER_IMIX	监控混音		0
SOUND_MIXER_ALTPCM	PCM			1
SOUND_MIXER_RECLEV	（未分配）
SOUND_MIXER_IGAIN	捕获			0
SOUND_MIXER_OGAIN	播放			0
SOUND_MIXER_LINE1	辅助			0
SOUND_MIXER_LINE2	辅助			1
SOUND_MIXER_LINE3	辅助			2
SOUND_MIXER_DIGITAL1	数字			0
SOUND_MIXER_DIGITAL2	数字			1
SOUND_MIXER_DIGITAL3	数字			2
SOUND_MIXER_PHONEIN	电话输入		0
SOUND_MIXER_PHONEOUT	电话输出		1
SOUND_MIXER_VIDEO	视频			0
SOUND_MIXER_RADIO	无线电			0
SOUND_MIXER_MONITOR	监控			0
====================	=====================	=====

第二列是相应ALSA控制的基础字符串。实际上，还将检查带有“XXX [Playback|Capture] [Volume|Switch]”的控制。
当前这些混音器元素的分配列在 `/proc` 文件中，具体路径为 `/proc/asound/cardX/oss_mixer`，内容如下所示：

```
VOLUME "Master" 0
BASS "" 0
TREBLE "" 0
SYNTH "" 0
PCM "PCM" 0
...
```

其中第一列为 OSS 音量元素，第二列为对应的 ALSA 控制的基本字符串，第三列为控制索引。当字符串为空时，表示相应的 OSS 控制不可用。

要更改这些分配，可以向此 `/proc` 文件写入配置。例如，将 "Wave Playback" 映射到 PCM 音量，可以发送如下命令：

```
% echo 'VOLUME "Wave Playback" 0' > /proc/asound/card0/oss_mixer
```

命令格式与 `/proc` 文件中的内容完全相同。你可以一次更改一个或多个元素，每行一个音量。在最后一个例子中，当 PCM 音量发生变化时，“Wave Playback Volume” 和 “Wave Playback Switch” 都会受到影响。

与 PCM `/proc` 文件的情况类似，该 `/proc` 文件的权限取决于 `snd` 模块的选项。通常你需要具有超级用户权限才能发送上述命令。

同样地，你也可以通过读取和写入整个文件来保存和恢复当前的混音器配置。

全双工流
==========

请注意，在尝试使用单个设备文件进行播放和捕获时，OSS API 不提供任何方式来分别设置不同方向上的格式、采样率或通道数量。因此：

```
io_handle = open("device", O_RDWR)
```

只有当两个方向上的值相同时，此操作才会正确运行。

为了在两个方向上使用不同的值，需要分别打开：

```
input_handle = open("device", O_RDONLY)
output_handle = open("device", O_WRONLY)
```

并为相应的句柄设置值。

不支持的功能
====================

ICE1712 驱动程序上的 MMAP
----------------------

ICE1712 仅支持非常规格式，即交错的 10 通道 24 位（打包在 32 位中）格式。因此，在 OSS 中你无法以常规格式（单声道或双声道，8 或 16 位）对缓冲区进行 MMAP。
