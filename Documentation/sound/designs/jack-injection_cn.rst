============================
ALSA Jack 软件注入
============================

简要介绍 Jack 注入
=====================================

此处的 Jack 注入是指用户可以通过 debugfs 接口向音频接口注入插拔事件，这对于验证 ALSA 用户空间更改非常有帮助。例如，我们在 PulseAudio 中更改了音频配置切换代码，并希望验证这些更改是否按预期工作以及是否引入了回归，在这种情况下，我们可以在一个或多个音频接口上注入插拔事件，而无需物理访问设备并实际插入或拔出物理设备到音频接口。

在这个设计中，音频接口并不等同于物理音频接口。有时一个物理音频接口具有多种功能，并且 ALSA 驱动程序为每个 `snd_jack` 创建了多个 `jack_kctl`。这里的 `snd_jack` 表示一个物理音频接口，而 `jack_kctl` 表示一种功能。例如，一个物理接口具有两种功能：耳机和麦克风输入，ASoC ALSA 驱动程序将为此接口构建两个 `jack_kctl`。Jack 注入是基于 `jack_kctl` 实现的，而不是基于 `snd_jack`。

为了向音频接口注入事件，我们需要首先通过 `sw_inject_enable` 启用 Jack 注入，一旦启用，此接口将不再根据硬件事件改变状态，我们可以通过 `jackin_inject` 注入插拔事件，并通过 `status` 检查接口状态。在完成测试后，我们需要通过 `sw_inject_enable` 禁用 Jack 注入；一旦禁用，接口状态将根据最后报告的硬件事件恢复，并由未来的硬件事件改变。

Jack 注入接口布局
======================================

如果用户在内核中启用了 SND_JACK_INJECTION_DEBUG，音频 Jack 注入接口将如下创建：
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
  只读，获取 `jack_kctl->kctl` 的 ID
  ::

     sound/card1/Headphone_Jack# cat kctl_id
     Headphone Jack

mask_bits
  只读，获取 `jack_kctl` 支持的事件掩码位
  ::

     sound/card1/Headphone_Jack# cat mask_bits
     0x0001 HEADPHONE(0x0001)

status
  只读，获取 `jack_kctl` 的当前状态

- 耳机未插入：

  ::

     sound/card1/Headphone_Jack# cat status
     Unplugged

- 耳机已插入：

  ::

     sound/card1/Headphone_Jack# cat status
     Plugged

type
  只读，从类型获取 `snd_jack` 支持的事件（物理音频接口上的所有支持事件）
  ::

     sound/card1/Headphone_Jack# cat type
     0x7803 HEADPHONE(0x0001) MICROPHONE(0x0002) BTN_3(0x0800) BTN_2(0x1000) BTN_1(0x2000) BTN_0(0x4000)

sw_inject_enable
  读写，启用或禁用注入

- 注入已禁用：

  ::

     sound/card1/Headphone_Jack# cat sw_inject_enable
     Jack: Headphone Jack		Inject Enabled: 0

- 注入已启用：

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

- 注入插入事件：

  ::

     sound/card1/Headphone_Jack# echo 1 > jackin_inject

- 注入拔出事件：

  ::

     sound/card1/Headphone_Jack# echo 0 > jackin_inject
