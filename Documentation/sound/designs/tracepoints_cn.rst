ALSA 中的追踪点
===================

2017/07/02
高桥 坂本

ALSA PCM 核心中的追踪点
============================

ALSA PCM 核心将 `snd_pcm` 子系统注册到内核追踪点系统。这个子系统包含两类追踪点：一类用于 PCM 缓冲区的状态，另一类用于处理 PCM 硬件参数。这些追踪点在相应的内核配置被启用时可用。当 `CONFIG_SND_DEBUG` 被启用时，后一类追踪点可用。如果同时启用了额外的 `SND_PCM_XRUN_DEBUG`，前一类追踪点也将被启用。

PCM 缓冲区状态的追踪点
------------------------------------

这一类别包括四个追踪点：`hwptr`、`applptr`、`xrun` 和 `hw_ptr_error`。

处理 PCM 硬件参数的追踪点
-----------------------------------------------------

这一类别包括两个追踪点：`hw_mask_param` 和 `hw_interval_param`。

在 ALSA PCM 核心的设计中，数据传输被抽象为 PCM 子流。应用程序管理 PCM 子流以维持 PCM 帧的数据传输。在开始数据传输之前，应用程序需要配置 PCM 子流。在此过程中，通过应用程序和 ALSA PCM 核心之间的交互来确定 PCM 硬件参数。一旦确定，PCM 子流的运行时就会保持这些参数。

这些参数在结构 `snd_pcm_hw_params` 中描述。该结构包含多种类型的参数。应用程序为这些参数设置首选值，然后执行带有 `SNDRV_PCM_IOCTL_HW_REFINE` 或 `SNDRV_PCM_IOCTL_HW_PARAMS` 的 ioctl(2)。前者仅用于细化可用的参数集，后者则用于实际确定参数。

结构 `snd_pcm_hw_params` 包含以下成员：

``flags``
        可配置。ALSA PCM 核心和某些驱动程序会处理此标志以选择合适的参数或改变其行为。
``masks``
        可配置。这种类型的参数在 `struct snd_mask` 中描述，并表示掩码值。截至 PCM 协议 v2.0.13，定义了三种类型。
- SNDRV_PCM_HW_PARAM_ACCESS
- SNDRV_PCM_HW_PARAM_FORMAT
- SNDRV_PCM_HW_PARAM_SUBFORMAT
`intervals`
    可配置。这种类型的参数在 `struct snd_interval` 中描述，并表示具有范围的值。截至 PCM 协议版本 2.0.13，定义了十二种类型。
- SNDRV_PCM_HW_PARAM_SAMPLE_BITS
- SNDRV_PCM_HW_PARAM_FRAME_BITS
- SNDRV_PCM_HW_PARAM_CHANNELS
- SNDRV_PCM_HW_PARAM_RATE
- SNDRV_PCM_HW_PARAM_PERIOD_TIME
- SNDRV_PCM_HW_PARAM_PERIOD_SIZE
- SNDRV_PCM_HW_PARAM_PERIOD_BYTES
- SNDRV_PCM_HW_PARAM_PERIODS
- SNDRV_PCM_HW_PARAM_BUFFER_TIME
- SNDRV_PCM_HW_PARAM_BUFFER_SIZE
- SNDRV_PCM_HW_PARAM_BUFFER_BYTES
- SNDRV_PCM_HW_PARAM_TICK_TIME

`rmask`
    可配置。此值仅在使用 SNDRV_PCM_IOCTL_HW_REFINE 执行 ioctl(2) 时进行评估。应用程序可以选择哪些 mask/interval 参数可以由 ALSA PCM 核心更改。对于 SNDRV_PCM_IOCTL_HW_PARAMS，此掩码将被忽略，并且所有参数都将被更改。

`cmask`
    只读。ioctl(2) 返回后，用户空间中的 `struct snd_pcm_hw_params` 缓存包含每个操作的结果。此掩码表示实际更改了哪些 mask/interval 参数。

