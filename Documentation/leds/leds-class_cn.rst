========================
Linux 下的 LED 控制
========================

在最简单的形式下，LED 类仅允许用户空间控制 LED。LED 会出现在 `/sys/class/leds/` 中。LED 的最大亮度定义在 `max_brightness` 文件中。`brightness` 文件将设置 LED 的亮度（取值范围为 0 到 `max_brightness`）。大多数 LED 没有硬件亮度支持，因此对于非零亮度设置，它们只会被打开。
该类还引入了可选的 LED 触发器概念。触发器是内核级别的 LED 事件源。触发器可以是简单的也可以是复杂的。简单触发器不可配置，并且设计时考虑了以最小的额外代码量嵌入现有子系统。例如 disk-activity、nand-disk 和 sharpsl-charge 触发器。当禁用 LED 触发器时，代码会进行优化处理。
复杂的触发器虽然对所有 LED 都可用，但具有特定于 LED 的参数，并且按每个 LED 运作。定时器触发器就是一个例子。
定时器触发器会周期性地改变 LED 的亮度，使其在 LED 关闭状态和当前亮度设置之间切换。可以通过 `/sys/class/leds/<device>/delay_{on,off}` 设置“开启”和“关闭”时间（单位：毫秒）。
您可以独立于定时器触发器更改 LED 的亮度值。但是，如果您将亮度值设置为 LED 关闭，则也会禁用定时器触发器。
您可以通过类似 I/O 调度程序选择的方式更改触发器（通过 `/sys/class/leds/<device>/trigger`）。选定特定触发器后，其特定参数可能会出现在 `/sys/class/leds/<device>` 中。

设计理念
==========

底层的设计理念是简洁性。LED 是简单的设备，目标是保持少量的代码以提供尽可能多的功能。在提议增强功能时，请记住这一点。

LED 设备命名
=============

目前的形式如下：

    "devicename:color:function"

- `devicename`: 
        应该是指由内核创建的独特标识符，例如对于网络设备使用 phyN 或者对于输入设备使用 inputN，而不是指向硬件；与给定设备相关的产品信息和总线信息可以在 sysfs 中获取，并且可以使用 tools/leds 目录下的 get_led_device_info.sh 脚本检索；通常这一部分主要针对与其它设备相关的 LED
- `color`: 
        来自头文件 `include/dt-bindings/leds/common.h` 中的 LED_COLOR_ID_* 定义之一
- `function`: 
        来自头文件 `include/dt-bindings/leds/common.h` 中的 LED_FUNCTION_* 定义之一
如果缺少所需的颜色或功能，请向linux-leds@vger.kernel.org提交补丁。
对于特定平台，可能需要多个相同颜色和功能的LED，它们之间仅通过序数进行区分。
在这种情况下，最好是在驱动程序中将预定义的LED_FUNCTION_*名称与所需的"-N"后缀拼接起来。基于fwnode的驱动程序可以使用function-enumerator属性来实现这一点，然后在LED类设备注册时，拼接操作将由LED核心自动处理。
当热插拔设备的驱动程序创建LED类设备且没有提供唯一的设备名部分时，可能会发生命名冲突。在这种情况下，在请求的LED类设备名称后添加数字后缀（例如"_1"、"_2"、"_3"等）。
可能还有一些LED类驱动程序使用供应商或产品名称作为设备名，但这种方法现在已被弃用，因为它并没有增加任何价值。产品信息可以在sysfs的其他地方找到（参见tools/leds/get_led_device_info.sh）。
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

get_led_device_info.sh脚本可用于验证LED名称是否满足此处提出的要求。它会验证LED类设备名部分，并在验证失败时给出关于预期值的提示。目前，该脚本支持以下类型的设备与LED之间的关联验证：

        - 输入设备
        - 符合ieee80211标准的USB设备

脚本是开放扩展的。

有人提议将LED属性（如颜色）导出为单独的LED类属性。为了减少开销，我建议这些属性成为设备名称的一部分。上述命名方案为将来可能需要的更多属性留出了空间。如果名称的部分不适用，则可以将其留空。

**亮度设置API**

LED子系统核心提供了以下API用于设置亮度：

    - led_set_brightness：
		保证不会睡眠，传递LED_OFF将停止闪烁，

    - led_set_brightness_sync：
		适用于需要立即效果的情况——它可能会阻塞调用者以访问设备寄存器所需的时间并可能睡眠，传递LED_OFF将停止硬件闪烁，如果启用了软件闪烁回退则返回-EBUSY

**LED注册API**

