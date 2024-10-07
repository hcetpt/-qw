```
SPDX 许可声明标识符: GPL-2.0
.. include:: <isonum.txt>

=========================================================
SCC.C - 适用于 AX.25 的基于 Z8530 的 HDLC 卡的 Linux 驱动程序
=========================================================

这是文档的一部分。要使用此驱动程序，您必须获取完整的软件包：

互联网上可从以下地址获得：
    
    1. ftp://ftp.ccac.rwth-aachen.de/pub/jr/z8530drv-utils_3.0-3.tar.gz
    
    2. ftp://ftp.pspt.fi/pub/ham/linux/ax25/z8530drv-utils_3.0-3.tar.gz

请注意，本文档中的信息可能已过时。
最新版本的文档以及指向其他重要的 Linux 内核 AX.25 文档和程序的链接可以在 http://yaina.de/jreuter 找到。

版权所有 |copy| 1993,2000 由 Joerg Reuter DL1BKE <jreuter@yaina.de> 提供

部分版权 |copy| 1993 由 Guido ten Dolle PE1NNZ 提供

有关完整的版权声明，请参见 >> Copying.Z8530DRV <<

1. 驱动程序初始化
===============================

为了使用该驱动程序，需要执行以下三个步骤：

    1. 如果作为模块编译：加载模块
    2. 使用 sccinit 设置硬件、MODEM 和 KISS 参数
    3. 通过 "ifconfig" 将每个通道连接到 Linux 内核 AX.25

与 2.4 版本之前的版本不同，这个驱动程序是一个真正的网络设备驱动程序。如果您想运行 xNOS 而不是我们的优秀内核 AX.25，可以使用 2.x 版本（可以从上述站点获得）或阅读 AX.25-HOWTO 了解如何在网络设备驱动程序上模拟 KISS TNC。

1.1 加载模块
======================

（如果您打算将驱动程序编译为内核镜像的一部分，请跳过本章并继续阅读 1.2）

在您可以使用一个模块之前，您需要通过以下命令加载它：

	insmod scc.o

请阅读随模块初始化工具一起提供的 'man insmod'
您应该将 insmod 包含在 /etc/rc.d/rc.* 文件之一中，并不要忘记之后插入对 sccinit 的调用。它会读取您的 /etc/z8530drv.conf 文件。

1.2. /etc/z8530drv.conf
=======================

为了设置所有参数，您必须从 rc.* 文件之一运行 /sbin/sccinit。这必须在您能够 "ifconfig" 接口之前完成。sccinit 会读取文件 /etc/z8530drv.conf 并设置硬件、MODEM 和 KISS 参数。此软件包附带了一个示例文件。根据您的需求对其进行修改。
该文件本身包含两个主要部分：

1.2.1 硬件参数配置
==========================================

硬件设置部分为每个 Z8530 定义了以下参数：

    chip    1
    data_a  0x300                   # 数据端口 A
    ctrl_a  0x304                   # 控制端口 A
    data_b  0x301                   # 数据端口 B
    ctrl_b  0x305                   # 控制端口 B
    irq     5                       # 中断请求号 5
    pclock  4915200                 # 时钟
    board   BAYCOM                  # 硬件类型
    escc    no                      # 增强型 SCC 芯片？（8580/85180/85280）
    vector  0                       # 中断向量锁存器
    special no                      # 特殊功能寄存器地址
    option  0                       # 通过特殊功能寄存器设置的选项

chip
	- 这只是一个分隔符，以简化 sccinit 的编程。该参数没有效果。
data_a
	- 此 Z8530 的数据端口 A 地址（必需）
ctrl_a
	- 控制端口 A 地址（必需）
data_b
	- 数据端口 B 地址（必需）
ctrl_b
	- 控制端口 B 地址（必需）

irq
	- 此芯片使用的中断请求。不同的芯片可以使用不同的中断请求或相同的。如果它们共享一个中断，则需要在同一个芯片定义中指定。
pclock  - Z8530 的 PCLK 引脚上的时钟（选项，默认值为 4915200），以赫兹为单位

board
	- 板卡的“类型”：

	   =======================  ========
	   SCC 类型                 值
	   =======================  ========
	   PA0HZP SCC 卡            PA0HZP
	   EAGLE 卡                 EAGLE
	   PC100 卡                 PC100
	   PRIMUS-PC (DG9BL) 卡     PRIMUS
	   BayCom (U)SCC 卡         BAYCOM
	   =======================  ========

escc
	- 如果您需要支持 ESCC 芯片（8580, 85180, 85280），将其设置为 "yes"（选项，默认值为 "no"）

vector
	- PA0HZP 卡的向量锁存器（又称“中断确认端口”）地址。所有芯片只能有一个向量锁存器！（选项，默认值为 0）

special
	- 某些板卡上的特殊功能寄存器地址（选项，默认值为 0）

option  - 写入该寄存器的值（选项，默认值为 0）

您可以指定最多四个芯片（8 个通道）。如果这还不够，只需更改：

	#define MAXSCC 4

为更高的值即可。
```
BAYCOM USCC 的示例配置：
----------------------------

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
------------------------------

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

