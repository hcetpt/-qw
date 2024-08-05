MFP 配置用于 PXA2xx/PXA3xx 处理器
==============================================

			艾瑞克·苗 <eric.miao@marvell.com>

MFP 代表多功能引脚，它是 PXA3xx 及后续 PXA 系列处理器上的引脚复用逻辑。本文档描述了现有的 MFP API，以及板卡/平台驱动程序作者如何利用它。

基本概念
=============

与 PXA25x 和 PXA27x 上的 GPIO 复用功能设置不同，从 PXA3xx 开始引入了一种新的 MFP 机制，将所有的引脚复用功能完全从 GPIO 控制器中移出。除了引脚复用配置之外，MFP 还控制每个引脚的低功耗状态、驱动强度、上拉/下拉以及事件检测。下面是 MFP 逻辑与 SoC 其他外设内部连接的示意图：

```
+--------+
|        |--(GPIO19)--+
|  GPIO  |            |
|        |--(GPIO...) |
+--------+            |
                       |       +---------+
 +--------+            +------>|         |
 |  PWM2  |--(PWM_OUT)-------->|   MFP   |
 +--------+            +------>|         |-------> 到外部 PAD
                       | +---->|         |
 +--------+            | | +-->|         |
 |  SSP2  |---(TXD)----+ | |   +---------+
 +--------+              | |
                         | |
 +--------+              | |
 | Keypad |--(MKOUT4)----+ |
 +--------+                |
                           |
 +--------+                |
 |  UART2 |---(TXD)--------+
 +--------+
```

**注意**：外部 PAD 被命名为 MFP_PIN_GPIO19，并不一定意味着它专用于 GPIO19，这只是表明该引脚可以由 GPIO 控制器的 GPIO19 内部路由。

为了更好地理解从 PXA25x/PXA27x 的 GPIO 复用功能到这种新 MFP 机制的变化，这里有几点关键内容：

1. PXA3xx 上的 GPIO 控制器现在是一个专用控制器，与其他内部控制器（如 PWM、SSP 和 UART）相同，具有 128 个内部信号，这些信号可以通过一个或多个 MFP 路由到外部（例如，GPIO<0> 可以通过 MFP_PIN_GPIO0 以及 MFP_PIN_GPIO0_2 路由，参见 arch/arm/mach-pxa/mfp-pxa300.h）。

2. GPIO 控制器上的复用功能配置已被删除，剩下的功能仅限于 GPIO 特有的功能：
    - GPIO 信号电平控制
    - GPIO 方向控制
    - GPIO 电平变化检测

3. 每个引脚的低功耗状态现在由 MFP 控制，这意味着 PXA2xx 上的 PGSRx 寄存器在 PXA3xx 上已经没有作用了。

4. 唤醒检测现在由 MFP 控制，PWER 不再控制来自 GPIO 的唤醒，根据睡眠状态的不同，ADxER（如 pxa3xx-regs.h 中定义的）控制 MFP 的唤醒。

**注意**：随着 MFP 和 GPIO 的清晰分离，我们通常说的 GPIO<xx> 指的是 GPIO 信号，而 MFP<xxx> 或者 pin xxx 指的是物理 PAD（或者球）。

MFP API 使用
=============

对于编写板卡代码的人员，这里有一些指导原则：

1. 在你的 <board>.c 文件中包含以下头文件之一：

   - `#include "mfp-pxa25x.h"`
   - `#include "mfp-pxa27x.h"`
   - `#include "mfp-pxa300.h"`
   - `#include "mfp-pxa320.h"`
   - `#include "mfp-pxa930.h"`

   **注意**：在你的 <board>.c 文件中只包含一个文件，这取决于所使用的处理器，因为这些文件中的引脚配置定义可能会发生冲突（即相同的名字，在不同的处理器上有不同的含义和设置）。例如，对于支持 PXA300/PXA310 和 PXA320 的 Zylonite 平台，引入了两个单独的文件：zylonite_pxa300.c 和 zylonite_pxa320.c（除了处理 MFP 配置差异外，它们还处理这两种组合之间的其他差异）。

