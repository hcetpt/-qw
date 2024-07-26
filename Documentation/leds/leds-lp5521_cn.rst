========================
LP5521 的内核驱动程序
========================

* 国家半导体 LP5521 LED 驱动芯片
* 数据手册：http://www.national.com/pf/LP/LP5521.html

作者：Mathias Nyman, Yuri Zaporozhets, Samu Onkalo

联系人：Samu Onkalo (samu.p.onkalo-at-nokia.com)

描述
-----------

LP5521 可以驱动最多 3 个通道。LED 可以直接通过 LED 类控制接口进行控制。通道具有通用名称：lp5521:channelx，其中 x 为 0 到 2。

所有三个通道也可以使用引擎微程序来控制。更多关于指令的详细信息可以从公开的数据手册中找到。
LP5521 内部有程序存储器用于运行各种 LED 模式。有两种方式可以运行 LED 模式：
1) 传统接口 —— enginex_mode 和 enginex_load
   引擎的控制接口：

   x 是 1 到 3

   enginex_mode:
   禁用、加载、运行
   enginex_load:
   存储程序（仅在引擎加载模式下可见）

  示例（开始使通道 2 的 LED 闪烁）::

    cd /sys/class/leds/lp5521:channel2/device
    echo "load" > engine3_mode
    echo "037f4d0003ff6000" > engine3_load
    echo "run" > engine3_mode

  要停止引擎，执行如下操作::

    echo "disabled" > engine3_mode

2) 固件接口 —— LP55xx 公共接口

详情请参阅 'firmware' 部分在 leds-lp55xx.txt 文件中。

sysfs 包含一个自检入口。
测试与芯片通信，并检查时钟模式是否自动设置为您请求的模式。
每个通道都有其自己的 LED 电流设置。
- /sys/class/leds/lp5521:channel0/led_current - 读写
- /sys/class/leds/lp5521:channel0/max_current - 只读

格式：10x mA，例如 10 表示 1.0 mA

平台数据示例::

  static struct lp55xx_led_config lp5521_led_config[] = {
      {
        .name = "red",
        .chan_nr        = 0,
        .led_current    = 50,
        .max_current    = 130,
      }, {
        .name = "green",
        .chan_nr        = 1,
        .led_current    = 0,
        .max_current    = 130,
      }, {
        .name = "blue",
        .chan_nr        = 2,
        .led_current    = 0,
        .max_current    = 130,
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
      .led_config     = lp5521_led_config,
      .num_channels   = ARRAY_SIZE(lp5521_led_config),
      .clock_mode     = LP55XX_CLOCK_EXT,
      .setup_resources   = lp5521_setup,
      .release_resources = lp5521_release,
      .enable            = lp5521_enable,
  };

注意事项：
  chan_nr 的值可以在 0 到 2 之间。
每个通道的名字可以配置。
如果未定义名字字段，则默认名字将被设置为 'xxxx:channelN'
  （XXXX : pdata->label 或 I2C 客户端名称，N : 通道编号）

如果平台数据中的电流设置为 0，则该通道被禁用，并且在 sysfs 中不可见。
您没有提供需要翻译的文本。请提供需要翻译成中文的英文或其他语言的文本。
