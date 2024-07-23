充电器管理器
=============

（版权所有）2011年，Ham MyungJoo <myungjoo.ham@samsung.com>，遵循GPL协议

充电器管理器提供了内核中的电池充电器管理功能，该功能在挂起到RAM状态时需要温度监控，并且每个电池可能有多个充电器连接，用户空间希望查看多个充电器的聚合信息。充电器管理器是一个带有电源供应类条目的平台驱动程序。一个充电器管理器实例（通过充电器管理器创建的平台设备）代表了一个独立的电池及其充电器。如果系统中存在多个具有各自独立充电器的电池，则系统可能需要多个充电器管理器实例。

1. 引言
=========

充电器管理器支持以下功能：

* 支持多个充电器（例如，具有USB、交流电和太阳能板的设备）
    系统可能有多个充电器（或电源），并且它们中的一些可能同时激活。每个充电器可能有自己的电源供应类，每个电源供应类可以提供关于电池状态的不同信息。此框架从多个来源聚合与充电器相关的信息，并将其作为单一电源供应类显示综合信息。
* 支持在挂起到RAM时的轮询（使用suspend_again回调）
    当电池正在充电且系统处于挂起到RAM状态时，我们可能需要通过检查环境或电池温度来监测电池健康状况。我们可以通过周期性唤醒系统来实现这一点。然而，这种方法为了监测电池健康和任务以及本应保持挂起状态的用户进程而不必要的唤醒设备，反过来，这会导致不必要的电力消耗并减慢充电过程。或者甚至，这种峰值电力消耗可能在充电过程中停止充电器（外部电力输入<设备电力消耗），这不仅影响充电时间，而且影响电池寿命。
    充电器管理器提供了一个函数“cm_suspend_again”，它可以作为platform_suspend_ops的suspend_again回调。如果平台需要除cm_suspend_again之外的任务，它可能实现自己的suspend_again回调，在其中调用cm_suspend_again。
    通常情况下，平台将需要恢复和挂起充电器管理器使用的某些设备。
* 支持过早的满电事件处理
    如果在满电事件后经过“fullbatt_vchkdrop_ms”时间，电池电压下降了“fullbatt_vchkdrop_uV”，框架将重新开始充电。此检查也在挂起状态下执行，相应设置唤醒时间并使用suspend_again。
* 支持uevent通知
    在与充电器相关的事件中，设备向用户发送UEVENT通知。

2. 与suspend_again相关的全局充电器管理器数据
================================================

为了使用挂起再启动功能（挂起中的监控）设置充电器管理器，用户应该使用setup_charger_manager(`struct charger_global_desc *`)提供charger_global_desc。
此`charger_global_desc`数据用于挂起期间的监控，如其名称所示，是全局的。因此，即使有多个电池，用户也只需提供一次。如果有多个电池，则多个`Charger Manager`实例将共享同一个`charger_global_desc`，它将为所有`Charger Manager`实例管理挂起期间的监控。为了激活挂起期间的监控，用户需要正确地向`struct charger_global_desc`提供以下三个条目：

`char *rtc_name;`
这是用于通过`Charger Manager`从挂起状态唤醒系统的RTC（例如，“rtc0”）的名称。RTC的报警中断（AIE）应该能够从挂起状态唤醒系统。`Charger Manager`会保存和恢复报警值，并使用先前定义的报警值（如果它将在`Charger Manager`之前触发），以确保`Charger Manager`不会干扰先前定义的报警。

`bool (*rtc_only_wakeup)(void);`
这个回调函数应告知`CM`唤醒是否仅由同一结构中的“rtc”的报警引起。如果有其他唤醒源触发了唤醒，则应回答`false`。如果“rtc”是唯一的唤醒原因，则应回答`true`。

`bool assume_timer_stops_in_suspend;`
如果为`true`，则`Charger Manager`假设在挂起期间计时器（`CM`使用`jiffies`作为计时器）停止运行。那么，`CM`假定挂起持续时间与报警长度相同。

3. 如何设置`suspend_again`
======================
`Charger Manager`提供了一个函数`extern bool cm_suspend_again(void)`。当调用`cm_suspend_again`时，它会监控每个电池。系统的平台`suspend_ops`可以调用`cm_suspend_again`函数来判断`Charger Manager`是否希望再次进入挂起状态。
如果没有其他设备或任务希望使用`suspend_again`功能，平台`suspend_ops`可以直接引用`cm_suspend_again`作为它的`suspend_again`回调。
如果系统被`Charger Manager`唤醒且轮询（挂起期间的监控）结果为“正常”，`cm_suspend_again()`将返回`true`（意味着“我想再次进入挂起状态”）。

