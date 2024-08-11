### SPDX 许可证标识符：GPL-2.0
### 版权所有 (C) 2022, Google LLC
==================================

#### 内核内存检查器 (KMSAN)
==================================

KMSAN 是一个动态错误检测工具，旨在发现未初始化值的使用。它基于编译器插桩，并且与用户空间的 `MemorySanitizer 工具`_ 非常相似。重要的一点是，KMSAN 不打算用于生产环境，因为它会显著增加内核的内存占用并减慢整个系统的运行速度。

### 使用方法
=============

#### 构建内核
-------------------

为了构建带有 KMSAN 的内核，你需要最新的 Clang（14.0.6 或更高版本）。请参考 `LLVM 文档`_ 获取构建 Clang 的指导说明。现在配置并构建内核，启用 CONFIG_KMSAN。
#### 示例报告
--------------

以下是一个 KMSAN 报告的例子：

```
======================================================================
BUG: KMSAN: 在 test_uninit_kmsan_check_memory+0x1be/0x380 [kmsan_test] 中检测到未初始化值
   test_uninit_kmsan_check_memory+0x1be/0x380 mm/kmsan/kmsan_test.c:273
   kunit_run_case_internal lib/kunit/test.c:333
   kunit_try_run_case+0x206/0x420 lib/kunit/test.c:374
   kunit_generic_run_threadfn_adapter+0x6d/0xc0 lib/kunit/try-catch.c:28
   kthread+0x721/0x850 kernel/kthread.c:327
   ret_from_fork+0x1f/0x30 ??:?

未初始化值被存储到内存的位置：
   do_uninit_local_array+0xfa/0x110 mm/kmsan/kmsan_test.c:260
   test_uninit_kmsan_check_memory+0x1a2/0x380 mm/kmsan/kmsan_test.c:271
   kunit_run_case_internal lib/kunit/test.c:333
   kunit_try_run_case+0x206/0x420 lib/kunit/test.c:374
   kunit_generic_run_threadfn_adapter+0x6d/0xc0 lib/kunit/try-catch.c:28
   kthread+0x721/0x850 kernel/kthread.c:327
   ret_from_fork+0x1f/0x30 ??:?

局部变量 uninit 在此创建：
   do_uninit_local_array+0x4a/0x110 mm/kmsan/kmsan_test.c:256
   test_uninit_kmsan_check_memory+0x1a2/0x380 mm/kmsan/kmsan_test.c:271

4-7 字节（共8字节）未初始化
大小为 8 字节的内存访问从地址 ffff888083fe3da0 开始

CPU: 0 PID: 6731 进程名: kunit_try_catch 污染: G    B       E     5.16.0-rc3+ #104
硬件名称: QEMU Standard PC (i440FX + PIIX, 1996), BIOS 1.14.0-2 04/01/2014
======================================================================
```

该报告指出，局部变量 `uninit` 在 `do_uninit_local_array()` 中被创建时未初始化。第三条堆栈跟踪对应于创建该变量的位置。
第一条堆栈跟踪显示了未初始化值在 `test_uninit_kmsan_check_memory()` 中被使用的地点。该工具展示了局部变量中未被初始化的字节以及在使用前将值复制到其他内存位置的堆栈。

当 KMSAN 在以下情况下检测到未初始化值 `v` 的使用时，会发出报告：

- 在条件语句中，例如 `if (v) { ... }`;
- 在索引或指针解引用中，例如 `array[v]` 或 `*v`;
- 当其被复制到用户空间或硬件中，例如 `copy_to_user(..., &v, ...)`; 
- 当其作为参数传递给函数时，并且 `CONFIG_KMSAN_CHECK_PARAM_RETVAL` 被启用（见下文）

上述情况（除了将数据复制到用户空间或硬件中，这可能是一个安全问题外）从 C11 标准的角度来看被认为是未定义行为。
禁用监控工具
-----------------------------

