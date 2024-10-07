==============================================================
高级 Linux 声音架构 - 驱动配置指南
==============================================================

内核配置
====================

为了启用 ALSA 支持，您至少需要使用主声卡支持（``CONFIG_SOUND``）来构建内核。由于 ALSA 可以模拟 OSS，因此您无需选择任何 OSS 模块。如果您希望在 ALSA 下运行 OSS 应用程序，请启用“OSS API 模拟”（``CONFIG_SND_OSSEMUL``）以及 OSS 混音器和 PCM 支持。如果您想在如 SB Live! 这样的声卡上支持 WaveTable 功能，则需要启用“序列器支持”（``CONFIG_SND_SEQUENCER``）。为了使 ALSA 的调试信息更详细，可以启用“详细 printk”和“调试”选项。要检查内存泄漏，请开启“调试内存”。启用“调试检测”将增加对声卡检测的检查。

请注意，所有 ALSA ISA 驱动都支持 Linux isapnp API（如果声卡支持 ISA PnP）。您无需使用 isapnptools 来配置这些声卡。

模块参数
=================

用户可以使用选项加载模块。如果模块支持多种声卡并且您有多种相同类型的声卡，则可以使用逗号分隔多个值来指定选项。

snd 模块
----------

这是 ALSA 的核心模块。所有 ALSA 声卡驱动都会使用它。它包含以下具有全局影响的选项：

major
    声音驱动的主要编号；
    默认：116

cards_limit
    用于自动加载的声卡索引限制（1-8）；
    默认：1；
    如果要自动加载多张声卡，请指定此选项并配合 snd-card-X 别名一起使用。

slots
    为给定驱动预留槽位索引；
    此选项接受多个字符串
参见 `模块自动加载支持`_ 部分以获取详细信息
调试
    指定调试消息级别；
    （0 = 禁用调试打印，1 = 正常调试消息，
    2 = 详细调试消息）；
    当 ``CONFIG_SND_DEBUG=y`` 时此选项才会出现
此选项可以通过 sysfs 动态更改
    /sys/modules/snd/parameters/debug 文件

snd-pcm-oss 模块
------------------

PCM OSS 模拟模块
此模块采用一些选项来改变设备的映射
dsp_map
    PCM 设备编号映射到第一个 OSS 设备；
    默认值：0
adsp_map
    PCM 设备编号映射到第二个 OSS 设备；
    默认值：1
nonblock_open
    不阻塞打开忙碌的 PCM 设备；
    默认值：1

例如，当 ``dsp_map=2`` 时，/dev/dsp 将映射到第 0 张卡上的 PCM #2。同样地，当 ``adsp_map=0`` 时，/dev/adsp 将映射到第 0 张卡上的 PCM #0。
对于更改第二张或之后的卡，可以使用逗号分隔的形式指定选项，例如 ``dsp_map=0,1``。
``nonblock_open`` 选项用于更改 PCM 打开设备的行为。当此选项非零时，打开一个忙碌的 OSS PCM 设备不会被阻塞，而是立即返回 EAGAIN（就像设置了 O_NONBLOCK 标志一样）。

snd-rawmidi 模块
------------------

此模块采用与 snd-pcm-oss 模块类似的选项来改变设备的映射。
midi_map
    指定给第一个OSS设备的MIDI设备编号映射；
    默认值：0
amidi_map
    指定给第二个OSS设备的MIDI设备编号映射；
    默认值：1

模块 snd-soc-core
-------------------

soc 核心模块。所有 ALSA 声卡驱动都会使用它。
它包含以下选项，这些选项具有全局影响：
prealloc_buffer_size_kbytes
    指定预分配缓冲区大小（单位：千字节，默认值：512）

声卡顶层模块的通用参数
--------------------------------------------

每个声卡顶层模块都接受以下选项：
index
    声卡的索引号（槽位号）；
    取值范围：0 到 31 或者负数；
    如果是非负数，则分配该索引号；
    如果是负数，则解释为允许索引的位掩码；
    分配第一个空闲的允许索引；
    默认值：-1
id
    声卡ID（标识符或名称）；
    最多可以有 15 个字符长；
    默认值：声卡类型；
    在 `/proc/asound/` 下创建一个与此 ID 同名的目录，
    包含有关声卡的信息；
    此 ID 可以在识别声卡时代替索引号
enable
    启用声卡；
    默认值：启用，对于 PCI 和 ISA PnP 声卡

这些选项用于指定实例的顺序或者控制多个设备绑定到同一驱动程序时的启用和禁用。例如，很多机器有两个 HD-Audio 控制器（一个用于 HDMI/DP 音频，另一个用于板载模拟音频）。在大多数情况下，第二个控制器是主要使用的，并且用户希望将其分配为第一个出现的声卡。他们可以通过指定 "index=1,0" 的模块参数来交换分配的槽位。
如今，在像 PulseAudio 和 PipeWire 这样的支持动态配置的声音后端中，这个功能几乎没有用处，但在过去静态配置时这是一个帮助。

模块 snd-adlib
----------------

AdLib FM 卡的模块
port
    OPL 芯片的端口号

此模块支持多个声卡。它不支持自动探测，因此必须指定端口。对于实际的 AdLib FM 卡，端口号为 0x388。
请注意，此卡没有 PCM 支持，也没有混音器；只有 FM 合成。
确保您已经安装了 alsa-tools 包中的 `sbiload` 工具，并且在加载模块后，通过 `sbiload -l` 查找分配的 ALSA 序列器端口号。
示例输出：

```
端口     客户端名称                       端口名称
64:0     OPL2 FM合成器                     OPL2 FM 端口
```

加载 `std.sb` 和 `drums.sb` 补丁，这些补丁也由 `sbiload` 提供：

```
sbiload -p 64:0 std.sb drums.sb
```

如果您使用此驱动程序来驱动 OPL3，可以使用 `std.o3` 和 `drums.o3`。要让声卡产生声音，请使用 alsa-utils 中的 `aplaymidi`：

```
aplaymidi -p 64:0 foo.mid
```

snd-ad1816a 模块
------------------

基于 Analog Devices AD1816A/AD1815 ISA 芯片的声卡模块

clockfreq
    AD1816A 芯片的时钟频率（默认值 = 0, 33000 Hz）

此模块支持多张声卡、自动探测和即插即用功能。

snd-ad1848 模块
-----------------

基于 AD1848/AD1847/CS4248 ISA 芯片的声卡模块

port
    AD1848 芯片的端口号
irq
    AD1848 芯片的中断请求号
dma1
    AD1848 芯片的 DMA 号（0, 1, 3）

此模块支持多张声卡。不支持自动探测，因此必须指定主端口号！其他端口是可选的。
支持电源管理功能。

snd-ad1889 模块
-----------------

Analog Devices AD1889 芯片模块

ac97_quirk
    针对奇怪硬件的 AC'97 解决方案；
    详细信息请参见 intel8x0 模块的描述

此模块支持多张声卡。

snd-ali5451 模块
------------------

ALi M5451 PCI 芯片模块

pcm_channels
    分配给 PCM 的硬件通道数
spdif
    支持 SPDIF 输入输出；
    默认：禁用

此模块支持一张芯片并自动探测。
电源管理得到支持  
模块 snd-als100
-----------------

基于 Avance Logic ALS100/ALS120 ISA 芯片的声音卡模块  
此模块支持多张声卡、自动探测和即插即用（PnP）  
电源管理得到支持  
模块 snd-als300
-----------------

适用于 Avance Logic ALS300 和 ALS300+ 的模块  

此模块支持多张声卡  
电源管理得到支持  
模块 snd-als4000
------------------

基于 Avance Logic ALS4000 PCI 芯片的声音卡模块  
joystick_port  
    用于传统游戏杆支持的端口号；  
    0 = 禁用（默认），1 = 自动检测  

此模块支持多张声卡、自动探测和即插即用（PnP）  
电源管理得到支持  
模块 snd-asihpi
-----------------

适用于 AudioScience ASI 声卡的模块  

enable_hpi_hwdep  
    为 AudioScience 声卡启用 HPI hwdep  

此模块支持多张声卡
驱动程序需要内核上的固件加载器支持

snd-atiixp 模块
-----------------

用于 ATI IXP 150/200/250/400 AC97 控制器的模块
ac97_clock
    AC'97 时钟（默认 = 48000）
ac97_quirk
    AC'97 对奇怪硬件的变通方法；请参阅下面的 `AC97 Quirk Option`_ 部分
ac97_codec
    变通方法以指定要使用的 AC'97 编解码器而不是探测
如果这对你有效，请提交一个包含你的 `lspci -vn` 输出的 bug 报告
（-2 = 强制探测，-1 = 默认行为，0-2 = 使用指定的编解码器）
spdif_aclink
    通过 AC-link 的 S/PDIF 传输（默认 = 1）

此模块支持一张声卡并自动探测
ATI IXP 有控制 S/PDIF 输出的两种不同方法。一种是通过 AC-link，另一种是通过“直接”S/PDIF 输出。实现取决于主板，你需要通过 spdif_aclink 模块选项选择正确的方法。
支持电源管理

snd-atiixp-modem 模块
-----------------------

用于 ATI IXP 150/200/250 AC97 调制解调控制器的模块
此模块支持一张调制解调卡并自动探测
注：此模块的默认索引值为 -2，即第一个插槽被排除在外。
支持电源管理。
模块 snd-au8810、snd-au8820、snd-au8830
------------------------------------------------

此模块适用于 Aureal Vortex、Vortex2 和 Advantage 设备
pcifix
    控制 PCI 修正；
    0 = 禁用所有修正，
    1 = 强制将 Aureal 卡的 PCI 延迟设置为 0xff，
    2 = 强制启用 VIA KT133 AGP 桥接器上的扩展 PCI#2 内部主控以实现对空请求的有效处理，
    3 = 同时强制启用两个设置，
    255 = 自动检测所需设置（默认）

此模块支持所有 ADB PCM 通道、AC97 混音器、SPDIF、硬件均衡器、mpu401、游戏端口。A3D 和波表支持仍在开发中。
开发和反向工程工作在 https://savannah.nongnu.org/projects/openvortex/ 进行。
SPDIF 输出是 AC97 编解码器输出的副本，除非您使用“spdif”PCM 设备，这允许原始数据直通。
硬件均衡器和 SPDIF 仅存在于 Vortex2 和 Advantage 中。
注意：一些 ALSA 混音器应用程序无法正确处理 SPDIF 采样率控制。如果您遇到与此相关的问题，请尝试使用其他符合 ALSA 标准的混音器（alsamixer 可用）。
模块 snd-azt1605
------------------------

此模块适用于基于 Aztech AZT1605 芯片组的 Aztech Sound Galaxy 声卡
port
    BASE 的端口号（0x220、0x240、0x260、0x280）
wss_port
    WSS 的端口号（0x530、0x604、0xe80、0xf40）
irq
    WSS 的中断请求号（7、9、10、11）
dma1
    WSS 播放的 DMA 号（0、1、3）
dma2
    WSS 录制的 DMA 号（0、1），-1 = 禁用（默认）
mpu_port
    MPU-401 UART 的端口号（0x300、0x330），-1 = 禁用（默认）
mpu_irq
    MPU-401 UART 的中断请求号（3、5、7、9），-1 = 禁用（默认）
fm_port
    OPL3 的端口号（0x388），-1 = 禁用（默认）

