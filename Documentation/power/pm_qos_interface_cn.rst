===============================
PM 服务质量接口
===============================

此接口提供内核和用户模式的接口，用于在以下参数之一上由驱动程序、子系统和用户空间应用程序注册性能期望值：
两种不同的PM QoS框架可用：
 * CPU延迟QoS
* 每设备PM QoS框架提供了API来管理每设备的延迟约束和PM QoS标志
PM QoS框架中使用的延迟单位是微秒（usec）

1. PM QoS框架
===================

维护了一个全局的CPU延迟QoS请求列表以及一个聚合（有效）目标值。当请求列表或列表元素发生更改时，会更新聚合目标值。对于CPU延迟QoS，列表元素中保存的请求值的最小值即为聚合目标值。

注意：聚合目标值实现为原子变量，以便读取聚合值不需要任何锁定机制。

从内核空间使用此接口很简单：

void cpu_latency_qos_add_request(handle, target_value)：
  将以目标值插入到CPU延迟QoS列表的一个元素。
当此列表发生变化时，将重新计算新目标，并仅在目标值现在不同的情况下调用任何已注册的通知器。
PM QoS的客户端需要保存返回的句柄以供将来在其他PM QoS API函数中使用。

void cpu_latency_qos_update_request(handle, new_target_value)：
  将使用新的目标值更新由句柄指向的列表元素，并重新计算新的聚合目标，如果目标改变则调用通知树。
以下是给定代码和描述的中文翻译：

`void cpu_latency_qos_remove_request(handle):`
这将移除指定元素。移除后，它会更新总体目标值，并在移除请求导致目标值改变的情况下调用通知树。

`int cpu_latency_qos_limit():`
返回CPU延迟QoS的聚合值。

`int cpu_latency_qos_request_active(handle):`
判断请求是否仍然有效，即该请求尚未从CPU延迟QoS列表中移除。

`int cpu_latency_qos_add_notifier(notifier):`
向CPU延迟QoS添加一个通知回调函数。当CPU延迟QoS的聚合值发生变化时，会调用此回调。

`int cpu_latency_qos_remove_notifier(notifier):`
从CPU延迟QoS中移除通知回调函数。

从用户空间的角度：

该基础设施为CPU延迟QoS暴露了一个设备节点，即`/dev/cpu_dma_latency`。
只有进程可以注册PM QoS请求。为了确保自动清理进程，接口要求进程按照以下方式注册其参数请求：
要注册CPU延迟QoS的默认PM QoS目标，进程必须打开`/dev/cpu_dma_latency`。
只要设备节点保持打开状态，该进程就有一个已注册的参数请求。
要更改请求的目标值，进程需要向打开的设备节点写入`s32`类型的值。或者，它可以使用10字符长的格式写入一个十六进制字符串表示该值，例如`"0x12345678"`。这等同于调用`cpu_latency_qos_update_request()`。
要移除用户模式对目标值的请求，只需关闭设备节点。

2. 每设备的PM QoS延迟和标志框架
==================================

对于每个设备，存在三份PM QoS请求列表。其中两份分别维护着恢复延迟和活动状态延迟容忍度（以微秒为单位）的聚合目标值，而第三份则是用于PM QoS标志值。这些值会根据请求列表的变化进行更新。
恢复延迟和活动状态延迟容忍度的目标值仅仅是参数列表元素中请求值的最小值。
PM QoS标志的聚合值是所有列表元素值的集合（位或运算）。目前定义了一个设备PM QoS标志：PM_QOS_FLAG_NO_POWER_OFF
注意：聚合目标值的实现方式使得读取聚合值时无需任何锁定机制。
从内核模式使用此接口的方式如下：

int dev_pm_qos_add_request(device, handle, type, value):
  将向识别出的设备列表中插入一个带有目标值的元素。当这个列表发生变化时，将重新计算新的目标值，并且仅在目标值已改变的情况下调用注册的通知器。
dev_pm_qos的客户端需要保存句柄以便在其他dev_pm_qos API函数中使用。
int dev_pm_qos_update_request(handle, new_value):
  将使用新目标值更新由句柄指向的列表元素，并重新计算新的聚合目标，如果目标值发生变化，则调用通知树。
int dev_pm_qos_remove_request(handle):
  将移除该元素。移除后，它将更新聚合目标，并在移除请求导致目标值改变的情况下调用通知树。
