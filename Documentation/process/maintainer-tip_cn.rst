SPDX 许可证标识符：GPL-2.0

尖端树手册
==========

什么是尖端树？
---------------

尖端树是一系列子系统和开发领域的集合。尖端树既是直接的开发树，也是多个子维护者树的聚合树。尖端树的 GitWeb URL 是：https://git.kernel.org/pub/scm/linux/kernel/git/tip/tip.git

尖端树包含以下子系统：

- **x86 架构**

  x86 架构的开发在尖端树中进行，但 x86 KVM 和 XEN 特定部分则在其对应的子系统中维护，并直接从那里合并到主线。对于 x86 特定的 KVM 和 XEN 补丁，仍然建议抄送 x86 维护者。
  某些 x86 子系统有自己的维护者，除了总体的 x86 维护者之外。请在修改 arch/x86 下的文件时抄送总体的 x86 维护者，即使这些文件没有被 MAINTAINER 文件特别指出。
  注意，“x86@kernel.org”不是一个邮件列表，而只是一个邮件别名，用于将邮件分发给 x86 高级维护者团队。请始终抄送 Linux 内核邮件列表（LKML）`linux-kernel@vger.kernel.org`，否则您的邮件只会进入维护者的私人收件箱。
- **调度器**

  调度器开发在尖端树中的 sched/core 分支进行——有时会有专门的子主题树来处理正在进行中的补丁集。
- **锁定与原子操作**

  锁定开发（包括原子操作和其他与锁定相关的同步原语）在尖端树中的 locking/core 分支进行——有时会有专门的子主题树来处理正在进行中的补丁集。
- **通用中断子系统及中断芯片驱动程序**：

  - 中断核心开发在 irq/core 分支进行。

  - 中断芯片驱动程序开发也在 irq/core 分支进行，但补丁通常会在单独的维护者树中应用，然后汇总到 irq/core 分支。
- **时间、定时器、时间保持、NOHZ 及相关芯片驱动程序**：

  - 时间保持、clocksource 核心、NTP 和 alarmtimer 开发在 timers/core 分支进行，但补丁通常会在单独的维护者树中应用，然后汇总到 timers/core 分支。

  - clocksource/event 驱动程序开发在 timers/core 分支进行，但补丁大多在单独的维护者树中应用，然后汇总到 timers/core 分支。
- **性能计数器核心、架构支持和工具**：

  - perf 核心和架构支持开发在 perf/core 分支进行。

  - perf 工具开发在 perf 工具维护者树中进行，并汇总到尖端树。
- **CPU 热插拔核心**

- **RAS 核心**

  大多数特定于 x86 的 RAS 补丁收集在尖端树的 ras/core 分支中。
- **EFI 核心**

  EFI 开发在 efi Git 树中。收集的补丁汇总在尖端树的 efi/core 分支中。
- **RCU**

  RCU 开发在 linux-rcu 树中进行。最终更改汇总到尖端树的 core/rcu 分支。
- **各种核心代码组件**：

  - debugobjects

  - objtool

  - 各种零散的部分

补丁提交说明
-------------

选择树/分支
^^^^^^^^^^^^^^^^^^^^^^^^^

一般来说，针对尖端树主分支的开发是可行的，但对于那些独立维护、有自己的 Git 树并且仅汇总到尖端树的子系统，开发应在相关的子系统树或分支中进行。
针对主线的 Bug 修复应该始终适用于主线内核树。对于已经在 tip 树中排队的变更所引起的潜在冲突，由维护者处理。

补丁主题
^^^^^^^^^^^^^

tip 树偏好的补丁主题前缀格式为 '子系统/组件:'，例如 'x86/apic:'、'x86/mm/fault:'、'sched/fair:'、'genirq/core:'。请不要使用文件名或完整的文件路径作为前缀。在大多数情况下，`git log path/to/file` 应该能给你一个合理的提示。

主题行中的简要补丁描述应以大写字母开头，并用命令式语气书写。

变更日志
^^^^^^^^^

关于变更日志的一般规则在《提交补丁指南》(:ref:`Submitting patches guide <describe_changes>`) 中适用。