**注意**：PXA300 和 PXA310 在引脚配置上几乎相同（PXA310 支持一些额外的功能），因此这种差异实际上在一个 mfp-pxa300.h 文件中就涵盖了。

2. 准备一个用于初始引脚配置的数组，例如：

   ```c
   static unsigned long mainstone_pin_config[] __initdata = {
      /* 芯片选择 */
      GPIO15_nCS_1,

      /* LCD - 16bpp 主动 TFT */
      GPIOxx_TFT_LCD_16BPP,
      GPIO16_PWM0_OUT,  /* 背光 */

      /* MMC */
      GPIO32_MMC_CLK,
      GPIO112_MMC_CMD,
      GPIO92_MMC_DAT_0,
      GPIO109_MMC_DAT_1,
      GPIO110_MMC_DAT_2,
      GPIO111_MMC_DAT_3,

      ..
      /* GPIO */
      GPIO1_GPIO | WAKEUP_ON_EDGE_BOTH,
   };
   ```

   a) 一旦引脚配置传递给 pxa{2xx,3xx}_mfp_config() 并写入实际寄存器，它们就没有用了，可以丢弃。添加 `__initdata` 有助于在这里节省一些额外的字节。
b) 当一个组件只有一个可能的引脚配置时，可以使用一些简化的定义，例如在PXA25x和PXA27x处理器上使用的`GPIOxx_TFT_LCD_16BPP`。

c) 如果根据板卡设计，一个引脚可以通过配置使其从低功耗状态唤醒系统，则可以将其与以下任一选项进行“或”操作：

   - `WAKEUP_ON_EDGE_BOTH`
   - `WAKEUP_ON_EDGE_RISE`
   - `WAKEUP_ON_EDGE_FALL`
   - `WAKEUP_ON_LEVEL_HIGH` - 特别用于启用键盘GPIO

以此表示该引脚具有唤醒系统的能力，并指出是在哪个边缘。然而，这并不意味着该引脚一定会唤醒系统，只有当通过`set_irq_wake()`函数使用相应的GPIO中断（`GPIO_IRQ(xx)`或`gpio_to_irq()`）并最终调用`gpio_set_wake()`以设置实际寄存器时，它才会真正唤醒系统。

d) 尽管PXA3xx MFP支持每个引脚上的边沿检测，但内部逻辑仅在ADxER寄存器中的特定位被设置时唤醒系统，这些位可以很好地映射到对应的外设，因此可以使用`set_irq_wake()`函数与外设中断一起调用来启用唤醒功能。

PXA3xx的MFP
=============

PXA3xx中的每一个外部I/O端口（除了特殊用途的端口）都有一个与之关联的MFP逻辑，并由一个MFP寄存器(MFPR)控制。MFPR具有以下位定义（针对PXA300/PXA310/PXA320）：

```
31                        16 15 14 13 12 11 10  9  8  7  6  5  4  3  2  1  0
 +-------------------------+--+--+--+--+--+--+--+--+--+--+--+--+--+--+--+--+
 |         RESERVED        |PS|PU|PD|  DRIVE |SS|SD|SO|EC|EF|ER|--| AF_SEL |
 +-------------------------+--+--+--+--+--+--+--+--+--+--+--+--+--+--+--+--+
 
位 3:   保留
位 4:   EDGE_RISE_EN - 启用此引脚上的上升沿检测
位 5:   EDGE_FALL_EN - 启用此引脚上的下降沿检测
位 6:   EDGE_CLEAR   - 禁用此引脚上的边沿检测
位 7:   SLEEP_OE_N   - 在低功耗模式下启用输出
位 8:   SLEEP_DATA   - 在低功耗模式下引脚的输出数据
位 9:   SLEEP_SEL    - 选择低功耗模式信号的控制
位 13:  PULLDOWN_EN  - 启用此引脚上的内部下拉电阻
位 14:  PULLUP_EN    - 启用此引脚上的内部上拉电阻
位 15:  PULL_SEL     - 拉动状态由选定的备用功能（0）或由PULL{UP,DOWN}_EN位（1）控制

位 0 - 2: AF_SEL - 备用功能选择，有8种可能性，从0-7
位 10-12: DRIVE  - 驱动强度和斜率
           0b000 - 快速 1mA
           0b001 - 快速 2mA
           0b002 - 快速 3mA
           0b003 - 快速 4mA
           0b004 - 慢速 6mA
           0b005 - 快速 6mA
           0b006 - 慢速 10mA
           0b007 - 快速 10mA
```

