### 已弃用的接口、语言特性、属性和约定

在一个理想的世界里，可以在一个开发周期内将所有已弃用API的实例转换为新的API，并完全移除旧的API。然而，由于内核的庞大、维护层次结构以及时间因素，一次性进行这些转换往往是不可行的。这意味着在移除旧API的同时可能会有新的实例悄悄地加入内核，这只会增加移除API的工作量。为了教育开发者关于哪些已经被弃用以及为什么被弃用，创建了这份列表作为参考，当提出使用已弃用的内容时可以指向这个列表。

__deprecated
------------
虽然这个属性在视觉上标记了一个接口为已弃用，但它`不再在构建过程中产生警告<https://git.kernel.org/linus/771c035372a036f83353eef46dbb829780330234>`，因为内核的一个长期目标是无警告构建，而实际上没有人真正做任何事情来移除这些已弃用的接口。虽然在头文件中使用`__deprecated`来标记旧API是不错的做法，但这并不是完整的解决方案。这样的接口必须要么从内核中完全移除，要么添加到此文件中以阻止未来其他人使用它们。

BUG() 和 BUG_ON()
------------------
请改用 WARN() 和 WARN_ON()，并尽可能优雅地处理“不可能”的错误条件。虽然BUG()-系列API最初设计用于充当“不可能情况”断言，并且“安全”地终止一个内核线程，但事实证明它们太冒险了（例如，“锁需要按照什么顺序释放？各种状态是否已被恢复？”）。非常常见的是，使用BUG()会导致系统不稳定或完全崩溃，这使得调试甚至获得有效的崩溃报告都变得不可能。Linus对此有`非常强烈的意见<https://lore.kernel.org/lkml/CA+55aFy6jNLsywVYdGp83AMrXBo_P-pkjkphPGrO=82SPKCpLQ@mail.gmail.com/>`。
请注意，WARN()-系列仅应用于“预期不可达”的情况。如果你想警告“可达但不希望发生”的情况，请使用pr_warn()-系列函数。系统所有者可能已经设置了*panic_on_warn* sysctl，以确保他们的系统在面对“不可达”条件时不会继续运行。（例如，参见像`这个提交<https://git.kernel.org/linus/d4689846881d160a4d12a514e991a740bcb5d65a>`这样的提交。）

分配器参数中的显式编码算术
----------------------------
动态大小计算（特别是乘法）不应该在内存分配器（或类似）函数的参数中执行，因为存在溢出的风险。这可能导致值回绕，分配的内存比调用方期望的小。使用这些分配可能导致堆内存线性溢出和其他不当行为。（一个例外是编译器可以警告可能溢出的字面值。然而，在这种情况下，首选的方法是重构代码如下所示，以避免显式编码算术。）

例如，不要使用`count * size`作为参数，如：

    foo = kmalloc(count * size, GFP_KERNEL);

相反，应该使用分配器的双因子形式：

    foo = kmalloc_array(count, size, GFP_KERNEL);

具体来说，kmalloc()可以用kmalloc_array()替换，而kzalloc()可以用kcalloc()替换。
如果没有双因子形式可用，则应使用饱和溢出帮助函数：

    bar = dma_alloc_coherent(dev, array_size(count, size), &dma, GFP_KERNEL);

另一个常见的需要避免的情况是在结构体末尾包含其他结构体数组时计算结构体的大小，如：

    header = kzalloc(sizeof(*header) + count * sizeof(*header->item), GFP_KERNEL);

相反，应使用帮助函数：

    header = kzalloc(struct_size(header, item, count), GFP_KERNEL);

**注释：**如果你正在对包含零长度或单元素数组作为尾部数组成员的结构体使用struct_size()，请重构此类数组的使用，并切换到一个`灵活数组成员<#zero-length-and-one-element-arrays>`。
对于其他计算，请组合使用size_mul()、size_add()和size_sub()帮助函数。例如，在以下情况中：

    foo = krealloc(current_size + chunk_size * (count - 3), GFP_KERNEL);

相反，应使用帮助函数：

    foo = krealloc(size_add(current_size,
                            size_mul(chunk_size,
                                     size_sub(count, 3))), GFP_KERNEL);

更多信息，请参阅array3_size()和flex_array_size()，以及相关的check_mul_overflow()、check_add_overflow()、check_sub_overflow()和check_shl_overflow()函数族。

simple_strtol(), simple_strtoll(), simple_strtoul(), simple_strtoull()
----------------------------------------------------------------------
simple_strtol(), simple_strtoll(), simple_strtoul(), 和 simple_strtoull() 函数明确忽略溢出，这可能会导致调用方出现意外结果。相应的kstrtol(), kstrtoll(), kstrtoul(), 和 kstrtoull() 函数通常是正确的替代品，不过请注意，这些函数要求字符串以NUL或换行符终止。

