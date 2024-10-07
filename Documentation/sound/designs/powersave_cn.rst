关于节能模式的说明
==========================

AC97 和 HD 音频驱动程序具有自动节能模式
此功能分别通过 Kconfig 选项 ``CONFIG_SND_AC97_POWER_SAVE`` 和 ``CONFIG_SND_HDA_POWER_SAVE`` 启用
当没有操作需求时，驱动程序会适当关闭编解码器电源。当没有任何应用程序使用设备和/或没有设置模拟回环时，电源将被完全或部分禁用。这可以节省一定的电力消耗，因此对笔记本电脑（甚至台式机）有益。
自动关机的超时时间可以通过 snd-ac97-codec 和 snd-hda-intel 模块的 ``power_save`` 模块选项指定。超时值以秒为单位。0 表示禁用自动节能。超时默认值通过 Kconfig 选项 ``CONFIG_SND_AC97_POWER_SAVE_DEFAULT`` 和 ``CONFIG_SND_HDA_POWER_SAVE_DEFAULT`` 给出。将此值设置为 1（最小值）不建议，因为许多应用程序尝试频繁重新打开设备。对于正常操作，10 秒是一个不错的选择。
``power_save`` 选项是可写的。这意味着您可以随时通过 sysfs 调整其值。例如，要启用 10 秒的自动节能模式，请写入 ``/sys/modules/snd_ac97_codec/parameters/power_save``（通常需要 root 权限）：
::

	# echo 10 > /sys/modules/snd_ac97_codec/parameters/power_save

请注意，在改变电源状态时您可能会听到咔哒声/爆音。此外，从关机状态唤醒到活动状态通常需要一定的时间。这些问题往往难以修复，除非您有修复补丁，否则不要额外报告这些问题。

对于 HD 音频接口，还有一个模块选项 `power_save_controller`。这可以启用或禁用控制器端的节能模式。启用此选项可能会进一步减少一些电力消耗，但也可能导致更长的唤醒时间和咔哒声。如果您经常遇到这种情况，尝试将其关闭。