PXA2xx/PXA3xx的MFP设计
============================

由于PXA2xx和PXA3xx之间引脚复用处理的不同，引入了一个统一的MFP API来覆盖这两个系列的处理器。
这个设计的基本思想是为所有可能的引脚配置引入定义，这些定义与处理器和平台无关，然后通过实际调用API将这些定义转换为寄存器设置并使之生效。
涉及的文件
--------------

  - `arch/arm/mach-pxa/include/mach/mfp.h`

    包括：
      1. 统一的引脚定义 - 所有可配置引脚的枚举常量
      2. 可能的MFP配置中处理器无关的位定义

  - `arch/arm/mach-pxa/mfp-pxa3xx.h`

    包括PXA3xx特定的MFPR寄存器位定义和PXA3xx通用的引脚配置

  - `arch/arm/mach-pxa/mfp-pxa2xx.h`

    包括PXA2xx特定的定义和PXA25x/PXA27x通用的引脚配置

  - `arch/arm/mach-pxa/mfp-pxa25x.h`, `arch/arm/mach-pxa/mfp-pxa27x.h`, `arch/arm/mach-pxa/mfp-pxa300.h`, `arch/arm/mach-pxa/mfp-pxa320.h`, `arch/arm/mach-pxa/mfp-pxa930.h`

    包括特定处理器的定义

  - `arch/arm/mach-pxa/mfp-pxa3xx.c`, `arch/arm/mach-pxa/mfp-pxa2xx.c`

    实现引脚配置对实际处理器生效
引脚配置
-----------------

以下是来自mfp.h的注释（请参阅实际源代码获取最新信息）：

```
/*
 * 可能的MFP配置由一个32位整数表示
 *
 * 位  0.. 9 - MFP 引脚编号（最多1024个引脚）
 * 位 10..12 - 备用功能选择
 * 位 13..15 - 驱动强度
 * 位 16..18 - 低功耗模式状态
 * 位 19..20 - 低功耗模式边沿检测
 * 位 21..22 - 运行模式拉态
 *
 * 为了便于定义，提供了以下宏
 *
 * MFP_CFG_DEFAULT - 默认MFP配置值，其中
 * 		  备用功能 = 0，
 * 		  驱动强度 = 快速 3mA (MFP_DS03X)
 * 		  低功耗模式 = 默认
 * 		  边沿检测 = 无
 *
 * MFP_CFG	- 具有备用功能的默认MFPR值
 * MFP_CFG_DRV	- 具有备用功能和引脚驱动强度的默认MFPR值
 * MFP_CFG_LPM	- 具有备用功能和低功耗模式的默认MFPR值
 * MFP_CFG_X	- 具有备用功能、引脚驱动强度和低功耗模式的默认MFPR值
 */
```

引脚配置的例子如下：

```
#define GPIO94_SSP3_RXD		MFP_CFG_X(GPIO94, AF1, DS08X, FLOAT)
```

这意味着GPIO94可以配置为SSP3_RXD，备用功能选择为1，驱动强度为0b101，在低功耗模式下的状态为浮空。
**注意**：这是该引脚配置为SSP3_RXD的默认设置，虽然可以在板级代码中稍作修改，但这不建议这样做，因为这个默认设置通常是精心编码的，应该在大多数情况下都能工作。
寄存器设置
-----------------

在PXA3xx上为引脚配置设置寄存器实际上是相当直接的，大多数位可以直接转换为MFPR值，以更简单的方式实现。计算两组MFPR值：运行时的值和低功耗模式的值，以允许不同的设置。
从通用引脚配置到PXA2xx实际寄存器设置的转换较为复杂：涉及多个寄存器，包括GAFRx, GPDRx, PGSRx, PWER, PKWR, PFER和PRER。请参阅mfp-pxa2xx.c了解如何进行转换。
您没有提供需要翻译的文本。请提供需要翻译成中文的英文或其他语言的文本。
