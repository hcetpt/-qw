========================
Linux 下的 LED 控制
========================

在最简单的情况下，LED 类别仅允许用户空间控制 LED。LED 在 /sys/class/leds/ 中出现。LED 的最大亮度定义在 max_brightness 文件中。brightness 文件将设置 LED 的亮度（取值范围为 0 到 max_brightness）。大多数 LED 没有硬件亮度支持，因此在非零亮度设置下只会被开启。
该类别还引入了可选的 LED 触发器概念。触发器是内核级别的 LED 事件源。触发器可以是简单的也可以是复杂的。简单触发器不可配置，并且设计用于以最少的额外代码嵌入现有子系统。例如，disk-activity、nand-disk 和 sharpsl-charge 触发器。当禁用 LED 触发器时，代码会优化掉复杂触发器。
尽管所有 LED 都可以使用复杂触发器，但它们具有特定于 LED 的参数，并按每个 LED 进行工作。计时器触发器就是一个例子。
计时器触发器会周期性地改变 LED 的亮度，在 LED_OFF 和当前亮度设置之间切换。“on”和“off”的时间可以通过 /sys/class/leds/<device>/delay_{on,off}（以毫秒为单位）来指定。
您可以独立于计时器触发器更改 LED 的亮度值。但是，如果您将亮度值设置为 LED_OFF，则也会禁用计时器触发器。
您可以通过类似 I/O 调度器选择的方式更改触发器（通过 /sys/class/leds/<device>/trigger）。选定特定触发器后，触发器特定的参数会出现在 /sys/class/leds/<device> 中。

设计理念
=================

底层的设计理念是简洁。LED 是简单的设备，目标是保持少量代码提供尽可能多的功能。在建议增强功能时，请牢记这一点。

LED 设备命名
=================

目前的形式如下：

    "devicename:color:function"

- devicename：
        应该是指由内核创建的独特标识符，如对于网络设备的 phyN 或对于输入设备的 inputN，而不是指硬件；与给定设备相关的产品信息和所连接的总线信息可以在 sysfs 中找到，并且可以使用工具目录下的 get_led_device_info.sh 脚本获取；通常这一部分主要用于与其它设备有一定关联的 LED
- color：
        来自头文件 include/dt-bindings/leds/common.h 中的 LED_COLOR_ID_* 定义之一
- function：
        来自头文件 include/dt-bindings/leds/common.h 中的 LED_FUNCTION_* 定义之一
如果缺少所需的颜色或功能，请向linux-leds@vger.kernel.org提交补丁。
对于给定平台，可能需要多个颜色和功能相同的LED，仅通过序号区分。
在这种情况下，最好在驱动程序中将预定义的LED_FUNCTION_*名称与所需的"-N"后缀拼接。基于fwnode的驱动程序可以使用function-enumerator属性，然后在注册LED类设备时，LED核心会自动处理拼接。
LED子系统还具有防止名称冲突的保护机制，这可能会发生在热插拔设备的驱动程序创建LED类设备且未提供唯一设备名的情况下。此时会在请求的LED类设备名称后添加数字后缀（例如"_1"、"_2"、"_3"等）。
仍然可能存在使用供应商或产品名称作为设备名的LED类驱动程序，但这种方法现在已弃用，因为它没有任何附加价值。产品信息可以在sysfs中的其他地方找到（参见tools/leds/get_led_device_info.sh）。
正确的LED名称示例：

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

get_led_device_info.sh脚本可用于验证LED名称是否符合此处指出的要求。它会对LED类设备名部分进行验证，并在验证失败时给出该部分预期值的提示。目前，该脚本支持对以下类型设备与LED之间关联的验证：

  - 输入设备
  - 符合ieee80211标准的USB设备

该脚本支持扩展。
有人建议将LED属性（如颜色）导出为单独的LED类属性。为了避免过多开销，我建议这些属性成为设备名称的一部分。上述命名方案为将来可能需要的更多属性留出了空间。如果某些部分不适用，则只需留空即可。

亮度设置API
=============

LED子系统核心提供了以下API用于设置亮度：

- `led_set_brightness`：
  保证不会休眠，传递LED_OFF将停止闪烁，

- `led_set_brightness_sync`：
  在需要立即生效的情况下使用——它可以阻塞调用者直到访问设备寄存器所需的时间，并且可以休眠，传递LED_OFF将停止硬件闪烁，如果启用了软件闪烁回退，则返回-EAGAIN。

LED注册API
=============

