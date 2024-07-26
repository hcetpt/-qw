===============================
PM 服务质量接口
===============================

此接口提供了一个内核和用户模式接口，用于让驱动程序、子系统和用户空间应用程序对某个参数注册性能期望。
存在两种不同的PM服务质量（QoS）框架：
 * CPU延迟QoS
* 每设备PM QoS框架提供了API来管理每设备的延迟约束和PM QoS标志
PM QoS框架中使用的延迟单位是微秒（usec）

1. PM QoS框架
===================

维护了一个全局的CPU延迟QoS请求列表以及一个聚合（有效）的目标值。当请求列表或列表元素发生变化时，聚合目标值会被更新。对于CPU延迟QoS而言，聚合目标值仅仅是列表元素中存储的请求值的最小值。
注意：聚合目标值被实现为原子变量，因此读取聚合值不需要任何锁定机制
从内核空间使用此接口很简单：

void cpu_latency_qos_add_request(handle, target_value):
  将会向CPU延迟QoS列表中插入一个具有目标值的元素
当这个列表发生变化时，将重新计算新的目标值，并且只有当目标值发生变化时才会调用已注册的通知器
PM QoS的客户端需要保存返回的句柄以便将来在其他PM QoS API函数中使用
void cpu_latency_qos_update_request(handle, new_target_value):
  将会使用新的目标值更新由句柄指向的列表元素，并重新计算新的聚合目标值，如果目标值发生变化，则调用通知树
翻译成中文：

`void cpu_latency_qos_remove_request(handle):`
  将移除该元素。移除后，它将更新聚合目标，并在移除请求导致目标发生变化时调用通知树。

`int cpu_latency_qos_limit():`
  返回CPU延迟QoS的聚合值。

`int cpu_latency_qos_request_active(handle):`
  判断请求是否仍然有效，即它尚未从CPU延迟QoS列表中被移除。

`int cpu_latency_qos_add_notifier(notifier):`
  向CPU延迟QoS添加一个通知回调函数。当CPU延迟QoS的聚合值发生改变时，会调用该回调。

`int cpu_latency_qos_remove_notifier(notifier):`
  从CPU延迟QoS中移除通知回调函数。

从用户空间的角度：

基础设施暴露了一个设备节点 `/dev/cpu_dma_latency` 用于CPU延迟QoS。
只有进程可以注册PM QoS请求。为了实现进程的自动清理，接口要求进程以如下方式注册其参数请求：
要注册CPU延迟QoS的默认PM QoS目标，进程必须打开 `/dev/cpu_dma_latency`。
只要设备节点保持打开状态，那么该进程就有一个已注册的参数请求。
要更改请求的目标值，进程需要向打开的设备节点写入一个`s32`类型的值。或者，也可以使用10个字符长度的十六进制字符串格式（例如"0x12345678"）来写入值。这等同于调用 `cpu_latency_qos_update_request()`。
要移除用户模式对目标值的请求，只需关闭设备节点。

2. PM QoS 每设备延迟与标志框架
=================================

对于每个设备，存在三份 PM QoS 请求列表。其中两份分别维护着恢复延迟和活动状态延迟容忍度（以微秒为单位）的汇总目标值，而第三份则用于 PM QoS 标志。这些值会根据请求列表的变化进行更新。
恢复延迟和活动状态延迟容忍度的目标值简单来说就是参数列表元素中请求值的最小值。
PM QoS 标志的汇总值是所有列表元素值的集合（按位或操作）。目前定义了一个设备 PM QoS 标志：PM_QOS_FLAG_NO_POWER_OFF。
注意：汇总的目标值实现方式使得读取这些汇总值时不需要任何锁定机制。
从内核模式使用此接口的方式如下：

int dev_pm_qos_add_request(device, handle, type, value):
  将向已识别设备的列表中插入一个带有目标值的元素。当这个列表发生变化时，将重新计算新的目标值，并仅在目标值改变的情况下调用注册的通知器。
dev_pm_qos 的客户端需要保存句柄以便将来在其他 dev_pm_qos API 函数中使用。
int dev_pm_qos_update_request(handle, new_value):
  将通过句柄更新列表中的元素为目标的新值，并重新计算汇总目标值，如果目标值发生变化，则调用通知树。
int dev_pm_qos_remove_request(handle):
  将移除该元素。移除后，它会更新汇总目标值，并在移除请求导致目标值变化的情况下调用通知树。
以下是提供的函数和通知机制的中文翻译：

