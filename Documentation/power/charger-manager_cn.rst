充电器管理器
===============

	(C) 2011 MyungJoo Ham <myungjoo.ham@samsung.com>，GPL

充电器管理器提供了内核中的电池充电器管理功能，在挂起到RAM状态时需要温度监控，并且每个电池可能连接有多个充电器，用户空间希望查看这些充电器的聚合信息。充电器管理器是一个具有电源供应类条目的平台驱动程序。一个充电器管理器实例（通过充电器管理器创建的平台设备）代表一个独立的电池及其充电器。如果系统中有多个独立工作的电池及其充电器，则系统可能需要多个充电器管理器实例。

1. 引言
===============

充电器管理器支持以下功能：

* 支持多个充电器（例如，带有USB、交流电和太阳能板的设备）
	系统可能拥有多个充电器（或电源），并且某些充电器可能同时激活。每个充电器可能有自己的电源供应类条目，并且每个电源供应类条目可以提供有关电池状态的不同信息。此框架从多个来源聚合充电器相关信息，并将其显示为单一的电源供应类条目。
* 支持挂起到RAM时的轮询（带suspend_again回调）
	在电池充电过程中且系统处于挂起到RAM状态时，我们可能需要通过查看环境或电池温度来监控电池健康状况。我们可以通过周期性唤醒系统来实现这一点。然而，这种方法会为了监控电池健康状况和任务以及本应保持挂起状态的用户进程而无谓地唤醒设备。这反过来会导致不必要的功耗增加并减慢充电过程。甚至，这种峰值功耗可能会在充电中途停止充电器（外部输入功率<设备消耗功率），这不仅影响了充电时间，还会影响电池的寿命。
	充电器管理器提供了一个名为“cm_suspend_again”的函数，可以作为platform_suspend_ops中的suspend_again回调。如果平台还需要执行其他任务，可以实现自己的suspend_again回调并在其中调用cm_suspend_again。
通常情况下，平台需要恢复和挂起充电器管理器所使用的某些设备。
* 支持提前满电事件处理
	如果在满电事件发生后经过“fullbatt_vchkdrop_ms”毫秒，电池电压下降超过“fullbatt_vchkdrop_uV”，则框架将重新开始充电。此检查在挂起状态下也会进行，通过相应设置唤醒时间并使用suspend_again来实现。
* 支持uevent通知
	当发生与充电器相关的事件时，设备会向用户发送UEVENT通知。

2. 与suspend_again相关的全局充电器管理器数据
=========================================================
为了使用挂起再唤醒功能（挂起时监控），用户需要通过setup_charger_manager(`struct charger_global_desc *`)提供charger_global_desc。
此`charger_global_desc`数据用于挂起监控，正如其名称所示，是全局的。因此，即使有多个电池，用户也只需提供一次。如果有多个电池，多个实例的充电器管理器将共享相同的`charger_global_desc`，并为所有充电器管理器实例管理挂起监控。为了激活挂起监控，用户需要正确地提供`struct charger_global_desc`中的以下三个条目：

`char *rtc_name;`
这是用于通过充电器管理器从挂起状态唤醒系统的RTC（例如，“rtc0”）的名称。RTC的报警中断（AIE）应能够从挂起状态唤醒系统。充电器管理器会保存和恢复报警值，并在它将比之前定义的报警更早触发的情况下使用之前定义的报警，以确保充电器管理器不会干扰之前定义的报警。

`bool (*rtc_only_wakeup)(void);`
此回调函数应告知CM（充电器管理器），是否仅由同一结构中的“rtc”的报警导致了从挂起状态唤醒。如果还有其他唤醒源触发了唤醒，则应回答false。如果“rtc”是唯一的唤醒原因，则应回答true。

`bool assume_timer_stops_in_suspend;`
如果为true，则充电器管理器假定计时器（CM使用jiffies作为计时器）在挂起期间停止。这样，CM假定挂起时间与报警长度相同。

### 如何设置suspend_again
=============================
充电器管理器提供了一个函数`extern bool cm_suspend_again(void)`。当调用cm_suspend_again时，它会监控每个电池。系统的平台挂起操作（`suspend_ops`）可以调用cm_suspend_again函数来判断充电器管理器是否希望再次进入挂起状态。
如果没有其他设备或任务希望使用suspend_again功能，平台挂起操作可以直接引用cm_suspend_again作为其suspend_again回调。

