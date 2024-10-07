子系统追踪点：电源
=============================

电源追踪系统捕获内核中与电源转换相关的事件。大致来说，有三个主要的子标题：

- 电源状态切换，报告与挂起（S状态）、CPU空闲（C状态）和CPU频率（P状态）相关的事件
- 系统时钟相关的变化
- 电源域相关的变化和转换

本文件描述了每个追踪点是什么以及它们可能有什么用处。
参考 `include/trace/events/power.h` 获取事件定义。

1. 电源状态切换事件
============================

1.1 追踪API
-----------------

一个“cpu”事件类收集与CPU相关的事件：CPU空闲和CPU频率
::

  cpu_idle		"state=%lu cpu_id=%lu"
  cpu_frequency		"state=%lu cpu_id=%lu"
  cpu_frequency_limits	"min=%lu max=%lu cpu_id=%lu"

一个挂起事件用于指示系统进入或退出挂起模式：
::

  machine_suspend		"state=%lu"

注意：对于状态值为'-1'或'4294967295'意味着从当前状态退出，即`trace_cpu_idle(4, smp_processor_id())`表示系统进入空闲状态4，而`trace_cpu_idle(PWR_EVENT_EXIT, smp_processor_id())`表示系统退出前一个空闲状态。
在追踪中具有`state=4294967295`的事件对于使用它来检测当前状态结束的用户空间工具非常重要，因此可以正确绘制状态图并计算准确的统计信息等。

2. 时钟事件
================
时钟事件用于时钟启用/禁用及时钟速率变化
::

  clock_enable		"%s state=%lu cpu_id=%lu"
  clock_disable		"%s state=%lu cpu_id=%lu"
  clock_set_rate		"%s state=%lu cpu_id=%lu"

第一个参数给出时钟名称（例如 "gpio1_iclk"）
第二个参数对于启用为'1'，禁用为'0'，设置速率的目标时钟速率为设置速率

3. 电源域事件
=======================
电源域事件用于电源域的转换
::

  power_domain_target	"%s state=%lu cpu_id=%lu"

第一个参数给出电源域名称（例如 "mpu_pwrdm"）
第二个参数是电源域目标状态
4. PM QoS 事件
================
PM QoS 事件用于 QoS 的添加、更新和移除请求，以及目标/标志的更新。

::

  pm_qos_update_target               "action=%s prev_value=%d curr_value=%d"
  pm_qos_update_flags                "action=%s prev_value=0x%x curr_value=0x%x"

第一个参数是 QoS 操作名称（例如 "ADD_REQ"）。
第二个参数是之前的 QoS 值。
第三个参数是要更新的当前 QoS 值。

还有用于设备 PM QoS 添加、更新和移除请求的事件：

::

  dev_pm_qos_add_request             "device=%s type=%s new_value=%d"
  dev_pm_qos_update_request          "device=%s type=%s new_value=%d"
  dev_pm_qos_remove_request          "device=%s type=%s new_value=%d"

第一个参数是尝试添加、更新或移除 QoS 请求的设备名称。
第二个参数是请求类型（例如 "DEV_PM_QOS_RESUME_LATENCY"）。
第三个参数是要添加、更新或移除的值。

此外，还有用于 CPU 延迟 QoS 添加、更新和移除请求的事件：

::

  pm_qos_add_request        "value=%d"
  pm_qos_update_request     "value=%d"
  pm_qos_remove_request     "value=%d"

参数是要添加、更新或移除的值。
当然，请提供您需要翻译的文本。
