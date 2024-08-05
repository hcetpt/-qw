以下是文档的翻译：

---

### ARM Marvell 系统级芯片 (SoC)

#### Orion 家族

- **型号**：
  - 88F5082
  - 88F5181（又名 Orion-1）
  - 88F5181L（又名 Orion-VoIP）
  - 88F5182（又名 Orion-NAS）
  - 88F5281（又名 Orion-2）
  - 88F6183（又名 Orion-1-90）

- **数据手册**：  
  - [88F5182](https://web.archive.org/web/20210124231420/http://csclub.uwaterloo.ca/~board/ts7800/MV88F5182-datasheet.pdf)  
  - [程序员用户指南](https://web.archive.org/web/20210124231536/http://csclub.uwaterloo.ca/~board/ts7800/MV88F5182-opensource-manual.pdf)  
  - [用户手册](https://web.archive.org/web/20210124231631/http://csclub.uwaterloo.ca/~board/ts7800/MV88F5182-usermanual.pdf)  
  - [功能错误](https://web.archive.org/web/20210704165540/https://www.digriz.org.uk/ts78xx/88F5182_Functional_Errata.pdf)  
  - [88F5281](https://web.archive.org/web/20131028144728/http://www.ocmodshop.com/images/reviews/networking/qnap_ts409u/marvel_88f5281_data_sheet.pdf)

- **主页**：[Marvell Orion](https://web.archive.org/web/20080607215437/http://www.marvell.com/products/media/index.jsp)

- **核心**：Feroceon 88fr331（88f51xx）或 88fr531-vd（88f52xx），兼容 ARMv5

- **Linux 内核 mach 目录**：`arch/arm/mach-orion5x`

- **Linux 内核 plat 目录**：`arch/arm/plat-orion`

#### Kirkwood 家族

- **型号**：
  - 88F6282（又名 Armada 300）
  - 88F6283（又名 Armada 310）
  - 88F6190
  - 88F6192
  - 88F6182
  - 88F6180
  - 88F6280
  - 88F6281
  - 88F6321
  - 88F6322
  - 88F6323

- **主页**：[Marvell Kirkwood](https://web.archive.org/web/20160513194943/http://www.marvell.com/embedded-processors/kirkwood/)

- **核心**：Feroceon 88fr131，兼容 ARMv5

- **Linux 内核 mach 目录**：`arch/arm/mach-mvebu`

- **Linux 内核 plat 目录**：无

#### Discovery 家族

- **型号**：
  - MV78100
  - MV78200
  - MV76100

- **主页**：[Marvell Discovery](https://web.archive.org/web/20110924171043/http://www.marvell.com/embedded-processors/discovery-innovation/)

- **核心**：Feroceon 88fr571-vd，兼容 ARMv5

- **Linux 内核 mach 目录**：`arch/arm/mach-mv78xx0`

- **Linux 内核 plat 目录**：`arch/arm/plat-orion`

#### EBU Armada 家族

- **Armada 370 型号**：
  - 88F6710
  - 88F6707
  - 88F6W11

- **Armada XP 型号**：
  - MV78230
  - MV78260
  - MV78460

- **Armada 375 型号**：
  - 88F6720

- **Armada 38x 型号**：
  - 88F6810 Armada 380
  - 88F6811 Armada 381
  - 88F6821 Armada 382
  - 88F6W21 Armada 383
  - 88F6820 Armada 385
  - 88F6825
  - 88F6828 Armada 388

- **Armada 39x 型号**：
  - 88F6920 Armada 390
  - 88F6925 Armada 395
  - 88F6928 Armada 398

- **Linux 内核 mach 目录**：`arch/arm/mach-mvebu`

- **Linux 内核 plat 目录**：无

#### EBU Armada 家族 ARMv8

- **Armada 3710/3720 型号**：
  - 88F3710
  - 88F3720

- **Armada 7K 型号**：
  - 88F6040
  - 88F7020
  - 88F7040

- **Armada 8K 型号**：
  - 88F8020
  - 88F8040

- **Octeon TX2 CN913x 型号**：
  - CN9130
  - CN9131
  - CN9132

- **Linux 内核设备树文件目录**：`arch/arm64/boot/dts/marvell/*`

#### Avanta 家族

- **型号**：
  - 88F6500
  - 88F6510
  - 88F6530P
  - 88F6550
  - 88F6560
  - 88F6601

- **主页**：[Marvell Avanta](https://web.archive.org/web/20181005145041/http://www.marvell.com/broadband/)

- **核心**：兼容 ARMv5

- **Linux 内核 mach 目录**：计划未来加入主线内核

- **Linux 内核 plat 目录**：计划未来加入主线内核

#### Storage 家族

- **Armada SP**：
  - 88RC1580

- **核心**：Sheeva，兼容 ARMv7 的四核 PJ4C

- **（不支持上游 Linux 内核）**

#### Dove 家族（应用处理器）

- **型号**：
  - 88AP510（又名 Armada 510）

- **核心**：兼容 ARMv7

- **目录**：
  - `arch/arm/mach-mvebu`（启用设备树的平台）
  - `arch/arm/mach-dove`（未启用设备树的平台）

#### PXA 2xx/3xx/93x/95x 家族

- **型号**：
  - PXA21x, PXA25x, PXA26x
  - PXA270, PXA271, PXA272
  - PXA300, PXA310, PXA320
  - PXA930, PXA935
  - PXA955

- **核心**：XScale1, XScale2, XScale3, Sheeva PJ4

- **Linux 内核 mach 目录**：`arch/arm/mach-pxa`

#### MMP/MMP2/MMP3 家族（通信处理器）

- **型号**：
  - PXA168（又名 Armada 168）
  - PXA910/PXA920
  - PXA688（又名 MMP2，又名 Armada 610）
  - PXA2128（又名 MMP3，又名 Armada 620）
  - PXA960/PXA968/PXA978
  - PXA986/PXA988
  - PXA1088/PXA1920
  - PXA1908/PXA1928/PXA1936

- **Linux 内核 mach 目录**：`arch/arm/mach-mmp`

#### Berlin 家族（多媒体解决方案）

- **型号**：
  - 88DE3010, Armada 1000
  - 88DE3005, Armada 1500 Mini
  - 88DE3006, Armada 1500 Mini Plus
  - 88DE3100, Armada 1500
  - 88DE3114, Armada 1500 Pro
  - 88DE3214, Armada 1500 Pro 4K
  - 88DE3218, ARMADA 1500 Ultra

- **目录**：`arch/arm/mach-berlin`

#### CPU 核心

- **XScale 核心**：由 Intel 设计，在较旧的 PXA 处理器中使用。
- **Feroceon 核心**：由 Marvell 自主设计。
- **Sheeva 核心**：取代了 XScale 和 Feroceon 核心。
- **ARM Cortex-A 核心**：取代了 Sheeva 核心。
XScale 1  
CPUID 0x69052xxx  
ARMv5, iWMMXt  
XScale 2  
CPUID 0x69054xxx  
ARMv5, iWMMXt  
XScale 3  
CPUID 0x69056xxx 或 0x69056xxx  
ARMv5, iWMMXt  
Feroceon-1850 88fr331 "Mohawk"  
CPUID 0x5615331x 或 0x41xx926x  
ARMv5TE, 单指令流  
Feroceon-2850 88fr531-vd "Jolteon"  
CPUID 0x5605531x 或 0x41xx926x  
ARMv5TE, VFP, 双指令流  
Feroceon 88fr571-vd "Jolteon"  
CPUID 0x5615571x  
ARMv5TE, VFP, 双指令流  
Feroceon 88fr131 "Mohawk-D"  
CPUID 0x5625131x  
ARMv5TE, 单指令流有序执行  
Sheeva PJ1 88sv331 "Mohawk"  
CPUID 0x561584xx  
ARMv5, 单指令流 iWMMXt v2  
Sheeva PJ4 88sv581x "Flareon"  
CPUID 0x560f581x  
ARMv7, idivt, 可选 iWMMXt v2  
Sheeva PJ4B 88sv581x  
CPUID 0x561f581x  
ARMv7, idivt, 可选 iWMMXt v2  
Sheeva PJ4B-MP / PJ4C  
CPUID 0x562f584x  
ARMv7, idivt/idiva, LPAE, 可选 iWMMXt v2 和/或 NEON  

长期规划  
------------  
* 将 mach-dove/、mach-mv78xx0/ 和 mach-orion5x/ 统一到 mach-mvebu/ 中，以支持 Marvell EBU（工程业务部门）的所有系统级芯片在一个单一的 mach-<foo> 目录中。因此，plat-orion/ 将会消失  
致谢  
-------  

- Maen Suleiman <maen@marvell.com>  
- Lior Amsalem <alior@marvell.com>  
- Thomas Petazzoni <thomas.petazzoni@free-electrons.com>  
- Andrew Lunn <andrew@lunn.ch>  
- Nicolas Pitre <nico@fluxnic.net>  
- Eric Miao <eric.y.miao@gmail.com>