一个函数可以被标记为 ``__no_kmsan_checks``。这样做会使 KMSAN
忽略该函数中的未初始化值，并将其输出标记为已初始化。
因此，用户将不会收到与该函数相关的 KMSAN 报告。
另一个由 KMSAN 支持的函数属性是 ``__no_sanitize_memory``。
将此属性应用于函数会导致 KMSAN 不对其进行监控，
这对于不希望编译器干扰某些低级代码（例如使用 ``noinstr`` 标记的代码，
这会隐式添加 ``__no_sanitize_memory``）是有帮助的。
然而，这样做是有代价的：来自此类函数的栈分配将具有错误的阴影/来源值，
可能会导致误报。从非监控代码调用的函数也可能为其参数接收到错误的元数据。

作为一般规则，应避免显式使用 ``__no_sanitize_memory``。
也可以在 Makefile 中为单个文件（例如 main.o）禁用 KMSAN ：

  KMSAN_SANITIZE_main.o := n

或者为整个目录禁用：

  KMSAN_SANITIZE := n

这相当于将 ``__no_sanitize_memory`` 应用于文件或目录中的每个函数。
大多数用户不需要 KMSAN_SANITIZE，除非他们的代码因 KMSAN 而出现故障（例如，在早期启动时运行）。

支持
======

为了让 KMSAN 正常工作，内核必须使用 Clang 构建，这是目前唯一支持 KMSAN 的编译器。
内核监控传递基于用户空间的 `MemorySanitizer 工具`_。
当前，运行时库仅支持 x86_64。

KMSAN 如何工作
=================

KMSAN 阴影内存
-------------------

KMSAN 为内核内存的每个字节关联了一个元数据字节（也称为阴影字节）。
如果对应的内核内存位未初始化，则阴影字节中的位会被设置。将内存标记为未初始化（即
将影子字节设置为 ``0xff`` 的操作被称为“毒化”，而将它标记为已初始化（即将影子字节设置为 ``0x00``）的操作则被称为“解毒”。

当栈上分配一个新的变量时，默认情况下，由编译器插入的工具代码会对其进行毒化（除非该变量是一个立即被初始化的栈变量）。任何没有使用 ``__GFP_ZERO`` 标志进行的新堆分配也会被毒化。

编译器工具代码还会跟踪影子值在代码中的使用情况。在需要时，工具代码会调用位于 ``mm/kmsan/`` 中的运行时库来持久化影子值。

基本类型或复合类型的影子值是一个与该类型长度相同的字节数组。当一个常数值被写入内存时，这部分内存会被解毒。

当从内存中读取一个值时，其影子内存也会被读取并传播到所有使用该值的操作中。对于每个接受一个或多个值的指令，编译器都会生成代码来根据这些值及其影子计算结果的影子。

**示例：**

```c
int a = 0xff;  // 即 0x000000ff
int b;
int c = a | b;
```

在这个例子中，``a`` 的影子是 ``0``，``b`` 的影子是 ``0xffffffff``，而 ``c`` 的影子是 ``0xffffff00``。这意味着 ``c`` 的高三位字节未初始化，而低字节已初始化。

**起源追踪**

----------

每四个字节的内核内存也都有一个所谓的“起源”映射到它们。这个起源描述了未初始化值创建时程序执行的位置。每个起源都关联到完整的分配栈（对于堆分配的内存），或者包含未初始化变量的函数（对于局部变量）。

当在栈或堆上分配一个未初始化的变量时，会创建一个新的起源值，并将该变量的起源填充为此值。当从内存中读取一个值时，它的起源也会被读取并和影子一起保持。对于每个接受一个或多个值的指令，结果的起源是任何未初始化输入对应的起源之一。

如果一个被毒化的值被写入内存，它的起源也会被写入相应的存储空间中。
### 示例 1:

```c
int a = 42;
int b;
int c = a + b;
```

在此例中，`b` 的起源在函数入口时生成，并且在加法结果写入内存之前，存储到 `c` 的起源中。
如果多个变量存储在同一四字节块中，则它们可能具有相同的起源地址。在这种情况下，对任一变量的每次写入都会更新所有这些变量的起源。在这种情况下我们不得不牺牲一些精度，因为为每个位（甚至是每个字节）存储起源代价太大。

### 示例 2:

```c
int combine(short a, short b) {
    union ret_t {
        int i;
        short s[2];
    } ret;
    ret.s[0] = a;
    ret.s[1] = b;
    return ret.i;
}
```

