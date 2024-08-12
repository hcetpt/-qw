SPDX 许可证标识符: GPL-2.0

===============================
TI EMIF SDRAM 控制器驱动程序
===============================

作者
======
Aneesh V <aneesh@ti.com>

位置
========
driver/memory/emif.c

支持的 SoC:
===============
TI OMAP44xx
TI OMAP54xx

Menuconfig 选项:
==================
设备驱动程序
   内存设备
      德州仪器 EMIF 驱动程序

描述
===========
此驱动程序适用于德州仪器 SoC 中的 EMIF 模块。EMIF 是一个 SDRAM 控制器，根据其版本，支持一种或多种 DDR2、DDR3 和 LPDDR2 SDRAM 协议。目前此驱动程序只处理 LPDDR2 内存。该驱动程序的功能包括在频率、电压和温度变化时重新配置 AC 定时参数和其他设置。

平台数据（参见 include/linux/platform_data/emif_plat.h）
===========================================================
可以通过平台数据（struct emif_platform_data）传递 DDR 设备详细信息及其他与板卡和 SoC 相关的信息。

- DDR 设备详细信息：'struct ddr_device_info'
- 设备 AC 时序：'struct lpddr2_timings' 和 'struct lpddr2_min_tck'
- 自定义配置：通过 'struct emif_custom_configs' 提供可定制的策略选项
- IP 版本
- PHY 类型

与外部世界的接口
===============================
EMIF 驱动程序为影响 EMIF 的电压和频率变化注册了通知器，并在这些通知器被触发时采取适当的措施。
- freq_pre_notify_handling()
- freq_post_notify_handling()
- volt_notify_handling()

Debugfs
=======
对于每个设备，驱动程序创建两个 Debugfs 条目
- regcache_dump : 计算并保存至今为止所有使用的频率的寄存器值
- mr4 : LPDDR2 设备中 MR4 寄存器的最后轮询值。MR4 表示设备当前的温度级别