strcpy()
--------
strcpy() 不会对目标缓冲区进行边界检查。这可能会导致超出缓冲区末端的线性溢出，从而引发各种不当行为。虽然`CONFIG_FORTIFY_SOURCE=y`和各种编译器标志有助于降低使用此函数的风险，但没有充分的理由添加新的使用情况。安全的替代方案是strscpy()，但在任何使用strcpy()返回值的地方需要注意，因为strscpy()不返回指向目的地的指针，而是返回非NUL字节的复制数量（或截断时的负errno值）。

strncpy() 在NUL终止的字符串上
-------------------------------
使用strncpy()并不能保证目标缓冲区会被NUL终止。这可能会导致因缺少终止符而导致的各种线性读取溢出和其他不当行为。它还会在源内容短于目标缓冲区大小时对目标缓冲区进行NUL填充，这对于只使用NUL终止字符串的调用者而言可能是不必要的性能开销。

当目标缓冲区需要NUL终止时，替代方案是strscpy()，但在任何使用strncpy()返回值的地方需要注意，因为strscpy()不返回指向目的地的指针，而是返回非NUL字节的复制数量（或截断时的负errno值）。如果仍然需要NUL填充的情况，请改用strscpy_pad()。
如果调用者使用非空字符终止的字符串，应使用 `strtomem()`，并且目标应标记为 `__nonstring <https://gcc.gnu.org/onlinedocs/gcc/Common-Variable-Attributes.html>`_ 属性以避免未来的编译器警告。对于仍然需要空字符填充的情况，可以使用 `strtomem_pad()`。

`strlcpy()`
-----------
`strlcpy()` 首先读取整个源缓冲区（因为返回值旨在与 `strlen()` 的结果相匹配）。这种读取可能会超出目标大小限制。这不仅效率低下，而且如果源字符串没有空字符终止，则可能导致线性读溢出。安全的替代方法是使用 `strscpy()`，但需要注意任何依赖 `strlcpy()` 返回值的情况，因为当 `strscpy()` 截断时会返回负的 `errno` 值。

`%p` 格式化指定符
-------------------
传统上，在格式字符串中使用 `%p` 会导致 dmesg、proc、sysfs 等中的常规地址暴露漏洞。为了避免这些漏洞被利用，内核中所有的 `%p` 使用都打印为哈希值，使其无法用于地址解析。不应向内核添加新的 `%p` 使用。对于文本地址，使用 `%pS` 可能更好，因为它会产生更有用的符号名称。对于几乎所有其他情况，最好根本不添加 `%p`。

引用 Linus 当前的 `指导 <https://lore.kernel.org/lkml/CA+55aFwQEd_d40g4mUCSsVRZzrFPUJt74vc6PPpb675hYNXcKw@mail.gmail.com/>`_：

- 如果哈希后的 `%p` 值毫无意义，问问自己指针本身是否重要。也许它应该完全被移除？
- 如果你真的认为真实的指针值很重要，那么为什么某些系统状态或用户权限级别被认为是“特殊”的？如果你认为你能足够好地在注释和提交日志中证明这一点，经得起 Linus 的审视，也许你可以使用 `%px`，同时确保你有合理的权限。

如果你正在调试某个因 `%p` 哈希导致问题的情况，你可以暂时使用调试标志 `no_hash_pointers <https://git.kernel.org/linus/5ead723a20e0447bc7db33dc3070b420e5f80aa6>`_ 启动。

可变长度数组 (VLAs)
---------------------
使用栈上的 VLAs 生成的机器代码远不如静态大小的栈数组高效。虽然这些复杂的 `性能问题 <https://git.kernel.org/linus/02361bc77888>`_ 已经足以消除 VLAs，但它们也是一个安全隐患。栈数组的动态增长可能会超过栈段中剩余的内存。这可能会导致崩溃，可能覆盖栈末尾的敏感内容（当未启用 `CONFIG_THREAD_INFO_IN_TASK=y` 编译时），或者覆盖栈附近的内容（当未启用 `CONFIG_VMAP_STACK=y` 编译时）。

隐式 switch case 下滑
----------------------
C 语言允许在 case 结尾缺少 “break” 语句的情况下从一个 case 下滑到下一个 case。然而，这样做会在代码中引入模糊性，因为并不总是清楚缺少的 break 是故意的还是一个错误。例如，并不能仅从代码中看出 `STATE_ONE` 是否有意下滑到 `STATE_TWO`：

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

由于缺少 "break" 语句而产生的大量缺陷 `<https://cwe.mitre.org/data/definitions/484.html>`_，我们不再允许隐式下滑。为了识别故意下滑的情况，我们采用了伪关键字宏 "fallthrough"，它扩展为 gcc 的扩展 `__attribute__((__fallthrough__)) <https://gcc.gnu.org/onlinedocs/gcc/Statement-Attributes.html>`_（当 C17/C18 的 `[[fallthrough]]` 语法更普遍地被 C 编译器、静态分析器和 IDE 支持时，我们可以将该宏伪关键字切换为使用该语法）。

