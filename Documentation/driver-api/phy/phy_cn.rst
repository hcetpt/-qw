PHY 子系统
=============

:作者: Kishon Vijay Abraham I <kishon@ti.com>

本文档解释了通用 PHY 框架及其提供的 API，以及如何使用这些内容。

简介
============

*PHY* 是物理层的缩写。它用于将设备连接到物理介质上，例如，USB 控制器有一个 PHY 来提供诸如序列化、反序列化、编码、解码等功能，并负责获得所需的数据传输速率。需要注意的是，有些 USB 控制器将 PHY 功能嵌入其中，而其他控制器则使用外部 PHY。使用 PHY 的其他外设包括无线局域网（Wireless LAN）、以太网（Ethernet）、串行 ATA（SATA）等。
创建此框架的目的在于将分散在 Linux 内核中的 PHY 驱动集中到 `drivers/phy` 目录下，以增加代码复用性并提高代码可维护性。
该框架仅对使用外部 PHY（PHY 功能未嵌入控制器内）的设备有用。

注册/注销 PHY 提供者
==========================================

PHY 提供者是指实现一个或多个 PHY 实例的实体。
对于简单的情况，即 PHY 提供者只实现一个 PHY 实例时，框架提供了其自己的 `of_xlate` 实现，即 `of_phy_simple_xlate`。如果 PHY 提供者实现了多个实例，则应提供自己的 `of_xlate` 实现。`of_xlate` 只用于基于设备树（device tree）引导的情况。

```
#define of_phy_provider_register(dev, xlate)    \
        __of_phy_provider_register((dev), NULL, THIS_MODULE, (xlate))

#define devm_of_phy_provider_register(dev, xlate)       \
        __devm_of_phy_provider_register((dev), NULL, THIS_MODULE, (xlate))
```

`of_phy_provider_register` 和 `devm_of_phy_provider_register` 宏可用于注册 PHY 提供者，它们接受设备和 `of_xlate` 作为参数。对于基于设备树引导的情况，所有 PHY 提供者都应使用上述两个宏之一来注册 PHY 提供者。

通常与 PHY 提供者相关的设备树节点会包含一组子节点，每个子节点代表一个单独的 PHY。某些绑定可能会在额外的层次中嵌套子节点以提供上下文和扩展性，在这种情况下可以使用低级别的 `of_phy_provider_register_full()` 和 `devm_of_phy_provider_register_full()` 宏来覆盖包含子节点的节点。

```
#define of_phy_provider_register_full(dev, children, xlate) \
        __of_phy_provider_register(dev, children, THIS_MODULE, xlate)

#define devm_of_phy_provider_register_full(dev, children, xlate) \
        __devm_of_phy_provider_register_full(dev, children, \
                                             THIS_MODULE, xlate)

void devm_of_phy_provider_unregister(struct device *dev, \
                                     struct phy_provider *phy_provider);
void of_phy_provider_unregister(struct phy_provider *phy_provider);
```

`devm_of_phy_provider_unregister` 和 `of_phy_provider_unregister` 可用于注销 PHY。

创建 PHY
================

为了使其他外围控制器能够使用 PHY，PHY 驱动需要创建 PHY。PHY 框架提供了两个 API 来创建 PHY：
PHY驱动程序可以使用上面的两个API之一来创建PHY，通过传递设备指针和PHY操作集（phy_ops）。
`phy_ops`是一组用于执行PHY操作（如初始化、退出、上电和断电）的功能指针。
为了引用私有数据（在phy_ops中），PHY提供者驱动可以在创建PHY后使用`phy_set_drvdata()`设置私有数据，并在phy_ops中使用`phy_get_drvdata()`获取这些私有数据。

获取PHY引用
==============================

在控制器能够利用PHY之前，它必须获取一个PHY的引用。此框架提供了以下API来获取PHY的引用：

```c
struct phy *phy_get(struct device *dev, const char *string);
struct phy *devm_phy_get(struct device *dev, const char *string);
struct phy *devm_phy_optional_get(struct device *dev, const char *string);
struct phy *devm_of_phy_get(struct device *dev, struct device_node *np, const char *con_id);
struct phy *devm_of_phy_optional_get(struct device *dev, struct device_node *np, const char *con_id);
struct phy *devm_of_phy_get_by_index(struct device *dev, struct device_node *np, int index);
```

