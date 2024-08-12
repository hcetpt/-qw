### SPDX 许可证标识符: GPL-2.0

======================================
Intel® 动态平台与热框架 Sysfs 接口
======================================

**版权所有**：© 2022 Intel 公司

**作者**：Srinivas Pandruvada <srinivas.pandruvada@linux.intel.com>

#### 引言

Intel® 动态平台与热框架 (DPTF) 是一个用于电源和热管理的平台级硬件/软件解决方案。作为多种电源/热技术的容器，DPTF 提供了一种协调的方法来影响系统的硬件状态。
由于它是一个平台级框架，因此包含多个组件。该技术的部分实现位于固件中，并使用 ACPI 和 PCI 设备来暴露各种功能以进行监控和控制。Linux 拥有一组内核驱动程序，它们将硬件接口暴露给用户空间。这使得用户空间热解决方案（如“Linux 热守护进程”）能够读取特定于平台的热和电源表，从而在保持系统在热限制之下时提供足够的性能。

#### DPTF ACPI 驱动程序接口

文件 `/sys/bus/platform/devices/<N>/uuids`，其中 `<N>` = INT3400|INTC1040|INTC1041|INTC10A0

- `available_uuids` (只读)
  - 一组 UUID 字符串表示可用策略，当用户空间可以支持这些策略时，应通知固件。
  - UUID 字符串：
    - `"42A441D6-AE6A-462b-A84B-4A8CE79027D3"`：被动 1
    - `"3A95C389-E4B8-4629-A526-C52C88626BAE"`：主动
    - `"97C68AE7-15FA-499c-B8C9-5DA81D606E0A"`：关键
    - `"63BE270F-1C11-48FD-A6F7-3AF253FF3E2D"`：自适应性能
    - `"5349962F-71E6-431D-9AE8-0A635B710AEE"`：紧急呼叫
    - `"9E04115A-AE87-4D1C-9500-0F3E340BFE75"`：被动 2
    - `"F5A35014-C209-46A4-993A-EB56DE7530A1"`：功率老板
    - `"6ED722A7-9240-48A5-B479-31EEF723D7CF"`：虚拟传感器
    - `"16CAF1B7-DD38-40ED-B1C1-1B8A1913D531"`：冷却模式
    - `"BE84BABF-C4D4-403D-B495-3128FD44DAC1"`：HDC

- `current_uuid` (读写)
  - 用户空间可以从可用 UUID 中写入字符串，一次一个。

文件 `/sys/bus/platform/devices/<N>/`，其中 `<N>` = INT3400|INTC1040|INTC1041|INTC10A0

- `imok` (写入)
  - 用户空间守护进程写入 1 来响应固件事件，发送持续存活通知。当固件调用用户空间以通过 imok ACPI 方法进行响应时，用户空间会收到 THERMAL_EVENT_KEEP_ALIVE kobject uevent 通知。
- `odvp*` (只读)
  - 固件热状态变量值。根据这些变量值，热表要求不同的处理方式。
- `data_vault` (只读)
  - 二进制热表。请参阅 https://github.com/intel/thermal_daemon 获取解码热表的信息。
- `production_mode` (只读)
  - 当不为零时，制造商锁定热配置，防止进一步更改。
ACPI 热关系表接口
------------------------------

:文件:`/dev/acpi_thermal_rel`

此设备提供了用于通过 ACPI 方法 `_TRT` 和 `_ART` 读取标准 ACPI 热关系表的 IOCTL 接口。这些 IOCTL 在 `drivers/thermal/intel/int340x_thermal/acpi_thermal_rel.h` 中定义。

IOCTLs:

- `ACPI_THERMAL_GET_TRT_LEN`: 获取 TRT 表的长度

- `ACPI_THERMAL_GET_ART_LEN`: 获取 ART 表的长度

- `ACPI_THERMAL_GET_TRT_COUNT`: TRT 表中的记录数

- `ACPI_THERMAL_GET_ART_COUNT`: ART 表中的记录数

- `ACPI_THERMAL_GET_TRT`: 读取二进制 TRT 表，要读取的长度由 ioctl() 的参数提供
- `ACPI_THERMAL_GET_ART`: 读取二进制 ART 表，要读取的长度由 ioctl() 的参数提供

DPTF ACPI 传感器驱动程序
------------------------------

DPTF 传感器驱动程序以标准热 sysfs thermal_zone 的形式呈现。

DPTF ACPI 冷却驱动程序
------------------------------

DPTF 冷却驱动程序以标准热 sysfs cooling_device 的形式呈现。

DPTF 处理器热 PCI 驱动程序接口
--------------------------------------------

:文件:`/sys/bus/pci/devices/0000\:00\:04.0/power_limits/`

