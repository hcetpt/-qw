标题：LP5523内核驱动程序

* 国家半导体LP5523 LED驱动芯片
* 数据手册：http://www.national.com/pf/LP/LP5523.html

作者：Mathias Nyman，Yuri Zaporozhets，Samu Onkalo
联系人：Samu Onkalo（samu.p.onkalo-at-nokia.com）

描述
------
LP5523最多可驱动9个通道。LED可通过LED类控制接口直接控制。
每个通道的名称可在平台数据中进行配置 - 名称和标签
有三种方式来定义通道名称：

a）在平台数据中定义'名称'

要为特定通道命名，使用平台数据中的'名称'
- /sys/class/leds/R1               （名称：'R1'）
- /sys/class/leds/B1               （名称：'B1'）

b）仅使用'标签'而无'名称'字段

对于单一设备名加通道编号，使用'标签'
- /sys/class/leds/RGB:channelN     （标签：'RGB'，N：0~8）

c）默认

如果两个字段都为空，将默认使用'lp5523'
- /sys/class/leds/lp5523:channelN  （N：0~8）

LP5523具有内部程序内存，用于运行各种LED模式
有两种方式运行LED模式：
1）传统接口 - enginex_mode，enginex_load 和 enginex_leds

  对引擎的控制接口：

  x 是 1 到 3

  enginex_mode:
    禁用，加载，运行
  enginex_load:
    微码加载
  enginex_leds:
    LED多路复用控制

  示例：

  cd /sys/class/leds/lp5523:channel2/device
  echo "load" > engine3_mode
  echo "9d80400004ff05ff437f0000" > engine3_load
  echo "111111111" > engine3_leds
  echo "run" > engine3_mode

  要停止引擎：

  echo "disabled" > engine3_mode

2）固件接口 - LP55xx通用接口

详情请参阅leds-lp55xx.txt中的'固件'部分

LP5523具有三个主调光器。如果一个通道映射到其中一个
主调光器，其输出将根据主调光器的值进行调暗
例如：

  echo "123000123" > master_fader_leds

创建以下通道-调光器映射：

  通道 0,6 到 master_fader1
  通道 1,7 到 master_fader2
  通道 2,8 到 master_fader3

然后，要使通道0,6的输出为原输出的25%：

  echo 64 > master_fader1

要使通道1,7的输出为原输出的0%（即无输出）：

  echo 0 > master_fader2

要使通道2,8的输出为原输出的100%（即不调暗）：

  echo 255 > master_fader3

要清除所有主调光器控制：

  echo "000000000" > master_fader_leds

自检始终使用来自平台数据的电流。
每个通道包含 LED 电流设置：
- /sys/class/leds/lp5523:channel2/led_current - 读写
- /sys/class/leds/lp5523:channel2/max_current - 只读

格式：10x mA，即 10 表示 1.0 mA。

平台数据示例：

```c
static struct lp55xx_led_config lp5523_led_config[] = {
	{
		.name       = "D1",
		.chan_nr    = 0,
		.led_current    = 50,  // LED 电流
		.max_current    = 130, // 最大电流
	},
	...
	{
		.chan_nr    = 8,
		.led_current    = 50,  // LED 电流
		.max_current    = 130, // 最大电流
	}
};

static int lp5523_setup(void)
{
	/* 设置硬件资源 */
}

static void lp5523_release(void)
{
	/* 释放硬件资源 */
}

static void lp5523_enable(bool state)
{
	/* 控制芯片使能信号 */
}

static struct lp55xx_platform_data lp5523_platform_data = {
	.led_config     = lp5523_led_config,
	.num_channels   = ARRAY_SIZE(lp5523_led_config), // LED 配置数组的大小
	.clock_mode     = LP55XX_CLOCK_EXT,
	.setup_resources   = lp5523_setup,
	.release_resources = lp5523_release,
	.enable            = lp5523_enable,
};
```

**注释**
`chan_nr` 的值可以在 0 到 8 之间。
