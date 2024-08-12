=====================
内核驱动程序 nouveau
=====================

支持的芯片：

* NV43+

作者：Martin Peres (mupuf) <martin.peres@free.fr>

描述
-----------

此驱动程序允许读取GPU核心温度、控制GPU风扇并设置温度警报。
目前，由于缺少内核内的API来访问HWMON驱动程序，Nouveau无法访问它可能找到的任何I2C外部监控芯片。如果您有这些芯片之一，则通过Nouveau的HWMON接口进行的温度和/或风扇管理可能无法工作。因此，本文档可能不完全涵盖您的情况。
温度管理
----------------------

温度作为只读HWMON属性temp1_input暴露。

为了防止GPU过热，Nouveau支持4个可配置的温度阈值：

 * 风扇加速：
	达到此温度时，风扇速度设置为100%；
 * 降频：
	GPU将被降频以降低其功耗；
 * 关键：
	GPU将被置于待机状态以进一步降低功耗；
 * 关机：
	关闭计算机以保护您的GPU
警告：
	根据您的芯片组，Nouveau可能不会使用这些阈值中的某些阈值。
这些阈值的默认值来自GPU的vbios。可以使用以下HWMON属性来配置这些阈值：

 * 风扇加速：temp1_auto_point1_temp 和 temp1_auto_point1_temp_hyst；
 * 降频：temp1_max 和 temp1_max_hyst；
 * 关键：temp1_crit 和 temp1_crit_hyst；
 * 关机：temp1_emergency 和 temp1_emergency_hyst
注意：请记住，这些值是以毫度摄氏度存储的。不要忘记乘以！

风扇管理
--------------

并非所有显卡都具有可控风扇。如果您的显卡具备，那么应提供以下HWMON属性：

 * pwm1_enable：
	当前风扇管理模式（无、手动或自动）；
 * pwm1：
	当前PWM值（功率百分比）；
 * pwm1_min：
	允许的最小PWM速度；
 * pwm1_max：
	允许的最大PWM速度（达到风扇加速温度时将被忽略）；

您还可能会有以下属性：

 * fan1_input：
	风扇的转速（RPM）

您的风扇可以采用不同的模式驱动：

 * 0：不触碰风扇；
 * 1：手动驱动风扇（使用pwm1更改速度）；
 * 2：根据温度自动驱动风扇
注意：
  如果要手动控制风扇速度，请确保使用手动模式。

注意2：
  当在vbios定义的[PWM_min, PWM_max]范围之外以手动模式运行时，报告的风扇速度（RPM）可能不准确，具体取决于您的硬件。
错误报告
-----------

Nouveau上的热管理是新的功能，并且可能不是在所有显卡上都能正常工作。如果您有任何疑问，请在IRC上联系mupuf (#nouveau, OFTC)
错误报告应当填写在Freedesktop的错误追踪系统上。请遵循
https://nouveau.freedesktop.org/wiki/Bugs 的指引。
