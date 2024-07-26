============= 
ALSA Jack 控制器
=============

为什么我们需要 Jack kcontrols
=================================

ALSA 使用 kcontrols 来将音频控制（开关、音量、多路复用器等）导出到用户空间。这意味着像 pulseaudio 这样的用户空间应用程序可以在没有耳机插入时关闭耳机并打开扬声器。
旧的 ALSA Jack 代码只为每个注册的 Jack 创建输入设备。这些 Jack 输入设备无法被以非 root 身份运行的用户空间设备读取。
新的 Jack 代码为每个 Jack 创建嵌入式 Jack kcontrols，任何进程都可以读取。
这可以与 UCM 结合使用，使用户空间能够根据 Jack 插入或移除事件更智能地路由音频。
Jack Kcontrol 内部结构
=======================

每个 Jack 都会有一个 kcontrol 列表，因此我们可以在创建 Jack 时创建一个 kcontrol 并将其附加到 Jack 上。我们也可以在需要时向已存在的 Jack 添加一个 kcontrol。
当 Jack 被释放时，这些 kcontrols 将自动被释放。
如何使用 Jack kcontrols
========================

为了保持兼容性，`snd_jack_new()` 已经通过添加两个参数进行了修改：

initial_kctl
  如果为真，则创建一个 kcontrol 并将其添加到 Jack 列表中
phantom_jack
  对于幻影 Jack 不要创建输入设备
HDA Jacks 可以将 `phantom_jack` 设置为真来创建一个幻影 Jack，并将 `initial_kctl` 设置为真来使用正确的 ID 创建初始 kcontrol。
ASoC Jacks 应该将 `initial_kctl` 设置为假。Pin 名称将被分配为 Jack kcontrol 的名称。
您没有提供需要翻译的文本。请提供需要翻译成中文的英文或其他语言的文本。
