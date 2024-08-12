======================
通用热Sysfs驱动程序使用说明
======================

作者：Sujith Thomas <sujith.thomas@intel.com>，张瑞 <rui.zhang@intel.com>

更新日期：2008年1月2日

版权所有 © 2008 Intel公司


0. 引言
=======

通用热Sysfs提供了一套接口供热区设备（传感器）和热冷却设备（风扇、处理器等）注册到热管理解决方案中并成为其中的一部分。
本使用说明侧重于使新的热区和冷却设备能够参与到热管理中来。
此解决方案与平台无关，任何类型的热区设备和冷却设备都应该能够利用这一基础设施。
热Sysfs驱动程序的主要任务是将热区属性及冷却设备属性暴露给用户空间。
智能的热管理应用程序可以根据来自热区属性的输入（当前温度和临界点温度）做出决策，并对适当的设备进行调节。
- `[0-*]` 表示从0开始的任意正数
- `[1-*]` 表示从1开始的任意正数

1. 热Sysfs驱动程序接口函数
==================================

1.1 热区设备接口
-------------------

    ::

    struct thermal_zone_device
    *thermal_zone_device_register(char *type,
                                  int trips, int mask, void *devdata,
                                  struct thermal_zone_device_ops *ops,
                                  const struct thermal_zone_params *tzp,
                                  int passive_delay, int polling_delay)

    此接口函数将一个新的热区设备（传感器）添加到/sys/class/thermal文件夹下，命名为`thermal_zone[0-*]`。它会尝试绑定所有同时注册的热冷却设备。
type:
    热区类型
trips:
    此热区支持的临界点总数
mask:
    位字符串：如果第'n'位被设置，则第'n'个临界点可写
devdata:
    设备私有数据
ops:
    热区设备回调
.bind:
	将热区设备与一个散热设备绑定
.unbind:
	解除热区设备与一个散热设备的绑定
.get_temp:
	获取热区的当前温度
.set_trips:
	设置触发点窗口。每当更新当前温度时，会立即找到当前温度之下的和之上的触发点
.get_mode:
	获取热区的当前模式（启用/禁用）
- "启用" 意味着内核热管理已启用
- "禁用" 将阻止内核热驱动程序在触发点上采取行动，以便用户应用程序可以负责热管理
.set_mode:
	设置热区的模式（启用/禁用）
.get_trip_type:
	获取特定触发点的类型
.get_trip_temp:
	获取特定触发点将在其之上被触发的温度
翻译如下：

.set_emul_temp:  
    设置仿真温度，这有助于调试不同的阈值温度点。

tzp:  
    热区域平台参数

passive_delay:  
    在进行被动冷却时，每次轮询之间等待的毫秒数。

polling_delay:  
    在检查是否已越过阈值点时，每次轮询之间等待的毫秒数（对于中断驱动系统为0）。
::

    void thermal_zone_device_unregister(struct thermal_zone_device *tz)

    此接口函数移除热区域设备。它会从/sys/class/thermal目录中删除对应的条目，并解除绑定所有使用的热冷却设备。
::

    struct thermal_zone_device *thermal_zone_of_sensor_register(struct device *dev, int sensor_id, void *data, const struct thermal_zone_of_device_ops *ops)

    此接口向设备树描述的热区域中添加一个新的传感器。此函数会在设备树中搜索指向由`dev->of_node`所指传感器设备作为温度提供者的热区域。对于指向传感器节点的热区域，该传感器将被加入到设备树热区域设备中。
    对于此接口的参数说明如下：

    dev:  
        包含有效节点指针`dev->of_node`的传感器设备节点。

    sensor_id:  
        传感器标识符，在传感器IP包含多个传感器的情况下使用。

    data:  
        一个私有指针（归调用者所有），当需要读取温度数据时会被传递回去。
下面是给定内容的中文翻译：

