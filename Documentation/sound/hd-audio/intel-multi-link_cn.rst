### SPDX 许可声明：(GPL-2.0-only 或 BSD-3-Clause)
### 包含：<isonum.txt>

==================================
英特尔平台上的 HDAudio 多链路扩展
==================================

版权所有：|copy| 2023 英特尔公司

本文件记录了在 2015 年随 Skylake 处理器引入的“多链路结构”以及最近在更新的英特尔平台上所做的扩展。

#### HDAudio 现有链路映射（2015 年 Skylake 添加）
外部 HDAudio 解码器通过链路 #0 处理，而 HDMI/DisplayPort 的 iDISP 解码器通过链路 #1 处理。
对 2015 年定义的唯一更改是 LCAP.ALT=0x0 的声明 —— 由于 ALT 位之前被保留，这是一个向后兼容的更改。
LCTL.SPA 和 LCTL.CPA 在退出重置时自动设置。它们仅在现有驱动程序中需要校正 SCF 值时使用。
##### HDAudio 解码器的基本结构
```
+-----------+
| ML 能力 #0 |
+-----------+
| ML 能力 #1 |---+
+-----------+   |
                |
                +--> 0x0 +---------------+ LCAP
                             | ALT=0         |
                             +---------------+
                             | S192          |
                             +---------------+
                             | S96           |
                             +---------------+
                             | S48           |
                             +---------------+
                             | S24           |
                             +---------------+
                             | S12           |
                             +---------------+
                             | S6            |
                             +---------------+

                     0x4 +---------------+ LCTL
                             | INTSTS        |
                             +---------------+
                             | CPA           |
                             +---------------+
                             | SPA           |
                             +---------------+
                             | SCF           |
                             +---------------+

                     0x8 +---------------+ LOSIDV
                             | L1OSIVD15     |
                             +---------------+
                             | L1OSIDV..     |
                             +---------------+
                             | L1OSIDV1      |
                             +---------------+

                     0xC +---------------+ LSDIID
                             | SDIID14       |
                             +---------------+
                             | SDIID...      |
                             +---------------+
                             | SDIID0        |
                             +---------------+
```

#### SoundWire HDAudio 扩展链路映射

当 LCAP.ALT=1 和 LEPTR.ID=0 时标识出一个 SoundWire 扩展链路。
DMA 控制使用现有的 LOSIDV 寄存器。
更改包括为枚举添加了以前几代没有的描述：
- 多链路同步：LCAP.LSS 中的能力和 LSYNC 中的控制
- 子链路数量（管理器 IP）在 LCAP.LSCOUNT 中
- 功率管理从 SHIM 移动到 LCTL.SPA 位
- 将 DSP 用于访问多链路寄存器，SHIM/IP 与 LCTL.OFLEN
- SoundWire 解码器与 SDI ID 位的映射
- SHIM 和 Cadence 寄存器移动到不同的偏移量，功能不变。LEPTR.PTR 的值是从 ML 地址的偏移量，默认值为 0x30000
##### SoundWire 的扩展结构（假设 4 个 Manager IP）

```
+-----------+
| ML 能力 #0 |
+-----------+
| ML 能力 #1 |
+-----------+
| ML 能力 #2 |---+
+-----------+   |
                |
                +--> 0x0 +---------------+ LCAP
                             | ALT=1         |
                             +---------------+
                             | INTC          |
                             +---------------+
                             | OFLS          |
                             +---------------+
                             | LSS           |
                             +---------------+
                             | SLCOUNT=4     |-----------+
                             +---------------+           |
                                                                  |
                         0x4 +---------------+ LCTL      |
                             | INTSTS        |           |
                             +---------------+           |
                             | CPA (x 位)    |           |
                             +---------------+           |
                             | SPA (x 位)    |           |
                             +---------------+         对于每个子链路 x
                             | INTEN         |           |
                             +---------------+           |
                             | OFLEN         |           |
                             +---------------+           |
                                                                  |
                         0x8 +---------------+ LOSIDV    |
                             | L1OSIVD15     |           |
                             +---------------+           |
                             | L1OSIDV..     |           |
                             +---------------+           |
                             | L1OSIDV1      |       +---+----------------------------------------------------------+
                             +---------------+       |                                                              |
                                                             v                                                              |
               0xC + 0x2 * x +---------------+ LSDIIDx    +---> 0x30000  +-----------------+  0x00030000            |
                             | SDIID14       |            |              | SoundWire SHIM  |                        |
                             +---------------+            |              | 通用           |                        |
                             | SDIID...      |            |              +-----------------+  0x00030100            |
                             +---------------+            |              | SoundWire IP    |                        |
                             | SDIID0        |            |              +-----------------+  0x00036000            |
                             +---------------+            |              | SoundWire SHIM  |                        |
                                                                      |              | 厂商特定的 |                        |
                                  0x1C +---------------+ LSYNC      |              +-----------------+                        |
                             | CMDSYNC       |            |                                                         v
                             +---------------+            |              +-----------------+  0x00030000 + 0x8000 * x
                             | SYNCGO        |            |              | SoundWire SHIM  |
                             +---------------+            |              | 通用           |
                             | SYNCPU        |            |              +-----------------+  0x00030100 + 0x8000 * x
                             +---------------+            |              | SoundWire IP    |
                             | SYNPRD        |            |              +-----------------+  0x00036000 + 0x8000 * x
                             +---------------+            |              | SoundWire SHIM  |
                                                                      |              | 厂商特定的 |
                                  0x20 +---------------+ LEPTR      |              +-----------------+
                             | ID = 0        |            |
                             +---------------+            |
                             | VER           |            |
                             +---------------+            |
                             | PTR           |------------+
                             +---------------+
```

