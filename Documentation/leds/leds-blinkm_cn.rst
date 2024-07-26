BlinkM LED 驱动程序
==================

`leds-blinkm` 驱动程序支持 BlinkM 系列设备。
这些设备是通过 ATtiny 微控制器驱动的 RGB-LED 模块，并通过 I2C 进行通信。这些模块的默认地址为 0x09，但可以通过命令进行更改。这样您可以在一个 I2C 总线上级联多达 127 个 BlinkM 设备。
该设备可通过独立命令接受 RGB 和 HSB 颜色值。此外，您可以将闪烁序列作为“脚本”存储在控制器中并运行它们。同时支持渐变功能。
此驱动程序提供的接口分为两部分：

a) LED 类接口用于触发器
############################################

注册遵循以下模式： 

  `blinkm-<i2c-总线号>-<i2c-设备号>-<颜色>`

  `$ ls -h /sys/class/leds/blinkm-6-*`
  `/sys/class/leds/blinkm-6-9-blue:`
  `brightness  device  max_brightness  power  subsystem  trigger  uevent`

  `/sys/class/leds/blinkm-6-9-green:`
  `brightness  device  max_brightness  power  subsystem  trigger  uevent`

  `/sys/class/leds/blinkm-6-9-red:`
  `brightness  device  max_brightness  power  subsystem  trigger  uevent`

（相同路径为 `/sys/bus/i2c/devices/6-0009/leds`）

我们可以分别控制红、绿和蓝色，并为每种颜色分配触发器。
例如： 

  `$ cat blinkm-6-9-blue/brightness`
  `05`

  `$ echo 200 > blinkm-6-9-blue/brightness`
  `$`

  `$ modprobe ledtrig-heartbeat`
  `$ echo heartbeat > blinkm-6-9-green/trigger`
  `$`

b) 控制 RGB、渐变、HSB、脚本等的 Sysfs 组
#####################################################

此扩展接口作为 BlinkM 文件夹提供于 I2C 设备的 Sysfs 文件夹中。
例如，在 `/sys/bus/i2c/devices/6-0009/blinkm` 下。

  `$ ls -h /sys/bus/i2c/devices/6-0009/blinkm/`
  `blue  green  red  test`

目前仅支持设置红色、绿色、蓝色以及测试序列。
例如：

  `$ cat *`
  `00`
  `00`
  `00`
  `# 将数字写入 test 来启动测试序列！#`

  `$ echo 1 > test`
  `$`

  `$ echo 255 > red`
  `$`

截至 2012 年 6 月

dl9pf[at]gmx[dot]de