此模块支持多张声卡。它不支持自动探测：“port”、“wss_port”、“irq” 和 “dma1” 必须指定。
其他值为可选。
``port`` 需要与卡上的 BASE ADDRESS 跳线匹配（0x220 或 0x240），或者对于那些具有 EEPROM 并且其“CONFIG MODE”跳线设置为“EEPROM SETTING”的卡，需要与卡的 EEPROM 中存储的值匹配。其他值可以从上面列举的选项中自由选择。

如果指定了 ``dma2`` 并且与 ``dma1`` 不同，则卡将以全双工模式运行。当 ``dma1=3`` 时，只有 ``dma2=0`` 是有效的，并且这是唯一可以启用捕获的方式，因为只有通道 0 和 1 可用于捕获。

通用设置是：``port=0x220 wss_port=0x530 irq=10 dma1=1 dma2=0 mpu_port=0x330 mpu_irq=9 fm_port=0x388``

无论你选择哪个 IRQ 和 DMA 通道，请确保在 BIOS 中为 legacy ISA 预留这些资源。

模块 snd-azt2316
------------------

基于 Aztech AZT2316 芯片组的 Aztech Sound Galaxy 声卡模块

port
    BASE 的端口号（0x220、0x240、0x260、0x280）
wss_port
    WSS 的端口号（0x530、0x604、0xe80、0xf40）
irq
    WSS 的 IRQ 号（7、9、10、11）
dma1
    WSS 播放的 DMA 号（0、1、3）
dma2
    WSS 捕获的 DMA 号（0、1），-1 表示禁用（默认）
mpu_port
    MPU-401 UART 的端口号（0x300、0x330），-1 表示禁用（默认）
mpu_irq
    MPU-401 UART 的 IRQ 号（5、7、9、10），-1 表示禁用（默认）
fm_port
    OPL3 的端口号（0x388），-1 表示禁用（默认）

此模块支持多张卡。它不支持自动探测：必须指定 ``port``、``wss_port``、``irq`` 和 ``dma1``。
其他值是可选的。

``port`` 需要与卡上的 BASE ADDRESS 跳线匹配（0x220 或 0x240），或者对于那些具有 EEPROM 并且其“CONFIG MODE”跳线设置为“EEPROM SETTING”的卡，需要与卡的 EEPROM 中存储的值匹配。其他值可以从上面列举的选项中自由选择。

如果指定了 ``dma2`` 并且与 ``dma1`` 不同，则卡将以全双工模式运行。当 ``dma1=3`` 时，只有 ``dma2=0`` 是有效的，并且这是唯一可以启用捕获的方式，因为只有通道 0 和 1 可用于捕获。

通用设置是：``port=0x220 wss_port=0x530 irq=10 dma1=1 dma2=0 mpu_port=0x330 mpu_irq=9 fm_port=0x388``
无论你选择哪些IRQ和DMA通道，请确保在BIOS中为传统的ISA保留它们。

模块 snd-aw2
--------------

适用于Audiowerk2声卡的模块

此模块支持多张卡

模块 snd-azt2320
------------------

适用于基于Aztech System AZT2320 ISA芯片（仅即插即用）的声卡

此模块支持多张卡、即插即用和自动探测

支持电源管理

模块 snd-azt3328
------------------

适用于基于Aztech AZF3328 PCI芯片的声卡

joystick
    启用游戏杆（默认关闭）

此模块支持多张卡

模块 snd-bt87x
----------------

适用于基于Bt87x芯片的视频卡

digital_rate
    覆盖默认的数字频率（Hz）

load_all
    即使不知道卡的型号也加载驱动程序

此模块支持多张卡

注意：此模块的默认索引值为-2，即第一个插槽被排除在外。
### Module snd-ca0106
-----------------
适用于 Creative Audigy LS 和 SB Live 24位声卡的模块

此模块支持多张声卡

### Module snd-cmi8330
-----------------
适用于基于 C-Media CMI8330 ISA 芯片的声卡

isapnp
    ISA 即插即用检测 - 0 = 禁用，1 = 启用（默认）

当使用 `isapnp=0` 时，以下选项可用：

wssport
    CMI8330 芯片（WSS）的端口号
wssirq
    CMI8330 芯片（WSS）的中断号
wssdma
    CMI8330 芯片（WSS）的第一个 DMA 号
sbport
    CMI8330 芯片（SB16）的端口号
sbirq
    CMI8330 芯片（SB16）的中断号
sbdma8
    CMI8330 芯片（SB16）的 8 位 DMA 号
sbdma16
    CMI8330 芯片（SB16）的 16 位 DMA 号
fmport
    （可选）OPL3 输入输出端口
mpuport
    （可选）MPU401 输入输出端口
mpuirq
    （可选）MPU401 中断号

此模块支持多张声卡和自动探测，并且支持电源管理

### Module snd-cmipci
-----------------
适用于 C-Media CMI8338/8738/8768/8770 PCI 声卡的模块

mpu_port
    MIDI 接口的端口地址（仅限 8338）：
    0x300, 0x310, 0x320, 0x330 = 传统端口，
    1 = 集成 PCI 端口（8738 的默认设置），
    0 = 禁用
fm_port
    OPL-3 FM 合成器的端口地址（仅限 8x38）：
    0x388 = 传统端口，
    1 = 集成 PCI 端口（8738 的默认设置），
    0 = 禁用
soft_ac3
    原始 SPDIF 数据包的软件转换（仅限 model 033）（默认值 = 1）
joystick_port
    摇杆端口地址（0 = 禁用，1 = 自动探测）

此模块支持自动探测和多张声卡，并且支持电源管理

### Module snd-cs4231
-----------------
适用于基于 CS4231 ISA 芯片的声卡

port
    CS4231 芯片的端口号
mpu_port
    MPU-401 UART 的端口号（可选），-1 = 禁用
irq
    CS4231 芯片的中断号
mpu_irq
    MPU-401 UART 的中断号
dma1
    CS4231 芯片的第一个 DMA 号
dma2
    CS4231 芯片的第二个 DMA 号

此模块支持多张声卡。此模块不支持自动探测，因此必须指定主端口号！其他端口是可选的，并且支持电源管理
### 模块 snd-cs4236
-----------------

基于 CS4232/CS4232A、CS4235/CS4236/CS4236B/CS4237B/CS4238B/CS4239 ISA 芯片的声卡模块  
isapnp  
    ISA 即插即用检测 - 0 = 禁用，1 = 启用（默认）

使用 `isapnp=0` 时，以下选项可用：

port  
    CS4236 芯片的端口号（即插即用设置 - 0x534）  
cport  
    CS4236 芯片的控制端口号（即插即用设置 - 0x120, 0x210, 0xf00）  
mpu_port  
    MPU-401 UART 的端口号（即插即用设置 - 0x300），-1 = 禁用  
fm_port  
    CS4236 芯片的 FM 端口号（即插即用设置 - 0x388），-1 = 禁用  
irq  
    CS4236 芯片的 IRQ 号（5, 7, 9, 11, 12, 15）  
mpu_irq  
    MPU-401 UART 的 IRQ 号（9, 11, 12, 15）  
dma1  
    CS4236 芯片的第一个 DMA 号（0, 1, 3）  
dma2  
    CS4236 芯片的第二个 DMA 号（0, 1, 3），-1 = 禁用  

此模块支持多张声卡。如果不使用 ISA 即插即用，则必须指定主端口和控制端口！！！其他端口是可选的。  
此模块支持电源管理。  
此模块作为 snd-cs4232 的别名，因为它也提供了旧版 snd-cs4232 的功能。

### 模块 snd-cs4281
-----------------

Cirrus Logic CS4281 声卡芯片模块  
dual_codec  
    辅助编解码器 ID（0 = 禁用，默认）

此模块支持多张声卡。  
此模块支持电源管理。

### 模块 snd-cs46xx
-----------------

基于 CS4610/CS4612/CS4614/CS4615/CS4622/CS4624/CS4630/CS4280 PCI 芯片的 PCI 声卡模块  
external_amp  
    强制启用外部放大器  
thinkpad  
    强制启用 Thinkpad 的 CLKRUN 控制
mmap_valid  
支持OSS mmap模式（默认=0）  
此模块支持多张声卡和自动探测功能  
通常外部放大器和CLKRUN控制会根据PCI子供应商/设备ID自动检测。如果它们不起作用，请明确给出上述选项  
支持电源管理  
snd-cs5530模块  
-----------------  
适用于Cyrix/NatSemi Geode 5530芯片的模块  

snd-cs5535audio模块  
----------------------  
适用于多功能CS5535伴行PCI设备的模块  
支持电源管理  

snd-ctxfi模块  
-----------------  
适用于Creative Sound Blaster X-Fi系列板卡（20k1/20k2芯片）的模块  
* Creative Sound Blaster X-Fi Titanium Fatal1ty Champion Series  
* Creative Sound Blaster X-Fi Titanium Fatal1ty Professional Series  
* Creative Sound Blaster X-Fi Titanium Professional Audio  
* Creative Sound Blaster X-Fi Titanium  
* Creative Sound Blaster X-Fi Elite Pro  
* Creative Sound Blaster X-Fi Platinum  
* Creative Sound Blaster X-Fi Fatal1ty  
* Creative Sound Blaster X-Fi XtremeGamer  
* Creative Sound Blaster X-Fi XtremeMusic  

reference_rate  
参考采样率，44100或48000（默认）  
multiple  
参考采样率的倍数，1或2（默认）  
subsystem  
用于探测时覆盖PCI SSID；该值由SSVID << 16 | SSDID组成  
默认为零，表示不覆盖  
此模块支持多张声卡  

snd-darla20模块  
------------------  
适用于Echoaudio Darla20的模块  
此模块支持多张声卡  
驱动程序需要内核中的固件加载器支持
### 模块 snd-darla24
------------------

此模块支持 Echoaudio Darla24

此模块支持多个声卡
驱动程序需要内核上的固件加载器支持

### 模块 snd-dt019x
-----------------

此模块支持 Diamond Technologies DT-019X / Avance Logic ALS-007（仅即插即用）

此模块支持多个声卡。此模块仅在启用 ISA 即插即用支持时才可用
支持电源管理

### 模块 snd-dummy
----------------

此模块用于虚拟声卡。这个“声卡”不执行任何输入或输出，但你可以使用此模块来满足任何需要声卡的应用程序（如 RealPlayer）
pcm_devs
    分配给每个声卡的 PCM 设备数量（默认 = 1，最多 4）
pcm_substreams
    分配给每个 PCM 的 PCM 子流数量（默认 = 8，最多 128）
hrtimer
    使用高精度定时器（=1，默认）或系统定时器（=0）
fake_buffer
    虚拟缓冲区分配（默认 = 1）

当创建多个 PCM 设备时，snd-dummy 会为每个 PCM 设备提供不同的行为：
* 0 = 支持 mmap 的交错模式
* 1 = 支持 mmap 的非交错模式
* 2 = 不支持 mmap 的交错模式
* 3 = 不支持 mmap 的非交错模式

默认情况下，snd-dummy 驱动程序不会分配实际的缓冲区，而是忽略读写操作或将一个虚拟页面映射到所有缓冲区页面，以节省资源。如果你的应用程序需要读取/写入的数据缓冲区一致，请传递 fake_buffer=0 选项
支持电源管理

### 模块 snd-echo3g
-----------------

