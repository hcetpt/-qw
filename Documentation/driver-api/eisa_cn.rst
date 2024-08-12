EISA 总线支持
================

:作者: Marc Zyngier <maz@wild-wind.fr.eu.org>

本文档汇总了一些关于将 EISA 驱动程序移植到新的 EISA/sysfs API 的随机笔记。
从版本 2.5.59 开始，EISA 总线几乎获得了与其他更主流总线（如 PCI 或 USB）相同的地位。这得益于 sysfs，它定义了一套相当不错的抽象来管理总线、设备和驱动程序。

尽管新 API 使用起来相当简单，但将现有驱动程序转换为新的基础设施并非易事（主要是因为检测代码通常也用于探测 ISA 卡）。此外，大多数 EISA 驱动程序都是最古老的 Linux 驱动程序之一，因此可想而知，这些年来已经积聚了一些陈旧的代码。
EISA 基础设施由三个部分组成：

- 总线代码实现了大部分通用代码。它在所有运行 EISA 代码的架构中共享。它实现了总线探测（检测总线上可用的 EISA 卡）、分配 I/O 资源、允许通过 sysfs 进行高级命名，并为驱动程序提供了注册接口。
- 总线根驱动程序实现了总线硬件与通用总线代码之间的粘合层。它负责发现实现该总线的设备，并将其设置好以便稍后由总线代码进行探测。这可能从像在 x86 上保留一个 I/O 区域这样简单的操作，到像 hppa EISA 代码那样更为复杂的操作。这是为了使 EISA 在一个新的平台上运行而需要实现的部分。
- 驱动程序向总线提供其管理的设备列表，并实现必要的回调以在被指示时探测和释放设备。
下面的每个函数/结构都位于 `<linux/eisa.h>` 中，该文件严重依赖于 `<linux/device.h>`。

总线根驱动程序
===============

```
int eisa_root_register(struct eisa_root_device *root);
```

`eisa_root_register` 函数用于声明一个设备作为 EISA 总线的根。`eisa_root_device` 结构体包含对该设备的引用以及一些用于探测目的的参数。

```
struct eisa_root_device {
    struct device   *dev;        /* 指向桥接设备的指针 */
    struct resource *res;
    unsigned long    bus_base_addr;
    int              slots;      /* 最大槽号 */
    int              force_probe; /* 即使没有槽 0 也要进行探测 */
    u64              dma_mask;   /* 来自桥接设备 */
    int              bus_nr;     /* 由 eisa_root_register 设置 */
    struct resource  eisa_root_res;
};
```

== 参数解释 ======================================================
node          用于 `eisa_root_register` 内部目的
dev           根设备指针
res           根设备 I/O 资源
bus_base_addr 此总线上槽 0 的地址
slots         探测的最大槽号
force_probe   即使槽 0 为空（没有 EISA 主板）也要进行探测
dma_mask      默认 DMA 掩码。通常是桥接设备的 dma_mask
bus_nr        唯一的总线 ID，由 `eisa_root_register` 设置
== 参数解释 ======================================================

驱动程序
======

```
int eisa_driver_register(struct eisa_driver *edrv);
void eisa_driver_unregister(struct eisa_driver *edrv);
```

清楚吗？

```
struct eisa_device_id {
    char sig[EISA_SIG_LEN];
    unsigned long driver_data;
};

struct eisa_driver {
    const struct eisa_device_id *id_table;
    struct device_driver         driver;
};
```

== 成员解释 ====================================================
id_table      一个由 NULL 终止的 EISA 标识符字符串数组，后面跟一个空字符串。每个字符串可以可选地与一个驱动程序相关的值配对（`driver_data`）
driver        一个通用驱动程序，如在 `Documentation/driver-api/driver-model/driver.rst` 中所述。只有 `.name`、`.probe` 和 `.remove` 成员是必需的
== 成员解释 ====================================================
一个例子是 3c59x 驱动程序:

