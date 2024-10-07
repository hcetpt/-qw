===============================
ALSA 上的 OSS 序列器仿真
===============================

版权所有 (c) 1998, 1999 由 Takashi Iwai

版本 0.1.8；1999 年 11 月 16 日

描述
===========

此目录包含在 ALSA 上的 OSS 序列器仿真驱动程序。请注意，该程序仍处于开发阶段。
其功能是——它提供了对通过 `/dev/sequencer` 和 `/dev/music` 设备访问的 OSS 序列器的仿真。
大多数使用 OSS 的应用程序可以在适当的 ALSA 序列器准备就绪的情况下运行。
此驱动程序仿真了以下特性：

* 正常的序列器和 MIDI 事件：

    这些事件会被转换为 ALSA 序列器事件，并发送到相应的端口。
* 定时器事件：

    定时器不能通过 ioctl 选择。控制速率固定为 100，与 HZ 无关。也就是说，即使在 Alpha 系统上，每秒也会有一个刻度。基础速率和节拍可以在 `/dev/music` 中更改。
* 音色加载：

    音色加载是否支持完全取决于合成器驱动程序，因为音色加载是通过回调到合成器驱动程序来实现的。
* 输入输出控制：

    大多数控制命令都被接受。一些控制命令依赖于合成器驱动程序，甚至也依赖于原始的 OSS。

此外，您还可以找到以下高级特性：

* 更好的队列机制：

    在处理事件之前，这些事件会被排队。
* 多个应用程序：

    您可以同时运行两个或更多应用程序（即使是 OSS 序列器）！
    然而，每个 MIDI 设备是独占使用的——也就是说，如果某个应用程序已经打开了一个 MIDI 设备，其他应用程序就不能使用它。合成器设备没有这样的限制。
* 实时事件处理：

    无需使用超出范围的 ioctl 即可实时处理事件。要切换到实时模式，请发送 ABSTIME 0 事件。随后的事件将在不排队的情况下实时处理。要关闭实时模式，请发送 RELTIME 0 事件。
* ``/proc`` 接口：

    应用程序和设备的状态可以通过 ``/proc/asound/seq/oss`` 在任何时候显示。在后续版本中，配置也将通过 ``/proc`` 接口进行更改。

安装
=====

运行配置脚本时需包含音序器支持（``--with-sequencer=yes``）和 OSS 模拟（``--with-oss=yes``）选项。将创建一个模块 ``snd-seq-oss.o``。如果声卡的合成器模块支持 OSS 模拟（目前只有 Emu8000 驱动），该模块将自动加载。
否则，需要手动加载此模块。
一开始，此模块会探测所有已连接到音序器的 MIDI 端口。之后，端口的创建和删除将由 ALSA 音序器的通知机制监控。
可用的合成器和 MIDI 设备可以在 ``/proc`` 接口中找到。
运行 ``cat /proc/asound/seq/oss`` 并检查设备。例如，如果你使用的是 AWE64 卡，你将会看到如下信息：
::

    OSS sequencer emulation version 0.1.8
    ALSA client number 63
    ALSA receiver port 0

    Number of applications: 0

    Number of synth devices: 1
    synth 0: [EMU8000]
      type 0x1 : subtype 0x20 : voices 32
      capabilities : ioctl enabled / load_patch enabled

    Number of MIDI devices: 3
    midi 0: [Emu8000 Port-0] ALSA port 65:0
      capability write / opened none

    midi 1: [Emu8000 Port-1] ALSA port 65:1
      capability write / opened none

    midi 2: [0: MPU-401 (UART)] ALSA port 64:0
      capability read/write / opened none

请注意，设备编号可能与 ``/proc/asound/oss-devices`` 中的信息或原始 OSS 驱动中的信息不同。
使用 ``/proc/asound/seq/oss`` 中列出的设备编号来通过 OSS 音序器模拟进行播放。

使用合成器设备
===============

运行你最喜欢的程序。我已经测试了 playmidi-2.4、awemidi-0.4.3、gmod-3.1 和 xmp-1.1.5。你可以像使用 sfxload 一样通过 ``/dev/sequencer`` 加载样本。
如果低级驱动支持对合成器设备的多重访问（如 Emu8000 驱动），允许两个或多个应用程序同时运行。

使用 MIDI 设备
===============