`info`
    只读。这表示硬件/驱动程序的能力，用 SNDRV_PCM_INFO_XXX 位标志表示。通常，应用程序执行 ioctl(2) 使用 SNDRV_PCM_IOCTL_HW_REFINE 获取此标志，然后决定参数候选值，并使用 SNDRV_PCM_IOCTL_HW_PARAMS 执行 ioctl(2) 来配置 PCM 子流。

`msbits`
    只读。此值表示 PCM 样本的 MSB（最高有效位）侧的有效位宽。当 SNDRV_PCM_HW_PARAM_SAMPLE_BITS 参数被确定为一个固定值时，此值也会根据它进行计算。否则为零。但这种行为取决于驱动程序的实现。

`rate_num`
    只读。此值表示采样率分数表示法中的分子。基本上，当 SNDRV_PCM_HW_PARAM_RATE 参数被确定为单个值时，此值也会根据它进行计算。否则为零。但这种行为取决于驱动程序的实现。

`rate_den`
    只读。此值表示采样率分数表示法中的分母。基本上，当 SNDRV_PCM_HW_PARAM_RATE 参数被确定为单个值时，此值也会根据它进行计算。否则为零。但这种行为取决于驱动程序的实现。

`fifo_size`
    只读。此值表示硬件串行声音接口中 FIFO 的大小。基本上，每个驱动程序可以为此参数分配适当的值，但某些驱动程序会根据硬件设计或数据传输协议有意地设置为零。

当应用程序使用 SNDRV_PCM_HW_REFINE 或 SNDRV_PCM_HW_PARAMS 执行 ioctl(2) 时，ALSA PCM 核心会处理 `struct snd_pcm_hw_params` 缓冲区。
缓冲区中的参数根据 `struct snd_pcm_hardware` 和运行时的约束规则进行更改。该结构描述了所处理硬件的能力。这些规则描述了多个参数之间的依赖关系，从而决定了某个参数的值。每条规则都有一个回调函数，驱动程序可以注册任意函数来计算目标参数。ALSA PCM 核心会在默认情况下向运行时注册一些规则。

每个驱动程序只要在 `struct snd_pcm_ops.open` 的回调中准备两件事，就可以参与这种交互：

1. 在回调中，驱动程序需要根据相应硬件的能力更改运行时中的 `struct snd_pcm_hardware` 类型的一个成员。
2. 同样在这个回调中，如果由于硬件设计导致多个参数之间存在依赖关系，驱动程序还需要向运行时注册额外的约束规则。

驱动程序可以在 `struct snd_pcm_ops.hw_params` 的回调中引用交互的结果，但不应更改内容。

此类别中的跟踪点用于跟踪掩码/间隔参数的变化。当 ALSA PCM 核心更改这些参数时，会根据更改参数的类型探测 `hw_mask_param` 或 `hw_interval_param` 事件。ALSA PCM 核心还为每个跟踪点提供了一个易于阅读的格式。以下是一个 `hw_mask_param` 的示例：

```
hw_mask_param: pcmC0D0p 001/023 FORMAT 00000000000000000000001000000044 00000000000000000000001000000044
```

以下是一个 `hw_interval_param` 的示例：

```
hw_interval_param: pcmC0D0p 000/023 BUFFER_SIZE 0 0 [0 4294967295] 0 1 [0 4294967295]
```

前三个字段是通用的。它们依次表示 ALSA PCM 字符设备的名称、约束规则和更改的参数名称。约束规则字段包含两个子字段：应用的规则索引和添加到运行时的总规则数。例外情况是索引 000，这意味着参数是由 ALSA PCM 核心更改的，与规则无关。
其余的字段表示参数在更改前后的状态。这些字段根据参数的类型而不同。对于掩码类型的参数，这些字段表示参数内容的十六进制转储。对于区间类型的参数，这些字段按顺序表示结构体 `snd_interval` 中 `empty`、`integer`、`openmin`、`min`、`max` 和 `openmax` 各个成员的值。

驱动程序中的追踪点
=================

一些驱动程序为开发人员的便利提供了追踪点。关于这些追踪点，请参考各自的文档或实现。
