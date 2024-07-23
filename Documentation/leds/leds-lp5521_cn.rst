========================
LP5521内核驱动程序
========================

* 国家半导体LP5521 LED驱动芯片
* 数据手册：http://www.national.com/pf/LP/LP5521.html

作者：Mathias Nyman，Yuri Zaporozhets，Samu Onkalo

联系人：Samu Onkalo（samu.p.onkalo-at-nokia.com）

描述
-----------

LP5521最多可驱动3个通道。LED可通过LED类控制接口直接控制。通道具有通用名称：
lp5521:channelx，其中x为0至2。

所有三个通道也可通过引擎微程序进行控制。
更多指令详情可从公开的数据手册中找到。
LP5521具有内部程序存储器，用于运行各种LED模式。
有两种方式运行LED模式：

1）传统接口 - enginex_mode 和 enginex_load
   引擎的控制接口：

   x是1至3

   enginex_mode:
   禁用，加载，运行
   enginex_load:
   存储程序（仅在引擎加载模式下可见）

示例（开始使通道2 LED闪烁）：

```
cd /sys/class/leds/lp5521:channel2/device
echo "load" > engine3_mode
echo "037f4d0003ff6000" > engine3_load
echo "run" > engine3_mode
```

要停止引擎：

```
echo "disabled" > engine3_mode
```

2）固件接口 - LP55xx通用接口

详情请参阅leds-lp55xx.txt中的“固件”部分。

sysfs包含一个自检条目。
测试与芯片通信并检查时钟模式是否自动设置为所请求的模式。
每个通道都有其独立的LED电流设置：
- /sys/class/leds/lp5521:channel0/led_current - 可读写
- /sys/class/leds/lp5521:channel0/max_current - 只读

格式：10x mA 即 10表示1.0 mA

示例平台数据：

```c
static struct lp55xx_led_config lp5521_led_config[] = {
	{
		.name = "red",
		.chan_nr = 0,
		.led_current = 50,
		.max_current = 130,
	}, {
		.name = "green",
		.chan_nr = 1,
		.led_current = 0,
		.max_current = 130,
	}, {
		.name = "blue",
		.chan_nr = 2,
		.led_current = 0,
		.max_current = 130,
	}
};

static int lp5521_setup(void)
{
	/* 设置硬件资源 */
}

static void lp5521_release(void)
{
	/* 释放硬件资源 */
}

static void lp5521_enable(bool state)
{
	/* 芯片启用信号控制 */
}

static struct lp55xx_platform_data lp5521_platform_data = {
	.led_config = lp5521_led_config,
	.num_channels = ARRAY_SIZE(lp5521_led_config),
	.clock_mode = LP55XX_CLOCK_EXT,
	.setup_resources = lp5521_setup,
	.release_resources = lp5521_release,
	.enable = lp5521_enable,
};
```

注释：
  chan_nr的值可在0和2之间
每个通道的名称可以是可配置的
如果未定义名称字段，则默认名称将设置为'xxxx:channelN'
（XXXX：pdata->label或i2c客户端名称，N：通道编号）

如果在平台数据中将电流设置为0，则该通道被禁用且在sysfs中不可见。
你没有给出需要翻译的文本，所以我无法完成翻译。请提供需要翻译成中文的英文文本。例如：

Translate to Chinese: "Hello, how are you?"

你好，你怎么样？
