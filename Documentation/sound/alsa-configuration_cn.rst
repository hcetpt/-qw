==============================================================
高级 Linux 音频架构 — 驱动配置指南
==============================================================

内核配置
====================

要启用 ALSA 支持，至少需要使用主声卡支持（``CONFIG_SOUND``）来构建内核。由于 ALSA 可以模拟 OSS，因此您不必选择任何 OSS 模块。启用“OSS API 模拟”（``CONFIG_SND_OSSEMUL``），如果您希望用 ALSA 运行 OSS 应用程序，则同时启用 OSS 混音器和 PCM 支持。如果您希望支持 SB Live! 等卡片上的 WaveTable 功能，则需要启用“序列器支持”（``CONFIG_SND_SEQUENCER``）。为了使 ALSA 调试消息更详细，请启用“详细的 printk”和“调试”选项。要检查内存泄漏，请打开“调试内存”。 “调试检测”将增加对卡片检测的检查。

请注意，所有 ALSA ISA 驱动程序都支持 Linux isapnp API（如果卡片支持 ISA PnP）。您无需使用 isapnptools 来配置卡片。
模块参数
=================

用户可以使用选项加载模块。如果模块支持多种卡片类型，并且您拥有相同类型的多张卡片，则可以为该选项指定多个值，各值之间用逗号分隔。
snd 模块
----------

这是 ALSA 核心模块。它被所有 ALSA 卡驱动程序所使用。
它接受以下具有全局影响的选项：
major
    声卡驱动的主要编号；
    默认值：116
cards_limit
    自动加载时限制卡片索引范围（1-8）；
    默认值：1；
    若要自动加载多张卡片，请与 snd-card-X 别名一起指定此选项
slots
    为给定驱动程序保留插槽索引；
    此选项接受多个字符串
请参阅`模块自动加载支持`_ 部分以获取详细信息。
调试
    指定调试消息级别；
    （0 = 禁用调试打印，1 = 正常调试消息，
    2 = 详细调试消息）；
    当配置项 ``CONFIG_SND_DEBUG=y`` 时此选项才会出现。
此选项可以通过 sysfs 动态更改
    /sys/modules/snd/parameters/debug 文件
snd-pcm-oss 模块
------------------

PCM OSS 模拟模块
此模块提供了一些选项来改变设备的映射关系
dsp_map
    PCM 设备编号映射到第一个 OSS 设备；
    默认值：0
adsp_map
    PCM 设备编号映射到第二个 OSS 设备；
    默认值：1
nonblock_open
    不阻塞打开繁忙的 PCM 设备；
    默认值：1

例如，当 ``dsp_map=2`` 时，/dev/dsp 将被映射为第 0 张声卡上的 PCM #2。类似地，当 ``adsp_map=0`` 时，/dev/adsp 将被映射为第 0 张声卡上的 PCM #0。
为了更改第二张或之后的声卡，请使用逗号分隔的方式指定该选项，如 ``dsp_map=0,1``。
``nonblock_open`` 选项用于改变 PCM 打开设备的行为。当此选项非零时，尝试打开一个忙碌的 OSS PCM 设备将不会被阻塞，而是立即返回 EAGAIN（就像设置了 O_NONBLOCK 标志一样）。
snd-rawmidi 模块
------------------

此模块提供了与 snd-pcm-oss 模块类似的选项来改变设备的映射关系。
### `midi_map`
MIDI 设备编号映射到第一个 OSS 设备；
默认值：0
`amidi_map`
MIDI 设备编号映射到第二个 OSS 设备；
默认值：1

### 模块 `snd-soc-core`
#### 社交核心模块。
此模块被所有 ALSA 卡驱动程序使用。
它接受以下具有全局影响的选项：
- `prealloc_buffer_size_kbytes`
  - 指定预分配缓冲区大小（以千字节为单位）（默认：512）

### 高级声卡模块通用参数
每个顶级声卡模块都接受以下选项：
- `index`
  - 声卡的索引号（插槽编号）；
  - 取值范围：0 至 31 或负数；
  - 如果是非负数，则分配该索引号；
  - 如果是负数，则将其解释为允许索引的位掩码；
  - 分配第一个空闲的允许索引号；
  - 默认值：-1
- `id`
  - 卡标识符（或名称）；
  - 最多可以有 15 个字符长；
  - 默认值：声卡类型；
  - 在 `/proc/asound/` 下创建以此 ID 命名的目录，其中包含有关声卡的信息；
  - 此 ID 可用于代替索引号来识别声卡
- `enable`
  - 启用声卡；
  - 默认值：启用，适用于 PCI 和 ISA PnP 卡

这些选项用于指定实例的顺序或控制使用同一驱动程序绑定的多个设备的启用和禁用。例如，许多机器都有两个 HD-Audio 控制器（一个用于 HDMI/DP 音频，另一个用于板载模拟）。在大多数情况下，第二个控制器是主要使用的，并且用户可能希望将其分配为第一个出现的声卡。他们可以通过指定 "index=1,0" 模块参数来实现这一点，这将交换分配的索引位置。
如今，在像 PulseAudio 和 PipeWire 这样的支持动态配置的声音后端下，这种方法的用途不大，但在过去对于静态配置来说是一个帮助。

### 模块 `snd-adlib`
#### 适用于 AdLib FM 卡的模块
- `port`
  - OPL 芯片的端口号

此模块支持多张卡。它不支持自动探测，因此必须指定端口。对于实际的 AdLib FM 卡，端口通常是 0x388。
请注意，这张卡没有 PCM 支持并且没有混音器；只有 FM 合成。
确保您已安装来自 alsa-tools 包的 `sbiload` 并在加载模块后，通过 `sbiload -l` 查找分配给 ALSA 序列器的端口号。
示例输出：

```
端口     客户端名称                       端口名称
64:0     OPL2 FM 合成器                   OPL2 FM 端口
```

加载 `std.sb` 和 `drums.sb` 补丁，这些补丁也由 `sbiload` 提供：
```
sbiload -p 64:0 std.sb drums.sb
```

如果您使用此驱动程序来驱动 OPL3，您可以使用 `std.o3` 和 `drums.o3`。
要使声卡发出声音，请使用 alsa-utils 中的 `aplaymidi`：
```
aplaymidi -p 64:0 foo.mid
```

snd-ad1816a 模块
------------------

基于 Analog Devices AD1816A/AD1815 ISA 芯片的声音卡模块
clockfreq
    AD1816A 芯片的时钟频率（默认 = 0, 33000Hz）

此模块支持多张声卡、自动探测和即插即用功能。

snd-ad1848 模块
-----------------

基于 AD1848/AD1847/CS4248 ISA 芯片的声音卡模块
port
    AD1848 芯片的端口号
irq
    AD1848 芯片的中断请求号
dma1
    AD1848 芯片的数据传输模式号（0,1,3）

此模块支持多张声卡。它不支持自动探测，因此必须指定主端口！其他端口是可选的。
支持电源管理。

snd-ad1889 模块
-----------------

Analog Devices AD1889 芯片模块
ac97_quirk
    针对奇怪硬件的 AC'97 解决方案；
    详情请参阅 intel8x0 模块的描述

此模块支持多张声卡。

snd-ali5451 模块
------------------

ALi M5451 PCI 芯片模块
pcm_channels
    分配给 PCM 的硬件通道数量
spdif
    支持 SPDIF 输入输出；
    默认：禁用

此模块支持一张芯片并具有自动探测功能。
电源管理得到支持  
模块 snd-als100  
-----------------  

基于 Avance Logic ALS100/ALS120 ISA 芯片的声卡模块  
此模块支持多张声卡、自动探测和即插即用（PnP）  
电源管理得到支持  
模块 snd-als300  
-----------------  

适用于 Avance Logic ALS300 和 ALS300+ 的模块  

此模块支持多张声卡  
电源管理得到支持  
模块 snd-als4000  
------------------  

基于 Avance Logic ALS4000 PCI 芯片的声卡模块  
joystick_port  
    为传统游戏杆提供的端口号；  
    0 = 禁用（默认），1 = 自动检测  
    
此模块支持多张声卡、自动探测和即插即用（PnP）  
电源管理得到支持  
模块 snd-asihpi  
-----------------  

适用于 AudioScience ASI 声卡的模块  

enable_hpi_hwdep  
    为 AudioScience 声卡启用 HPI hwdep  

此模块支持多张声卡
驱动程序需要内核模块 `snd-atiixp` 中的固件加载器支持。
### 模块 `snd-atiixp`
#### 针对 ATI IXP 150/200/250/400 AC97 控制器的模块
- **ac97_clock**
  - AC'97 时钟（默认 = 48000）
- **ac97_quirk**
  - AC'97 为奇怪硬件提供的变通方案；
  - 参见下面的 `AC97 Quirk Option`_ 部分
- **ac97_codec**
  - 用于指定 AC'97 编解码器而不是探测的变通方案
  - 如果这对你有效，请附上你的 `lspci -vn` 输出并提交一个错误报告
  - （-2 = 强制探测，-1 = 默认行为，0-2 = 使用指定的编解码器）
- **spdif_aclink**
  - 通过 AC-link 进行 S/PDIF 传输（默认 = 1）

此模块支持一张卡和自动探测功能。
ATI IXP 有两种不同的方法来控制 SPDIF 输出。一种是通过 AC-link，另一种是通过“直接”SPDIF 输出。实现取决于主板，并且您需要通过 `spdif_aclink` 模块选项选择正确的方法。
支持电源管理。
### 模块 `snd-atiixp-modem`
#### 针对 ATI IXP 150/200/250 AC97 调制解调器控制器的模块
此模块支持一张卡和自动探测功能。
注：此模块的默认索引值为 -2，即第一个插槽被排除在外。
支持电源管理。
模块 snd-au8810、snd-au8820、snd-au8830
---------------------------------------------------

此模块适用于 Aureal Vortex、Vortex2 和 Advantage 设备
pcifix
    控制 PCI 解决方案；
    0 = 禁用所有解决方案，
    1 = 强制将 Aureal 卡的 PCI 延迟设置为 0xff，
    2 = 强制设置 Extend PCI#2 内部主控以高效处理虚拟请求在 VIA KT133 AGP 桥上，
    3 = 同时强制两个设置，
    255 = 自动检测所需的设置（默认）

此模块支持所有 ADB PCM 通道、AC97 混音器、SPDIF、硬件均衡器、mpu401、游戏端口。A3D 和波表功能仍在开发中。
开发和逆向工程工作在 https://savannah.nongnu.org/projects/openvortex/ 中进行协调。
SPDIF 输出是 AC97 编解码输出的副本，除非您使用 "spdif" PCM 设备，它允许原始数据直通。
硬件均衡器和 SPDIF 仅存在于 Vortex2 和 Advantage 中。
注：一些 ALSA 混音器应用程序不能正确处理 SPDIF 采样率控制。如果您遇到与此相关的问题，请尝试使用另一个符合 ALSA 标准的混音器（alsamixer 可用）。
模块 snd-azt1605
------------------

