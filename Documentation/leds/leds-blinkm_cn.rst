### BlinkM LED 驱动

#### BlinkM LED 驱动

BlinkM LED 驱动支持 BlinkM 系列设备。这些设备是通过 ATtiny 微控制器驱动的 RGB LED 模块，并通过 I2C 接口进行通信。这些模块的默认地址为 0x09，但可以通过命令更改。因此，可以在一个 I2C 总线上级联多达 127 个 BlinkM 设备。该设备接受通过独立命令传递的 RGB 和 HSB 颜色值。此外，您还可以将闪烁序列存储为“脚本”在控制器中运行。渐变也是一个可选项。

此驱动程序提供的接口分为两部分：

1. **LED 类接口用于触发器**

   注册方案如下：

   ```
   blinkm-<i2c-bus-nr>-<i2c-device-nr>-<color>
   ```

   示例：

   ```
   $ ls -h /sys/class/leds/blinkm-6-*
   /sys/class/leds/blinkm-6-9-blue:
   brightness  device  max_brightness  power  subsystem  trigger  uevent

   /sys/class/leds/blinkm-6-9-green:
   brightness  device  max_brightness  power  subsystem  trigger  uevent

   /sys/class/leds/blinkm-6-9-red:
   brightness  device  max_brightness  power  subsystem  trigger  uevent
   ```

   （同上：`/sys/bus/i2c/devices/6-0009/leds`）

   我们可以分别控制红色、绿色和蓝色，并为每种颜色分配触发器。例如：

   ```
   $ cat blinkm-6-9-blue/brightness
   05

   $ echo 200 > blinkm-6-9-blue/brightness

   $ modprobe ledtrig-heartbeat
   $ echo heartbeat > blinkm-6-9-green/trigger
   ```

2. **Sysfs 组来控制 RGB、渐变、HSB、脚本等**

   这个扩展接口作为文件夹 `blinkm` 在 I2C 设备的 sysfs 文件夹中提供。例如，在 `/sys/bus/i2c/devices/6-0009/blinkm` 下：

   ```
   $ ls -h /sys/bus/i2c/devices/6-0009/blinkm/
   blue  green  red  test
   ```

   目前仅支持设置红色、绿色、蓝色以及测试序列。例如：

   ```
   $ cat *
   00
   00
   00
   #写入 test 启动测试序列！#

   $ echo 1 > test

   $ echo 255 > red
   ```

   2012年6月

   dl9pf <at> gmx <dot> de
