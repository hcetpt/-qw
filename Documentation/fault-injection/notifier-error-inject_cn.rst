通知器错误注入
========================

通知器错误注入提供了在指定的通知链回调中注入人工错误的能力。这有助于测试很少被执行的通知链故障处理。有内核模块可用于测试以下通知器：
* 电源管理（PM）通知器
* 内存热插拔通知器
* PowerPC pSeries 重构通知器
* 网络设备通知器

电源管理（PM）通知器错误注入模块
----------------------------------
此功能通过 debugfs 接口进行控制：

  `/sys/kernel/debug/notifier-error-inject/pm/actions/<通知事件>/error`

可能失败的 PM 通知器事件包括：

 * `PM_HIBERNATION_PREPARE`
 * `PM_SUSPEND_PREPARE`
 * `PM_RESTORE_PREPARE`

示例：注入 PM 挂起错误（-12 = -ENOMEM）：

	```bash
	# cd /sys/kernel/debug/notifier-error-inject/pm/
	# echo -12 > actions/PM_SUSPEND_PREPARE/error
	# echo mem > /sys/power/state
	bash: echo: write error: Cannot allocate memory
	```

内存热插拔通知器错误注入模块
----------------------------------------------
此功能通过 debugfs 接口进行控制：

  `/sys/kernel/debug/notifier-error-inject/memory/actions/<通知事件>/error`

可能失败的内存通知器事件包括：

 * `MEM_GOING_ONLINE`
 * `MEM_GOING_OFFLINE`

示例：注入内存热插拔离线错误（-12 == -ENOMEM）：

	```bash
	# cd /sys/kernel/debug/notifier-error-inject/memory
	# echo -12 > actions/MEM_GOING_OFFLINE/error
	# echo offline > /sys/devices/system/memory/memoryXXX/state
	bash: echo: write error: Cannot allocate memory
	```

PowerPC pSeries 重构通知器错误注入模块
--------------------------------------------------------
此功能通过 debugfs 接口进行控制：

  `/sys/kernel/debug/notifier-error-inject/pSeries-reconfig/actions/<通知事件>/error`

可能失败的 pSeries 重构通知器事件包括：

 * `PSERIES_RECONFIG_ADD`
 * `PSERIES_RECONFIG_REMOVE`
 * `PSERIES_DRCONF_MEM_ADD`
 * `PSERIES_DRCONF_MEM_REMOVE`

网络设备通知器错误注入模块
----------------------------------------------
此功能通过 debugfs 接口进行控制：

  `/sys/kernel/debug/notifier-error-inject/netdev/actions/<通知事件>/error`

可以失败的网络设备通知器事件包括：

 * `NETDEV_REGISTER`
 * `NETDEV_CHANGEMTU`
 * `NETDEV_CHANGENAME`
 * `NETDEV_PRE_UP`
 * `NETDEV_PRE_TYPE_CHANGE`
 * `NETDEV_POST_INIT`
 * `NETDEV_PRECHANGEMTU`
 * `NETDEV_PRECHANGEUPPER`
 * `NETDEV_CHANGEUPPER`

示例：注入网络设备 MTU 更改错误（-22 == -EINVAL）：

	```bash
	# cd /sys/kernel/debug/notifier-error-inject/netdev
	# echo -22 > actions/NETDEV_CHANGEMTU/error
	# ip link set eth0 mtu 1024
	RTNETLINK answers: Invalid argument
	```

更多使用示例
-----------------------
有工具和自测脚本使用通知器错误注入功能来进行 CPU 和内存通知器的测试：
* `tools/testing/selftests/cpu-hotplug/cpu-on-off-test.sh`
 * `tools/testing/selftests/memory-hotplug/mem-on-off-test.sh`

这些脚本首先进行简单的在线和离线测试，然后如果可用的话，再进行通知器错误注入测试。
