.. SPDX 许可证标识符: GPL-2.0

.. _废弃：

================================================================================
已废弃的接口、语言特性、属性和约定
================================================================================

在一个理想的世界里，可以在一个开发周期内将所有已废弃API的实例转换为新API，并完全移除旧API。然而，由于内核规模庞大、维护者层级结构以及时间因素，一次性完成这些转换并不总是可行的。这意味着在移除旧API的同时，新的实例可能会悄悄进入内核，使得移除API的工作量不断增加。为了教育开发者了解哪些内容已被废弃及原因，创建了此列表，以供提出在内核中包含已废弃内容时参考。

__deprecated
------------
虽然此属性在视觉上标记了一个接口为废弃，但`它不再在构建过程中生成警告 <https://git.kernel.org/linus/771c035372a036f83353eef46dbb829780330234>`_，因为内核的一个长期目标是无警告构建，而没有人真正采取措施移除这些废弃接口。尽管在头文件中使用`__deprecated`来注释旧API是不错的做法，但这并不是完整的解决方案。此类接口必须从内核中完全移除，或者添加到此文件中，以阻止他人在未来使用它们。

BUG() 和 BUG_ON()
------------------
请改用 WARN() 和 WARN_ON()，并尽可能优雅地处理“不可能”的错误条件。虽然BUG()系列API最初设计用于作为“不可能情况”的断言并安全地终止内核线程，但事实证明它们风险太大。（例如，“锁需要以什么顺序释放？各种状态是否已经恢复？”）非常常见的是，使用BUG()会导致系统变得不稳定或完全崩溃，从而无法调试甚至获取有效的崩溃报告。Linus对此有`非常强烈的看法 <https://lore.kernel.org/lkml/CA+55aFy6jNLsywVYdGp83AMrXBo_P-pkjkphPGrO=82SPKCpLQ@mail.gmail.com/>`_。

请注意，WARN()系列仅应用于“预期不可达”的情况。如果您想警告“可达但不希望”的情况，请使用pr_warn()系列函数。系统所有者可能设置了*panic_on_warn* sysctl，以确保他们的系统在面对“不可达”条件时不会继续运行。（例如，参见像`这个提交 <https://git.kernel.org/linus/d4689846881d160a4d12a514e991a740bcb5d65a>`_。）

分配器参数中的显式算术
--------------------------------------------
动态大小计算（特别是乘法）不应在内存分配器（或类似功能）的参数中执行，因为存在溢出的风险。这可能导致值循环并分配比调用者期望的小得多的空间。使用这些分配可能导致堆内存线性溢出和其他异常行为。（唯一例外是编译器可以警告可能溢出的字面值。然而，在这种情况下，建议的做法是重构代码，如下所述，以避免显式算术。）

例如，不要使用 `count * size` 作为参数，如：

    foo = kmalloc(count * size, GFP_KERNEL);

相反，应使用分配器的双因子形式：

    foo = kmalloc_array(count, size, GFP_KERNEL);

具体来说，kmalloc() 可以替换为 kmalloc_array()，kzalloc() 可以替换为 kcalloc()。
如果没有双因子形式可用，则应使用饱和溢出辅助函数：

    bar = dma_alloc_coherent(dev, array_size(count, size), &dma, GFP_KERNEL);

另一个常见的需要避免的情况是在结构体尾部带有其他结构体数组时计算结构体大小，如：

    header = kzalloc(sizeof(*header) + count * sizeof(*header->item), GFP_KERNEL);

相反，使用辅助函数：

    header = kzalloc(struct_size(header, item, count), GFP_KERNEL);

.. note:: 如果您在一个包含零长度或单元素数组作为尾部数组成员的结构体上使用struct_size()，请重构此类数组用法并切换为`灵活数组成员 <#zero-length-and-one-element-arrays>`_。

对于其他计算，请组合使用 size_mul()、size_add() 和 size_sub() 辅助函数。例如，在以下情况下：

    foo = krealloc(current_size + chunk_size * (count - 3), GFP_KERNEL);

相反，使用辅助函数：

    foo = krealloc(size_add(current_size,
            size_mul(chunk_size,
                    size_sub(count, 3))), GFP_KERNEL);

更多信息，请参阅 array3_size() 和 flex_array_size()，以及相关的 check_mul_overflow()、check_add_overflow()、check_sub_overflow() 和 check_shl_overflow() 系列函数。

simple_strtol()、simple_strtoll()、simple_strtoul()、simple_strtoull()
----------------------------------------------------------------------
simple_strtol()、simple_strtoll()、simple_strtoul() 和 simple_strtoull() 函数明确忽略溢出，这可能导致调用者产生意外结果。相应的 kstrtol()、kstrtoll()、kstrtoul() 和 kstrtoull() 函数通常是正确的替代品，不过请注意，这些函数要求字符串以 NUL 或换行符终止。