tip 树的维护者重视遵循这些规则，特别是要求以命令式语气编写变更日志，并不以代码或其执行的方式进行描述。这不仅仅是维护者的偏好。抽象词句书写的变更日志更精确且不容易引起混淆。

将变更日志结构化为几个段落也是有用的，而不是将其全部堆在一起。一个好的结构是分别解释背景、问题和解决方案，并按此顺序排列。

示例说明：

  示例 1::

    x86/intel_rdt/mbm: 在 CPU 热插拔期间修复 MBM 溢出处理

    当一个 CPU 即将失效时，我们会取消工作并在同一域的不同 CPU 上调度一个新的工作。但如果定时器已经快要过期（比如 0.99 秒），那么实际上会加倍间隔时间。
    我们修改了热插拔 CPU 的处理方式，在即将失效的 CPU 上取消延迟工作，并在同一域的不同 CPU 上立即运行工作。我们不会刷新工作，因为 MBM 溢出工作会在同一 CPU 上重新调度并扫描域->cpu_mask 来获取域指针。

    改进版本::

    x86/intel_rdt/mbm: 在 CPU 热插拔期间修复 MBM 溢出处理

    当一个 CPU 即将失效时，溢出工作被取消并在同一域的不同 CPU 上重新调度。但如果定时器已经快要过期，这实际上会加倍间隔时间，可能会导致未检测到的溢出。
    取消溢出工作并在同一域的不同 CPU 上立即重新调度。工作也可以被刷新，但这会导致在同一 CPU 上重新调度。
示例 2：

    时间：POSIX CPU 定时器：确保变量已初始化

    如果 `cpu_timer_sample_group` 返回 `-EINVAL`，它将不会写入 `*sample`。检查 `cpu_timer_sample_group` 的返回值排除了在后续块中使用未初始化的 `now` 值的可能性。
如果 `clock_idx` 无效，之前的代码可能会以未定义的方式覆盖 `*oldval`。现在这种情况已被防止。我们还利用了 `&&` 的短路特性，仅在结果实际用于更新 `*oldval` 时才采样定时器。
改进版本：

    POSIX-CPU-定时器：使 `set_process_cpu_timer()` 更健壮

    由于没有检查 `cpu_timer_sample_group()` 的返回值，编译器和静态检查工具可以合法地警告可能使用未初始化的变量 `now`。这不是运行时问题，因为所有调用点都传递了有效的时钟 ID。
此外，即使 `*oldval` 为 `NULL`（即不使用结果）时，`cpu_timer_sample_group()` 也会无条件被调用。
让调用有条件，并检查返回值。

示例 3：

    该实体也可以用于其他目的
让我们将其重命名为更通用的名字
改进版本：

    该实体也可以用于其他目的
将其重命名为更通用的名字
对于复杂场景，特别是在竞态条件和内存排序问题上，使用表格来描绘场景是非常有价值的，表格展示了事件的并行性和时间顺序。以下是一个例子：

    CPU0                            CPU1
    free_irq(X)                     interrupt X
                                    spin_lock(desc->lock)
                                    wake irq thread()
                                    spin_unlock(desc->lock)
    spin_lock(desc->lock)
    remove action()
    shutdown_irq()
    release_resources()             thread_handler()
    spin_unlock(desc->lock)           access released resources
同步中断（synchronize_irq()）

锁依赖（Lockdep）提供了类似的有用输出以描绘一个可能的死锁场景：

```
CPU0                                    CPU1
rtmutex_lock(&rcu->rt_mutex)
  spin_lock(&rcu->rt_mutex.wait_lock)
                                            local_irq_disable()
                                            spin_lock(&timer->it_lock)
                                            spin_lock(&rcu->mutex.wait_lock)
    --> 中断
        spin_lock(&timer->it_lock)
```

更改日志中的函数引用
^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^

当在更改日志中提及某个函数时，无论是文本正文还是主题行，请使用“函数名()”的格式。省略函数名后的括号可能会引起歧义：

```
主题：子系统/组件：使reservation_count静态化

reservation_count仅在reservation_stats中使用。使其成为静态变量。
```
带括号的变体更精确：

```
主题：子系统/组件：使reservation_count()静态化

reservation_count()仅在reservation_stats()中被调用。使其静态化。
```

更改日志中的回溯信息
^^^^^^^^^^^^^^^^^^^^^^^^

