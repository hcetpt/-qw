SPDX 许可证标识符: GPL-2.0

========================================
GPMC（通用内存控制器）
========================================

GPMC 是一种统一的内存控制器，专门用于与外部内存设备接口，如：

* 类似内存和专用集成电路器件的异步 SRAM
* 异步、同步和分页模式突发 NOR 闪存器件
* NAND 闪存
* 伪 SRAM 器件

GPMC 存在于德州仪器的 SoC 中（基于 OMAP 的）
IP 详情：https://www.ti.com/lit/pdf/spruh73 第 7.1 节


GPMC 通用时序计算：
================================

为了使 GPMC 正常工作，需要为 GPMC 编程一些特定的时序，而外围设备也有另一套时序。要使外围设备与 GPMC 协同工作，必须将外围设备的时序转换成 GPMC 可以理解的形式。这种转换的方式取决于连接的外围设备。此外，某些 GPMC 时序依赖于 GPMC 时钟频率。因此，开发了一种通用时序程序来满足上述要求。通用程序提供了一种从 GPMC 外围设备时序计算 GPMC 时序的一般方法。需要根据连接到 GPMC 的外围设备的数据表更新 `struct gpmc_device_timings` 字段。部分外围设备时序可以以时间或周期形式输入，已提供了处理这种情况的功能（参见 `struct gpmc_device_timings` 定义）。可能会出现数据表中规定的时序在时序结构中不存在的情况，在这种情况下，尝试将外围设备时序与可用时序关联起来。如果这行不通，则尝试根据外围设备需求添加新字段，并告知通用时序程序如何处理这些字段，确保它不会破坏任何现有功能。还可能有外围设备数据表未提及 `struct gpmc_device_timings` 中某些字段的情况，将这些条目设置为零。通用时序程序已在多个 onenand 和 tusb6010 外围设备上验证过，可以正常工作。
注意：通用时序程序是基于对 GPMC 时序、外围设备时序、可用自定义时序程序的理解以及某种程度上的逆向工程而开发的（大多数数据表和硬件都不支持，确切地说，没有一个主流支持的拥有自定义时序程序的设备）并通过模拟进行测试。

GPMC 时序对外围设备时序的依赖关系如下：

[<gpmc_timing>: <peripheral timing1>, <peripheral timing2> ...]

1. 公共

cs_on:
	t_ceasu
adv_on:
	t_avdasu, t_ceavd

2. 同步公共

sync_clk:
	clk
page_burst_access:
	t_bacc
clk_activation:
	t_ces, t_avds

3. 读取异步复用

adv_rd_off:
	t_avdp_r
oe_on:
	t_oeasu, t_aavdh
access:
	t_iaa, t_oe, t_ce, t_aa
rd_cycle:
	t_rd_cycle, t_cez_r, t_oez

4. 读取异步非复用

adv_rd_off:
	t_avdp_r
oe_on:
	t_oeasu
access:
	t_iaa, t_oe, t_ce, t_aa
rd_cycle:
	t_rd_cycle, t_cez_r, t_oez

5. 读取同步复用

adv_rd_off:
	t_avdp_r, t_avdh
oe_on:
	t_oeasu, t_ach, cyc_aavdh_oe
access:
	t_iaa, cyc_iaa, cyc_oe
rd_cycle:
	t_cez_r, t_oez, t_ce_rdyz

6. 读取同步非复用

adv_rd_off:
	t_avdp_r
oe_on:
	t_oeasu
access:
	t_iaa, cyc_iaa, cyc_oe
rd_cycle:
	t_cez_r, t_oez, t_ce_rdyz

7. 写入异步复用

adv_wr_off:
	t_avdp_w
we_on, wr_data_mux_bus:
	t_weasu, t_aavdh, cyc_aavhd_we
we_off:
	t_wpl
cs_wr_off:
	t_wph
wr_cycle:
	t_cez_w, t_wr_cycle

8. 写入异步非复用

adv_wr_off:
	t_avdp_w
we_on, wr_data_mux_bus:
	t_weasu
we_off:
	t_wpl
cs_wr_off:
	t_wph
wr_cycle:
	t_cez_w, t_wr_cycle

9. 写入同步复用

adv_wr_off:
	t_avdp_w, t_avdh
we_on, wr_data_mux_bus:
	t_weasu, t_rdyo, t_aavdh, cyc_aavhd_we
we_off:
	t_wpl, cyc_wpl
cs_wr_off:
	t_wph
wr_cycle:
	t_cez_w, t_ce_rdyz

10. 写入同步非复用

adv_wr_off:
	t_avdp_w
we_on, wr_data_mux_bus:
	t_weasu, t_rdyo
we_off:
	t_wpl, cyc_wpl
cs_wr_off:
	t_wph
wr_cycle:
	t_cez_w, t_ce_rdyz

注：
许多 GPMC 时序依赖于其他 GPMC 时序（某些 GPMC 时序纯粹依赖于其他 GPMC 时序，这就是上面缺少一些 GPMC 时序的原因），这将导致外围设备时序间接地依赖于除上述列出之外的其他 GPMC 时序。有关更多详细信息，请参考时序程序。要了解这些外围设备时序对应的内容，请参阅 `struct gpmc_device_timings` 定义中的解释。至于 GPMC 时序，请参阅 IP 详情（链接在上方）。