所有 switch/case 块必须以以下之一结束：

* break;
* fallthrough;
* continue;
* goto <label>;
* return [expression];

零长度和单元素数组
-------------------
内核中经常需要提供一种方式来声明具有动态大小尾随元素的结构。内核代码应始终使用 "灵活数组成员" `<https://en.wikipedia.org/wiki/Flexible_array_member>`_ 来处理这些情况。旧式的单元素或零长度数组不应再使用。

在较老的 C 代码中，通过在结构体的末尾指定一个单元素数组来实现动态大小的尾随元素：

```c
struct something {
        size_t count;
        struct foo items[1];
};
```

这导致了通过 sizeof() 进行的脆弱大小计算（需要减去单个尾随元素的大小以获得“头部”的正确大小）。GNU C 引入了一个扩展来允许使用零长度数组，以避免这类大小问题：

```c
struct something {
        size_t count;
        struct foo items[0];
};
```

但这带来了其他问题，并且没有解决两种风格共有的某些问题，比如当这种数组意外地不位于结构体末尾时无法检测到（这可能直接发生，也可能发生在联合体、结构体内的结构体等情况下）。

C99 引入了“灵活数组成员”，其数组声明中完全没有数值大小：

```c
struct something {
        size_t count;
        struct foo items[];
};
```

这是内核期望声明动态大小尾随元素的方式。它允许编译器在灵活数组不是结构体最后一个成员时生成错误，有助于防止某些类型的 `未定义行为 <https://git.kernel.org/linus/76497732932f15e7323dc805e8ea8dc11bb587cf>`_ 虫子不经意间被引入代码库。它还允许编译器正确分析数组大小（通过 sizeof()、`CONFIG_FORTIFY_SOURCE` 和 `CONFIG_UBSAN_BOUNDS`）。例如，没有机制警告我们对零长度数组应用 sizeof() 操作符总是结果为零：

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

在上面代码的最后一行，`size` 结果为 `零`，而人们可能以为它表示最近为尾随数组 `items` 动态分配的内存的总字节数。以下是该问题的几个示例：`链接 1 <https://git.kernel.org/linus/f2cd32a443da694ac4e28fbf4ac6f9d5cc63a539>`_、`链接 2 <https://git.kernel.org/linus/ab91c2a89f86be2898cee208d492816ec238b2cf>`_。

相反，`灵活数组成员具有不完整类型，因此不能对 sizeof() 运算符应用 <https://gcc.gnu.org/onlinedocs/gcc/Zero-Length.html>`_，因此对运算符的任何误用都会立即在构建时被注意到。
关于单元素数组，我们必须清楚地意识到这类数组至少占用与单个 `<https://gcc.gnu.org/onlinedocs/gcc/Zero-Length.html>`_ 类型对象相同的空间，因此它们会增加包含结构体的大小。这在人们想要计算包含此类数组的结构体动态内存总大小时很容易出错：

        struct something {
                size_t count;
                struct foo items[1];
        };

        struct something *instance;

        instance = kmalloc(struct_size(instance, items, count - 1), GFP_KERNEL);
        instance->count = count;

        size = sizeof(instance->items) * instance->count;
        memcpy(instance->items, source, size);

在上面的例子中，我们不得不记住在使用 struct_size() 帮助函数时要计算 `count - 1`，否则我们会无意中为多一个 `items` 对象分配了内存。实现这一功能最干净且最少出错的方式是通过使用 `可变长度数组成员`，结合 struct_size() 和 flex_array_size() 帮助函数：

        struct something {
                size_t count;
                struct foo items[];
        };

        struct something *instance;

        instance = kmalloc(struct_size(instance, items, count), GFP_KERNEL);
        instance->count = count;

        memcpy(instance->items, source, flex_array_size(instance, items, instance->count));

有两种特殊情况需要使用 DECLARE_FLEX_ARRAY() 帮助函数（请注意，在用户空间接口头文件中它被命名为 __DECLARE_FLEX_ARRAY()）。这些情况是：当可变长度数组作为结构体中的唯一成员或作为联合体的一部分时。C99 规范禁止这样做，但并没有技术上的原因（正如现有的此类数组在这两种位置上的使用以及 DECLARE_FLEX_ARRAY() 所采用的解决方案所表明的那样）。例如，将以下代码进行转换：

        struct something {
                ...
union {
                        struct type1 one[0];
                        struct type2 two[0];
                };
        };

必须使用帮助函数：

        struct something {
                ...
union {
                        DECLARE_FLEX_ARRAY(struct type1, one);
                        DECLARE_FLEX_ARRAY(struct type2, two);
                };
        };