```plaintext
struct thermal_zone_of_device_ops *
=====================  =======================================
get_temp           指向一个读取传感器温度的函数的指针。这是由传感器驱动程序提供的必需回调。
set_trips          指向一个设置温度窗口的函数的指针。当离开这个窗口时，驱动程序必须通过 thermal_zone_device_update 告知热核心。
get_trend          指向一个读取传感器温度趋势的函数的指针。
set_emul_temp      指向一个设置模拟传感器温度的函数的指针。
=====================  =======================================

热区域的温度是由 thermal_zone_of_device_ops 中的 get_temp() 函数指针提供的。当被调用时，它将返回私有指针 @data。
如果失败则返回错误指针，否则返回有效的热区域设备句柄。调用者应使用 IS_ERR() 检查返回的句柄以判断是否成功。

::

    void thermal_zone_of_sensor_unregister(struct device *dev,
                                           struct thermal_zone_device *tzd)

此接口用于从 DT 热区域中注销一个之前通过 thermal_zone_of_sensor_register() 接口成功添加的传感器。
此函数会移除与 thermal_zone_of_sensor_register() 接口注册的热区域设备相关的传感器回调和私有数据。同时，该函数还会通过移除 .get_temp() 和 get_trend() 热区域设备回调来使区域静默。

::

    struct thermal_zone_device
    *devm_thermal_zone_of_sensor_register(struct device *dev,
                                          int sensor_id,
                                          void *data,
                                          const struct thermal_zone_of_device_ops *ops)

此接口是 thermal_zone_of_sensor_register() 的资源管理版本。
```

请注意，代码块中的 `::` 表示的是伪代码或文档注释中的分隔符，并非实际代码的一部分。
在第1.1.3节中描述的所有关于`thermal_zone_of_sensor_register()`的细节在此处同样适用。
使用此接口注册传感器的好处是，在错误路径或驱动程序解绑期间无需显式调用`thermal_zone_of_sensor_unregister()`，因为这些操作由驱动资源管理器自动完成。

```c
void devm_thermal_zone_of_sensor_unregister(struct device *dev,
                                             struct thermal_zone_device *tzd);
```

此接口是`thermal_zone_of_sensor_unregister()`的资源管理版本。在第1.1.4节中描述的所有关于`thermal_zone_of_sensor_unregister()`的细节在此处同样适用。
通常情况下，不需要调用此函数，因为资源管理代码会确保资源被释放。

```c
int thermal_zone_get_slope(struct thermal_zone_device *tz);
```

此接口用于读取热区域设备的斜率属性值，这对平台驱动程序进行温度计算可能有用。

```c
int thermal_zone_get_offset(struct thermal_zone_device *tz);
```

此接口用于读取热区域设备的偏移量属性值，这对平台驱动程序进行温度计算可能有用。

### 1.2 热冷却设备接口

```c
struct thermal_cooling_device *
thermal_cooling_device_register(char *name,
                                void *devdata, struct thermal_cooling_device_ops *);
```

此接口函数向`/sys/class/thermal/`目录下添加一个新的热冷却设备（如风扇、处理器等），名称为`cooling_device[0-*]`。它试图与所有同时注册的热区域设备绑定。
- **name:** 冷却设备名称
- **devdata:** 设备私有数据
:: 
 热冷却设备回调
.get_max_state: 
	获取热冷却设备的最大节流状态
.get_cur_state: 
	获取热冷却设备当前请求的节流状态
.set_cur_state: 
	设置热冷却设备的当前节流状态
::

 void thermal_cooling_device_unregister(struct thermal_cooling_device *cdev)

    此接口函数移除热冷却设备。
它从/sys/class/thermal目录中删除相应的条目，并
    使所有使用该设备的热区域设备与之解除绑定。
1.3 绑定热区域设备与热冷却设备的接口
-----------------------------------------------------------------------------

    ::

	int thermal_zone_bind_cooling_device(struct thermal_zone_device *tz,
		int trip, struct thermal_cooling_device *cdev,
		unsigned long upper, unsigned long lower, unsigned int weight);

    此接口函数将一个热冷却设备绑定到特定热区域设备的一个触发点上。
