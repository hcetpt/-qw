==============================================
Digigram miXart8 和 miXart8AES/EBU 声卡的 Alsa 驱动
==============================================

Digigram <alsa@digigram.com>

概述
=====

miXart8 是一款多通道音频处理和混音声卡，具有 4 路立体声音频输入和 4 路立体声音频输出。miXart8AES/EBU 在此基础上增加了一块扩展卡，提供了额外的 4 路数字立体声音频输入和输出。此外，这块扩展卡还支持外部时钟同步（AES/EBU、字时钟、时间码和视频同步）。

主板上有一个 PowerPC 处理器，提供板载的 MPEG 编码和解码、采样率转换以及各种效果。在加载特定固件之前，驱动程序无法正常工作，即不会出现 PCM 或混音设备。请使用 alsa-tools 包中的 mixartloader。

版本 0.1.0
==========

一块 miXart8 声卡将表现为 4 张 Alsa 卡，每张卡有 1 个立体声模拟捕获设备 'pcm0c' 和 1 个立体声模拟播放设备 'pcm0p'。如果使用的是 miXart8AES/EBU，则每张卡还会有 1 个立体声数字输入设备 'pcm1c' 和 1 个立体声数字输出设备 'pcm1p'。

格式
-----
U8, S16_LE, S16_BE, S24_3LE, S24_3BE, FLOAT_LE, FLOAT_BE
采样率：8000 - 48000 Hz 连续可调

播放
-----
例如，播放设备配置为最多 4 个子流进行硬件混音。如果需要，可以更改为最多 24 个子流。
单声道文件将在左右声道播放。每个声道可以在每个流中静音，以便独立使用 8 个模拟/数字输出。

捕获
-----
每个捕获设备有一个子流。例如，只支持立体声格式。
### 混音器
-----
<Master> 和 <Master Capture>
- 播放和录制的模拟音量控制
<PCM 0-3> 和 <PCM Capture>
- 各个模拟子流的数字音量控制
<AES 0-3> 和 <AES Capture>
- 各个 AES/EBU 子流的数字音量控制
<Monitoring>
- 从 'pcm0c' 到 'pcm0p' 的环回，带有数字音量和静音控制
备注：为了获得最佳音频质量，请尽量保持 PCM 和 AES 音量控制为 0 衰减（范围 0 至 255 中的 219，约等于 86%，使用 alsamixer 时）

### 尚未实现的功能
- 外部时钟支持（AES/EBU、字时钟、时间码、视频同步）
- MPEG 音频格式
- 单声道录音
- 板载效果和采样率转换
- 链接流

### 固件
[自 2.6.11 版本起，当设置 CONFIG_FW_LOADER 时，固件可以自动加载。mixartloader 仅在旧版本或内核构建驱动程序时需要。]

为了在模块加载后自动加载固件，请使用安装命令。例如，在 /etc/modprobe.d/mixart.conf 中添加以下条目以用于 miXart 驱动程序：
```
install snd-mixart /sbin/modprobe --first-time -i snd-mixart && /usr/bin/mixartloader
```

（对于 2.2/2.4 内核，可以在 /etc/modules.conf 中添加 "post-install snd-mixart /usr/bin/vxloader"。）

固件二进制文件安装在 /usr/share/alsa/firmware（或根据 configure 的前缀选项安装在 /usr/local/share/alsa/firmware）。将有一个 miXart.conf 文件，定义 DSP 映像文件。
固件文件版权归 Digigram SA 所有。

### 版权声明
版权所有 © 2003 Digigram SA <alsa@digigram.com>
根据 GPL 发布