参见 :ref:`backtraces`

提交标签的顺序
^^^^^^^^^^^^^^^^^^^^^^^

为了统一查看提交标签，维护者使用以下标签排序方案：

- Fixes: 12字符-SHA1 ("子系统/组件: 原始主题行")

  即使不需要将更改回退到稳定内核版本，也应添加Fixes标签，即当解决最近引入的问题时，该问题只影响tip或主线当前版本。这些标签有助于识别原始提交，并且比在更改日志文本中显眼地提及引入问题的提交更有价值，因为它们可以自动提取。

下面的例子说明了区别：

```
提交

  abcdef012345678 ("x86/xxx: 替换foo为bar")

  留下了未使用的foo变量实例。移除它
签署者: J.Dev <j.dev@mail>
```

请改为：

```
最近替换foo为bar留下了未使用的foo变量实例。移除它
Fixes: abcdef012345678 ("x86/xxx: 替换foo为bar")
  签署者: J.Dev <j.dev@mail>
```

后者将补丁信息置于焦点，并附上引入问题的提交参考，而不是一开始就关注原始提交。

- Reported-by: ``报告者 <reporter@mail>``

- Closes: ``此修复的bug报告的URL或消息ID``

- Originally-by: ``原始作者 <original-author@mail>``

- Suggested-by: ``建议者 <suggester@mail>``

- Co-developed-by: ``共同作者 <co-author@mail>``

  签署者: ``共同作者 <co-author@mail>``

  注意，Co-developed-by和共同作者的签署者必须成对出现。

- 签署者: ``作者 <author@mail>``

  第一个签署者（SOB）在最后一个Co-developed-by/SOB对之后是作者的签署者，即git标记的作者。

- 签署者: ``补丁处理者 <handler@mail>``

  作者签署者之后的签署者来自处理和传输补丁的人，但没有参与开发。认可应作为Acked-by行给出，审查批准应作为Reviewed-by行给出。
如果处理者对补丁或变更日志进行了修改，则应在变更日志文本**之后**、所有提交标签**之前**，按照以下格式提及：

```
... 变更日志文本结束
[ 处理者: 将foo替换为bar并更新了变更日志 ]

     第一个标签: ....
注意，该通知与变更日志文本和提交标签之间有两行空行。
```

如果补丁由处理者发送到邮件列表，则作者必须在变更日志的第一行中注明，格式如下：

```
From: 作者 <author@mail>

     变更日志文本从这里开始...
```

这样可以保留作者身份。`From:` 行后面必须跟一个空行。如果没有这个 `From:` 行，则该补丁将归因于发送（传输、处理）它的人。

`From:` 行在补丁应用时会被自动移除，并不会出现在最终的 Git 变更日志中。它仅影响结果 Git 提交的作者信息。

- 测试者: ``Tester <tester@mail>``
- 审查者: ``Reviewer <reviewer@mail>``
- 确认者: ``Acker <acker@mail>``
- 抄送: ``抄送人员 <person@mail>``

如果需要将补丁回退到稳定版本，请添加 `'Cc: stable@vger.kernel.org'` 标签，但在发送邮件时不要抄送 stable。

- 链接: ``https://link/to/information``

引用内核邮件列表上发布的邮件时，请使用 `lore.kernel.org` 的重定向 URL，例如：

```
链接: https://lore.kernel.org/email-message-id@here
```

此 URL 应用于引用相关邮件主题、相关补丁集或其他重要讨论线程。

一种方便的方法是使用类似 Markdown 的括号表示法将 `链接: ` 附加到提交消息中，例如：

```
以前曾尝试过类似的方法作为另一项工作的一部分 [1]，但最初的实现导致了太多回归问题 [2]，因此被撤销并重新实现。
链接: https://lore.kernel.org/some-msgid@here # [1]
     链接: https://bugzilla.example.org/bug/12345  # [2]
```

您还可以使用 `链接: ` 标记来指示在将补丁应用于您的 Git 仓库时的补丁来源。在这种情况下，请使用专用的 `patch.msgid.link` 域名而不是 `lore.kernel.org`。
这种做法使得自动化工具能够识别出哪个链接用于检索原始补丁提交。例如：

