SPDX 许可证标识符: GPL-2.0

虚拟 PCM 测试驱动
=================

虚拟 PCM 测试驱动模拟了一个通用的 PCM 设备，可以用于测试用户空间 ALSA 应用程序以及 PCM 中间层的模糊测试。此外，它还可以用来模拟难以复现的 PCM 设备问题。

这个驱动能做什么？
~~~~~~~~~~~~~~~~~~~~~

目前，该驱动能够完成以下功能：
- 模拟捕获和播放过程
- 生成随机或基于模式的捕获数据
- 在播放和捕获过程中注入延迟
- 在 PCM 回调函数中注入错误

它支持最多 8 个子流和 4 个通道，并且支持交错和非交错访问模式。

此外，该驱动还可以检查播放流是否包含预定义的模式，这在相应的自测脚本（alsa/pcmtest-test.sh）中用于检查 PCM 中间层的数据传输功能。另外，该驱动重新定义了默认的 RESET ioctl，自测也覆盖了这一 PCM API 功能。

配置
-----

除了常见的 ALSA 模块参数外，该驱动还有几个额外的参数：

- `fill_mode`（布尔型）- 缓冲区填充模式（见下文）
- `inject_delay`（整型）
- `inject_hwpars_err`（布尔型）
- `inject_prepare_err`（布尔型）
- `inject_trigger_err`（布尔型）

捕获数据生成
-------------

该驱动有两种数据生成模式：第一种（`fill_mode` 参数为 0）表示随机数据生成，第二种（`fill_mode` 参数为 1）表示基于模式的数据生成。我们来看第二种模式。
首先，您可能希望指定一个用于数据生成的模式。您可以通过将模式写入 debugfs 文件来实现这一点。每个通道都有对应的模式缓冲区 debugfs 条目，同时还有包含模式缓冲区长度的条目：
- `/sys/kernel/debug/pcmtest/fill_pattern[0-3]`
- `/sys/kernel/debug/pcmtest/fill_pattern[0-3]_len`

要为通道 0 设置模式，您可以执行以下命令：

```bash
echo -n mycoolpattern > /sys/kernel/debug/pcmtest/fill_pattern0
```

然后，在每次对 `pcmtest` 设备执行捕获操作后，通道 0 的缓冲区将包含 `'mycoolpatternmycoolpatternmycoolpatternmy...'`。
模式本身最长可达 4096 字节。

延迟注入
---------

该驱动有一个名为 `inject_delay` 的参数，其名称非常直观，可用于时间延迟/加速模拟。该参数为整型，表示在模块内部计时器的刻度之间添加的延迟。
如果 `inject_delay` 值为正数，则缓冲区填充速度会变慢；如果为负数，则填充速度会加快。您可以通过在任何音频录制应用程序（如 Audacity）中选择 `pcmtest` 设备作为源来进行录音尝试。
此参数还可以用于在极短的时间内生成大量音频数据（通过设置负值的 `inject_delay`）。
错误注入
---------

此模块可用于在PCM通信过程中注入错误。这一操作可以帮助您了解用户空间ALSA程序在异常情况下的表现。
例如，您可以通过向`inject_hwpars_err`模块参数写入`1`，使所有`hw_params` PCM回调返回`EBUSY`错误：

```bash
echo 1 > /sys/module/snd_pcmtest/parameters/inject_hwpars_err
```

可以向以下PCM回调注入错误：

- `hw_params`（`EBUSY`）
- `prepare`（`EINVAL`）
- `trigger`（`EINVAL`）

播放测试
--------

此驱动程序还可以用于测试播放功能——每当您将播放数据写入`pcmtest` PCM设备并关闭它时，驱动程序会检查缓冲区是否包含循环模式（该模式通过每个通道的`fill_pattern` debugfs文件指定）。如果播放缓冲区的内容代表了循环模式，则将`pc_test` debugfs条目设置为`1`；否则，驱动程序将其设置为`0`。

ioctl重新定义测试
-------------------

驱动程序重新定义了默认适用于所有PCM设备的`reset` ioctl。为了测试此功能，我们可以触发`reset` ioctl并检查`ioctl_test` debugfs条目：

```bash
cat /sys/kernel/debug/pcmtest/ioctl_test
```

如果ioctl成功触发，此文件将包含`1`；否则，包含`0`。
