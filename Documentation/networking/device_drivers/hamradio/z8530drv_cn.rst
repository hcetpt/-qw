这是驱动文档的一部分。要使用此驱动程序，您必须从以下位置获取完整包：

互联网上:

1. `ftp://ftp.ccac.rwth-aachen.de/pub/jr/z8530drv-utils_3.0-3.tar.gz`

2. `ftp://ftp.pspt.fi/pub/ham/linux/ax25/z8530drv-utils_3.0-3.tar.gz`

请注意，本文档中的信息可能已经过时。最新的文档版本以及指向其他重要的 Linux 内核 AX.25 文档和程序的链接可在 http://yaina.de/jreuter 上找到。

版权所有 © 1993,2000 乔格·雷特尔（Joerg Reuter DL1BKE）<jreuter@yaina.de>

部分版权 © 1993 格伊多·滕·多勒（Guido ten Dolle PE1NNZ）

完整的版权声明请参见“Copying.Z8530DRV”。

1. 驱动程序初始化
==================

要使用该驱动程序，需要执行以下三个步骤：

1. 如果作为模块编译：加载模块
2. 使用 sccinit 设置硬件、MODEM 和 KISS 参数
3. 通过 "ifconfig" 将每个通道连接到 Linux 内核 AX.25

与 2.4 版本之前的版本不同，此驱动程序是一个真正的网络设备驱动程序。如果您想要运行 xNOS 而不是我们优秀的内核 AX.25，请使用 2.x 版本（可从上述站点获得），或者阅读 AX.25-HOWTO 了解如何在网络设备驱动程序上模拟 KISS TNC。
1.1 加载模块
=============

（如果您打算将驱动程序作为内核镜像的一部分进行编译，请跳过本章，直接进入 1.2）

在可以使用模块之前，您需要使用以下命令加载它：

```sh
insmod scc.o
```

请阅读随模块初始化工具一起提供的 `man insmod` 命令手册。
您应该在 `/etc/rc.d/rc.*` 文件之一中包含 `insmod` 命令，并且不要忘记之后调用 `sccinit`。它会读取您的 `/etc/z8530drv.conf` 文件。
1.2 `/etc/z8530drv.conf`
========================

为了设置所有参数，您必须从您的 `rc.*` 文件之一中运行 `/sbin/sccinit`。这必须在您能够使用 `ifconfig` 命令配置接口之前完成。`sccinit` 会读取文件 `/etc/z8530drv.conf` 并设置硬件、MODEM 和 KISS 参数。此包附带了一个示例文件。根据您的需求对其进行修改。
该文件本身由两大部分组成：
1.2.1 硬件参数配置
=====================

硬件设置部分为每个 Z8530 定义了以下参数：

```sh
chip    1
data_a  0x300                   # 数据端口 A
ctrl_a  0x304                   # 控制端口 A
data_b  0x301                   # 数据端口 B
ctrl_b  0x305                   # 控制端口 B
irq     5                       # 中断请求号 5
pclock  4915200                 # 时钟频率
board   BAYCOM                  # 硬件类型
escc    no                      # 增强型 SCC 芯片？（8580/85180/85280）
vector  0                       # 中断向量锁存器地址
special no                      # 特殊功能寄存器地址
option  0                       # 通过特殊功能寄存器设置的选项
```

- **chip**  
  这只是为了让 `sccinit` 编程更简单的一个分隔符。这个参数没有实际作用。
- **data_a**  
  此 Z8530 的数据端口 A 地址（必需）。
- **ctrl_a**  
  控制端口 A 地址（必需）。
- **data_b**  
  数据端口 B 地址（必需）。
- **ctrl_b**  
  控制端口 B 地址（必需）。

- **irq**  
  此芯片使用的中断请求号。不同的芯片可以使用不同的中断请求号或相同的中断请求号。如果它们共享一个中断，则只能在一个芯片定义中指定。
- **pclock**  
  Z8530 的 PCLK 引脚上的时钟频率（可选，默认为 4915200），以赫兹为单位。

