========================
Linux 下的 LED 控制
========================

在最简单的形式下，LED 类仅允许用户空间控制 LED。LED 在 /sys/class/leds/ 目录下可见。LED 的最大亮度由 max_brightness 文件定义。brightness 文件将设置 LED 的亮度（取值范围为 0 到 max_brightness）。大多数 LED 没有硬件亮度支持，因此对于非零亮度设置，它们将被开启。
该类还引入了可选的 LED 触发器概念。触发器是基于内核的 LED 事件源。触发器可以是简单或复杂的。简单触发器不可配置，并旨在以最少的额外代码融入现有子系统。例如，disk-activity、nand-disk 和 sharpsl-charge 触发器。当禁用 LED 触发器时，代码会优化掉复杂触发器。
虽然所有 LED 都可以使用复杂触发器，但这些触发器具有 LED 特定参数，并按每个 LED 进行工作。定时器触发器就是一个例子。
定时器触发器会周期性地改变 LED 亮度，在 LED_OFF 和当前亮度设置之间切换。"on" 和 "off" 时间可通过 /sys/class/leds/<device>/delay_{on,off}（以毫秒为单位）指定。
您可以独立于定时器触发器更改 LED 的亮度值。但是，如果您将亮度值设置为 LED_OFF，则也会禁用定时器触发器。
您可以通过类似 I/O 调度程序选择的方式来更改触发器（通过 /sys/class/leds/<device>/trigger）。选定特定触发器后，触发器特定参数可能出现在 /sys/class/leds/<device> 中。

设计哲学
=================

基础的设计哲学是简单性。LED 是简单设备，目标是保持少量代码提供尽可能多的功能。在建议增强功能时，请记住这一点。

LED 设备命名
=================

目前的形式如下：

	"devicename:color:function"

- devicename:
        应该是指内核创建的唯一标识符，例如，对于网络设备为 phyN 或对于输入设备为 inputN，而不是指硬件；与给定设备相关的产品和总线信息可在 sysfs 中找到，并可使用 tools/leds 目录下的 get_led_device_info.sh 脚本检索；通常，此部分主要用于与其它设备有关联的 LED
- color:
        来自头文件 include/dt-bindings/leds/common.h 的 LED_COLOR_ID_* 定义之一
- function:
        来自头文件 include/dt-bindings/leds/common.h 的 LED_FUNCTION_* 定义之一
如果缺少所需的颜色或功能，请向 linux-leds@vger.kernel.org 提交补丁。
对于特定平台，可能需要多个颜色和功能相同但仅通过序数编号区分的 LED。
在这种情况下，最好是在驱动程序中将预定义的 LED_FUNCTION_* 名称与所需的 "-N" 后缀拼接起来。基于 fwnode 的驱动程序可以使用 function-enumerator 属性来实现这一点，然后在注册 LED 类设备时，LED 核心会自动处理拼接。
LED 子系统还具有防止名称冲突的保护机制，这可能会发生在热插拔设备的驱动程序创建 LED 类设备且未提供唯一 devicename 情况下。在这种情况下，会在请求的 LED 类设备名称后添加数字后缀（例如 "_1"、"_2"、"_3" 等）。
仍然可能存在使用供应商或产品名称作为 devicename 的 LED 类驱动程序，但现在这种方法已废弃，因为它没有带来任何附加价值。产品信息可以在 sysfs 的其他地方找到（参见 tools/leds/get_led_device_info.sh）。
正确的 LED 名称示例：

  - "red:disk"
  - "white:flash"
  - "red:indicator"
  - "phy1:green:wlan"
  - "phy3::wlan"
  - ":kbd_backlight"
  - "input5::kbd_backlight"
  - "input3::numlock"
  - "input3::scrolllock"
  - "input3::capslock"
  - "mmc1::status"
  - "white:status"

get_led_device_info.sh 脚本可用于验证 LED 名称是否符合此处指出的要求。它会对 LED 类设备名称部分进行验证，并在验证失败时给出预期值的提示。目前，该脚本支持以下类型设备与 LED 关联性的验证：

  - 输入设备
  - 符合 IEEE 802.11 的 USB 设备

该脚本开放扩展。
有人呼吁将 LED 的属性（如颜色）导出为单独的 led 类属性。为了避免过多开销，我建议这些属性成为设备名称的一部分。上述命名方案为将来可能需要的其他属性留出了空间。如果名称中的部分不适用，则可以将其留空。
亮度设置 API
=============

LED 子系统核心提供了以下 API 来设置亮度：

- `led_set_brightness`: 保证不会休眠，传递 LED_OFF 值会停止闪烁。

- `led_set_brightness_sync`: 当需要立即生效时使用 —— 它可能会阻塞调用者，以访问设备寄存器所需的时间并可能休眠，传递 LED_OFF 值会停止硬件闪烁，如果启用了软件闪烁回退，则返回 -EBUSY。
LED 注册 API
=============