#### DMIC HDAudio 扩展链路映射

当 LCAP.ALT=1 和 LEPTR.ID=0xC1 设置时标识出一个 DMIC 扩展链路。
DMA 控制使用现有的 LOSIDV 寄存器。

更改包括为枚举添加了以前几代没有的描述：
- 多链路同步：LCAP.LSS 中的能力和 LSYNC 中的控制
- 使用 LCTL.SPA 位进行功率管理
- 将 DSP 用于访问多链路寄存器，SHIM/IP 与 LCTL.OFLEN

- 将 DMIC 寄存器移动到不同的偏移量，功能不变。LEPTR.PTR 的值是从 ML 地址的偏移量，默认值为 0x10000
### 扩展结构用于DMIC
---------------------------

::
  
  +-----------+
  | ML 能力 #0 |
  +-----------+
  | ML 能力 #1 |
  +-----------+
  | ML 能力 #2 |---+
  +-----------+   |
                  |
                  +--> 0x0 +---------------+ LCAP
                           | ALT=1         |
                           +---------------+
                           | INTC          |
                           +---------------+
                           | OFLS          |
                           +---------------+
                           | SLCOUNT=1     |
                           +---------------+

                       0x4 +---------------+ LCTL
                           | INTSTS        |
                           +---------------+
                           | CPA           |
                           +---------------+
                           | SPA           |
                           +---------------+
                           | INTEN         |
                           +---------------+
                           | OFLEN         |
                           +---------------+           +---> 0x10000  +-----------------+  0x00010000
                                                       |              | DMIC SHIM       |
                       0x8 +---------------+ LOSIDV    |              | 通用           |
                           | L1OSIVD15     |           |              +-----------------+  0x00010100
                           +---------------+           |              | DMIC IP         |
                           | L1OSIDV..     |           |              +-----------------+  0x00016000
                           +---------------+           |              | DMIC SHIM       |
                           | L1OSIDV1      |           |              | 厂商特定       |
                           +---------------+           |              +-----------------+
                                                       |
                      0x20 +---------------+ LEPTR     |
                           | ID = 0xC1     |           |
                           +---------------+           |
                           | VER           |           |
                           +---------------+           |
                           | PTR           |-----------+
                           +---------------+


### SSP HDaudio 扩展链路映射
=================================

当 LCAP.ALT=1 和 LEPTR.ID=0xC0 设置时，可以识别出一个DMIC扩展链路。
DMA控制使用现有的 LOSIDV 寄存器。

变化包括在早期版本中未出现的枚举和控制所需的额外描述：
- LCAP.LSCOUNT 中的子链路（SSP IP 实例）数量
- 从SHIM移到LCTL.SPA位的电源管理
- 通过LCTL.OFLEN将多链路寄存器SHIM/IP的访问权限交给DSP
- SHIM 和 SSP IP 寄存器移动到不同的偏移量，功能不变。LEPTR.PTR 的值是相对于 ML 地址的偏移量，默认值为 0x28000
扩展结构用于SSP（假设有3个IP实例）
-----------------------------------------------------------

::
  
  +-----------+
  | ML 能力 #0 |
  +-----------+
  | ML 能力 #1 |
  +-----------+
  | ML 能力 #2 |---+
  +-----------+   |
                  |
                  +--> 0x0 +---------------+ LCAP
                           | ALT=1         |
                           +---------------+
                           | INTC          |
                           +---------------+
                           | OFLS          |
                           +---------------+
                           | SLCOUNT=3     |-------------------------对于每个子链路 x -------------------------+
                           +---------------+                                                                     |
                                                                                                                 |
                       0x4 +---------------+ LCTL                                                                |
                           | INTSTS        |                                                                     |
                           +---------------+                                                                     |
                           | CPA (x 位)    |                                                                     |
                           +---------------+                                                                     |
                           | SPA (x 位)    |                                                                     |
                           +---------------+                                                                     |
                           | INTEN         |                                                                     |
                           +---------------+                                                                     |
                           | OFLEN         |                                                                     |
                           +---------------+           +---> 0x28000  +-----------------+  0x00028000            |
                                                       |              | SSP SHIM        |                        |
                       0x8 +---------------+ LOSIDV    |              | 通用           |                        |
                           | L1OSIVD15     |           |              +-----------------+  0x00028100            |
                           +---------------+           |              | SSP IP          |                        |
                           | L1OSIDV..     |           |              +-----------------+  0x00028C00            |
                           +---------------+           |              | SSP SHIM        |                        |
                           | L1OSIDV1      |           |              | 厂商特定       |                        |
                           +---------------+           |              +-----------------+                        |
                                                       |                                                         v
                      0x20 +---------------+ LEPTR     |              +-----------------+  0x00028000 + 0x1000 * x
                           | ID = 0xC0     |           |              | SSP SHIM        |
                           +---------------+           |              | 通用           |
                           | VER           |           |              +-----------------+  0x00028100 + 0x1000 * x
                           +---------------+           |              | SSP IP          |
                           | PTR           |-----------+              +-----------------+  0x00028C00 + 0x1000 * x
                           +---------------+                          | SSP SHIM        |
                                                                      | 厂商特定       |
                                                                      +-----------------+
