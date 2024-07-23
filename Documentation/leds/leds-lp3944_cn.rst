核心驱动程序：lp3944
====================

* 国家半导体 LP3944 Fun-light 芯片

    前缀: 'lp3944'

    扫描的地址: 无（参见下面的注释部分）

    数据手册：

    在国家半导体网站上公开提供
    http://www.national.com/pf/LP/LP3944.html

作者:
	Antonio Ospite <ospite@studenti.unina.it>

描述
-----------
LP3944 是一个辅助芯片，可以驱动多达8个LED，并具有两种可编程的
DIM模式；它甚至可以用作GPIO扩展器，但此驱动程序假设它
用作LED控制器。
DIM模式用于设置LED的_闪烁_模式，模式通过提供两个参数指定：

  - 周期：
    从0秒到1.6秒
  - 占空比：
    LED开启时占周期的百分比，从0到100

将LED设置为DIM0或DIM1模式会使其根据模式闪烁
参见数据手册以获取详细信息。
在Motorola A910智能手机中可以找到LP3944，其中它驱动RGB
LED、相机闪光灯和LCD电源。

注释
-----
该芯片主要用于嵌入式环境，因此此驱动程序期望使用i2c_board_info机制注册它。
要在适配器0上的地址0x60处注册芯片，请按照include/linux/leds-lp3944.h设置平台数据，
设置i2c板信息如下所示：

	static struct i2c_board_info a910_i2c_board_info[] __initdata = {
		{
			I2C_BOARD_INFO("lp3944", 0x60),
			.platform_data = &a910_lp3944_leds,
		},
	};

并在平台初始化函数中注册它：

	i2c_register_board_info(0, a910_i2c_board_info,
			ARRAY_SIZE(a910_i2c_board_info));