```
Link: https://patch.msgid.link/patch-source-message-id@here
```

请不要使用组合标签（如 ``Reported-and-tested-by``），因为它们会增加自动化提取标签的复杂性。

文档链接
^^^^^^^^^^^^^^^^^^^^^^

在更改日志中提供文档链接对于后续调试和分析非常有帮助。不幸的是，URL经常很快失效，因为公司会频繁重组其网站。例外情况包括英特尔SDM和AMD APM这些非“易变”的文档。
因此，对于“易变”的文档，请在内核Bugzilla（https://bugzilla.kernel.org）中创建一个条目，并将这些文档附加到Bugzilla条目中。最后，在更改日志中提供Bugzilla条目的URL。

补丁重发或提醒
^^^^^^^^^^^^^^^^^^^^^^^^^

参见 :ref:`resend_reminders`

合并窗口
^^^^^^^^^^^^

请不要期望在合并窗口期间或前后补丁会被维护者审查或合并。在此期间，树仅对紧急修复开放。一旦合并窗口关闭并发布新的-rc1内核后，树会重新开放。
大型系列应在合并窗口开启前至少一周提交至可合并状态。对于错误修复以及有时针对新硬件的小型独立驱动程序或硬件启用的最小侵入性补丁，可以作为例外处理。
在合并窗口期间，维护者主要关注上游变更、修复合并窗口带来的问题、收集错误修复，并给自己一些喘息的时间。请尊重这一点。
所谓的“紧急”分支将在每个发布的稳定阶段合并到主线中。

Git
^^^

tip维护者接受那些提供子系统变更以在tip树中聚合的维护者的git拉取请求。
通常不接受新的补丁提交的拉取请求，也不能替代通过邮件列表进行的正式补丁提交。主要原因在于审核流程是基于电子邮件的。
如果你提交一个较大的补丁系列，提供一个私有仓库中的 Git 分支是有帮助的，这样可以让感兴趣的人轻松地拉取该系列进行测试。通常的做法是在补丁系列的封面信中提供一个 Git URL。

测试
^^^^^^^

在提交代码给维护者之前，应该对代码进行测试。除了微小的更改外，其他任何更改都应使用全面（且重量级）的内核调试选项进行构建、启动和测试。
这些调试选项可以在 `kernel/configs/x86_debug.config` 中找到，并可以通过运行以下命令添加到现有的内核配置中：

```
make x86_debug.config
```

其中一些选项是特定于 x86 的，在其他架构上测试时可以忽略这些选项。
.. _maintainer-tip-coding-style:

编码风格注意事项
------------------

注释风格
^^^^^^^^^^^^^

注释中的句子以大写字母开头。
单行注释示例：

```c
/* 这是一个单行注释 */
```

多行注释示例：

```c
/*
 * 这是一个格式正确的
 * 多行注释
 *
 * 较大的多行注释应分为段落
 */
```

不要使用尾注释（见下文）：

  请避免使用尾注释。尾注释几乎在所有上下文中都会干扰阅读流程，特别是在代码中：

```c
if (somecondition_is_true) /* 不要在这种地方加注释 */
    dostuff(); /* 也不要在这种地方加注释 */

seed = MAGIC_CONSTANT; /* 也不要在这里加注释 */
```

使用独立注释代替：

```c
/* 如果没有注释，这个条件并不明显 */
if (somecondition_is_true) {
    /* 这确实需要文档说明 */
    dostuff();
}

/* 这个神奇的初始化需要注释。也许不需要？ */
seed = MAGIC_CONSTANT;
```

使用 C++ 风格的尾注释来记录头文件中的结构体，以实现更紧凑的布局和更好的可读性：

```c
// eax
u32     x2apic_shift    :  5, // 位移 APIC ID 右侧的位数，用于下一级的拓扑 ID
                                : 27; // 保留

// ebx
u32     num_processors  : 16, // 当前级别的处理器数量
                                : 16; // 保留
```

与下面的对比：

```c
/* eax */
        /*
         * 位移 APIC ID 右侧的位数，用于下一级的拓扑 ID
         */
        u32     x2apic_shift    :  5,
                /* 保留 */
                                : 27;

/* ebx */
        /* 当前级别的处理器数量 */
u32     num_processors  : 16,
        /* 保留 */
                : 16;
```