DRSI 卡应该可以使用这个配置（实际上是两张 DRSI 卡）：
--------------------------------------------------------

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

请注意，您不能使用 DRSI 卡上的板载波特率生成器。应使用 "mode dpll" 作为时钟源（见下文）。这是基于 Mike Bilow 提供的信息，并由 Paul Helay 验证。

“gencfg” 实用程序：
----------------------

如果您只知道 DOS 下的 PE1CHL 驱动参数，请运行 gencfg。它将生成正确的端口地址（希望如此）。其参数与使用 “attach scc” 命令时使用的参数完全相同，只是字符串 “init” 不应出现。例如：

```
gencfg 2 0x150 4 2 0 1 0x168 9 4915200
```

将会输出一个 OptoSCC 的 z8530drv.conf 模板到标准输出：

```
gencfg 2 0x300 2 4 5 -4 0 7 4915200 0x10
```

则为 BAYCOM USCC 卡做同样的事情。在我看来，编辑 scc_config.h 更简单一些。

1.2.2 通道配置
=====================

每个通道的定义分为三个子部分：

scc0 的示例配置：

```plaintext
# 设备
device scc0  # 以下参数对应的设备

# MODEM / 缓冲区
speed 1200   # 默认波特率
clock dpll   # 时钟源：
            #   dpll     = 正常半双工操作
            #   external = MODEM 提供自己的 Rx/Tx 时钟
            #   divider  = 如果安装了全双工分频器，则使用它
mode nrzi    # HDLC 编码模式
            #   nrzi = 1k2 MODEM, G3RUH 9k6 MODEM
            #   nrz  = DF9IC 9k6 MODEM
bufsize 384  # 缓冲区大小。注意这必须包括 AX.25 头部，而不仅仅是数据字段！（可选，默认值为 384）

# KISS（第一层）
txdelay 36  # （见第 1.4 章节）
persist 64
slot 8
tail 8
fulldup 0
wait 12
min 3
maxkey 7
idle 3
maxdef 120
group 0
txoff off
softdcd on
slip off
```

这些部分内部的顺序不重要。但这些部分之间的顺序很重要。MODEM 参数是通过第一个被识别的 KISS 参数设置的。

请注意，您只能在启动（或加载模块）后初始化一次板卡。您可以稍后通过 Sccparam 程序或 KISS 改变所有参数，但不能改变 “mode” 和 “clock”。这样做是为了避免安全漏洞。

（1）这个分频器通常安装在 SCC-PBC（PA0HZP）上，或者在 BayCom 上不存在。它将 DPLL（数字锁相环）的输出反馈作为传输时钟。如果未安装分频器而使用这种模式，通常会导致发射机一直工作直到 maxkey 到期——当然不会发送任何有用的数据。

