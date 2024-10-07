===============================
PM 服务质量接口
===============================

此接口提供了内核和用户模式下的接口，允许驱动程序、子系统和用户空间应用程序对某个参数注册性能期望值。
有两种不同的 PM QoS 框架：
 * CPU 延迟 QoS
* 每设备 PM QoS 框架提供了管理每设备延迟约束和 PM QoS 标志的 API
PM QoS 框架中使用的延迟单位是微秒（usec）

1. PM QoS 框架
===================

维护了一个全局的 CPU 延迟 QoS 请求列表以及一个聚合（有效）目标值。聚合目标值会随着请求列表或列表元素的变化而更新。对于 CPU 延迟 QoS，聚合目标值仅仅是列表元素中所持有的请求值中的最小值。
注意：聚合目标值被实现为一个原子变量，因此读取聚合值不需要任何锁定机制。
从内核空间使用此接口非常简单：

void cpu_latency_qos_add_request(handle, target_value)：
  将以目标值插入到 CPU 延迟 QoS 列表中
当此列表发生变化时，将重新计算新的目标值，并且仅在目标值发生变化时调用所有已注册的通知器
PM QoS 的客户端需要保存返回的句柄以便将来在其他 PM QoS API 函数中使用
void cpu_latency_qos_update_request(handle, new_target_value)：
  将使用新的目标值更新由句柄指向的列表元素，并重新计算新的聚合目标值，如果目标值发生变化，则调用通知树
```python
def cpu_latency_qos_remove_request(handle):
    """
    将移除指定元素。移除后，它将更新聚合目标，并在移除请求导致目标变化的情况下调用通知树。
    """
def cpu_latency_qos_limit():
    """
    返回 CPU 延迟 QoS 的聚合值。
    """
def cpu_latency_qos_request_active(handle):
    """
    检查请求是否仍然有效，即该请求尚未从 CPU 延迟 QoS 列表中移除。
    """
def cpu_latency_qos_add_notifier(notifier):
    """
    向 CPU 延迟 QoS 添加一个通知回调函数。当 CPU 延迟 QoS 的聚合值发生变化时，会调用此回调。
    """
def cpu_latency_qos_remove_notifier(notifier):
    """
    从 CPU 延迟 QoS 中移除一个通知回调函数。
    """

# 用户空间

# 该基础设施暴露了一个设备节点 /dev/cpu_dma_latency 用于 CPU 延迟 QoS。
# 只有进程可以注册 PM QoS 请求。为了自动清理进程，接口要求进程以如下方式注册其参数请求：
# 要为 CPU 延迟 QoS 注册默认的 PM QoS 目标，进程必须打开 /dev/cpu_dma_latency。
# 只要保持设备节点处于打开状态，该进程就有一个已注册的参数请求。
# 要更改请求的目标值，进程需要向打开的设备节点写入一个 s32 值。或者，也可以使用 10 字符长度的格式写入一个十六进制字符串（例如 "0x12345678"）。这相当于调用 cpu_latency_qos_update_request()。
```

希望这个翻译对你有帮助！如果你有任何其他问题，请告诉我。
要移除用户模式对目标值的请求，只需关闭设备节点。

2. PM QoS 每设备延迟和标志框架
=================================

对于每个设备，有三个PM QoS请求列表。其中两个列表维护着恢复延迟和活动状态延迟容忍度（以微秒为单位）的聚合目标值，第三个列表用于PM QoS 标志。这些值会根据请求列表的变化进行更新。
恢复延迟和活动状态延迟容忍度的目标值是参数列表元素中请求值的最小值。
PM QoS 标志的聚合值是对所有列表元素值进行聚集（按位或）的结果。目前定义了一个设备PM QoS标志：PM_QOS_FLAG_NO_POWER_OFF。
注意：聚合目标值的实现方式使得读取聚合值不需要任何锁定机制。
从内核模式使用此接口的方法如下：

int dev_pm_qos_add_request(device, handle, type, value)：
  将在识别到的设备列表中插入一个带有目标值的元素。当该列表发生变化时，将重新计算新的目标值，并且仅当目标值改变时才会调用已注册的通知器。
dev_pm_qos 的客户端需要保存句柄以便将来在其他dev_pm_qos API函数中使用。

int dev_pm_qos_update_request(handle, new_value)：
  将使用新目标值更新由句柄指向的列表元素，并重新计算新的聚合目标值。如果目标值发生变化，则调用通知树。