此模块支持 Echoaudio 3G 声卡（Gina3G/Layla3G）

此模块支持多个声卡
驱动程序需要内核上的固件加载器支持

### 模块 snd-emu10k1
------------------

此模块支持基于 EMU10K1/EMU10k2 的 PCI 声卡
* Sound Blaster Live!
* Sound Blaster PCI 512
* Sound Blaster Audigy
* E-MU APS（部分支持）
* E-MU DAS

extin
    FX8010 可用外部输入的位图（见下文）
extout
    FX8010 可用外部输出的位图（见下文）
seq_ports
    已分配的音序器端口（默认为 4 个）
max_synth_voices
    用于波表合成的最大声音数（默认为 64）
max_buffer_size
    指定以 MB 为单位的波表/PCM 缓冲区的最大大小。默认值为 128
enable_ir
    启用红外功能

此模块支持多张声卡和自动探测
输入与输出配置			[extin/extout]
* Creative 卡无数字输出			[0x0003/0x1f03]
* Creative 卡有数字输出			[0x0003/0x1f0f]
* Creative 卡有数字 CD 输入			[0x000f/0x1f0f]
* Creative 卡无数字输出 + LiveDrive		[0x3fc3/0x1fc3]
* Creative 卡有数字输出 + LiveDrive		[0x3fc3/0x1fcf]
* Creative 卡有数字 CD 输入 + LiveDrive		[0x3fcf/0x1fcf]
* Creative 卡无数字输出 + 数字 I/O 2		[0x0fc3/0x1f0f]
* Creative 卡有数字输出 + 数字 I/O 2		[0x0fc3/0x1f0f]
* Creative 卡有数字 CD 输入 + 数字 I/O 2		[0x0fcf/0x1f0f]
* Creative 5.1 卡 + 数字输出 + LiveDrive		[0x3fc3/0x1fff]
* Creative 5.1 卡（c）2003 年版			[0x3fc3/0x7cff]
* Creative 卡所有输入和输出			[0x3fff/0x7fff]

支持电源管理
模块 snd-emu10k1x
-------------------

适用于 Creative Emu10k1X（SB Live Dell OEM 版本）的模块

此模块支持多张声卡
模块 snd-ens1370
------------------

适用于 Ensoniq AudioPCI ES1370 PCI 声卡的模块
* SoundBlaster PCI 64
* SoundBlaster PCI 128

joystick
    启用游戏杆（默认关闭）

此模块支持多张声卡和自动探测
支持电源管理
模块 snd-ens1371
------------------

适用于 Ensoniq AudioPCI ES1371 PCI 声卡的模块
* SoundBlaster PCI 64
* SoundBlaster PCI 128
* SoundBlaster Vibra PCI

joystick_port
    游戏杆端口号（0x200、0x208、0x210、0x218），0 = 禁用（默认），1 = 自动检测

此模块支持多张声卡和自动探测
支持电源管理
### 模块 snd-es1688
-----------------

此模块适用于 ESS AudioDrive ES-1688 和 ES-688 声卡
isapnp
    ISA PnP 检测 - 0 = 禁用，1 = 启用（默认）
mpu_port
    MPU-401 端口的端口号（0x300、0x310、0x320、0x330），-1 = 禁用（默认）
mpu_irq
    MPU-401 端口的中断请求号（IRQ）（5、7、9、10）
fm_port
    OPL3 的端口号（可选；默认情况下与 MPU-401 共享同一个端口）

当使用 `isapnp=0` 时，以下附加选项可用：

port
    ES-1688 芯片的端口号（0x220、0x240、0x260）
irq
    ES-1688 芯片的中断请求号（IRQ）（5、7、9、10）
dma8
    ES-1688 芯片的数据传输模式号（DMA）（0、1、3）

此模块支持多张声卡和自动探测（不包括 MPU-401 端口），以及带有 ES968 芯片的即插即用（PnP）功能。

### 模块 snd-es18xx
-----------------

此模块适用于 ESS AudioDrive ES-18xx 声卡
isapnp
    ISA PnP 检测 - 0 = 禁用，1 = 启用（默认）

当使用 `isapnp=0` 时，以下选项可用：

port
    ES-18xx 芯片的端口号（0x220、0x240、0x260）
mpu_port
    MPU-401 端口的端口号（0x300、0x310、0x320、0x330），-1 = 禁用（默认）
fm_port
    FM 的端口号（可选，不使用）
irq
    ES-18xx 芯片的中断请求号（IRQ）（5、7、9、10）
dma1
    ES-18xx 芯片的第一个数据传输模式号（DMA）（0、1、3）
dma2
    ES-18xx 芯片的第一个数据传输模式号（DMA）（0、1、3）

此模块支持多张声卡、ISA PnP 和自动探测（不包括 MPU-401 端口，如果未使用本机 ISA PnP 例程的话）。
当 `dma2` 等于 `dma1` 时，驱动程序以半双工模式工作。
支持电源管理。

### 模块 snd-es1938
-----------------

此模块适用于基于 ESS Solo-1（ES1938、ES1946）芯片的声卡
此模块支持多张声卡和自动探测。
支持电源管理。

### 模块 snd-es1968
-----------------

此模块适用于基于 ESS Maestro-1/2/2E（ES1968/ES1978）芯片的声卡。
total_bufsize  
总缓冲区大小（单位：千字节，范围：1-4096千字节）

pcm_substreams_p  
播放声道数（范围：1-8，默认值：2）

pcm_substreams_c  
录音声道数（范围：1-8，默认值：0）

clock  
时钟设置（0 = 自动检测）

use_pm  
支持电源管理（0 = 关闭，1 = 开启，2 = 自动，默认值：2）

enable_mpu  
启用MPU401（0 = 关闭，1 = 开启，2 = 自动，默认值：2）

joystick  
启用游戏杆（默认关闭）

此模块支持多张声卡和自动探测。
支持电源管理。
Module snd-fm801  
----------------

此模块用于基于ForteMedia FM801的PCI声卡。

tea575x_tuner  
启用TEA575x调谐器；
1 = MediaForte 256-PCS，
2 = MediaForte 256-PCPR，
3 = MediaForte 64-PCR
高16位是视频（或无线电）设备编号+1；
例如：0x10002（MediaForte 256-PCPR，设备1）

此模块支持多张声卡和自动探测。
支持电源管理。
Module snd-gina20  
-----------------

此模块用于Echoaudio Gina20。

此模块支持多张声卡。
驱动程序需要内核中的固件加载器支持。
Module snd-gina24  
-----------------

此模块用于Echoaudio Gina24。

此模块支持多张声卡。
驱动程序需要内核中的固件加载器支持。
Module snd-gusclassic  
---------------------

此模块用于Gravis UltraSound Classic声卡。
### 模块 snd-gusextreme
---------------------

**模块用于 Gravis UltraSound Extreme (Synergy ViperMax) 声卡**

- **port**
  - ES-1688 芯片的端口号 (0x220, 0x230, 0x240, 0x250, 0x260)
- **gf1_port**
  - GF1 芯片的端口号 (0x210, 0x220, 0x230, 0x240, 0x250, 0x260, 0x270)
- **mpu_port**
  - MPU-401 端口的端口号 (0x300, 0x310, 0x320, 0x330)，-1 = 禁用
- **irq**
  - ES-1688 芯片的 IRQ 号 (5, 7, 9, 10)
- **gf1_irq**
  - GF1 芯片的 IRQ 号 (3, 5, 9, 11, 12, 15)
- **mpu_irq**
  - MPU-401 端口的 IRQ 号 (5, 7, 9, 10)
- **dma8**
  - ES-1688 芯片的 DMA 号 (0, 1, 3)
- **dma1**
  - GF1 芯片的 DMA 号 (1, 3, 5, 6, 7)
- **joystick_dac**
  - 0 到 31，(0.59V-4.52V 或 0.389V-2.98V)
- **voices**
  - GF1 的音轨限制 (14-32)
- **pcm_voices**
  - 预留的 PCM 音轨

此模块支持多张声卡和自动探测（不包括 MPU-401 端口）

### 模块 snd-gusmax
-----------------

**模块用于 Gravis UltraSound MAX 声卡**

- **port**
  - GF1 芯片的端口号 (0x220, 0x230, 0x240, 0x250, 0x260)
- **irq**
  - GF1 芯片的 IRQ 号 (3, 5, 9, 11, 12, 15)
- **dma1**
  - GF1 芯片的 DMA 号 (1, 3, 5, 6, 7)
- **dma2**
  - GF1 芯片的 DMA 号 (1, 3, 5, 6, 7, -1=禁用)
- **joystick_dac**
  - 0 到 31，(0.59V-4.52V 或 0.389V-2.98V)
- **voices**
  - GF1 的音轨限制 (14-32)
- **pcm_voices**
  - 预留的 PCM 音轨

此模块支持多张声卡和自动探测

### 模块 snd-hda-intel
--------------------

**模块用于 Intel HD Audio (ICH6, ICH6M, ESB2, ICH7, ICH8, ICH9, ICH10, PCH, SCH)，ATI SB450, SB600, R600, RS600, RS690, RS780, RV610, RV620, RV630, RV635, RV670, RV770, VIA VT8251/VT8237A, SIS966, ULI M5461**

**每张声卡实例有多个选项**

- **model**
  - 强制指定模型名称
- **position_fix**
  - 修复 DMA 指针；
  - -1 = 系统默认：根据控制器硬件选择合适的值，
  - 0 = 自动：当 POSBUF 不工作时回退到 LPIB，
  - 1 = 使用 LPIB，
  - 2 = POSBUF：使用位置缓冲区，
  - 3 = VIACOMBO：VIA 特定的捕获工作区，
  - 4 = COMBO：播放时使用 LPIB，捕获流时自动，
  - 5 = SKL+：应用最近的 Intel 芯片上的延迟计算，
  - 6 = FIFO：使用固定 FIFO 大小来修正位置，适用于最近的 AMD 芯片
- **probe_mask**
  - 探测编解码器的位掩码（默认 = -1，表示所有插槽）；
  - 当第 8 位 (0x100) 被设置时，低 8 位作为“固定”的编解码器插槽；即驱动程序会探测插槽，无论硬件返回什么结果
- **probe_only**
  - 只进行探测而不初始化编解码器（默认=关闭）；
  - 有助于调试时检查初始编解码器状态
- **bdl_pos_adj**
  - 指定 DMA IRQ 定时延迟的样本数
  - 传递 -1 将使驱动程序基于控制器芯片选择合适的值
- **patch**
  - 指定在初始化编解码器之前的早期“补丁”文件以修改 HD-Audio 设置
  - 此选项仅在设置 ``CONFIG_SND_HDA_PATCH_LOADER=y`` 时可用。详见 hd-audio/notes.rst
- **beep_mode**
  - 选择蜂鸣注册模式 (0=关闭, 1=开启)；
  - 默认值通过 ``CONFIG_SND_HDA_INPUT_BEEP_MODE`` kconfig 设置
[单个（全局）选项]

single_cmd
    使用单个立即命令与编解码器通信（仅用于调试）
enable_msi
    启用消息信号中断（MSI）（默认：关闭）
power_save
    自动节能超时时间（以秒为单位，0 = 禁用）
power_save_controller
    在节能模式下重置高清音频控制器（默认：开启）
align_buffer_size
    强制将缓冲区/周期大小调整为128字节的倍数
    这在内存访问方面更高效，但不符合HDA规范，并且阻止用户指定确切的周期/缓冲区大小。（默认：开启）
