========================
LP5521 内核驱动程序
========================

* 国家半导体 LP5521 LED 驱动芯片
* 数据手册：http://www.national.com/pf/LP/LP5521.html

作者：Mathias Nyman, Yuri Zaporozhets, Samu Onkalo

联系人：Samu Onkalo (samu.p.onkalo-at-nokia.com)

描述
------------

LP5521 可以驱动最多 3 个通道。LED 可以通过 LED 类控制接口直接控制。通道的通用名称为：lp5521:channelx，其中 x 是 0 到 2。

所有三个通道也可以通过引擎微程序进行控制。有关指令的更多详细信息可以从公开的数据手册中找到。
LP5521 具有内部程序存储器，可以运行各种 LED 模式。有两种方式来运行 LED 模式：
1) 传统接口 - enginex_mode 和 enginex_load
   引擎控制接口：

   x 是 1 到 3

   enginex_mode:
   禁用、加载、运行
   enginex_load:
   存储程序（仅在引擎加载模式下可见）

   示例（使通道 2 的 LED 闪烁）::

      cd /sys/class/leds/lp5521:channel2/device
      echo "load" > engine3_mode
      echo "037f4d0003ff6000" > engine3_load
      echo "run" > engine3_mode

   要停止引擎::

      echo "disabled" > engine3_mode

2) 固件接口 - LP55xx 公共接口

详情请参阅 `leds-lp55xx.txt` 中的“固件”部分。

sysfs 包含一个自检条目。该测试与芯片通信，并检查时钟模式是否自动设置为请求的模式。
每个通道都有自己的 LED 电流设置：
- /sys/class/leds/lp5521:channel0/led_current - 可读写
- /sys/class/leds/lp5521:channel0/max_current - 只读

格式：10x mA，即 10 表示 1.0 mA。

示例平台数据::

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
    /* 控制芯片启用信号 */
  }

  static struct lp55xx_platform_data lp5521_platform_data = {
    .led_config = lp5521_led_config,
    .num_channels = ARRAY_SIZE(lp5521_led_config),
    .clock_mode = LP55XX_CLOCK_EXT,
    .setup_resources = lp5521_setup,
    .release_resources = lp5521_release,
    .enable = lp5521_enable,
  };

注意事项：
  chan_nr 的值可以在 0 到 2 之间。
  每个通道的名称可以配置。
  如果未定义名称字段，默认名称将设置为 'xxxx:channelN'。
  （XXXX：pdata->label 或 I2C 客户端名称，N：通道编号）

  如果在平台数据中将电流设置为 0，则该通道被禁用，在 sysfs 中不可见。
当然，请提供你需要翻译的文本。