目前为止，仅测试了 MIDI 输出。尚未检查 MIDI 输入，但希望它能正常工作。使用 ``/proc/asound/seq/oss`` 中列出的设备编号。
请注意，这些数字大多与
``/proc/asound/oss-devices`` 中的列表不同。

模块选项
==============

以下模块选项是可用的：

maxqlen
  指定最大读/写队列长度。此队列是为 OSS 序列器专用的，因此它独立于 ALSA 序列器的队列长度。默认值为 1024。
  
seq_oss_debug
  指定调试级别，并接受零（= 不输出调试信息）或正整数。默认值为 0。

队列机制
==============

OSS 序列器仿真使用一个 ALSA 优先级队列。来自 ``/dev/sequencer`` 的事件被处理并放入由模块选项指定的队列中。
所有来自 ``/dev/sequencer`` 的事件在开始时都会被解析。
定时事件也在这一时刻被解析，以便事件可以在实时模式下处理。发送一个 ABSTIME 0 事件会切换到实时模式，而发送一个 RELTIME 0 事件则会关闭该模式。
在实时模式下，所有事件都会立即分发。
已排队的事件会在 ALSA 序列器调度器安排的时间后被分发到相应的 ALSA 序列器端口。
如果写入队列已满，则应用程序会在阻塞模式下等待直到有足够的空间（默认情况下为一半）变为空。也实现了写入同步。
来自 MIDI 设备的输入或回声事件会被存储在读 FIFO 队列中。如果应用程序以阻塞模式读取 ``/dev/sequencer``，则进程将被唤醒。
合成器设备接口
===============================

注册
------------

要注册一个OSS合成器设备，使用snd_seq_oss_synth_register()函数：
::

  int snd_seq_oss_synth_register(char *name, int type, int subtype, int nvoices,
          snd_seq_oss_callback_t *oper, void *private_data)

参数`name`、`type`、`subtype`和`nvoices`用于创建ioctl所需的synth_info结构。返回值是该设备的索引号。此索引号必须记住以便注销。如果注册失败，将返回-errno。要释放此设备，请调用snd_seq_oss_synth_unregister()函数：
::

  int snd_seq_oss_synth_unregister(int index)

其中`index`是注册函数返回的索引号。

回调
---------

OSS合成器设备具有样本下载和ioctl（如重置样本）的能力。在OSS仿真中，这些特殊功能通过使用回调来实现。注册参数oper用于指定这些回调。以下回调函数必须定义：
::

  snd_seq_oss_callback_t:
   int (*open)(snd_seq_oss_arg_t *p, void *closure);
   int (*close)(snd_seq_oss_arg_t *p);
   int (*ioctl)(snd_seq_oss_arg_t *p, unsigned int cmd, unsigned long arg);
   int (*load_patch)(snd_seq_oss_arg_t *p, int format, const char *buf, int offs, int count);
   int (*reset)(snd_seq_oss_arg_t *p);

除了`open`和`close`回调外，其他允许为NULL。每个回调函数的第一个参数类型为`snd_seq_oss_arg_t`：
::

  struct snd_seq_oss_arg_t {
      int app_index;
      int file_mode;
      int seq_mode;
      snd_seq_addr_t addr;
      void *private_data;
      int event_passing;
  };

前三个字段`app_index`、`file_mode`和`seq_mode`由OSS音序器初始化。`app_index`是应用程序索引，每个打开OSS音序器的应用程序都是唯一的。`file_mode`是表示文件操作模式的位标志。其含义请参见`seq_oss.h`。`seq_mode`是音序器的操作模式。当前版本中仅使用`SND_OSSSEQ_MODE_SYNTH`
接下来的两个字段`addr`和`private_data`必须在打开回调时由合成器驱动程序填充。`addr`包含分配给此设备的ALSA音序器端口地址。如果驱动程序为`private_data`分配了内存，则必须在关闭回调中自行释放。
最后一个字段`event_passing`指示如何转换note-on/off事件。在`PROCESS_EVENTS`模式下，将note 255视为速度变化，并将按键压力事件传递给端口。在`PASS_EVENTS`模式下，所有note on/off事件都原样传递给端口。`PROCESS_KEYPRESS`模式检查高于128的音符，并将其视为按键压力事件（主要用于Emu8000驱动程序）。

打开回调
------------

每次应用程序使用OSS音序器打开此设备时都会调用`open`。这不能为NULL。通常，打开回调执行以下步骤：

