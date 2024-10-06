========================
LP5523 内核驱动程序
========================

* 国家半导体 LP5523 LED 驱动芯片
* 数据手册：http://www.national.com/pf/LP/LP5523.html

作者：Mathias Nyman、Yuri Zaporozhets、Samu Onkalo
联系人：Samu Onkalo（samu.p.onkalo-at-nokia.com）

描述
-----------
LP5523 最多可以驱动 9 个通道。LED 可以通过 LED 类控制接口直接控制。
每个通道的名称可以在平台数据中进行配置 —— 名称和标签。

有三种方式来定义通道名称：
a) 在平台数据中定义 'name'

要使用特定的通道名称，请使用 'name' 平台数据：
- /sys/class/leds/R1               （name: 'R1'）
- /sys/class/leds/B1               （name: 'B1'）

b) 使用 'label' 而不使用 'name' 字段

对于一个设备名称加上通道编号，可以使用 'label'：
- /sys/class/leds/RGB:channelN     （label: 'RGB', N: 0 ~ 8）

c) 默认

如果两个字段都为空，则默认使用 'lp5523'：
- /sys/class/leds/lp5523:channelN  （N: 0 ~ 8）

LP5523 内部具有用于运行各种 LED 模式的程序内存。
有两种方式来运行 LED 模式：
1) 传统接口 —— enginex_mode, enginex_load 和 enginex_leds

  发动机控制接口：

  x 是 1 到 3

  enginex_mode:
    disabled, load, run
  enginex_load:
    微码加载
  enginex_leds:
    LED 多路复用控制

  示例：

  ```
  cd /sys/class/leds/lp5523:channel2/device
  echo "load" > engine3_mode
  echo "9d80400004ff05ff437f0000" > engine3_load
  echo "111111111" > engine3_leds
  echo "run" > engine3_mode
  ```

  要停止发动机：

  ```
  echo "disabled" > engine3_mode
  ```

2) 固件接口 —— LP55xx 公共接口

详细信息请参阅 `leds-lp55xx.txt` 中的“固件”部分。

LP5523 有三个主调光器。如果一个通道映射到其中一个主调光器，其输出将根据主调光器的值进行调光。
例如：

  ```
  echo "123000123" > master_fader_leds
  ```

这会创建以下通道-调光器映射：

  通道 0,6 映射到 master_fader1
  通道 1,7 映射到 master_fader2
  通道 2,8 映射到 master_fader3

然后，要在通道 0,6 上获得原始输出的 25%：

  ```
  echo 64 > master_fader1
  ```

要在通道 1,7 上获得 0% 的原始输出（即无输出）：

  ```
  echo 0 > master_fader2
  ```

要在通道 2,8 上获得 100% 的原始输出（即无调光）：

  ```
  echo 255 > master_fader3
  ```

要清除所有主调光器控制：

  ```
  echo "000000000" > master_fader_leds
  ```

自检始终使用平台数据中的电流。
每个通道包含 LED 电流设置：
- `/sys/class/leds/lp5523:channel2/led_current` - 读写（RW）
- `/sys/class/leds/lp5523:channel2/max_current` - 只读（RO）

格式：10x mA，即 10 表示 1.0 mA

示例平台数据：

```c
static struct lp55xx_led_config lp5523_led_config[] = {
	{
		.name       = "D1",
		.chan_nr    = 0,
		.led_current    = 50,
		.max_current    = 130,
	},
	...
	{
		.chan_nr    = 8,
		.led_current    = 50,
		.max_current    = 130,
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
	.num_channels   = ARRAY_SIZE(lp5523_led_config),
	.clock_mode     = LP55XX_CLOCK_EXT,
	.setup_resources   = lp5523_setup,
	.release_resources = lp5523_release,
	.enable            = lp5523_enable,
};
```

注意
`chan_nr` 的值可以在 0 到 8 之间。