snoop
    启用/禁用窥探（默认：开启）

此模块支持多张声卡和自动探测
有关HD-audio驱动程序的更多详细信息，请参阅hd-audio/notes.rst
每个编解码器可能有不同的配置模型表
如果您的机器未列在那里，则会设置默认（通常是最小）配置。您可以通过传递``model=<name>``选项来指定某个模型。不同编解码器芯片有不同的模型。可用模型列表可以在hd-audio/models.rst中找到
模型名称``generic``被视为特殊情况。当提供此模型时，驱动程序将使用不带“codec-patch”的通用编解码器解析器。这有时对测试和调试很有帮助
模型选项也可以用于别名到另一个PCI或编解码器SSID。当它以``model=XXXX:YYYY``的形式传递时，其中XXXX和YYYY分别是十六进制格式的子供应商和子设备ID，驱动程序将引用该SSID作为怪癖表的参考
如果默认配置不起作用，并且上述情况之一与您的设备匹配，请将其与alsa-info.sh输出（带有``--no-upload``选项）一起报告给内核Bugzilla或alsa-devel邮件列表（参见“链接和地址”部分）
``power_save``和``power_save_controller``选项用于节能模式。详情请参阅powersave.rst
注意2：如果您在输出中听到咔嗒声，尝试使用模块选项``position_fix=1``或``2``。``position_fix=1``将使用SD_LPIB寄存器值（不进行FIFO大小校正）作为当前DMA指针。``position_fix=2``将使驱动程序使用位置缓冲区而不是读取SD_LPIB寄存器。
通常情况下，SD_LPIB 寄存器比位置缓冲区更准确。

``position_fix=3`` 是针对 VIA 设备的。捕获流的位置会从 LPIB 和 POSBUF 的值进行检查。``position_fix=4`` 是一种组合模式，使用 LPIB 进行回放，POSBUF 进行捕获。

注意：如果在加载时出现大量“azx_get_response 超时”消息，这可能是中断问题（例如 ACPI IRQ 路由）。可以尝试使用如 ``pci=noacpi`` 的选项启动。此外，您还可以尝试使用 ``single_cmd=1`` 模块选项。这将把 HDA 控制器和编解码器之间的通信方法切换为单个立即命令，而不是使用 CORB/RIRB。基本上，单命令模式仅提供给 BIOS，并且您也不会收到未请求的事件。但是，至少这种方式可以独立于 IRQ 工作。请记住这是最后的手段，应尽可能避免使用。

关于 “azx_get_response 超时” 问题的更多说明：
在某些硬件上，您可能需要添加一个适当的 probe_mask 选项来避免上述的 “azx_get_response 超时” 问题。这种情况通常发生在访问不存在或不工作的编解码器插槽（可能是调制解调器插槽）导致通过 HD 音频总线的通信停滞。您可以启用 ``CONFIG_SND_DEBUG_VERBOSE`` 来查看哪些编解码器插槽被探测，或者直接从编解码器 proc 文件的文件名中查看。然后通过 probe_mask 选项限制要探测的插槽。
例如，``probe_mask=1`` 表示只探测第一个插槽，而 ``probe_mask=4`` 表示只探测第三个插槽。

支持电源管理。

snd-hdsp 模块
--------------

RME Hammerfall DSP 音频接口模块

此模块支持多个声卡。
注意：当设置了 ``CONFIG_FW_LOADER`` 时，固件数据可以通过热插拔自动加载。否则，您需要通过 alsa-tools 包中的 hdsploader 实用程序加载固件。
固件数据位于 alsa-firmware 包中。
注意：snd-page-alloc 模块完成了以前由 snd-hammerfall-mem 模块完成的工作。它将在发现任何 HDSP 卡时提前分配缓冲区。为了确保缓冲区的分配，请在启动序列的早期加载 snd-page-alloc 模块。请参阅“早期缓冲区分配”部分。
### 模块 snd-hdspm
----------------

此模块用于 RME HDSP MADI 板卡
- precise_ptr
  - 启用精确指针，或禁用
- line_outs_monitor
  - 默认将播放流发送到模拟输出
- enable_monitor
  - 默认启用通道 63/64 的模拟输出
详情请参阅 `hdspm.rst`

### 模块 snd-ice1712
------------------

此模块用于基于 Envy24（ICE1712）的 PCI 声卡
- MidiMan M Audio Delta 1010
- MidiMan M Audio Delta 1010LT
- MidiMan M Audio Delta DiO 2496
- MidiMan M Audio Delta 66
- MidiMan M Audio Delta 44
- MidiMan M Audio Delta 410
- MidiMan M Audio Audiophile 2496
- TerraTec EWS 88MT
- TerraTec EWS 88D
- TerraTec EWX 24/96
- TerraTec DMX 6Fire
- TerraTec Phase 88
- Hoontech SoundTrack DSP 24
- Hoontech SoundTrack DSP 24 Value
- Hoontech SoundTrack DSP 24 Media 7.1
- Event Electronics, EZ8
- Digigram VX442
- Lionstracs, Mediastaton
- Terrasoniq TS 88

- model
  - 使用指定的板卡型号，可选的型号包括：
    - delta1010, dio2496, delta66, delta44, audiophile, delta410,
    - delta1010lt, vx442, ewx2496, ews88mt, ews88mt_new, ews88d,
    - dmx6fire, dsp24, dsp24_value, dsp24_71, ez8,
    - phase88, mediastation
- omni
  - MidiMan M-Audio Delta44/66 的 Omni I/O 支持
- cs8427_timeout
  - CS8427 芯片（S/PDIF 接收器）的重置超时时间（毫秒），默认值为 500（0.5 秒）

此模块支持多张声卡和自动探测。
注意：并非所有基于 Envy24 的声卡都会使用消费部分（例如在 MidiMan Delta 系列中）
注意：通过读取 EEPROM 或 PCI SSID（如果 EEPROM 不可用）来检测支持的板卡。可以通过传递 `model` 模块选项来覆盖模型，以便在驱动程序配置不正确或需要测试其他类型时使用。

### 模块 snd-ice1724
------------------

此模块用于基于 Envy24HT（VT/ICE1724）和 Envy24PT（VT1720）的 PCI 声卡
* MidiMan M Audio Revolution 5.1
* MidiMan M Audio Revolution 7.1
* MidiMan M Audio Audiophile 192
* AMP Ltd AUDIO2000
* TerraTec Aureon 5.1 Sky
* TerraTec Aureon 7.1 Space
* TerraTec Aureon 7.1 Universe
* TerraTec Phase 22
* TerraTec Phase 28
* AudioTrak Prodigy 7.1
* AudioTrak Prodigy 7.1 LT
* AudioTrak Prodigy 7.1 XT
* AudioTrak Prodigy 7.1 HIFI
* AudioTrak Prodigy 7.1 HD2
* AudioTrak Prodigy 192
* Pontis MS300
* Albatron K8X800 Pro II 
* Chaintech ZNF3-150
* Chaintech ZNF3-250
* Chaintech 9CJS
* Chaintech AV-710
* Shuttle SN25P
* Onkyo SE-90PCI
* Onkyo SE-200PCI
* ESI Juli@
* ESI Maya44
* Hercules Fortissimo IV
* EGO-SYS WaveTerminal 192M

型号
使用给定的声卡型号，选项如下：
revo51, revo71, amp2000, prodigy71, prodigy71lt,
prodigy71xt, prodigy71hifi, prodigyhd2, prodigy192,
juli, aureon51, aureon71, universe, ap192, k8x800,
phase22, phase28, ms300, av710, se200pci, se90pci,
fortissimo4, sn25p, WT192M, maya44

此模块支持多张声卡并自动探测。
注意：通过读取EEPROM或PCI SSID（如果EEPROM不可用则读取SSID）来检测支持的声卡。您可以传递`model`模块选项来覆盖模型，以便在驱动程序配置不正确时或为了测试其他类型时使用。

snd-indigo 模块
-----------------

用于Echoaudio Indigo的模块。

此模块支持多张声卡。
该驱动程序需要内核中的固件加载器支持。

snd-indigodj 模块
-------------------

用于Echoaudio Indigo DJ的模块。

此模块支持多张声卡。
该驱动程序需要内核中的固件加载器支持。

snd-indigoio 模块
-------------------

用于Echoaudio Indigo IO的模块。

此模块支持多张声卡。
该驱动程序需要内核中的固件加载器支持。

snd-intel8x0 模块
-------------------

用于Intel及其兼容的AC'97主板
* Intel i810/810E, i815, i820, i830, i84x, MX440 ICH5, ICH6, ICH7,
  6300ESB, ESB2 
* SiS 7012 (SiS 735)
* NVidia NForce, NForce2, NForce3, MCP04, CK804 CK8, CK8S, MCP501
* AMD AMD768, AMD8111
* ALi m5455

ac97_clock
AC'97 编解码器时钟基频（0 = 自动检测）

ac97_quirk
AC'97 对奇怪硬件的变通方法；
请参阅下面的“AC97 Quirk Option”部分。
### buggy_irq
启用某些主板上中断错误的解决方案（默认在 nForce 芯片上为开启，其他情况下为关闭）

### buggy_semaphore
启用硬件上信号量错误的解决方案（例如一些 ASUS 笔记本电脑）（默认关闭）

### spdif_aclink
使用 AC-link 的 S/PDIF 而不是直接从控制器芯片连接（0 = 关闭，1 = 开启，-1 = 默认）

此模块支持一个芯片并自动探测

注意：最新驱动支持自动检测芯片时钟。如果您仍然遇到播放过快的问题，请通过模块选项 `ac97_clock=41194` 明确指定时钟。

此驱动不支持游戏杆/MIDI 端口。如果您的主板上有这些设备，请分别使用 ns558 或 snd-mpu401 模块。

支持电源管理

### Module snd-intel8x0m
--------------------

Intel ICH (i8x0) 芯片组 MC97 调制解调器模块
* Intel i810/810E, i815, i820, i830, i84x, MX440 ICH5, ICH6, ICH7
* SiS 7013 (SiS 735)
* NVidia NForce, NForce2, NForce2s, NForce3
* AMD AMD8111
* ALi m5455

### ac97_clock
AC'97 编码器时钟基（0 = 自动检测）

此模块支持一个卡并自动探测

注意：此模块的默认索引值为 -2，即第一个插槽被排除在外。

支持电源管理

### Module snd-interwave
--------------------

Gravis UltraSound PnP、Dynasonic 3-D/Pro、STB Sound Rage 32 及其他基于 AMD InterWave (tm) 芯片的声音卡模块
joystick_dac  
    0 到 31，（0.59V-4.52V 或 0.389V-2.98V）  
midi  
    1 = 启用 MIDI UART，0 = 禁用 MIDI UART（默认）  
pcm_voices  
    为合成器预留的 PCM 声道数（默认 2）  
effect  
    1 = 启用 InterWave 效果（默认 0）；需要 8 个声道  
isapnp  
    ISA 即插即用检测 - 0 = 禁用，1 = 启用（默认）

当 `isapnp=0` 时，以下选项可用：  
port  
    InterWave 芯片的端口号（0x210、0x220、0x230、0x240、0x250、0x260）  
irq  
    InterWave 芯片的 IRQ 号（3、5、9、11、12、15）  