此函数通常在热区域设备的.bind回调中被调用。
tz:
	热区域设备
cdev:
	热冷却设备
trip:
	指示热冷却设备关联的热区域中的哪一个触发点
upper:
	此触发点的最大冷却状态
### 翻译

`THERMAL_NO_LIMIT`表示没有上限，
并且冷却设备可以处于最大状态。

较低：
对于此临界点，可以使用最低冷却状态。
`THERMAL_NO_LIMIT`表示没有下限，
并且冷却设备可以处于冷却状态0。

权重：
在该热区中，此冷却设备的影响。更多详情请参见下面1.4.1节。

```c
int thermal_zone_unbind_cooling_device(struct thermal_zone_device *tz,
                int trip, struct thermal_cooling_device *cdev);
```

此接口函数从特定热区设备的临界点解除绑定一个热冷却设备。此函数通常在热区设备的.unbind回调中被调用。
- `tz`: 热区设备
- `cdev`: 热冷却设备
- `trip`: 指示在此热区中，冷却设备与哪个临界点相关联

#### 1.4 热区参数
------------------------

```c
struct thermal_zone_params
```

此结构体定义了热区的平台级参数。
对于每个热区，这些数据应该来自平台层。
这是一个可选功能，某些平台可以选择不提供这些数据。
- `.governor_name`: 用于此区域的热管理器名称
- `.no_hwmon`: 布尔值，指示是否需要热到硬件监控(sysfs)接口。当`no_hwmon == false`时，将创建一个硬件监控(sysfs)接口；当`no_hwmon == true`时，则不会做任何事情。
如果`thermal_zone_params`为NULL，则会创建hwmon接口（为了向后兼容）。

2. sysfs属性结构
=============================

==	================
RO	只读值
WO	写入专用值
RW	读写值
==	================

热相关的sysfs属性位于`/sys/class/thermal`下。
如果hwmon被编译进内核或作为模块构建，hwmon的sysfs接口扩展也位于`/sys/class/hwmon`下。
当注册一个热区域设备时创建的热区域设备sysfs接口如下：

  `/sys/class/thermal/thermal_zone[0-*]`:
    |---type:			热区域类型
    |---temp:			当前温度
    |---mode:			热区域的工作模式
    |---policy:			用于此区域的热管理器
    |---available_policies:	此区域可用的热管理器
    |---trip_point_[0-*]_temp:	触发点温度
    |---trip_point_[0-*]_type:	触发点类型
    |---trip_point_[0-*]_hyst:	此触发点的滞后值
    |---emul_temp:		模拟温度设置节点
    |---sustainable_power:      可持续散发的功率
    |---k_po:                   温度过高时的比例项
    |---k_pu:                   温度过低时的比例项
    |---k_i:                    功率分配管理器中PID的积分项
    |---k_d:                    功率分配管理器中PID的微分项
    |---integral_cutoff:        超过该偏移量时累积误差
    |---slope:                  作为线性外推应用的斜率常数
    |---offset:                 作为线性外推应用的偏移常数

当注册一个冷却设备时创建的热冷却设备sysfs接口如下：

  `/sys/class/thermal/cooling_device[0-*]`:
    |---type:			冷却设备类型（如处理器/风扇/…）
    |---max_state:		冷却设备的最大冷却状态
    |---cur_state:		冷却设备的当前冷却状态
    |---stats:			包含冷却设备统计信息的目录
    |---stats/reset:		写入任何值以重置统计信息
    |---stats/time_in_state_ms:	在各种冷却状态下花费的时间（毫秒）
    |---stats/total_trans:	冷却状态改变的总次数
    |---stats/trans_table:	冷却状态转换表

接下来创建和删除的两个动态属性是成对出现的。它们代表了热区域与其关联的冷却设备之间的关系。
对于每次成功执行`thermal_zone_bind_cooling_device`/`thermal_zone_unbind_cooling_device`，都会创建/删除这些属性：

  `/sys/class/thermal/thermal_zone[0-*]`:
    |---cdev[0-*]:		当前热区域中的第[0-*]个冷却设备
    |---cdev[0-*]_trip_point:	cdev[0-*]与之关联的触发点
    |---cdev[0-*]_weight:       此冷却设备在此热区域中的影响程度

