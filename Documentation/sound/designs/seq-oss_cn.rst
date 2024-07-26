===============================
ALSA 上的 OSS 序列器仿真
===============================

版权所有 (c) 1998,1999 由 沼田 隆司

版本 0.1.8；1999 年 11 月 16 日

描述
====

此目录包含在 ALSA 上的 OSS 序列器仿真驱动程序。请注意，该程序仍处于开发阶段。
它的作用是 —— 它提供了 OSS 序列器的仿真，通过 `/dev/sequencer` 和 `/dev/music` 设备访问
如果准备了适当的 ALSA 序列器，大多数使用 OSS 的应用程序都可以运行。
此驱动程序仿真了以下特性：

* 正常的序列器和 MIDI 事件：

    这些事件将转换为 ALSA 序列器事件，并发送到相应的端口
* 定时器事件：

    定时器无法通过 ioctl 选择。控制速率固定为每秒 100 个单位，无论系统频率如何。也就是说，在 Alpha 系统上，一个节拍始终为 1/100 秒。基本速率和节奏可以在 `/dev/music` 中更改
* 音色加载：

    是否支持音色加载完全取决于合成器驱动程序，因为音色加载是通过回调到合成器驱动程序来实现的
* 输入/输出控制：

    大多数控制都被接受。某些控制取决于合成器驱动程序，这与原始 OSS 类似
此外，您还可以找到以下高级功能：

* 更好的队列机制：

    在处理之前，事件被放入队列
* 多个应用程序：

    您可以同时运行两个或多个应用程序（即使是针对 OSS 序列器）！
    但是，每个 MIDI 设备都是独占使用的 —— 如果某个应用程序已经打开了一个 MIDI 设备，其他应用程序就不能使用它。合成器设备没有此类限制
* 实时事件处理：

    无需使用超出范围的 ioctl 即可实时处理事件。要切换到实时模式，请发送 ABSTIME 0 事件。随后的事件将不经过队列而直接进行实时处理。要关闭实时模式，请发送 RELTIME 0 事件
* ``/proc`` 接口：

    应用程序和设备的状态可以通过 ``/proc/asound/seq/oss`` 在任何时候展示。在后续版本中，
    配置也将通过 ``/proc`` 接口进行更改。
安装
====

使用支持音序器（``--with-sequencer=yes``）和 OSS 模拟（``--with-oss=yes``）的选项运行配置脚本。将创建一个模块 ``snd-seq-oss.o``。
如果您的声卡的合成器模块支持 OSS 模拟（到目前为止，只有 Emu8000 驱动程序支持），则此模块将自动加载。
否则，您需要手动加载此模块。
开始时，此模块会探测所有已连接到音序器的 MIDI 端口。此后，端口的创建和删除将由 ALSA 音序器的通告机制监控。
可以在 ``/proc`` 接口中找到可用的合成器和 MIDI 设备。
运行 ``cat /proc/asound/seq/oss``，并检查设备。例如，
如果您使用 AWE64 卡，则会看到如下所示的内容：
::

    OSS 音序器模拟版本 0.1.8
    ALSA 客户编号 63
    ALSA 接收端口 0

    应用程序数量：0

    合成器设备数量：1
    synth 0: [EMU8000]
      类型 0x1 ：子类型 0x20 ：音轨 32
      功能：ioctl 已启用 / load_patch 已启用

    MIDI 设备数量：3
    midi 0: [Emu8000 Port-0] ALSA 端口 65:0
      功能写入 / 打开无

    midi 1: [Emu8000 Port-1] ALSA 端口 65:1
      功能写入 / 打开无

    midi 2: [0: MPU-401 (UART)] ALSA 端口 64:0
      功能读/写 / 打开无

请注意，设备编号可能与 ``/proc/asound/oss-devices`` 中的信息或原始 OSS 驱动程序中的信息不同。
使用 ``/proc/asound/seq/oss`` 中列出的设备编号通过 OSS 音序器模拟播放。
使用合成器设备
===============

运行您喜欢的程序。我已经测试了 playmidi-2.4、awemidi-0.4.3、gmod-3.1 和 xmp-1.1.5。您也可以通过 ``/dev/sequencer`` 加载样本，就像 sfxload 一样。
如果低级驱动程序支持对合成器设备的多重访问（如 Emu8000 驱动程序），则允许两个或多个应用程序同时运行。
使用 MIDI 设备
==============

