========================
内核驱动 exynos_tmu
========================

支持的芯片：

* ARM 三星 Exynos4、Exynos5 系列 SoC

  数据手册：非公开可用

作者：Donggeun Kim <dg77.kim@samsung.com>
作者：Amit Daniel <amit.daniel@samsung.com>

TMU 控制器描述：
---------------------------

此驱动允许读取三星 Exynos4/5 系列 SoC 内部的温度。
该芯片仅通过寄存器暴露测量得到的 8 位温度码值。
温度可以从温度码中获取。
有三个方程式用于从温度转换为温度码。
这三个方程分别是：
  1. 两点校准：

	Tc = (T - 25) * (TI2 - TI1) / (85 - 25) + TI1

  2. 单点校准：

	Tc = T + TI1 - 25

  3. 无校准：

	Tc = T + 50

  其中，
  Tc:
       温度码， T: 温度，
  TI1:
       25 度 Celsius 的校准信息（存储在 TRIMINFO 寄存器）
       在 25 度 Celsius 下不变的测量温度码
  TI2:
       85 度 Celsius 的校准信息（存储在 TRIMINFO 寄存器）
       在 85 度 Celsius 下不变的测量温度码

Exynos4/5 中的 TMU（热管理单元）会在温度超过预定义水平时生成中断。
可配置阈值的最大数量是五个。
阈值级别定义如下：

  Level_0: 当前温度 > 触发水平_0 + 阈值
  Level_1: 当前温度 > 触发水平_1 + 阈值
  Level_2: 当前温度 > 触发水平_2 + 阈值
  Level_3: 当前温度 > 触发水平_3 + 阈值

阈值和每个触发水平通过相应的寄存器设置。
当发生中断时，此驱动程序使用函数 exynos_report_trigger 通知内核热框架。
虽然可以设置 Level_0 的中断条件，
但它可以用于同步冷却动作。

TMU 驱动程序描述：
-----------------------

exynos 热驱动程序的结构如下：

					内核核心热框架
				(thermal_core.c, step_wise.c, cpufreq_cooling.c)
								^
								|
								|
  TMU 配置数据 -----> TMU 驱动程序  <----> Exynos 核心热封装
  (exynos_tmu_data.c)	      (exynos_tmu.c)	   (exynos_thermal_common.c)
  (exynos_tmu_data.h)	      (exynos_tmu.h)	   (exynos_thermal_common.h)

a) TMU 配置数据：
		这部分包括通过 exynos_tmu_registers 结构描述的 TMU 寄存器偏移量/位字段。
		此外，还有几个其他平台数据（struct exynos_tmu_platform_data 成员）被用来配置 TMU。
b) TMU 驱动：
    此组件初始化 TMU 控制器并设置不同的阈值。它通过调用 exynos_report_trigger
    来启动核心热实施。

c) Exynos 核心热封装：
    这提供了 3 个用于 Kernel 核心热框架的封装函数。它们分别是 exynos_unregister_thermal，
    exynos_register_thermal 和 exynos_report_trigger。