基于 Aztech AZT1605 芯片组的 Aztech Sound Galaxy 声卡模块
port
    BASE 的端口号（0x220、0x240、0x260、0x280）
wss_port
    WSS 的端口号（0x530、0x604、0xe80、0xf40）
irq
    WSS 的 IRQ 号（7、9、10、11）
dma1
    WSS 播放的 DMA 号（0、1、3）
dma2
    WSS 录音的 DMA 号（0、1），-1 = 禁用（默认）
mpu_port
    MPU-401 UART 的端口号（0x300、0x330），-1 = 禁用（默认）
mpu_irq
    MPU-401 UART 的 IRQ 号（3、5、7、9），-1 = 禁用（默认）
fm_port
    OPL3 的端口号（0x388），-1 = 禁用（默认）

此模块支持多张声卡。它不支持自动探测：
`port`、`wss_port`、`irq` 和 `dma1` 必须指定
其他值可选。
``port`` 需要与声卡上的基础地址跳线匹配（0x220 或 0x240），或者对于那些具有 EEPROM 并且其“CONFIG MODE”跳线设置为“EEPROM 设置”的声卡，需要与卡上 EEPROM 中存储的值相匹配。其他值可以从上面列举的选项中自由选择。

如果指定了 ``dma2`` 并且它与 ``dma1`` 不同，则声卡将以全双工模式运行。当 ``dma1=3`` 时，只有 ``dma2=0`` 是有效的，并且这是启用录音功能的唯一方式，因为仅通道 0 和 1 可用于录音。

通用设置为：``port=0x220 wss_port=0x530 irq=10 dma1=1 dma2=0 mpu_port=0x330 mpu_irq=9 fm_port=0x388``

无论你选择哪个 IRQ 和 DMA 通道，请确保在你的 BIOS 中为传统 ISA 预留这些通道。

### snd-azt2316 模块

基于 Aztech AZT2316 芯片组的 Aztech Sound Galaxy 声卡模块。

- port
    - 基础端口编号（0x220、0x240、0x260、0x280）
- wss_port
    - WSS 端口编号（0x530、0x604、0xe80、0xf40）
- irq
    - WSS 的 IRQ 编号（7、9、10、11）
- dma1
    - WSS 播放的 DMA 编号（0、1、3）
- dma2
    - WSS 录音的 DMA 编号（0、1），-1 表示禁用（默认）
- mpu_port
    - MPU-401 UART 的端口编号（0x300、0x330），-1 表示禁用（默认）
- mpu_irq
    - MPU-401 UART 的 IRQ 编号（5、7、9、10），-1 表示禁用（默认）
- fm_port
    - OPL3 的端口编号（0x388），-1 表示禁用（默认）

此模块支持多张声卡。它不支持自动探测：必须指定 ``port``、``wss_port``、``irq`` 和 ``dma1``。
其他值是可选的。

``port`` 需要与声卡上的基础地址跳线匹配（0x220 或 0x240），或者对于那些具有 EEPROM 并且其“CONFIG MODE”跳线设置为“EEPROM 设置”的声卡，需要与卡上 EEPROM 中存储的值相匹配。其他值可以从上面列举的选项中自由选择。

如果指定了 ``dma2`` 并且它与 ``dma1`` 不同，则声卡将以全双工模式运行。当 ``dma1=3`` 时，只有 ``dma2=0`` 是有效的，并且这是启用录音功能的唯一方式，因为仅通道 0 和 1 可用于录音。

通用设置为：``port=0x220 wss_port=0x530 irq=10 dma1=1 dma2=0 mpu_port=0x330 mpu_irq=9 fm_port=0x388``
> 无论你选择哪些 IRQ 和 DMA 通道，请确保在你的 BIOS 中为传统 ISA 预留这些通道。
> 
> 模块 snd-aw2
> --------------
> 
> 适用于 Audiowerk2 声卡的模块
> 
> 此模块支持多张声卡
> 
> 模块 snd-azt2320
> ------------------
> 
> 适用于基于 Aztech System AZT2320 ISA 芯片（仅即插即用）的声卡的模块
> 
> 此模块支持多张声卡、即插即用和自动探测。支持电源管理。
> 
> 模块 snd-azt3328
> ------------------
> 
> 适用于基于 Aztech AZF3328 PCI 芯片的声卡的模块
> 
> 游戏杆
>     启用游戏杆（默认关闭）
> 
> 此模块支持多张声卡
> 
> 模块 snd-bt87x
> -----------------
> 
> 适用于基于 Bt87x 芯片的视频卡的模块
> 
> 数字频率
>     覆盖默认的数字频率（赫兹）
> 
> 加载所有
>     即使不知道声卡型号也加载驱动程序
> 
> 此模块支持多张声卡
> 
> 注意：此模块的默认索引值为 -2，也就是说第一个插槽被排除在外。
模块 snd-ca0106
-----------------

适用于 Creative Audigy LS 和 SB Live 24位声卡的模块。

此模块支持多张声卡。
模块 snd-cmi8330
------------------

适用于基于 C-Media CMI8330 ISA 芯片的声卡的模块。
isapnp
    ISA 插即用检测 - 0 = 禁用, 1 = 启用（默认）

使用 `isapnp=0` 时，以下选项可用：

wssport
    CMI8330 芯片（WSS）的端口号
wssirq
    CMI8330 芯片（WSS）的中断请求号
wssdma
    CMI8330 芯片（WSS）的第一个直接内存访问号
sbport
    CMI8330 芯片（SB16）的端口号
sbirq
    CMI8330 芯片（SB16）的中断请求号
sbdma8
    CMI8330 芯片（SB16）的 8 位直接内存访问号
sbdma16
    CMI8330 芯片（SB16）的 16 位直接内存访问号
fmport
    （可选）OPL3 输入/输出端口
mpuport
    （可选）MPU401 输入/输出端口
mpuirq
    （可选）MPU401 中断请求号

此模块支持多张声卡和自动探测，并且支持电源管理。
模块 snd-cmipci
-----------------

适用于 C-Media CMI8338/8738/8768/8770 PCI 声卡的模块。
mpu_port
    MIDI 接口的端口地址（仅 8338）：
    0x300、0x310、0x320、0x330 = 传统端口，
    1 = 集成 PCI 端口（8738 默认），
    0 = 禁用
fm_port
    OPL-3 FM 合成器的端口地址（仅 8x38）：
    0x388 = 传统端口，
    1 = 集成 PCI 端口（8738 默认），
    0 = 禁用
soft_ac3
    原始 SPDIF 数据包的软件转换（仅限型号 033）（默认 = 1）
joystick_port
    游戏杆端口地址（0 = 禁用, 1 = 自动检测）

此模块支持自动探测和多张声卡，并且支持电源管理。
模块 snd-cs4231
-----------------

适用于基于 CS4231 ISA 芯片的声卡的模块。
port
    CS4231 芯片的端口号
mpu_port
    MPU-401 UART 的端口号（可选），-1 = 禁用
irq
    CS4231 芯片的中断请求号
mpu_irq
    MPU-401 UART 的中断请求号
dma1
    CS4231 芯片的第一个直接内存访问号
dma2
    CS4231 芯片的第二个直接内存访问号

此模块支持多张声卡。此模块不支持自动探测，因此必须指定主端口号！其他端口为可选项。
该模块支持电源管理。
模块 snd-cs4236
--------------

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

此模块支持多张声卡。此模块不支持自动探测（如果不使用 ISA 即插即用）因此必须指定主端口和控制端口！！！其他端口是可选的。
支持电源管理。
此模块别名为 snd-cs4232，因为它也提供了旧版 snd-cs4232 的功能。

模块 snd-cs4281
--------------

Cirrus Logic CS4281 声卡芯片模块
dual_codec
    次要编解码器 ID（0 = 禁用，默认）

此模块支持多张声卡。
支持电源管理。

模块 snd-cs46xx
--------------

基于 CS4610/CS4612/CS4614/CS4615/CS4622/CS4624/CS4630/CS4280 PCI 芯片的 PCI 声卡模块
external_amp
    强制启用外部放大器
thinkpad
    强制启用 Thinkpad 的 CLKRUN 控制
mmap_valid  
支持 OSS mmap 模式（默认 = 0）  
此模块支持多张声卡及自动探测。  
通常外部放大器和 CLKRUN 控制会根据 PCI 子供应商/设备 ID 自动检测到。如果不起作用，请明确给出上述选项。  
支持电源管理。  
snd-cs5530 模块  
-----------------  
适用于 Cyrix/NatSemi Geode 5530 芯片的模块。  

snd-cs5535audio 模块  
----------------------  
适用于多功能 CS5535 伴行 PCI 设备的模块。  
支持电源管理。  
snd-ctxfi 模块  
-----------------  
适用于 Creative Sound Blaster X-Fi 系列板卡（20k1 / 20k2 芯片）的模块：  
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
参考采样率，44100 或 48000（默认）  
multiple  
参考采样率的倍数，1 或 2（默认）  
subsystem  
用于探测时覆盖 PCI SSID；该值由 SSVID 左移 16 位或 SSDID 组成。  
默认为零，意味着不进行覆盖。  
此模块支持多张声卡。  
snd-darla20 模块  
------------------  
适用于 Echoaudio Darla20 的模块。  
此模块支持多张声卡。  
驱动程序需要内核上的固件加载器支持。
### Module snd-darla24
------------------

针对 Echoaudio Darla24 的模块

此模块支持多张声卡
驱动程序需要内核上的固件加载器支持
### Module snd-dt019x
-----------------

针对 Diamond Technologies DT-019X / Avance Logic ALS-007（仅即插即用）的模块

此模块支持多张声卡。此模块仅在启用 ISA 即插即用支持时有效
支持电源管理
### Module snd-dummy
----------------

针对虚拟声卡的模块。这张“声卡”不进行任何输出或输入，但您可以使用此模块来满足任何需要声卡的应用程序的需求（如 RealPlayer）
- pcm_devs
    分配给每张声卡的 PCM 设备数量（默认 = 1，最多 4）
- pcm_substreams
    分配给每个 PCM 的 PCM 子流数量（默认 = 8，最多 128）
- hrtimer
    使用高分辨率定时器（=1，默认）或系统定时器（=0）
- fake_buffer
    虚拟缓冲区分配（默认 = 1）

当创建多个 PCM 设备时，snd-dummy 会为每个 PCM 设备提供不同的行为：
- *0* = 交错模式，并支持内存映射
- *1* = 非交错模式，并支持内存映射
- *2* = 交错模式，不支持内存映射
- *3* = 非交错模式，不支持内存映射

默认情况下，snd-dummy 驱动程序不会分配真实的缓冲区，而是忽略读写操作或为所有缓冲区页面映射一个虚拟页，以节省资源。如果您的应用程序需要读取/写入的缓冲区数据保持一致，请传递 `fake_buffer=0` 选项
支持电源管理
### Module snd-echo3g
-----------------