如果 `a` 已初始化而 `b` 未初始化，则结果的阴影将是 `0xffff0000`，而结果的起源将是 `b` 的起源。
`ret.s[0]` 将具有相同的起源，但由于该变量已被初始化所以它将不会被使用。
如果函数的两个参数都未初始化，则只保留第二个参数的起源。

### 起源链

为了简化调试，KMSAN 为每次未初始化值写入内存的操作创建一个新的起源。新起源既引用了其创建栈又引用了该值之前的起源。这可能会导致内存消耗增加，因此我们在运行时限制了起源链的长度。

### Clang 仪器化 API

Clang 仪器化插件在内核代码中插入了定义在 `mm/kmsan/instrumentation.c` 中的函数调用。

### 阴影操作

对于每次内存访问，编译器会发出一个函数调用来返回指向给定内存的阴影和起源地址的指针对：

```c
typedef struct {
    void *shadow, *origin;
} shadow_origin_ptr_t;

shadow_origin_ptr_t __msan_metadata_ptr_for_load_{1,2,4,8}(void *addr)
shadow_origin_ptr_t __msan_metadata_ptr_for_store_{1,2,4,8}(void *addr)
shadow_origin_ptr_t __msan_metadata_ptr_for_load_n(void *addr, uintptr_t size)
shadow_origin_ptr_t __msan_metadata_ptr_for_store_n(void *addr, uintptr_t size)
```

函数名称取决于内存访问大小。
编译器确保对于每个加载的值，其阴影和起源值从内存中读取。当一个值存储到内存中时，它的阴影和起源也使用元数据指针进行存储。

### 处理局部变量

使用一个特殊函数来为局部变量创建一个新的起源值，并将该变量的起源设置为该值：

```c
void __msan_poison_alloca(void *addr, uintptr_t size, char *descr)
```

### 访问每任务数据

在每个仪器化函数开始时，KMSAN 插入了一个调用到 `__msan_get_context_state()`：

```c
kmsan_context_state *__msan_get_context_state(void)
```

`kmsan_context_state` 在 `include/linux/kmsan.h` 中声明：

```c
struct kmsan_context_state {
    char param_tls[KMSAN_PARAM_SIZE];
    char retval_tls[KMSAN_RETVAL_SIZE];
    char va_arg_tls[KMSAN_PARAM_SIZE];
    char va_arg_origin_tls[KMSAN_PARAM_SIZE];
    u64 va_arg_overflow_size_tls;
    char param_origin_tls[KMSAN_PARAM_SIZE];
    depot_stack_handle_t retval_origin_tls;
};
```

此结构用于 KMSAN 在仪器化函数之间传递参数阴影和起源（除非参数立即通过 `CONFIG_KMSAN_CHECK_PARAM_RETVAL` 进行检查）。
传递未初始化的值给函数
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

Clang 的 MemorySanitizer 仪器具有一个选项，
``-fsanitize-memory-param-retval``，它使编译器检查通过值传递的函数参数以及函数返回值。
该选项由 ``CONFIG_KMSAN_CHECK_PARAM_RETVAL`` 控制，默认情况下启用该选项以让 KMSAN 更早地报告未初始化的值。
请参阅 `LKML 讨论`_ 获取更多详细信息。
由于 LLVM 中实现检查的方式（它们仅应用于标记为 ``noundef`` 的参数），并非所有参数都保证会被检查，因此我们不能放弃在 ``kmsan_context_state`` 中的元数据存储。
字符串函数
~~~~~~~~~~~~~~~~

编译器将对 ``memcpy()``/``memmove()``/``memset()`` 的调用替换为以下函数。这些函数也会在数据结构初始化或复制时被调用，确保阴影和原始值与数据一起被复制： 

```c
  void *__msan_memcpy(void *dst, void *src, uintptr_t n)
  void *__msan_memmove(void *dst, void *src, uintptr_t n)
  void *__msan_memset(void *dst, int c, uintptr_t n)
```

错误报告
~~~~~~~~~~~~~~~

对于每个值的使用，编译器会发出一个阴影检查，如果该值被污染，则调用 ``__msan_warning()`` ：