2. 通过您的 AX.25 软件附加一个通道
==================================

2.1 内核 AX.25
================

要设置一个 AX.25 设备，只需键入：

```
ifconfig scc0 44.128.1.1 hw ax25 dl0tha-7
```

这将创建一个具有 IP 地址 44.128.20.107 和呼号 "dl0tha" 的网络接口。如果您还没有 IP 地址，可以使用 44.128.0.0 网络。请注意，您不需要 axattach。axattach（像 slattach 一样）的作用是创建一个链接到 TTY 的 KISS 网络设备。请阅读 ax25-utils 文档和 AX.25-HOWTO 来了解如何设置内核 AX.25 的参数。

2.2 NOS、NET 和 TFKISS
=======================

由于 TTY 驱动（即 KISS TNC 模拟）已不再存在，您需要模拟旧的行为。使用这些程序的成本是，您可能需要编译内核 AX.25，无论您是否实际使用它。首先设置您的 /etc/ax25/axports，例如：

```
9k6  dl0tha-9  9600  255 4 9600 baud port (scc3)
axlink  dl0tha-15 38400 255 4 Link to NOS
```

现在配置 scc 设备：

```
ifconfig scc3 44.128.1.1 hw ax25 dl0tha-9
```

现在可以 axattach 一个伪 TTY：

```
axattach /dev/ptys0 axlink
```

然后启动您的 NOS 并在其中附加 /dev/ptys0。问题是 NOS 只能通过内核 AX.25 经过 digipeating 访问（在 DAMA 控制的信道上灾难性地慢）。为了解决这个问题，配置 "rxecho" 以从 "9k6" 向 "axlink" 回显传入帧，并从 "axlink" 向 "9k6" 回显传出帧，然后启动：

```
rxecho
```

或者简单地使用 z8530drv-utils 包中的 "kissbridge"：

```
ifconfig scc3 hw ax25 dl0tha-9
kissbridge scc3 /dev/ptys0
```

3. 参数调整和显示
=======================

3.1 显示 SCC 参数
==============================

一旦 SCC 通道被附加，就可以使用 param 程序显示参数设置和一些统计信息：

```
dl1bke-u:~$ sccstat scc0
```

输出如下：

```plaintext
Parameters:

speed       : 1200 baud
txdelay     : 36
persist     : 255
slottime    : 0
txtail      : 8
fulldup     : 1
waittime    : 12
mintime     : 3 sec
maxkeyup    : 7 sec
idletime    : 3 sec
maxdefer    : 120 sec
group       : 0x00
txoff       : off
softdcd     : on
SLIP        : off

Status:

HDLC                  Z8530           Interrupts         Buffers
-----------------------------------------------------------------------
Sent       :     273  RxOver :     0  RxInts :   125074  Size    :  384
Received   :    1095  TxUnder:     0  TxInts :     4684  NoSpace :    0
RxErrors   :    1591                  ExInts :    11776
TxErrors   :       0                  SpInts :     1503
Tx State   :    idle
```

状态信息说明：

==============   ==============================================================
Sent             已发送的帧数
Received         已接收的帧数
RxErrors         接收错误数（CRC，ABORT）
TxErrors         被丢弃的 Tx 帧数（由于各种原因）
Tx State         Tx 中断处理程序的状态：空闲/忙/活动/尾部 (2)
RxOver           接收溢出次数
TxUnder          发送欠载次数
RxInts           接收中断次数
TxInts           发送中断次数
ExInts           接收特殊条件中断次数
SpInts           外部/状态中断次数
Size             AX.25 帧的最大大小（包含 AX.25 头部！）
NoSpace          缓冲区无法分配的次数
==============   ==============================================================

