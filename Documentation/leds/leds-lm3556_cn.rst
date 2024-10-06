========================
LM3556 内核驱动程序
========================

* 德州仪器：
  1.5 A 同步升压 LED 闪光驱动器带高侧电流源
* 数据手册：http://www.national.com/ds/LM/LM3556.pdf

作者：
      - Daniel Jeong

联系人：Daniel Jeong (daniel.jeong-at-ti.com, gshark.jeong-at-gmail.com)

描述
-----------
LM3556 具有三种功能：闪光模式、手电筒模式和指示模式。

闪光模式
^^^^^^^^^^

在闪光模式下，LED 电流源提供从 93.75 mA 到 1500 mA 的 16 个目标电流级别。闪光电流通过 CURRENT CONTROL REGISTER (0x09) 进行调整。闪光模式可以通过 ENABLE REGISTER (0x0A) 或将 STROBE 引脚拉高来激活。
LM3556 闪光模式可以通过 `/sys/class/leds/flash/brightness` 文件进行控制。

* 如果 STROBE 引脚被启用，则以下示例仅控制亮度，而开/关由 STROBE 引脚控制。
闪光示例：

关闭::

	#echo 0 > /sys/class/leds/flash/brightness

93.75 mA::

	#echo 1 > /sys/class/leds/flash/brightness

...
1500 mA::

	#echo 16 > /sys/class/leds/flash/brightness

手电筒模式
^^^^^^^^^^

在手电筒模式下，电流源（LED）通过 CURRENT CONTROL REGISTER (0x09) 进行编程。手电筒模式可以通过 ENABLE REGISTER (0x0A) 或硬件 TORCH 输入来激活。
LM3556 手电筒模式可以通过 `/sys/class/leds/torch/brightness` 文件进行控制。

* 如果 TORCH 引脚被启用，则以下示例仅控制亮度，而开/关由 TORCH 引脚控制。
手电筒示例：

关闭::

	#echo 0 > /sys/class/leds/torch/brightness

46.88 mA::

	#echo 1 > /sys/class/leds/torch/brightness

...
375 mA::

	#echo 8 > /sys/class/leds/torch/brightness

指示模式
^^^^^^^^^^^^^^

指示模式可以通过 `/sys/class/leds/indicator/pattern` 文件设置，且在 `indicator_pattern` 数组中预定义了四种模式。
根据 N-lank、脉冲时间和 N 周期值，会生成不同的模式。如果您需要为自己的设备创建新的模式，请使用您自己的值更改 `indicator_pattern` 数组及其大小 `INDIC_PATTERN_SIZE`。
请参阅数据手册以获取有关 N-Blank、脉冲时间和 N 周期的更多详细信息。

指示器模式示例：

模式 0：

```
#echo 0 > /sys/class/leds/indicator/pattern
```

...
模式 3：

```
#echo 3 > /sys/class/leds/indicator/pattern
```

指示器亮度可以通过以下文件进行控制：
/sys/class/leds/indicator/brightness
示例：

关闭：

```
#echo 0 > /sys/class/leds/indicator/brightness
```

5.86 毫安：

```
#echo 1 > /sys/class/leds/indicator/brightness
```

...
46.875 毫安：

```
#echo 8 > /sys/class/leds/indicator/brightness
```

注意事项
------
驱动程序期望使用 i2c_board_info 机制进行注册。
为了在特定适配器上的地址 0x63 注册芯片，请根据 include/linux/platform_data/leds-lm3556.h 设置平台数据，并设置 i2c 板卡信息。

示例：

```c
static struct i2c_board_info board_i2c_ch4[] __initdata = {
	{
		I2C_BOARD_INFO(LM3556_NAME, 0x63),
		.platform_data = &lm3556_pdata,
	},
};
```

并在平台初始化函数中进行注册。

示例：

```c
board_register_i2c_bus(4, 400,
			board_i2c_ch4, ARRAY_SIZE(board_i2c_ch4));
```