int dev_pm_qos_remove_request(handle)：
  将移除该元素。移除后，将更新聚合目标值，并且如果移除请求导致目标值发生变化，则调用通知树。
```s32 dev_pm_qos_read_value(device, type):
返回给定设备约束列表中的聚合值。

enum pm_qos_flags_status dev_pm_qos_flags(device, mask)
检查给定设备的 PM QoS 标志是否符合给定的标志掩码。
返回值的意义如下：

    PM_QOS_FLAGS_ALL:
        掩码中的所有标志都已设置
    PM_QOS_FLAGS_SOME:
        掩码中的一部分标志已设置
    PM_QOS_FLAGS_NONE:
        掩码中的任何标志都没有设置
    PM_QOS_FLAGS_UNDEFINED:
        设备的 PM QoS 结构尚未初始化，或者请求列表为空

int dev_pm_qos_add_ancestor_request(dev, handle, type, value)
为给定设备的第一个直接祖先添加一个 PM QoS 请求，该祖先的 power.ignore_children 标志未设置（对于 DEV_PM_QOS_RESUME_LATENCY 请求），
或者其 power.set_latency_tolerance 回调指针不为 NULL（对于 DEV_PM_QOS_LATENCY_TOLERANCE 请求）

int dev_pm_qos_expose_latency_limit(device, value)
将一个恢复延迟约束请求添加到设备的 PM QoS 列表中，并在设备的电源目录下创建一个 sysfs 属性 `pm_qos_resume_latency_us`，
允许用户空间操作该请求

void dev_pm_qos_hide_latency_limit(device)
从设备的 PM QoS 恢复延迟约束列表中移除由 dev_pm_qos_expose_latency_limit() 添加的请求，并删除设备电源目录下的 sysfs 属性 `pm_qos_resume_latency_us`

int dev_pm_qos_expose_flags(device, value)
将一个标志请求添加到设备的 PM QoS 列表中，并在设备的电源目录下创建一个 sysfs 属性 `pm_qos_no_power_off`，
允许用户空间更改 PM_QOS_FLAG_NO_POWER_OFF 标志的值

void dev_pm_qos_hide_flags(device)
从设备的 PM QoS 标志列表中移除由 dev_pm_qos_expose_flags() 添加的请求，并删除设备电源目录下的 sysfs 属性 `pm_qos_no_power_off`

通知机制：

每个设备的 PM QoS 框架都有一个特定于设备的通知树
int dev_pm_qos_add_notifier(device, notifier, type)
为设备针对特定类型的请求添加一个通知回调函数
```
回调函数在设备约束列表的聚合值发生变化时被调用。

```c
int dev_pm_qos_remove_notifier(device, notifier, type):
```
移除设备的通知回调函数。

### 激活状态下的延迟容忍度

^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^

这种设备 PM QoS 类型用于支持硬件可以在运行时切换到节能模式的系统。在这些系统中，如果硬件选择的操作模式过于激进地尝试节省能源，可能会导致软件中出现过大的延迟，从而导致错过某些协议要求或目标帧率或采样率等。

如果给定设备有可用的延迟容忍度控制机制，则该设备的 `dev_pm_info` 结构中的 `.set_latency_tolerance` 回调应该被填充。该回调指向的函数应实现将有效要求值传递给硬件所需的一切操作。

每当设备的有效延迟容忍度发生变化时，其 `.set_latency_tolerance()` 回调将被执行，并将有效值传递给它。如果该值为负数，这意味着设备的延迟容忍度要求列表为空，回调函数应将底层硬件延迟容忍度控制机制切换到自主模式（如果可用）。如果该值为 `PM_QOS_LATENCY_ANY` 并且硬件支持一种特殊的“无要求”设置，则回调函数应使用该设置。这允许软件防止硬件在响应其电源状态变化时（例如从 D3cold 切换到 D0）自动更新设备的延迟容忍度，通常这种情况下可以使用自主延迟容忍度控制模式。

如果设备存在 `.set_latency_tolerance()` 回调，则在设备的电源目录中将存在 sysfs 属性 `pm_qos_latency_tolerance_us`。这样，用户空间可以通过该属性来指定其对设备的延迟容忍度要求（如果有）。写入 "any" 表示 “没有要求，但不要让硬件控制延迟容忍度”，而写入 "auto" 允许硬件在没有其他内核侧要求的情况下切换到自主模式。

内核代码可以使用上述函数以及 `DEV_PM_QOS_LATENCY_TOLERANCE` 设备 PM QoS 类型来添加、移除和更新设备的延迟容忍度要求。
