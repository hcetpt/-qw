========================
LP5562 内核驱动程序
========================

* TI LP5562 LED 驱动程序

作者：Milo(Woogyom) Kim <milo.kim@ti.com>

描述
===========

  LP5562 可以驱动最多 4 个通道。红（R）、绿（G）、蓝（B）和白色（White）LED 可以通过 led 类控制接口直接控制。
所有四个通道也可以使用引擎微程序来控制。LP5562 具有内部程序存储器，用于运行各种 LED 模式。
详细信息，请参阅 `leds-lp55xx.txt` 中的“固件”部分。

设备属性
================

engine_mux
  在 LP5562 中分配了 3 个引擎，但通道数为 4。
因此，每个通道应映射到引擎编号。
值：RGB 或 W

  此属性用于通过固件接口编程 LED 数据。
与 LP5521/LP5523/55231 不同，LP5562 的 engine_mux 功能独特，
因此需要额外的 sysfs。

  LED 映射

  ===== === ===============================
  红色   ... 引擎 1（固定）
  绿色 ... 引擎 2（固定）
  蓝色  ... 引擎 3（固定）
  白色 ... 引擎 1 或 2 或 3（可选）
  ===== === ===============================

如何使用 engine_mux 加载程序数据
=============================================

  在加载 LP5562 程序数据之前，应先在引擎选择和加载固件之间写入 engine_mux。
engine_mux 有两种不同的模式，RGB 和 W。
RGB 用于加载 RGB 程序数据，W 用于加载白色（W）程序数据。
例如，运行闪烁的绿色通道模式：

```
echo 2 > /sys/bus/i2c/devices/xxxx/select_engine     # 2 表示绿色通道
echo "RGB" > /sys/bus/i2c/devices/xxxx/engine_mux    # RGB 的引擎复用器
echo 1 > /sys/class/firmware/lp5562/loading
echo "4000600040FF6000" > /sys/class/firmware/lp5562/data
echo 0 > /sys/class/firmware/lp5562/loading
echo 1 > /sys/bus/i2c/devices/xxxx/run_engine
```

要运行闪烁的白色模式：

```
echo 1 或者 2 或者 3 > /sys/bus/i2c/devices/xxxx/select_engine
echo "W" > /sys/bus/i2c/devices/xxxx/engine_mux
echo 1 > /sys/class/firmware/lp5562/loading
echo "4000600040FF6000" > /sys/class/firmware/lp5562/data
echo 0 > /sys/class/firmware/lp5562/loading
echo 1 > /sys/bus/i2c/devices/xxxx/run_engine
```

如何加载预定义的模式
==================

请参考 'leds-lp55xx.txt'

设置每个通道的电流
==================

如同 LP5521 和 LP5523/55231，LP5562 提供了 LED 电流设置。
使用 'led_current' 和 'max_current'
平台数据示例
============

``` 
static struct lp55xx_led_config lp5562_led_config[] = {
	{
		.name       = "R",
		.chan_nr    = 0,
		.led_current= 20,
		.max_current= 40,
	},
	{
		.name       = "G",
		.chan_nr    = 1,
		.led_current= 20,
		.max_current= 40,
	},
	{
		.name       = "B",
		.chan_nr    = 2,
		.led_current= 20,
		.max_current= 40,
	},
	{
		.name       = "W",
		.chan_nr    = 3,
		.led_current= 20,
		.max_current= 40,
	},
};

static int lp5562_setup(void)
{
	/* 设置硬件资源 */
}

static void lp5562_release(void)
{
	/* 释放硬件资源 */
}

static void lp5562_enable(bool state)
{
	/* 控制芯片使能信号 */
}

static struct lp55xx_platform_data lp5562_platform_data = {
	.led_config     = lp5562_led_config,
	.num_channels   = ARRAY_SIZE(lp5562_led_config),
	.setup_resources   = lp5562_setup,
	.release_resources = lp5562_release,
	.enable            = lp5562_enable,
};
```

为了配置平台特定的数据，使用 lp55xx_platform_data 结构体。

如果在平台数据中将电流设置为 0，那么该通道将被禁用，并且在 sysfs 中不可见。