针对 Echoaudio 3G 声卡（Gina3G/Layla3G）的模块

此模块支持多张声卡
驱动程序需要内核上的固件加载器支持
### Module snd-emu10k1
------------------

针对基于 EMU10K1/EMU10k2 的 PCI 声卡的模块
* Sound Blaster Live!
* Sound Blaster PCI 512
* Sound Blaster Audigy
* E-MU APS（部分支持）
* E-MU DAS

extin  
    FX8010可用外部输入的位图（参见下方说明）
extout  
    FX8010可用外部输出的位图（参见下方说明）
seq_ports  
    分配的音序端口（默认为4个）
max_synth_voices  
    波表合成声音的最大数量（默认为64）
max_buffer_size  
    以MB为单位指定波表/PCM缓冲区的最大大小。默认值为128。
enable_ir  
    启用红外功能

此模块支持多张声卡和自动探测。
输入与输出配置			[extin/extout]
* 创意声卡无数字输出			[0x0003/0x1f03]
* 创意声卡有数字输出			[0x0003/0x1f0f]
* 创意声卡有数字CD输入			[0x000f/0x1f0f]
* 创意声卡无数字输出+LiveDrive		[0x3fc3/0x1fc3]
* 创意声卡有数字输出+LiveDrive		[0x3fc3/0x1fcf]
* 创意声卡有数字CD输入+LiveDrive		[0x3fcf/0x1fcf]
* 创意声卡无数字输出+数字I/O 2		[0x0fc3/0x1f0f]
* 创意声卡有数字输出+数字I/O 2		[0x0fc3/0x1f0f]
* 创意声卡有数字CD输入+数字I/O 2		[0x0fcf/0x1f0f]
* 创意声卡5.1/有数字输出+LiveDrive		[0x3fc3/0x1fff]
* 创意声卡5.1（版权2003年）			[0x3fc3/0x7cff]
* 创意声卡所有输入和输出			[0x3fff/0x7fff]

支持电源管理。
Module snd-emu10k1x  
-------------------
适用于Creative Emu10k1X（SB Live Dell OEM版本）的模块。

此模块支持多张声卡。
Module snd-ens1370  
------------------
适用于Ensoniq AudioPCI ES1370 PCI声卡的模块
* SoundBlaster PCI 64
* SoundBlaster PCI 128

joystick  
    启用游戏手柄（默认关闭）

此模块支持多张声卡和自动探测。
支持电源管理。
Module snd-ens1371  
------------------
适用于Ensoniq AudioPCI ES1371 PCI声卡的模块
* SoundBlaster PCI 64
* SoundBlaster PCI 128
* SoundBlaster Vibra PCI

joystick_port  
    游戏手柄端口号（0x200、0x208、0x210、0x218），0 = 禁用（默认），1 = 自动检测

此模块支持多张声卡和自动探测。
支持电源管理。
### Module snd-es1688
-----------------

此模块适用于ESS AudioDrive ES-1688 和 ES-688 声卡
isapnp
    ISA 即插即用检测 - 0 = 禁用, 1 = 启用（默认）
mpu_port
    MPU-401 端口的端口号（0x300, 0x310, 0x320, 0x330），-1 = 禁用（默认）
mpu_irq
    MPU-401 端口的中断请求号（IRQ）（5, 7, 9, 10）
fm_port
    OPL3 的端口号（可选；默认情况下与 MPU-401 共享同一个端口）

使用 `isapnp=0` 时，以下额外选项可用：

port
    ES-1688 芯片的端口号（0x220, 0x240, 0x260）
irq
    ES-1688 芯片的中断请求号（IRQ）（5, 7, 9, 10）
dma8
    ES-1688 芯片的数据管理器地址（DMA）编号（0, 1, 3）

此模块支持多张声卡和自动探测（不包括 MPU-401 端口）以及带有 ES968 芯片的即插即用功能。

### Module snd-es18xx
-----------------

此模块适用于ESS AudioDrive ES-18xx 声卡
isapnp
    ISA 即插即用检测 - 0 = 禁用, 1 = 启用（默认）

使用 `isapnp=0` 时，以下选项可用：

port
    ES-18xx 芯片的端口号（0x220, 0x240, 0x260）
mpu_port
    MPU-401 端口的端口号（0x300, 0x310, 0x320, 0x330），-1 = 禁用（默认）
fm_port
    FM 的端口号（可选，未使用）
irq
    ES-18xx 芯片的中断请求号（IRQ）（5, 7, 9, 10）
dma1
    ES-18xx 芯片的第一个数据管理器地址（DMA）编号（0, 1, 3）
dma2
    ES-18xx 芯片的第一个数据管理器地址（DMA）编号（0, 1, 3）

当 `dma2` 与 `dma1` 相等时，驱动程序以半双工模式工作。
此模块支持多张声卡、ISA 即插即用和自动探测（如果不使用原生的 ISA 即插即用例程，则不包括 MPU-401 端口）。
支持电源管理。

### Module snd-es1938
-----------------

此模块适用于基于 ESS Solo-1 (ES1938, ES1946) 芯片的声卡
此模块支持多张声卡和自动探测。
支持电源管理。

### Module snd-es1968
-----------------

此模块适用于基于 ESS Maestro-1/2/2E (ES1968/ES1978) 芯片的声卡
### 参数说明：

- `total_bufsize`
    - 总缓冲区大小，单位为千字节（KB）（范围：1-4096KB）
- `pcm_substreams_p`
    - 播放声道数（范围：1-8，默认值为2）
- `pcm_substreams_c`
    - 录音声道数（范围：1-8，默认值为0）
- `clock`
    - 时钟设置（0 = 自动检测）
- `use_pm`
    - 支持电源管理功能（0 = 关闭，1 = 开启，2 = 自动，默认为自动）
- `enable_mpu`
    - 启用MPU401功能（0 = 关闭，1 = 开启，2 = 自动，默认为自动）
- `joystick`
    - 启用游戏手柄功能（默认关闭）

### 模块描述：

#### Module `snd-fm801`

- **用途**：适用于基于ForteMedia FM801的PCI声卡。
- **特性**：
  - 支持多张声卡及自动探测。
  - 支持电源管理。

#### `tea575x_tuner`
- **启用TEA575x调谐器**；具体配置如下：
  - 1 = MediaForte 256-PCS
  - 2 = MediaForte 256-PCPR
  - 3 = MediaForte 64-PCR
- **附加信息**：
  - 高16位表示视频（或无线电）设备编号加1；
  - 示例：`0x10002`（MediaForte 256-PCPR，设备1号）

- **特性**：
  - 支持多张声卡及自动探测。
  - 支持电源管理。

#### Module `snd-gina20`

- **用途**：适用于Echoaudio Gina20声卡。
- **特性**：
  - 支持多张声卡。
  - 需要内核级别的固件加载器支持。

#### Module `snd-gina24`

- **用途**：适用于Echoaudio Gina24声卡。
- **特性**：
  - 支持多张声卡。
  - 需要内核级别的固件加载器支持。

#### Module `snd-gusclassic`

- **用途**：适用于Gravis UltraSound Classic声卡。
以下是提供的配置选项的中文翻译：

### 模块snd-gusextreme
---------------------
此模块用于Gravis UltraSound Extreme (Synergy ViperMax) 声卡。

- **port**
    - ES-1688芯片的端口号 (0x220, 0x230, 0x240, 0x250, 0x260)
- **gf1_port**
    - GF1芯片的端口号 (0x210, 0x220, 0x230, 0x240, 0x250, 0x260, 0x270)
- **mpu_port**
    - MPU-401端口的端口号 (0x300, 0x310, 0x320, 0x330)，-1 = 禁用
- **irq**
    - ES-1688芯片的IRQ号 (5, 7, 9, 10)
- **gf1_irq**
    - GF1芯片的IRQ号 (3, 5, 9, 11, 12, 15)
- **mpu_irq**
    - MPU-401端口的IRQ号 (5, 7, 9, 10)
- **dma8**
    - ES-1688芯片的DMA号 (0, 1, 3)
- **dma1**
    - GF1芯片的DMA号 (1, 3, 5, 6, 7)
- **joystick_dac**
    - 0 到 31，(0.59V-4.52V 或 0.389V-2.98V)
- **voices**
    - GF1音轨限制 (14-32)
- **pcm_voices**
    - 预留的PCM音轨

此模块支持多张声卡和自动探测（不包括MPU-401端口）。

### 模块snd-gusmax
-----------------
此模块用于Gravis UltraSound MAX 声卡。

- **port**
    - GF1芯片的端口号 (0x220, 0x230, 0x240, 0x250, 0x260)
- **irq**
    - GF1芯片的IRQ号 (3, 5, 9, 11, 12, 15)
- **dma1**
    - GF1芯片的DMA号 (1, 3, 5, 6, 7)
- **dma2**
    - GF1芯片的DMA号 (1, 3, 5, 6, 7, -1=禁用)
- **joystick_dac**
    - 0 到 31，(0.59V-4.52V 或 0.389V-2.98V)
- **voices**
    - GF1音轨限制 (14-32)
- **pcm_voices**
    - 预留的PCM音轨

此模块支持多张声卡和自动探测。

### 模块snd-hda-intel
--------------------
此模块用于Intel HD Audio (ICH6, ICH6M, ESB2, ICH7, ICH8, ICH9, ICH10, PCH, SCH), ATI SB450, SB600, R600, RS600, RS690, RS780, RV610, RV620, RV630, RV635, RV670, RV770, VIA VT8251/VT8237A, SIS966, ULI M5461等。

- **model**
    - 强制指定模型名称
- **position_fix**
    - 修正DMA指针；
    - -1 = 系统默认：根据控制器硬件选择适当的设置，
    - 0 = 自动：当POSBUF不起作用时回退到LPIB，
    - 1 = 使用LPIB，
    - 2 = POSBUF: 使用位置缓冲区，
    - 3 = VIACOMBO: VIA特有的用于捕获的解决方案，
    - 4 = COMBO: 播放使用LPIB，捕获流自动设置，
    - 5 = SKL+: 对最近的Intel芯片应用延迟计算，
    - 6 = FIFO: 通过固定FIFO大小来校正位置，适用于最近的AMD芯片
- **probe_mask**
    - 探测编解码器的位掩码（默认 = -1，意味着所有插槽）；
    - 当第8位 (0x100) 被设置时，低8位被用作“固定”的编解码器插槽；即驱动程序将探测这些插槽，而不论硬件报告的内容。
- **probe_only**
    - 仅探测而不初始化编解码器（默认=关闭）；
    - 用于调试检查初始编解码器状态很有用。
- **bdl_pos_adj**
    - 指定基于控制器芯片的DMA IRQ定时延迟的样本数
    - 传递-1将使驱动程序选择适当值
