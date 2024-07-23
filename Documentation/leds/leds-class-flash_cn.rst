在Linux下处理闪光LED
==============================

一些LED设备提供了两种模式——手电筒和闪光。在LED子系统中，这两种模式分别由LED类（参见Documentation/leds/leds-class.rst）和LED闪光类支持。默认情况下，与手电筒模式相关的特点是启用的，而闪光特点仅在驱动程序通过设置LED_DEV_CAP_FLASH标志声明时才启用。
为了支持闪光LED，内核配置中必须定义CONFIG_LEDS_CLASS_FLASH符号。LED闪光类驱动程序必须使用led_classdev_flash_register函数在LED子系统中注册。以下sysfs属性被暴露用于控制闪光LED设备：（参见Documentation/ABI/testing/sysfs-class-led-flash）

    - flash_brightness
    - max_flash_brightness
    - flash_timeout
    - max_flash_timeout
    - flash_strobe
    - flash_fault


V4L2闪光包装器为闪光LED
=================================

LED子系统驱动程序也可以从VideoForLinux2子系统的级别进行控制。为此，内核配置中必须定义CONFIG_V4L2_FLASH_LED_CLASS符号。
驱动程序必须调用v4l2_flash_init函数以在V4L2子系统中注册。该函数接受六个参数：

- dev：
   闪光设备，例如I2C设备
- of_node：
   LED的of_node，如果与设备相同则可以为NULL
- fled_cdev：
   要包装的LED闪光类设备
- iled_cdev：
   与fled_cdev关联的指示LED的LED闪光类设备，可能为NULL
- ops：
   V4L2特定的操作

     * external_strobe_set
       定义闪光LED闪烁源——V4L2_CID_FLASH_STROBE控制或外部源，通常是传感器，这使得能够将闪光开始与曝光开始同步，
     * intensity_to_led_brightness 和 led_brightness_to_intensity
       在设备特定方式下执行
       枚举led_brightness <-> V4L2强度转换——它们可用于具有非线性LED电流刻度的设备
- config：
   V4L2闪光子设备的配置

     * dev_name
       媒体实体的名称，在系统中唯一，
     * flash_faults
       LED闪光类设备可以报告的闪光故障位掩码；相应的LED_FAULT*位定义在<linux/led-class-flash.h>中可用，
     * torch_intensity
       LED在TORCH模式下的约束
       以微安培为单位，
     * indicator_intensity
       指示LED的约束
       以微安培为单位，
     * has_external_strobe
       确定是否可以将闪光闪烁源
       切换到外部，

移除时，必须调用v4l2_flash_release函数，它接受一个参数——之前由v4l2_flash_init返回的struct v4l2_flash指针
此函数可以安全地用NULL或错误指针参数调用
请参阅drivers/leds/leds-max77693.c以了解v4l2闪光包装器的示例性使用
一旦由创建Media控制器设备的驱动程序注册了V4L2子设备，子设备节点就像本机V4L2闪光API设备的节点一样工作。调用被简单地路由到LED闪光API
打开V4L2闪光子设备会使LED子系统sysfs接口不可用。在关闭V4L2闪光子设备后，接口将重新启用。