`s32 dev_pm_qos_read_value(device, type):`
  返回给定设备约束列表中特定类型的聚合值。

`enum pm_qos_flags_status dev_pm_qos_flags(device, mask)`
  使用给定的标志掩码检查给定设备的电源管理服务质量（PM QoS）标志。
返回值的含义如下：

    `PM_QOS_FLAGS_ALL:`
        掩码中的所有标志都被设置。
    `PM_QOS_FLAGS_SOME:`
        掩码中的一些标志被设置。
    `PM_QOS_FLAGS_NONE:`
        掩码中的任何标志都没有被设置。
    `PM_QOS_FLAGS_UNDEFINED:`
        设备的电源管理服务质量结构尚未初始化，
        或请求列表为空。

`int dev_pm_qos_add_ancestor_request(dev, handle, type, value)`
  对于给定设备，向第一个直接祖先添加一个电源管理服务质量请求。该祖先的`power.ignore_children`标志未设置（对于`DEV_PM_QOS_RESUME_LATENCY`请求）
  或其`power.set_latency_tolerance`回调指针不为`NULL`（对于`DEV_PM_QOS_LATENCY_TOLERANCE`请求）。

`int dev_pm_qos_expose_latency_limit(device, value)`
  向设备的电源管理服务质量恢复延迟约束列表中添加一个请求，并在设备的电源目录下创建名为`pm_qos_resume_latency_us`的sysfs属性，允许用户空间操纵该请求。

`void dev_pm_qos_hide_latency_limit(device)`
  从设备的电源管理服务质量恢复延迟约束列表中移除由`dev_pm_qos_expose_latency_limit()`添加的请求，并删除设备电源目录下的`pm_qos_resume_latency_us` sysfs属性。

`int dev_pm_qos_expose_flags(device, value)`
  向设备的电源管理服务质量标志列表中添加一个请求，并在设备的电源目录下创建名为`pm_qos_no_power_off`的sysfs属性，允许用户空间更改`PM_QOS_FLAG_NO_POWER_OFF`标志的值。

`void dev_pm_qos_hide_flags(device)`
  从设备的电源管理服务质量标志列表中移除由`dev_pm_qos_expose_flags()`添加的请求，并删除设备电源目录下的`pm_qos_no_power_off` sysfs属性。

**通知机制：**

每个设备的电源管理服务质量框架都有一个每设备的通知树。

`int dev_pm_qos_add_notifier(device, notifier, type):`
  为设备针对特定请求类型添加一个通知回调函数。
回调函数在设备约束列表的聚合值发生变化时被调用。
```
int dev_pm_qos_remove_notifier(device, notifier, type):
```
这会移除设备的通知回调函数。

**活动状态下的延迟容忍度**

^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^

这种设备PM QoS类型用于支持硬件可以即时切换到节能操作模式的系统。在这些系统中，如果硬件选择的操作模式过于激进地尝试节省能源，可能会导致软件可见的额外延迟，进而使得软件无法满足某些协议要求或目标帧率、采样率等。

如果对于给定设备存在可供软件使用的延迟容忍度控制机制，该设备的`dev_pm_info`结构中的`.set_latency_tolerance`回调应当被填充。所指向的例程应当实现将有效需求值传递给硬件所需的一切。

每当设备的有效延迟容忍度发生变化时，其`.set_latency_tolerance()`回调就会被执行，并将有效值传给它。如果该值为负数，意味着设备的延迟容忍度需求列表为空，期望回调将底层硬件的延迟容忍度控制机制切换到自主模式（如果可用）。如果该值为`PM_QOS_LATENCY_ANY`，并且硬件支持一种特殊的“无要求”设置，则期望回调使用该设置。这允许软件阻止硬件根据其电源状态变化（例如从D3cold到D0的过渡）自动更新设备的延迟容忍度，通常这可以在自主延迟容忍度控制模式下完成。

如果设备存在`.set_latency_tolerance()`，那么在设备的电源目录中将会存在sysfs属性`pm_qos_latency_tolerance_us`。
这样，用户空间就可以使用该属性来指定对设备的延迟容忍度需求（如果有的话）。向其中写入"any"表示“无要求，但不允许硬件控制延迟容忍度”，而写入"auto"则允许硬件在没有来自内核侧的其他需求时切换到自主模式。

内核代码可以使用上述描述的函数以及`DEV_PM_QOS_LATENCY_TOLERANCE`设备PM QoS类型来添加、移除和更新设备的延迟容忍度需求。