4. `Charger-Manager` 数据 (`struct charger_desc`)
=============================================
对于每个独立于其他电池充电的电池（如果一系列电池由单个充电器充电，则它们被视为一个独立电池），都会有一个`Charger Manager`实例与之关联。以下是`struct charger_desc`中的一些元素：

`char *psy_name;`
这是电池的电源供应类名称，默认为“battery”，如果`psy_name`为`NULL`。用户可以在`/sys/class/power_supply/[psy_name]/`处访问这些`psy`条目。

`enum polling_modes polling_mode;`
    `CM_POLL_DISABLE`: 不对这个电池进行轮询
以下是给定文本的中文翻译：

`CM_POLL_ALWAYS:`  
始终轮询此电池

`CM_POLL_EXTERNAL_POWER_ONLY:`  
仅在连接外部电源时轮询此电池

`CM_POLL_CHARGING_ONLY:`  
仅在电池正在充电时轮询此电池

`unsigned int fullbatt_vchkdrop_ms;`  
`unsigned int fullbatt_vchkdrop_uV;`  
如果两者都有非零值，充电管理器将在电池完全充满后`fullbatt_vchkdrop_ms`毫秒检查电池电压下降。如果电压下降超过`fullbatt_vchkdrop_uV`微伏，充电管理器将尝试通过禁用和启用充电器来重新充电电池。仅基于电压下降条件（无延迟条件）的再充电需要通过来自燃料计或充电设备/芯片的硬件中断来实现。

`unsigned int fullbatt_uV;`  
如果指定非零值，充电管理器假设如果电池未处于充电状态且电池电压等于或大于`fullbatt_uV`微伏，则电池已充满（容量=100）

`unsigned int polling_interval_ms;`  
要求的轮询间隔（以毫秒为单位）。充电管理器将以`polling_interval_ms`或更频繁的时间间隔轮询此电池

`enum data_source battery_present;`  
`CM_BATTERY_PRESENT:`  
假设电池存在

`CM_NO_BATTERY:`  
假设不存在电池

`CM_FUEL_GAUGE:`  
从燃料计获取电池存在信息

`CM_CHARGER_STAT:`  
从充电器获取电池存在信息
```c
// char **psy_charger_stat;
// 这是一个以NULL结尾的数组，包含充电器的电源类别名称。
// 每个电源类别应当提供 "PRESENT"（如果battery_present为"CM_CHARGER_STAT"），
// "ONLINE"（显示外部电源是否已连接），以及 "STATUS"（显示电池是否{"FULL" 或 不是 "FULL"} 
// 或者 {"FULL", "Charging", "Discharging", "NotCharging"}）

int num_charger_regulators; 
struct regulator_bulk_data *charger_regulators;
// 表示充电器的调节器，形式适合调节器框架的大批量功能。

char *psy_fuel_gauge;
// 燃料表的电源类别名称。

int (*temperature_out_of_range)(int *mC); 
bool measure_battery_temp;
// 此回调函数在温度适宜充电时返回0，在温度过热无法充电时返回正数，
// 在温度过冷无法充电时返回负数。通过变量mC，此回调函数返回千分之一摄氏度的温度值。
// 温度源根据measure_battery_temp的值可以是电池或环境温度。

// 如果需要通知充电管理器有关充电器事件的信息：
// cm_notify_event()
// =======================================================
// 如果有需要通知充电管理器的充电器事件，触发该事件的充电器设备驱动程序可以通过调用
// cm_notify_event(psy, type, msg)来通知相应的充电管理器。
// 在这个函数中，psy是指向充电器驱动程序的power_supply结构的指针，它与充电管理器相关联。
// 参数"type"与中断类型相同（cm_event_types枚举）。事件消息"msg"是可选的，仅当事件类型为"UNDESCRIBED"或"OTHERS"时才有效。

// 其他考虑因素
// ==============
// 对于如电池拔出、充电器拔出、充电器插入、DCIN过压/欠压、充电停止等与充电器和电池相关的事件，
// 系统应当配置为被唤醒。
// 至少以下情况应能从挂起状态唤醒系统：
// a) 充电器开/关 b) 外部电源插/拔 c) 电池插/拔（在充电过程中）
// 这通常是通过将PMIC配置为唤醒源来实现的。
```