1. 分配私有数据记录
2. 创建一个ALSA音序器端口
3. 设置新的端口地址到`arg->addr`
#. 设置 `arg->private_data` 上的私有数据记录指针
请注意，此合成器端口的 `port_info` 中的类型位标志不应包含 `TYPE_MIDI_GENERIC` 位。相反，应使用 `TYPE_SPECIFIC`。同时，也不应包含 `CAP_SUBSCRIPTION` 位。这是为了将其与其他普通 MIDI 设备区分开来。如果打开过程成功，返回零；否则，返回 `-errno`。

Ioctl 回调
----------

`ioctl` 回调在序列器接收到特定设备的 ioctl 时被调用。以下两个 ioctl 应由该回调处理：

`IOCTL_SEQ_RESET_SAMPLES`
重置所有内存中的样本——返回 0

`IOCTL_SYNTH_MEMAVL`
返回可用内存大小

`FM_4OP_ENABLE`
通常可以忽略

其他 ioctl 由序列器内部处理，不会传递到低级驱动程序。

加载补丁回调
-------------

`load_patch` 回调用于样本下载。此回调必须从用户空间读取数据并传输到每个设备。如果成功，返回 0；如果失败，返回 `-errno`。格式参数是补丁信息记录中的补丁键。buf 是存储补丁信息记录的用户空间指针。offs 可以忽略。count 是此样本数据的总数据大小。

关闭回调
---------

`close` 回调在应用程序关闭此设备时被调用。如果在打开回调中分配了任何私有数据，则必须在关闭回调中释放这些数据。删除 ALSA 端口也应在此处完成。此回调不得为 NULL。

重置回调
---------

`reset` 回调在序列器设备被应用程序重置或关闭时被调用。回调应立即关闭相关端口上的声音，并初始化端口的状态。如果未定义此回调，OSS 序列器会向端口发送一个 `HEARTBEAT` 事件。

事件
======

大多数事件由序列器处理并转换为适当的 ALSA 序列器事件，因此每个合成器设备都可以通过 ALSA 序列器端口的输入事件回调接收。以下 ALSA 事件应由驱动程序实现：

=============	===================
ALSA 事件	原始 OSS 事件
=============	===================
NOTEON		SEQ_NOTEON, MIDI_NOTEON
NOTE		SEQ_NOTEOFF, MIDI_NOTEOFF
KEYPRESS	MIDI_KEY_PRESSURE
CHANPRESS	SEQ_AFTERTOUCH, MIDI_CHN_PRESSURE
PGMCHANGE	SEQ_PGMCHANGE, MIDI_PGM_CHANGE
PITCHBEND	SEQ_CONTROLLER(CTRL_PITCH_BENDER), MIDI_PITCH_BEND
CONTROLLER	MIDI_CTL_CHANGE, SEQ_BALANCE (with CTL_PAN)
CONTROL14	SEQ_CONTROLLER
REGPARAM	SEQ_CONTROLLER(CTRL_PITCH_BENDER_RANGE)
SYSEX		SEQ_SYSEX
=============	===================

这些行为大部分可以通过 Emu8000 低级驱动程序中包含的 MIDI 模拟驱动程序实现。在未来的版本中，这个模块将独立出来。

一些 OSS 事件（如 `SEQ_PRIVATE` 和 `SEQ_VOLUME` 事件）作为事件类型 `SND_SEQ_OSS_PRIVATE` 传递。OSS 序列器在不作任何修改的情况下传递这些事件的 8 字节数据包。低级驱动程序应适当处理这些事件。

与 MIDI 设备的接口
==================

由于 OSS 模拟通过接收来自 ALSA 序列器的公告自动探测 ALSA MIDI 序列器端口的创建和删除，因此 MIDI 设备不需要像合成器设备那样显式注册。

然而，注册到 ALSA 序列器的 MIDI `port_info` 必须包含组名 `SND_SEQ_GROUP_DEVICE` 和能力位 `CAP_READ` 或 `CAP_WRITE`。此外，还必须定义订阅能力 `CAP_SUBS_READ` 或 `CAP_SUBS_WRITE`。如果不满足这些条件，则端口不会作为 OSS 序列器 MIDI 设备注册。
通过MIDI设备的事件在OSS序列器中被解析并转换为相应的ALSA序列器事件。来自MIDI序列器的输入同样也被OSS序列器转换为MIDI字节事件。这与seq_midi模块的工作方式正好相反。

已知问题 / 待办事项
=======================

* 通过ALSA乐器层加载补丁尚未实现