- **board**  
  板卡的“类型”：
  
  | SCC 类型         | 值        |
  |------------------|-----------|
  | PA0HZP SCC 卡    | PA0HZP    |
  | EAGLE 卡         | EAGLE     |
  | PC100 卡         | PC100     |
  | PRIMUS-PC (DG9BL)卡 | PRIMUS    |
  | BayCom (U)SCC 卡 | BAYCOM    |

- **escc**  
  如果您希望支持 ESCC 芯片（8580, 85180, 85280），将其设置为“yes”（可选，默认为“no”）。

- **vector**  
  PA0HZP 卡的向量锁存器（即“intack 端口”）地址。对于所有芯片只能有一个向量锁存器！（可选，默认为 0）

- **special**  
  若干卡上的特殊功能寄存器地址（可选，默认为 0）。

- **option**  
  您写入该寄存器的值（可选，默认为 0）。

您可以指定最多四个芯片（8 个通道）。如果这还不够，只需更改：

```c
#define MAXSCC 4
```

为一个更高的值。
BAYCOM USCC 的示例配置：
```
chip    1
data_a  0x300                   # 数据端口 A
ctrl_a  0x304                   # 控制端口 A
data_b  0x301                   # 数据端口 B
ctrl_b  0x305                   # 控制端口 B
irq     5                       # 中断请求号 5
board   BAYCOM                  # 硬件类型
# 
# SCC 芯片 2
#
chip    2
data_a  0x302
ctrl_a  0x306
data_b  0x303
ctrl_b  0x307
board   BAYCOM
```

PA0HZP 卡的示例配置：
```
chip 1
data_a 0x153
data_b 0x151
ctrl_a 0x152
ctrl_b 0x150
irq 9
pclock 4915200
board PA0HZP
vector 0x168
escc no
# 
# 
# 
chip 2
data_a 0x157
data_b 0x155
ctrl_a 0x156
ctrl_b 0x154
irq 9
pclock 4915200
board PA0HZP
vector 0x168
escc no
```

DRSI 卡的示例配置（假设为两张卡）：
```
chip 1
data_a 0x303
data_b 0x301
ctrl_a 0x302
ctrl_b 0x300
irq 7
pclock 4915200
board DRSI
escc no
# 
# 
# 
chip 2
data_a 0x313
data_b 0x311
ctrl_a 0x312
ctrl_b 0x310
irq 7
pclock 4915200
board DRSI
escc no
```

请注意，您不能使用 DRSI 卡上的板载波特率发生器。应使用 "mode dpll" 来设置时钟源（参见下文）。这是基于 Mike Bilow 提供的信息，并且已由 Paul Helay 验证。

“gencfg”实用工具：
--------------------
如果您只知道用于 DOS 下 PE1CHL 驱动程序的参数，请运行 gencfg。它将生成正确的端口地址（希望如此）。其参数与您在 net 中使用 "attach scc" 命令时使用的参数完全相同，只是字符串 "init" 不应该出现。例如：
```
gencfg 2 0x150 4 2 0 1 0x168 9 4915200
```
将向标准输出打印一个适用于 OptoSCC 的 z8530drv.conf 模板：
```
gencfg 2 0x300 2 4 5 -4 0 7 4915200 0x10
```
对于 BAYCOM USCC 卡执行相同操作。在我看来，直接编辑 scc_config.h 更简单一些。

1.2.2 信道配置
==================
信道定义被分为针对每个信道的三个子部分：

scc0 的示例配置：
```
# 设备

device scc0       # 以下参数对应的设备

# MODEM / 缓冲区

speed 1200        # 默认波特率
clock dpll        # 时钟源：
                #  dpll     = 正常半双工操作
                #  external = MODEM 提供自己的 Rx/Tx 时钟
                #  divider  = 如果安装了全双工分频器则使用该分频器
mode nrzi         # HDLC 编码模式
                #  nrzi = 1k2 MODEM, G3RUH 9k6 MODEM
                #  nrz  = DF9IC 9k6 MODEM
bufsize 384       # 缓冲区大小。注意这必须包括 AX.25 头部，而不仅仅是数据字段！
                # （可选，默认为 384）

# KISS (第 1 层)

txdelay 36        # （参见第 1.4 章）
persist 64
slot    8
tail    8
fulldup 0
wait    12
min     3
maxkey  7
idle    3
maxdef  120
group   0
txoff   off
softdcd on
slip    off
```
这些部分内部的顺序不重要。但是这些部分之间的顺序很重要。MODEM 参数会随着第一个被识别的 KISS 参数设置。

