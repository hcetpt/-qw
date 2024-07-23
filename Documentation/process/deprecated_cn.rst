### 已弃用的接口、语言特性、属性和约定

在一个理想的世界里，可以在一个开发周期内将所有已弃用API的实例转换为新的API，并完全移除旧的API。然而，由于内核的庞大、维护层次结构以及时间因素，一次性进行这些转换往往是不可行的。这意味着在移除旧API的同时可能会有新的实例悄悄地加入到内核中，这只会增加移除API的工作量。为了教育开发者了解哪些已经被弃用及其原因，创建了这份列表作为参考，当提议将已弃用的内容包含在内核中时可以引用。

__deprecated
------------
尽管此属性在视觉上标记了一个接口已被弃用，但它不再在构建过程中产生警告[1]，因为内核的一个长期目标是无警告构建，而实际上没有人真正去移除这些被弃用的接口。虽然在头文件中使用`__deprecated`来标注旧的API是很不错的，但这并不是完整的解决方案。这样的接口要么从内核中完全移除，要么添加到本文件中以阻止他人在未来使用它们。

BUG() 和 BUG_ON()
------------------
请改用WARN() 和 WARN_ON()，并尽可能优雅地处理“不可能”的错误条件。虽然BUG()系列API最初设计用于表示“不可能的情况”断言并安全地终止内核线程，但事实证明它们风险太大（例如，“锁需要以什么顺序释放？各种状态是否已经恢复？”）。非常常见的是，使用BUG()会导致系统不稳定或完全崩溃，使得调试甚至获取有效的崩溃报告变得不可能。Linus对此持有非常强烈的观点[2][3]。
请注意，WARN()系列只应用于“预期不可达”的情况。如果您想警告“可达但不期望”的情况，请使用pr_warn()系列函数。系统所有者可能设置了*panic_on_warn* sysctl选项，以确保其系统不会在面对“不可达”的情况下继续运行。（例如，参见像这样的提交[4]）。

分配器参数中的开放编码算术
--------------------------------------------
不应在内存分配器（或其他类似函数）的参数中执行动态大小计算（特别是乘法），因为存在溢出的风险。这可能导致值回绕，导致分配的内存比调用者期望的小。使用这些分配可能导致堆内存线性溢出和其他异常行为。（例外是编译器可以发出警告的字面值。在这种情况下，推荐的做法是重构代码如下所示，以避免开放编码算术。）

例如，不要使用`count * size`作为参数，如：
```c
foo = kmalloc(count * size, GFP_KERNEL);
```

相反，应使用分配器的两因子形式：
```c
foo = kmalloc_array(count, size, GFP_KERNEL);
```

具体来说，kmalloc()可以用kmalloc_array()替换，kzalloc()可以用kcalloc()替换。如果没有可用的两因子形式，则应使用饱和溢出助手：
```c
bar = dma_alloc_coherent(dev, array_size(count, size), &dma, GFP_KERNEL);
```

另一个常见的需要避免的情况是在结构体尾部计算其他结构体数组的大小：
```c
header = kzalloc(sizeof(*header) + count * sizeof(*header->item), GFP_KERNEL);
```

相反，使用助手：
```c
header = kzalloc(struct_size(header, item, count), GFP_KERNEL);
```

**注意：**如果您正在对包含零长度或单元素数组作为尾部成员的结构体使用struct_size()，请重构此类数组使用，并切换到**灵活数组成员**[5]。

对于其他计算，请组合使用size_mul()、size_add()和size_sub()等辅助函数。例如，在以下情况下：
```c
foo = krealloc(current_size + chunk_size * (count - 3), GFP_KERNEL);
```

相反，使用辅助函数：
```c
foo = krealloc(size_add(current_size, 
                        size_mul(chunk_size, 
                                 size_sub(count, 3))), GFP_KERNEL);
```

有关更多详细信息，请参阅array3_size()和flex_array_size()，以及相关的check_mul_overflow()、check_add_overflow()、check_sub_overflow()和check_shl_overflow()等函数。

simple_strtol()、simple_strtoll()、simple_strtoul()、simple_strtoull()
----------------------------------------------------------------------
simple_strtol()、simple_strtoll()、simple_strtoul()和simple_strtoull()函数明确忽略了溢出，这可能会导致调用者中出现意外的结果。相应的kstrtol()、kstrtoll()、kstrtoul()和kstrtoull()函数通常是正确的替代方案，但请注意，这些函数要求字符串必须以NUL或换行符终止。