dma1  
    InterWave 芯片的 DMA 号（0、1、3、5、6、7）  
dma2  
    InterWave 芯片的 DMA 号（0、1、3、5、6、7、-1=禁用）

此模块支持多张声卡、自动探测和 ISA 即插即用  
Module snd-interwave-stb  
------------------------  

UltraSound 32-Pro 的模块（Compaq 使用的 STB 声卡）和其他基于 AMD InterWave™ 芯片的声卡，配备 TEA6330T 电路以扩展控制低音、高音和主音量  
joystick_dac  
    0 到 31，（0.59V-4.52V 或 0.389V-2.98V）  
midi  
    1 = 启用 MIDI UART，0 = 禁用 MIDI UART（默认）  
pcm_voices  
    为合成器预留的 PCM 声道数（默认 2）  
effect  
    1 = 启用 InterWave 效果（默认 0）；需要 8 个声道  
isapnp  
    ISA 即插即用检测 - 0 = 禁用，1 = 启用（默认）

当 `isapnp=0` 时，以下选项可用：  
port  
    InterWave 芯片的端口号（0x210、0x220、0x230、0x240、0x250、0x260）  
port_tc  
    TEA6330T 芯片（I2C 总线）的端口号（0x350、0x360、0x370、0x380）  
irq  
    InterWave 芯片的 IRQ 号（3、5、9、11、12、15）  
dma1  
    InterWave 芯片的 DMA 号（0、1、3、5、6、7）  
dma2  
    InterWave 芯片的 DMA 号（0、1、3、5、6、7、-1=禁用）

此模块支持多张声卡、自动探测和 ISA 即插即用  
Module snd-jazz16  
-------------------  

Media Vision Jazz16 芯片组的模块。该芯片组由三个芯片组成：MVD1216 + MVA416 + MVA514  
port  
    SB DSP 芯片的端口号（0x210、0x220、0x230、0x240、0x250、0x260）  
irq  
    SB DSP 芯片的 IRQ 号（3、5、7、9、10、15）  
dma8  
    SB DSP 芯片的 DMA 号（1、3）  
dma16  
    SB DSP 芯片的 DMA 号（5、7）  
mpu_port  
    MPU-401 端口号（0x300、0x310、0x320、0x330）  
mpu_irq  
    MPU-401 IRQ 号（2、3、5、7）

此模块支持多张声卡  
Module snd-korg1212  
-------------------  

Korg 1212 IO PCI 卡的模块

此模块支持多张声卡  
Module snd-layla20  
------------------  

Echoaudio Layla20 的模块

此模块支持多张声卡  
驱动程序需要内核中的固件加载器支持  
Module snd-layla24  
------------------  

Echoaudio Layla24 的模块

此模块支持多张声卡  
驱动程序需要内核中的固件加载器支持
模块 snd-lola
---------------
用于 Digigram Lola PCI-e 板卡的模块

此模块支持多张卡

模块 snd-lx6464es
-------------------
用于 Digigram LX6464ES 板卡的模块

此模块支持多张卡

模块 snd-maestro3
-------------------
用于 Allegro/Maestro3 芯片的模块

external_amp
    启用外部放大器（默认已启用）
amp_gpio
    外部放大器的 GPIO 引脚编号（0-15）或 -1 使用默认引脚（Allegro 为 8，其他为 1）

此模块支持自动探测和多个芯片
注意：放大器的绑定依赖于硬件
如果所有通道都未静音但仍然没有声音，请尝试通过 amp_gpio 选项指定其他 GPIO 连接。
例如，松下笔记本可能需要 `amp_gpio=0x0d` 选项
支持电源管理

模块 snd-mia
---------------
用于 Echoaudio Mia 的模块

此模块支持多张卡
驱动程序需要内核上的固件加载器支持

模块 snd-miro
---------------
用于 Miro 声卡：miroSOUND PCM 1 pro, miroSOUND PCM 12, miroSOUND PCM 20 Radio

port
    端口号（0x530, 0x604, 0xe80, 0xf40）
irq
    中断请求号（5, 7, 9, 10, 11）
dma1
    第一个 DMA 号（0, 1, 3）
dma2
    第二个 DMA 号（0, 1）
mpu_port
    MPU-401 端口号（0x300, 0x310, 0x320, 0x330）
mpu_irq
    MPU-401 中断请求号（5, 7, 9, 10）
fm_port
    FM 端口号（0x388）
wss
    启用 WSS 模式
ide
    启用板载 IDE 支持

模块 snd-mixart
-----------------
用于 Digigram miXart8 声卡的模块
此模块支持多张声卡
注意：一个miXart8板子将被表示为4张ALSA声卡。
详情请参阅Documentation/sound/cards/mixart.rst
当驱动程序作为模块编译并且支持热插拔固件时，固件数据会通过热插拔自动加载。
请在alsa-firmware包中安装必要的固件文件。
如果没有可用的热插拔固件加载器，则需要通过alsa-tools包中的mixartloader工具手动加载固件。

### Module snd-mona
--------------

Echoaudio Mona的模块

此模块支持多张声卡
该驱动程序需要内核上的固件加载器支持

### Module snd-mpu401
--------------

MPU-401 UART设备的模块

- port
  端口号或-1（禁用）
- irq
  中断请求号或-1（禁用）
- pnp
  即插即用检测 - 0 = 禁用，1 = 启用（默认）

此模块支持多个设备和即插即用功能
### 模块 snd-msnd-classic
----------------------

此模块适用于 Turtle Beach MultiSound Classic、Tahiti 或 Monterey 声卡。

- io
    - MultiSound Classic 卡的端口号
- irq
    - MultiSound Classic 卡的中断请求号
- mem
    - 内存地址（0xb0000, 0xc8000, 0xd0000, 0xd8000, 0xe0000 或 0xe8000）
- write_ndelay
    - 启用写入 ndelay（默认 = 1）
- calibrate_signal
    - 校准信号（默认 = 0）
- isapnp
    - ISA 即插即用检测 - 0 = 禁用，1 = 启用（默认）
- digital
    - 数字子板存在（默认 = 0）
- cfg
    - 配置端口（0x250, 0x260 或 0x270），默认 = 即插即用
- reset
    - 重置所有设备
- mpu_io
    - MPU401 I/O 端口
- mpu_irq
    - MPU401 中断请求号
- ide_io0
    - IDE 端口 0
- ide_io1
    - IDE 端口 1
- ide_irq
    - IDE 中断请求号
- joystick_io
    - 游戏杆 I/O 端口

该驱动程序需要固件文件 `turtlebeach/msndinit.bin` 和 `turtlebeach/msndperm.bin` 存放在正确的固件目录中。有关此驱动程序的重要信息，请参阅 `Documentation/sound/cards/multisound.sh`。请注意，该驱动程序已停止支持，但可以在 https://www.turtlebeach.com 查看 Voyetra Turtle Beach 的知识库条目。

### 模块 snd-msnd-pinnacle
------------------------

此模块适用于 Turtle Beach MultiSound Pinnacle/Fiji 声卡。

- io
    - Pinnacle/Fiji 卡的端口号
- irq
    - Pinnacle/Fiji 卡的中断请求号
- mem
    - 内存地址（0xb0000, 0xc8000, 0xd0000, 0xd8000, 0xe0000 或 0xe8000）
- write_ndelay
    - 启用写入 ndelay（默认 = 1）
- calibrate_signal
    - 校准信号（默认 = 0）
- isapnp
    - ISA 即插即用检测 - 0 = 禁用，1 = 启用（默认）

该驱动程序需要固件文件 `turtlebeach/pndspini.bin` 和 `turtlebeach/pndsperm.bin` 存放在正确的固件目录中。

### 模块 snd-mtpav
-------------------

此模块适用于 MOTU MidiTimePiece AV 多端口 MIDI（通过并行端口）。

- port
    - MTPAV 的 I/O 端口号（0x378, 0x278，默认 = 0x378）
- irq
    - MTPAV 的中断请求号（7, 5，默认 = 7）
- hwports
    - 支持的硬件端口数量，默认 = 8

此模块仅支持一张卡，并且没有启用选项。

### 模块 snd-mts64
-------------------

此模块适用于 Ego Systems (ESI) Miditerminal 4140。

- 此模块支持多个设备
- 需要并口（`CONFIG_PARPORT`）

### 模块 snd-nm256
-------------------

此模块适用于 NeoMagic NM256AV/ZX 芯片。

- playback_bufsize
    - 最大播放帧大小（4-128kB）
- capture_bufsize
    - 最大捕获帧大小（4-128kB）
- force_ac97
    - 0 或 1（默认禁用）
- buffer_top
    - 指定缓冲区顶部地址
- use_cache
    - 0 或 1（默认禁用）
- vaio_hack
    - 等同于 buffer_top=0x25a800
- reset_workaround
    - 启用某些笔记本电脑的 AC97 重置规避方法
- reset_workaround2
    - 启用其他某些笔记本电脑的扩展 AC97 重置规避方法

此模块支持一个芯片并自动探测。
电源管理已得到支持。
注意：在某些笔记本电脑上，缓冲区地址无法自动检测，或者会在初始化过程中导致死机。
在这种情况下，请通过 `buffer_top` 选项显式指定缓冲区顶部地址。
例如，
Sony F250: buffer_top=0x25a800
Sony F270: buffer_top=0x272800
驱动程序仅支持 AC97 编码解码器。即使未检测到 AC97，也可以强制初始化/使用 AC97。在这种情况下，使用 `force_ac97=1` 选项——但不保证是否有效！

注意：NM256 芯片可以内部连接非 AC97 编码解码器。此驱动程序仅支持 AC97 编码解码器，并且无法在其他（可能是 CS423x 或 OPL3SAx）芯片的机器上工作，即使这些设备在 lspci 中被检测到。在这种情况下，请尝试其他驱动程序，例如 snd-cs4232 或 snd-opl3sa2。有些有 ISA-PnP 支持，有些没有 ISA-PnP 支持。如果没有 ISA-PnP，需要指定 `isapnp=0` 和正确的硬件参数。
注意：某些笔记本电脑需要一个针对 AC97 重置的变通方法。对于已知的硬件如 Dell Latitude LS 和 Sony PCG-F305，此变通方法会自动启用。对于其他出现严重冻结问题的笔记本电脑，可以尝试使用 `reset_workaround=1` 选项。
注意：Dell Latitude CSx 笔记本电脑在 AC97 重置方面还有另一个问题。在这些笔记本电脑上，默认启用了 `reset_workaround2` 选项。如果之前的 `reset_workaround` 选项无效，这个选项值得一试。
注意：此驱动程序确实很差。它是从 OSS 驱动程序移植过来的，而 OSS 驱动程序是通过黑魔法逆向工程的结果。如果驱动程序在 X-server 之后加载，则编解码器的检测将会失败。您可能能够强制加载模块，但这可能会导致死机。因此，如果您遇到此类问题，请确保在启动 X 之前加载此模块。

snd-opl3sa2 模块
------------------

适用于 Yamaha OPL3-SA2/SA3 声卡的模块

isapnp
    ISA PnP 检测 - 0 = 禁用，1 = 启用（默认）

使用 `isapnp=0` 时，以下选项可用：

port
    OPL3-SA 芯片的控制端口编号（0x370）
sb_port
    OPL3-SA 芯片的 SB 端口编号（0x220,0x240）
