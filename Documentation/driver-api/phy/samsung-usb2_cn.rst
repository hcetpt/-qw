### 三星USB 2.0 PHY适配层

#### 1. 描述

三星系统级芯片(SoC)中的USB 2.0 PHY模块架构在许多SoC中是相似的。尽管存在这些相似性，但很难创建一个适用于所有这些PHY控制器的单一驱动程序。通常，差异很小，并且体现在PHY寄存器的特定位上。在一些罕见的情况下，寄存器写入顺序或PHY启动过程需要改变。这个适配层是在拥有单独驱动程序和拥有一个支持多种特殊情况的单一驱动程序之间的折衷方案。

#### 2. 文件描述

- **phy-samsung-usb2.c**
  这是适配层的主要文件。此文件包含探测函数并为通用PHY框架提供了两个回调函数。这两个回调用于打开和关闭PHY。它们执行所有版本的PHY模块都需要完成的共同工作。根据所选的SoC，它们会执行特定于SoC的回调。特定的SoC版本通过选择适当的兼容字符串来选定。此外，此文件还包含了针对特定SoC的`struct of_device_id`定义。
  
- **phy-samsung-usb2.h**
  这是包含文件。它声明了本驱动程序使用的结构体。此外，它还应该包含描述特定SoC的结构体的外部声明。

#### 3. 支持的SoC

为了支持新的SoC，应向`drivers/phy`目录添加一个新的文件。每个SoC的配置都存储在`struct samsung_usb2_phy_config`的一个实例中：

```c
struct samsung_usb2_phy_config {
    const struct samsung_usb2_common_phy *phys;
    int (*rate_to_clk)(unsigned long, u32 *);
    unsigned int num_phys;
    bool has_mode_switch;
};
```

`num_phys`表示由驱动程序处理的PHY数量。`*phys`是一个数组，包含每个PHY的配置。`has_mode_switch`属性是一个布尔标志，用于确定SoC是否在一对引脚上具有USB主机和设备功能。如果是这样，则必须修改一个特殊寄存器以改变这些引脚在USB设备或主机模块之间的内部路由。

例如，Exynos 4210的配置如下：

```c
const struct samsung_usb2_phy_config exynos4210_usb2_phy_config = {
    .has_mode_switch = 0,
    .num_phys = EXYNOS4210_NUM_PHYS,
    .phys = exynos4210_phys,
    .rate_to_clk = exynos4210_rate_to_clk,
};
```

- `int (*rate_to_clk)(unsigned long, u32 *)`

  `rate_to_clk`回调用于将用作PHY模块参考时钟的时钟速率转换为应在硬件寄存器中写入的值。

Exynos 4210的`phys`配置数组如下：

```c
static const struct samsung_usb2_common_phy exynos4210_phys[] = {
    {
        .label = "device",
        .id = EXYNOS4210_DEVICE,
        .power_on = exynos4210_power_on,
        .power_off = exynos4210_power_off,
    },
    {
        .label = "host",
        .id = EXYNOS4210_HOST,
        .power_on = exynos4210_power_on,
        .power_off = exynos4210_power_off,
    },
    {
        .label = "hsic0",
        .id = EXYNOS4210_HSIC0,
        .power_on = exynos4210_power_on,
        .power_off = exynos4210_power_off,
    },
    {
        .label = "hsic1",
        .id = EXYNOS4210_HSIC1,
        .power_on = exynos4210_power_on,
        .power_off = exynos4210_power_off,
    },
    {},
};
```

- `int (*power_on)(struct samsung_usb2_phy_instance *);`
  `int (*power_off)(struct samsung_usb2_phy_instance *);`

  这两个回调用于通过修改相应的寄存器来打开和关闭PHY。

最后一步是在`phy-samsung-usb2.c`文件中添加适当的兼容值。对于Exynos 4210，在`struct of_device_id samsung_usb2_phy_of_match[]`数组中添加了以下行：

```c
#ifdef CONFIG_PHY_EXYNOS4210_USB2
{
    .compatible = "samsung,exynos4210-usb2-phy",
    .data = &exynos4210_usb2_phy_config,
},
#endif
```

为了进一步增强驱动程序的灵活性，Kconfig文件允许在编译的驱动程序中包含对选定SoC的支持。Exynos 4210的Kconfig条目如下：

```c
config PHY_EXYNOS4210_USB2
bool "Support for Exynos 4210"
depends on PHY_SAMSUNG_USB2
depends on CPU_EXYNOS4210
help
  启用Exynos 4210的USB PHY支持。此选项要求启用三星USB 2.0 PHY驱动程序，并意味着对该特定SoC的支持被编译到驱动程序中。对于Exynos 4210，有四个PHY可用 - 设备、主机、HSCI0和HSCI1
```

新创建的支持新SoC的文件还需要添加到Makefile中。对于Exynos 4210，添加的行如下：

```makefile
obj-$(CONFIG_PHY_EXYNOS4210_USB2) += phy-exynos4210-usb2.o
```

完成这些步骤后，新SoC的支持应该就准备好了。
