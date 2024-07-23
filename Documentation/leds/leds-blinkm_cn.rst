BlinkM LED 驱动程序
==================

BlinkM LED驱动程序支持BlinkM家族的设备，
这些设备是RGB-LED模块，由（AT）tiny微控制器驱动，并通过I2C通信。
这些模块的默认地址是0x09，但可以通过命令更改。
这样，你可以在一个I2C总线上串联多达127个BlinkM。
该设备通过独立的命令接受RGB和HSB颜色值。
此外，你还可以将闪烁序列作为“脚本”存储在控制器中并运行它们。
渐变也是一个选项。

此驱动程序提供的接口分为两部分：

a) LED类接口用于触发器
############################################

注册遵循以下模式：

  blinkm-<i2c总线号>-<i2c设备号>-<颜色>

例如：

  $ ls -h /sys/class/leds/blinkm-6-*
  /sys/class/leds/blinkm-6-9-blue:
  brightness  device  max_brightness  power  subsystem  trigger  uevent

  /sys/class/leds/blinkm-6-9-green:
  brightness  device  max_brightness  power  subsystem  trigger  uevent

  /sys/class/leds/blinkm-6-9-red:
  brightness  device  max_brightness  power  subsystem  trigger  uevent

(与/sys/bus/i2c/devices/6-0009/leds相同)

我们可以分别控制红色、绿色和蓝色，并为每种颜色分配触发器。
例如：

  $ cat blinkm-6-9-blue/brightness
  05

  $ echo 200 > blinkm-6-9-blue/brightness

  $ modprobe ledtrig-heartbeat
  $ echo heartbeat > blinkm-6-9-green/trigger


b) 控制rgb、渐变、hsb、脚本等的sysfs组
#####################################################

这个扩展接口作为一个名为blinkm的文件夹出现在I2C设备的sysfs文件夹中。
例如，在/sys/bus/i2c/devices/6-0009/blinkm下。

  $ ls -h /sys/bus/i2c/devices/6-0009/blinkm/
  blue  green  red  test

目前仅支持设置红色、绿色、蓝色和测试序列。
例如：

  $ cat *
  00
  00
  00
  #写入test以开始测试序列！#

  $ echo 1 > test

  $ echo 255 > red

截至2012年6月

dl9pf <at> gmx <dot> de

注：以上翻译可能需要根据具体上下文进行适当调整。