wss_port
    OPL3-SA 芯片的 WSS 端口编号（0x530,0xe80,0xf40,0x604）
midi_port
    MPU-401 UART 的端口编号（0x300,0x330），-1 = 禁用
fm_port
    OPL3-SA 芯片的 FM 端口编号（0x388），-1 = 禁用
irq
    OPL3-SA 芯片的 IRQ 编号（5,7,9,10）
dma1
    Yamaha OPL3-SA 芯片的第一个 DMA 编号（0,1,3）
dma2
    Yamaha OPL3-SA 芯片的第二个 DMA 编号（0,1,3），-1 = 禁用

此模块支持多张声卡和 ISA PnP。如果不使用 ISA PnP，则不支持自动探测，因此必须指定所有端口！

电源管理已得到支持。
### 模块 snd-opti92x-ad1848
-------------------------

基于 OPTi 82c92x 和 Analog Devices AD1848 芯片的声卡模块。  
该模块也支持 OAK Mozart 声卡。  
isapnp  
    ISA PnP 检测 - 0 = 禁用，1 = 启用（默认）

使用 `isapnp=0` 时，以下选项可用：

port  
    WSS 芯片的端口号（0x530、0xe80、0xf40、0x604）  
mpu_port  
    MPU-401 UART 的端口号（0x300、0x310、0x320、0x330）  
fm_port  
    OPL3 设备的端口号（0x388）  
irq  
    WSS 芯片的 IRQ 号（5、7、9、10、11）  
mpu_irq  
    MPU-401 UART 的 IRQ 号（5、7、9、10）  
dma1  
    WSS 芯片的第一个 DMA 号（0、1、3）

此模块仅支持一张卡，并且支持自动探测和 PnP。

### 模块 snd-opti92x-cs4231
-------------------------

基于 OPTi 82c92x 和 Crystal CS4231 芯片的声卡模块。  
isapnp  
    ISA PnP 检测 - 0 = 禁用，1 = 启用（默认）

使用 `isapnp=0` 时，以下选项可用：

port  
    WSS 芯片的端口号（0x530、0xe80、0xf40、0x604）  
mpu_port  
    MPU-401 UART 的端口号（0x300、0x310、0x320、0x330）  
fm_port  
    OPL3 设备的端口号（0x388）  
irq  
    WSS 芯片的 IRQ 号（5、7、9、10、11）  
mpu_irq  
    MPU-401 UART 的 IRQ 号（5、7、9、10）  
dma1  
    WSS 芯片的第一个 DMA 号（0、1、3）  
dma2  
    WSS 芯片的第二个 DMA 号（0、1、3）

此模块仅支持一张卡，并且支持自动探测和 PnP。

### 模块 snd-opti93x
------------------

基于 OPTi 82c93x 芯片的声卡模块。  
isapnp  
    ISA PnP 检测 - 0 = 禁用，1 = 启用（默认）

使用 `isapnp=0` 时，以下选项可用：

port  
    WSS 芯片的端口号（0x530、0xe80、0xf40、0x604）  
mpu_port  
    MPU-401 UART 的端口号（0x300、0x310、0x320、0x330）  
fm_port  
    OPL3 设备的端口号（0x388）  
irq  
    WSS 芯片的 IRQ 号（5、7、9、10、11）  
mpu_irq  
    MPU-401 UART 的 IRQ 号（5、7、9、10）  
dma1  
    WSS 芯片的第一个 DMA 号（0、1、3）  
dma2  
    WSS 芯片的第二个 DMA 号（0、1、3）

此模块仅支持一张卡，并且支持自动探测和 PnP。

### 模块 snd-oxygen
-----------------

基于 C-Media CMI8786/8787/8788 芯片的声卡模块：

* Asound A-8788
* Asus Xonar DG/DGX
* AuzenTech X-Meridian
* AuzenTech X-Meridian 2G
* Bgears b-Enspirer
* Club3D Theatron DTS
* HT-Omega Claro (plus)
* HT-Omega Claro halo (XT)
* Kuroutoshikou CMI8787-HG2PCI
* Razer Barracuda AC-1
* Sondigo Inferno
* TempoTec HiFier Fantasia
* TempoTec HiFier Serenade

此模块支持自动探测和多张卡。

### 模块 snd-pcsp
---------------

内部 PC 音箱模块。  
nopcm  
    禁用 PC 音箱的 PCM 音效。只保留蜂鸣音。
nforce_wa  
启用 NForce 芯片组的解决方案。音质可能较差  
此模块支持系统蜂鸣声、某种 PCM 播放，甚至一些混音器控制  

Module snd-pcxhr  
----------------  
Digigram PCXHR 板卡模块  

此模块支持多张卡  

Module snd-portman2x4  
---------------------  
Midiman Portman 2x4 并口 MIDI 接口模块  

此模块支持多张卡  

Module snd-powermac（仅限于 ppc）  
---------------------------------  
适用于 PowerMac、iMac 和 iBook 的板载声卡模块  

enable_beep  
使用 PCM 启用蜂鸣声（默认已启用）  

此模块支持自动探测芯片  
注意：该驱动程序可能存在字节顺序问题  
支持电源管理  

Module snd-pxa2xx-ac97（仅限于 arm）  
------------------------------------  
适用于 Intel PXA2xx 芯片的 AC97 驱动  

仅适用于 ARM 架构  
支持电源管理  

Module snd-riptide  
------------------  
Conexant Riptide 芯片模块  

joystick_port  
游戏杆端口编号（默认：0x200）  
mpu_port  
MPU401 端口编号（默认：0x330）  
opl3_port  
OPL3 端口编号（默认：0x388）  

此模块支持多张卡
驱动程序需要内核上的固件加载器支持  
您需要将固件文件 `riptide.hex` 安装到标准固件路径（例如 `/lib/firmware`）

### 模块 snd-rme32
---

适用于 RME Digi32、Digi32 Pro 和 Digi32/8（Sek'd Prodif32、Prodif96 和 Prodif Gold）声卡的模块  
此模块支持多张卡

### 模块 snd-rme96
---

适用于 RME Digi96、Digi96/8 和 Digi96/8 PRO/PAD/PST 声卡的模块  
此模块支持多张卡

### 模块 snd-rme9652
---

适用于 RME Digi9652（Hammerfall、Hammerfall-Light）声卡的模块  
`precise_ptr`
    启用精确指针（不可靠）。默认值 = 0

此模块支持多张卡  
注意：snd-page-alloc 模块执行了先前由 snd-hammerfall-mem 模块完成的工作。当检测到任何 RME9652 卡时，它会提前分配缓冲区。为了确保缓冲区分配成功，请在启动序列的早期加载 snd-page-alloc 模块。请参阅“早期缓冲区分配”部分

### 模块 snd-sa11xx-uda1341（仅限 ARM）
---

适用于 Compaq iPAQ H3600 声卡上的 Philips UDA1341TS 的模块
模块仅支持一张声卡  
模块没有启用和索引选项  
支持电源管理  
模块 snd-sb8
--------------

8 位 SoundBlaster 声卡模块：SoundBlaster 1.0，SoundBlaster 2.0，SoundBlaster Pro

port
    SB DSP 芯片的端口号（0x220、0x240、0x260）
irq
    SB DSP 芯片的中断请求号（IRQ）（5、7、9、10）
dma8
    SB DSP 芯片的 8 位直接内存访问（DMA）号（1、3）

此模块支持多张声卡和自动探测  
支持电源管理  
模块 snd-sb16 和 snd-sbawe
-----------------------------

16 位 SoundBlaster 声卡模块：SoundBlaster 16（即插即用），SoundBlaster AWE 32（即插即用），SoundBlaster AWE 64 即插即用

mic_agc
    麦克风自动增益控制 - 0 = 禁用，1 = 启用（默认）
csp
    ASP/CSP 芯片支持 - 0 = 禁用（默认），1 = 启用
isapnp
    ISA 即插即用检测 - 0 = 禁用，1 = 启用（默认）

当 isapnp=0 时，以下选项可用：

port
    SB DSP 4.x 芯片的端口号（0x220、0x240、0x260）
mpu_port
    MPU-401 UART 的端口号（0x300、0x330），-1 = 禁用
awe_port
    EMU8000 合成器的基本端口号（0x620、0x640、0x660）（仅适用于 snd-sbawe 模块）
irq
    SB DSP 4.x 芯片的中断请求号（IRQ）（5、7、9、10）
dma8
    SB DSP 4.x 芯片的 8 位直接内存访问（DMA）号（0、1、3）
dma16
    SB DSP 4.x 芯片的 16 位直接内存访问（DMA）号（5、6、7）

此模块支持多张声卡、自动探测和 ISA 即插即用  
注意：要在 16 位半双工模式下使用 Vibra16X 声卡，必须通过设置 dma16 = -1 来禁用 16 位 DMA 参数  
此外，所有 Sound Blaster 16 类型的声卡都可以通过禁用其 16 位 DMA 通道来在 8 位 DMA 通道上以 16 位半双工模式运行  
支持电源管理  
模块 snd-sc6000
-----------------

Gallant SC-6000 声卡及其后续型号 SC-6600 和 SC-7000 的模块
端口
    端口号（0x220 或 0x240）
mss_port
    MSS 端口号（0x530 或 0xe80）
irq
    IRQ 号（5、7、9、10、11）
mpu_irq
    MPU-401 IRQ 号（5、7、9、10），0 - 不使用 MPU-401 IRQ
dma
    DMA 号（1、3、0）
joystick
    启用游戏端口 - 0 = 禁用（默认），1 = 启用

此模块支持多张卡
此卡也称为 Audio Excel DSP 16 或 Zoltrix AV302
snd-sscape 模块
-----------------

适用于 ENSONIQ SoundScape 卡的模块
port
    端口号（即插即用设置）
wss_port
    WSS 端口号（即插即用设置）
irq
    IRQ 号（即插即用设置）
mpu_irq
    MPU-401 IRQ 号（即插即用设置）
dma
    DMA 号（即插即用设置）
dma2
    第二个 DMA 号（即插即用设置，-1 表示禁用）
joystick
    启用游戏端口 - 0 = 禁用（默认），1 = 启用

此模块支持多张卡
驱动程序需要内核上的固件加载器支持
snd-sun-amd7930 模块（仅限于 sparc）
--------------------------------------

适用于 Sparc 上的 AMD7930 音频芯片的模块
此模块支持多张卡
snd-sun-cs4231 模块（仅限于 sparc）
-------------------------------------

适用于 Sparc 上的 CS4231 音频芯片的模块
此模块支持多张卡
snd-sun-dbri 模块（仅限于 sparc）
-----------------------------------

适用于 Sparc 上的 DBRI 音频芯片的模块
此模块支持多张声卡

Module snd-wavefront
--------------------

此模块用于Turtle Beach Maui、Tropez和Tropez+声卡

use_cs4232_midi
    使用CS4232 MPU-401接口（位于计算机内部，无法直接访问）

isapnp
    ISA PnP检测 - 0 = 禁用, 1 = 启用（默认）

当isapnp=0时，以下选项可用：

cs4232_pcm_port
    CS4232 PCM接口的端口号

cs4232_pcm_irq
    CS4232 PCM接口的IRQ号（5, 7, 9, 11, 12, 15）

cs4232_mpu_port
    CS4232 MPU-401接口的端口号

cs4232_mpu_irq
    CS4232 MPU-401接口的IRQ号（9, 11, 12, 15）

