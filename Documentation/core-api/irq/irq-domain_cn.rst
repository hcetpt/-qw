==================================================
中断域（irq_domain）的中断编号映射库
==================================================

当前Linux内核的设计使用了一个大型的统一编号空间，其中每个独立的中断源都被分配了不同的编号。当只有一个中断控制器时，这种方式很简单，但在拥有多个中断控制器的系统中，内核必须确保每个中断控制器被分配互不重叠的Linux中断（IRQ）编号。

注册为唯一中断芯片（irqchip）的中断控制器数量呈现出上升的趋势：例如，不同类型的子驱动（如GPIO控制器）通过将其中断处理程序建模为中断芯片来避免重新实现与IRQ核心系统相同的回调机制，即实际上实现了中断控制器的级联。在这种情况下，中断编号与硬件中断编号失去了直接对应关系：在过去，中断编号可以设置为与根中断控制器（即实际向CPU发出中断信号的组件）的硬件中断线相匹配；而现在，这个编号仅仅是一个数字。

因此，我们需要一种机制来区分控制器本地的中断编号（称为硬件中断或hwirq）和Linux中断编号。irq_alloc_desc*() 和 irq_free_desc*() API 提供了中断编号的分配，但它们没有提供从控制器本地IRQ（hwirq）编号到Linux IRQ编号空间的反向映射支持。

中断域（irq_domain）库在 irq_alloc_desc*() API 的基础上增加了 hwirq 和 IRQ 编号之间的映射。相较于中断控制器驱动程序自己编写反向映射方案，创建和管理映射的中断域（irq_domain）更为优选。

irq_domain 还实现了从抽象的 irq_fwspec 结构到 hwirq 编号的转换（目前支持设备树和 ACPI GSI），并且可以轻松扩展以支持其他中断拓扑数据来源。

irq_domain 使用方法
=====================

中断控制器驱动程序通过调用 irq_domain_add_*() 或 irq_domain_create_*() 函数之一来创建并注册一个中断域。成功后，这些函数会返回指向 irq_domain 的指针。调用者必须提供一个 irq_domain_ops 结构给分配器函数。
在大多数情况下，中断域（`irq_domain`）最初为空，没有任何关于硬件中断（`hwirq`）和中断请求（IRQ）编号之间的映射。映射是通过调用`irq_create_mapping()`添加到中断域中的，该函数接受中断域和一个硬件中断编号作为参数。如果还没有为这个硬件中断创建映射，则会分配一个新的Linux `irq_desc`结构，并将其与硬件中断关联起来，然后调用`.map()`回调函数以便驱动程序执行任何所需的硬件设置。

一旦建立了映射，就可以通过多种方法检索或使用它：

- `irq_resolve_mapping()`对于给定的域和硬件中断编号返回指向`irq_desc`结构的指针；如果没有映射，则返回NULL。
- `irq_find_mapping()`对于给定的域和硬件中断编号返回一个Linux中断请求编号；如果没有映射，则返回0。
- `irq_linear_revmap()`现在等同于`irq_find_mapping()`，并且已废弃。
- `generic_handle_domain_irq()`处理由一个域和硬件中断编号描述的中断。

需要注意的是，中断域查找必须在与读取临界区兼容的上下文中进行。

`irq_create_mapping()`函数必须至少被调用一次，在任何对`irq_find_mapping()`的调用之前，否则描述符将不会被分配。

如果驱动程序已经有了Linux中断请求编号或者`irq_data`指针，并且需要知道相关的硬件中断编号（例如，在`irq_chip`回调中），那么可以直接从`irq_data->hwirq`获取。

中断域映射类型
============================

有几种可用的方法可以反向映射硬件中断到Linux中断，每种方法都使用不同的分配函数。应该使用的反向映射类型取决于具体的应用场景。下面描述了每种反向映射类型：

线性映射
------

```
irq_domain_add_linear()
irq_domain_create_linear()
```