发生溢出是不正常的。如果大量发生这种情况，表明您的计算机处理能力不足以应对当前波特率和接口数量的乘积。NoSpace 错误不大可能是由驱动程序或内核 AX.25 引起的。

3.2 设置参数
======================

模拟 KISS TNC 的参数设置方式在 SCC 驱动中也是相同的。您可以使用 ax25-utils 包中的 kissparms 程序或使用 sccparam 程序来更改参数：

```
sccparam <device> <paramname> <decimal-|hexadecimal value>
```

您可以更改以下参数：

===========   =====
param         value
===========   =====
speed         1200
txdelay       36
persist       255
slottime      0
txtail        8
fulldup       1
waittime      12
mintime       3
maxkeyup      7
idletime      3
maxdefer      120
group         0x00
txoff         off
softdcd       on
SLIP          off
===========   =====

参数含义如下：

speed:
     该通道上的波特率（位/秒）

     示例：`sccparam /dev/scc3 speed 9600`

txdelay:
     发射机接通后开始发送第一个字节前的延迟（以 10 毫秒为单位）。这通常在 TNC 中称为 "TXDELAY"。当指定为 0 时，驱动程序将等待 CTS 信号有效。这假定 MODEM 和/或发射机中有定时器或其他电路，在发射机准备好发送数据时使 CTS 信号有效。
此参数的正常值为30-36。
示例：sccparam /dev/scc0 txd 20

persist（持续）：
    当发现信道空闲时，发射机被激活的概率。这是一个从0到255的值，概率为(value+1)/256。该值应接近50-60，并且在信道使用更加频繁时应降低。
示例：sccparam /dev/scc2 persist 20

slottime（时隙时间）：
    采样信道的时间间隔。以10毫秒为单位表示。大约200-300毫秒（值20-30）似乎是一个合适的值。
示例：sccparam /dev/scc0 slot 20

tail（尾部）：
    发射机在最后一个数据包字节传输到SCC后保持激活的时间。这是必要的，因为CRC和标志还需要离开SCC才能关闭发射机。值取决于所选的波特率。几个字符时间就足够了，例如在1200波特率下为40毫秒（值4）。此参数的值以10毫秒为单位。
示例：sccparam /dev/scc2 tail 4

full（全双工模式）：
    全双工模式开关。可以是以下值之一：

    0：接口将在CSMA模式下运行（正常的半双工包无线电操作）
    1：全双工模式，即发射机在任何时候都会被激活，无需检查接收的载波。当没有数据包发送时，它将被关闭。
    2：类似于1，但即使没有数据包发送时，发射机也会保持激活状态。在这种情况下会发送标志，直到发生超时（参数10）为止。
示例：sccparam /dev/scc0 fulldup off

wait（等待）：
    数据帧排队发送后的初始等待时间。这是CSMA模式下的第一个时隙的长度。在全双工模式下，为了达到最佳性能，它会被设置为0。
此参数的值以10毫秒为单位。
示例：sccparam /dev/scc1 wait 4

maxkey（最大激活时间）：
    发射机发送数据包的最大时间，以秒为单位。在繁忙的CSMA信道上，这可能是有用的，以避免在产生大量流量时“获得坏名声”。在指定的时间过去后，不会开始新的帧。相反，发射机会被关闭一段时间（参数min），然后重新启动选定的激活算法。
值0以及"off"将禁用此功能，并允许无限的传输时间。
### 示例：sccparam /dev/scc0 maxk 20

#### min:
这个参数表示当最大传输时间超过时，发射器将被关闭的时间。
示例：sccparam /dev/scc3 min 10

#### idle:
这个参数指定了全双工模式2下的最大空闲时间（以秒为单位）。当在此时间内没有发送任何帧时，发射器将被关闭。值为0的效果与全双工模式1相同。此参数可以禁用。
示例：sccparam /dev/scc2 idle off  # 永远不关闭发射器

