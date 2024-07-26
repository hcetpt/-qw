===== 核心驱动程序 lp3944 =====

  * 国家半导体 LP3944 Fun-light 芯片

    前缀: 'lp3944'

    扫描地址: 无（参见下面的注释部分）

    数据手册:

      公开提供于国家半导体网站
      http://www.national.com/pf/LP/LP3944.html

作者:
  安东尼奥·奥斯皮特 <ospite@studenti.unina.it>

描述
-----------
LP3944 是一个辅助芯片，能够驱动最多 8 个 LED，并具有两种可编程的
DIM 模式；它甚至可以用作 GPIO 扩展器，但此驱动程序假设它被用作 LED 控制器。
DIM 模式用于设置 LED 的 _闪烁_ 模式，模式通过提供两个参数来指定：

  - 周期：
    从 0 秒到 1.6 秒
  - 占空比：
    LED 开启时间占周期的百分比，范围从 0 到 100

将 LED 设置为 DIM0 或 DIM1 模式会使它根据指定的模式进行闪烁。
有关详细信息，请参阅数据手册。
在摩托罗拉 A910 智能手机中可以找到 LP3944，该芯片用于驱动 RGB LED、摄像头闪光灯和 LCD 电源。

注释
-----
该芯片主要应用于嵌入式环境中，因此此驱动程序期望通过 i2c_board_info 机制进行注册。
要在适配器 0 上的地址 0x60 处注册芯片，请根据 include/linux/leds-lp3944.h 设置平台数据，设置 i2c 板信息如下所示：

```c
static struct i2c_board_info a910_i2c_board_info[] __initdata = {
	{
		I2C_BOARD_INFO("lp3944", 0x60),
		.platform_data = &a910_lp3944_leds,
	},
};
```

并在平台初始化函数中注册它：

```c
i2c_register_board_info(0, a910_i2c_board_info,
			ARRAY_SIZE(a910_i2c_board_info));
```
