==============================
Linux 下的 Flash LED 处理
==============================

一些 LED 设备提供了两种模式——手电筒模式和闪光模式。在 LED 子系统中，这两种模式分别由 LED 类（见 `Documentation/leds/leds-class.rst`）和 LED Flash 类支持。手电筒模式相关的功能默认启用，而闪光模式的功能仅在驱动程序设置 `LED_DEV_CAP_FLASH` 标志时才启用。为了支持闪光 LED，内核配置中必须定义 `CONFIG_LEDS_CLASS_FLASH` 符号。一个 LED Flash 类驱动程序必须通过 `led_classdev_flash_register` 函数注册到 LED 子系统中。

以下 sysfs 属性用于控制闪光 LED 设备：
（见 `Documentation/ABI/testing/sysfs-class-led-flash`）

- flash_brightness
- max_flash_brightness
- flash_timeout
- max_flash_timeout
- flash_strobe
- flash_fault

V4L2 闪光包装器用于闪光 LED
=================================

一个 LED 子系统驱动程序也可以从 VideoForLinux2 子系统的级别进行控制。为此，内核配置中必须定义 `CONFIG_V4L2_FLASH_LED_CLASS` 符号。驱动程序必须调用 `v4l2_flash_init` 函数以在 V4L2 子系统中注册。该函数需要六个参数：

- dev:
  闪光设备，例如 I2C 设备。
- of_node:
  LED 的 of_node，如果与设备相同则可以为 NULL。
- fled_cdev:
  要包装的 LED Flash 类设备。
- iled_cdev:
  与 `fled_cdev` 关联的指示 LED 的 LED Flash 类设备，可以为 NULL。
- ops:
  V4L2 特定的操作：

  * external_strobe_set
    定义闪光 LED 闪烁源——是使用 `V4L2_CID_FLASH_STROBE` 控制还是外部源（通常是传感器），以便能够同步闪光开始与曝光开始。
  * intensity_to_led_brightness 和 led_brightness_to_intensity
    在设备特定的方式下执行 enum `led_brightness` <-> V4L2 强度转换——可用于具有非线性 LED 电流比例的设备。
- config:
  V4L2 Flash 子设备的配置：

  * dev_name
    媒体实体的名称，在系统中唯一。
  * flash_faults
    LED Flash 类设备可以报告的闪光故障位掩码；相应的 `LED_FAULT*` 位定义可以在 `<linux/led-class-flash.h>` 中找到。
  * torch_intensity
    手电筒模式下 LED 的约束条件，单位为微安培。
  * indicator_intensity
    指示 LED 的约束条件，单位为微安培。
  * has_external_strobe
    确定是否可以将闪光闪烁源切换到外部。

在卸载时，必须调用 `v4l2_flash_release` 函数，该函数需要一个参数——之前由 `v4l2_flash_init` 返回的 `struct v4l2_flash` 指针。此函数可以安全地接受 NULL 或错误指针作为参数。
请参考 `drivers/leds/leds-max77693.c` 文件中的示例来使用 V4L2 闪光包装器。
一旦由创建了 Media 控制器设备的驱动程序注册了 V4L2 子设备，子设备节点就像一个原生 V4L2 闪光 API 设备的节点一样工作。调用会被简单地路由到 LED 闪光 API。
打开 V4L2 闪光子设备会使 LED 子系统的 sysfs 接口不可用。在关闭 V4L2 闪光子设备后，该接口会重新启用。
