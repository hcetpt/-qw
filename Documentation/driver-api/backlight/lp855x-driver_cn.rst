===== 核心驱动程序 lp855x =====

为 LP855x 集成电路提供的背光驱动程序

支持的芯片：

- 德州仪器 LP8550、LP8551、LP8552、LP8553、LP8555、LP8556 和
- LP8557

作者：Milo (Woogyom) Kim <milo.kim@ti.com>

描述
-------------

* 亮度控制

  亮度可以通过脉宽调制（PWM）输入或 I2C 命令进行控制。
  lp855x 驱动程序同时支持这两种情况。
* 设备属性

  1) bl_ctl_mode

    背光控制模式
    值：基于 PWM 或基于寄存器

  2) chip_id

    lp855x 芯片 ID
    值：lp8550/lp8551/lp8552/lp8553/lp8555/lp8556/lp8557

lp855x 的平台数据
------------------------

为了支持特定平台的数据，可以使用 lp855x 平台数据：
* name:
    背光驱动程序名称。如果没有定义，则设置默认名称。
* device_control:
    DEVICE CONTROL 寄存器的值。
* initial_brightness:
    背光亮度的初始值。
* period_ns:
    特定平台的 PWM 周期值。单位是纳秒。
    当亮度通过 PWM 输入时才有效。
* size_program:
	总大小（元素数量）的 `lp855x_rom_data`
* rom_data:
	新 EEPROM/EPROM 寄存器的列表
示例
=====

1) `lp8552` 平台数据：使用新的 EEPROM 数据的 I2C 寄存器模式 ::

    #define EEPROM_A5_ADDR   0xA5
    #define EEPROM_A5_VAL    0x4f    /* EN_VSYNC=0 */

    static struct lp855x_rom_data lp8552_eeprom_arr[] = {
        {EEPROM_A5_ADDR, EEPROM_A5_VAL},
    };

    static struct lp855x_platform_data lp8552_pdata = {
        .name = "lcd-bl",
        .device_control = I2C_CONFIG(LP8552),
        .initial_brightness = INITIAL_BRT,
        .size_program = ARRAY_SIZE(lp8552_eeprom_arr),
        .rom_data = lp8552_eeprom_arr,
    };

2) `lp8556` 平台数据：PWM 输入模式和默认的 ROM 数据 ::

    static struct lp855x_platform_data lp8556_pdata = {
        .device_control = PWM_CONFIG(LP8556),
        .initial_brightness = INITIAL_BRT,
        .period_ns = 1000000,
    };
