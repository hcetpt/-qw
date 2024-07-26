LM3556 内核驱动程序
========================

* 德州仪器：
  1.5 A 同步升压 LED 闪光灯驱动器，带高侧电流源
* 数据手册：http://www.national.com/ds/LM/LM3556.pdf

作者：
      - 丁俊 (Daniel Jeong)

联系人：丁俊 (daniel.jeong-at-ti.com, gshark.jeong-at-gmail.com)

描述
-----------
LM3556 具有三种功能：闪光、手电筒和指示器。
闪光模式
^^^^^^^^^^

在闪光模式下，LED 电流源提供从 93.75 mA 到 1500 mA 的 16 级目标电流。闪光电流通过“电流控制寄存器”(0x09) 进行调节。闪光模式由“使能寄存器”(0x0A) 或将 STROBE 引脚置为高电平来激活。
LM3556 闪光灯可通过 `/sys/class/leds/flash/brightness` 文件进行控制。

* 如果启用了 STROBE 引脚，则下面的例子仅控制亮度，而开/关则由 STROBE 引脚控制。
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

在手电筒模式下，电流源通过“电流控制寄存器”(0x09) 来编程。手电筒模式由“使能寄存器”(0x0A) 或硬件 TORCH 输入激活。
LM3556 手电筒可通过 `/sys/class/leds/torch/brightness` 文件进行控制。
* 如果启用了 TORCH 引脚，则下面的例子仅控制亮度，而开/关则由 TORCH 引脚控制。
手电筒示例：

关闭::

	#echo 0 > /sys/class/leds/torch/brightness

46.88 mA::

	#echo 1 > /sys/class/leds/torch/brightness

...
375 mA::

	#echo 8 > /sys/class/leds/torch/brightness

指示器模式
^^^^^^^^^^^^^^

指示器模式可以通过 `/sys/class/leds/indicator/pattern` 文件设置，预定义了 4 种模式在 `indicator_pattern` 数组中。
根据 N-级数、脉冲时间和 N 周期值，会生成不同的模式。如果您希望为自己的设备创建新的模式，请使用您自己的值更改 `indicator_pattern` 数组和 `INDIC_PATTERN_SIZE`。
请参阅数据手册以获取更多关于 N-空位 (N-Blank)、脉冲时间和 N 周期的详细信息。

指示器模式示例：

模式 0:: 

	# echo 0 > /sys/class/leds/indicator/pattern

..
模式 3:: 

	# echo 3 > /sys/class/leds/indicator/pattern

指示器亮度可以通过/sys/class/leds/indicator/brightness 文件进行控制。
示例：

关闭:: 

	# echo 0 > /sys/class/leds/indicator/brightness

5.86 毫安:: 

	# echo 1 > /sys/class/leds/indicator/brightness

..
46.875 毫安:: 

	# echo 8 > /sys/class/leds/indicator/brightness

注释
-----
驱动程序期望通过 i2c_board_info 机制注册。
为了在特定适配器上的地址 0x63 注册芯片，请根据 include/linux/platform_data/leds-lm3556.h 设置平台数据，并设置 i2c 板卡信息。

示例:: 

	static struct i2c_board_info board_i2c_ch4[] __initdata = {
		{
			 I2C_BOARD_INFO(LM3556_NAME, 0x63),
			 .platform_data = &lm3556_pdata,
		 },
	};

并在平台初始化函数中注册它。

示例:: 

	board_register_i2c_bus(4, 400,
				board_i2c_ch4, ARRAY_SIZE(board_i2c_ch4));