想要为其自身或其他驱动程序 / 用户空间注册 LED 类设备的驱动程序需要分配和填充一个 led_classdev 结构体，然后调用 `[devm_]led_classdev_register`。如果使用非 devm 版本，驱动程序必须在其移除函数中调用 `led_classdev_unregister` 并在释放 led_classdev 结构体之前完成。
如果驱动程序可以检测到硬件引发的亮度变化，并希望拥有 brightness_hw_changed 属性，则在注册之前必须在 flags 中设置 LED_BRIGHT_HW_CHANGED 标志。对未使用 LED_BRIGHT_HW_CHANGED 标志注册的类设备调用 `led_classdev_notify_brightness_hw_changed` 是一个错误，并会触发 WARN_ON。
标题：硬件加速的LED闪烁

有些LED可以被编程以在没有CPU介入的情况下闪烁。为了支持这一特性，LED驱动器可选地实现blink_set()函数（见<linux/leds.h>）。然而，要将LED设置为闪烁状态，最好使用API函数led_blink_set()，因为它会检查并必要时实施软件回退。要停止闪烁，使用API函数led_brightness_set()并将亮度值设为LED_OFF，这应该停止任何可能因闪烁而需要的软件定时器。
如果blink_set()函数被调用时参数`*delay_on==0` && `*delay_off==0`，它应当选择一个用户友好的闪烁值。在这种情况下，驱动器应通过delay_on和delay_off参数向LED子系统返回所选的值。
通过brightness_set()回调函数将亮度设置为零应当完全关闭LED，并取消之前可能已编程的硬件闪烁功能。

标题：由硬件驱动的LED

有些LED可以被编程为由硬件驱动。这不仅仅限于闪烁，还包括自主地关闭或开启。
对于硬件控制的支持，LED需要实现各种额外的操作，并且需要声明对所支持触发器的具体支持。
当提及硬件控制时，我们指的是由硬件驱动的LED。
LED驱动器必须定义以下值来支持硬件控制：

    - hw_control_trigger：
               在硬件控制模式下由LED支持的唯一触发器名称。
LED驱动器必须实现以下API来支持硬件控制：
    - hw_control_is_supported：
                检查由支持的触发器传递的标志是否可以解析，并在LED上激活硬件控制。
如果传递的标志掩码是受支持的，并且可以通过hw_control_set()设置，则返回0。
如果传递的标志掩码不受支持，必须返回-EOPNOTSUPP。在这种情况下，LED触发器将使用软件回退。
在设备未准备好或超时等任何其他错误的情况下，返回一个负错误值。
- hw_control_set：
激活硬件控制。LED驱动程序将使用从受支持的触发器传递过来的标志，并将其解析为一组模式，然后设置LED以硬件驱动的方式根据请求的模式运行。
通过brightness_set设置LED_OFF来停用硬件控制。
成功时返回0，在应用标志失败时返回一个负的错误编号。
- hw_control_get：
从已处于硬件控制下的LED获取活动模式，解析它们，并在标志中设置当前活动的标志，用于受支持的触发器。
成功时返回0，在解析初始模式失败时返回一个负的错误编号。
此函数的错误并非致命，因为设备可能处于由连接的LED触发器不支持的初始状态。
- hw_control_get_device：
返回与处于硬件控制下的LED驱动程序关联的设备。触发器可能会使用这个函数返回的设备与配置给触发器的设备进行匹配，作为闪烁事件的源并正确启用硬件控制（例如，配置为针对特定设备闪烁的网络设备触发器会将get_device返回的设备与设置硬件控制的设备进行匹配）。

返回指向struct device的指针，如果没有当前连接的设备，则返回NULL。
LED驱动程序可以默认激活额外的模式，以解决在支持的触发器上无法支持每种不同模式的问题。
例如，可以将闪烁速度硬编码为固定间隔，或启用特殊功能，如在不满足某些条件时绕过闪烁。
一个触发器应首先检查LED驱动程序是否支持硬件控制API，并检查该触发器是否受支持，以验证是否可能进行硬件控制。使用hw_control_is_supported检查是否支持这些标志，只有在最后使用hw_control_set来激活硬件控制。
触发器可以使用hw_control_get检查LED是否已经在硬件控制下，并初始化其标志。
当LED处于硬件控制下时，不可能进行软件闪烁，这样做实际上会禁用硬件控制。

已知问题
==========
LED触发器核心不能作为模块，因为简单的触发器功能会导致依赖性问题的噩梦。我认为，与简单触发器功能带来的好处相比，这是一个较小的问题。LED子系统的其余部分可以是模块化的。

请注意，这段文字描述了在Linux内核的LED子系统中如何处理硬件控制和触发器的细节。它提到了一些关键点，包括硬件控制的激活、硬件控制下的LED状态以及模块化的问题。这通常是在内核开发文档或代码注释中找到的内容。
