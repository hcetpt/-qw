========================
LP5523 内核驱动程序
========================

* National Semiconductor LP5523 LED 驱动芯片
* 数据手册: http://www.national.com/pf/LP/LP5523.html

作者: Mathias Nyman, Yuri Zaporozhets, Samu Onkalo
联系人: Samu Onkalo (samu.p.onkalo-at-nokia.com)

描述
-----------
LP5523 可以驱动最多 9 个通道。LED 可以通过 LED 类控制接口直接控制。
每个通道的名称可以在平台数据中进行配置 - 即名称和标签。
有三种方式来设置通道名：

a) 在平台数据中定义 ‘name’

为了指定某个特定的通道名称，可以使用 ‘name’ 平台数据
- /sys/class/leds/R1              (名称: 'R1')
- /sys/class/leds/B1              (名称: 'B1')

b) 使用 ‘label’ 而不使用 ‘name’ 字段

对于单一设备名称与通道编号组合的情况，则使用 ‘label’
- /sys/class/leds/RGB:channelN    (标签: 'RGB', N: 0 到 8)

c) 默认值

如果两个字段都是 NULL，则默认使用 ‘lp5523’
- /sys/class/leds/lp5523:channelN (N: 0 到 8)

LP5523 具有内部程序存储器，用于运行各种 LED 模式。
有两种方式运行 LED 模式：
1) 传统接口 - enginex_mode, enginex_load 和 enginex_leds

  发动机控制接口：

  x 是 1 到 3

  enginex_mode:
   禁用, 加载, 运行
  enginex_load:
   微码加载
  enginex_leds:
   LED 复用控制

  ::

    cd /sys/class/leds/lp5523:channel2/device
    echo "load" > engine3_mode
    echo "9d80400004ff05ff437f0000" > engine3_load
    echo "111111111" > engine3_leds
    echo "run" > engine3_mode

  要停止发动机，请执行如下操作：::

    echo "disabled" > engine3_mode

2) 固件接口 - LP55xx 公共接口

详情请参阅 leds-lp55xx.txt 中的 “固件” 部分。

LP5523 有三个主调光器。如果一个通道映射到其中一个主调光器，
那么该通道的输出将根据主调光器的值进行调光。
例如：::

  echo "123000123" > master_fader_leds

创建以下通道-调光器映射：::

  通道 0,6 映射到 master_fader1
  通道 1,7 映射到 master_fader2
  通道 2,8 映射到 master_fader3

要使通道 0,6 的输出为原始输出的 25%：::

  echo 64 > master_fader1

要使通道 1,7 的输出为原始输出的 0%（即无输出）：::

  echo 0 > master_fader2

要使通道 2,8 的输出为原始输出的 100%（即无调光）：::

  echo 255 > master_fader3

要清除所有主调光器控制：::

  echo "000000000" > master_fader_leds

自检总是使用来自平台数据中的当前电流。
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
