### WatchDog 模块参数

此文件提供了许多 Linux Watchdog 驱动程序模块参数的信息。除非驱动程序有自己的特定信息文件，否则 Watchdog 驱动程序参数规范应在此列出。

有关为内置驱动程序与可加载模块提供内核参数的信息，请参阅 `Documentation/admin-guide/kernel-parameters.rst`。

---

**Watchdog 核心：**
- `open_timeout`: 
    - 单位：秒
    - Watchdog 框架在用户空间打开相应的 `/dev/watchdogN` 设备之前，处理运行中的硬件 Watchdog 的最大时间。值为 0 表示无限超时。将此设置为非零值可以确保用户空间正常启动或使板卡重置并允许引导加载程序中的回退逻辑尝试其他操作。

---

**acquirewdt：**
- `wdt_stop`: 
    - 获取 Watchdog “停止” I/O 端口（默认 0x43）
- `wdt_start`: 
    - 获取 Watchdog “启动” I/O 端口（默认 0x443）
- `nowayout`: 
    - Watchdog 启动后无法停止（默认=内核配置参数）

---

**advantechwdt：**
- `wdt_stop`: 
    - Advantech Watchdog “停止” I/O 端口（默认 0x443）
- `wdt_start`: 
    - Advantech Watchdog “启动” I/O 端口（默认 0x443）
- `timeout`: 
    - Watchdog 超时时间，单位：秒（1≤超时时间≤63，默认 60 秒）
- `nowayout`: 
    - Watchdog 启动后无法停止（默认=内核配置参数）

---

**alim1535_wdt：**
- `timeout`: 
    - Watchdog 超时时间，单位：秒（0<超时时间<18000，默认 60 秒）
- `nowayout`: 
    - Watchdog 启动后无法停止（默认=内核配置参数）

---

**alim7101_wdt：**
- `timeout`: 
    - Watchdog 超时时间，单位：秒（1≤超时时间≤3600，默认 30 秒）
- `use_gpio`: 
    - 使用 GPIO Watchdog（旧的 Cobalt 板卡必需）
    - 默认=0/关闭/否
- `nowayout`: 
    - Watchdog 启动后无法停止（默认=内核配置参数）

---

**ar7_wdt：**
- `margin`: 
    - Watchdog 边距，单位：秒（默认 60 秒）
- `nowayout`: 
    - 关闭时禁用 Watchdog 重置（默认=内核配置参数）

---

**armada_37xx_wdt：**
- `timeout`: 
    - Watchdog 超时时间，单位：秒（默认 120 秒）
- `nowayout`: 
    - 关闭时禁用 Watchdog 重置（默认=内核配置参数）

---

**at91rm9200_wdt：**
- `wdt_time`: 
    - Watchdog 时间，单位：秒（默认 5 秒）
- `nowayout`: 
    - Watchdog 启动后无法停止（默认=内核配置参数）

---

**at91sam9_wdt：**
- `heartbeat`: 
    - Watchdog 心跳周期，单位：秒（默认 15 秒）
- `nowayout`: 
    - Watchdog 启动后无法停止（默认=内核配置参数）

---

**bcm47xx_wdt：**
- `wdt_time`: 
    - Watchdog 时间，单位：秒（默认 30 秒）
- `nowayout`: 
    - Watchdog 启动后无法停止（默认=内核配置参数）

---

**coh901327_wdt：**
- `margin`: 
    - Watchdog 边距，单位：秒（默认 60 秒）

---

**cpu5wdt：**
- `port`: 
    - Watchdog 卡的基本地址（默认 0x91）
- `verbose`: 
    - 输出详细信息（默认 0，否）
- `ticks`: 
    - 计数器倒计时，单位：tick（默认 10000）

---

**cpwd：**
- `wd0_timeout`: 
    - 默认 Watchdog0 超时时间，单位：十分之一秒
- `wd1_timeout`: 
    - 默认 Watchdog1 超时时间，单位：十分之一秒
- `wd2_timeout`: 
    - 默认 Watchdog2 超时时间，单位：十分之一秒

---

