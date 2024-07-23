========================
LM3556内核驱动程序
========================

* 德州仪器：
  1.5 A 同步升压 LED 闪光灯驱动器，带高侧电流源
* 数据手册：http://www.national.com/ds/LM/LM3556.pdf

作者：
      - 丁俊（Daniel Jeong）

   联系人：丁俊（daniel.jeong-at-ti.com, gshark.jeong-at-gmail.com）

描述
-----------
LM3556有三种功能：闪光、手电筒和指示器。
闪光模式
^^^^^^^^^^

在闪光模式下，LED电流源（LED）提供从93.75 mA到1500 mA的16个目标电流级别。闪光电流通过CURRENT CONTROL REGISTER（0x09）进行调整。闪光模式由ENABLE REGISTER（0x0A）激活，或者通过将STROBE引脚拉至高电平实现。
LM3556闪光可以通过/sys/class/leds/flash/brightness文件控制。

* 如果STROBE引脚被启用，则下面的例子仅控制亮度，而开/关将由STROBE引脚控制。
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

在手电筒模式下，电流源（LED）通过CURRENT CONTROL REGISTER（0x09）编程。手电筒模式由ENABLE REGISTER（0x0A）或硬件TORCH输入激活。
LM3556手电筒可以通过/sys/class/leds/torch/brightness文件控制。
* 如果TORCH引脚被启用，则下面的例子仅控制亮度，而开/关将由TORCH引脚控制。
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

指示器模式可通过/sys/class/leds/indicator/pattern文件设置，且在indicator_pattern数组中预定义了4种模式。
根据N级、脉冲时间和N周期值，将生成不同的模式。如果你想为自己的设备设置新模式，请使用你自己的值修改indicator_pattern数组和INDIC_PATTERN_SIZE。
请参阅数据手册以获取关于N-空位、脉冲时间和N周期的更多详细信息。
指示器模式示例：

模式0：

	通过命令 `echo 0 > /sys/class/leds/indicator/pattern` 设置

...
模式3：

	通过命令 `echo 3 > /sys/class/leds/indicator/pattern` 设置

指示器亮度可以通过
/sys/class/leds/indicator/brightness 文件进行控制
示例：

关闭：

	通过命令 `echo 0 > /sys/class/leds/indicator/brightness` 设置

5.86 mA：

	通过命令 `echo 1 > /sys/class/leds/indicator/brightness` 设置

...
46.875mA：

	通过命令 `echo 8 > /sys/class/leds/indicator/brightness` 设置

注释
-----
驱动程序期望使用i2c_board_info机制进行注册
为了在特定适配器上的地址0x63处注册芯片，设置平台数据
根据include/linux/platform_data/leds-lm3556.h中的定义设置i2c板信息

示例：

	静态声明如下结构体数组 `struct i2c_board_info board_i2c_ch4[] __initdata`：
		{
			 I2C_BOARD_INFO(LM3556_NAME, 0x63),
			 .platform_data = &lm3556_pdata,
		 },
	};

并在平台初始化函数中注册它

示例：

	调用 `board_register_i2c_bus(4, 400, board_i2c_ch4, ARRAY_SIZE(board_i2c_ch4));` 进行注册。