线性反向映射维护了一个固定大小的表，索引是硬件中断编号。当硬件中断被映射时，为硬件中断分配一个`irq_desc`，并将中断编号存储在表中。
线性映射适用于最大硬件中断数量是固定的并且相对较小的情况（~< 256）。这种映射的优点是查询中断编号的时间固定，并且只对正在使用的中断分配`irq_desc`。缺点是表的大小必须等于最大的可能硬件中断编号。
`irq_domain_add_linear()`和`irq_domain_create_linear()`功能上是等价的，除了第一个参数不同——前者接受Open Firmware特定的`struct device_node`，而后者接受更通用的抽象`struct fwnode_handle`。
大多数驱动程序应该使用线性映射。
### 树形结构

`irq_domain_add_tree()` 和 `irq_domain_create_tree()`

`irq_domain` 使用一个从硬件中断号（hwirq）到 Linux IRQ 的基数树映射。当一个 hwirq 被映射时，会分配一个 `irq_desc`，并且 hwirq 用作基数树的查找键。
树形映射是一个不错的选择，如果 hwirq 号可能非常大，因为它不需要为最大的 hwirq 分配同样大小的表。缺点是 hwirq 到 IRQ 编号的查找依赖于表中的条目数量。

`irq_domain_add_tree()` 和 `irq_domain_create_tree()` 在功能上等价，除了第一个参数不同 —— 前者接受 Open Firmware 特定的 `struct device_node`，而后者接受更为通用的抽象 `struct fwnode_handle`。

很少有驱动程序需要这种映射。

### 无映射

`irq_domain_add_nomap()`

无映射适用于硬件中可编程的 hwirq 编号。在这种情况下，最好直接在硬件中编程 Linux IRQ 编号，以避免映射的需求。调用 `irq_create_direct_mapping()` 将分配一个 Linux IRQ 编号，并调用 `.map()` 回调函数以便驱动程序将 Linux IRQ 编号编程进硬件。

大多数驱动程序无法使用这种映射，并且现在它受到 `CONFIG_IRQ_DOMAIN_NOMAP` 配置选项的控制。请尽量不要引入新的 API 用户。

### 传统映射

`irq_domain_add_simple()`  
`irq_domain_add_legacy()`  
`irq_domain_create_simple()`  
`irq_domain_create_legacy()`

传统映射适用于已经为 hwirqs 分配了一组 `irq_desc` 的驱动程序。当驱动程序不能立即转换为使用线性映射时使用它。例如，许多嵌入式系统板支持文件使用一组 `#define` 来定义传递给设备注册的 IRQ 编号。在这种情况下，Linux IRQ 编号不能动态分配，应该使用传统映射。

如其名所示，`*_legacy()` 函数已被弃用，仅用于支持古老平台。不应添加新用户。同样地，当使用导致传统行为时，也不应使用 `*_simple()` 函数。

传统映射假定控制器已经为连续范围的 IRQ 编号分配了空间，并且可以通过向 hwirq 编号添加固定偏移来计算 IRQ 编号，反之亦然。缺点是它要求中断控制器管理 IRQ 分配，并且即使未使用的 hwirq 也需要为其分配一个 `irq_desc`。

只有当必须支持固定的 IRQ 映射时，才应使用传统映射。例如，ISA 控制器将使用传统映射来映射 Linux IRQs 0-15，以便现有的 ISA 驱动程序获得正确的 IRQ 编号。
大多数使用传统映射的用户应该使用 `irq_domain_add_simple()` 或 `irq_domain_create_simple()`，这些函数仅在系统提供 IRQ 范围时使用传统域，否则将使用线性域映射。
此调用的语义是这样的：如果指定了 IRQ 范围，则会为其动态分配描述符；如果没有指定范围，则会退回到 `irq_domain_add_linear()` 或 `irq_domain_create_linear()`，这意味着不会分配任何 IRQ 描述符。
简单域的一个典型使用场景是 IRQ 芯片提供者同时支持动态和静态 IRQ 分配的情况。
为了避免出现线性域被使用但没有分配描述符的情况，非常重要的一点是在进行任何 `irq_find_mapping()` 调用之前，使用简单域的驱动程序必须先调用 `irq_create_mapping()`，因为后者实际上适用于静态 IRQ 分配情况。
`irq_domain_add_simple()` 和 `irq_domain_create_simple()` 与 `irq_domain_add_legacy()` 和 `irq_domain_create_legacy()` 在功能上是等价的，只是第一个参数不同 —— 前者接受一个 Open Firmware 特定的 `struct device_node` 结构体，而后者接受一个更通用的抽象 `struct fwnode_handle`。