`s32 dev_pm_qos_read_value(device, type):`
返回给定设备约束列表的聚合值。

`enum pm_qos_flags_status dev_pm_qos_flags(device, mask)`
检查给定设备的电源管理服务质量（PM QoS）标志是否与给定的标志掩码相匹配。
返回值的意义如下：

	`PM_QOS_FLAGS_ALL:`
		掩码中的所有标志都被设置
	`PM_QOS_FLAGS_SOME:`
		掩码中的一些标志被设置
	`PM_QOS_FLAGS_NONE:`
		掩码中的任何标志都没有被设置
	`PM_QOS_FLAGS_UNDEFINED:`
		设备的PM QoS结构未初始化，
		或者请求列表为空

`int dev_pm_qos_add_ancestor_request(dev, handle, type, value)`
为给定设备的第一个直接祖先添加一个电源管理服务质量请求，该祖先的power.ignore_children标志未设置（对于DEV_PM_QOS_RESUME_LATENCY请求）
或其power.set_latency_tolerance回调指针不为NULL（对于DEV_PM_QOS_LATENCY_TOLERANCE请求）

`int dev_pm_qos_expose_latency_limit(device, value)`
向设备的电源管理服务质量列表中添加恢复延迟约束请求，并在设备的电源目录下创建sysfs属性pm_qos_resume_latency_us，
允许用户空间操纵该请求。

`void dev_pm_qos_hide_latency_limit(device)`
从设备的电源管理服务质量恢复延迟约束列表中删除由dev_pm_qos_expose_latency_limit()添加的请求，
并从设备的电源目录中移除sysfs属性pm_qos_resume_latency_us。

`int dev_pm_qos_expose_flags(device, value)`
向设备的电源管理服务质量标志列表中添加一个请求，并在设备的电源目录下创建sysfs属性pm_qos_no_power_off，
允许用户空间改变PM_QOS_FLAG_NO_POWER_OFF标志的值。

`void dev_pm_qos_hide_flags(device)`
从设备的电源管理服务质量标志列表中删除由dev_pm_qos_expose_flags()添加的请求，
并从设备的电源目录中移除sysfs属性pm_qos_no_power_off。

通知机制：

每个设备的电源管理服务质量框架都有一个设备专用的通知树。

`int dev_pm_qos_add_notifier(device, notifier, type):`
为设备的特定请求类型添加一个通知回调函数。
当设备约束列表的聚合值发生变化时，回调函数会被调用。
`int dev_pm_qos_remove_notifier(device, notifier, type):`
删除设备的通知回调函数。

**活动状态下的延迟容忍度**

^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^

此设备PM QoS类型用于支持硬件可以即时切换到节能操作模式的系统。在这些系统中，如果硬件选择的操作模式试图以过于激进的方式节省能源，可能会导致软件可见的额外延迟，从而使其无法满足某些协议要求或目标帧率、采样率等。
如果给定设备有可供软件使用的延迟容忍度控制机制，该设备的`dev_pm_info`结构中的`.set_latency_tolerance`回调应被填充。指向它的例程应该实现将有效需求值传递给硬件所需的一切。
每当设备的有效延迟容忍度发生变化时，其`.set_latency_tolerance()`回调将被执行，并将有效值传递给它。如果该值为负数，意味着设备的延迟容忍度需求列表为空，期望回调将底层硬件延迟容忍度控制机制切换到自主模式（如果可用）。反过来，如果该值为`PM_QOS_LATENCY_ANY`，且硬件支持特殊的“无需求”设置，期望回调使用它。这允许软件阻止硬件根据其电源状态变化（例如，在从D3cold过渡到D0期间）自动更新设备的延迟容忍度，通常可以在自主延迟容忍度控制模式下完成。
如果设备存在`.set_latency_tolerance()`，sysfs属性`pm_qos_latency_tolerance_us`将存在于设备的电源目录中。
然后，用户空间可以使用该属性来指定对设备的延迟容忍度需求，如果有的话。向其中写入"any"意味着"无需求，但不要让硬件控制延迟容忍度"，而向其中写入"auto"允许将硬件切换到自主模式，前提是设备列表中没有来自内核侧的其他需求。
内核代码可以使用上述描述的函数以及`DEV_PM_QOS_LATENCY_TOLERANCE`设备PM QoS类型来添加、移除和更新设备的延迟容忍度需求。