请注意，您只能在启动后（或使用 insmod）初始化一次板卡。您可以稍后通过 Sccparam 程序或通过 KISS 更改除 "mode" 和 "clock" 以外的所有参数，以避免安全漏洞。
(1) 这个分频器通常安装在 SCC-PBC (PA0HZP) 上，或者在 BayCom 上不存在。它将 DPLL (数字锁相环) 的输出反馈作为发送时钟。如果未安装此模式所需的分频器，则通常会导致发射机一直工作直到 maxkey 超时——当然不会发送任何有用的数据。

2. 通过您的 AX.25 软件连接信道
==================================

2.1 内核 AX.25
=================
要设置一个 AX.25 设备，您只需键入：
```
ifconfig scc0 44.128.1.1 hw ax25 dl0tha-7
```
这将创建一个具有 IP 地址 44.128.20.107 和呼号 "dl0tha" 的网络接口。如果您还没有 IP 地址（暂时），您可以使用 44.128.0.0 网络中的任意地址。请注意，您不需要 axattach。axattach（像 slattach 一样）的目的在于创建一个与 TTY 链接的 KISS 网络设备。请阅读 ax25-utils 文档和 AX.25-HOWTO 了解如何设置内核 AX.25 的参数。

2.2 NOS、NET 和 TFKISS
======================
由于 TTY 驱动程序（即 KISS TNC 模拟）已经消失，您需要模拟旧的行为。使用这些程序的成本是您可能需要编译内核 AX.25，无论您是否实际使用它。首先设置您的 /etc/ax25/axports，例如：
```
9k6    dl0tha-9  9600  255 4 9600 baud port (scc3)
axlink dl0tha-15 38400 255 4 Link to NOS
```
现在使用 ifconfig 设置 scc 设备：
```
ifconfig scc3 44.128.1.1 hw ax25 dl0tha-9
```
您现在可以使用 axattach 创建一个伪 TTY：
```
axattach /dev/ptys0 axlink
```
然后启动您的 NOS 并在那里附加 /dev/ptys0。问题是 NOS 只能通过内核 AX.25 的中继访问（在 DAMA 控制的信道上灾难性）。为了解决这个问题，配置 "rxecho" 以便将从 "9k6" 接收到的数据帧回显到 "axlink"，并将从 "axlink" 发出的数据帧回显到 "9k6"，然后启动：
```
rxecho
```
或者简单地使用 z8530drv-utils 包含的 "kissbridge"：
```
ifconfig scc3 hw ax25 dl0tha-9
kissbridge scc3 /dev/ptys0
```

3. 参数调整和显示
=====================

3.1 显示 SCC 参数：
======================
一旦 SCC 信道被连接，可以使用 param 程序来显示参数设置和一些统计信息：
```
dl1bke-u:~$ sccstat scc0
```
显示的状态信息如下：

=================	===================================================================
Sent		传输的帧数
Received	接收的帧数
RxErrors	接收错误数（CRC、ABORT）
TxErrors	丢弃的发送帧数（由于各种原因）
Tx State	发送中断处理器的状态：空闲/忙碌/活动/尾部 (2)
RxOver		接收器溢出次数
TxUnder		发送器欠满次数
RxInts		接收中断次数
TxInts		发送中断次数
EpInts		接收特殊条件中断次数
SpInts		外部/状态中断次数
Size		AX.25 帧的最大尺寸（*包含* AX.25 头部！）
NoSpace		无法分配缓冲区的次数
=================	===================================================================

