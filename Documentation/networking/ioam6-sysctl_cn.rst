... SPDX-License-Identifier: GPL-2.0

=====================
IOAM6 Sysfs 变量
=====================


/proc/sys/net/conf/<iface>/ioam6_* 变量:
=============================================

ioam6_enabled - 布尔值
        对于此接口，在入口处接受(=启用)或忽略(=禁用)IPv6 IOAM选项
* 0 - 禁用（默认）
        * 1 - 启用

ioam6_id - 短整数
        定义此接口的 IOAM ID
默认值为 ~0
ioam6_id_wide - 整数
        定义此接口的宽 IOAM ID
默认值为 ~0