请参阅文档 `Documentation/power/powercap/powercap.rst` 了解 powercap ABI。

``power_limit_0_max_uw``（只读）
	对于 Intel RAPL 的最大 powercap sysfs 约束条件 0_power_limit_uw。

``power_limit_0_step_uw``（只读）
	Intel RAPL 约束条件 0 功率限制的功率限制增量/减量。

``power_limit_0_min_uw``（只读）
	对于 Intel RAPL 的最小 powercap sysfs 约束条件 0_power_limit_uw。

``power_limit_0_tmin_us``（只读）
	对于 Intel RAPL 的最小 powercap sysfs 约束条件 0_time_window_us。

``power_limit_0_tmax_us``（只读）
	对于 Intel RAPL 的最大 powercap sysfs 约束条件 0_time_window_us。

``power_limit_1_max_uw``（只读）
	对于 Intel RAPL 的最大 powercap sysfs 约束条件 1_power_limit_uw。

``power_limit_1_step_uw``（只读）
	Intel RAPL 约束条件 1 功率限制的功率限制增量/减量。

``power_limit_1_min_uw``（只读）
	对于 Intel RAPL 的最小 powercap sysfs 约束条件 1_power_limit_uw。

``power_limit_1_tmin_us``（只读）
	对于 Intel RAPL 的最小 powercap sysfs 约束条件 1_time_window_us。

``power_limit_1_tmax_us``（只读）
	对于 Intel RAPL 的最大 powercap sysfs 约束条件 1_time_window_us。

``power_floor_status``（只读）
	设置为 1 时，表示在当前配置下系统已达到功率底限。需要重新配置以允许进一步降低功率。
``power_floor_enable``（可读写）
	设置为 1 时，启用功率底限状态的读取和通知。当功率底限状态属性值发生变化时会触发通知。

:文件:`/sys/bus/pci/devices/0000\:00\:04.0/`

``tcc_offset_degree_celsius``（可读写）
	TCC 从临界温度的偏移量，当达到该温度时硬件将降低 CPU 的运行速度。

:文件:`/sys/bus/pci/devices/0000\:00\:04.0/workload_request`

``workload_available_types``（只读）
	可用的工作负载类型。用户空间可以通过 workload_type 指定其当前正在执行的工作负载类型。例如：空闲、突发性、持续等。
### `workload_type` (可读写)
用户空间可以使用此接口指定任何可用的工作负载类型。

### DPTF 处理器热射频干扰管理接口
--------------------------------------------

射频干扰管理（RFIM）接口允许调整全集成电压调节器（FIVR）、双倍数据速率内存（DDR）和数字线性电压调节器（DLVR）的频率，以避免与Wi-Fi和5G产生的射频干扰。
开关式电压调节器（VR）在基频及其谐波上会产生辐射电磁干扰（EMI）或射频干扰（RFI）。某些谐波可能干扰集成在像笔记本电脑这样的主机系统中的非常敏感的无线接收器，如Wi-Fi和蜂窝网络。一种缓解方法是请求SOC集成的VR（IVR）切换频率调整到较小的百分比，并将切换噪声谐波干扰从无线电信道中移开。原始设备制造商（OEM）或原始设计制造商（ODM）可以使用驱动程序来控制SOC IVR的操作范围，以确保不影响IVR性能。
一些产品使用DLVR而非FIVR作为开关式电压调节器，在这种情况下，必须调整DLVR的属性而不是FIVR的属性。
在调整频率的同时可能会引入额外的时钟噪声，通过调整展频百分比来进行补偿，这有助于降低时钟噪声并满足监管合规要求。展频百分比增加信号传输带宽，从而减少干扰、噪声和信号衰落的影响。
DDR IO接口的DRAM设备及其电源平面可能在数据速率下产生EMI。类似于IVR控制机制，Intel提供了一种机制，当满足以下条件时可以改变DDR的数据速率：因为DDR存在强烈的RFI干扰；CPU功率管理没有其他限制去改变DDR数据速率；PC ODMs在BIOS中启用此功能（实时DDR RFI缓解，简称DDR-RFIM），用于Wi-Fi。
### FIVR属性

文件路径：`/sys/bus/pci/devices/0000:00:04.0/fivr/`

- `vco_ref_code_lo` (可读写)
  VCO参考码是一个11位字段，用于控制FIVR的切换频率。这是3位LSB字段。
- `vco_ref_code_hi` (可读写)
  VCO参考码是一个11位字段，用于控制FIVR的切换频率。这是8位MSB字段。
- `spread_spectrum_pct` (可读写)
  设置FIVR的展频时钟百分比。
- `spread_spectrum_clk_enable` (可读写)
  启用/禁用FIVR的展频时钟特性。
- `rfi_vco_ref_code` (只读)
  此字段是一个只读状态寄存器，反映了当前FIVR的切换频率。