接收器溢出是异常情况。如果发生大量此类溢出，则表明您计算机的处理能力不足以处理当前的波特率乘以接口数量。NoSpace 错误不太可能是由驱动程序或内核 AX.25 引起的。

3.2 设置参数
================
模拟 KISS TNC 的参数设置方式在 SCC 驱动程序中是相同的。您可以使用 ax25-utils 包中的 kissparms 程序或使用 sccparam 程序来更改参数：
```
sccparam <device> <paramname> <decimal-|hexadecimal value>
```
您可以更改以下参数：

========   =====
param      value
========   =====
speed      1200
txdelay    36
persist    255
slottime   0
txtail     8
fulldup    1
waittime   12
mintime    3
maxkeyup   7
idletime   3
maxdefer   120
group      0x00
txoff      off
softdcd    on
SLIP       off
========   =====

参数的含义如下：

speed:
     该信道上的波特率（每秒位数）

     示例: sccparam /dev/scc3 speed 9600

txdelay:
     启用发射器后，直至发送第一个字节前的延迟（以 10 毫秒为单位）。这通常称为 TNC 中的 "TXDELAY"。当指定为 0 时，驱动程序将等待直到 CTS 信号被置位。这假定了 MODEM 和/或发射器中存在的定时器或其他电路，在发射器准备好接收数据时将 CTS 置位。
该参数的正常值为 30-36。
示例: sccparam /dev/scc0 txd 20

persist（持续）:
     当检测到信道空闲时，发射机被激活的概率。它的取值范围是0到255，概率计算公式为 (value+1)/256。该值应接近50-60，在信道使用更加频繁时，应降低此值。
示例: sccparam /dev/scc2 persist 20

slottime（时隙时间）:
     这是检测信道间隔的时间。以10毫秒为单位。大约200-300毫秒（值为20-30）似乎是一个好的选择。
示例: sccparam /dev/scc0 slot 20

tail（尾部）:
     发射机在最后一个数据包字节传输至SCC后保持激活的时间。这是必要的，因为CRC校验和标志还需要离开SCC才能关闭发射机。该值取决于所选波特率。通常几倍字符时间就足够了，例如1200波特时40毫秒（值4）。此参数的值以10毫秒为单位。
示例: sccparam /dev/scc2 tail 4

full（全双工模式）:
     全双工模式开关，可设置以下几种值：

     0:   接口将以CSMA模式运行（即标准半双工分组无线电操作）
     1:   全双工模式，即发射机将一直保持激活状态，不检查接收的载波信号。当没有数据包需要发送时，发射机会自动关闭。
2:   类似于1，但即使没有数据包发送时，发射机也会保持激活状态，并在这种情况下发送标志，直到超时（参数10）发生
示例: sccparam /dev/scc0 fulldup off

wait（等待）:
     在帧排队发送后首次尝试传输前的初始等待时间。这是CSMA模式下的第一个时隙长度。在全双工模式下，为了获得最佳性能，该值设置为0。
此参数的值以10毫秒为单位。
示例: sccparam /dev/scc1 wait 4

maxkey（最大激活时间）:
     发射机连续发送数据包的最大时间，以秒为单位。在繁忙的CSMA信道上，为了避免因产生大量流量而“名声不好”，这可能很有用。达到指定时间后，将不再启动新的帧。相反，发射机将在特定时间内关闭（由参数min决定），然后再次启动选定的开机算法。
值0或"off"将禁用此功能，允许无限的传输时间。
示例：sccparam /dev/scc0 maxk 20

最小时间(min):
    当达到最大传输时间时，此参数定义发射机关闭的时间。
示例：sccparam /dev/scc3 min 10

空闲(idle):
    此参数指定了全双工模式2下的最大空闲时间（以秒为单位）。如果在此时间内没有发送任何帧，则将关闭发射机。值0的结果与全双工模式1相同。此参数可以禁用。
示例：sccparam /dev/scc2 idle off # 持续发射

最大等待时间(maxdefer):
    这是指在发送之前等待一个空闲通道的最大时间（以秒为单位）。当计时器到期时，发射机会立即启动。如果你喜欢与其他用户产生冲突，你可以将这个值设置得非常低；）

