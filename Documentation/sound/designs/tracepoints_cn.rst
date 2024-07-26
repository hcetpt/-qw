ALSA 中的追踪点
===================

2017/07/02
高橋 壯

ALSA PCM 核心中的追踪点
============================

ALSA PCM 核心向内核追踪点系统注册 `snd_pcm` 子系统。
此子系统包括两类追踪点：一类用于 PCM 缓冲区的状态，另一类用于处理 PCM 硬件参数。这些追踪点在相应的内核配置被启用时可用。
当 `CONFIG_SND_DEBUG` 被启用时，后一类追踪点可用。如果同时启用了额外的 `SND_PCM_XRUN_DEBUG`，那么前一类追踪点也被启用。

PCM 缓冲区状态的追踪点
------------------------------------

这一类别包括四个追踪点：`hwptr`、`applptr`、`xrun` 和 `hw_ptr_error`。

处理 PCM 硬件参数的追踪点
-----------------------------------------------------

这一类别包括两个追踪点：`hw_mask_param` 和 `hw_interval_param`。

在 ALSA PCM 核心的设计中，数据传输被抽象为 PCM 子流。
应用程序管理 PCM 子流以维持 PCM 帧的数据传输。在开始数据传输之前，应用程序需要配置 PCM 子流。在此过程中，通过应用程序与 ALSA PCM 核心之间的交互决定 PCM 硬件参数。一旦确定，PCM 子流的运行时将保持这些参数不变。

这些参数描述在结构 `snd_pcm_hw_params` 中。该结构包含几种类型的参数。应用程序为这些参数设置首选值，然后执行带有 `SNDRV_PCM_IOCTL_HW_REFINE` 或 `SNDRV_PCM_IOCTL_HW_PARAMS` 的 ioctl(2)。前者仅用于细化可用的参数集，而后者则用于实际决定参数。

结构 `snd_pcm_hw_params` 包含以下成员：

`flags`
        可配置。ALSA PCM 核心和一些驱动程序会处理这个标志来选择合适的参数或改变其行为。
`masks`
        可配置。这种类型的参数在结构 `snd_mask` 中描述，并表示掩码值。截至 PCM 协议 v2.0.13，定义了三种类型。
- SNDRV_PCM_HW_PARAM_ACCESS
  - SNDRV_PCM_HW_PARAM_FORMAT
  - SNDRV_PCM_HW_PARAM_SUBFORMAT
``intervals``
  可配置。这种类型的参数在 `struct snd_interval` 中描述，代表具有范围的值。截至 PCM 协议版本 2.0.13，定义了十二种类型：
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
``rmask``
  可配置。仅在使用 `SNDRV_PCM_IOCTL_HW_REFINE` 调用 ioctl(2) 时进行评估。应用程序可以选择由 ALSA PCM 核心更改的哪些掩码/区间参数。对于 `SNDRV_PCM_IOCTL_HW_PARAMS`，此掩码被忽略，并且所有参数都将被更改。
``cmask``
  只读。从 ioctl(2) 返回后，用户空间中 `struct snd_pcm_hw_params` 的缓冲区包含每个操作的结果。此掩码表示实际更改了哪些掩码/区间参数。
``info``
  只读。这通过位标志表示硬件/驱动程序的能力，使用 `SNDRV_PCM_INFO_XXX`。通常，应用程序会使用 `SNDRV_PCM_IOCTL_HW_REFINE` 执行 ioctl(2) 来检索此标志，然后决定参数候选值，并使用 `SNDRV_PCM_IOCTL_HW_PARAMS` 执行 ioctl(2) 来配置 PCM 子流。
``msbits``
  只读。此值表示 PCM 样本 MSB 一侧可用的位宽度。如果 `SNDRV_PCM_HW_PARAM_SAMPLE_BITS` 参数被确定为一个固定数值，则此值也会根据该数值计算得出。否则，为零。但是，这种行为取决于驱动程序实现。
``rate_num``
  只读。此值表示以分数表示的采样率的分子。基本上，如果 `SNDRV_PCM_HW_PARAM_RATE` 参数被确定为单个值，则此值也会根据该值计算得出。否则，为零。但是，这种行为取决于驱动程序实现。
``rate_den``
  只读。此值表示以分数表示的采样率的分母。基本上，如果 `SNDRV_PCM_HW_PARAM_RATE` 参数被确定为单个值，则此值也会根据该值计算得出。否则，为零。但是，这种行为取决于驱动程序实现。
``fifo_size``
  只读。此值表示硬件串行声音接口的 FIFO 大小。基本上，每个驱动程序可以为此参数分配适当的值，但有些驱动程序出于硬件设计或数据传输协议方面的考虑有意设置为零。

ALSA PCM 核心在应用程序使用 `SNDRV_PCM_HW_REFINE` 或 `SNDRV_PCM_HW_PARAMS` 调用 ioctl(2) 时处理 `struct snd_pcm_hw_params` 缓冲区。
缓冲区中的参数根据 `struct snd_pcm_hardware` 结构体及运行时的约束规则进行更改。该结构体描述了所处理硬件的能力。这些规则描述了根据硬件设计中多个参数之间的依赖关系来决定某个参数的方式。
每条规则都有一个回调函数，驱动程序可以注册任意函数来计算目标参数。ALSA PCM 核心向运行时环境注册了一些默认规则。
每个驱动程序只要在 `struct snd_pcm_ops.open` 的回调中准备好了两件事就可以参与到交互过程中：
1. 在回调中，驱动程序应根据相应硬件的能力更改运行时环境中的 `struct snd_pcm_hardware` 类型成员。
2. 同样在这个回调中，当几个参数由于硬件设计而存在依赖关系时，驱动程序还应向运行时环境注册额外的约束规则。
驱动程序可以在 `struct snd_pcm_ops.hw_params` 的回调中引用交互结果，但不应改变其内容。
本类别的追踪点旨在追踪掩码/区间参数的变化。当 ALSA PCM 核心更改这些参数时，会根据被更改参数的类型探测到 `hw_mask_param` 或 `hw_interval_param` 事件。
ALSA PCM 核心还为每个追踪点提供了一个易于阅读的打印格式。下面是一个 `hw_mask_param` 追踪点的例子：
::

    hw_mask_param: pcmC0D0p 001/023 FORMAT 00000000000000000000001000000044 00000000000000000000001000000044

下面是一个 `hw_interval_param` 追踪点的例子：
::

    hw_interval_param: pcmC0D0p 001/023 BUFFER_SIZE 0 0 [0 4294967295] 0 1 [0 4294967295]

前三个字段是共通的。它们分别代表 ALSA PCM 字符设备的名称、约束规则和被更改参数的名称。约束规则字段由两个子字段组成：应用的规则索引和添加到运行时环境中的规则总数。例外情况是索引 000，这意味着参数是由 ALSA PCM 核心更改的，而不考虑规则的影响。
其余的字段表示参数在更改前/后的状态。这些字段根据参数类型的不同而不同。对于掩码（mask）类型的参数，这些字段表示参数内容的十六进制形式。对于区间（interval）类型的参数，这些字段按顺序表示`empty`、`integer`、`openmin`、`min`、`max`、`openmax`在`snd_interval`结构中的值。

驱动程序中的追踪点
==================

一些驱动程序为了开发者的方便设置了追踪点。关于这些追踪点，请参考各驱动的具体文档或实现代码。
