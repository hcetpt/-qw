关于内核OSS模拟的说明
=============================

2004年1月22日  Takashi Iwai <tiwai@suse.de>

模块
===

ALSA为内核提供强大的OSS模拟功能。
PCM、混音器和序列器设备的OSS模拟是作为附加的内核模块实现的，即snd-pcm-oss、snd-mixer-oss和snd-seq-oss。
当你需要访问OSS PCM、混音器或序列器设备时，相应的模块必须被加载。
当调用相应的服务时，这些模块会自动加载。别名定义为`sound-service-x-y`，其中x和y分别是卡号和次单元号。
通常你不必自己定义这些别名。
为了自动加载OSS模块，唯一需要的步骤是在`/etc/modprobe.d/alsa.conf`中定义卡别名，例如：

	alias sound-slot-0 snd-emu10k1

如果你有第二张声卡，也定义`sound-slot-1`。
请注意，你不能再使用别名作为目标名称（即`alias sound-slot-0 snd-card-0`不再像旧版modutils那样工作）。
当前可用的OSS配置显示在/proc/asound/oss/sndstat中。这与商业OSS驱动程序提供的/dev/sndstat具有相同的语法。
在ALSA中，你可以将/dev/sndstat链接到此proc文件。
请注意，只有在加载了相应的OSS模拟模块后，此proc文件中列出的设备才会出现。即使显示“CONFIG中未启用”也不必担心。
设备映射
==============

ALSA 支持以下 OSS 设备文件：
::

	PCM:
		/dev/dspX
		/dev/adspX

	混合器(Mixer):
		/dev/mixerX

	MIDI:
		/dev/midi0X
		/dev/amidi0X

	序列器(Sequencer):
		/dev/sequencer
		/dev/sequencer2（别名 /dev/music）

其中 X 是从 0 到 7 的卡号
（注意：某些发行版有像 /dev/midi0 和 /dev/midi1 这样的设备文件。它们不是为 OSS 而设，而是为 tclmidi 设计的，这是一个完全不同的东西。）

与真正的 OSS 不同，ALSA 不能使用超过分配给它的设备文件。例如，第一张声卡只能使用 /dev/dsp0 和 /dev/adsp0，而不能使用 /dev/dsp1 或 /dev/dsp2。如上所述，PCM 和 MIDI 可能有两个设备。通常，第一个 PCM 设备（在 ALSA 中是“hw:0,0”）被映射到 /dev/dsp，而第二个设备（“hw:0,1”）则映射到 /dev/adsp（如果可用）。对于 MIDI，则分别对应 /dev/midi 和 /dev/amidi。
您可以通过 snd-pcm-oss 和 snd-rawmidi 模块选项来更改此设备映射。对于 PCM，snd-pcm-oss 提供了以下选项：

dsp_map
	分配给 /dev/dspX 的 PCM 设备编号
	（默认值 = 0）
adsp_map
	分配给 /dev/adspX 的 PCM 设备编号
	（默认值 = 1）

例如，要将第三 PCM 设备（“hw:0,2”）映射到 /dev/adsp0，请这样定义：
::

	options snd-pcm-oss adsp_map=2

这些选项接受数组形式。为了配置第二张卡，需要指定两个以逗号分隔的条目。例如，要将第二张卡上的第三个 PCM 设备映射到 /dev/adsp1，请如下定义：
::

	options snd-pcm-oss adsp_map=0,2

为了改变 MIDI 设备的映射，snd-rawmidi 提供了以下选项：

midi_map
	分配给 /dev/midi0X 的 MIDI 设备编号
	（默认值 = 0）
amidi_map
	分配给 /dev/amidi0X 的 MIDI 设备编号
	（默认值 = 1）

例如，要将第一张卡上的第三个 MIDI 设备映射到 /dev/midi00，请这样定义：
::

	options snd-rawmidi midi_map=2


PCM 模式
========