- **patch**
    - 指定在初始化编解码器之前的早期“补丁”文件以修改HD音频设置
    - 此选项仅在设置`CONFIG_SND_HDA_PATCH_LOADER=y`时可用。详情请参阅hd-audio/notes.rst
- **beep_mode**
    - 选择蜂鸣注册模式 (0=关闭, 1=开启)；
    - 默认值通过`CONFIG_SND_HDA_INPUT_BEEP_MODE` kconfig设置

每个声卡实例都有多个选项。
[单一（全局）选项]

single_cmd  
    使用单一即时命令与编解码器通信  
    （仅用于调试）
enable_msi  
    启用消息指示中断（MSI）（默认：关闭）
power_save  
    自动节能超时时间（单位：秒，0 = 禁用）
power_save_controller  
    在节能模式下重置高清音频控制器（默认：开启）
align_buffer_size  
    强制将缓冲区/周期大小调整为128字节的倍数  
    这在内存访问方面更高效，但并非HDA规范的要求，并且会阻止用户指定确切的周期/缓冲区大小。（默认：开启）
snoop  
    启用/禁用窥探（默认：开启）

此模块支持多张声卡及自动探测。
有关高清音频驱动程序的更多详细信息，请参阅`hd-audio/notes.rst`。
每个编解码器可能有不同的配置模型表。
如果您的机器未列在其中，则会设置默认配置（通常是最低配置）。
您可以传递`model=<name>`选项来指定某种特定的模型。根据不同的编解码器芯片，存在多种模型。
您可以在`hd-audio/models.rst`中找到可用模型的列表。
模型名称`generic`被视为特殊情况。当给出此模型时，驱动程序将使用不含“编解码器补丁”的通用编解码器解析器。这有时对测试和调试很有帮助。
模型选项也可以用于别名到另一个PCI或编解码器SSID。如果以`model=XXXX:YYYY`的形式传递，其中`XXXX`和`YYYY`分别是十六进制形式的子厂商和子设备ID，则驱动程序会将该SSID作为怪癖表的引用。
如果默认配置不起作用，并且上述某项与您的设备匹配，请将`alsa-info.sh`输出（使用`--no-upload`选项）以及相关信息报告给内核bug追踪系统或alsa-devel邮件列表（请参见`链接和地址`_部分）。
`power_save`和`power_save_controller`选项用于节能模式。详情请参阅`powersave.rst`。
注意2：如果您在输出时听到咔哒声，尝试使用模块选项`position_fix=1`或`2`。`position_fix=1`将使用SD_LPIB寄存器值（不进行FIFO大小校正）作为当前DMA指针。`position_fix=2`会使驱动程序使用位置缓冲区而不是读取SD_LPIB寄存器。
（通常，SD_LPIB 寄存器比位置缓冲区更准确。）

`position_fix=3` 是 VIA 设备特有的。捕获流的位置会从 LPIB 和 POSBUF 的值中进行检查。`position_fix=4` 是一种组合模式，播放时使用 LPIB，捕获时使用 POSBUF。

注意：如果你在加载过程中遇到许多“azx_get_response 超时”消息，这可能是中断问题（例如 ACPI 中断路由）。尝试使用如 `pci=noacpi` 这样的选项启动。此外，你也可以试试 `single_cmd=1` 模块选项。这将把 HDA 控制器和编解码器之间的通信方式改为单一即时命令而不是 CORB/RIRB。基本上，单一命令模式只为 BIOS 提供，并且你也不会接收到未被请求的事件。但是至少，这种方式不受中断的影响。请记住这是最后的手段，并应尽可能避免使用。
关于“azx_get_response 超时”问题的更多说明：
在某些硬件上，你可能需要添加一个合适的 probe_mask 选项来避免上述的“azx_get_response 超时”问题。这种情况发生在访问不存在或不工作的编解码器插槽（很可能是调制解调器插槽）导致通过高清音频总线的通信停滞。你可以通过启用 `CONFIG_SND_DEBUG_VERBOSE` 或者仅仅从编解码器 proc 文件的文件名中查看哪些编解码器插槽被探测了。然后通过 probe_mask 选项限制要探测的插槽。
例如，`probe_mask=1` 表示只探测第一个插槽，而 `probe_mask=4` 表示只探测第三个插槽。
支持电源管理。
snd-hdsp 模块
-------------------

RME Hammerfall DSP 音频接口模块

此模块支持多张卡。
注意：当设置了 `CONFIG_FW_LOADER` 时，固件数据可以通过热插拔自动加载。否则，你需要通过 alsa-tools 包中的 hdsploader 实用程序加载固件。
固件数据可以在 alsa-firmware 包中找到。
注意：snd-page-alloc 模块完成了之前由 snd-hammerfall-mem 模块完成的工作。当检测到任何 HDSP 卡时，它将提前分配缓冲区。为了确保缓冲区的分配，请在启动序列的早期阶段加载 snd-page-alloc 模块。请参阅“早期缓冲区分配”部分。
### Module snd-hdspm
-------------------

RME HDSP MADI 板卡的模块
- precise_ptr
    - 启用精确指针，或禁用
- line_outs_monitor
    - 默认将播放流发送到模拟输出
- enable_monitor
    - 默认在第 63/64 通道启用模拟输出
详情请参阅 `hdspm.rst`

### Module snd-ice1712
----------------------

基于 Envy24 (ICE1712) 的 PCI 声卡模块
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
    - 使用给定的板卡型号，选项如下：
        - delta1010, dio2496, delta66, delta44, audiophile, delta410,
        - delta1010lt, vx442, ewx2496, ews88mt, ews88mt_new, ews88d,
        - dmx6fire, dsp24, dsp24_value, dsp24_71, ez8,
        - phase88, mediastation
- omni
    - MidiMan M-Audio Delta44/66 的 Omni I/O 支持
- cs8427_timeout
    - CS8427 芯片（S/PDIF 收发器）的重置超时时间（以毫秒为单位），默认值为 500（0.5 秒）

此模块支持多张声卡和自动探测。
注意：并非所有基于 Envy24 的声卡都使用消费级部分（例如在 MidiMan Delta 系列中）
注意：通过读取 EEPROM 或 PCI SSID（如果不可用 EEPROM）来检测支持的板卡。如果您想覆盖模型，可以通过传递 `model` 模块选项，比如驱动程序配置不正确或您想要尝试其他类型来进行测试。

### Module snd-ice1724
----------------------

基于 Envy24HT (VT/ICE1724)，Envy24PT (VT1720) 的 PCI 声卡模块
这些是不同型号的音频卡和相关模块的描述。下面是翻译成中文的内容：

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

模型
使用给定的板卡模型，选择以下之一：
revo51, revo71, amp2000, prodigy71, prodigy71lt, prodigy71xt, prodigy71hifi, prodigyhd2, prodigy192, juli, aureon51, aureon71, universe, ap192, k8x800, phase22, phase28, ms300, av710, se200pci, se90pci, fortissimo4, sn25p, WT192M, maya44

此模块支持多张卡，并自动探测
注意：通过读取EEPROM或PCI SSID（如果不可用EEPROM）来检测支持的板卡。您可以通过传递“model”模块选项来覆盖模型，如果驱动程序配置不正确或者您想尝试其他类型以进行测试。

snd-indigo 模块
---------------

用于Echoaudio Indigo的模块

此模块支持多张卡
驱动程序需要内核上的固件加载器支持

snd-indigodj 模块
------------------

用于Echoaudio Indigo DJ的模块

此模块支持多张卡
驱动程序需要内核上的固件加载器支持

snd-indigoio 模块
------------------

用于Echoaudio Indigo IO的模块

此模块支持多张卡
驱动程序需要内核上的固件加载器支持

snd-intel8x0 模块
------------------

用于Intel及兼容AC'97主板的模块
* Intel i810/810E, i815, i820, i830, i84x, MX440 ICH5, ICH6, ICH7, 6300ESB, ESB2
* SiS 7012 (SiS 735)
* NVidia NForce, NForce2, NForce3, MCP04, CK804 CK8, CK8S, MCP501
* AMD AMD768, AMD8111
* ALi m5455

ac97_clock
AC'97 编码时钟基频（0 = 自动检测）

ac97_quirk
AC'97 对于奇怪硬件的工作绕行选项；
请参阅下面的「AC97 Quirk Option」部分
### buggy_irq
启用某些主板上存在问题的中断的工作绕过方案（默认情况下，nForce芯片上为开启，其他情况下为关闭）

### buggy_semaphore
启用针对具有问题信号量硬件的工作绕过方案（例如，在某些ASUS笔记本电脑上）（默认为关闭）

### spdif_aclink
使用AC-link上的S/PDIF而非直接从控制器芯片连接（0 = 关闭，1 = 开启，-1 = 默认）

此模块支持单一芯片和自动探测。
注意：最新驱动程序支持芯片时钟的自动检测。如果仍然遇到播放速度过快的问题，请通过模块选项 `ac97_clock=41194` 明确指定时钟。

本驱动程序不支持游戏杆/MIDI端口。如果您的主板有这些设备，请分别使用ns558或snd-mpu401模块。
支持电源管理。
### Module snd-intel8x0m

此模块用于Intel ICH（i8x0）芯片组MC97调制解调器：
* Intel i810/810E, i815, i820, i830, i84x, MX440 ICH5, ICH6, ICH7
* SiS 7013 (SiS 735)
* NVidia NForce, NForce2, NForce2s, NForce3
* AMD AMD8111
* ALi m5455

### ac97_clock
AC'97编解码器时钟基频（0 = 自动检测）

此模块支持单一卡和自动探测。
注意：此模块的默认索引值为-2，即第一个插槽被排除在外。
支持电源管理。
### Module snd-interwave

此模块适用于基于AMD InterWave™ 芯片的Gravis UltraSound PnP、Dynasonic 3-D/Pro、STB Sound Rage 32和其他声卡。
以下是提供的英文配置选项和模块说明的中文翻译：

### joystick_dac
0 到 31，（0.59V-4.52V 或 0.389V-2.98V）

### midi
1 = 启用 MIDI UART，0 = 禁用 MIDI UART（默认）

### pcm_voices
为合成器预留的 PCM 声道数（默认为 2）

### effect
1 = 启用 InterWave 效果（默认为 0）；需要 8 个声道

### isapnp
ISA 即插即用检测 - 0 = 禁用，1 = 启用（默认）

当 `isapnp=0` 时，以下选项可用：

### port
InterWave 芯片的端口号（0x210、0x220、0x230、0x240、0x250、0x260）

### port_tc
TEA6330T 芯片（I2C 总线）的音调控制端口号（0x350、0x360、0x370、0x380）

### irq
InterWave 芯片的 IRQ 号（3、5、9、11、12、15）

### dma1
InterWave 芯片的 DMA 号（0、1、3、5、6、7）

### dma2
InterWave 芯片的 DMA 号（0、1、3、5、6、7，-1=禁用）