- `fivr_fffc_rev` (可读写)
  此字段指示FIVR硬件的版本。
### DVFS 属性

文件路径：`/sys/bus/pci/devices/0000:00:04.0/dvfs/`

- `rfi_restriction_run_busy` (读写)
  - 请求限制特定的DDR数据速率并设置此值为1。操作后自动重置为0。
- `rfi_restriction_err_code` (读写)
  - 0: 请求被接受，1: 功能禁用，2: 请求限制的数据点超出允许范围。
- `rfi_restriction_data_rate_Delta` (读写)
  - 用于RFI保护的受限DDR数据速率：下限。
- `rfi_restriction_data_rate_Base` (读写)
  - 用于RFI保护的受限DDR数据速率：上限。
- `ddr_data_rate_point_0` (只读)
  - DDR数据速率选择的第一个点。
- `ddr_data_rate_point_1` (只读)
  - DDR数据速率选择的第二个点。
- `ddr_data_rate_point_2` (只读)
  - DDR数据速率选择的第三个点。
- `ddr_data_rate_point_3` (只读)
  - DDR数据速率选择的第四个点。
- `rfi_disable` (读写)
  - 禁用DDR速率变化功能。

### DLVR 属性

文件路径：`/sys/bus/pci/devices/0000:00:04.0/dlvr/`

- `dlvr_hardware_rev` (只读)
  - DLVR硬件版本信息。
- `dlvr_freq_mhz` (只读)
  - 当前DLVR PLL频率（单位：MHz）。
- `dlvr_freq_select` (读写)
  - 设置DLVR PLL时钟频率。一旦设置并通过`dlvr_rfim_enable`启用，`dlvr_freq_mhz`将显示当前的DLVR PLL频率。
- `dlvr_pll_busy` (只读)
  - 当设置为1时，PLL无法接受频率改变。
- `dlvr_rfim_enable` (读写)
  - 0: 禁用RF频率跳变，1: 启用RF频率跳变。
- `dlvr_spread_spectrum_pct` (读写)
  - 设置DLVR频谱扩展的百分比值。
- `dlvr_control_mode` (读写)
  - 指定使用频谱扩展技术进行频率分布的方式：
    - 0: 下行频谱扩展，
    - 1: 在中心进行频谱扩展。
- `dlvr_control_lock` (读写)
  - 设置为1时，未来对该寄存器的写入操作将被忽略。
DPTF 电源供应与电池接口
----------------------------------------

请参阅文档/ABI/测试/sysfs-platform-dptf

DPTF 风扇控制
----------------------------------------

请参阅文档/管理指南/acpi/fan_performance_states.rst

工作负载类型提示
----------------------------------------

Meteor Lake 处理器系列中的固件能够识别工作负载类型，并向操作系统传递关于该类型的提示。提供了一个特殊的 sysfs 接口，允许用户空间获取来自固件的工作负载类型提示，并控制这些提示的提供频率。用户空间可以通过轮询属性“workload_type_index”来获取当前的提示，或者在该属性值更新时接收通知。
文件路径：`/sys/bus/pci/devices/0000:00:04.0/workload_hint/`
段 0、总线 0、设备 4、功能 0 在所有英特尔客户端处理器上都是为处理器热设备保留的。因此，上述路径不会根据处理器系列的变化而改变。
``workload_hint_enable``（读写）
	启用固件向用户空间发送工作负载类型提示
``notification_delay_ms``（读写）
	固件在通知操作系统之前的最小延迟（以毫秒为单位）。这是为了控制通知的频率。此延迟是指固件中工作负载类型预测更改和通知操作系统之间的时间。默认延迟为 1024 毫秒。0 毫秒的延迟是无效的。
延迟将向上取整到最接近的 2 的幂次，以便简化固件对延迟值的编程。读取 `notification_delay_ms` 属性会显示实际使用的有效值。
``workload_type_index``（只读）
	预测的工作负载类型索引。用户空间可以通过现有的 sysfs 属性变更通知机制获取变更的通知
对于 Meteor Lake 处理器系列，支持的索引值及其含义如下：

	0 - 空闲：系统不执行任何任务，在长时间内功率和空闲驻留时间始终很低
1 - 电池寿命：功率相对较低，但处理器可能仍然在长时间内积极执行任务，例如视频播放
2 - 持续：长时间保持相对较高的功率水平，几乎不存在或没有空闲期，这最终会导致 RAPL 功率限制 1 和 2 被耗尽
3 – 突发型: 消耗相对恒定的平均功率，但相对空闲的时期会被活动爆发所打断。这些爆发相对较短，而它们之间的相对空闲期通常能够防止RAPL功率限制1被耗尽。
4 – 未知类型: 无法分类
