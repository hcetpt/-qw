OMAP PM 接口
=====================

本文档描述了临时的 OMAP PM 接口。驱动程序作者使用这些函数向内核电源管理代码传达最小延迟或吞吐量限制。
随着时间的推移，计划将 OMAP PM 接口中的一些特性合并到 Linux PM QoS 代码中。
驱动程序需要表达 PM 参数，这些参数应满足以下要求：

- 支持 TI SRF 中存在的各种电源管理参数；
- 将驱动程序与底层 PM 参数实现分离，无论是 TI SRF、Linux PM QoS、Linux 延迟框架还是其他；
- 用基本单位（如延迟和吞吐量）而不是特定于 OMAP 或特定 OMAP 变体的单位来指定 PM 参数；
- 允许在其他架构（例如 DaVinci）中共享的驱动程序以一种不会影响非 OMAP 系统的方式添加这些约束；
- 能够立即实现，并尽量减少对其他架构的影响。

本文档提出了 OMAP PM 接口，包括以下五个电源管理函数供驱动程序代码使用：

1. 设置最大 MPU 唤醒延迟：
   `(*pdata->set_max_mpu_wakeup_lat)(struct device *dev, unsigned long t)`

2. 设置最大设备唤醒延迟：
   `(*pdata->set_max_dev_wakeup_lat)(struct device *dev, unsigned long t)`

3. 设置最大系统 DMA 传输开始延迟（CORE pwrdm）：
   `(*pdata->set_max_sdma_lat)(struct device *dev, long t)`

4. 设置设备所需的最小总线吞吐量：
   `(*pdata->set_min_bus_tput)(struct device *dev, u8 agent_id, unsigned long r)`

5. 返回设备上下文丢失次数：
   `(*pdata->get_dev_context_loss_count)(struct device *dev)`

所有 OMAP PM 接口函数的详细文档可以在 `arch/arm/plat-omap/include/mach/omap-pm.h` 中找到。
OMAP PM 层旨在作为临时方案
---------------------------------------------

最终目标是 Linux PM QoS 层应该支持 OMAP3 中存在的各种电源管理功能。随着这一目标的实现，现有使用 OMAP PM 接口的驱动程序可以修改为使用 Linux PM QoS 代码；OMAP PM 接口则可以消失。

驱动程序使用 OMAP PM 函数
-------------------------------------

正如上述示例中的 'pdata' 所指示的那样，这些函数通过驱动程序的 `.platform_data` 结构中的函数指针暴露给驱动程序。函数指针由 `board-*.c` 文件初始化，指向相应的 OMAP PM 函数：

- `set_max_dev_wakeup_lat` 将指向 `omap_pm_set_max_dev_wakeup_lat()` 等等。不支持这些函数的其他架构应该让这些函数指针保持为 NULL。驱动程序应该使用以下模式：
  ```
  if (pdata->set_max_dev_wakeup_lat)
      (*pdata->set_max_dev_wakeup_lat)(dev, t);
  ```

这些函数最常用的用途可能是指定从发生中断到设备变得可访问的最大时间。为此，驱动程序编写者应使用 `set_max_mpu_wakeup_lat()` 函数来限制 MPU 唤醒延迟，并使用 `set_max_dev_wakeup_lat()` 函数来限制设备唤醒延迟（从 `clk_enable()` 到可访问性）。例如：
```
/* 限制 MPU 唤醒延迟 */
if (pdata->set_max_mpu_wakeup_lat)
    (*pdata->set_max_mpu_wakeup_lat)(dev, tc);

/* 限制设备电源域唤醒延迟 */
if (pdata->set_max_dev_wakeup_lat)
    (*pdata->set_max_dev_wakeup_lat)(dev, td);

/* 在这个例子中的总唤醒延迟：(tc + td) */
```

可以通过再次调用函数并传递新值来覆盖 PM 参数。可以通过传入 `-1` 的 `t` 参数（除了 `set_max_bus_tput()` 应该传入 `0` 的 `r` 参数）来取消设置。

上述第五个函数 `omap_pm_get_dev_context_loss_count()` 是为了优化而设计的，允许驱动程序确定设备是否丢失了其内部上下文。如果上下文已丢失，则驱动程序必须在继续之前恢复其内部上下文。

其他专门接口函数
-------------------------------------

上述列出的五个函数旨在适用于任何设备驱动程序。DSPBridge 和 CPUFreq 有一些特殊需求。

- DSPBridge 使用 OPP ID 来表示目标 DSP 性能级别。
- CPUFreq 使用 MPU 频率来表示目标 MPU 性能级别。

OMAP PM 接口包含用于这些特殊情况的函数，将输入信息（OPP/MPU 频率）转换为底层电源管理实现所需的形式：

6. `(*pdata->dsp_get_opp_table)(void)`

7. `(*pdata->dsp_set_min_opp)(u8 opp_id)`

8. `(*pdata->dsp_get_opp)(void)`

9. `(*pdata->cpu_get_freq_table)(void)`

10. `(*pdata->cpu_set_freq)(unsigned long f)`

11. `(*pdata->cpu_get_freq)(void)`

为平台定制 OPP
==================
定义 `CONFIG_PM` 应该启用硅片上的 OPP 层，并且 OPP 表的注册应该自动进行。
然而，在特殊情况下，可能需要对默认的 OPP（Operating Performance Points，操作性能点）表进行调整，例如：

 * 启用那些默认被禁用但可以在某个平台上启用的默认 OPP
 * 在平台上禁用不支持的 OPP
 * 定义并添加一个自定义的 OPP 表项

在这些情况下，板级文件需要执行额外的步骤，如下所示：

`arch/arm/mach-omapx/board-xyz.c`:

	#include "pm.h"
	...
static void __init omap_xyz_init_irq(void)
	{
		...
/* 初始化默认表 */
		omapx_opp_init();
		/* 对默认设置进行定制 */
		...
}

**注：**
`omapx_opp_init` 将根据 OMAP 家族的不同而不同，比如可能是 `omap3_opp_init` 或者其他按需选择的初始化函数。
