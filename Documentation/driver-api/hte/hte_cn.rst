SPDX 许可证标识符: GPL-2.0+

============================================
Linux 硬件时间戳引擎 (HTE)
============================================

:作者: Dipen Patel

简介
------------

某些设备内置了硬件时间戳引擎，可以实时监控系统信号、线路、总线等的状态变化；一旦检测到状态变化，它们就能自动存储发生时刻的时间戳。这种功能可能有助于实现比使用软件对应方案（例如 ktime 及其相关组件）更高的时间戳精度。
本文档描述了一个 API，硬件时间戳引擎 (HTE) 提供者和消费者驱动程序都可以使用该 API 来利用 HTE 框架。消费者和提供者都必须包含 `#include <linux/hte.h>`。

HTE 框架的提供者 API
----------------------------------------

.. kernel-doc:: drivers/hte/hte.c
   :functions: devm_hte_register_chip hte_push_ts_ns

HTE 框架的消费者 API
----------------------------------------

.. kernel-doc:: drivers/hte/hte.c
   :functions: hte_init_line_attr hte_ts_get hte_ts_put devm_hte_request_ts_ns hte_request_ts_ns hte_enable_ts hte_disable_ts of_hte_req_count hte_get_clk_src_info

HTE 框架的公共结构体
-----------------------------------
.. kernel-doc:: include/linux/hte.h

关于 HTE 时间戳数据的更多信息
------------------------------
`struct hte_ts_data` 用于在消费者与提供者之间传递时间戳详情。它以纳秒为单位表达时间戳数据（u64类型）。以下是 GPIO 线路典型时间戳数据生命周期的一个示例：

- 监控 GPIO 线路的变化
- 检测 GPIO 线路上的状态变化
- 将时间戳转换为纳秒
- 如果提供者具有相应的硬件能力，则将 GPIO 的原始电平存储在 raw_level 变量中
- 将此 hte_ts_data 对象推送到 HTE 子系统
- HTE 子系统递增 seq 计数器，并调用消费者提供的回调函数
- 根据回调返回值，HTE 核心在线程上下文中调用次级回调

HTE 子系统的 debugfs 属性
--------------------------------
HTE 子系统会在 `/sys/kernel/debug/hte/` 下创建 debugfs 属性。
它还在 `/sys/kernel/debug/hte/<provider>/<label or line id>/` 下创建了与线路或信号相关的 debugfs 属性。请注意，这些属性是只读的。

`ts_requested`  
从给定提供者请求的实体总数，这里的实体由提供者指定，可以代表线路、GPIO、芯片信号、总线等。
该属性将在以下位置可用：
``/sys/kernel/debug/hte/<provider>/``

`total_ts`  
提供者支持的实体总数。
该属性将在以下位置可用：
``/sys/kernel/debug/hte/<provider>/``

`dropped_timestamps`  
给定线路的丢失时间戳。
该属性将在以下位置可用：
``/sys/kernel/debug/hte/<provider>/<label or line id>/``