注释重要的内容：

  应在操作不明显的地方添加注释。记录显而易见的内容只会造成干扰：

```c
/* 减少引用计数并检查是否为零 */
if (refcount_dec_and_test(&p->refcnt)) {
    do;
    lots;
    of;
    magic;
    things;
}
```

相反，注释应解释非显而易见的细节并记录约束：

```c
if (refcount_dec_and_test(&p->refcnt)) {
    /*
     * 解释为什么需要执行下面的魔法事情，包括顺序和锁定约束等。
     */
    do;
    lots;
    of;
    magic;
    /* 必须是最后一个操作，因为... */
    things;
}
```

函数文档注释：

  为了记录函数及其参数，请使用 kernel-doc 格式而不是自由形式的注释：

```c
/**
 * magic_function - 执行大量魔法操作
 * @magic: 指向要操作的魔法数据的指针
 * @offset: @magic 数据数组中的偏移量
 *
 * 使用 @magic 执行神秘操作的深入解释以及返回值的文档说明
 *
 * 注意，上面的参数描述是以表格形式排列的
 */
```

这尤其适用于全局可见的函数和公共头文件中的内联函数。对于每个需要简短解释的静态函数使用 kernel-doc 格式可能会显得多余。使用描述性强的函数名通常可以替代这些简短的注释。
始终运用常识

记录锁要求
^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^

记录锁要求是一件好事，但注释不一定是最佳选择。与其这样写：

```c
/* 调用者必须持有 foo->lock */
void func(struct foo *foo)
{
    ..
}
```

请使用如下方式：

```c
void func(struct foo *foo)
{
    lockdep_assert_held(&foo->lock);
    ..
}
```

在启用 `PROVE_LOCKING` 的内核中，如果调用者没有持有锁，`lockdep_assert_held()` 会发出警告。注释无法做到这一点。

括号规则
^^^^^^^^^^^^^

只有当紧跟 `if`、`for`、`while` 等语句后面的代码真正是单行时，才省略括号：

```c
if (foo)
    do_something();
```

尽管 C 语言不要求括号，但以下情况仍不应视为单行语句：

```c
for (i = 0; i < end; i++)
    if (foo[i])
        do_something(foo[i]);
```

在外层循环周围添加括号可以增强阅读流程：

```c
for (i = 0; i < end; i++) {
    if (foo[i])
        do_something(foo[i]);
}
```

变量声明
^^^^^^^^^^^^^^^^^^^^^

函数开头的变量声明顺序应遵循逆序圣诞树格式：

```c
struct long_struct_name *descriptive_name;
unsigned long foo, bar;
unsigned int tmp;
int ret;
```

以上比反向排序更快解析：

```c
int ret;
unsigned int tmp;
unsigned long foo, bar;
struct long_struct_name *descriptive_name;
```

并且比随机排序更快解析：

```c
unsigned long foo, bar;
int ret;
struct long_struct_name *descriptive_name;
unsigned int tmp;
```

同时，请尝试将相同类型的变量聚合到一行中。没有必要浪费屏幕空间：

```c
unsigned long a;
unsigned long b;
unsigned long c;
unsigned long d;
```

实际上只需这样做即可：

```c
unsigned long a, b, c, d;
```

请勿在变量声明中引入行分割：

```c
struct long_struct_name *descriptive_name = container_of(bar,
                                                         struct long_struct_name,
                                                         member);
struct foobar foo;
```

最好将初始化移到声明后的单独行：

```c
struct long_struct_name *descriptive_name;
struct foobar foo;

descriptive_name = container_of(bar, struct long_struct_name, member);
```

变量类型
^^^^^^^^^^^^^^

对于描述硬件或作为访问硬件函数参数的变量，请使用适当的 `u8`、`u16`、`u32`、`u64` 类型。这些类型明确定义了位宽，并避免了截断、扩展和 32/64 位混淆。

当使用 `unsigned long` 可能导致 32 位内核代码歧义时，也建议使用 `u64`。虽然在这种情况下也可以使用 `unsigned long long`，但 `u64` 更短且明确表示该操作需要在目标 CPU 上为 64 位。

请使用 `unsigned int` 而不是 `unsigned`。