想要为其他驱动程序/用户空间注册LED类设备的驱动程序需要分配并填充一个`led_classdev`结构体，然后调用`[devm_]led_classdev_register`。如果使用非devm版本，则必须在删除函数中调用`led_classdev_unregister`，然后再释放`led_classdev`结构体。
如果驱动程序能够检测到由硬件引发的亮度变化，并希望具有brightness_hw_changed属性，则在注册之前必须在flags中设置LED_BRIGHT_HW_CHANGED标志。对未使用LED_BRIGHT_HW_CHANGED标志注册的类设备调用`led_classdev_notify_brightness_hw_changed`是错误行为，并会触发WARN_ON警告。
### 硬件加速的LED闪烁

一些LED可以通过编程实现无需CPU干预的闪烁。为了支持此功能，LED驱动程序可以选择性地实现`blink_set()`函数（见`<linux/leds.h>`）。然而，要将LED设置为闪烁状态，最好使用API函数`led_blink_set()`，因为它会检查并在必要时实现软件回退。
要停止闪烁，可以使用API函数`led_brightness_set()`并将亮度值设为`LED_OFF`，这应该会停止任何可能需要用于闪烁的软件定时器。
当`blink_set()`函数被调用且参数`*delay_on == 0` && `*delay_off == 0`时，应选择一个用户友好的闪烁值。在这种情况下，驱动程序应通过`delay_on`和`delay_off`参数将所选值返回给LED子系统。
通过`brightness_set()`回调函数将亮度设置为零应该完全关闭LED，并取消之前可能编程的硬件闪烁功能。

### 硬件驱动的LED

一些LED可以通过编程实现硬件驱动。这不仅限于闪烁，还包括自主开关。
为了支持此功能，LED需要实现各种附加的操作，并声明对支持的触发器的具体支持。
我们所说的硬件控制是指由硬件驱动的LED。
LED驱动程序必须定义以下值以支持硬件控制：

- `hw_control_trigger`：在硬件控制模式下由LED支持的唯一触发器名称。

LED驱动程序必须实现以下API以支持硬件控制：

- `hw_control_is_supported`：检查由支持的触发器传递的标志是否可以解析并激活LED上的硬件控制。
如果传递的标志掩码受支持并且可以通过`hw_control_set()`设置，则返回0。
如果传递的标志掩码不受支持，则必须返回-EOPNOTSUPP，此时LED触发器将使用软件回退。
在出现其他错误（如设备未准备好或超时）的情况下返回负数错误代码。

- hw_control_set：
                激活硬件控制。LED驱动程序将使用从支持的触发器传递的标志，并将其解析为一组模式，然后设置LED以按照请求的模式由硬件驱动。
通过brightness_set设置LED_OFF来停用硬件控制。
成功时返回0，应用标志失败时返回负数错误代码。
- hw_control_get：
                获取已处于硬件控制状态的LED的活动模式，解析这些模式并将当前活动的标志设置到支持的触发器中。
成功时返回0，解析初始模式失败时返回负数错误代码。
此函数的错误不是致命的，因为设备可能处于不被附加的LED触发器支持的初始状态。
- hw_control_get_device：
                返回与处于硬件控制状态下的LED驱动程序关联的设备。触发器可能会使用此功能来匹配此函数返回的设备与配置的设备，以便正确启用硬件控制作为闪烁事件的源。
（例如，一个配置为针对特定设备闪烁的网络设备触发器会匹配get_device返回的设备以设置硬件控制）

                如果当前没有连接任何设备，则返回指向struct device的指针或NULL。
LED驱动程序可以默认激活额外的模式，以解决支持的不同模式无法在触发器上实现的问题。
例如，可以将闪烁速度硬编码为固定间隔，或在某些条件不满足时启用特殊功能（如跳过闪烁）。

触发器应首先检查LED驱动程序是否支持硬件控制API，并检查该触发器是否受支持，以验证是否可以进行硬件控制。使用`hw_control_is_supported`来检查是否支持这些标志，并且只有在最后使用`hw_control_set`来激活硬件控制。

触发器可以使用`hw_control_get`来检查LED是否已经在硬件控制下，并初始化其标志。

当LED处于硬件控制时，不可能进行软件闪烁，这样做实际上会禁用硬件控制。

已知问题
========

LED触发器核心不能作为模块，因为简单的触发器功能会导致依赖关系问题。我认为这是一个次要问题，与简单触发器功能带来的好处相比微不足道。LED子系统的其余部分可以是模块化的。