**da9052wdt：**
- `timeout`: 
    - Watchdog 超时时间，单位：秒（2≤超时时间≤131，默认 2.048 秒）
- `nowayout`: 
    - Watchdog 启动后无法停止（默认=内核配置参数）

---

**davinci_wdt：**
- `heartbeat`: 
    - Watchdog 心跳周期，单位：秒（1≤心跳周期≤600，默认 60 秒）

---

**ebc-c384_wdt：**
- `timeout`: 
    - Watchdog 超时时间，单位：秒（1≤超时时间≤15300，默认 60 秒）
- `nowayout`: 
    - Watchdog 启动后无法停止

---

**ep93xx_wdt：**
- `nowayout`: 
    - Watchdog 启动后无法停止
- `timeout`: 
    - Watchdog 超时时间，单位：秒（1≤超时时间≤3600，默认待定）

---

**eurotechwdt：**
- `nowayout`: 
    - Watchdog 启动后无法停止（默认=内核配置参数）
- `io`: 
    - Eurotech Watchdog I/O 端口（默认 0x3f0）
- `irq`: 
    - Eurotech Watchdog 中断请求（默认 10）
- `ev`: 
    - Eurotech Watchdog 事件类型（默认为 `int`）

---

**gef_wdt：**
- `nowayout`: 
    - Watchdog 启动后无法停止（默认=内核配置参数）

---

**geodewdt：**
- `timeout`: 
    - Watchdog 超时时间，单位：秒（1≤超时时间≤131，默认 60 秒）
- `nowayout`: 
    - Watchdog 启动后无法停止（默认=内核配置参数）

---

**i6300esb：**
- `heartbeat`: 
    - Watchdog 心跳周期，单位：秒（1<心跳周期<2046，默认 30 秒）
- `nowayout`: 
    - Watchdog 启动后无法停止（默认=内核配置参数）

---

**iTCO_wdt：**
- `heartbeat`: 
    - Watchdog 心跳周期，单位：秒
    （2<心跳周期<39（TCO v1）或 613（TCO v2），默认 30 秒）
- `nowayout`: 
    - Watchdog 启动后无法停止（默认=内核配置参数）

---

**iTCO_vendor_support：**
- `vendorsupport`: 
    - iTCO 厂商特定支持模式（默认 0，无；1=SuperMicro Pent3；2=SuperMicro Pent4+；911=损坏的 SMI BIOS）

---

**ib700wdt：**
- `timeout`: 
    - Watchdog 超时时间，单位：秒（0≤超时时间≤30，默认 30 秒）
- `nowayout`: 
    - Watchdog 启动后无法停止（默认=内核配置参数）

---

**ibmasr：**
- `nowayout`: 
    - Watchdog 启动后无法停止（默认=内核配置参数）

---

**imx2_wdt：**
- `timeout`: 
    - Watchdog 超时时间，单位：秒（默认 60 秒）
- `nowayout`: 
    - Watchdog 启动后无法停止（默认=内核配置参数）

---

**indydog：**
- `nowayout`: 
    - Watchdog 启动后无法停止（默认=内核配置参数）

---

**iop_wdt：**
- `nowayout`: 
    - Watchdog 启动后无法停止（默认=内核配置参数）

---

**it8712f_wdt：**
- `margin`: 
    - Watchdog 边距，单位：秒（默认 60 秒）
- `nowayout`: 
    - 关闭时禁用 Watchdog 重置（默认=内核配置参数）

---

**it87_wdt：**
- `nogameport`: 
    - 禁止激活游戏端口（默认 0）
- `nocir`: 
    - 禁止使用 CIR（解决某些故障设置的问题）；如果系统尽管 Watchdog 守护进程正在运行仍重置，则设置为 1（默认 0）
- `exclusive`: 
    - Watchdog 独占设备打开（默认 1）
- `timeout`: 
    - Watchdog 超时时间，单位：秒（默认 60 秒）
- `testmode`: 
    - Watchdog 测试模式（1 = 不重启，默认 0）
- `nowayout`: 
    - Watchdog 启动后无法停止（默认=内核配置参数）