除了热区域设备sysfs接口和冷却设备sysfs接口之外，通用热驱动程序还为每种类型的热区域设备创建一个hwmon sysfs接口。
例如，通用热驱动程序为所有已注册的ACPI热区域注册一个hwmon类设备并构建相应的hwmon sysfs接口。
请参阅`Documentation/ABI/testing/sysfs-class-thermal`获取关于热区域和冷却设备属性的详细信息：

  `/sys/class/hwmon/hwmon[0-*]`:
    |---name:			热区域设备的类型
    |---temp[1-*]_input:	热区域[1-*]的当前温度
    |---temp[1-*]_critical:	热区域[1-*]的关键触发点

请参阅`Documentation/hwmon/sysfs-interface.rst`获取更多信息。

3. 简单实现
==========================

ACPI热区域可能支持多个触发点，如关键、过热、被动、主动等。
如果一个ACPI热区域同时支持关键、被动、主动[0]和主动[1]，则它可以作为一个具有四个触发点的热区域设备（thermal_zone1）进行注册。
它有一个处理器和一个风扇，这两个都被注册为热冷却设备。两者都被认为在冷却热区域方面具有相同的效果。
如果处理器在_PSL方法中列出，而风扇在_AL0方法中列出，则系统接口结构将构建如下：

/sys/class/thermal:
|thermal_zone1:
    |---type:			acpitz
    |---temp:			37000
    |---mode:			enabled
    |---policy:			step_wise
    |---available_policies:	step_wise fair_share
    |---trip_point_0_temp:	100000
    |---trip_point_0_type:	critical
    |---trip_point_1_temp:	80000
    |---trip_point_1_type:	passive
    |---trip_point_2_temp:	70000
    |---trip_point_2_type:	active0
    |---trip_point_3_temp:	60000
    |---trip_point_3_type:	active1
    |---cdev0:			--->/sys/class/thermal/cooling_device0
    |---cdev0_trip_point:	1	/* cdev0 可用于被动模式 */
    |---cdev0_weight:           1024
    |---cdev1:			--->/sys/class/thermal/cooling_device3
    |---cdev1_trip_point:	2	/* cdev1 可用于 active[0] */
    |---cdev1_weight:           1024

|cooling_device0:
    |---type:			Processor
    |---max_state:		8
    |---cur_state:		0

|cooling_device3:
    |---type:			Fan
    |---max_state:		2
    |---cur_state:		0

/sys/class/hwmon:
|hwmon0:
    |---name:			acpitz
    |---temp1_input:		37000
    |---temp1_crit:		100000

4. 导出符号APIs
=====================

4.1. get_tz_trend
-----------------

此函数返回热区的趋势，即热区温度变化率。理想情况下，热传感器驱动程序应实现回调功能。如果没有实现，热框架通过比较前一个和当前的温度值来计算趋势。
4.2. get_thermal_instance
-------------------------

此函数根据给定的 {thermal_zone, cooling_device, trip_point} 组合返回对应的 thermal_instance。如果不存在这样的实例，则返回 NULL。
4.3. thermal_cdev_update
------------------------

此函数作为仲裁者设置冷却设备的状态。尽可能地将冷却设备设置为最深的冷却状态。

5. thermal_emergency_poweroff
=============================

当达到临界阈温时，热框架会通过调用 hw_protection_shutdown() 来关闭系统。hw_protection_shutdown() 首先尝试进行有序关机，但接受一定延迟后继续执行强制关机或作为最后手段的紧急重启。
应仔细评估这个延迟时间以确保有足够的时间完成有序关机。
如果将延迟设置为0，则不支持紧急关机。因此，要触发紧急关机，必须设置一个经过仔细评估的非零正值。
