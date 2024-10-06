USB端口LED触发器
====================

此LED触发器可用于向用户指示给定端口中是否存在USB设备。当设备插入时，它会点亮LED；当设备拔出时，熄灭LED。
需要选择要监控的USB端口。所有可用的端口都会在“ports”子目录中以独立条目的形式列出。选择端口是通过向所选端口回显“1”来完成的。
请注意，此触发器允许为单个LED选择多个USB端口。这在以下两种情况下非常有用：

1) 具有单个USB LED和几个物理端口的设备
====================================================

在这种情况下，只要至少有一个连接的USB设备，LED就会亮起。
2) 具有由多个控制器处理的物理端口的设备
=========================================================

某些设备可能每个PHY标准都有一个控制器。例如，USB 3.0物理端口可能由ohci-platform、ehci-platform和xhci-hcd处理。如果只有一个LED，用户很可能希望将这三个集线器的所有端口都分配给这个LED。
此触发器可以从用户空间通过led类设备激活，如下所示：

```
echo usbport > trigger
```

这会在LED上添加sysfs属性，具体文档参见：
Documentation/ABI/testing/sysfs-class-led-trigger-usbport

示例用法：

```
echo usbport > trigger
echo 1 > ports/usb1-port1
echo 1 > ports/usb2-port1
cat ports/usb1-port1
echo 0 > ports/usb1-port1
```