strcpy()
--------
strcpy()不对目标缓冲区执行边界检查。这可能会导致超出缓冲区末尾的线性溢出，从而导致各种异常行为。虽然`CONFIG_FORTIFY_SOURCE=y`和各种编译器标志有助于减少使用此函数的风险，但没有充分的理由添加新的使用实例。安全的替代方案是strscpy()，但在任何使用strcpy()返回值的情况下都需要注意，因为strscpy()不返回指向目的地的指针，而是返回复制的非NUL字节数（截断时返回负errno）。

strncpy() 在NUL终止的字符串上
-----------------------------------
使用strncpy()并不能保证目标缓冲区会被NUL终止。这可能会导致由于缺少终止而导致的各种线性读取溢出和其他异常行为。它还会在源内容短于目标缓冲区大小时向目标缓冲区NUL填充，这对于仅使用NUL终止的字符串的调用者来说可能是不必要的性能损失。

当需要目标缓冲区NUL终止时，替换方案是strscpy()，但在任何使用strncpy()返回值的情况下都需要注意，因为strscpy()不返回指向目的地的指针，而是返回复制的非NUL字节数（截断时返回负errno）。仍然需要NUL填充的任何情况应改为使用strscpy_pad()。

---

[1] [不再在构建过程中产生警告](https://git.kernel.org/linus/771c035372a036f83353eef46dbb829780330234)
[2] [Linus对此持有的非常强烈的观点](https://lore.kernel.org/lkml/CA+55aFy6jNLsywVYdGp83AMrXBo_P-pkjkphPGrO=82SPKCpLQ@mail.gmail.com/)
[3] [关于此的观点](https://lore.kernel.org/lkml/CAHk-=whDHsbK3HTOpTF=ue_o04onRwTEaK_ZoJp_fjbqq4+=Jw@mail.gmail.com/)
[4] [示例提交](https://git.kernel.org/linus/d4689846881d160a4d12a514e991a740bcb5d65a)
[5] [零长度和单元素数组](#zero-length-and-one-element-arrays)
如果调用者使用非空终止字符串，应使用`strtomem()`函数，并且目标应标记为`__nonstring`属性（<https://gcc.gnu.org/onlinedocs/gcc/Common-Variable-Attributes.html>），以避免未来的编译器警告。对于仍然需要空填充的情况，可以使用`strtomem_pad()`函数。

`strlcpy()`会先读取整个源缓冲区（因为返回值旨在匹配`strlen()`的结果）。此读取可能会超出目标大小限制。这不仅效率低下，而且如果源字符串未空终止，可能会导致线性读溢出。安全的替代方案是使用`strscpy()`，但在任何使用`strlcpy()`返回值的情况下需小心，因为当`strscpy()`截断时会返回负的errno值。

`%p`格式化符
传统上，在格式化字符串中使用“%p”会导致dmesg、proc、sysfs等中的常规地址暴露缺陷。为了避免这些被利用，内核中所有“%p”的使用都被打印为哈希值，使它们无法用于寻址。不应向内核添加新的“%p”使用。对于文本地址，使用“%pS”可能更好，因为它会产生更有用的符号名称。对于几乎所有其他情况，根本不要添加“%p”。

参照Linus当前的指导（<https://lore.kernel.org/lkml/CA+55aFwQEd_d40g4mUCSsVRZzrFPUJt74vc6PPpb675hYNXcKw@mail.gmail.com/>）：

- 如果哈希后的“%p”值毫无意义，问问自己指针本身是否重要。也许应该完全删除？
- 如果你真的认为真实的指针值很重要，为什么某些系统状态或用户权限级别被认为是“特殊”的？如果你认为你可以足够好地在注释和提交日志中证明它，以经受住Linus的审查，也许你可以使用“%px”，同时确保你有合理的权限。

如果你正在调试某个问题，其中“%p”哈希导致问题，你可以暂时使用调试标志`no_hash_pointers`（<https://git.kernel.org/linus/5ead723a20e0447bc7db33dc3070b420e5f80aa6>`）启动。

可变长度数组（VLAs）
使用堆栈上的VLA会产生比静态大小的堆栈数组更糟糕的机器代码。虽然这些非平凡的性能问题（<https://git.kernel.org/linus/02361bc77888>`）足以消除VLA，但它们也是一个安全风险。堆栈数组的动态增长可能会超过堆栈段中剩余的内存。这可能导致崩溃，可能覆盖堆栈末尾的敏感内容（当未使用`CONFIG_THREAD_INFO_IN_TASK=y`构建时），或覆盖堆栈相邻的内存（当未使用`CONFIG_VMAP_STACK=y`构建时）

隐式switch case穿透
C语言允许在case末尾缺少“break”语句时，switch case穿透到下一个case。然而，这在代码中引入了歧义，因为并不总是清楚缺失的break是有意还是错误。例如，仅从代码看，`STATE_ONE`是否故意穿透到`STATE_TWO`并不明显：

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

由于缺少“break”语句（<https://cwe.mitre.org/data/definitions/484.html>`）导致了一系列的缺陷，我们不再允许隐式穿透。为了识别有意的穿透情况，我们采用了伪关键字宏“fallthrough”，它扩展为GCC的扩展`__attribute__((__fallthrough__))`（<https://gcc.gnu.org/onlinedocs/gcc/Statement-Attributes.html>`）。当C17/C18的`[[fallthrough]]`语法被C编译器、静态分析器和IDE更广泛支持时，我们可以将该语法用于宏伪关键字。

所有switch/case块必须以以下之一结束：

* break;
* fallthrough;
* continue;
* goto <label>;
* return [expression];

零长度和单元素数组
内核中经常需要提供一种方法来声明具有动态大小的结构尾部元素集。内核代码应始终使用“灵活数组成员”（<https://en.wikipedia.org/wiki/Flexible_array_member>`）来处理这些情况。旧样式的一元素或零长度数组不应再使用。

在旧的C代码中，通过在结构末尾指定一个一元素数组来实现动态大小的尾部元素：

```c
struct something {
    size_t count;
    struct foo items[1];
};
```

这导致了通过sizeof()进行的脆弱大小计算（需要去除单个尾部元素的大小以获得正确的“头”大小）。引入了一个GNU C扩展（<https://gcc.gnu.org/onlinedocs/gcc/Zero-Length.html>`）以允许零长度数组，以避免这类大小问题：

```c
struct something {
    size_t count;
    struct foo items[0];
};
```

但这带来了其他问题，并没有解决两种风格共有的某些问题，比如当这种数组意外地不是在结构末尾使用时无法检测（这可能直接发生，或者当此类结构位于联合体、结构的结构中时）

C99引入了“灵活数组成员”，其数组声明完全缺乏数字大小：

```c
struct something {
    size_t count;
    struct foo items[];
};
```

这是内核期望声明动态大小尾部元素的方式。它允许编译器在灵活数组不位于结构末尾时生成错误，有助于防止某些类型的未定义行为（<https://git.kernel.org/linus/76497732932f15e7323dc805e8ea8dc11bb587cf>`）错误不经意地引入到代码库中。它还允许编译器正确分析数组大小（通过sizeof()、`CONFIG_FORTIFY_SOURCE`和`CONFIG_UBSAN_BOUNDS`）。例如，没有机制警告我们以下对零长度数组应用sizeof()运算符总是结果为零：

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

在上面代码的最后一行，`size`结果为`零`，而人们可能以为它代表了最近为尾部数组`items`动态分配的内存的总字节大小。以下是该问题的两个示例：链接1（<https://git.kernel.org/linus/f2cd32a443da694ac4e28fbf4ac6f9d5cc63a539>`）、链接2（<https://git.kernel.org/linus/ab91c2a89f86be2898cee208d492816ec238b2cf>`）

相反，`flexible array members`具有不完整类型，因此不能应用sizeof()运算符（<https://gcc.gnu.org/onlinedocs/gcc/Zero-Length.html>`），因此任何此类运算符的误用将在构建时立即被注意到。
关于单元素数组，我们必须清楚地意识到，此类数组至少占用与`单个该类型对象`相同的空间（参考链接：`<https://gcc.gnu.org/onlinedocs/gcc/Zero-Length.html>`），因此它们会增加包含结构体的大小。这在人们想要计算包含这种数组作为成员的结构体动态内存总大小时，很容易出错：

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

在上述示例中，使用struct_size()辅助函数时，我们不得不记住计算`count - 1`，否则我们将无意中为多一个`items`对象分配了内存。最干净且最少出错的实现方式是通过使用`可变长度数组成员`，结合struct_size()和flex_array_size()辅助函数：

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

有两种特殊情况需要使用DECLARE_FLEX_ARRAY()辅助函数进行替换。（注意，在UAPI头文件中它被命名为__DECLARE_FLEX_ARRAY()。）这些情况是当可变长度数组成员单独存在于结构体中或作为联合的一部分时。C99规范不允许这种情况发生，但这并非出于技术原因（从现有在这些位置使用此类数组的情况以及DECLARE_FLEX_ARRAY()使用的解决方法可以看出）。例如，要转换以下代码：

```c
    struct something {
            ..
    union {
            struct type1 one[0];
            struct type2 two[0];
    };
    };
```

必须使用辅助函数：

```c
    struct something {
            ..
    union {
            DECLARE_FLEX_ARRAY(struct type1, one);
            DECLARE_FLEX_ARRAY(struct type2, two);
    };
    };
```
