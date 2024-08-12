==============================
内核驱动：x86_pkg_temp_thermal
==============================

支持的芯片：

* x86：具有封装级别的热管理功能

（验证方法：CPUID.06H:EAX[位 6] = 1）

作者：Srinivas Pandruvada <srinivas.pandruvada@linux.intel.com>

参考
---------

英特尔® 64 和 IA-32 架构软件开发人员手册（2013年1月）：
第 14.6 章：封装级别的热管理

描述
-----------

此驱动程序将CPU数字温度封装级别传感器注册为一个热区，最多有两个用户模式可配置的触发点。触发点的数量取决于封装的能力。一旦触发点被违反，
用户模式可以通过热通知机制接收通知，并可以采取任何行动来控制温度。
阈值管理
--------------------
每个封装都将作为热区在 /sys/class/thermal 下注册
例如::

	/sys/class/thermal/thermal_zone1

这包含两个触发点：

- trip_point_0_temp
- trip_point_1_temp

用户可以在 0 到 TJ-Max 温度之间设置任何温度。温度单位是毫度摄氏度。关于热 sys-fs 的详细信息，请参阅 "Documentation/driver-api/thermal/sysfs-api.rst"
除了 0 之外的这些触发点中的任何值都可以触发热通知
设置为 0，停止发送热通知
热通知：
要获取 kobject-uevent 通知，需要将热区策略设置为 "user_space"
例如::

	echo -n "user_space" > policy
