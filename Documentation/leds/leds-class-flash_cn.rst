==============================
Linux 下的 Flash LED 控制
==============================

一些 LED 设备提供了两种模式 —— 手电筒和闪光。在 LED 子系统中，这两种模式分别由 LED 类（参见 `Documentation/leds/leds-class.rst`）和支持 LED 闪光类来支持。与手电筒模式相关的功能默认启用，而闪光功能仅当驱动程序通过设置 `LED_DEV_CAP_FLASH` 标志声明时才启用。
为了支持闪光 LED，必须在内核配置中定义 `CONFIG_LEDS_CLASS_FLASH` 符号。一个 LED 闪光类驱动程序必须使用 `led_classdev_flash_register` 函数在 LED 子系统中注册。以下是用于控制闪光 LED 设备的 sysfs 属性：
- flash_brightness
- max_flash_brightness
- flash_timeout
- max_flash_timeout
- flash_strobe
- flash_fault

V4L2 闪光封装器对于闪光 LED 的支持
==================================

LED 子系统的驱动程序也可以从 VideoForLinux2 子系统的层面进行控制。为此，需要在内核配置中定义 `CONFIG_V4L2_FLASH_LED_CLASS` 符号。
驱动程序必须调用 `v4l2_flash_init` 函数以在 V4L2 子系统中注册。该函数接收六个参数：

- dev:
    闪光设备，例如 I2C 设备
- of_node:
    LED 的 of_node，如果与设备相同则可以为 NULL
- fled_cdev:
    要封装的 LED 闪光类设备
- iled_cdev:
    与 `fled_cdev` 关联的指示 LED 的 LED 闪光类设备，可以为 NULL
- ops:
    V4L2 特定的操作：

    * external_strobe_set
        定义了闪光 LED 闪烁源 —— 是来自 `V4L2_CID_FLASH_STROBE` 控制还是外部源（通常是传感器），这使得可以将闪光开始与曝光开始同步，
    * intensity_to_led_brightness 和 led_brightness_to_intensity
        在设备特定的方式下执行 enum `led_brightness` <-> V4L2 强度的转换 —— 这些可以用于具有非线性 LED 电流刻度的设备
- config:
    针对 V4L2 闪光子设备的配置：

    * dev_name
        媒体实体的名称，在系统中是唯一的，
    * flash_faults
        LED 闪光类设备可以报告的闪存故障的位掩码；对应的 `LED_FAULT*` 位定义可在 `<linux/led-class-flash.h>` 中找到，
    * torch_intensity
        LED 在手电筒模式下的约束条件，单位微安培，
    * indicator_intensity
        指示 LED 的约束条件，单位微安培，
    * has_external_strobe
        决定了闪光灯的闪烁源是否可以切换到外部，

在移除时，必须调用 `v4l2_flash_release` 函数，该函数接收一个参数 —— 之前由 `v4l2_flash_init` 返回的 `struct v4l2_flash` 指针。
此函数可以安全地与 NULL 或错误指针一起调用。
请参阅 `drivers/leds/leds-max77693.c` 以获取 `v4l2` 闪光封装器使用的示例。
一旦由创建媒体控制器设备的驱动程序注册了 V4L2 子设备，该子设备节点就类似于原生 V4L2 闪光 API 设备的节点。调用被简单地路由到 LED 闪光 API。
打开 V4L2 闪光子设备会使 LED 子系统的 sysfs 接口不可用。在关闭 V4L2 闪光子设备后，该接口将重新启用。