当系统被充电器管理器唤醒且轮询（挂起监控）结果为“正常”时，cm_suspend_again()返回true（表示“我希望再次进入挂起状态”）。

### 充电器管理器数据（struct charger_desc）
=============================================
对于每个独立于其他电池充电的电池（如果一组电池由单个充电器充电，它们被视为一个独立电池），都有一个充电器管理器实例与其关联。以下是`struct charger_desc`元素：

`char *psy_name;`
这是电池的电源供应类名称，默认情况下，如果`psy_name`为NULL，则默认为“battery”。用户可以通过路径`/sys/class/power_supply/[psy_name]/`访问这些电源供应项。

`enum polling_modes polling_mode;`
- `CM_POLL_DISABLE`: 不对此电池进行轮询
CM_POLL_ALWAYS:
始终轮询此电池

CM_POLL_EXTERNAL_POWER_ONLY:
仅在有外部电源连接时轮询此电池

CM_POLL_CHARGING_ONLY:
仅在电池正在充电时轮询此电池

`unsigned int fullbatt_vchkdrop_ms; / unsigned int fullbatt_vchkdrop_uV;`
如果这两个值均非零，Charger Manager 将在电池完全充满后 `fullbatt_vchkdrop_ms` 时间后检查电池电压下降。如果电压下降超过 `fullbatt_vchkdrop_uV`，Charger Manager 将通过禁用和启用充电器来尝试重新充电。仅基于电压下降条件（不带延迟条件）的重新充电需要通过燃油表或充电设备/芯片的硬件中断来实现。

`unsigned int fullbatt_uV;`
如果指定了一个非零值，Charger Manager 假定当电池未在充电且电压等于或大于 `fullbatt_uV` 时，电池是满电状态（容量 = 100）

`unsigned int polling_interval_ms;`
所需的轮询间隔（毫秒）。Charger Manager 将以 `polling_interval_ms` 或更频繁的频率轮询此电池。

`enum data_source battery_present;`
CM_BATTERY_PRESENT:
假定电池存在

CM_NO_BATTERY:
假定没有电池

CM_FUEL_GAUGE:
从燃油表获取电池存在信息

CM_CHARGER_STAT:
从充电器获取电池存在信息
```c
char **psy_charger_stat;
```

一个以 `NULL` 结尾的数组，包含充电器的电源类别名称。每个电源类别应该提供 "PRESENT"（如果 `battery_present` 是 "CM_CHARGER_STAT"），"ONLINE"（显示是否连接了外部电源），以及 "STATUS"（显示电池状态为 {"FULL" 或非 FULL} 或 {"FULL", "Charging", "Discharging", "NotCharging"}）

```c
int num_charger_regulators; 
struct regulator_bulk_data *charger_regulators;
```

表示充电器的调节器，采用调节器框架的批量函数形式。

```c
char *psy_fuel_gauge;
```

燃油表的电源类别名称。

```c
int (*temperature_out_of_range)(int *mC); 
bool measure_battery_temp;
```

此回调函数在温度适合充电时返回 0，在温度过热无法充电时返回正数，在温度过冷无法充电时返回负数。通过变量 `mC`，该回调函数返回千分之一摄氏度的温度值。温度源可以是电池温度或环境温度，具体取决于 `measure_battery_temp` 的值。

5. 通知充电管理器充电事件：`cm_notify_event()`
==============================================================

如果需要通知充电管理器有充电事件发生，触发事件的充电设备驱动程序可以调用 `cm_notify_event(psy, type, msg)` 来通知相应的充电管理器。在此函数中，`psy` 是与充电管理器关联的充电驱动程序的 `power_supply` 指针。参数 `type` 与中断类型相同（枚举 `cm_event_types`）。事件消息 `msg` 是可选的，并且仅在事件类型为 "UNDESCRIBED" 或 "OTHERS" 时有效。

6. 其他注意事项
=======================

在充电器/电池相关的事件（如电池拔出、充电器拔出、充电器插入、DCIN 过压/欠压、充电停止等）发生时，系统应配置为唤醒。至少以下情况应使系统从挂起状态唤醒：
a) 充电器开启/关闭
b) 外部电源接入/断开
c) 充电过程中电池插入/拔出

这通常是通过将 PMIC 配置为唤醒源来实现的。