此模块支持多张卡、自动探测以及 ISA 即插即用。

### Module snd-interwave-stb

此模块适用于 UltraSound 32-Pro（来自 STB 的声卡，被康柏使用）以及其他基于 AMD InterWave™ 芯片的声卡，该芯片带有 TEA6330T 电路用于扩展低音、高音和主音量的控制。
- joystick_dac：0 到 31，（0.59V-4.52V 或 0.389V-2.98V）
- midi：1 = 启用 MIDI UART，0 = 禁用 MIDI UART（默认）
- pcm_voices：为合成器预留的 PCM 声道数（默认为 2）
- effect：1 = 启用 InterWave 效果（默认为 0）；需要 8 个声道
- isapnp：ISA 即插即用检测 - 0 = 禁用，1 = 启用（默认）

当 `isapnp=0` 时，以下选项可用：
- port：InterWave 芯片的端口号（0x210、0x220、0x230、0x240、0x250、0x260）
- port_tc：TEA6330T 芯片（I2C 总线）的音调控制端口号（0x350、0x360、0x370、0x380）
- irq：InterWave 芯片的 IRQ 号（3、5、9、11、12、15）
- dma1：InterWave 芯片的 DMA 号（0、1、3、5、6、7）
- dma2：InterWave 芯片的 DMA 号（0、1、3、5、6、7，-1=禁用）

此模块支持多张卡、自动探测以及 ISA 即插即用。

### Module snd-jazz16

此模块适用于 Media Vision Jazz16 芯片组。该芯片组由 3 个芯片组成：MVD1216 + MVA416 + MVA514。
- port：SB DSP 芯片的端口号（0x210、0x220、0x230、0x240、0x250、0x260）
- irq：SB DSP 芯片的 IRQ 号（3、5、7、9、10、15）
- dma8：SB DSP 芯片的 DMA 号（1、3）
- dma16：SB DSP 芯片的 DMA 号（5、7）
- mpu_port：MPU-401 的端口号（0x300、0x310、0x320、0x330）
- mpu_irq：MPU-401 的 IRQ 号（2、3、5、7）

此模块支持多张卡。

### Module snd-korg1212

此模块适用于 Korg 1212 IO PCI 卡。

此模块支持多张卡。

### Module snd-layla20

此模块适用于 Echoaudio Layla20。

此模块支持多张卡。驱动程序要求内核支持固件加载器。

### Module snd-layla24

此模块适用于 Echoaudio Layla24。

此模块支持多张卡。驱动程序要求内核支持固件加载器。
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
    外部放大器的 GPIO 引脚编号（0-15）或 -1 表示使用默认引脚（Allegro 为 8，其他为 1）

此模块支持自动探测和多个芯片
注意：放大器的绑定取决于硬件
如果所有通道都未静音但听不到声音，请尝试通过 `amp_gpio` 选项指定其他 GPIO 连接。
例如，松下笔记本电脑可能需要 `amp_gpio=0x0d` 选项
支持电源管理功能
模块 snd-mia
---------------
用于 Echoaudio Mia 的模块

此模块支持多张卡
驱动程序需要内核上的固件加载器支持
模块 snd-miro
---------------
用于 Miro 声卡：miroSOUND PCM 1 pro、miroSOUND PCM 12、miroSOUND PCM 20 Radio
port
    端口号（0x530、0x604、0xe80、0xf40）
irq
    IRQ 号码（5、7、9、10、11）
dma1
    第一个 DMA 号码（0、1、3）
dma2
    第二个 DMA 号码（0、1）
mpu_port
    MPU-401 端口号（0x300、0x310、0x320、0x330）
mpu_irq
    MPU-401 IRQ 号码（5、7、9、10）
fm_port
    FM 端口号（0x388）
wss
    启用 WSS 模式
ide
    启用板载 IDE 支持

模块 snd-mixart
-----------------
用于 Digigram miXart8 声卡的模块
此模块支持多张声卡。
注意：一个miXart8板将被表示为4张ALSA声卡。
详情请参阅Documentation/sound/cards/mixart.rst。
当驱动程序作为模块编译并且支持热插拔固件时，固件数据会通过热插拔自动加载。
请在alsa-firmware包中安装必要的固件文件。
如果没有可用的热插拔固件加载器，您需要通过alsa-tools包中的mixartloader实用工具来加载固件。

snd-mona 模块
--------------

Echoaudio Mona 的模块。

此模块支持多张声卡。
该驱动程序需要内核上的固件加载器支持。

snd-mpu401 模块
-----------------

MPU-401 UART设备的模块。
端口
    端口号或-1（禁用）
中断请求(IRQ)
    中断请求号或-1（禁用）
即插即用(PnP)
    即插即用检测 - 0 = 禁用, 1 = 启用（默认）

此模块支持多个设备和即插即用功能。
### Module snd-msnd-classic
-----------------------

此模块适用于Turtle Beach MultiSound Classic、Tahiti或Monterey声卡。
io
    MultiSound Classic卡的端口号
irq
    MultiSound Classic卡的IRQ号
mem
    内存地址（0xb0000、0xc8000、0xd0000、0xd8000、0xe0000 或 0xe8000）
write_ndelay
    启用写入无延迟（默认 = 1）
calibrate_signal
    校准信号（默认 = 0）
isapnp
    ISA 即插即用检测 - 0 = 禁用，1 = 启用（默认）
digital
    数字子板存在（默认 = 0）
cfg
    配置端口（0x250、0x260 或 0x270）默认 = 即插即用
reset
    重置所有设备
mpu_io
    MPU401 I/O端口
mpu_irq
    MPU401 IRQ号
ide_io0
    IDE端口#0
ide_io1
    IDE端口#1
ide_irq
    IDE IRQ号
joystick_io
    摇杆I/O端口

驱动程序需要固件文件`turtlebeach/msndinit.bin`和`turtlebeach/msndperm.bin`位于正确的固件目录中。请参阅Documentation/sound/cards/multisound.sh以获取关于此驱动程序的重要信息。请注意，它已被废弃，但Voyetra Turtle Beach知识库条目仍然可以在以下网址获得：
https://www.turtlebeach.com

### Module snd-msnd-pinnacle
------------------------

此模块适用于Turtle Beach MultiSound Pinnacle/Fiji声卡。
io
    Pinnacle/Fiji卡的端口号
irq
    Pinnacle/Fiji卡的IRQ号
mem
    内存地址（0xb0000、0xc8000、0xd0000、0xd8000、0xe0000 或 0xe8000）
write_ndelay
    启用写入无延迟（默认 = 1）
calibrate_signal
    校准信号（默认 = 0）
isapnp
    ISA 即插即用检测 - 0 = 禁用，1 = 启用（默认）

驱动程序需要固件文件`turtlebeach/pndspini.bin`和`turtlebeach/pndsperm.bin`位于正确的固件目录中。

### Module snd-mtpav
-------------------

此模块适用于MOTU MidiTimePiece AV多端口MIDI（位于并行端口上）。
port
    MTPAV的I/O端口号（0x378、0x278，默认=0x378）
irq
    MTPAV的IRQ号（7、5，默认=7）
hwports
    支持的硬件端口数量，默认=8

此模块仅支持一张卡。此模块没有启用选项。

### Module snd-mts64
-------------------

此模块适用于Ego Systems (ESI) Miditerminal 4140。

此模块支持多个设备。
需要parport (`CONFIG_PARPORT`)。

### Module snd-nm256
-------------------

此模块适用于NeoMagic NM256AV/ZX芯片。

playback_bufsize
    最大播放帧大小（千字节）（4-128kB）
capture_bufsize
    最大捕获帧大小（千字节）（4-128kB）
force_ac97
    0 或 1（默认禁用）
buffer_top
    指定缓冲区顶部地址
use_cache
    0 或 1（默认禁用）
vaio_hack
    别名 buffer_top=0x25a800
reset_workaround
    为某些笔记本电脑启用AC97重置规避
reset_workaround2
    为其他一些笔记本电脑启用扩展的AC97重置规避

此模块支持一个芯片并自动探测。
电源管理得到了支持。

注意：在某些笔记本电脑上，无法自动检测缓冲区地址，或者会在初始化过程中导致系统挂起。
在这种情况下，请通过 `buffer_top` 选项明确指定缓冲区顶部地址。
例如，
Sony F250: buffer_top=0x25a800
Sony F270: buffer_top=0x272800
驱动程序仅支持 AC97 编解码器。即使没有检测到 AC97，也可以强制初始化/使用 AC97。在这种情况下，请使用 `force_ac97=1` 选项 —— 但是不保证是否有效！

注意：NM256 芯片可以与非 AC97 编解码器内部连接。此驱动程序仅支持 AC97 编解码器，因此对于使用其他芯片（最有可能是 CS423x 或 OPL3SAx）的机器将不起作用，尽管设备在 lspci 中被检测到。在这种情况下，请尝试其他驱动程序，例如 snd-cs4232 或 snd-opl3sa2。有些有 ISA-PnP 支持，但有些没有。如果没有 ISA PnP，则需要指定 `isapnp=0` 和正确的硬件参数。
注意：某些笔记本电脑需要对 AC97 重置进行变通处理。对于已知的硬件，如 Dell Latitude LS 和 Sony PCG-F305，这种变通处理会自动启用。对于其他出现严重冻结问题的笔记本电脑，您可以尝试使用 `reset_workaround=1` 选项。
注意：Dell Latitude CSx 笔记本电脑有关于 AC97 重置的另一个问题。对于这些笔记本电脑，默认启用了 reset_workaround2 选项。如果之前提到的 reset_workaround 选项没有帮助，这个选项值得一试。
注意：此驱动程序真的很差。它是从 OSS 驱动程序移植过来的，而 OSS 驱动程序则是通过黑魔法逆向工程的结果。如果按照上述说明，在加载 X-server 之后再加载此驱动程序，那么编解码器的检测可能会失败。您可能能够强制加载模块，但这可能会导致系统挂起。因此，如果您遇到此类问题，请确保在启动 X 之前加载此模块。

### 模块 snd-opl3sa2
#### 

为 Yamaha OPL3-SA2/SA3 声卡提供的模块

isapnp
    ISA PnP 检测 - 0 = 禁用, 1 = 启用（默认）

使用 `isapnp=0` 时，以下选项可用：

port
    OPL3-SA 芯片的控制端口号（0x370）
sb_port
    OPL3-SA 芯片的 SB 端口号（0x220,0x240）
wss_port
    OPL3-SA 芯片的 WSS 端口号（0x530,0xe80,0xf40,0x604）
midi_port
    MPU-401 UART 的端口号（0x300,0x330），-1 = 禁用
fm_port
    OPL3-SA 芯片的 FM 端口号（0x388），-1 = 禁用
irq
    OPL3-SA 芯片的 IRQ 号（5,7,9,10）
dma1
    Yamaha OPL3-SA 芯片的第一个 DMA 号（0,1,3）
