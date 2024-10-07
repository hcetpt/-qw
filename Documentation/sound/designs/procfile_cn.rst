ALSA 驱动程序的 Proc 文件
==========================

Takashi Iwai <tiwai@suse.de>

概述
=======

ALSA 有自己的 proc 目录树，即 /proc/asound。许多有用的信息都可以在这个目录树中找到。当你遇到问题需要调试时，请检查以下各节中列出的文件。每张声卡都有一个对应的子目录 cardX，其中 X 的取值范围为 0 到 7。特定于声卡的文件存储在 ``card*`` 子目录中。

全局信息
==================

cards
	显示当前配置的 ALSA 驱动程序列表，包括索引、ID 字符串、简短描述和详细描述。
version
	显示版本字符串和编译日期。
modules
	列出每个声卡对应的模块。
devices
	列出 ALSA 原生设备映射。
meminfo
	显示通过 ALSA 驱动程序分配的页面状态。仅当 ``CONFIG_SND_DEBUG=y`` 时出现。
hwdep
	以 ``<card>-<device>: <name>`` 格式列出当前可用的 hwdep 设备。
pcm
	以 ``<card>-<device>: <id>: <name> : <sub-streams>`` 格式列出当前可用的 PCM 设备。
timer
	列出当前可用的定时器设备。

oss/devices
	列出 OSS 设备映射。
oss/sndstat
	提供与 /dev/sndstat 兼容的输出。你可以将此文件符号链接到 /dev/sndstat。
特定声卡的文件
===================

特定声卡的文件位于 ``/proc/asound/card*`` 目录中。
某些驱动程序（例如 cmipci）有自己的 proc 条目来显示寄存器转储等信息（例如，``/proc/asound/card*/cmipci`` 显示寄存器转储）。这些文件对于调试非常有帮助。

当此声卡上有 PCM 设备时，你可以看到类似于 pcm0p 或 pcm1c 的目录。它们保存了每个 PCM 流的 PCM 信息。`pcm` 后面的数字是 PCM 设备编号，从 0 开始，最后的 `p` 或 `c` 分别表示播放或捕捉方向。此子树中的文件将在后面描述。

MIDI I/O 状态可以在 ``midi*`` 文件中找到。它显示了设备名称和通过 MIDI 设备接收/传输的字节数。

如果声卡配备了 AC97 编解码器，则会有 ``codec97#*`` 子目录（稍后描述）。

如果启用了 OSS 混音器仿真（并且加载了模块），则也会在此处出现 oss_mixer 文件。这显示了 OSS 混音器元素到 ALSA 控制元素的当前映射。可以通过写入该设备来更改映射。详情请参阅 OSS-Emulation.txt。

PCM Proc 文件
==============

``card*/pcm*/info``
	此 PCM 设备的一般信息：声卡编号、设备编号、子流等。
``card*/pcm*/xrun_debug``
	当 ``CONFIG_SND_DEBUG=y`` 和 ``CONFIG_SND_PCM_XRUN_DEBUG=y`` 时，此文件会出现。
这显示了 ALSA PCM 中间层的 xrun（= 缓冲区溢出/xrun）和无效 PCM 位置调试/检查的状态。
它接受一个整数值，可以通过写入该文件来更改，例如：

		```
		# echo 5 > /proc/asound/card0/pcm0p/xrun_debug
		```

该值由以下位标志组成：

	* 位 0 = 启用 XRUN/jiffies 调试消息
	* 位 1 = 在 XRUN/jiffies 检查时显示堆栈跟踪
	* 时隙 2 = 启用额外的 jiffies 检查

当设置了位 0 时，驱动程序会在检测到 xrun 时将消息显示在内核日志中。当在更新周期时（通常从中断处理程序调用）检测到无效硬件指针时，也会显示调试消息。
当第1位被设置时，驱动程序将额外显示堆栈跟踪。这可能有助于调试。

从2.6.30版本开始，此选项可以使用jiffies启用硬件指针检查。这可以检测突发的无效指针回调值，但对于那些不能平滑更新指针的（通常是存在问题的）硬件来说，可能会导致过多的校正。

此功能通过设置第2位来启用：
``card*/pcm*/sub*/info``
此PCM子流的一般信息。
``card*/pcm*/sub*/status``
此PCM子流的当前状态、已用时间、硬件位置等。
``card*/pcm*/sub*/hw_params``
为此子流设置的硬件参数。
``card*/pcm*/sub*/sw_params``
为此子流设置的软件参数。
``card*/pcm*/sub*/prealloc``
缓冲区预分配信息。
``card*/pcm*/sub*/xrun_injection``
当向此proc文件写入任何值时，会触发正在运行的流中的XRUN。用于故障注入。
此条目仅支持写操作。
AC97 编解码器信息
======================

``card*/codec97#*/ac97#?-?``
	显示此 AC97 编解码器芯片的基本信息，如名称、功能、设置等。
``card*/codec97#0/ac97#?-?+regs``
	显示 AC97 寄存器转储。对于调试非常有用。
当启用 CONFIG_SND_DEBUG 时，可以向此文件写入以直接更改 AC97 寄存器。传递两个十六进制数。
例如，

::

	# echo 02 9f1f > /proc/asound/card0/codec97#0/ac97#0-0+regs


USB 音频流
=================

``card*/stream*``
	显示指定声卡的每个音频流的分配和当前状态。这些信息对于调试非常有用。

高清音频 (HD-Audio) 编解码器
==============================

``card*/codec#*``
	显示基本编解码器信息及每个小部件节点的属性。
``card*/eld#*``
	适用于 HDMI 或 DisplayPort 接口。
显示从连接的 HDMI 接收设备获取的 ELD（类似 EDID 的数据）信息，并描述其音频功能和配置。
某些 ELD 字段可以通过执行 ``echo name hex_value > eld#*`` 来修改。
仅在确认 HDMI 接收设备提供的值错误时进行修改。
如果这样操作后您的 HDMI 音频工作正常，请向我们报告，以便我们在未来的内核版本中修复该问题。
### 序列器信息
=====================

seq/drivers  
列出当前可用的 ALSA 序列器驱动程序

seq/clients  
显示当前可用的序列器客户端和端口。此文件中还会显示连接状态和运行状态

seq/queues  
列出当前分配/运行中的序列器队列

seq/timer  
列出当前分配/运行中的序列器定时器

seq/oss  
列出与 OSS 兼容的序列器组件

### 调试帮助？
===================

当问题与 PCM 相关时，首先尝试开启 xrun_debug 模式。这会在内核消息中显示 xrun 发生的时间和位置。
如果确实是一个 bug，请报告以下信息：

- 驱动程序/声卡名称，显示在 `/proc/asound/cards` 中
- 如果可用，寄存器转储（例如 `card*/cmipci`）

如果是 PCM 问题，

- PCM 的设置，显示在 PCM 子流目录中的 hw_parms、sw_params 和状态

如果是混音器问题，

- AC97 进程文件，`codec97#*/*` 文件

对于 USB 音频/MIDI，

- `lsusb -v` 的输出
- 卡目录中的 `stream*` 文件

ALSA 的 Bug 跟踪系统位于：
https://bugtrack.alsa-project.org/alsa-bug/
