以下是文档的中文翻译：

==================
ARM Allwinner 系统级芯片(SoC)
==================

本文档列出了当前在Linux内核主线中支持的所有ARM Allwinner系统级芯片(SoC)。本文档还将提供这些SoC的数据手册和/或文档链接。

SunXi系列
---------
Linux内核mach目录：arch/arm/mach-sunxi

版本：

* 基于ARM926的SoC
  - Allwinner F20（sun3i）

    * 不受支持

* 基于ARM Cortex-A8的SoC
  - Allwinner A10（sun4i）

    * 数据手册

      http://dl.linux-sunxi.org/A10/A10%20Datasheet%20-%20v1.21%20%282012-04-06%29.pdf
    * 用户手册

      http://dl.linux-sunxi.org/A10/A10%20User%20Manual%20-%20v1.20%20%282012-04-09%2c%20DECRYPTED%29.pdf

  - Allwinner A10s（sun5i）

    * 数据手册

      http://dl.linux-sunxi.org/A10s/A10s%20Datasheet%20-%20v1.20%20%282012-03-27%29.pdf

  - Allwinner A13 / R8（sun5i）

    * 数据手册

      http://dl.linux-sunxi.org/A13/A13%20Datasheet%20-%20v1.12%20%282012-03-29%29.pdf
    * 用户手册

      http://dl.linux-sunxi.org/A13/A13%20User%20Manual%20-%20v1.2%20%282013-01-08%29.pdf

  - Next Thing Co GR8（sun5i）

* 单核ARM Cortex-A7的SoC
  - Allwinner V3s（sun8i）

    * 数据手册

      http://linux-sunxi.org/File:Allwinner_V3s_Datasheet_V1.0.pdf

* 双核ARM Cortex-A7的SoC
  - Allwinner A20（sun7i）

    * 用户手册

      http://dl.linux-sunxi.org/A20/A20%20User%20Manual%202013-03-22.pdf

  - Allwinner A23（sun8i）

    * 数据手册

      http://dl.linux-sunxi.org/A23/A23%20Datasheet%20V1.0%2020130830.pdf
    * 用户手册

      http://dl.linux-sunxi.org/A23/A23%20User%20Manual%20V1.0%2020130830.pdf

* 四核ARM Cortex-A7的SoC
  - Allwinner A31（sun6i）

    * 数据手册

      http://dl.linux-sunxi.org/A31/A3x_release_document/A31/IC/A31%20datasheet%20V1.3%2020131106.pdf
    * 用户手册

      http://dl.linux-sunxi.org/A31/A3x_release_document/A31/IC/A31%20user%20manual%20V1.1%2020130630.pdf

  - Allwinner A31s（sun6i）

    * 数据手册

      http://dl.linux-sunxi.org/A31/A3x_release_document/A31s/IC/A31s%20datasheet%20V1.3%2020131106.pdf
    * 用户手册

      http://dl.linux-sunxi.org/A31/A3x_release_document/A31s/IC/A31s%20User%20Manual%20%20V1.0%2020130322.pdf

  - Allwinner A33（sun8i）

    * 数据手册

      http://dl.linux-sunxi.org/A33/A33%20Datasheet%20release%201.1.pdf
    * 用户手册

      http://dl.linux-sunxi.org/A33/A33%20user%20manual%20release%201.1.pdf

  - Allwinner H2+（sun8i）

    * 目前没有可用的文档，但已知与H3驱动程序和内存映射兼容。
  - Allwinner H3（sun8i）

    * 数据手册

      https://linux-sunxi.org/images/4/4b/Allwinner_H3_Datasheet_V1.2.pdf
  - Allwinner R40（sun8i）

    * 数据手册

      https://github.com/tinalinux/docs/raw/r40-v1.y/R40_Datasheet_V1.0.pdf
    * 用户手册

      https://github.com/tinalinux/docs/raw/r40-v1.y/Allwinner_R40_User_Manual_V1.0.pdf

* 四核ARM Cortex-A15、四核ARM Cortex-A7的SoC
  - Allwinner A80

    * 数据手册

      http://dl.linux-sunxi.org/A80/A80_Datasheet_Revision_1.0_0404.pdf

* 八核ARM Cortex-A7的SoC
  - Allwinner A83T

    * 数据手册

      https://github.com/allwinner-zh/documents/raw/master/A83T/A83T_Datasheet_v1.3_20150510.pdf
    * 用户手册

      https://github.com/allwinner-zh/documents/raw/master/A83T/A83T_User_Manual_v1.5.1_20150513.pdf

* 四核ARM Cortex-A53的SoC
  - Allwinner A64

    * 数据手册

      http://dl.linux-sunxi.org/A64/A64_Datasheet_V1.1.pdf
    * 用户手册

      http://dl.linux-sunxi.org/A64/Allwinner%20A64%20User%20Manual%20v1.0.pdf
  - Allwinner H6

    * 数据手册

      https://linux-sunxi.org/images/5/5c/Allwinner_H6_V200_Datasheet_V1.1.pdf
    * 用户手册

      https://linux-sunxi.org/images/4/46/Allwinner_H6_V200_User_Manual_V1.1.pdf
  - Allwinner H616

    * 数据手册

      https://linux-sunxi.org/images/b/b9/H616_Datasheet_V1.0_cleaned.pdf
    * 用户手册

      https://linux-sunxi.org/images/2/24/H616_User_Manual_V1.0_cleaned.pdf