`phy_get`, `devm_phy_get` 和 `devm_phy_optional_get` 可以用来获取PHY。
对于设备树引导的情况，字符串参数应包含设备树数据中指定的PHY名称；对于非设备树引导，则应包含PHY的标签。
`devm_phy_get` 关联了设备与PHY，在成功获取PHY时使用`devres`。当驱动卸载时，会在`devres`数据上调用释放函数并释放`devres`数据。
当PHY是可选的时候，应该使用`_optional_get`变体。这些函数永远不会返回`-ENODEV`，而是在找不到PHY时返回NULL。
一些通用驱动，如ehci，可能会使用多个PHY。在这种情况下，可以使用`devm_of_phy_get` 或 `devm_of_phy_get_by_index` 根据名称或索引来获取PHY引用。
需要注意的是，NULL是一个有效的PHY引用。对NULL PHY的所有PHY消费者调用都会变成空操作（NOP）。也就是说，对NULL PHY应用的释放调用、`phy_init()` 和 `phy_exit()` 调用以及 `phy_power_on()` 和 `phy_power_off()` 调用都是NOP。NULL PHY在处理可选PHY设备时非常有用。

API调用顺序
==================

一般的调用顺序应该是：

```c
[devm_][of_]phy_get()
phy_init()
phy_power_on()
[phy_set_mode[_ext]()]
..
```
phy_power_off()  
phy_exit()  
[[of_]phy_put()]

一些物理层(PHY)驱动程序可能没有实现:c:func:`phy_init` 或 :c:func:`phy_power_on`，
但是控制器应该始终调用这些函数以确保与其他PHY的兼容性。某些PHY可能需要调用 :c:func:`phy_set_mode <phy_set_mode_ext>`，而其他PHY可能会使用默认模式（通常通过设备树或其他固件配置）。为了保持兼容性，如果您知道自己将要使用的模式，则应始终调用此函数。一般来说，此函数应在 :c:func:`phy_power_on` 调用之后进行，尽管有些PHY驱动程序可能允许在任何时间点调用它。

释放对PHY的引用
==================

当控制器不再需要PHY时，必须释放通过上述API获得的PHY引用。PHY框架提供了两个API来释放对PHY的引用：
```
void phy_put(struct phy *phy);
void devm_phy_put(struct device *dev, struct phy *phy);
```

这两个API都用于释放对PHY的引用，而devm_phy_put会销毁与该PHY相关的devres。

销毁PHY
==================

当创建了PHY的驱动程序被卸载时，应该使用以下两个API之一来销毁创建的PHY：
```
void phy_destroy(struct phy *phy);
void devm_phy_destroy(struct device *dev, struct phy *phy);
```

这两个API都会销毁PHY，而devm_phy_destroy会销毁与该PHY相关的devres。

电源管理运行时
==================

这个子系统支持电源管理运行时。因此，在创建PHY时，会调用由这个子系统创建的PHY设备的pm_runtime_enable，并且在销毁PHY时，会调用pm_runtime_disable。请注意，这个子系统创建的PHY设备将是调用phy_create的设备（PHY提供者设备）的子设备。
因此，phy_device由这个子系统创建的pm_runtime_get_sync将会调用PHY提供者设备的pm_runtime_get_sync，这是由于父级-子级关系的原因。
还应该注意的是，phy_power_on和phy_power_off分别执行phy_pm_runtime_get_sync和phy_pm_runtime_put。
有一些导出的API如phy_pm_runtime_get、phy_pm_runtime_get_sync、phy_pm_runtime_put、phy_pm_runtime_put_sync、phy_pm_runtime_allow和phy_pm_runtime_forbid来进行电源管理操作。

PHY映射
==================

为了在没有设备树帮助的情况下获取对PHY的引用，框架提供了一些查找功能，可以将其与clkdev进行比较，允许clk结构绑定到设备。可以在运行时进行查找，当已经存在指向struct phy的句柄时。

框架提供了以下API来注册和注销这些查找：
```
int phy_create_lookup(struct phy *phy, const char *con_id, const char *dev_id);
void phy_remove_lookup(struct phy *phy, const char *con_id, const char *dev_id);
```

设备树绑定
==================

关于PHY设备树绑定的文档可以在以下位置找到:
Documentation/devicetree/bindings/phy/phy-bindings.txt
