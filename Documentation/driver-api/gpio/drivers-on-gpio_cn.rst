============================
使用 GPIO 的子系统驱动程序
============================

请注意，对于常见的 GPIO 任务，标准内核中已存在相应的驱动程序，这些驱动程序可以为内核内部及用户空间提供正确的 API/ABI 接口，并且这些驱动程序很容易通过诸如设备树或 ACPI 等硬件描述与内核中的其他子系统进行交互：

- leds-gpio: `drivers/leds/leds-gpio.c` 可以处理连接到 GPIO 线的 LED，为你提供 LED 的 sysfs 接口。

- ledtrig-gpio: `drivers/leds/trigger/ledtrig-gpio.c` 提供一个 LED 触发器，即当 GPIO 线变为高电平或低电平时 LED 将打开或关闭（这个 LED 可能会使用上面提到的 leds-gpio）。
- gpio-keys: `drivers/input/keyboard/gpio_keys.c` 在你的 GPIO 线可以通过按键按下产生中断时使用。同时也支持防抖动。
- gpio-keys-polled: `drivers/input/keyboard/gpio_keys_polled.c` 当你的 GPIO 线不能产生中断时使用，因此需要通过定时器周期性地轮询。
- gpio_mouse: `drivers/input/mouse/gpio_mouse.c` 仅使用 GPIO 并没有鼠标端口的情况下提供最多三个按钮的鼠标功能。你可以剪断鼠标线并将电线连接到 GPIO 线上，或者在这些线上焊接一个鼠标连接器来实现更持久的解决方案。
- gpio-beeper: `drivers/input/misc/gpio-beeper.c` 用于通过连接到 GPIO 线的外部扬声器发出蜂鸣声。（如果蜂鸣声是由开关控制的，想要得到实际的 PWM 波形，请参见下面的 pwm-gpio。）

- pwm-gpio: `drivers/pwm/pwm-gpio.c` 用于利用高分辨率计时器在 GPIO 线上生成 PWM 波形来切换 GPIO，就像 Linux 高分辨率计时器所能做的那样。
- extcon-gpio: `drivers/extcon/extcon-gpio.c` 在你需要读取外部连接器状态时使用，例如音频驱动程序的耳机线或 HDMI 连接器。它将提供比 GPIO 更好的用户空间 sysfs 接口。
- restart-gpio: `drivers/power/reset/gpio-restart.c` 通过拉起 GPIO 线来重启/重置系统，并注册一个重启处理器以便用户空间可以发出正确的系统调用来重启系统。
- poweroff-gpio: `drivers/power/reset/gpio-poweroff.c` 通过拉起 GPIO 线来关闭系统电源，并注册一个 `pm_power_off()` 回调函数，这样用户空间就可以发出正确的系统调用来关闭系统。
- gpio-gate-clock: `drivers/clk/clk-gpio.c` 用于控制使用 GPIO 的门控时钟（开/关），并集成到时钟子系统中。
- i2c-gpio: `drivers/i2c/busses/i2c-gpio.c` 用于通过敲击（位爆破）两个 GPIO 线来驱动 I2C 总线（两条线，SDA 和 SCL）。它在系统中看起来就像是任何其他 I2C 总线一样，并使得可以在总线上连接 I2C 设备的驱动程序，就像任何其他 I2C 总线驱动程序一样。
- spi_gpio: 驱动程序 `drivers/spi/spi-gpio.c` 用于通过 GPIO 锤击（位敲击）驱动 SPI 总线（可变数量的线路，至少包括 SCK，可选地包括 MISO、MOSI 和芯片选择线路）。它将像系统中的其他 SPI 总线一样出现，并使得能够像使用其他 SPI 总线驱动程序那样在总线上连接 SPI 设备的驱动程序。例如，任何 MMC/SD 卡都可以通过 MMC/SD 子系统的 mmc_spi 主机连接到此 SPI 总线。
- w1-gpio: 驱动程序 `drivers/w1/masters/w1-gpio.c` 用于通过 GPIO 线路驱动单总线，与 W1 子系统集成并像处理其他 W1 设备一样处理总线上的设备。
- gpio-fan: 驱动程序 `drivers/hwmon/gpio-fan.c` 用于控制一个连接到 GPIO 线路（以及可选的 GPIO 报警线路）的风扇来冷却系统，提供所有必要的内核和 sysfs 接口以防止系统过热。
- gpio-regulator: 驱动程序 `drivers/regulator/gpio-regulator.c` 用于通过拉拽 GPIO 线路来控制一个提供特定电压的稳压器，与稳压器子系统集成并为您提供所有正确的接口。
- gpio-wdt: 驱动程序 `drivers/watchdog/gpio_wdt.c` 用于提供一个看门狗定时器，该定时器会周期性地通过在 GPIO 线路上进行 1-0-1 的切换来“ping”硬件。如果该硬件没有定期接收到它的“ping”，它将重置系统。
- gpio-nand: 驱动程序 `drivers/mtd/nand/raw/gpio.c` 用于通过一组简单的 GPIO 线路（RDY、NCE、ALE、CLE、NWP）连接一个 NAND 闪存芯片。它与 NAND 闪存 MTD 子系统交互并像其他 NAND 驱动硬件一样提供芯片访问和分区解析功能。
- ps2-gpio: 驱动程序 `drivers/input/serio/ps2-gpio.c` 用于通过位敲击两个 GPIO 线路来驱动 PS/2（IBM）串行总线的数据和时钟线路。它对系统来说就像任何其他串行总线，并使得能够连接例如键盘和其他基于 PS/2 协议的设备的驱动程序。
- cec-gpio: 驱动程序 `drivers/media/platform/cec-gpio/` 用于仅使用 GPIO 与 CEC 消费电子控制总线交互。它用于与 HDMI 总线上的设备通信。
- gpio-charger: 驱动程序 `drivers/power/supply/gpio-charger.c` 在您需要执行电池充电且仅能通过 GPIO 线路检查 AC 充电器的存在或执行更复杂的任务（如指示充电状态）时使用。该驱动程序提供了这些功能，并且还提供了一种明确的方法来从硬件描述（如设备树）传递充电参数。
- gpio-mux: 驱动程序 `drivers/mux/gpio.c` 用于使用 n 个 GPIO 线路控制一个多路复用器，使得可以通过激活不同的 GPIO 线路来复用 2^n 个不同的设备。通常 GPIO 在 SoC 上，而设备是 SoC 外部实体，例如 PCB 上的不同组件，可以选择性启用。
除了这些，还有一些特殊的GPIO驱动程序位于诸如MMC/SD子系统中，用于读取卡片检测和写保护GPIO线路，以及在TTY串行子系统中通过使用两个GPIO线路来模拟MCTRL（调制解控控制）信号CTS/RTS。MTD NOR闪存也有额外的GPIO线路扩展，尽管地址总线通常直接连接到闪存。
不要直接从用户空间与GPIO交互；它们与内核框架的集成比你的用户空间代码更好。
不用说，仅仅使用合适的内核驱动程序就能简化并加速你的嵌入式开发工作，特别是因为它们提供了现成的组件。