strcpy()
--------
strcpy() 不对目标缓冲区进行边界检查。这可能导致缓冲区末尾之外的线性溢出，导致各种异常行为。尽管 `CONFIG_FORTIFY_SOURCE=y` 和各种编译器标志有助于降低使用该函数的风险，但没有充分的理由新增对此函数的使用。安全的替代方案是 strscpy()，但在任何使用 strcpy() 返回值的情况下需谨慎，因为 strscpy() 不返回指向目标的指针，而是返回复制的非 NUL 字节数（截断时返回负 errno）。

strncpy() 在 NUL 终止字符串上的使用
-----------------------------------
strncpy() 的使用不能保证目标缓冲区会被 NUL 终止。这可能导致因缺少终止符而引发的各种线性读取溢出和其他异常行为。此外，如果源内容短于目标缓冲区大小，它还会 NUL 填充目标缓冲区，这可能是对仅使用 NUL 终止字符串的调用者的不必要的性能损失。

当目标需要被 NUL 终止时，替代方案是 strscpy()，但在任何使用 strncpy() 返回值的情况下需谨慎，因为 strscpy() 不返回指向目标的指针，而是返回复制的非 NUL 字节数（截断时返回负 errno）。任何仍需要 NUL 填充的情况应改为使用 strscpy_pad()。
### 使用非NUL终止字符串的情况