想要为其自身或其他驱动程序/用户空间注册LED类设备的驱动程序需要分配并填充一个led_classdev结构体，然后调用`[devm_]led_classdev_register`。如果使用非devm版本，则在释放led_classdev结构体之前，驱动程序必须在其remove函数中调用led_classdev_unregister。
如果驱动程序能够检测到由硬件发起的亮度变化，并希望具有brightness_hw_changed属性，则在注册前必须在flags中设置LED_BRIGHT_HW_CHANGED标志。对未使用LED_BRIGHT_HW_CHANGED标志注册的类设备调用led_classdev_notify_brightness_hw_changed是一个错误，将触发WARN_ON警告。
### 硬件加速的LED闪烁

一些LED可以被编程为在没有任何CPU交互的情况下闪烁。为了支持这个特性，LED驱动程序可以选择实现`blink_set()`函数（参见 `<linux/leds.h>`）。然而，要设置一个LED进行闪烁，最好是使用API函数`led_blink_set()`，因为它会检查并根据需要实现软件回退。要关闭闪烁，可以使用API函数`led_brightness_set()`并将亮度值设为`LED_OFF`，这应该停止任何可能为闪烁所需的软件定时器。
当`blink_set()`函数被调用时，如果参数`*delay_on == 0`且`*delay_off == 0`，则应选择一个用户友好的闪烁值。在这种情况下，驱动程序应该通过`delay_on`和`delay_off`参数将所选的值返回给LED子系统。
通过`brightness_set()`回调函数将亮度设置为零应该完全关闭LED，并取消之前可能已编程的硬件闪烁功能。
### 由硬件驱动的LED

一些LED可以被编程为由硬件驱动。这不仅仅限于闪烁，还包括自主地打开或关闭。
当我们提到硬件控制时，指的是由硬件驱动的LED。
LED驱动程序必须定义以下值以支持硬件控制：

    - `hw_control_trigger`：
          在硬件控制模式下由LED支持的唯一触发器名称
LED驱动程序必须实现以下API以支持硬件控制：

    - `hw_control_is_supported`：
            检查由支持的触发器传递的标志是否可以解析，并激活LED上的硬件控制
返回0表示传递的标志掩码是受支持的，并且可以通过`hw_control_set()`设置
如果传递的标志掩码不受支持，则必须返回 `-EOPNOTSUPP`，在这种情况下 LED 触发器将使用软件回退。
在遇到其他错误（如设备未准备好或超时）的情况下返回一个负数表示的错误。
- `hw_control_set`：
    激活硬件控制。LED 驱动程序将使用从受支持的触发器传递过来的标志，并将它们解析为一组模式，然后设置 LED 以根据请求的模式由硬件驱动。
    通过 `brightness_set` 设置 `LED_OFF` 来停用硬件控制。
    成功时返回 0，无法应用标志时返回一个负数表示的错误号。
- `hw_control_get`：
    从已经处于硬件控制状态下的 LED 获取活动模式，解析这些模式，并在标志中设置当前活动的标志，供受支持的触发器使用。
    成功时返回 0，在解析初始模式失败时返回一个负数表示的错误号。
    该函数返回的错误不是致命的，因为设备可能处于不受所连接 LED 触发器支持的初始状态。
- `hw_control_get_device`：
    返回与处于硬件控制状态下的 LED 驱动程序相关联的设备。触发器可能会使用此函数返回的设备与配置给触发器的设备进行匹配，作为闪烁事件的来源，并正确启用硬件控制
    （例如，一个网络设备触发器被配置为特定设备的闪烁，需要与 `get_device` 返回的设备相匹配来设置硬件控制）。

    返回指向 `struct device` 的指针，如果没有连接任何设备则返回 `NULL`。
LED驱动程序可以默认激活额外的模式，以此来解决在支持的触发器上无法支持每种不同模式的问题。例如，可以将闪烁速度硬编码为固定间隔，或者启用特殊功能，如在不满足某些条件时绕过闪烁操作。
一个触发器首先应检查LED驱动程序是否支持硬件控制API，并检查该触发器是否被支持以验证是否可能进行硬件控制。使用`hw_control_is_supported`检查是否支持这些标志，并且只有在最后使用`hw_control_set`来激活硬件控制。
触发器可以使用`hw_control_get`来检查LED是否已经处于硬件控制之下，并初始化其标志。
当LED处于硬件控制下时，不可能进行软件闪烁，这样做实际上会禁用硬件控制。

### 已知问题

LED触发核心不能作为一个模块，因为简单的触发功能会导致依赖关系变得极其复杂。我认为与简单触发功能带来的好处相比，这是一个较小的问题。LED子系统的其余部分可以是可插拔的模块。
