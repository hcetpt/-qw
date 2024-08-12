SPDX 许可证标识符: GPL-2.0

调谐器驱动程序
===============

简单的调谐器编程
------------------

存在几种不同版本的调谐器编程API，这些API主要通过频段切换字节来区分：
- L= LG_API       （VHF_LOW=0x01, VHF_HIGH=0x02, UHF=0x08, 无线电=0x04）
- P= PHILIPS_API  （VHF_LOW=0xA0, VHF_HIGH=0x90, UHF=0x30, 无线电=0x04）
- T= TEMIC_API    （VHF_LOW=0x02, VHF_HIGH=0x04, UHF=0x01）
- A= ALPS_API     （VHF_LOW=0x14, VHF_HIGH=0x12, UHF=0x11）
- M= PHILIPS_MK3  （VHF_LOW=0x01, VHF_HIGH=0x02, UHF=0x04, 无线电=0x19）

调谐器制造商
-------------

- 三星调谐器识别：（例如TCPM9091PD27）

```none
TCP [ABCJLMNQ] 90[89][125] [DP] [ACD] 27 [ABCD]
[ABCJLMNQ]:
  A= BG+DK
  B= BG
  C= I+DK
  J= 日本NTSC
  L= SECAM LL
  M= BG+I+DK
  N= NTSC
  Q= BG+I+DK+LL
[89]: ?
[125]:
  2: 无FM
  5: 带FM
[DP]:
  D= NTSC
  P= PAL
[ACD]:
  A= F-接头
  C= 音频插孔
  D= DIN插孔
[ABCD]:
  3线/I2C调谐，2频带/3频带
```

这些调谐器与PHILIPS_API兼容
飞利浦调谐器识别：（例如FM1216MF）

```none
F[IRMQ]12[1345]6{MF|ME|MP}
F[IRMQ]:
  FI12x6: 调谐器系列
  FR12x6: 调谐器 + 无线电IF
  FM12x6: 调谐器 + FM
  FQ12x6: 特殊
  FMR12x6: 特殊
  TD15xx: 数字调谐器ATSC
12[1345]6:
  1216: PAL BG
  1236: NTSC
  1246: PAL I
  1256: PAL DK
{MF|ME|MP}
  MF: BG LL 带SECAM（多法国）
  ME: BG DK I LL   （多欧洲）
  MP: BG DK I      （多PAL）
  MR: BG DK M (?)
  MG: BG DKI M (?)
MK2 系列 PHILIPS_API，大多数调谐器与此兼容！
MK3 系列于2002年引入，使用PHILIPS_MK3_API
```

TEMIC调谐器识别：（例如4006FH5）

```none
4[01][0136][269]F[HYNR]5
  40x2: 调谐器（5V/33V），TEMIC_API
40x6: 调谐器5V
  41xx: 紧凑型调谐器
  40x9: 带FM的紧凑型调谐器
[0136]
  xx0x: PAL BG
  xx1x: PAL DK，SECAM LL
  xx3x: NTSC
  xx6x: PAL I
F[HYNR]5
  FH5: PAL BG
  FY5: 其他
  FN5: 多标准
  FR5: 带FM无线电
3X xxxx: 具有特定接头的订单号
注：只有40x2系列具有TEMIC_API，所有较新的调谐器都使用PHILIPS_API
```

LG Innotek 调谐器：

- TPI8NSR11 : NTSC J/M    （TPI8NSR01带FM）  （P,210/497）
- TPI8PSB11 : PAL B/G     （TPI8PSB01带FM）  （P,170/450）
- TAPC-I701 : PAL I       （TAPC-I001带FM）  （P,170/450）
- TPI8PSB12 : PAL D/K+B/G （TPI8PSB02带FM）  （P,170/450）
- TAPC-H701P: NTSC_JP     （TAPC-H001P带FM） （L,170/450）
- TAPC-G701P: PAL B/G     （TAPC-G001P带FM） （L,170/450）
- TAPC-W701P: PAL I       （TAPC-W001P带FM） （L,170/450）
- TAPC-Q703P: PAL D/K     （TAPC-Q001P带FM） （L,170/450）
- TAPC-Q704P: PAL D/K+I   （L,170/450）
- TAPC-G702P: PAL D/K+B/G （L,170/450）

- TADC-H002F: NTSC （L,175/410?; 2-B, C-W+11, W+12-69）
- TADC-M201D: PAL D/K+B/G+I （L,143/425）  （音频控制在I2C地址 0xc8）
- TADC-T003F: NTSC 台湾  （L,175/410?; 2-B, C-W+11, W+12-69）

后缀：
  - P= 标准音频母接口
  - D= IEC母接口
  - F= F-接头

其他调谐器：

- TCL2002MB-1 : PAL BG + DK       =TUNER_LG_PAL_NEW_TAPC
- TCL2002MB-1F: PAL BG + DK 带FM  =PHILIPS_PAL
- TCL2002MI-2 : PAL I         = ??

ALPS调谐器：

- 大多数与LG_API兼容
- TSCH6使用ALPS_API（TSCH5？）
- TSBE1有额外的API 05,02,08 控制字节=0xCB 来源：[#f1]_

.. [#f1] conexant100029b-PCI-Decoder-ApplicationNote.pdf
