========================
通用时钟框架
========================

:作者: Mike Turquette <mturquette@ti.com>

本文档旨在解释通用时钟框架的细节，以及如何将一个平台迁移到此框架上。它目前还不是对include/linux/clk.h中时钟API的一个详细说明，但也许有一天会包含这些信息。
介绍和接口划分
=====================

通用时钟框架是一个用于控制当今各种设备上可用的时钟节点的接口。这可能以时钟门控、速率调整、多路复用或其他操作的形式出现。该框架是通过CONFIG_COMMON_CLK选项启用的。
接口本身分为两个部分，每个部分都屏蔽了对方的细节。首先是统一的struct clk定义，它统一了通常在各种平台上重复实现的框架级会计和基础设施。第二是在drivers/clk/clk.c中定义的clk.h API的通用实现。最后还有struct clk_ops，其操作由clk API实现调用。
接口的另一半由与struct clk_ops注册的硬件特定回调以及为表示特定时钟所需的相应硬件特定结构组成。在本文档的其余部分中，对struct clk_ops中的任何回调（如.enable或.set_rate）的引用都意味着是该代码的硬件特定实现。同样，对struct clk_foo的引用作为对假设的"foo"硬件实现的硬件特定部分的一种方便的简称。
将这两个接口的半部分连接在一起的是struct clk_hw，它在struct clk_foo中定义并在struct clk_core中指针指向。这使得在通用时钟接口的两个独立部分之间进行轻松导航成为可能。
通用数据结构和API
======================

下面是drivers/clk/clk.c中的通用struct clk_core定义，为了简洁进行了修改:: 

    struct clk_core {
        const char		*name;
        const struct clk_ops	*ops;
        struct clk_hw		*hw;
        struct module		*owner;
        struct clk_core		*parent;
        const char		**parent_names;
        struct clk_core		**parents;
        u8			num_parents;
        u8			new_parent_index;
        ..
    };

上述成员构成了时钟树拓扑的核心。时钟API本身定义了几种面向驱动程序的功能，这些功能在struct clk上运行。该API在include/linux/clk.h中进行了记录。
使用通用struct clk_core的平台和设备利用struct clk_core中的struct clk_ops指针来执行在clk-provider.h中定义的操作的硬件特定部分:: 

    struct clk_ops {
        int		(*prepare)(struct clk_hw *hw);
        void		(*unprepare)(struct clk_hw *hw);
        int		(*is_prepared)(struct clk_hw *hw);
        void		(*unprepare_unused)(struct clk_hw *hw);
        int		(*enable)(struct clk_hw *hw);
        void		(*disable)(struct clk_hw *hw);
        int		(*is_enabled)(struct clk_hw *hw);
        void		(*disable_unused)(struct clk_hw *hw);
        unsigned long	(*recalc_rate)(struct clk_hw *hw,
                        unsigned long parent_rate);
        long		(*round_rate)(struct clk_hw *hw,
                        unsigned long rate,
                        unsigned long *parent_rate);
        int		(*determine_rate)(struct clk_hw *hw,
                                  struct clk_rate_request *req);
        int		(*set_parent)(struct clk_hw *hw, u8 index);
        u8		(*get_parent)(struct clk_hw *hw);
        int		(*set_rate)(struct clk_hw *hw,
                        unsigned long rate,
                        unsigned long parent_rate);
        int		(*set_rate_and_parent)(struct clk_hw *hw,
                        unsigned long rate,
                        unsigned long parent_rate,
                        u8 index);
        unsigned long	(*recalc_accuracy)(struct clk_hw *hw,
                        unsigned long parent_accuracy);
        int		(*get_phase)(struct clk_hw *hw);
        int		(*set_phase)(struct clk_hw *hw, int degrees);
        void		(*init)(struct clk_hw *hw);
        void		(*debug_init)(struct clk_hw *hw,
                              struct dentry *dentry);
    };

硬件时钟实现
==================

通用struct clk_core的强大之处在于它的.ops和.hw指针，它们抽象了struct clk与硬件特定部分之间的细节，反之亦然。为了说明这一点，请考虑drivers/clk/clk-gate.c中的简单门控时钟实现:: 

    struct clk_gate {
        struct clk_hw	hw;
        void __iomem    *reg;
        u8              bit_idx;
        ..
    };

struct clk_gate包含了struct clk_hw hw以及关于哪个寄存器和位控制此时钟门控的硬件特定知识。
这里不需要有关时钟拓扑或会计的信息，例如enable_count或notifier_count，所有这些都是由通用框架代码和struct clk_core处理的。
让我们通过驱动代码来启用这个时钟（clk）:

```c
struct clk *clk;
clk = clk_get(NULL, "my_gateable_clk");

clk_prepare(clk);
clk_enable(clk);
```

`clk_enable`的调用图非常简单:

```c
clk_enable(clk);
    clk->ops->enable(clk->hw);
        [解析为...]
            clk_gate_enable(hw);
                [解析为使用to_clk_gate(hw)的struct clk_gate]
                    clk_gate_set_bit(gate);
```

`clk_gate_set_bit`的定义如下:

```c
static void clk_gate_set_bit(struct clk_gate *gate)
{
    u32 reg;

    reg = __raw_readl(gate->reg);
    reg |= BIT(gate->bit_idx);
    writel(reg, gate->reg);
}
```

请注意，`to_clk_gate`被定义为:

```c
#define to_clk_gate(_hw) container_of(_hw, struct clk_gate, hw)
```

这种抽象模式被用于每种时钟硬件表示。

### 支持自己的时钟硬件

