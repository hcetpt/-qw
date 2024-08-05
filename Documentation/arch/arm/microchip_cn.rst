=============================
ARM Microchip 系统级芯片 SoCs（即 AT91）
=============================


简介
------------
本文档提供了关于目前在 Linux 主线（也就是 kernel.org 上的版本）中支持的 ARM Microchip 系统级芯片的一些有用信息。需要注意的是，Microchip（原 Atmel）基于 ARM 的微处理器产品线在历史上一直被称为“AT91”或“at91”，尽管这个产品前缀已经完全从官方的 Microchip 产品名称中消失。无论如何，在文件、目录、Git 仓库、Git 分支/标签以及电子邮件主题中总是包含“at91”这一子字符串。
AT91 系统级芯片
---------
每种产品的文档和详细数据手册可在 Microchip 官网上找到：http://www.microchip.com
型号包括：
* 基于 ARM 920 的系统级芯片
  - at91rm9200

      * 数据手册

      http://ww1.microchip.com/downloads/en/DeviceDoc/Atmel-1768-32-bit-ARM920T-Embedded-Microprocessor-AT91RM9200_Datasheet.pdf

* 基于 ARM 926 的系统级芯片
  - at91sam9260

      * 数据手册

      http://ww1.microchip.com/downloads/en/DeviceDoc/Atmel-6221-32-bit-ARM926EJ-S-Embedded-Microprocessor-SAM9260_Datasheet.pdf

  - at91sam9xe

      * 数据手册

      http://ww1.microchip.com/downloads/en/DeviceDoc/Atmel-6254-32-bit-ARM926EJ-S-Embedded-Microprocessor-SAM9XE_Datasheet.pdf

  - at91sam9261

      * 数据手册

      http://ww1.microchip.com/downloads/en/DeviceDoc/Atmel-6062-ARM926EJ-S-Microprocessor-SAM9261_Datasheet.pdf

  - at91sam9263

      * 数据手册

      http://ww1.microchip.com/downloads/en/DeviceDoc/Atmel-6249-32-bit-ARM926EJ-S-Embedded-Microprocessor-SAM9263_Datasheet.pdf

  - at91sam9rl

      * 数据手册

      http://ww1.microchip.com/downloads/en/DeviceDoc/doc6289.pdf

  - at91sam9g20

      * 数据手册

      http://ww1.microchip.com/downloads/en/DeviceDoc/DS60001516A.pdf

  - at91sam9g45 系列
    - at91sam9g45
    - at91sam9g46
    - at91sam9m10
    - at91sam9m11（设备超集）

      * 数据手册

      http://ww1.microchip.com/downloads/en/DeviceDoc/Atmel-6437-32-bit-ARM926-Embedded-Microprocessor-SAM9M11_Datasheet.pdf

  - at91sam9x5 系列（也称为“5系列”）
    - at91sam9g15
    - at91sam9g25
    - at91sam9g35
    - at91sam9x25
    - at91sam9x35

      * 数据手册（可以认为覆盖了整个系列）

      http://ww1.microchip.com/downloads/en/DeviceDoc/Atmel-11055-32-bit-ARM926EJ-S-Microcontroller-SAM9X35_Datasheet.pdf

  - at91sam9n12

      * 数据手册

      http://ww1.microchip.com/downloads/en/DeviceDoc/DS60001517A.pdf

  - sam9x60

      * 数据手册

      http://ww1.microchip.com/downloads/en/DeviceDoc/SAM9X60-Data-Sheet-DS60001579A.pdf

* 基于 ARM Cortex-A5 的系统级芯片
  - sama5d3 系列

    - sama5d31
    - sama5d33
    - sama5d34
    - sama5d35
    - sama5d36（设备超集）

      * 数据手册

      http://ww1.microchip.com/downloads/en/DeviceDoc/Atmel-11121-32-bit-Cortex-A5-Microcontroller-SAMA5D3_Datasheet_B.pdf

* 基于 ARM Cortex-A5 + NEON 的系统级芯片
  - sama5d4 系列

    - sama5d41
    - sama5d42
    - sama5d43
    - sama5d44（设备超集）

      * 数据手册

      http://ww1.microchip.com/downloads/en/DeviceDoc/60001525A.pdf

  - sama5d2 系列

    - sama5d21
    - sama5d22
    - sama5d23
    - sama5d24
    - sama5d26
    - sama5d27（设备超集）
    - sama5d28（设备超集+环境监测器）

      * 数据手册

      http://ww1.microchip.com/downloads/en/DeviceDoc/DS60001476B.pdf

* 基于 ARM Cortex-A7 的系统级芯片
  - sama7g5 系列

    - sama7g51
    - sama7g52
    - sama7g53
    - sama7g54（设备超集）

      * 数据手册

      即将推出

  - lan966 系列
    - lan9662
    - lan9668

      * 数据手册

      即将推出

* 基于 ARM Cortex-M7 的微控制器
  - sams70 系列

    - sams70j19
    - sams70j20
    - sams70j21
    - sams70n19
    - sams70n20
    - sams70n21
    - sams70q19
    - sams70q20
    - sams70q21

  - samv70 系列

    - samv70j19
    - samv70j20
    - samv70n19
    - samv70n20
    - samv70q19
    - samv70q20

  - samv71 系列

    - samv71j19
    - samv71j20
    - samv71j21
    - samv71n19
    - samv71n20
    - samv71n21
    - samv71q19
    - samv71q20
    - samv71q21

      * 数据手册

      http://ww1.microchip.com/downloads/en/DeviceDoc/SAM-E70-S70-V70-V71-Family-Data-Sheet-DS60001527D.pdf


Linux 内核信息
------------------------
Linux 内核架构目录：arch/arm/mach-at91
MAINTAINERS 入口是：“ARM/Microchip (AT91) SoC 支持”


针对 AT91 系统级芯片及其板卡的设备树
------------------------------------
所有 AT91 系统级芯片都已经转换为设备树。自 Linux 3.19 版本起，这些产品必须使用此方法来启动 Linux 内核。
正在进行的工作声明：
适用于 AT91 系统级芯片及其板卡的设备树文件和设备树绑定被视为“不稳定”。为了完全清楚，任何 at91 绑定都可能随时发生变化。因此，请确保使用从同一源树生成的设备树二进制文件和内核镜像。
请参阅 Documentation/devicetree/bindings/ABI.rst 文件以了解“稳定”绑定/ABI 的定义。
当适当的时候，AT91 维护者会移除此声明。
命名约定及最佳实践：

- 系统级芯片的设备树源包含文件按产品的官方名称命名（例如 at91sam9g20.dtsi 或 sama5d33.dtsi）。
- 设备树源包含文件（.dtsi）用于收集可以在多个系统级芯片或板卡之间共享的通用节点（例如 sama5d3.dtsi 或 at91sam9x5cm.dtsi）。
当收集特定外设或主题的节点时，标识符应放在文件名末尾，并用一个下划线 "_" 隔开（例如 at91sam9x5_can.dtsi 或 sama5d3_gmac.dtsi）。
设备树源文件（.dts）以字符串"at91-"为前缀，以便于识别。注意有些文件是这一规则的历史例外（例如sama5d3[13456]ek.dts、usb_a9g20.dts或animeo_ip.dts）。