如果调用者使用的是非NUL终止的字符串，应使用`strtomem()`函数，并且目的地应标记为`__nonstring`属性（参见[链接](https://gcc.gnu.org/onlinedocs/gcc/Common-Variable-Attributes.html)），以避免未来的编译器警告。对于仍然需要NUL填充的情况，可以使用`strtomem_pad()`。

### `strlcpy()`

`strlcpy()`会首先读取整个源缓冲区（因为返回值旨在匹配`strlen()`的结果）。这可能会超过目标大小限制。这不仅效率低下，而且如果源字符串未NUL终止，则可能导致线性读取溢出。安全的替代方法是使用`strscpy()`，但在任何使用`strlcpy()`返回值的情况下需特别注意，因为`strscpy()`在截断时会返回负的`errno`值。

### `%p`格式化说明符

传统上，在格式化字符串中使用`%p`会导致dmesg、proc、sysfs等中的常规地址暴露缺陷。为了避免这些漏洞被利用，内核中所有`%p`的使用都将以哈希值形式打印，使其无法用于地址解析。不应向内核中添加新的`%p`用法。对于文本地址，使用`%pS`可能更好，因为它会生成更有用的符号名称。对于几乎所有其他情况，根本不要添加`%p`。

以下是Linus当前的[指导](https://lore.kernel.org/lkml/CA+55aFwQEd_d40g4mUCSsVRZzrFPUJt74vc6PPpb675hYNXcKw@mail.gmail.com/)：

- 如果哈希后的`%p`值毫无意义，请问自己这个指针本身是否重要。也许应该完全删除？
- 如果你真的认为真实的指针值很重要，为什么某些系统状态或用户权限级别被认为是“特殊的”？如果你认为你可以通过评论和提交日志充分证明这一点，经得起Linus的审查，那么你可以使用`%px`，同时确保有合理的权限。

如果你正在调试某个问题，而`%p`哈希导致了问题，你可以暂时使用调试标志`no_hash_pointers`启动。

### 可变长度数组（VLA）

使用栈上的VLA会产生比静态大小的栈数组更差的机器代码。尽管这些非平凡的[性能问题](https://git.kernel.org/linus/02361bc77888)本身就足以消除VLA，但它们也是安全风险。堆栈数组的动态增长可能会超出栈段中的剩余内存。这可能导致崩溃，可能覆盖栈末尾的敏感内容（当没有启用`CONFIG_THREAD_INFO_IN_TASK=y`时），或者覆盖栈附近的内存（当没有启用`CONFIG_VMAP_STACK=y`时）。

### 隐式switch case穿透

C语言允许在缺少`break`语句的情况下从一个case穿透到下一个case。然而，这会在代码中引入模糊性，因为并不总是清楚缺少的`break`是故意的还是一个错误。例如，仅从代码中看，并不清楚`STATE_ONE`是否故意穿透到`STATE_TWO`：

```c
switch (value) {
case STATE_ONE:
    do_something();
case STATE_TWO:
    do_other();
    break;
default:
    WARN("unknown state");
}
```

由于缺少`break`语句导致了大量的缺陷（参见[CWE定义484](https://cwe.mitre.org/data/definitions/484.html)），我们不再允许隐式穿透。为了标识故意穿透的情况，我们采用了一个伪关键字宏`fallthrough`，它扩展为GCC的扩展`__attribute__((__fallthrough__))`（参见[链接](https://gcc.gnu.org/onlinedocs/gcc/Statement-Attributes.html)）。

所有switch/case块必须以以下之一结束：

* `break;`
* `fallthrough;`
* `continue;`
* `goto <label>;`
* `return [expression];`

### 零长度和单元素数组

内核中经常需要一种方法来声明具有动态大小的尾部元素的结构。内核代码应始终使用“灵活数组成员”（参见[链接](https://en.wikipedia.org/wiki/Flexible_array_member)）来处理这些情况。旧的单元素或零长度数组的风格不应再使用。

在旧的C代码中，动态大小的尾部元素通过在结构末尾指定一个单元素数组实现：

```c
struct something {
    size_t count;
    struct foo items[1];
};
```

这导致了通过`sizeof()`进行脆弱的大小计算（需要减去单个尾部元素的大小以获得正确的“头部”大小）。引入了一个GNU C扩展，允许使用零长度数组，以避免这类大小问题：

```c
struct something {
    size_t count;
    struct foo items[0];
};
```

但这带来了其他问题，并且没有解决这两种风格共有的某些问题，比如无法检测这种数组是否意外地不在结构末尾使用（这可以直接发生，也可以在结构嵌套、结构中的结构等情况中发生）。

C99引入了“灵活数组成员”，该成员的数组声明不包含数字大小：

```c
struct something {
    size_t count;
    struct foo items[];
};
```

这是内核期望声明动态大小尾部元素的方式。它允许编译器在灵活数组不是位于结构末尾时生成错误，有助于防止某些类型的未定义行为（参见[链接](https://git.kernel.org/linus/76497732932f15e7323dc805e8ea8dc11bb587cf)）错误被无意引入代码库。它还允许编译器正确分析数组大小（通过`sizeof()`、`CONFIG_FORTIFY_SOURCE`和`CONFIG_UBSAN_BOUNDS`）。例如，没有机制警告我们以下对零长度数组应用`sizeof()`运算符总是结果为零：

```c
struct something {
    size_t count;
    struct foo items[0];
};

struct something *instance;

instance = kmalloc(struct_size(instance, items, count), GFP_KERNEL);
instance->count = count;

size = sizeof(instance->items) * instance->count;
memcpy(instance->items, source, size);
```

在上述代码的最后一行，`size`结果为零，而人们可能认为它代表最近分配给尾部数组`items`的动态内存的总字节数。这里有两个例子：[链接1](https://git.kernel.org/linus/f2cd32a443da694ac4e28fbf4ac6f9d5cc63a539)，[链接2](https://git.kernel.org/linus/ab91c2a89f86be2898cee208d492816ec238b2cf)。

相反，灵活数组成员具有不完整类型，因此不能对其应用`sizeof()`运算符（参见[链接](https://gcc.gnu.org/onlinedocs/gcc/Zero-Length.html)），因此任何此类运算符的误用将在构建时立即被发现。
关于单元素数组，必须明确意识到这样的数组至少占用一个该类型对象的空间（参考 `<https://gcc.gnu.org/onlinedocs/gcc/Zero-Length.html>`_），因此它们会影响包含结构体的大小。每当人们想要计算包含此类数组的结构体动态内存分配的总大小时，这很容易出错：

```c
struct something {
        size_t count;
        struct foo items[1];
};

struct something *instance;

instance = kmalloc(struct_size(instance, items, count - 1), GFP_KERNEL);
instance->count = count;

size = sizeof(instance->items) * instance->count;
memcpy(instance->items, source, size);
```

在上面的例子中，我们必须记得在使用 `struct_size()` 辅助函数时计算 `count - 1`，否则我们会无意中为多一个 `items` 对象分配内存。实现这一功能最干净且不易出错的方法是通过使用“可变长度数组成员”，并结合 `struct_size()` 和 `flex_array_size()` 辅助函数：

```c
struct something {
        size_t count;
        struct foo items[];
};

struct something *instance;

instance = kmalloc(struct_size(instance, items, count), GFP_KERNEL);
instance->count = count;

memcpy(instance->items, source, flex_array_size(instance, items, instance->count));
```

有两特殊情况需要使用 `DECLARE_FLEX_ARRAY()` 辅助函数（注意在 UAPI 头文件中它被命名为 `__DECLARE_FLEX_ARRAY()`）。这些情况包括：可变长度数组成员单独位于一个结构体中或作为联合的一部分。C99 规范禁止这两种情况，但这并非出于技术原因（从现有用法以及 `DECLARE_FLEX_ARRAY()` 的解决方法可以看出）。例如，要转换如下结构体：

```c
struct something {
        ...
union {
        struct type1 one[0];
        struct type2 two[0];
};
};
```

必须使用辅助函数：

```c
struct something {
        ...
union {
        DECLARE_FLEX_ARRAY(struct type1, one);
        DECLARE_FLEX_ARRAY(struct type2, two);
};
};
```
