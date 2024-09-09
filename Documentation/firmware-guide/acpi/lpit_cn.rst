... 许可证标识符：GPL-2.0

===========================
低功耗空闲表 (LPIT)
===========================

为了枚举平台的低功耗空闲状态，英特尔平台使用了“低功耗空闲表”（LPIT）。关于此表的更多详细信息可以从以下链接下载：
https://www.uefi.org/sites/default/files/resources/Intel_ACPI_Low_Power_S0_Idle.pdf

每个低功耗状态的驻留时间可以通过 FFH（功能固定硬件）或内存映射接口读取。在支持 S0ix 睡眠状态的平台上，可以有两种类型的驻留时间：

  - CPU 包 C10（通过 FFH 接口读取）
  - 平台控制器集线器 (PCH) SLP_S0（通过内存映射接口读取）

以下属性将动态添加到 cpuidle 的 sysfs 属性组中：

  /sys/devices/system/cpu/cpuidle/low_power_idle_cpu_residency_us  
  /sys/devices/system/cpu/cpuidle/low_power_idle_system_residency_us  

“low_power_idle_cpu_residency_us” 属性显示 CPU 包处于 PKG C10 的时间。

“low_power_idle_system_residency_us” 属性显示 SLP_S0 驻留时间，即系统在 SLP_S0# 信号有效时所花费的时间。
这是最低可能的系统功耗状态，只有当 CPU 处于 PKG C10 且 PCH 中的所有功能模块都处于低功耗状态时才能实现。