---

**ixp4xx_wdt：**
- `heartbeat`: 
    - Watchdog 心跳周期，单位：秒（默认 60 秒）
- `nowayout`: 
    - Watchdog 启动后无法停止（默认=内核配置参数）

---

**machzwd：**
- `nowayout`: 
    - Watchdog 启动后无法停止（默认=内核配置参数）
- `action`: 
    - Watchdog 重置后生成：
    0 = 重置（*） 1 = SMI 2 = NMI 3 = SCI

---

**max63xx_wdt：**
- `heartbeat`: 
    - Watchdog 心跳周期，单位：秒（1≤心跳周期≤60，默认 60 秒）
- `nowayout`: 
    - Watchdog 启动后无法停止（默认=内核配置参数）
- `nodelay`: 
    - 强制选择一个没有初始延迟的超时设置（仅适用于 max6373/74，默认 0）

---

**mixcomwd：**
- `nowayout`: 
    - Watchdog 启动后无法停止（默认=内核配置参数）

---

**mpc8xxx_wdt：**
- `timeout`: 
    - Watchdog 超时时间，单位：tick（0<超时时间<65536，默认 65535）
- `reset`: 
    - Watchdog 中断/重置模式（0 = 中断，1 = 重置）
- `nowayout`: 
    - Watchdog 启动后无法停止（默认=内核配置参数）

---

**mv64x60_wdt：**
- `nowayout`: 
    - Watchdog 启动后无法停止（默认=内核配置参数）

---

**ni903x_wdt：**
- `timeout`: 
    - 初始 Watchdog 超时时间，单位：秒（0<超时时间<516，默认 60 秒）
- `nowayout`: 
    - Watchdog 启动后无法停止（默认=内核配置参数）

---

**nic7018_wdt：**
- `timeout`: 
    - 初始 Watchdog 超时时间，单位：秒（0<超时时间<464，默认 80 秒）
- `nowayout`: 
    - Watchdog 启动后无法停止（默认=内核配置参数）

---

**omap_wdt：**
- `timer_margin`: 
    - 初始 Watchdog 超时时间，单位：秒
- `early_enable`: 
    - 在模块插入时启动 Watchdog（默认 0）
- `nowayout`: 
    - Watchdog 启动后无法停止（默认=内核配置参数）

---

**orion_wdt：**
- `heartbeat`: 
    - 初始 Watchdog 心跳周期，单位：秒
- `nowayout`: 
    - Watchdog 启动后无法停止（默认=内核配置参数）

---

**pc87413_wdt：**
- `io`: 
    - pc87413 Watchdog I/O 端口（默认 io）
- `timeout`: 
    - Watchdog 超时时间，单位：分钟（默认 timeout）
这些配置选项描述了不同硬件平台上的看门狗定时器（Watchdog Timer）的特性与设置。下面是翻译后的中文版本：

---

### nowayout:
一旦启动，看门狗将无法停止（默认值=内核配置参数）

---

### pika_wdt:
- **heartbeat:**
  看门狗心跳间隔，单位为秒。（默认 = 15 秒）
- **nowayout:**
  一旦启动，看门狗将无法停止（默认值=内核配置参数）

---

### pnx4008_wdt:
- **heartbeat:**
  看门狗心跳周期，单位为秒，范围从 1 到 60，默认为 19 秒。
- **nowayout:**
  设置为 1 可以确保在设备释放后看门狗仍然运行。

---

### pnx833x_wdt:
- **timeout:**
  看门狗超时时间，单位为 MHz（使用 68MHz 时钟），默认值为 2040000000（即 30 秒）。
- **nowayout:**
  一旦启动，看门狗将无法停止（默认值=内核配置参数）
- **start_enabled:**
  如果设置为 1，则在模块插入时启动看门狗（默认值=1）

---

### pseries-wdt:
- **action:**
  看门狗超时时采取的操作：0（关机），1（重启），2（转储并重启）。（默认值=1）
- **timeout:**
  初始看门狗超时时间，单位为秒。（默认值=60 秒）