#### maxdefer:
这是等待空闲信道发送的最大时间（以秒为单位）。当计时器超时时，发射器将立即启动。如果你喜欢与其他用户发生冲突，可以将此值设置得非常低。
示例：sccparam /dev/scc0 maxdefer 240  # 2分钟

#### txoff:
当此参数的值为0时，允许包的传输。否则，禁止传输。
示例：sccparam /dev/scc2 txoff on

#### group:
可以构建特殊的无线电设备来在同一频段使用多个频率，例如使用多个接收器和一个可以在不同频率之间切换的发射器。同样，你也可以连接在同一频段内活跃的多个无线电设备。在这种情况下，不可能或不是一个好主意同时在多个频率上发射。SCC驱动提供了一种方法来锁定不同接口上的发射器，使用命令 "param <interface> group <x>"。这仅在使用CSMA模式（参数full = 0）时有效。
数字<x>如果不需要组限制，则必须为0；可以通过以下方式计算来创建受限组：
<x> 是一些八进制数的和：

| 八进制数 | 描述 |
|---------|------|
| 200     | 此发射器只有在组中所有其他发射器都关闭时才会启动 |
| 100     | 此发射器只有在组中所有其他接口的载波检测关闭时才会启动 |
| 0xx     | 一个字节，可用于定义不同的组 |

接口在同一组内，当它们的xx值进行逻辑AND运算后结果非零。

示例：

当两个接口使用组201时，它们的发射器永远不会同时启动。
当两个接口使用组101时，发射器仅在两个信道同时空闲时才会启动。当使用组301时，发射器不会同时启动。

请在设置参数前将八进制数转换为十进制数。
示例：（待编写）

softdcd：
     使用软件DCD而不是真实的DCD……对于非常慢的静噪功能很有用
示例：sccparam /dev/scc0 soft on

4. 问题
===========

如果您在使用BayCom USCC卡时遇到发射问题，请检查8530芯片的制造商。SGS芯片的时序略有不同。尝试使用Zilog……一种解决方案是写入寄存器8而不是数据端口，但这种方法不适用于ESCC芯片
*唉！

一个非常常见的问题是PTT锁定直到最大键控定时器超时，尽管中断和时钟源都是正确的。大多数情况下，通过CONFIG_SCC_DELAY编译驱动程序（使用make config设置）可以解决问题。更多提示请参阅（伪）常见问题解答以及z8530drv-utils随附的文档。
我收到报告称该驱动程序在某些基于386的系统（例如Amstrad）上存在问题。这些系统的AT总线时序有问题，会导致中断响应延迟。您可以通过查看疑似端口的Sccstat输出来识别这些问题。如果显示欠载和过载，则表明您的系统存在此类问题。
接收数据处理延迟：这取决于

- 内核版本

- 是否编译了内核性能分析

- 高中断负载

- 机器高负载——运行X、Xmorph、XV和Povray，同时编译内核……嗯……即使有32 MB内存……;-) 或者在一个8 MB内存的机器上运行整个.ampr.org域名的named服务。
- 使用rxecho或kissbridge提供的信息
内核崩溃：请阅读/linux/README，并确定是否真的在scc驱动程序中发生。
如果你无法解决问题，请发送以下信息给我：

- 问题的描述，
- 硬件信息（计算机系统、SCC板、调制解调器）
- 内核版本
- `cat /proc/net/z8530` 的输出

4. Thor RLC100
==============

这块板似乎无法与驱动程序正常工作，原因不明。有谁能成功让它运行起来吗？

非常感谢 Linus Torvalds 和 Alan Cox 将该驱动程序纳入 Linux 标准发行版，并提供支持：

- Joerg Reuter
  - AMPR 网络：dl1bke@db0pra.ampr.org
  - AX-25：DL1BKE @ DB0ABH.#BAY.DEU.EU
  - Internet：jreuter@yaina.de
  - WWW：http://yaina.de/jreuter