常量
^^^^^^^^^

请不要在代码或初始化器中使用字面 (十六进制) 十进制数字。要么使用具有描述性名称的适当宏定义，要么考虑使用枚举。

结构体声明和初始化
^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^

结构体声明应以表格形式对齐成员名称：

```c
struct bar_order {
    unsigned int   guest_id;
    int            ordered_item;
    struct menu    *menu;
};
```

请避免在声明中记录结构体成员，因为这通常会导致奇怪格式的注释，并使结构体成员变得模糊不清：

```c
struct bar_order {
    unsigned int   guest_id; /* 唯一的客人 ID */
    int            ordered_item;
    /* 指向包含所有饮料的菜单实例 */
    struct menu    *menu;
};
```

相反，请考虑在结构体声明前使用内核文档格式的注释，这样更容易阅读，并且具有将信息包含在内核文档中的附加优势，例如：

```c
/**
 * struct bar_order - 描述酒吧订单
 * @guest_id:       唯一的客人 ID
 * @ordered_item:   菜单上的项目编号
 * @menu:           指向订购项目的菜单
 *
 * 使用该结构体的补充信息
 */
```
```c
/* 
 * 注意，上述的结构体成员描述是按表格形式排列的
 */
struct bar_order {
    unsigned int guest_id;
    int ordered_item;
    struct menu *menu;
};

/* 
 * 静态结构体初始化必须使用C99初始化器，并且也应按表格形式对齐
 */
static struct foo statfoo = {
    .a         = 0,
    .plain_integer = CONSTANT_DEFINE_OR_ENUM,
    .bar       = &statbar,
};

/* 
 * 注意，虽然C99语法允许省略最后一个逗号，但我们建议在最后一行使用逗号，
 * 因为这样使得重新排序和添加新行更容易，同时也使未来的补丁更易于阅读
 */

/* 
 * 行断行
 * ^^^^^^^
 * 将行长度限制在80个字符会使缩进很深的代码难以阅读。
 * 考虑将代码分解成辅助函数以避免过多的行断行。
 * 80个字符的规则并不是严格的规定，因此在断行时请使用常识。
 * 特别是格式字符串不应该被断开。
 * 当拆分行声明或函数调用时，请将第二行的第一个参数与第一行的第一个参数对齐：
 */

static int long_function_name(struct foobar *barfoo, unsigned int id,
                              unsigned int offset)
{
    if (!id) {
        ret = longer_function_name(barfoo, DEFAULT_BARFOO_ID,
                                   offset);
        ..
    }

/* 
 * 命名空间
 * ^^^^^^^
 * 函数/变量命名空间可以提高可读性并便于grep搜索。这些命名空间是全局可见的函数和变量名称的字符串前缀，包括内联函数。这些前缀应该结合子系统和组件名称，例如'x86_comp_'、'sched_'、'irq_'和'mutex_'。
 * 这还包括立即放入全局可见驱动模板中的静态文件作用域函数——对于这些符号来说，拥有一个好的前缀有助于回溯时的可读性。
 * 命名空间前缀可以省略局部静态函数和变量。真正局部的函数，只被其他局部函数调用，可以有较短的描述性名称——我们主要关心的是可grep性和回溯时的可读性。
 * 请注意，对于特定供应商文件中的静态函数，'xxx_vendor_' 和 'vendor_xxx_' 前缀并不有用。毕竟，代码已经是特定供应商的。此外，供应商名称应该仅用于真正特定于供应商的功能。
 * 如常运用常识，并力求一致性和可读性。
 */ 
```
提交通知
--------------------

尖端树（tip tree）由一个机器人监控新提交。对于每个新提交，该机器人会向专用邮件列表（``linux-tip-commits@vger.kernel.org``）发送一封电子邮件，并将所有在提交标签中被提及的人添加为抄送（Cc）。它使用标签列表末尾的Link标签中的电子邮件消息ID来设置In-Reply-To邮件头，以便消息能正确地与补丁提交邮件关联。尖端维护者和子维护者会在合并补丁时尝试回复提交者，但他们有时会忘记或觉得这不符合当时的操作流程。虽然机器人的消息是纯机械性的，但它也意味着“谢谢！已应用。”
