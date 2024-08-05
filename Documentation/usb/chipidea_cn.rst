ChipIdea 高速双角色控制器驱动程序

==============================================

1. 如何测试OTG状态机（HNP和SRP）
-----------------------------------

为了演示通过系统输入文件来展示OTG的HNP（主机协商协议）和SRP（会话请求协议）功能，使用两块Freescale i.MX6Q Sabre SD开发板。
1.1 如何启用OTG状态机
------------------------

1.1.1 在`menuconfig`中选择`CONFIG_USB_OTG_FSM`选项，并重新构建内核。
^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^

映像和模块。如果你想检查一些内部变量来了解OTG状态机的情况，请挂载debugfs，有两个文件可以展示OTG状态机的变量以及一些控制器寄存器的值：

```
cat /sys/kernel/debug/ci_hdrc.0/otg
cat /sys/kernel/debug/ci_hdrc.0/registers
```

1.1.2 在你的设备树源文件(DTS)中为你的控制器节点添加以下条目
^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^

```
otg-rev = <0x0200>;
adp-disable;
```

1.2 测试操作
--------------

1) 打开两块Freescale i.MX6Q Sabre SD开发板，并加载gadget类驱动程序（例如：g_mass_storage）。
2) 使用USB线连接两块开发板：一端是micro A插头，另一端是micro B插头。
    - A设备（插入micro A插头的一方）应该枚举B设备。
3) 角色切换

   在B设备上执行：

   ```
   echo 1 > /sys/bus/platform/devices/ci_hdrc.0/inputs/b_bus_req
   ```

   B设备应该变为主机角色并枚举A设备。
4) A设备切换回主机
在B设备上执行：

   ```
   echo 0 > /sys/bus/platform/devices/ci_hdrc.0/inputs/b_bus_req
   ```

   或者，通过引入HNP轮询机制，B主机可以知道何时A外围设备希望成为主机角色。这种角色切换也可以由A外围设备触发，通过响应来自B主机的轮询。这可以在A设备上完成：

   ```
   echo 1 > /sys/bus/platform/devices/ci_hdrc.0/inputs/a_bus_req
   ```

   A设备应该切换回主机并枚举B设备。
5) 移除B设备（拔掉micro B插头），并在10秒后再次插入；A设备应该再次枚举B设备。
6) 移除B设备（拔掉micro B插头），并在10秒后再次插入；A设备不应该枚举B设备。
如果A设备想要使用总线：

   在A设备上执行：

   ```
   echo 0 > /sys/bus/platform/devices/ci_hdrc.0/inputs/a_bus_drop
   echo 1 > /sys/bus/platform/devices/ci_hdrc.0/inputs/a_bus_req
   ```

如果B设备想要使用总线：

   在B设备上执行：

   ```
   echo 1 > /sys/bus/platform/devices/ci_hdrc.0/inputs/b_bus_req
   ```

7) A设备关闭总线。
在A设备上:

```
echo 1 > /sys/bus/platform/devices/ci_hdrc.0/inputs/a_bus_drop
```

A设备应该与B设备断开连接并关闭总线的电源。
8) B设备进行SRP的数据脉冲操作
在B设备上:

```
echo 1 > /sys/bus/platform/devices/ci_hdrc.0/inputs/b_bus_req
```

A设备应该恢复USB总线并枚举B设备。
1.3 参考文档
----------------------
《USB 2.0规范的On-The-Go和嵌入式主机补充文档
2012年7月27日 第2.0版版本1.1a》

2. 如何将USB设置为系统唤醒源
--------------------------------------------
以下是针对imx6平台如何将USB设置为系统唤醒源的例子：
2.1 启用核心唤醒功能:

```
echo enabled > /sys/bus/platform/devices/ci_hdrc.0/power/wakeup
```

2.2 启用粘合层唤醒功能:

```
echo enabled > /sys/bus/platform/devices/2184000.usb/power/wakeup
```

2.3 启用PHY唤醒功能（可选）:

```
echo enabled > /sys/bus/platform/devices/20c9000.usbphy/power/wakeup
```

2.4 启用根集线器唤醒功能:

```
echo enabled > /sys/bus/usb/devices/usb1/power/wakeup
```

2.5 启用相关设备的唤醒功能:

```
echo enabled > /sys/bus/usb/devices/1-1/power/wakeup
```

如果系统只有一个USB端口，并且希望在这个端口启用USB唤醒功能，您可以使用以下脚本来启用USB唤醒功能:

```
for i in $(find /sys -name wakeup | grep usb); do echo enabled > $i; done;
```