默认情况下，ALSA 使用所谓的插件层来模拟 OSS PCM，即当声卡不原生支持时尝试自动转换采样格式、采样率或声道数
这可能会导致一些应用程序（如 Quake 或 Wine）出现问题，特别是当它们只使用 MMAP 模式时
在这种情况下，您可以通过向 proc 文件写入命令来按应用程序更改 PCM 的行为。每个 PCM 流都有一个 proc 文件，“/proc/asound/cardX/pcmY[cp]/oss”，其中 X 是卡号（以零为基础），Y 是 PCM 设备号（以零为基础），而“p”代表播放，“c”代表捕获。请注意，此 proc 文件仅在加载 snd-pcm-oss 模块后才存在
命令序列具有以下语法：
::

	app_name fragments fragment_size [options]

`app_name` 是应用程序的名称，可以带有（优先级较高）或不带有路径
`fragments` 指定片段的数量或如果没有给出特定数量则为零
`fragment_size` 是以字节为单位的片段大小或如果没有给出则为零
`options` 是可选参数。以下选项可用：

disable
	应用程序试图为此通道打开一个 pcm 设备，但不想使用它
### 直接模式
   不使用插件

### 阻塞模式
   强制启用阻塞打开模式

### 非阻塞模式
   强制启用非阻塞打开模式

### 部分片段
   同时写入部分片段（仅影响播放）

### 不静音
   不填充静音以避免咔哒声

`disable` 选项在某个流方向（播放或捕获）虽被硬件支持但应用程序处理不当的情况下非常有用。
`direct` 选项如上所述，用于绕过自动转换，对MMAP应用程序很有用。

例如，要不使用插件播放第一个PCM设备以供Quake使用，可以通过echo命令如下发送：
```
% echo "quake 0 0 direct" > /proc/asound/card0/pcm0p/oss
```

如果Quake只需要播放功能，可以通过追加第二个命令来通知驱动程序只分配这个方向：
```
% echo "quake 0 0 disable" > /proc/asound/card0/pcm0c/oss
```

proc文件的权限取决于snd模块选项，默认设置为root用户，因此发送上述命令可能需要超级用户权限。
阻塞和非阻塞选项用于改变打开设备文件的行为。默认情况下，ALSA像原始OSS驱动程序一样，在忙时不会阻塞文件，并在此情况下返回 `-EBUSY` 错误。
这种阻塞行为可以通过snd-pcm-oss模块选项`nonblock_open`全局更改。若要将阻塞模式作为OSS设备的默认模式，请定义如下：
```
options snd-pcm-oss nonblock_open=0
```

`partial-frag` 和 `no-silence` 命令最近已被添加，这两个命令仅供优化使用。前者指定只有当整个片段被填满时才调用写传输；后者停止自动提前写入静音数据。两者默认都处于禁用状态。
可以通过读取proc文件检查当前定义的配置。读取的内容可以再次发送到proc文件，因此您可以保存当前配置：
```
% cat /proc/asound/card0/pcm0p/oss > /somewhere/oss-cfg
```

然后恢复它如下：
```
% cat /somewhere/oss-cfg > /proc/asound/card0/pcm0p/oss
```

此外，要清除所有当前配置，可以发送 `erase` 命令如下：
```
% echo "erase" > /proc/asound/card0/pcm0p/oss
```

### 混音器元素

由于ALSA拥有完全不同的混音器接口，因此OSS混音器的仿真相对复杂。ALSA根据名称字符串从多个不同的ALSA（混音器）控制中构建一个混音器元素。例如，音量元素 `SOUND_MIXER_PCM` 由“PCM Playback Volume”和“PCM Playback Switch”控制组成，用于播放方向，而“PCM Capture Volume”和“PCM Capture Switch”用于捕获方向（如果存在）。当OSS中的PCM音量发生变化时，上述所有的音量和开关控制都会自动调整。
默认情况下，ALSA使用以下控制来处理OSS音量：