dma2
    Yamaha OPL3-SA 芯片的第二个 DMA 号（0,1,3），-1 = 禁用

此模块支持多张声卡和 ISA PnP。如果不使用 ISA PnP，则不支持自动探测，因此必须指定所有端口！

电源管理得到了支持。
### Module snd-opti92x-ad1848
-------------------------------

基于 OPTi 82c92x 和 Analog Devices AD1848 芯片的声音卡模块。
此模块也适用于 OAK Mozart 卡。
isapnp  
    ISA 插即用检测 — 0 = 禁用，1 = 启用（默认）

使用 `isapnp=0` 时，以下选项可用：

port  
    为 WSS 芯片指定的端口号（0x530、0xe80、0xf40、0x604）
mpu_port  
    为 MPU-401 UART 指定的端口号（0x300、0x310、0x320、0x330）
fm_port  
    为 OPL3 设备指定的端口号（0x388）
irq  
    为 WSS 芯片指定的中断请求号（IRQ）（5、7、9、10、11）
mpu_irq  
    为 MPU-401 UART 指定的中断请求号（IRQ）（5、7、9、10）
dma1  
    为 WSS 芯片指定的第一个直接内存访问（DMA）号（0、1、3）

此模块仅支持一张卡，并支持自动探测和插即用。

### Module snd-opti92x-cs4231
-------------------------------

基于 OPTi 82c92x 和 Crystal CS4231 芯片的声音卡模块。
isapnp  
    ISA 插即用检测 — 0 = 禁用，1 = 启用（默认）

使用 `isapnp=0` 时，以下选项可用：

port  
    为 WSS 芯片指定的端口号（0x530、0xe80、0xf40、0x604）
mpu_port  
    为 MPU-401 UART 指定的端口号（0x300、0x310、0x320、0x330）
fm_port  
    为 OPL3 设备指定的端口号（0x388）
irq  
    为 WSS 芯片指定的中断请求号（IRQ）（5、7、9、10、11）
mpu_irq  
    为 MPU-401 UART 指定的中断请求号（IRQ）（5、7、9、10）
dma1  
    为 WSS 芯片指定的第一个直接内存访问（DMA）号（0、1、3）
dma2  
    为 WSS 芯片指定的第二个直接内存访问（DMA）号（0、1、3）

此模块仅支持一张卡，并支持自动探测和插即用。

### Module snd-opti93x
------------------------------

基于 OPTi 82c93x 芯片的声音卡模块。
isapnp  
    ISA 插即用检测 — 0 = 禁用，1 = 启用（默认）

使用 `isapnp=0` 时，以下选项可用：

port  
    为 WSS 芯片指定的端口号（0x530、0xe80、0xf40、0x604）
mpu_port  
    为 MPU-401 UART 指定的端口号（0x300、0x310、0x320、0x330）
fm_port  
    为 OPL3 设备指定的端口号（0x388）
irq  
    为 WSS 芯片指定的中断请求号（IRQ）（5、7、9、10、11）
mpu_irq  
    为 MPU-401 UART 指定的中断请求号（IRQ）（5、7、9、10）
dma1  
    为 WSS 芯片指定的第一个直接内存访问（DMA）号（0、1、3）
dma2  
    为 WSS 芯片指定的第二个直接内存访问（DMA）号（0、1、3）

此模块仅支持一张卡，并支持自动探测和插即用。

### Module snd-oxygen
------------------------------

基于 C-Media CMI8786/8787/8788 芯片的声音卡模块：

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

### Module snd-pcsp
------------------------------

内部 PC 喇叭模块
nopcm  
    禁用 PC 喇叭的 PCM 音频。仅保留蜂鸣声。
nforce_wa  
    启用 NForce 芯片组的解决方案。预期音质不佳。
此模块支持系统蜂鸣声、某种 PCM 播放，甚至一些混音器控制功能。
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

适用于 PowerMac、iMac 和 iBook 的板载音效芯片模块

enable_beep  
    使用 PCM 启用蜂鸣声（默认启用）

此模块支持自动探测芯片
注意：该驱动可能有关于字节顺序的问题
支持电源管理
Module snd-pxa2xx-ac97（仅限于 arm）
------------------------------------

Intel PXA2xx 芯片的 AC97 驱动模块

仅限 ARM 架构
支持电源管理
Module snd-riptide
------------------

Conexant Riptide 芯片模块

joystick_port  
    游戏杆端口号（默认：0x200）
mpu_port  
    MPU401 端口号（默认：0x330）
opl3_port  
    OPL3 端口号（默认：0x388）

此模块支持多张卡
驱动程序需要内核上的固件加载器支持。
您需要将固件文件 `riptide.hex` 安装到标准固件路径（例如 `/lib/firmware`）。

### 模块 snd-rme32
---

适用于 RME Digi32、Digi32 Pro 和 Digi32/8（Sek'd Prodif32、
Prodif96 和 Prodif Gold）声卡的模块。
此模块支持多张声卡。

### 模块 snd-rme96
---

适用于 RME Digi96、Digi96/8 和 Digi96/8 PRO/PAD/PST 声卡的模块。
此模块支持多张声卡。

### 模块 snd-rme9652
---

适用于 RME Digi9652（Hammerfall、Hammerfall-Light）声卡的模块。

- **precise_ptr**
  - 启用精确指针（可能无法可靠工作）。 （默认值 = 0）

此模块支持多张声卡。

**注意：**snd-page-alloc 模块执行了以前由 snd-hammerfall-mem 模块完成的工作。当发现任何 RME9652 声卡时，它会提前分配缓冲区。为了确保缓冲区的分配，请在启动序列的早期加载 snd-page-alloc 模块。请参阅 `Early Buffer Allocation`_ 部分。

### 模块 snd-sa11xx-uda1341（仅限 ARM）
---

适用于 Compaq iPAQ H3600 声卡上的 Philips UDA1341TS 的模块。
模块仅支持一张卡  
模块没有启用和索引选项  
支持电源管理  
模块 snd-sb8  
----------------  

### 8位SoundBlaster声卡模块：SoundBlaster 1.0、SoundBlaster 2.0、SoundBlaster Pro

port  
    SB DSP芯片的端口号（0x220、0x240、0x260）  
irq  
    SB DSP芯片的IRQ号（5、7、9、10）  
dma8  
    SB DSP芯片的8位DMA号（1、3）  

此模块支持多张卡和自动探测功能  
支持电源管理  
模块 snd-sb16 和 snd-sbawe  
----------------  

### 16位SoundBlaster声卡模块：SoundBlaster 16（即插即用）、SoundBlaster AWE 32（即插即用）、SoundBlaster AWE 64 即插即用

mic_agc  
    麦克风自动增益控制 —— 0 = 禁用，1 = 启用（默认）  
csp  
    ASP/CSP芯片支持 —— 0 = 禁用（默认），1 = 启用  
isapnp  
    ISA即插即用检测 —— 0 = 禁用，1 = 启用（默认）  

如果设置 isapnp=0，则以下选项可用：

port  
    SB DSP 4.x 芯片的端口号（0x220、0x240、0x260）  
mpu_port  
    MPU-401 UART 的端口号（0x300、0x330），-1 = 禁用  
awe_port  
    EMU8000 合成器的基础端口号（0x620、0x640、0x660）（仅适用于 snd-sbawe 模块）  
irq  
    SB DSP 4.x 芯片的IRQ号（5、7、9、10）  
dma8  
    SB DSP 4.x 芯片的8位DMA号（0、1、3）  
dma16  
    SB DSP 4.x 芯片的16位DMA号（5、6、7）  

此模块支持多张卡、自动探测和ISA即插即用  
注意：为了在16位半双工模式下使用Vibra16X卡，必须通过设置 dma16 = -1 参数来禁用16位DMA。此外，所有Sound Blaster 16 类型的卡都可以通过禁用其16位DMA通道并通过8位DMA通道工作在16位半双工模式下。  
支持电源管理  
模块 snd-sc6000  
----------------  

### Gallant SC-6000 声卡及其后续型号 SC-6600 和 SC-7000 的模块
这段文本描述了几个不同的音频模块及其配置选项。以下是翻译成中文的版本：

### 端口
- **端口号**（0x220 或 0x240）
- **MSS端口号**（0x530 或 0xe80）
- **IRQ号**（5、7、9、10、11）
- **MPU-401 IRQ号**（5、7、9、10），0表示没有MPU-401 IRQ
- **DMA号**（1、3、0）
- **游戏端口**——启用游戏端口：0 = 关闭（默认），1 = 开启

此模块支持多张声卡。

这张声卡也被称为Audio Excel DSP 16或Zoltrix AV302。

### 模块snd-sscape
-----------------
用于ENSONIQ SoundScape声卡的模块。
- **端口号**（即插即用设置）
- **WSS端口号**（即插即用设置）
- **IRQ号**（即插即用设置）
- **MPU-401 IRQ号**（即插即用设置）
- **DMA号**（即插即用设置）
- **第二个DMA号**（即插即用设置，-1以禁用）
- **游戏端口**——启用游戏端口：0 = 关闭（默认），1 = 开启

此模块支持多张声卡。

驱动程序需要内核上的固件加载器支持。

### 模块snd-sun-amd7930（仅sparc平台）
--------------------------------------
用于sparc平台上AMD7930音频芯片的模块。

此模块支持多张声卡。

### 模块snd-sun-cs4231（仅sparc平台）
-------------------------------------
用于sparc平台上CS4231音频芯片的模块。

此模块支持多张声卡。

### 模块snd-sun-dbri（仅sparc平台）
-----------------------------------
用于sparc平台上DBRI音频芯片的模块。
此模块支持多张声卡。
snd-wavefront 模块
--------------------
用于Turtle Beach Maui、Tropez和Tropez+声卡的模块
use_cs4232_midi
    使用CS4232 MPU-401接口
    （位于计算机内部，无法直接访问）
isapnp
    ISA即插即用检测 - 0 = 禁用，1 = 启用（默认）

在isapnp=0的情况下，以下选项可用：

cs4232_pcm_port
    CS4232 PCM接口的端口号
cs4232_pcm_irq
    CS4232 PCM接口的IRQ号（5、7、9、11、12、15）
cs4232_mpu_port
    CS4232 MPU-401接口的端口号
cs4232_mpu_irq
    CS4232 MPU-401接口的IRQ号（9、11、12、15）
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

以下是关于wavefront_synth特性的选项：

wf_raw
    假设我们需要启动操作系统（默认：否）；
    如果是，则在加载驱动程序时，会忽略声卡的状态，
    并且无论如何都会重置声卡并加载固件
fx_raw
    假设FX处理过程需要帮助（默认：是）；
    如果为假，则加载驱动程序时将保留FX处理器的当前状态。
    默认情况下，会下载微程序及其相关系数以设置FX处理器进行
    “默认”操作，无论这具体意味着什么。