ics2115_port
    ICS2115的端口号

ics2115_irq
    ICS2115的IRQ号

fm_port
    FM OPL-3端口号

dma1
    CS4232 PCM接口的DMA1号

dma2
    CS4232 PCM接口的DMA2号

以下是wavefront_synth功能的相关选项：

wf_raw
    假设我们需要引导操作系统（默认：否）；
    如果是，则在加载驱动程序时，忽略声卡的状态，并重置声卡并加载固件

fx_raw
    假设FX处理需要帮助（默认：是）；
    如果否，则在加载驱动程序时，保持FX处理器当前的状态。
    默认情况下，会下载微程序及相关系数以设置其为“默认”操作状态，无论该状态为何。
### debug_default
调试参数用于卡片初始化

### wait_usecs
等待时间（不休眠），单位为微秒（默认：150）；
根据我的有限实验，这个神奇的数字似乎提供了相当理想的吞吐量。
如果你想尝试调整它以找到一个更好的值，请随意尝试。记住，我们的目标是找到一个能够使我们尽可能多地忙等WaveFront命令的数值，但又不至于太大以至于占用整个CPU。
具体来说，使用这个数值，在大约134,000次状态等待中，只有大约250次会导致休眠。

### sleep_interval
等待回复时休眠的时间（默认：100）

### sleep_tries
在一次等待过程中尝试休眠的次数（默认：50）

### ospath
处理过的ICS2115操作系统固件路径名（默认：wavefront.os）；
在较新版本中，它是通过固件加载器框架处理的，因此必须安装在正确的路径下，通常是 /lib/firmware。

### reset_time
重置生效所需等待的时间（默认：2）

### ramcheck_time
RAM测试所需等待的时间（秒）（默认：20）

### osrun_time
等待ICS2115操作系统启动所需的时间（秒）（默认：10）

### 模块 snd-sonicvibes
---------------------
S3 SonicVibes PCI声卡模块
* PINE Schubert 32 PCI

#### reverb
回声启用 - 1 = 启用，0 = 禁用（默认）；
声卡必须有板载SRAM才能启用此功能。

#### mge
麦克风增益启用 - 1 = 启用，0 = 禁用（默认）

此模块支持多张卡片和自动探测。

### 模块 snd-serial-u16550
------------------------
UART16550A串行MIDI端口模块

#### port
UART16550A芯片的端口号

#### irq
UART16550A芯片的中断请求号，-1 = 轮询模式

#### speed
波特率（9600, 19200, 38400, 57600, 115200），默认为38400

#### base
波特率除数的基础值（57600, 115200, 230400, 460800），默认为115200

#### outs
串行端口中MIDI端口的数量（1-4），默认为1

#### adaptor
适配器类型
0 = Soundcanvas, 1 = MS-124T, 2 = MS-124W S/A, 3 = MS-124W M/B, 4 = Generic

此模块支持多张卡片。此模块不支持自动探测，因此必须指定主端口！其他选项是可选的。
### 模块 snd-trident
------------------

此模块支持 Trident 4DWave DX/NX 声卡：
* 最佳联盟 Miss Melody 4DWave PCI
* HIS 4DWave PCI
* Warpspeed ONSpeed 4DWave PCI
* AzTech PCI 64-Q3D
* Addonics SV 750
* CHIC True Sound 4Dwave
* Shark Predator4D-PCI
* Jaton SonicWave 4D
* SiS SI7018 PCI 音频
* Hoontech SoundTrack Digital 4DWave NX

pcm_channels
    为 PCM 预留的最大声道数（音轨）
wavetable_size
    最大波表大小，单位为 kB（4-？kb）

此模块支持多张声卡和自动探测功能
支持电源管理

### 模块 snd-ua101
----------------

此模块支持 Edirol UA-101/UA-1000 音频/MIDI 接口
此模块支持多个设备、自动探测和热插拔

### 模块 snd-usb-audio
--------------------

此模块支持 USB 音频和 USB MIDI 设备
vid
    设备的供应商 ID（可选）
pid
    设备的产品 ID（可选）
nrpacks
    每个 URB 的最大包数（默认：8）
device_setup
    设备特定的魔法数字（可选）；影响取决于设备
    默认值：0x0000
ignore_ctl_error
    忽略与混音器接口相关的任何 USB 控制器错误（默认：否）
autoclock
    启用 UAC2 设备的自动时钟选择（默认：是）
quirk_alias
    异常别名列表，传递类似于 ``0123abcd:5678beef`` 的字符串，将设备 5678:beef 的现有异常应用到新设备 0123:abcd 上
implicit_fb
    应用通用的隐式反馈同步模式。当设置此选项且播放流的同步模式为 ASYNC 时，驱动程序会尝试将相邻的 ASYNC 采集流作为隐式反馈源。这等同于异常标志位 17
use_vmalloc
    使用 vmalloc() 分配 PCM 缓冲区（默认：是）
对于具有不一致内存架构（如 ARM 或 MIPS）的系统，mmap 访问可能会导致与 vmalloc 分配的缓冲区结果不一致。如果在这些架构上使用 mmap，请关闭此选项，以便分配和使用 DMA 一致性缓冲区
### 延迟注册（delayed_register）

此选项适用于具有多个USB接口定义的多流设备。驱动程序可能会多次调用注册（每个接口一次），这可能导致设备枚举不足。

此选项接收一个字符串数组，您可以传递类似`0123abcd:4`这样的`ID:INTERFACE`格式来对指定设备执行延迟注册。例如，当探测到USB设备`0123:abcd`时，驱动程序会等待直到USB接口4被探测完成再进行注册。

对于此类设备，驱动程序会打印一条消息，如“找到延迟注册设备分配：1234abcd:04”，以便用户注意到该需求。

### 特殊标志（quirk_flags）

包含针对各种特定设备的修复措施的位标志。

应用于相应的卡索引：

- 位0：跳过读取采样率
- 位1：创建媒体控制器API条目
- 位2：允许在传输过程中音频子槽对齐
- 位3：向传输中添加长度指定符
- 位4：在实现反馈模式下从第一个开始播放流
- 位5：跳过时钟选择器设置
- 位6：忽略时钟源搜索中的错误
- 位7：指示基于ITF-USB DSD的DAC
- 位8：在每次控制消息处理时增加20毫秒的延迟
- 位9：在每次控制消息处理时增加1-2毫秒的延迟
- 位10：在每次控制消息处理时增加5-6毫秒的延迟
- 位11：在每次接口设置时增加50毫秒的延迟
- 位12：在探测时进行采样率验证
- 位13：禁用运行时PM自动挂起
- 位14：忽略混音器访问中的错误
- 位15：支持通用DSD原始U32_BE格式
- 位16：首次设置接口时像UAC1一样
- 位17：应用通用隐式反馈同步模式
- 位18：不应用隐式反馈同步模式

### 模块支持

此模块支持多个设备、自动探测和热插拔。

注意：`nrpacks`参数可以通过sysfs动态修改。不要将值设置超过20。通过sysfs修改没有合理性检查。

注意：如果在访问混音器元素（如URB错误-22）时遇到错误，`ignore_ctl_error=1`可能会有所帮助。这种情况发生在一些有缺陷的USB设备或控制器上。此修复措施对应于`quirk_flags`位14。

注意：`quirk_alias`选项仅用于测试/开发目的。
如果你希望获得适当的支持，请联系上游开发者在驱动代码中静态添加匹配的特殊处理。
对于“quirk_flags”也是如此。如果某个设备已知需要特定的变通方法，请向上游报告。
模块 snd-usb-caiaq
--------------------

适用于 caiaq UB 音频接口的模块，

* Native Instruments RigKontrol2
* Native Instruments Kore Controller
* Native Instruments Audio Kontrol 1
* Native Instruments Audio 8 DJ

此模块支持多个设备、自动探测和热插拔。
模块 snd-usb-usx2y
--------------------

适用于 Tascam USB US-122、US-224 和 US-428 设备的模块。
此模块支持多个设备、自动探测和热插拔。
注意：你需要通过 alsa-tools 和 alsa-firmware 包中包含的 `usx2yloader` 工具加载固件。
模块 snd-via82xx
------------------

适用于基于 VIA 82C686A/686B、8233、8233A、8233C、8235、8237（南桥）的 AC'97 主板的模块。

mpu_port
    0x300, 0x310, 0x320, 0x330，否则请在 BIOS 设置中获取
    [仅限 VIA686A/686B]

joystick
    启用游戏杆（默认关闭）[仅限 VIA686A/686B]

ac97_clock
    AC'97 编码器时钟基频（默认 48000Hz）

dxs_support
    支持 DXS 通道，0 = 自动（默认），1 = 启用，2 = 禁用，
    3 = 仅 48k，4 = 不使用 VRA，5 = 启用任何采样率并在不同通道上使用不同的采样率
    [仅限 VIA8233/C, 8235, 8237]

ac97_quirk
    AC'97 对奇怪硬件的变通方法；
    请参阅下面的 `AC97 Quirk Option`_ 部分

此模块支持一个芯片和自动探测。
注意：在某些 SMP 主板（如 MSI 694D）上，中断可能无法正确生成。在这种情况下，请尝试在 BIOS 中将 SMP（或 MPS）版本设置为 1.1 而不是默认值 1.4。然后中断号将被分配到 15 以下。你也可能需要升级你的 BIOS。
注：VIA8233/5/7（而非VIA8233A）可以支持DXS（直接声音）通道作为第一个PCM。在这些通道上，最多可以同时播放4个流，并且控制器可以为每个通道分别进行采样率转换。

默认情况下（`dxs_support = 0`），选择48kHz的固定采样率，除非已知设备由于BIOS的错误，在某些主板上除了48kHz外输出通常会有噪声。

请尝试一次`dxs_support=5`，如果其他采样率（例如MP3播放的44.1kHz）可以工作，请告知我们PCI子系统的供应商/设备ID（`lspci -nv`的输出）。

如果`dxs_support=5`不起作用，请尝试`dxs_support=4`；如果仍然不起作用，请尝试`dxs_support=1`。（`dxs_support=1`通常是针对旧主板的。正确的实现板应该能够使用4或5。）如果仍然不起作用并且默认设置可以正常工作，则`dxs_support=3`是正确选择。如果默认设置完全不起作用，请尝试`dxs_support=2`以禁用DXS通道。

在任何情况下，请告知我们结果和子系统的供应商/设备ID。参见下面的“链接和地址”。

注：对于VIA823x上的MPU401，请另外使用snd-mpu401驱动程序。mpu_port选项仅适用于VIA686芯片。

支持电源管理功能

snd-via82xx-modem模块
------------------------

此模块用于VIA82xx AC97调制解调器

ac97_clock
    AC'97编解码器时钟基准（默认48000Hz）

此模块支持一个卡并自动探测。

注：此模块的默认索引值为-2，即排除第一个插槽。

支持电源管理功能。
### 模块 snd-virmidi
------------------

**虚拟 rawmidi 设备模块**
此模块创建与相应的 ALSA 序列器端口通信的虚拟 rawmidi 设备。

**midi_devs**
    MIDI 设备数量（1-4，默认为 4）

此模块支持多张声卡。

### 模块 snd-virtuoso
-------------------

**基于 Asus AV66/AV100/AV200 芯片的声卡模块**
该模块适用于以下型号：Xonar D1、DX、D2、D2X、DS、DSX、Essence ST（Deluxe）、Essence STX（II）、HDAV1.3（Deluxe）和 HDAV1.3 Slim。

