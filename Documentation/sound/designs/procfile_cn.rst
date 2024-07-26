===== ALSA 驱动的 Proc 文件 =====

Takashi Iwai <tiwai@suse.de>

一般说明
========

ALSA 有其自己的 proc 目录结构，即 /proc/asound。在这个目录结构中可以找到许多有用的信息。当你遇到问题需要调试时，请检查以下各节列出的文件。
每张声卡都有一个对应的子目录 cardX，其中 X 的取值范围为 0 到 7。与特定声卡相关的文件存储在以“card*”开头的子目录中。

全局信息
========

cards
    显示当前配置的 ALSA 驱动列表，包括索引、ID 字符串、简短和详细的描述。
version
    显示版本字符串和编译日期。
modules
    列出每个声卡对应的模块。
devices
    列出 ALSA 原生设备映射。
meminfo
    显示通过 ALSA 驱动分配的页面状态。仅当配置选项 ``CONFIG_SND_DEBUG=y`` 时出现。
hwdep
    列出当前可用的 hwdep 设备，格式为 ``<card>-<device>: <name>``。

pcm
    列出当前可用的 PCM 设备，格式为 ``<card>-<device>: <id>: <name> : <sub-streams>``。

timer
    列出当前可用的定时器设备。

oss/devices
    列出 OSS 设备映射。
oss/sndstat
    提供与 /dev/sndstat 兼容的输出。你可以为此创建一个到 /dev/sndstat 的符号链接。
特定声卡的文件
===================

特定声卡的文件位于 ``/proc/asound/card*`` 目录下。
一些驱动程序（例如 cmipci）有它们自己的 `/proc` 条目来显示寄存器转储等信息（例如，``/proc/asound/card*/cmipci`` 显示寄存器转储）。这些文件对于调试非常有用。

当此声卡上有 PCM 设备时，你可以看到像 pcm0p 或 pcm1c 这样的目录。它们包含了每个 PCM 流的 PCM 信息。“pcm”后的数字是 PCM 设备编号，从 0 开始，“p”或“c”表示播放或捕获方向。这个子树中的文件将在后面进行描述。

MIDI 输入/输出的状态可以在 ``midi*`` 文件中找到。它显示了设备名称以及通过 MIDI 设备接收/发送的字节数。

如果声卡装有 AC97 解码器，则存在 ``codec97#*`` 子目录（稍后会进行描述）。

如果启用了 OSS 混音器仿真（并且加载了相应的模块），则这里也会出现 oss_mixer 文件。这显示了 OSS 混音器元素到 ALSA 控制元素的当前映射。你也可以通过写入该设备来更改映射。详情请参阅 OSS-Emulation.txt。

PCM 的 `/proc` 文件
==============

``card*/pcm*/info``
	关于此 PCM 设备的一般信息：声卡号、设备号、子流等。
``card*/pcm*/xrun_debug``
	当配置 ``CONFIG_SND_DEBUG=y`` 和 ``CONFIG_SND_PCM_XRUN_DEBUG=y`` 时，此文件会出现。
此文件显示 ALSA PCM 中间层的缓冲区溢出/丢失（xrun）状态及无效 PCM 位置的调试/检查。
它可以接受一个整数值，并可以通过写入此文件来更改，例如：

		``# echo 5 > /proc/asound/card0/pcm0p/xrun_debug``

该值由以下位标志组成：

	* 位 0 = 启用 XRUN/周期的调试消息
	* 位 1 = 在检测 XRUN/周期时显示堆栈跟踪
	* 位 2 = 启用额外的周期检查

当设置了位 0 时，在检测到丢失时，驱动程序会向内核日志显示消息。当在更新周期（通常从中断处理程序调用）时检测到无效的硬件指针时，也会显示调试消息。
当第1位被设置时，驱动程序将额外显示堆栈跟踪。这可能有助于调试。
自2.6.30版本起，此选项可以使用jiffies启用硬件指针（hwptr）检查。这能检测出自发的无效指针回调值，但对于不能平滑更新指针的（通常是有bug的）硬件来说，可能会导致过多的校正。

该功能是通过设置第2位来启用的：
``card*/pcm*/sub*/info``
    这个PCM子流的一般信息
``card*/pcm*/sub*/status``
    这个PCM子流当前的状态，如已过时间、硬件位置等
``card*/pcm*/sub*/hw_params``
    为这个子流设置的硬件参数
``card*/pcm*/sub*/sw_params``
    为这个子流设置的软件参数
``card*/pcm*/sub*/prealloc``
    缓冲区预分配的信息
``card*/pcm*/sub*/xrun_injection``
    当向此proc文件写入任何值时，会触发运行中的流产生XRUN。用于故障注入
该条目仅支持写操作。
AC97 编解码器信息
======================

``card*/codec97#*/ac97#?-?``
	显示此 AC97 编解码器芯片的基本信息，例如
	名称、功能、设置
``card*/codec97#0/ac97#?-?+regs``
	显示 AC97 寄存器的转储。对于调试非常有用
当启用了 CONFIG_SND_DEBUG 时，您可以向此文件写入以
	直接更改 AC97 寄存器。传递两个十六进制数字
例如，

::

	# echo 02 9f1f > /proc/asound/card0/codec97#0/ac97#0-0+regs


USB 音频流
=================

``card*/stream*``
	显示给定声卡上每个音频流的分配和当前状态
	这些信息对于调试非常有用
HD-Audio 编解码器
===============

``card*/codec#*``
	显示一般的编解码器信息以及每个
	小部件节点的属性
``card*/eld#*``
	适用于 HDMI 或 DisplayPort 接口
显示从连接的 HDMI 沉浸式设备检索到的 ELD（类似 EDID 的数据）信息，
	并描述其音频功能和配置
可以通过执行 ``echo name hex_value > eld#*`` 修改某些 ELD 字段
仅在您确定 HDMI 沉浸式设备提供的值错误时才这样做
如果这样做可以让您的 HDMI 音频工作，请告知我们，以便我们
	可以在未来的内核版本中修复它
### 序列器信息
=====================

seq/drivers  
列出当前可用的ALSA序列器驱动程序。
seq/clients  
显示当前可用的序列器客户端和端口列表。此文件中还展示了连接状态和运行状态。
seq/queues  
列出当前分配/运行中的序列器队列。
seq/timer  
列出当前分配/运行中的序列器定时器。
seq/oss  
列出OSS兼容的序列器组件。
调试帮助？
===================

如果问题与PCM相关，首先尝试开启xrun_debug模式。这将在xrun发生时给出内核消息。
如果是真正的错误，请报告以下信息：

- 驱动程序/声卡名称，显示在`/proc/asound/cards`中。
- 如果可用的话，寄存器转储（例如`card*/cmipci`）。

如果是PCM问题，

- PCM的设置，显示在PCM子流目录中的hw_parms、sw_params以及状态中。

如果是混音器问题，

- AC97进程文件，`codec97#*/*`文件。

对于USB音频/MIDI，

- `lsusb -v`的输出结果。
- 卡目录下的`stream*`文件。

ALSA的问题跟踪系统位于：
https://bugtrack.alsa-project.org/alsa-bug/