```c
// 定义了与特定设备ID关联的偏移量
static struct eisa_device_id vortex_eisa_ids[] = {
	{ "TCM5920", EISA_3C592_OFFSET },
	{ "TCM5970", EISA_3C597_OFFSET },
	{ "" }
};

// 定义了EISA驱动结构体，包含设备ID表以及驱动名称、探针函数和移除函数
static struct eisa_driver vortex_eisa_driver = {
	.id_table = vortex_eisa_ids,
	.driver   = {
		.name    = "3c59x",
		.probe   = vortex_eisa_probe,
		.remove  = vortex_eisa_remove
	}
};
```

设备
====

sysfs框架在发现或移除设备时会调用`.probe`和`.remove`函数（注意：只有当驱动作为模块构建时才会调用`.remove`函数）。这两个函数都会收到指向`struct device`结构体的指针，该结构体封装在一个`struct eisa_device`中，定义如下:

```c
struct eisa_device {
    struct eisa_device_id id; // 从设备读取的EISA ID。id.driver_data由匹配的驱动程序EISA ID设置
    int                   slot; // 设备被检测到所在的插槽号
    int                   state; // 表示设备状态的一组标志。当前的标志包括EISA_CONFIG_ENABLED和EISA_CONFIG_FORCED
    unsigned long         base_addr; // 基地址
    struct resource       res[EISA_MAX_RESOURCES]; // 分配给此设备的四个256字节I/O区域
    u64                   dma_mask; // 从父设备设置的DMA掩码
    struct device         dev; // 通用设备（参见Documentation/driver-api/driver-model/device.rst）
};
```

你可以使用`to_eisa_device`宏从`struct device`获取`struct eisa_device`。

杂项
=====

```c
void eisa_set_drvdata (struct eisa_device *edev, void *data);
// 将数据存储到设备的driver_data区域
```

```c
void *eisa_get_drvdata (struct eisa_device *edev);
// 获取之前存储在设备的driver_data区域的指针
```

```c
int eisa_get_region_index (void *addr);
// 返回给定地址所属的区域编号（0 <= x < EISA_MAX_RESOURCES）
```

内核参数
========

`eisa_bus.enable_dev`
- 以逗号分隔的插槽列表，即使固件将卡设置为禁用，也要启用这些插槽。驱动程序必须能够在这些条件下正确初始化设备。

`eisa_bus.disable_dev`
- 以逗号分隔的插槽列表，即使固件将卡设置为启用，也要禁用这些插槽。驱动程序不会被调用来处理这个设备。
### `virtual_root.force_probe`
强制探测代码即使在找不到符合EISA标准的主板（插槽0上没有任何设备）时也要探测EISA插槽。默认值为0（不强制），当设置了`CONFIG_EISA_VLB_PRIMING`时设置为1（强制探测）。

### 随笔
将EISA驱动程序转换为新API主要涉及*删除*代码（因为探测现在是在核心EISA代码中完成）。不幸的是，大多数驱动程序在其ISA和EISA之间共享探测例程。在移除EISA代码时必须特别小心，以免其他总线受到这些“外科手术”的影响。
从`eisa_driver_register`返回时，**不得**期望检测到任何EISA设备，因为总线很可能尚未被探测。实际上，这种情况通常会发生（总线根驱动程序通常在启动过程较晚的时候才会激活）
不幸的是，大多数驱动程序自行进行探测，并期望在退出探测例程时已经探索了整个机器。
例如，将您喜欢的EISA SCSI卡切换到“热插拔”模式是“正确的事情”。

### 感谢
我想感谢以下人士的帮助：
- Xavier Benigni借给我一台美妙的Alpha Jensen，
- James Bottomley、Jeff Garzik帮助我将这些内容加入内核，
- Andries Brouwer贡献了许多EISA标识符，
- Catrin Jones容忍家中有太多机器。