示例：sccparam /dev/scc0 maxdefer 240 # 2分钟

禁用发射(txoff):
    当此参数的值为0时，允许发送数据包。否则，禁止发送。
示例：sccparam /dev/scc2 txoff on

组(group):
    可以构建特殊的无线电设备来在同一频段使用多个频率，例如使用多个接收器和一个可以在不同频率间切换的发射机。此外，你还可以连接在同一频段活跃的多台无线电设备。在这种情况下，同时在多个频率上发射通常不是好主意或根本不可能。SCC驱动程序提供了一种方法，通过"param <interface> group <x>"命令锁定不同接口上的发射机。这仅在使用CSMA模式（参数full = 0）时有效。
数字<x>如果不需要组限制则应为0，并且可以根据以下规则计算以创建受限组：
<x>是某些八进制数的总和：

| 八进制数 | 描述 |
| --- | --- |
| 200 | 仅当组内的所有其他发射机都已关闭时，此发射机才会启动。 |
| 100 | 仅当组内所有其他接口的载波检测都为关闭状态时，此发射机才会启动。 |
| 0xx | 用于定义不同组的一个字节。 |
| 逻辑AND运算 | 当两个接口的xx值进行逻辑AND运算后结果非零时，它们属于同一组。 |

示例：

如果有2个接口使用组201，那么它们的发射机永远不会同时启动。
当两个接口使用组 101 时，发射器仅在两个信道同时空闲时才会启动。当使用组 301 时，发射器不会同时启动。

别忘了将八进制数转换为十进制数后再设置参数。
示例：（待编写）

softdcd：
使用软件 DCD 替代实际的 DCD……对于非常慢的静噪功能很有用。
示例: sccparam /dev/scc0 soft on


4. 问题
===========

如果您在使用 BayCom USCC 卡时遇到发射问题，请检查 8530 芯片的制造商。SGS 芯片的定时略有不同。尝试使用 Zilog……一种解决方案是向寄存器 8 写入而非数据端口，但这种方法不适用于 ESCC 芯片
*唉！

一个非常常见的问题是 PTT 锁定直到 maxkeyup 定时器过期，尽管中断和时钟源都是正确的。在大多数情况下，使用 CONFIG_SCC_DELAY 编译驱动程序（通过 make config 设置）可以解决这些问题。更多提示请参阅 (伪) 常见问题解答以及与 z8530drv-utils 一同提供的文档。
我收到报告称该驱动程序在某些基于 386 的系统（例如 Amstrad）上存在问题。这些系统的 AT 总线定时不准确，这会导致中断响应延迟。您可以通过查看疑似端口的 Sccstat 输出来识别这些问题。如果它显示有欠载和超载，则说明您拥有这样的系统。
接收数据处理延迟：这取决于

- 内核版本

- 是否编译了内核剖析

- 高中断负载

- 机器高负载——运行 X、Xmorph、XV 和 Povray，同时编译内核……嗯……即使有 32 MB 内存……;-) 或者在 8 MB 的机器上为整个 .ampr.org 域运行 named …
- 使用 rxecho 或 kissbridge 中的信息
内核崩溃：请阅读 /linux/README 并确定是否真的发生在 scc 驱动程序中。
如果无法解决问题，请给我提供以下信息：

- 问题的描述，
- 您的硬件信息（计算机系统，scc板，调制解调器）
- 您的内核版本
- `cat /proc/net/z8530` 的输出结果

4. Thor RLC100
==============

奇怪的是，这块板似乎无法与驱动程序配合工作。有没有人成功让它运行起来？

非常感谢 Linus Torvalds 和 Alan Cox 将驱动程序纳入 Linux 标准发行版中，并提供了支持：
  
  Joerg Reuter	ampr-net: dl1bke@db0pra.ampr.org  
            AX-25   : DL1BKE @ DB0ABH.#BAY.DEU.EU  
            Internet: jreuter@yaina.de  
            WWW     : http://yaina.de/jreuter
