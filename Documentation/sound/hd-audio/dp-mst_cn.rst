=======================
HD-Audio DP-MST 支持
=======================

为了支持 DP MST 音频，HD Audio HDMI 编码器驱动引入了虚拟引脚和动态 PCM 分配。
虚拟引脚是 per_pin 的扩展。DP MST 与传统模式的最大区别在于 DP MST 引入了设备条目。每个引脚可以包含多个设备条目。每个设备条目表现得像一个引脚。
由于每个引脚可能包含多个设备条目，且每个编码器可能包含多个引脚，如果我们为每个 per_pin 使用一个 PCM，那么将会有许多 PCM。
新的解决方案是创建少量的 PCM，并动态地将 PCM 绑定到 per_pin。驱动使用 spec->dyn_pcm_assign 标志来指示是否使用新方案。

PCM
===
待添加

引脚初始化
==================
每个引脚可能有多个设备条目（虚拟引脚）。在英特尔平台上，设备条目的数量是动态变化的。如果连接了 DP MST 枢纽，则处于 DP MST 模式，设备条目的数量为 3；否则，设备条目的数量为 1。
为了简化实现，无论是否处于 DP MST 模式，所有设备条目都会在启动时进行初始化。

连接列表
===============
DP MST 重用了连接列表代码。代码可以重用是因为同一引脚上的设备条目具有相同的连接列表。
这意味着 DP MST 可以在不设置设备条目的情况下获取设备条目的连接列表。

接口
====
假设：
- MST 必须使用 dyn_pcm_assign，并且是 acomp（对于英特尔场景）；
- NON-MST 可能使用或不使用 dyn_pcm_assign，它可以是 acomp 或 !acomp；

因此存在以下几种情况：
a. MST (&& dyn_pcm_assign && acomp)
b. NON-MST && dyn_pcm_assign && acomp
c. NON-MST && !dyn_pcm_assign && !acomp

下面的讨论将忽略 MST 和 NON-MST 的差异，因为这对接口处理影响不大。
驱动在 hdmi_spec 中使用了 struct hdmi_pcm pcm[] 数组，snd_jack 是 hdmi_pcm 的成员。每个引脚有一个 struct hdmi_pcm * pcm 指针。
对于 !dyn_pcm_assign，per_pin->pcm 将静态地分配给 spec->pcm[n]
对于 dyn_pcm_assign，当监视器热插拔时，per_pin->pcm 将分配给 spec->pcm[n]

构建 Jack
---------

- dyn_pcm_assign

  不使用 hda_jack 而是直接在 spec->pcm_rec[pcm_idx].jack 中使用 snd_jack
- !dyn_pcm_assign

  使用 hda_jack 并静态地将 spec->pcm_rec[pcm_idx].jack = jack->jack

未请求事件启用
---------------
如果 !acomp，则启用未请求事件

监视器热插拔事件处理
---------------------
- acomp

  pin_eld_notify() -> check_presence_and_report() -> hdmi_present_sense() -> sync_eld_via_acomp()
  
  对于 dyn_pcm_assign 和 !dyn_pcm_assign，直接在 spec->pcm_rec[pcm_idx].jack 上使用 snd_jack_report()

- !acomp

  hdmi_unsol_event() -> hdmi_intrinsic_event() -> check_presence_and_report() -> hdmi_present_sense() -> hdmi_prepsent_sense_via_verbs()

  对于 dyn_pcm_assign，直接在 spec->pcm_rec[pcm_idx].jack 上使用 snd_jack_report()
  
  使用 hda_jack 机制来处理 Jack 事件

其他内容稍后添加
==================