到目前为止，仅测试了 MIDI 输出。完全没有检查 MIDI 输入，但希望它能工作。使用 ``/proc/asound/seq/oss`` 中列出的设备编号。
请注意，这些数字大多与
``/proc/asound/oss-devices`` 
中的列表不同。
模块选项
==============

以下模块选项是可用的：

maxqlen
  指定最大读/写队列长度。此队列是为OSS音序器专用的，因此它独立于ALSA音序器的队列长度。默认值为1024。
seq_oss_debug
  指定调试级别，并接受零（=无调试信息）或正整数。默认值为0。
队列机制
==============

OSS音序器仿真使用了一个ALSA优先级队列。来自``/dev/sequencer``的事件被处理并放入由模块选项指定的队列中。
所有来自``/dev/sequencer``的事件在开始时都会被解析。
定时事件也会在这个时刻被解析，以便事件可以实时处理。发送一个ABSTIME 0事件会切换到实时模式，而发送一个RELTIME 0事件会关闭该模式。
在实时模式下，所有事件都会立即被分发。
排队的事件会在ALSA音序器调度器安排的时间后被分发到相应的ALSA音序器端口。
如果写入队列已满，则应用程序会在阻塞模式下睡眠，直到有一定数量（默认为一半）的空间变为空。也实现了对写入时间的同步。
从MIDI设备输入或回声反馈事件会被存储在读取FIFO队列中。如果应用程序以阻塞模式读取``/dev/sequencer``，则进程将被唤醒。
合成器设备接口
===============================

注册
------------

要注册一个OSS合成器设备，使用 `snd_seq_oss_synth_register()` 函数：
::

  int snd_seq_oss_synth_register(char *name, int type, int subtype, int nvoices,
          snd_seq_oss_callback_t *oper, void *private_data)

参数 `name`、`type`、`subtype` 和 `nvoices`
用于创建 ioctl 所需的适当 synth_info 结构。返回值是此设备的索引号。此索引必须被记住以便注销。如果注册失败，则返回 -errno。
要释放此设备，请调用 `snd_seq_oss_synth_unregister()` 函数：
::

  int snd_seq_oss_synth_unregister(int index)

其中 `index` 是由注册函数返回的索引号。
回调
---------

OSS合成器设备具有样本下载和 ioctl（如样本重置）的功能。在OSS仿真中，这些特殊功能通过回调实现。注册参数 `oper` 用于指定这些回调。以下回调函数必须定义：
::

  snd_seq_oss_callback_t:
   int (*open)(snd_seq_oss_arg_t *p, void *closure);
   int (*close)(snd_seq_oss_arg_t *p);
   int (*ioctl)(snd_seq_oss_arg_t *p, unsigned int cmd, unsigned long arg);
   int (*load_patch)(snd_seq_oss_arg_t *p, int format, const char *buf, int offs, int count);
   int (*reset)(snd_seq_oss_arg_t *p);

除了 `open` 和 `close` 回调之外，其余的可以为 NULL。
每个回调函数都接受类型为 `snd_seq_oss_arg_t` 的第一个参数：
::

  struct snd_seq_oss_arg_t {
      int app_index;
      int file_mode;
      int seq_mode;
      snd_seq_addr_t addr;
      void *private_data;
      int event_passing;
  };

前三个字段 `app_index`、`file_mode` 和 `seq_mode`
由OSS序列器初始化。`app_index` 是应用程序索引，对每个打开OSS序列器的应用程序都是唯一的。`file_mode` 是位标志，表示文件操作模式。具体含义请参阅 `seq_oss.h`。`seq_mode` 是序列器的操作模式。在当前版本中，仅使用 `SND_OSSSEQ_MODE_SYNTH`
接下来的两个字段 `addr` 和 `private_data` 必须在打开回调中由合成器驱动程序填充。`addr` 包含分配给此设备的ALSA序列器端口地址。如果驱动程序为 `private_data` 分配了内存，则必须在关闭回调中自行释放。
最后一个字段 `event_passing` 指示如何转换音符开/关事件。在 `PROCESS_EVENTS` 模式下，将音符255视为音量变化，并将按键压力事件传递给端口。在 `PASS_EVENTS` 模式下，所有音符开/关事件未经修改直接传递给端口。`PROCESS_KEYPRESS` 模式检查高于128的音符，并将其视为按键压力事件（主要用于Emu8000驱动程序）
打开回调
------------

`open` 在每次应用程序使用OSS序列器打开此设备时被调用。这不能为 NULL。通常，打开回调执行以下步骤：