在实现对新型时钟的支持时，只需包含以下头文件:

```c
#include <linux/clk-provider.h>
```

为了构建平台的时钟硬件结构，您必须定义以下内容:

```c
struct clk_foo {
    struct clk_hw hw;
    ... // 硬件特定数据放在这里
};
```

要利用您的数据，您需要支持对该时钟有效的操作:

```c
struct clk_ops clk_foo_ops = {
    .enable       = &clk_foo_enable,
    .disable      = &clk_foo_disable,
};
```

使用`container_of`实现上述函数:

```c
#define to_clk_foo(_hw) container_of(_hw, struct clk_foo, hw)

int clk_foo_enable(struct clk_hw *hw)
{
    struct clk_foo *foo;

    foo = to_clk_foo(hw);

    ... // 在foo上执行魔术操作
    return 0;
};
```

下面是一个矩阵，详细说明了根据该时钟的硬件能力哪些`clk_ops`是必需的。标记为"y"的单元格意味着是必需的，标记为"n"的单元格意味着包括该回调无效或不必要。空白单元格是可选的或者必须逐个案例进行评估。
```
表: 时钟硬件特性

+----------------+------+-------------+---------------+-------------+------+
|                | gate | change rate | single parent | multiplexer | root |
+================+======+=============+===============+=============+======+
|.prepare        |      |             |               |             |      |
+----------------+------+-------------+---------------+-------------+------+
|.unprepare      |      |             |               |             |      |
+----------------+------+-------------+---------------+-------------+------+
+----------------+------+-------------+---------------+-------------+------+
|.enable         | y    |             |               |             |      |
+----------------+------+-------------+---------------+-------------+------+
|.disable        | y    |             |               |             |      |
+----------------+------+-------------+---------------+-------------+------+
|.is_enabled     | y    |             |               |             |      |
+----------------+------+-------------+---------------+-------------+------+
+----------------+------+-------------+---------------+-------------+------+
|.recalc_rate    |      | y           |               |             |      |
+----------------+------+-------------+---------------+-------------+------+
|.round_rate     |      | y [1]_      |               |             |      |
+----------------+------+-------------+---------------+-------------+------+
|.determine_rate |      | y [1]_      |               |             |      |
+----------------+------+-------------+---------------+-------------+------+
|.set_rate       |      | y           |               |             |      |
+----------------+------+-------------+---------------+-------------+------+
+----------------+------+-------------+---------------+-------------+------+
|.set_parent     |      |             | n             | y           | n    |
+----------------+------+-------------+---------------+-------------+------+
|.get_parent     |      |             | n             | y           | n    |
+----------------+------+-------------+---------------+-------------+------+
+----------------+------+-------------+---------------+-------------+------+
|.recalc_accuracy|      |             |               |             |      |
+----------------+------+-------------+---------------+-------------+------+
+----------------+------+-------------+---------------+-------------+------+
|.init           |      |             |               |             |      |
+----------------+------+-------------+---------------+-------------+------+

[1] round_rate 或 determine_rate 其中之一是必需的
```

最后，在运行时使用特定于硬件的注册函数注册您的时钟。此函数仅填充`struct clk_foo`的数据，然后通过调用`clk_register(...)`将通用的`struct clk`参数传递给框架。

请参阅`drivers/clk/clk-*.c`中的基本时钟类型示例。

### 禁用未使用的时钟的时钟门控

在开发过程中，有时能够绕过默认禁用未使用时钟的功能是非常有用的。例如，如果驱动程序没有正确地启用时钟但依赖于引导加载程序将其打开，绕过禁用意味着在问题解决之前驱动程序仍将保持功能。

您可以通过以下启动参数查看已禁用的时钟:

```
tp_printk trace_event=clk:clk_disable
```

要绕过这种禁用，可以在内核启动参数中包含"clk_ignore_unused"。

### 锁定

公共时钟框架使用两个全局锁：准备锁和启用锁。
启用锁是一个自旋锁，并在调用`.enable`、`.disable`操作期间持有。因此这些操作不允许睡眠，而且对`clk_enable()`、`clk_disable()` API函数的调用允许在原子上下文中进行。
对于 `clk_is_enabled()` API，它也被设计为可以在原子上下文中使用。然而，在核心中持有启用锁实际上并没有太多意义，除非你想在持有该锁的情况下对启用状态信息做其他操作。否则，检查一个时钟是否被启用只是一个对启用状态的一次性读取，这个状态可能在函数返回后立即发生变化，因为锁已经被释放了。因此，使用此API的用户需要处理同步状态读取与其用途之间的关系，以确保在此期间启用状态不会改变。

准备锁是一个互斥锁，并且在所有其他操作调用过程中都被持有。所有这些操作都允许休眠，并且对应的API函数不允许在原子上下文中调用。
这实际上从锁定的角度将操作分为两组。
驱动程序不需要手动保护一组操作间共享资源的安全性，无论这些资源是否由多个时钟共享。但是，对于两组操作之间共享资源的访问，则需要由驱动程序进行保护。例如，一个同时控制时钟速率和时钟启用/禁用状态的寄存器就是这样的资源。

时钟框架是可重入的，也就是说，允许驱动程序在其实现时钟操作的过程中调用时钟框架函数。例如，这可能会导致在一个时钟的 `.set_rate` 操作中调用另一个时钟的 `.set_rate` 操作。这种情况必须在驱动程序实现中考虑，但通常情况下，代码流程是由驱动程序控制的。

需要注意的是，当外部代码需要访问用于时钟操作的资源时，也必须考虑锁定问题。这个问题被认为是超出本文档范围的。