### 层次 IRQ 域

在某些架构中，从设备向目标 CPU 传递中断可能涉及多个中断控制器。让我们来看一下 x86 平台上典型的中断传递路径：

```
设备 --> IOAPIC -> 中断重映射控制器 -> 本地 APIC -> CPU
```

这里涉及三个中断控制器：

1) IOAPIC 控制器
2) 中断重映射控制器
3) 本地 APIC 控制器

为了支持这种硬件拓扑结构，并使软件架构与硬件架构相匹配，为每个中断控制器构建了一个 `irq_domain` 数据结构，并将这些 `irq_domain` 组织成层次结构。当构建 `irq_domain` 层次结构时，靠近设备的 `irq_domain` 是子节点，靠近 CPU 的 `irq_domain` 是父节点。因此，对于上述示例，会构建如下层次结构：

```
CPU 向量 irq_domain（管理 CPU 向量的根 irq_domain）
    ^
    |
中断重映射 irq_domain（管理中断重映射条目）
    ^
    |
IOAPIC irq_domain（管理 IOAPIC 传递条目/引脚）
```

使用层次 IRQ 域有四大主要接口：

1) `irq_domain_alloc_irqs()`：分配 IRQ 描述符和与中断控制器相关的资源以传递这些中断
2) `irq_domain_free_irqs()`：释放与这些中断相关的 IRQ 描述符和中断控制器资源
3) `irq_domain_activate_irq()`：激活中断控制器硬件以传递中断
翻译如下：

4) `irq_domain_deactivate_irq()`：停用中断控制器硬件以停止发送中断。

为了支持层次化的 `irq_domain`，需要进行以下更改：

1) 在 `struct irq_domain` 中新增一个字段 `'parent'`；它用于维护 `irq_domain` 的层次结构信息。
2) 在 `struct irq_data` 中新增一个字段 `'parent_data'`；它用于构建与层次化 `irq_domain` 匹配的层次化 `irq_data`。`irq_data` 用于存储指向 `irq_domain` 的指针和硬件中断编号。
3) 在 `struct irq_domain_ops` 中新增回调函数来支持层次化的 `irq_domain` 操作。

在支持层次化的 `irq_domain` 和层次化的 `irq_data` 的基础上，为每个中断控制器构建了一个 `irq_domain` 结构，并为与 IRQ 关联的每个 `irq_domain` 分配了一个 `irq_data` 结构。现在我们可以更进一步地支持层次化的 `irq_chip`。也就是说，在层次结构中，每个 `irq_data` 都关联有一个 `irq_chip`。子 `irq_chip` 可能独立实现所需的操作，或与其父 `irq_chip` 协同工作来实现。

通过层次化的 `irq_chip`，中断控制器驱动程序只需处理由其自身管理的硬件，并在需要时向其父 `irq_chip` 请求服务。因此，可以实现更加清晰的软件架构。

为了让中断控制器驱动程序支持层次化的 `irq_domain`，需要做到：

1) 实现 `irq_domain_ops.alloc` 和 `irq_domain_ops.free`。
2) 可选地实现 `irq_domain_ops.activate` 和 `irq_domain_ops.deactivate`。
3) 可选地实现一个 `irq_chip` 来管理中断控制器硬件。
4) 不需要实现 `irq_domain_ops.map` 和 `irq_domain_ops.unmap`，因为在层次化的 `irq_domain` 中不会使用它们。

层次化的 `irq_domain` 并非特定于 x86 架构，并且广泛用于支持其他架构，如 ARM、ARM64 等。
调试
=====

通过打开CONFIG_GENERIC_IRQ_DEBUGFS配置，大多数IRQ子系统的内部机制都会在调试文件系统（debugfs）中暴露出来。