- **nowayout:**
  一旦启动，看门狗将无法停止（默认值=内核配置参数）

---

### rc32434_wdt:
- **timeout:**
  看门狗超时值，单位为秒（默认=20 秒）
- **nowayout:**
  一旦启动，看门狗将无法停止（默认值=内核配置参数）

---

### riowd:
- **riowd_timeout:**
  看门狗超时时间，单位为分钟（默认值=1 分钟）

---

### s3c2410_wdt:
- **tmr_margin:**
  看门狗计时器的 tmr_margin，单位为秒。（默认=15 秒）
- **tmr_atboot:**
  如果设置为 1，则在启动时启动看门狗，否则不启动（默认值=0）
- **nowayout:**
  一旦启动，看门狗将无法停止（默认值=内核配置参数）
- **soft_noboot:**
  看门狗动作，设置为 1 忽略重启，设置为 0 则重启
- **debug:**
  看门狗调试，设置大于 1 的值进行调试，（默认值=0）

---

### sa1100_wdt:
- **margin:**
  看门狗 margin，单位为秒（默认=60 秒）

---

### sb_wdog:
- **timeout:**
  看门狗超时时间，单位为微秒（最大/默认值为 8388607 或大约 8.3 秒）

---

### sbc60xxwdt:
- **wdt_stop:**
  SBC60xx WDT “停止” I/O 端口（默认值=0x45）
- **wdt_start:**
  SBC60xx WDT “启动” I/O 端口（默认值=0x443）
- **timeout:**
  看门狗超时时间，单位为秒。（1<=timeout<=3600，默认值=30 秒）
- **nowayout:**
  一旦启动，看门狗将无法停止（默认值=内核配置参数）

---

### sbc7240_wdt:
- **timeout:**
  看门狗超时时间，单位为秒。（1<=timeout<=255，默认值=30 秒）
- **nowayout:**
  关闭设备文件时禁用看门狗

---

### sbc8360:
- **timeout:**
  超时表索引（0-63）（默认值=27（即 60 秒））
- **nowayout:**
  一旦启动，看门狗将无法停止（默认值=内核配置参数）

---

### sbc_epx_c3:
- **nowayout:**
  一旦启动，看门狗将无法停止（默认值=内核配置参数）

---

### sbc_fitpc2_wdt:
- **margin:**
  看门狗 margin，单位为秒（默认=60 秒）
- **nowayout:**
  一旦启动，看门狗将无法停止

---

### sbsa_gwdt:
- **timeout:**
  看门狗超时时间，单位为秒。（默认值=10 秒）
- **action:**
  在第一阶段超时时看门狗的动作，设置为 0 忽略，设置为 1 引发 panic。（默认值=0）
- **nowayout:**
  一旦启动，看门狗将无法停止（默认值=内核配置参数）

---

### sc1200wdt:
- **isapnp:**
  当设置为 0 时禁用驱动程序的 ISA PnP 支持（默认值=1）
- **io:**
  I/O 端口
- **timeout:**
  范围为 0-255 分钟，默认值为 1 分钟
- **nowayout:**
  一旦启动，看门狗将无法停止（默认值=内核配置参数）

---

### sc520_wdt:
- **timeout:**
  看门狗超时时间，单位为秒。（1 <= timeout <= 3600，默认值=30 秒）
- **nowayout:**
  一旦启动，看门狗将无法停止（默认值=内核配置参数）

---

### sch311x_wdt:
- **force_id:**
  覆盖检测到的设备 ID
- **therm_trip:**
  如果设置为 1，则 ThermTrip 触发重置生成器
- **timeout:**
  看门狗超时时间，单位为秒。1<=timeout<=15300，默认值=60 秒
- **nowayout:**
  一旦启动，看门狗将无法停止（默认值=内核配置参数）

---

### scx200_wdt:
- **margin:**
  看门狗 margin，单位为秒
- **nowayout:**
  关闭时禁用看门狗关机

---

### shwdt:
- **clock_division_ratio:**
  时钟分频比。有效范围是从 0x5（1.31 毫秒）到 0x7（5.25 毫秒）。（默认值=7）