1. 分配私有数据记录
2. 创建一个ALSA序列器端口
3. 在 `arg->addr` 上设置新端口地址
#. 在 `arg->private_data` 上设置私有数据记录指针。
请注意，此合成端口的 `port_info` 中的类型位标志不应包含
`TYPE_MIDI_GENERIC`
位。相反，应当使用 `TYPE_SPECIFIC`。同时，也不应包含 `CAP_SUBSCRIPTION`
位。这是为了将其与其它常规 MIDI 设备区分开来。如果打开过程成功，则返回零。否则，
返回 -errno。

Ioctl 回调
----------

`ioctl` 回调在序列器接收到特定于设备的 ioctl 时被调用。以下两种 ioctl 应当由该回调处理：

IOCTL_SEQ_RESET_SAMPLES
    重置所有内存中的样本 — 返回 0

IOCTL_SYNTH_MEMAVL
    返回可用内存大小

FM_4OP_ENABLE
    通常可以忽略

其他 ioctl 由序列器内部处理，不会传递给低级驱动程序。

加载补丁回调
-------------

`load_patch` 回调用于样本下载。此回调必须从用户空间读取数据并传输到每个设备。成功时返回 0，失败时返回 -errno。格式参数是补丁信息记录中的补丁键。buf 是存储补丁信息记录的用户空间指针。offs 可以忽略。count 是此样本数据的总数据大小。

关闭回调
---------

`close` 回调在应用程序关闭此设备时被调用。如果在打开回调中分配了任何私有数据，则必须在此关闭回调中释放这些数据。删除 ALSA 端口也应在此完成。此回调不得为 NULL。

重置回调
---------

`reset` 回调在序列器设备被应用程序重置或关闭时被调用。回调应立即关闭相关端口上的声音，并初始化端口状态。如果未定义此回调，OSS seq 将向端口发送一个 `HEARTBEAT` 事件。

事件
====

大多数事件由序列器处理并转换为适当的 ALSA 序列器事件，因此每个合成设备都可以通过 ALSA 序列器端口的 input_event 回调接收。驱动程序应实现以下 ALSA 事件：

=============	===================
ALSA 事件	原始 OSS 事件
=============	===================
NOTEON		SEQ_NOTEON, MIDI_NOTEON
NOTE		SEQ_NOTEOFF, MIDI_NOTEOFF
KEYPRESS	MIDI_KEY_PRESSURE
CHANPRESS	SEQ_AFTERTOUCH, MIDI_CHN_PRESSURE
PGMCHANGE	SEQ_PGMCHANGE, MIDI_PGM_CHANGE
PITCHBEND	SEQ_CONTROLLER(CTRL_PITCH_BENDER),
		MIDI_PITCH_BEND
CONTROLLER	MIDI_CTL_CHANGE,
		SEQ_BALANCE (with CTL_PAN)
CONTROL14	SEQ_CONTROLLER
REGPARAM	SEQ_CONTROLLER(CTRL_PITCH_BENDER_RANGE)
SYSEX		SEQ_SYSEX
=============	===================

这些行为的大部分可以通过 Emu8000 低级驱动程序中包含的 MIDI 模拟驱动程序实现。在未来的版本中，此模块将独立出来。
某些 OSS 事件（`SEQ_PRIVATE` 和 `SEQ_VOLUME` 事件）作为事件类型 SND_SEQ_OSS_PRIVATE 传递。OSS 序列器将这些事件的 8 字节数据包未经修改地传递。低级驱动程序应适当地处理这些事件。

MIDI 设备接口
========================

由于 OSS 模拟通过接收来自 ALSA 序列器的通知自动探测 ALSA MIDI 序列器端口的创建和删除，因此 MIDI 设备不需要像合成设备那样显式注册。

然而，注册到 ALSA 序列器的 MIDI `port_info` 必须包含组名 `SND_SEQ_GROUP_DEVICE` 和能力位 `CAP_READ` 或 `CAP_WRITE`。还必须定义订阅能力，例如 `CAP_SUBS_READ` 或 `CAP_SUBS_WRITE`。如果不满足这些条件，端口将不会注册为 OSS 序列器的 MIDI 设备。
通过MIDI设备的事件在OSS序列器中被解析，并转换为对应的ALSA序列器事件。来自MIDI序列器的输入也被OSS序列器转换为MIDI字节事件。这与seq_midi模块的工作方式正好相反。

已知问题 / 待办事项
==================

* 通过ALSA乐器层加载音色补丁尚未实现。