### debug_default
调试参数用于卡片初始化。

### wait_usecs
在不进行睡眠的情况下等待的时间（微秒，默认：150）；
这个数值似乎是基于我有限的实验得出的一个相对最优的吞吐量。如果你想尝试调整它以找到一个更好的值，欢迎尝试。记住，目标是找到一个尽可能让我们对WaveFront命令进行繁忙等待的数字，但又不要太大以至于占用整个CPU。
具体来说，使用这个数值，在大约134,000次状态等待中，只有大约250次会导致睡眠。

### sleep_interval
等待回复时睡眠的时间（默认：100）。

### sleep_tries
等待过程中尝试睡眠的次数（默认：50）。

### ospath
处理过的ICS2115操作系统固件的路径名（默认：wavefront.os）；
在较新版本中，它是通过固件加载器框架处理的，因此必须安装在正确的路径下，通常是`/lib/firmware`。

### reset_time
重置生效需要等待的时间（默认：2）。

### ramcheck_time
RAM测试需要等待的秒数（默认：20）。

### osrun_time
等待ICS2115操作系统运行需要的秒数（默认：10）。

### 模块支持多张卡片和ISA PnP
注意：固件文件`wavefront.os`在早期版本中位于`/etc`目录下。现在它通过固件加载器加载，并且必须位于正确的固件路径下，例如`/lib/firmware`。如果升级内核后遇到有关固件下载的错误，请适当地复制（或创建符号链接）该文件。

### Module snd-sonicvibes
S3 SonicVibes PCI声卡模块
* PINE Schubert 32 PCI

#### reverb
回声启用 - 1 = 启用，0 = 禁用（默认）；声卡必须具有板载SRAM才能启用此功能。

#### mge
麦克风增益启用 - 1 = 启用，0 = 禁用（默认）

此模块支持多张卡片和自动探测。

### Module snd-serial-u16550
UART16550A串行MIDI端口模块
#### port
UART16550A芯片的端口号。

#### irq
UART16550A芯片的中断请求号，-1表示轮询模式。

#### speed
波特率速度（9600, 19200, 38400, 57600, 115200），默认为38400。

#### base
波特率除数的基础值（57600, 115200, 230400, 460800），默认为115200。

#### outs
串行端口中MIDI端口的数量（1-4），默认为1。

#### adaptor
适配器类型
0 = Soundcanvas, 1 = MS-124T, 2 = MS-124W S/A, 3 = MS-124W M/B, 4 = Generic

此模块支持多张卡片。此模块不支持自动探测，因此必须指定主端口！其他选项为可选。
### Module snd-trident
------------------

Trident 4DWave DX/NX 声卡模块
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
		   
`pcm_channels`
    为 PCM 预留的最大声道数（音轨）
`wavetable_size`
    最大波表大小（以千字节为单位，4-？kb）

此模块支持多张声卡和自动探测
支持电源管理功能
### Module snd-ua101
----------------

Edirol UA-101/UA-1000 音频/MIDI 接口模块
此模块支持多个设备、自动探测和热插拔
### Module snd-usb-audio
--------------------

USB 音频和 USB MIDI 设备模块
`vid`
    设备的供应商 ID（可选）
`pid`
    设备的产品 ID（可选）
`nrpacks`
    每个 URB 的最大包数（默认：8）
`device_setup`
    特定于设备的魔术数字（可选）；其影响取决于设备
    默认值：0x0000
`ignore_ctl_error`
    忽略与混音器接口相关的任何 USB 控制器错误（默认：否）
`autoclock`
    为 UAC2 设备启用自动时钟选择（默认：是）
`quirk_alias`
    Quirk 别名列表，传递字符串如 ``0123abcd:5678beef``，将应用现有设备 5678:beef 的 quirk 到新设备 0123:abcd 上
`implicit_fb`
    应用通用的隐式反馈同步模式。当设置此选项且播放流的同步模式为 ASYNC 时，驱动程序尝试将相邻的 ASYNC 录音流作为隐式反馈源。这等同于 quirk_flags 的第 17 位
`use_vmalloc`
    使用 vmalloc() 为 PCM 缓冲区分配内存（默认：是）
对于像 ARM 或 MIPS 这样的不一致内存架构，使用 vmalloc 分配的缓冲区进行 mmap 访问可能会导致不一致的结果。如果在这样的架构上使用 mmap，请关闭此选项，以便分配并使用 DMA 一致性缓冲区。
### 延迟注册 (delayed_register)

此选项适用于那些在多个USB接口中定义了多条流的设备。驱动程序可能会多次调用注册（每个接口一次），这可能导致设备枚举不充分。

此选项接收一个字符串数组，您可以传递类似 `0123abcd:4` 的 `ID:INTERFACE` 格式来对给定设备执行延迟注册。例如，当探测到 USB 设备 `0123:abcd` 时，驱动程序会等待直到 USB 接口 4 被探测后才进行注册。

对于此类设备，驱动程序会打印一条消息，如 "发现延迟注册设备分配: 1234abcd:04"，以便用户能够注意到需要这样做。

### 特殊标志 (quirk_flags)
包含针对各种特定设备的修正措施的位标志。

应用于相应的卡索引：
* 位 0: 对于设备跳过读取采样率
* 位 1: 创建媒体控制器API条目
* 位 2: 允许音频子槽传输时的对齐
* 位 3: 在传输中添加长度指定符
* 位 4: 实现反馈模式下从第一个开始播放流
* 位 5: 跳过时钟选择器设置
* 位 6: 忽略来自时钟源搜索的错误
* 位 7: 表示基于ITF-USB DSD的DAC
* 位 8: 每次处理控制消息时增加20毫秒的延迟
* 位 9: 每次处理控制消息时增加1-2毫秒的延迟
* 位 10: 每次处理控制消息时增加5-6毫秒的延迟
* 位 11: 每个接口设置时增加50毫秒的延迟
* 位 12: 在探测时执行采样率验证
* 位 13: 禁用运行时PM自动暂停
* 位 14: 忽略混音器访问的错误
* 位 15: 支持通用DSD原始U32_BE格式
* 位 16: 探测时像UAC1一样设置接口
* 位 17: 应用通用隐式反馈同步模式
* 位 18: 不应用隐式反馈同步模式

### 模块支持
本模块支持多个设备、自动探测和热插拔。

**注意：**
- `nrpacks` 参数可以通过 sysfs 动态修改。不要设置超过 20 的值。通过 sysfs 修改没有合理性检查。
- 如果在访问混音器元素（如 URB 错误 -22）时遇到错误，`ignore_ctl_error=1` 可能会有帮助。这种情况可能发生在某些有缺陷的 USB 设备或控制器上。此修正措施对应 `quirk_flags` 中的位 14。
- `quirk_alias` 选项仅用于测试/开发目的。
如果你需要得到适当的支持，请联系上游开发者，以便在驱动程序代码中静态地添加匹配的特殊处理。
对于`quirk_flags`也是如此。如果已知某个设备需要特定的变通方法，请向上游报告。

### 模块snd-usb-caiaq

这是针对caiaq UB音频接口的模块，

* Native Instruments RigKontrol2
* Native Instruments Kore Controller
* Native Instruments Audio Kontrol 1
* Native Instruments Audio 8 DJ

此模块支持多个设备、自动探测和热插拔。

### 模块snd-usb-usx2y

这是针对Tascam USB US-122、US-224 和 US-428 设备的模块。
此模块支持多个设备、自动探测和热插拔。
注意：你需要通过`alsa-tools`和`alsa-firmware`包中的`usx2yloader`工具加载固件。

### 模块snd-via82xx

这是基于VIA 82C686A/686B、8233、8233A、8233C、8235、8237（南桥）的AC'97主板模块。

- **mpu_port**
  - 0x300, 0x310, 0x320, 0x330，否则请从BIOS设置中获取
  - [仅限VIA686A/686B]

- **joystick**
  - 启用游戏杆（默认关闭）
  - [仅限VIA686A/686B]

- **ac97_clock**
  - AC'97编解码器时钟基频（默认48000Hz）

- **dxs_support**
  - 支持DXS通道，0=自动（默认），1=启用，2=禁用，3=仅48k，4=无VRA，5=启用任何采样率并在不同通道上使用不同的采样率
  - [仅限VIA8233/C, 8235, 8237]

- **ac97_quirk**
  - AC'97硬件异常的变通方法；参见下面的“AC97 Quirk Option”部分

此模块支持一个芯片和自动探测。

**注意**：在一些SMP主板（如MSI 694D）上，中断可能无法正确生成。在这种情况下，请尝试在BIOS中将SMP（或MPS）版本设置为1.1而不是默认的1.4。这样中断号将被分配到15以下。你也可以考虑升级你的BIOS。
注：VIA8233/5/7（而非VIA8233A）可以支持DXS（直接声音）通道作为第一个PCM。在这些通道上，最多可以同时播放4个流，并且控制器可以在每个通道上以独立的速率执行采样率转换。

默认情况下（`dxs_support = 0`），除了已知设备外，通常会选择48kHz的固定速率，因为有些主板由于BIOS的问题，除非设置为48kHz，否则输出往往会有噪音。

请尝试一次使用`dxs_support=5`，如果它能在其他采样率（例如MP3播放时的44.1kHz）下工作，请告知我们PCI子系统的供应商/设备ID（通过运行`lspci -nv`获得的输出）。

如果`dxs_support=5`不起作用，尝试`dxs_support=4`；如果也不行，尝试`dxs_support=1`。（`dxs_support=1`通常是为旧型号主板准备的。正确实现的主板应该能用4或5。）如果还是不行，并且默认设置是可以接受的，则`dxs_support=3`是正确的选择。如果默认设置完全不起作用，尝试`dxs_support=2`来禁用DXS通道。

无论哪种情况，请告知我们结果以及子系统的供应商/设备ID。请参见下方的“链接和地址”。

注：对于VIA823x上的MPU401，需要另外使用snd-mpu401驱动。mpu_port选项仅适用于VIA686芯片。

支持电源管理功能。

### snd-via82xx-modem 模块

#### VIA82xx AC97调制解调器模块

- **ac97_clock**
  - AC'97编解码器时钟基频（默认48000Hz）

此模块支持一张卡和自动探测。
注：此模块的默认索引值为-2，即排除第一个插槽。
支持电源管理功能。
模块 snd-virmidi
------------------

虚拟原始midi设备的模块
此模块创建与对应的ALSA序列器端口通信的虚拟原始midi设备
midi_devs
    MIDI 设备数量 #(1-4，默认=4)

此模块支持多张声卡
模块 snd-virtuoso
-------------------

基于 Asus AV66/AV100/AV200 芯片的声卡模块，例如：Xonar D1、DX、D2、D2X、DS、DSX、Essence ST (Deluxe)、Essence STX (II)、HDAV1.3 (Deluxe) 和 HDAV1.3 Slim
此模块支持自动探测和多张声卡
模块 snd-vx222
----------------