- **heartbeat:**
  看门狗心跳，单位为秒。（1 <= heartbeat <= 3600，默认值=30 秒）
- **nowayout:**
  一旦启动，看门狗将无法停止（默认值=内核配置参数）

---

### smsc37b787_wdt:
- **timeout:**
  范围是 1-255 单位，默认值为 60
- **nowayout:**
  一旦启动，看门狗将无法停止（默认值=内核配置参数）

---

### softdog:
- **soft_margin:**
  看门狗 soft_margin，单位为秒（0 < soft_margin < 65536，默认值=60 秒）
- **nowayout:**
  一旦启动，看门狗将无法停止（默认值=内核配置参数）
- **soft_noboot:**
  Softdog 动作，设置为 1 忽略重启，设置为 0 进行重启（默认值=0）

---

### stmp3xxx_wdt:
- **heartbeat:**
  看门狗心跳周期，单位为秒，范围从 1 到 4194304，默认值为 19 秒

---

### tegra_wdt:
- **heartbeat:**
  看门狗心跳，单位为秒。（默认值=120 秒）
- **nowayout:**
  一旦启动，看门狗将无法停止（默认值=内核配置参数）

---

### ts72xx_wdt:
- **timeout:**
  看门狗超时时间，单位为秒。（1 <= timeout <= 8，默认值=8 秒）
- **nowayout:**
  关闭时禁用看门狗关机

---

### twl4030_wdt:
- **nowayout:**
  一旦启动，看门狗将无法停止（默认值=内核配置参数）

---

### txx9wdt:
- **timeout:**
  看门狗超时时间，单位为秒。（0<timeout<N，默认值=60 秒）
- **nowayout:**
  一旦启动，看门狗将无法停止（默认值=内核配置参数）

---

### uniphier_wdt:
- **timeout:**
  看门狗超时时间，单位为 2 的幂次方秒（1 <= timeout <= 128，默认值=64 秒）
- **nowayout:**
  一旦启动，看门狗将无法停止（默认值=内核配置参数）

---

### w83627hf_wdt:
- **wdt_io:**
  w83627hf/thf WDT I/O 端口（默认值=0x2E）
- **timeout:**
  看门狗超时时间，单位为秒。1 <= timeout <= 255，默认值=60 秒
- **nowayout:**
  一旦启动，看门狗将无法停止（默认值=内核配置参数）

---

### w83877f_wdt:
- **timeout:**
  看门狗超时时间，单位为秒。（1<=timeout<=3600，默认值=30 秒）
- **nowayout:**
  一旦启动，看门狗将无法停止（默认值=内核配置参数）

---

### w83977f_wdt:
- **timeout:**
  看门狗超时时间，单位为秒（15..7635），默认值=45 秒
- **testmode:**
  看门狗测试模式（1 = 不重启），默认值=0
- **nowayout:**
  一旦启动，看门狗将无法停止（默认值=内核配置参数）

---

### wafer5823wdt:
- **timeout:**
  看门狗超时时间，单位为秒。1 <= timeout <= 255，默认值=60 秒
- **nowayout:**
  一旦启动，看门狗将无法停止（默认值=内核配置参数）

---

### wdt285:
- **soft_margin:**
  看门狗超时时间，单位为秒（默认值=60 秒）

---

### wdt977:
- **timeout:**
  看门狗超时时间，单位为秒（60..15300，默认值=60 秒）
- **testmode:**
  看门狗测试模式（1 = 不重启），默认值=0
- **nowayout:**
  一旦启动，看门狗将无法停止（默认值=内核配置参数）

---

### wm831x_wdt:
- **nowayout:**
  一旦启动，看门狗将无法停止（默认值=内核配置参数）

---

### wm8350_wdt:
- **nowayout:**
  一旦启动，看门狗将无法停止（默认值=内核配置参数）

---

### sun4v_wdt:
- **timeout_ms:**
  看门狗超时时间，单位为毫秒（1..180000，默认值=60000 毫秒）
- **nowayout:**
  一旦启动，看门狗将无法停止