| OSS音量       | ALSA 控制      | 索引 |
|-------------|--------------|-----|
| SOUND_MIXER_VOLUME | Master     | 0  |
| SOUND_MIXER_BASS  | Tone Control - Bass | 0  |
| SOUND_MIXER_TREBLE | Tone Control - Treble | 0  |
| SOUND_MIXER_SYNTH  | Synth      | 0  |
| SOUND_MIXER_PCM    | PCM        | 0  |
| SOUND_MIXER_SPEAKER | PC Speaker | 0  |
| SOUND_MIXER_LINE   | Line       | 0  |
| SOUND_MIXER_MIC    | Mic        | 0  |
| SOUND_MIXER_CD     | CD         | 0  |
| SOUND_MIXER_IMIX   | Monitor Mix | 0  |
| SOUND_MIXER_ALTPCM | PCM        | 1  |
| SOUND_MIXER_RECLEV | （未分配） |
| SOUND_MIXER_IGAIN  | Capture    | 0  |
| SOUND_MIXER_OGAIN  | Playback   | 0  |
| SOUND_MIXER_LINE1  | Aux        | 0  |
| SOUND_MIXER_LINE2  | Aux        | 1  |
| SOUND_MIXER_LINE3  | Aux        | 2  |
| SOUND_MIXER_DIGITAL1 | Digital | 0  |
| SOUND_MIXER_DIGITAL2 | Digital | 1  |
| SOUND_MIXER_DIGITAL3 | Digital | 2  |
| SOUND_MIXER_PHONEIN | Phone | 0  |
| SOUND_MIXER_PHONEOUT | Phone | 1  |
| SOUND_MIXER_VIDEO   | Video     | 0  |
| SOUND_MIXER_RADIO   | Radio     | 0  |
| SOUND_MIXER_MONITOR | Monitor   | 0  |

第二列是相应ALSA控制的基础字符串。实际上，除了基础字符串之外，还会检查带有 “XXX [Playback|Capture] [Volume|Switch]” 的控制。
这些混音器元素的当前分配列在 `/proc` 文件中，具体为 `/proc/asound/cardX/oss_mixer`，其内容如下所示：

	VOLUME "Master" 0
	BASS "" 0
	TREBLE "" 0
	SYNTH "" 0
	PCM "PCM" 0
	...
其中第一列为 OSS 音量元素，第二列为相应的 ALSA 控制的基础字符串，第三列为控制索引。当字符串为空时，意味着对应的 OSS 控制不可用。
为了更改此分配，您可以将配置写入该 `/proc` 文件。例如，要将 "Wave Playback" 映射到 PCM 音量，可以发送如下命令：

	% echo 'VOLUME "Wave Playback" 0' > /proc/asound/card0/oss_mixer

命令与 `/proc` 文件中的内容完全相同。您可以更改一个或多个元素，每个音量一行。在最后一个示例中，当 PCM 音量改变时，“Wave Playback Volume” 和 “Wave Playback Switch” 都会受到影响。
如同 PCM 的 `/proc` 文件一样，这些 `/proc` 文件的权限取决于 snd 模块选项。您可能需要以超级用户身份发送上述命令。
与 PCM 的 `/proc` 文件一样，您可以通过读取和写入整个文件来保存和恢复当前的混音器配置。

双向流
======

请注意，尝试使用单一设备文件进行播放和捕获时，OSS API 没有提供任何方式来分别设置不同方向上的格式、采样率或声道数量。因此，

	io_handle = open("device", O_RDWR)

仅当两个方向上的值相同时才会正确工作。
为了在两个方向上使用不同的值，请使用：

	input_handle = open("device", O_RDONLY)
	output_handle = open("device", O_WRONLY)

并为相应的句柄设置值。

不支持的功能
=============

ICE1712 驱动程序上的 MMAP
----------------------
ICE1712 只支持非常规的格式，即交错的 10 声道 24 位（打包在 32 位中）格式。因此，在 OSS 中您不能像常规格式（单声道或双声道，8 或 16 位）那样对缓冲区进行内存映射。
