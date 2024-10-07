.. SPDX 许可证标识符: GPL-2.0 或 GFDL-1.1 无不变部分或之后版本

.. _遥控器的 sysfs 节点:

*******************************
遥控器的 sysfs 节点
*******************************

如在 ``Documentation/ABI/testing/sysfs-class-rc`` 中定义，这些是用于控制遥控器的 sysfs 节点：

.. _sys_class_rc:

/sys/class/rc/
==============

``/sys/class/rc/`` 子目录属于遥控器核心，并提供了一个用于配置红外遥控接收器的 sysfs 接口。

.. _sys_class_rc_rcN:

/sys/class/rc/rcN/
==================

为每个遥控接收设备创建一个 ``/sys/class/rc/rcN`` 目录，其中 N 是接收器的编号。

.. _sys_class_rc_rcN_protocols:

/sys/class/rc/rcN/protocols
===========================

读取此文件会返回可用协议的列表，例如：

``rc5 [rc6] nec jvc [sony]``

启用的协议用 [] 括起来。
写入 "+proto" 将向启用的协议列表中添加一个协议。
写入 "-proto" 将从启用的协议列表中移除一个协议。
写入 "proto" 将仅启用 "proto"。
写入 "none" 将禁用所有协议。
如果使用了无效的协议组合或未知的协议名称，则写入将因 ``EINVAL`` 失败。

.. _sys_class_rc_rcN_filter:

/sys/class/rc/rcN/filter
========================

设置预期的扫描码过滤值。
结合使用 ``/sys/class/rc/rcN/filter_mask`` 来设置过滤掩码中设置位的预期值。如果硬件支持的话，不匹配该过滤器的扫描码将被忽略。否则，写入操作将以错误失败。
此值可能在当前协议更改时重置为 0
.. _sys_class_rc_rcN_filter_mask:

/sys/class/rc/rcN/filter_mask
=============================

设置位比较的扫描码过滤掩码。与 `/sys/class/rc/rcN/filter` 结合使用，以设置应与预期值进行比较的扫描码位。值为 0 表示禁用过滤器，允许处理所有有效的扫描码。
如果硬件支持的话，不匹配过滤器的扫描码将被忽略。否则写入会因错误而失败。
此值可能在当前协议更改时重置为 0
.. _sys_class_rc_rcN_wakeup_protocols:

/sys/class/rc/rcN/wakeup_protocols
==================================

读取此文件会返回可用于唤醒过滤器的协议列表，如下所示：

```
rc-5 nec nec-x rc-6-0 rc-6-6a-24 [rc-6-6a-32] rc-6-mce
```

请注意，列出了协议的不同变体，因此如果可用的话，“nec”、“sony”、“rc-5”、“rc-6” 将列出它们不同的位长度编码。
请注意，列出了所有协议变体。
启用的唤醒协议显示在 [] 括号中。
每次只能选择一个协议。
写入 "proto" 将使用 "proto" 进行唤醒事件。
写入 "none" 将禁用唤醒。
写入操作会因使用了无效的协议组合或未知的协议名称，或者硬件不支持唤醒功能而返回 `EINVAL` 错误。
.. _sys_class_rc_rcN_wakeup_filter:

`/sys/class/rc/rcN/wakeup_filter`
=================================

设置扫描码唤醒过滤器期望值。与 `/sys/class/rc/rcN/wakeup_filter_mask` 结合使用，以设置唤醒过滤器掩码中设置的位的期望值，从而触发系统唤醒事件。如果硬件支持并且 `wakeup_filter_mask` 不为 0，则匹配过滤器的扫描码将从例如挂起到内存或关机状态唤醒系统。否则，写入操作会返回错误。
此值可能在更改唤醒协议时重置为 0。
.. _sys_class_rc_rcN_wakeup_filter_mask:

`/sys/class/rc/rcN/wakeup_filter_mask`
======================================

设置用于比较的扫描码唤醒过滤器掩码位。与 `/sys/class/rc/rcN/wakeup_filter` 结合使用，以设置应与期望值进行比较的扫描码位，从而触发系统唤醒事件。如果硬件支持并且 `wakeup_filter_mask` 不为 0，则匹配过滤器的扫描码将从例如挂起到内存或关机状态唤醒系统。否则，写入操作会返回错误。
此值可能在更改唤醒协议时重置为 0。
