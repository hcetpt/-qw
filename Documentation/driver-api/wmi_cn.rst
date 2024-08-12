SPDX 许可证标识符: GPL-2.0 或更高版本

=================
WMI 驱动程序 API
=================

WMI 驱动核心支持一种更现代的基于总线的接口来与 WMI 设备进行交互，同时也支持一个较旧的基于 GUID 的接口。后者被认为已经过时，因此新的 WMI 驱动应该通常避免使用它，因为它在处理多个 WMI 设备和共享相同 GUID 和/或通知 ID 的事件时存在一些问题。相反，现代的基于总线的接口将每个 WMI 设备映射到一个 `struct wmi_device <wmi_device>` 类型的结构体，这样就支持了具有相同 GUID 和/或通知 ID 的 WMI 设备。驱动程序可以注册一个 `struct wmi_driver <wmi_driver>` 类型的结构体，该结构体将由驱动核心绑定到兼容的 WMI 设备上。

.. kernel-doc:: include/linux/wmi.h
   :internal:

.. kernel-doc:: drivers/platform/x86/wmi.c
   :export:
