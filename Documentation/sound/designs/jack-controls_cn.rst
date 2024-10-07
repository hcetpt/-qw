ALSA Jack 控制
==================

为什么我们需要 Jack kcontrols
==========================

ALSA 使用 kcontrols 将音频控制（开关、音量、多路复用器等）导出到用户空间。这意味着用户空间应用程序（如 pulseaudio）可以在没有耳机插入时关闭耳机并打开扬声器。
旧的 ALSA jack 代码只为每个注册的 jack 创建输入设备。这些 jack 输入设备不能被以非 root 身份运行的用户空间设备读取。
新的 jack 代码为每个 jack 创建嵌入式的 jack kcontrols，任何进程都可以读取这些 kcontrols。
这可以与 UCM 结合使用，允许用户空间根据 jack 插入或移除事件更智能地路由音频。
Jack Kcontrol 内部结构
=======================

每个 jack 都将有一个 kcontrol 列表，因此我们可以在创建 jack 时创建一个 kcontrol 并将其附加到 jack 列表中。我们还可以在需要时随时向现有的 jack 添加一个 kcontrol。
当 jack 被释放时，这些 kcontrols 会自动被释放。
如何使用 jack kcontrols
=========================

为了保持兼容性，snd_jack_new() 已经修改，增加了两个参数：

initial_kctl
  如果为 true，则创建一个 kcontrol 并将其添加到 jack 列表中
phantom_jack
  不为幻影 jack 创建输入设备
HDA jacks 可以将 phantom_jack 设置为 true 以创建一个幻影 jack，并将 initial_kctl 设置为 true 以使用正确的 ID 创建初始 kcontrol。
ASoC jacks 应该将 initial_kctl 设置为 false。pin 名称将作为 jack kcontrol 的名称。
当然，请提供您需要翻译的文本。