Digigram VX-Pocket VX222、V222 v2 和 Mic 卡的模块
mic
    启用 V222 Mic 上的麦克风 (暂未实现)
ibl
    捕获 IBL 大小。 (默认 = 0，最小大小)

此模块支持多张声卡
当驱动程序作为模块编译且支持热插拔固件时，固件数据会通过热插拔自动加载
请在 alsa-firmware 包中安装必要的固件文件
如果没有可用的热插拔固件加载器，您需要使用 alsa-tools 包中的 vxloader 实用程序加载固件。为了自动调用 vxloader，请在 /etc/modprobe.d/alsa.conf 中添加以下内容：

::

  install snd-vx222 /sbin/modprobe --first-time -i snd-vx222\
    && /usr/bin/vxloader

（对于 2.2/2.4 内核，在 /etc/modules.conf 中添加 `post-install /usr/bin/vxloader` 代替。）
IBL 大小定义了 PCM 的中断周期。更小的大小会导致更低的延迟，但也会导致更高的 CPU 使用率。
大小通常与126对齐。默认值（=0）时，选择最小的大小。可能的IBL值可以在`/proc/asound/cardX/vx-status`这个进程文件中找到。
支持电源管理。
snd-vxpocket模块
-------------------
适用于Digigram VX-Pocket VX2和440 PCMCIA卡的模块。
ibl
    采集IBL大小。（默认 = 0，即最小大小）

此模块支持多张卡。只有当内核支持PCMCIA时才会编译该模块。
对于较旧的2.6.x内核，要通过卡管理器激活驱动程序，需要设置`/etc/pcmcia/vxpocket.conf`。请参阅`sound/pcmcia/vx/vxpocket.c`。2.6.13或更高版本的内核不再需要配置文件。
当驱动程序被编译为模块并且支持热插拔固件时，固件数据将通过热插拔自动加载。
请在alsa-firmware包中安装必要的固件文件。
如果没有可用的热插拔固件加载器，则需要通过alsa-tools包中的vxloader实用工具来加载固件。
关于采集IBL的更多信息，请参见snd-vx222模块的描述。
注意：自ALSA 1.0.10起，snd-vxp440驱动程序已合并到snd-vxpocket驱动程序中。
电源管理功能得到支持。
snd-ymfpci 模块
-----------------
用于 Yamaha PCI 芯片（YMF72x, YMF74x 和 YMF75x）的模块
mpu_port
    默认为 0x300、0x330、0x332、0x334，0（禁用），
    1（仅对 YMF744/754 自动检测）
fm_port
    默认为 0x388、0x398、0x3a0、0x3a8，0（禁用）
    1（仅对 YMF744/754 自动检测）
joystick_port
    默认为 0x201、0x202、0x204、0x205，0（禁用），
    1（自动检测）
rear_switch
    启用共享后置/线路输入开关（布尔值）

此模块支持自动探测和多芯片
电源管理功能得到支持。
snd-pdaudiocf 模块
--------------------
用于 Sound Core PDAudioCF 声卡的模块
电源管理功能得到支持。
AC97 特殊处理选项
=================

ac97_quirk 选项用于启用/覆盖针对主板 AC'97 控制器（如 snd-intel8x0）上特定设备的解决方法。某些硬件在 Master 输出和耳机输出之间或环绕声输出之间交换了引脚（这归咎于 AC'97 规范版本间的混淆）。

驱动程序提供了已知问题设备的自动检测功能，但有些设备可能未知或被错误地检测到。在这种情况下，请使用此选项传递正确的值。
以下字符串是可接受的：

default
    不覆盖默认设置
none
    禁用特殊处理
hp_only
    将 Master 和耳机控制绑定为单一控制
swap_hp
    交换耳机和主控
swap_surround
    交换主控和环绕声控制
ad_sharing
    对于 AD1985，打开 OMS 位并使用耳机
alc_jack
    对于 ALC65x，打开麦克风插孔感应模式
inv_eapd
    反转 EAPD 实现
mute_led
    将 EAPD 位绑定用于开关静音指示灯

为了保持向后兼容性，也接受对应的整数值 -1、0 等
例如，如果您的设备上“Master”音量控制没有效果而只有“Headphone”有效，则应传递 ac97_quirk=hp_only 模块选项。
### 配置非ISAPNP卡
=================================

当内核配置了ISA-PnP支持时，支持ISAPNP卡的模块将具有模块选项`isapnp`。如果设置了此选项，则*仅*探测ISA-PnP设备。为了探测非ISA-PnP卡，你必须传递`isapnp=0`选项，同时还需要正确的I/O和IRQ配置。当内核没有配置ISA-PnP支持时，不会内置`isapnp`选项。

### 模块自动加载支持
=================================

ALSA驱动可以通过定义模块别名来实现按需自动加载。对于ALSA原生设备，请求字符串为`snd-card-%i`，其中`%i`代表从0到7的声卡编号。为了自动加载用于OSS服务的ALSA驱动，可以定义字符串`sound-slot-%i`，其中`%i`表示OSS中的插槽编号，这对应于ALSA中的声卡索引。通常，将其定义为相同的声卡模块。

下面是一个单个emu10k1卡的示例配置：
```plaintext
----- /etc/modprobe.d/alsa.conf
alias snd-card-0 snd-emu10k1
alias sound-slot-0 snd-emu10k1
----- /etc/modprobe.d/alsa.conf
```

可自动加载的声卡数量取决于`snd`模块的模块选项`cards_limit`。默认情况下，其值设置为1。为了启用多个声卡的自动加载，可以在该选项中指定声卡的数量。

当有多个声卡可用时，最好也通过模块选项指定每个声卡的索引号，以便保持声卡顺序的一致性。

下面是两个声卡的示例配置：
```plaintext
----- /etc/modprobe.d/alsa.conf
# ALSA部分
options snd cards_limit=2
alias snd-card-0 snd-interwave
alias snd-card-1 snd-ens1371
options snd-interwave index=0
options snd-ens1371 index=1
# OSS/Free部分
alias sound-slot-0 snd-interwave
alias sound-slot-1 snd-ens1371
----- /etc/modprobe.d/alsa.conf
```

在此示例中，interwave卡始终作为第一张卡（索引0）加载，而ens1371作为第二张卡（索引1）加载。
一种替代（且新颖）的插槽分配固定方法是使用snd模块的`slots`选项。以上述情况为例，可以像下面这样指定：
::
    options snd slots=snd-interwave,snd-ens1371

这样一来，第一个插槽（#0）为snd-interwave驱动保留，第二个插槽（#1）则为snd-ens1371驱动预留。如果使用了`slots`选项，可以在每个驱动中省略索引选项（尽管只要它们不冲突，你仍然可以同时拥有这两个选项）。
`slots`选项特别有助于避免可能发生的热插拔及其导致的插槽冲突问题。例如，在上述情况下，前两个插槽已经预留。如果其他驱动程序（如snd-usb-audio）在snd-interwave或snd-ens1371之前加载，它将被分配到第三个或之后的插槽上。
当模块名称前加上'!'时，该插槽将为除了该名称以外的所有模块保留。例如，`slots=!snd-pcsp`会为除了snd-pcsp之外的所有模块预留第一个插槽。

ALSA PCM设备到OSS设备的映射
=======================================
::
    /dev/snd/pcmC0D0[c|p]  -> /dev/audio0 (/dev/audio) -> minor 4
    /dev/snd/pcmC0D0[c|p]  -> /dev/dsp0 (/dev/dsp)     -> minor 3
    /dev/snd/pcmC0D1[c|p]  -> /dev/adsp0 (/dev/adsp)   -> minor 12
    /dev/snd/pcmC1D0[c|p]  -> /dev/audio1              -> minor 4+16 = 20
    /dev/snd/pcmC1D0[c|p]  -> /dev/dsp1                -> minor 3+16 = 19
    /dev/snd/pcmC1D1[c|p]  -> /dev/adsp1               -> minor 12+16 = 28
    /dev/snd/pcmC2D0[c|p]  -> /dev/audio2              -> minor 4+32 = 36
    /dev/snd/pcmC2D0[c|p]  -> /dev/dsp2                -> minor 3+32 = 39
    /dev/snd/pcmC2D1[c|p]  -> /dev/adsp2               -> minor 12+32 = 44

`/dev/snd/pcmC{X}D{Y}[c|p]`表达式中的第一个数字表示声卡编号，第二个数字表示设备编号。ALSA设备具有`c`或`p`后缀，分别表示捕获方向和播放方向。
请注意，上述设备映射可能会通过snd-pcm-oss模块的选项进行更改。
Proc接口（/proc/asound）
==============================

/proc/asound/card#/pcm#[cp]/oss
-------------------------------
erase
    清除所有有关OSS应用程序的额外信息。

<app_name> <fragments> <fragment_size> [<options>]
    <app_name>
	应用名称，可以带路径（优先级更高）或不带路径
    <fragments>
	片段数量或零（自动）
    <fragment_size>
	片段大小（以字节为单位）或零（自动）
    <options>
	可选参数

	disable
	    应用程序尝试为此通道打开PCM设备但并不想使用它
	    （可能导致bug或mmap问题）
	    对Quake等游戏而言这是个不错的选择
	direct
	    不使用插件
	block
	     强制使用阻塞模式（适用于rvplayer）
	non-block
	    强制使用非阻塞模式
	whole-frag
	    仅写入完整片段（只影响播放，用于优化）
	no-silence
	    避免咔哒声，不预先填充静音
	buggy-ptr
	    在GETOPTR ioctl中返回空白块而不是已填充块

示例：
::
    echo "x11amp 128 16384" > /proc/asound/card0/pcm0p/oss
    echo "squake 0 0 disable" > /proc/asound/card0/pcm0c/oss
    echo "rvplayer 0 0 block" > /proc/asound/card0/pcm0p/oss

早期缓冲区分配
=======================

某些驱动程序（如hdsp）需要较大的连续缓冲区，并且有时当实际加载驱动程序模块时寻找这些空间太晚了，因为内存碎片化的问题。你可以通过加载snd-page-alloc模块并在更早的阶段（例如在`/etc/init.d/*.local`脚本中）向其proc文件写入命令来预分配PCM缓冲区。
读取proc文件`/proc/drivers/snd-page-alloc`可以查看当前页面分配的使用情况。写入时，可以向snd-page-alloc驱动发送以下命令：

* add VENDOR DEVICE MASK SIZE BUFFERS

VENDOR和DEVICE是PCI供应商和设备ID。它们接受整数（对于十六进制值需要0x前缀）
MASK是PCI DMA掩码。如果不受限则传递0
SIZE是要分配的每个缓冲区的大小。你可以传递k和m后缀表示KB和MB。最大数值为16MB
`BUFFERS` 是要分配的缓冲区数量。它必须大于 0。最大数量是 4。

* `erase`

这将清除所有未使用到的预分配缓冲区。

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
