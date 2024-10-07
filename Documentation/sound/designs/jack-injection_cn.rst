============================
ALSA Jack 软件注入
============================

关于 Jack 注入的简单介绍
=====================================

这里的 Jack 注入意味着用户可以通过 debugfs 接口向音频插孔注入插拔事件，这对于验证 ALSA 用户空间的变化非常有帮助。例如，我们在 PulseAudio 中更改了音频配置切换代码，并希望验证这些更改是否按预期工作以及是否引入了回归，在这种情况下，我们可以向一个或多个音频插孔注入插拔事件，而无需物理接触设备并插拔硬件。在此设计中，音频插孔并不等同于物理音频插孔。有时一个物理音频插孔具有多种功能，ALSA 驱动程序会为一个 `snd_jack` 创建多个 `jack_kctl`，这里 `snd_jack` 代表一个物理音频插孔，而 `jack_kctl` 则代表一个功能。例如，一个物理插孔具有两个功能：耳机和麦克风输入，ALSA ASoC 驱动程序将为此插孔构建两个 `jack_kctl`。Jack 注入是基于 `jack_kctl` 实现的，而不是基于 `snd_jack`。

为了向音频插孔注入事件，我们需要首先通过 `sw_inject_enable` 启用 Jack 注入。一旦启用，此插孔将不再受硬件事件的影响，我们可以通过 `jackin_inject` 注入插拔事件，并通过 `status` 检查插孔状态。在完成测试后，我们需要通过 `sw_inject_enable` 禁用 Jack 注入。一旦禁用，插孔状态将根据最后一次报告的硬件事件恢复，并且将根据未来的硬件事件变化。

Jack 注入接口布局
======================================

如果用户在内核中启用了 SND_JACK_INJECTION_DEBUG，音频插孔注入接口将如下创建：
::

   $debugfs_mount_dir/sound
   |-- card0
   |-- |-- HDMI_DP_pcm_10_Jack
   |-- |-- |-- jackin_inject
   |-- |-- |-- kctl_id
   |-- |-- |-- mask_bits
   |-- |-- |-- status
   |-- |-- |-- sw_inject_enable
   |-- |-- |-- type
   ..
|-- |-- HDMI_DP_pcm_9_Jack
   |--     |-- jackin_inject
   |--     |-- kctl_id
   |--     |-- mask_bits
   |--     |-- status
   |--     |-- sw_inject_enable
   |--     |-- type
   |-- card1
       |-- HDMI_DP_pcm_5_Jack
       |-- |-- jackin_inject
       |-- |-- kctl_id
       |-- |-- mask_bits
       |-- |-- status
       |-- |-- sw_inject_enable
       |-- |-- type
       ..
|-- Headphone_Jack
       |-- |-- jackin_inject
       |-- |-- kctl_id
       |-- |-- mask_bits
       |-- |-- status
       |-- |-- sw_inject_enable
       |-- |-- type
       |-- Headset_Mic_Jack
           |-- jackin_inject
           |-- kctl_id
           |-- mask_bits
           |-- status
           |-- sw_inject_enable
           |-- type

节点说明
======================================

kctl_id
  只读，获取 jack_kctl->kctl 的 ID
  ::

     sound/card1/Headphone_Jack# cat kctl_id
     Headphone Jack

mask_bits
  只读，获取 jack_kctl 支持的事件掩码位
  ::

     sound/card1/Headphone_Jack# cat mask_bits
     0x0001 HEADPHONE(0x0001)

status
  只读，获取 jack_kctl 的当前状态

- 耳机未插入：

  ::

     sound/card1/Headphone_Jack# cat status
     Unplugged

- 耳机已插入：

  ::

     sound/card1/Headphone_Jack# cat status
     Plugged

type
  只读，获取 snd_jack 支持的事件类型（物理音频插孔上支持的所有事件）
  ::

     sound/card1/Headphone_Jack# cat type
     0x7803 HEADPHONE(0x0001) MICROPHONE(0x0002) BTN_3(0x0800) BTN_2(0x1000) BTN_1(0x2000) BTN_0(0x4000)

sw_inject_enable
  读写，启用或禁用注入

- 注入禁用：

  ::

     sound/card1/Headphone_Jack# cat sw_inject_enable
     Jack: Headphone Jack		Inject Enabled: 0

- 注入启用：

  ::

     sound/card1/Headphone_Jack# cat sw_inject_enable
     Jack: Headphone Jack		Inject Enabled: 1

- 启用 Jack 注入：

  ::

     sound/card1/Headphone_Jack# echo 1 > sw_inject_enable

- 禁用 Jack 注入：

  ::

     sound/card1/Headphone_Jack# echo 0 > sw_inject_enable

jackin_inject
  写入专用，注入插拔事件

- 注入插拔事件：

  ::

     sound/card1/Headphone_Jack# echo 1 > jackin_inject

- 注入拔出事件：

  ::

     sound/card1/Headphone_Jack# echo 0 > jackin_inject