```c
  void __msan_warning(u32 origin)
```

``__msan_warning()`` 会导致 KMSAN 运行时打印错误报告。
内联汇编仪器
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

KMSAN 为每个内联汇编输出添加了一个调用：

```c
  void __msan_instrument_asm_store(void *addr, uintptr_t size)
```

这会解除对该内存区域的污染标记。
这种方法可能会掩盖某些错误，但它也有助于避免大量位操作、原子操作等中的误报。
有时传递到内联汇编中的指针并不指向有效的内存。
在这种情况下，它们在运行时被忽略。
运行时库
---------------

代码位于 ``mm/kmsan/`` 目录中。
### 每任务 KMSAN 状态
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

每个 `task_struct` 都有关联的 KMSAN 任务状态，该状态保存了 KMSAN 的上下文（见上文）和一个每任务标志来禁止 KMSAN 报告：

```c
struct kmsan_context {
    // ...
    bool allow_reporting;
    struct kmsan_context_state cstate;
    // ...
}

struct task_struct {
    // ...
    struct kmsan_context kmsan;
    // ...
}
```

### KMSAN 上下文
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

当在内核任务上下文中运行时，KMSAN 使用 `current->kmsan.cstate` 来保存函数参数和返回值的元数据。
但在内核运行于中断、软中断或非屏蔽中断 (NMI) 上下文的情况下，由于此时 `current` 不可用，KMSAN 切换到每个 CPU 的中断状态：

```c
DEFINE_PER_CPU(struct kmsan_ctx, kmsan_percpu_ctx);
```

### 元数据分配
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

内核中有几个地方存储了元数据：
1. 每个 `struct page` 实例包含指向其影子页和原始页的两个指针：

```c
struct page {
    // ...
    struct page *shadow, *origin;
    // ...
};
```

在启动时，内核为每个可用的内核页分配影子页和原始页。这是在内核地址空间已经变得碎片化时进行的，因此正常的数据页可能与元数据页交错分布。
这意味着对于两个连续的内存页，它们的影子/原始页可能不连续。因此，如果一个内存访问跨越了一个内存块的边界，对影子/原始内存的访问可能会破坏其他页或从中读取错误的值。
在实际应用中，由同一个`alloc_pages()`调用返回的连续内存页会具有连续的元数据；而如果这些页属于两个不同的分配，则它们的元数据页可能会分散。
对于内核数据（如`.data`、`.bss`等）和每个CPU的内存区域，并不能保证元数据的连续性。
当`__msan_metadata_ptr_for_XXX_YYY()`命中两个非连续元数据页之间的边界时，它将返回指向假阴影/源区域的指针：

```c
char dummy_load_page[PAGE_SIZE] __attribute__((aligned(PAGE_SIZE)));
char dummy_store_page[PAGE_SIZE] __attribute__((aligned(PAGE_SIZE)));
```

`dummy_load_page`被零初始化，因此从中读取总是得到零。
所有对`dummy_store_page`的写入都会被忽略。
2. 对于通过`vmalloc`分配的内存和模块，内存范围、其阴影和源之间存在直接映射关系。KMSAN将`vmalloc`区域减少了3/4，仅使最初的1/4可用于`vmalloc()`。`vmalloc`区域的第二部分包含为第一部分提供服务的阴影内存，第三部分则保存源数据。第四部分的一小部分包含了内核模块的阴影和源数据。更多详细信息请参考`arch/x86/include/asm/pgtable_64_types.h`。
当一组页映射到连续的虚拟内存空间时，它们的阴影和源页也类似地映射到连续的区域。

参考文献
=========

E. Ste潘诺夫, K. 谢列布里亚尼. 《MemorySanitizer：快速检测C++中未初始化内存使用的工具》 <https://static.googleusercontent.com/media/research.google.com/en//pubs/archive/43308.pdf>  
发表于CGO 2015
.. _MemorySanitizer 工具: https://clang.llvm.org/docs/MemorySanitizer.html
.. _LLVM 文档: https://llvm.org/docs/GettingStarted.html
.. _LKML 讨论: https://lore.kernel.org/all/20220614144853.3693273-1-glider@google.com/