此模块支持自动探测和多张声卡。

### 模块 snd-vx222
------------------

**Digigram VX-Pocket VX222、V222 v2 和 Mic 卡模块**

**mic**
    在 V222 Mic 上启用麦克风（暂未实现）

**ibl**
    捕获 IBL 大小（默认 = 0，最小大小）

此模块支持多张声卡。当驱动程序作为模块编译并且支持热插拔固件时，固件数据会通过热插拔自动加载。请在 alsa-firmware 包中安装必要的固件文件。

如果没有可用的热插拔固件加载器，你需要通过 alsa-tools 包中的 vxloader 工具手动加载固件。为了自动调用 vxloader，请将以下内容添加到 `/etc/modprobe.d/alsa.conf` 文件中：

```
install snd-vx222 /sbin/modprobe --first-time -i snd-vx222\ 
    && /usr/bin/vxloader
```

对于 2.2/2.4 内核，在 `/etc/modules.conf` 中添加 `post-install /usr/bin/vxloader`。

IBL 大小定义了 PCM 的中断周期。较小的大小会导致较低的延迟，但也会增加 CPU 使用率。
大小通常对齐到126。默认情况下（=0），选择最小的大小。
可能的IBL值可以在/proc/asound/cardX/vx-status 文件中找到。
支持电源管理。
snd-vxpocket 模块
-------------------

此模块适用于Digigram VX-Pocket VX2 和 440 PCMCIA 卡。
ibl
    捕获IBL大小。（默认 = 0，最小大小）

此模块支持多张卡。仅当内核支持PCMCIA时，才会编译此模块。
在较旧的2.6.x内核中，要通过卡管理器激活驱动程序，需要设置/etc/pcmcia/vxpocket.conf。参见sound/pcmcia/vx/vxpocket.c。2.6.13 或更高版本的内核不再需要配置文件。
当驱动程序作为模块编译并且支持热插拔固件时，固件数据将通过热插拔自动加载。
请安装alsa-firmware 包中的必要固件文件。
如果没有可用的热插拔固件加载器，则需要使用alsa-tools 包中的vxloader 工具加载固件。
关于捕获IBL，请参阅snd-vx222模块的描述。
注意：自ALSA 1.0.10以来，snd-vxp440 驱动程序已合并到snd-vxpocket 驱动程序中。
电源管理受支持
模块 snd-ymfpci
-------------------

用于 Yamaha PCI 芯片（YMF72x，YMF74x 和 YMF75x）
mpu_port
    0x300, 0x330, 0x332, 0x334，默认为 0（禁用），
    1（仅自动检测 YMF744/754）
fm_port
    0x388, 0x398, 0x3a0, 0x3a8，默认为 0（禁用）
    1（仅自动检测 YMF744/754）
joystick_port
    0x201, 0x202, 0x204, 0x205，默认为 0（禁用），
    1（自动检测）
rear_switch
    启用共享后置/线路输入开关（布尔值）

此模块支持自动探测和多个芯片
电源管理受支持
模块 snd-pdaudiocf
--------------------

用于 Sound Core PDAudioCF 声卡
电源管理受支持
AC97 特殊选项
=================

ac97_quirk 选项用于启用/覆盖针对某些特定设备的 AC'97 控制器驱动（如 snd-intel8x0）中的变通方案。一些硬件在 Master 输出和耳机输出之间或环绕输出之间存在引脚互换的问题（这要归咎于不同版本的 AC'97 规范之间的混淆）。

驱动程序提供了对已知问题设备的自动检测功能，但有些设备可能未知或检测错误。在这种情况下，请通过此选项传递正确的值。
接受以下字符串：

default
    不覆盖默认设置
none
    禁用特殊处理
hp_only
    将 Master 和耳机控制绑定为单一控制
swap_hp
    互换耳机和主控
swap_surround
    互换主控和环绕控制
ad_sharing
    对于 AD1985，启用 OMS 位并使用耳机
alc_jack
    对于 ALC65x，启用插孔感应模式
inv_eapd
    反向实现 EAPD
mute_led
    绑定 EAPD 位以开启/关闭静音指示灯

为了保持向后兼容性，相应的整数值 -1、0、... 也接受。
例如，如果您的设备上“Master”音量控制没有效果，而只有“Headphone”有效，则应传递 ac97_quirk=hp_only 模块选项。
配置非 ISAPNP 卡
============================

当内核配置了 ISA-PnP 支持时，支持 ISAPNP 卡的模块将具有模块选项 `isapnp`。如果设置了此选项，则 *仅* 探测 ISA-PnP 设备。为了探测非 ISA-PnP 卡，您需要传递 `isapnp=0` 选项，并且还需要提供正确的 I/O 和 IRQ 配置。当内核没有配置 ISA-PnP 支持时，不会内置 isapnp 选项。

模块自动加载支持
==========================

通过定义模块别名，ALSA 驱动程序可以按需自动加载。对于 ALSA 原生设备，请求字符串为 `snd-card-%i`，其中 `%i` 是从零到七的声卡编号。为了自动加载 OSS 服务的 ALSA 驱动程序，定义字符串 `sound-slot-%i`，其中 `%i` 表示 OSS 的插槽编号，这对应于 ALSA 的声卡索引。通常，将其定义为相同的声卡模块。

下面是单个 emu10k1 声卡的示例配置：
```
----- /etc/modprobe.d/alsa.conf
alias snd-card-0 snd-emu10k1
alias sound-slot-0 snd-emu10k1
----- /etc/modprobe.d/alsa.conf
```

可自动加载的声卡数量取决于 snd 模块的模块选项 `cards_limit`。默认情况下，其值设置为 1。为了启用多个声卡的自动加载，请在此选项中指定声卡的数量。

当有多个声卡可用时，最好也通过模块选项指定每个声卡的索引号，以便保持声卡顺序的一致性。

下面是两个声卡的示例配置：
```
----- /etc/modprobe.d/alsa.conf
# ALSA 部分
options snd cards_limit=2
alias snd-card-0 snd-interwave
alias snd-card-1 snd-ens1371
options snd-interwave index=0
options snd-ens1371 index=1
# OSS/Free 部分
alias sound-slot-0 snd-interwave
alias sound-slot-1 snd-ens1371
----- /etc/modprobe.d/alsa.conf
```

在这个示例中，interwave 声卡始终作为第一张声卡（索引 0）加载，而 ens1371 作为第二张声卡（索引 1）。
替代（和新的）固定插槽分配的方法是使用snd模块的`slots`选项。在上面的例子中，可以如下指定：
::
    
    options snd slots=snd-interwave,snd-ens1371

这样，第一个插槽（#0）将为snd-interwave驱动保留，第二个插槽（#1）为snd-ens1371驱动保留。如果使用了slots选项，可以在每个驱动中省略索引选项（尽管只要它们不冲突，仍然可以同时使用）。
slots选项特别有助于避免可能的热插拔及由此产生的插槽冲突。例如，在上述情况下，前两个插槽已经预留。如果其他驱动程序（如snd-usb-audio）在snd-interwave或snd-ens1371之前加载，它将被分配到第三个或之后的插槽。
当模块名称以'!'开头时，该插槽将为除该名称之外的所有模块保留。例如，“slots=!snd-pcsp”将为除snd-pcsp之外的所有模块预留第一个插槽。

ALSA PCM设备到OSS设备的映射
=======================================
::
    
    /dev/snd/pcmC0D0[c|p]  -> /dev/audio0 (/dev/audio) -> 次设备号 4
    /dev/snd/pcmC0D0[c|p]  -> /dev/dsp0 (/dev/dsp)     -> 次设备号 3
    /dev/snd/pcmC0D1[c|p]  -> /dev/adsp0 (/dev/adsp)   -> 次设备号 12
    /dev/snd/pcmC1D0[c|p]  -> /dev/audio1              -> 次设备号 4+16 = 20
    /dev/snd/pcmC1D0[c|p]  -> /dev/dsp1                -> 次设备号 3+16 = 19
    /dev/snd/pcmC1D1[c|p]  -> /dev/adsp1               -> 次设备号 12+16 = 28
    /dev/snd/pcmC2D0[c|p]  -> /dev/audio2              -> 次设备号 4+32 = 36
    /dev/snd/pcmC2D0[c|p]  -> /dev/dsp2                -> 次设备号 3+32 = 39
    /dev/snd/pcmC2D1[c|p]  -> /dev/adsp2               -> 次设备号 12+32 = 44

``/dev/snd/pcmC{X}D{Y}[c|p]`` 表达式中的第一个数字表示声卡编号，第二个数字表示设备编号。ALSA设备有`c`或`p`后缀，分别表示捕获方向和播放方向。
请注意，上述设备映射可以通过snd-pcm-oss模块的模块选项进行调整。

proc接口（/proc/asound）
==============================

/proc/asound/card#/pcm#[cp]/oss
-------------------------------
erase
    清除所有关于OSS应用程序的附加信息

<app_name> <fragments> <fragment_size> [<options>]
    <app_name>
	应用程序名称（优先级更高）或不带路径
    <fragments>
	片段数量或自动时为零
    <fragment_size>
	片段大小（字节）或自动时为零
    <options>
	可选参数

	disable
	    应用程序试图为此通道打开一个pcm设备但不想使用它
	（会导致bug或mmap需要）
	    对Quake等游戏有好处
	direct
	    不使用插件
	block
	     强制块模式（适用于rvplayer）
	non-block
	    强制非块模式
	whole-frag
	    只写入完整的片段（仅影响播放的优化）
	no-silence
	    不填充静音以避免咔嚓声
	buggy-ptr
	    在GETOPTR ioctl中返回空白块而不是已填充块

示例：
::
    
    echo "x11amp 128 16384" > /proc/asound/card0/pcm0p/oss
    echo "squake 0 0 disable" > /proc/asound/card0/pcm0c/oss
    echo "rvplayer 0 0 block" > /proc/asound/card0/pcm0p/oss

早期缓冲区分配
=======================

一些驱动程序（例如hdsp）需要较大的连续缓冲区，并且有时在实际加载驱动程序模块时由于内存碎片化而找不到这样的空间。您可以通过加载snd-page-alloc模块并在早期启动阶段（例如``/etc/init.d/*.local``脚本）向其proc文件写入命令来预先分配PCM缓冲区。
读取proc文件 /proc/drivers/snd-page-alloc 可以查看当前页面分配的使用情况。在写入时，您可以向snd-page-alloc驱动发送以下命令：

* add VENDOR DEVICE MASK SIZE BUFFERS

VENDOR 和 DEVICE 是PCI供应商和设备ID。它们需要整数（十六进制需要0x前缀）
MASK 是PCI DMA掩码。如果不受限制，则传递0
SIZE 是要分配的每个缓冲区的大小。可以传递k和m后缀表示KB和MB。最大值为16MB
BUFFERS 是要分配的缓冲区数量。它必须大于 0。最大数量是 4。
* 清除

这将清除所有未使用的预分配缓冲区。
链接和地址
===========

ALSA 项目主页
    http://www.alsa-project.org
内核 Bugzilla
    http://bugzilla.kernel.org/
ALSA 开发者邮件列表
    mailto:alsa-devel@alsa-project.org
alsa-info.sh 脚本
    https://www.alsa-project.org/alsa-info.sh
