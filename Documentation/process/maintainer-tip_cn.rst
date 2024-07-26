SPDX 许可证标识符: GPL-2.0

尖端树手册
==========

什么是尖端树？
---------------

尖端树是多个子系统和开发领域的集合。尖端树既是直接的开发树，也是多个子维护者树的聚合树。尖端树的 GitWeb URL 为：https://git.kernel.org/pub/scm/linux/kernel/git/tip/tip.git

尖端树包含以下子系统：

- **x86 架构**

  x86 架构的开发在尖端树中进行，但 x86 KVM 和 XEN 的特定部分则在相应的子系统中维护，并直接从那里并入主线。对于与 x86 特定的 KVM 和 XEN 补丁，最好还是抄送给 x86 维护者。
  一些 x86 子系统除了总体 x86 维护者之外还有自己的维护者。请在触及 arch/x86 目录下的文件时抄送给总体 x86 维护者，即使这些文件没有被 MAINTAINER 文件特别指出。
  注意，“x86@kernel.org”并不是一个邮件列表，它只是一个邮件别名，用于将邮件分发给 x86 高层维护者团队。请始终抄送 Linux 内核邮件列表（LKML）"linux-kernel@vger.kernel.org"，否则你的邮件只会进入维护者的私人邮箱。

- **调度器**

  调度器的开发在 -tip 树的 sched/core 分支中进行，有时会为正在进行的工作集建立子主题树。

- **锁定和原子操作**

  锁定开发（包括原子操作和其他与锁定相关的同步原语）在 -tip 树的 locking/core 分支中进行，有时会为正在进行的工作集建立子主题树。

- **通用中断子系统和中断芯片驱动程序**：

  - 中断核心开发在 irq/core 分支中进行。

  - 中断芯片驱动程序的开发也在 irq/core 分支中进行，但补丁通常是在单独的维护者树中应用，然后再聚合到 irq/core 分支中。

- **时间、定时器、时钟同步、NOHZ 及相关芯片驱动程序**：

  - 时钟同步、clocksource 核心、NTP 和 alarmtimer 的开发在 timers/core 分支中进行，但补丁通常是在单独的维护者树中应用，然后聚合到 timers/core 分支中。

  - clocksource/event 驱动程序的开发在 timers/core 分支中进行，但补丁大多是在单独的维护者树中应用，然后聚合到 timers/core 分支中。

- **性能计数器核心、架构支持和工具**：

  - perf 核心和架构支持的开发在 perf/core 分支中进行。

  - perf 工具的开发在 perf 工具维护者树中进行，并聚合到尖端树中。

- **CPU 热插拔核心**

- **RAS 核心**

  大部分与 x86 特定的 RAS 补丁收集在尖端树的 ras/core 分支中。

- **EFI 核心**

  EFI 的开发在 efi Git 树中进行。收集的补丁被聚合在尖端树的 efi/core 分支中。

- **RCU**

  RCU 的开发在 linux-rcu 树中进行。产生的更改被聚合到尖端树的 core/rcu 分支中。

- **各种核心代码组件**：

  - debugobjects

  - objtool

  - 各种零碎的部分

提交补丁的注意事项
--------------------

选择树/分支
^^^^^^^^^^^^^^^^^^^^^^^^^

一般来说，在尖端树主分支的头部进行开发是可以的，但对于那些单独维护、有自己的 Git 树并仅聚合到尖端树中的子系统，开发应当针对相关的子系统树或分支进行。
### 错误修复

针对主线的目标错误修复应当适用于主线内核树。对于已经在tip树中排队的更改可能产生的冲突，由维护者处理。

### 补丁主题
^^^^^^^^^^^^^

补丁主题前缀在tip树中的首选格式是`子系统/组件:`, 例如 `x86/apic:`, `x86/mm/fault:`, `sched/fair:`, `genirq/core:`。请不要使用文件名或完整的文件路径作为前缀。在大多数情况下，“git log path/to/file”应该能给出一个合理的提示。

主题行中的精简补丁描述应以大写字母开头，并用命令式语气书写。

### 变更日志
^^^^^^^^^

关于变更日志的一般规则，在《提交补丁指南》(:ref:`Submitting patches guide <describe_changes>`)中适用。

tip树的维护者重视遵循这些规则，特别是要求以命令式语气编写变更日志和避免将代码或其执行过程拟人化的要求。这不仅仅是维护者的个人喜好。用抽象语言编写的变更日志更为精确，通常也比小说形式的变更日志更不容易引起混淆。

将变更日志结构化为几个段落也是有用的，而不是将所有内容都挤在一个段落里。一个好的结构是分别在不同的段落中解释上下文、问题和解决方案，并按此顺序排列。

### 示例说明

**示例 1：**

```
x86/intel_rdt/mbm: 在热插拔CPU期间修复MBM溢出处理器

当一个CPU即将失效时，我们取消工作程序并在同一域的不同CPU上调度一个新的工作程序。但如果定时器几乎就要过期（比如0.99秒），那么实际上就将间隔加倍了。
我们修改了热插拔CPU处理方式，取消即将失效CPU上的延迟工作，并立即在同一域的另一个CPU上运行工作程序。我们不刷新工作程序，因为MBM溢出工作程序会在同一CPU上重新调度工作程序，并扫描域->cpu_mask以获取域指针。
```

**改进版本：**

```
x86/intel_rdt/mbm: 在CPU热插拔期间修复MBM溢出处理器

当一个CPU即将失效时，溢出工作程序被取消并在同一域的不同CPU上重新调度。但如果定时器几乎就要过期，则实际上会将间隔加倍，可能导致未检测到的溢出。
取消溢出工作程序并立即在同一域的不同CPU上重新调度它。工作程序也可以被刷新，但这会导致在同一CPU上重新调度它。
```
### 示例 2:

**时间：POSIX CPU 定时器：确保变量已初始化**

如果 `cpu_timer_sample_group` 返回 `-EINVAL`，它将不会写入 `*sample`。检查 `cpu_timer_sample_group` 的返回值避免了后续代码块中可能使用未初始化的 `now` 变量。

给定一个无效的 `clock_idx`，之前的代码可能会以未定义的方式覆盖 `*oldval`。现在这种情况已被阻止。我们还利用 `&&` 的短路特性仅在结果实际用于更新 `*oldval` 时才采样定时器。

**改进版本：**

**POSIX-CPU-定时器：使 `set_process_cpu_timer()` 更健壮**

由于没有检查 `cpu_timer_sample_group()` 的返回值，编译器和静态检查工具可以合法地警告潜在使用未初始化的变量 `now`。这不是运行时问题，因为所有调用点都传入有效的时钟 ID。

还无条件调用了 `cpu_timer_sample_group()`，即使结果没有被使用（因为 `*oldval` 是 `NULL`）。

让调用条件化并检查返回值。

### 示例 3：

**实体还可以用于其他目的**

让我们将其重命名以更具通用性。

**改进版本：**

**实体还可以用于其他目的**

重命名以更具通用性

对于复杂的场景，特别是竞态条件和内存排序问题，通过表格描绘这些场景来展示并发性和事件的时间顺序是非常有价值的。以下是一个例子：

| **CPU0**                           | **CPU1** |
|------------------------------------|-----------------------------------|
| `free_irq(X)`                      | `interrupt X`                     |
|                                     | `spin_lock(desc->lock)`           |
|                                     | `wake irq thread()`               |
|                                     | `spin_unlock(desc->lock)`         |
| `spin_lock(desc->lock)`            |                                   |
| `remove action()`                  |                                   |
| `shutdown_irq()`                   |                                   |
| `release_resources()`              | `thread_handler()`                |
| `spin_unlock(desc->lock)`          |     `access released resources`   |

这里展示了两个 CPU 核心之间的交互，包括中断处理、锁的获取与释放以及资源释放的过程。
### 同步中断

`synchronize_irq()` 

Lockdep 提供了类似的有用输出来描绘一个可能的死锁场景：

    **CPU0**                                      **CPU1**
    rtmutex_lock(&rcu->rt_mutex)
      spin_lock(&rcu->rt_mutex.wait_lock)
                                            local_irq_disable()
                                            spin_lock(&timer->it_lock)
                                            spin_lock(&rcu->mutex.wait_lock)
    --> **中断**
        spin_lock(&timer->it_lock)

### 变更日志中的函数引用
当在变更日志中提及一个函数，无论是正文还是主题行，请使用格式 `function_name()`。省略函数名后的括号可能会导致歧义：

  **主题：** subsys/component: 将 reservation_count 设置为静态

  reservation_count 只在 reservation_stats 中使用。将其设置为静态。

使用括号的变体更加精确：

  **主题：** subsys/component: 将 reservation_count() 设置为静态

  reservation_count() 只从 reservation_stats() 被调用。将其设置为静态。

### 变更日志中的回溯信息
参见 :ref:`回溯信息`

### 提交标签的顺序
为了使提交标签的视图统一，维护者们采用以下标签排序方案：

- **Fixes:** 12字符-SHA1 ("sub/sys: 原始主题行")

  即使对于不需要回退到稳定内核的变化，也应该添加一个 Fixes 标签，即当解决的问题是最近引入且仅影响 tip 或主线当前版本时。这些标签有助于识别原始提交，并且比在变更日志正文中突出提及引入问题的提交更有价值，因为它们可以被自动提取。
下面的例子说明了这种差异：

     **提交**

       abcdef012345678 ("x86/xxx: 将 foo 替换为 bar")

     留下了一个未使用的 foo 变量实例。移除它
签署确认：J.Dev <j.dev@mail>

   请改为这样表述：

     最近将 foo 替换为 bar 的操作留下了一个未使用的 foo 变量实例。移除它
Fixes: abcdef012345678 ("x86/xxx: 将 foo 替换为 bar")
     签署确认：J.Dev <j.dev@mail>

   这种方式将关于补丁的信息放在焦点位置，并通过指向引入问题的提交来补充信息，而不是一开始就将焦点放在原始提交上。

- **Reported-by:** ``报告者 <reporter@mail>``
  
- **Closes:** ``此修复所对应的 bug 报告的 URL 或消息 ID``
  
- **Originally-by:** ``原始作者 <original-author@mail>``
  
- **Suggested-by:** ``建议者 <suggester@mail>``
  
- **Co-developed-by:** ``共同作者 <co-author@mail>``

   签署确认：``共同作者 <co-author@mail>``

   注意，共同开发者和共同作者的签署确认必须成对出现。
- **Signed-off-by:** ``作者 <author@mail>``

   第一个在最后一个共同开发者/签署确认对之后的签署确认（SOB）是作者的签署确认，即由 git 标记为作者的人。
- **Signed-off-by:** ``补丁处理者 <handler@mail>``

   在作者签署确认之后的签署确认来自处理并传递补丁的人，但并未参与开发。认可应该以 Acked-by 的形式给出，审查批准应以 Reviewed-by 的形式给出。
如果处理者对补丁或变更日志进行了修改，则应在**变更日志文本之后**和**所有提交标签之上**以以下格式提及这些修改：

```
... 变更日志文本结束
[ 处理者: 用 bar 替换了 foo 并更新了变更日志 ]

     第一个标签: ....
请注意，这两行空行将变更日志文本和提交标签与该通知分隔开来。
如果一个补丁由处理者发送到邮件列表，则作者必须在变更日志的第一行中注明，例如：

     From: 作者 <author@mail>

     变更日志文本从这里开始...
这样可以保留作者信息。'From:'行后面必须跟着一个空的新行。如果缺少这个'From:'行，则该补丁将被归因于发送（传输、处理）它的人。
'From:'行在应用补丁时会被自动移除，并不会出现在最终的git变更日志中。它仅影响结果Git提交的作者信息。
- 测试者: ``测试者 <tester@mail>``

 - 审阅者: ``审阅者 <reviewer@mail>``

 - 确认者: ``确认者 <acker@mail>``

 - 抄送: ``抄送人 <person@mail>``

   如果补丁需要回退到稳定版本，请添加一个'``Cc: stable@vger.kernel.org``'标签，但在发送邮件时不要Cc稳定版本。
- 链接: ``https://link/to/information``

   若要引用发送到内核邮件列表的电子邮件，请使用lore.kernel.org重定向URL，例如：

     链接: https://lore.kernel.org/email-message-id@here

   当引用相关的邮件列表主题、相关补丁集或其他值得注意的讨论线程时，应使用此URL。
一种方便的方法是使用类似markdown的括号标记法来将``链接:``拖尾与提交消息关联起来，例如：

     之前曾尝试过类似的方法作为另一项努力的一部分 [1]，但最初的实现导致了太多的问题 [2]，因此我们撤销了这一改动并重新实现了它。
链接: https://lore.kernel.org/some-msgid@here # [1]
     链接: https://bugzilla.example.org/bug/12345  # [2]

   在将补丁应用到您的git仓库时，您也可以使用``链接:``拖尾来表明补丁的来源。在这种情况下，请使用专门的``patch.msgid.link``域名，而不是``lore.kernel.org``。```
这种做法使得自动化工具能够识别出哪个链接用于检索原始补丁提交。例如：

     链接: https://patch.msgid.link/patch-source-message-id@here

请不要使用组合标签，例如 ``Reported-and-tested-by``，因为它们只会使标签的自动化提取变得复杂。
链接到文档
^^^^^^^^^^^^^^^^^^^^^^

在更改日志中提供指向文档的链接对于后续的调试和分析非常有帮助。不幸的是，URL往往很快就失效了，因为公司会频繁地重组他们的网站。例外情况是非“易变”的文档，如英特尔软件开发人员手册（Intel SDM）和AMD平台手册（AMD APM）。
因此，对于“易变”的文档，请在内核Bugzilla (https://bugzilla.kernel.org) 中创建一个条目，并将这些文档的副本附加到Bugzilla条目中。最后，在更改日志中提供Bugzilla条目的URL。
补丁重发或提醒
^^^^^^^^^^^^^^^^^^^^^^^^^

参见 :ref:`resend_reminders`
合并窗口
^^^^^^^^^^^^

请不要期望在合并窗口前后或期间，尖端（tip）维护者会审查或合并补丁。在此期间，除了紧急修复外，所有分支都关闭。一旦合并窗口关闭并发布了新的-rc1内核版本后，它们才会重新开放。
大型系列应该至少在合并窗口开启前一周以可合并的状态提交。对于错误修复以及有时针对新硬件的小型独立驱动程序或对硬件启用影响最小的补丁，则可以作为例外处理。
在合并窗口期间，维护者们会专注于追踪上游的变化、解决合并窗口带来的问题、收集错误修复，并给自己留一些喘息的时间。请对此表示尊重。
所谓的_紧急_分支将在每个发布周期的稳定阶段被合并进主线。
Git
^^^

尖端维护者接受来自提供子系统变更以汇总至尖端树的维护者的Git拉取请求。
对于新的补丁提交，通常不会接受拉取请求，并且这不能替代通过邮件列表进行正确的补丁提交。主要原因是审查流程基于电子邮件。
如果你提交一个较大的补丁系列，提供一个私有仓库中的 Git 分支会很有帮助，这样感兴趣的人可以轻松地拉取该系列进行测试。通常提供这种方式的方法是在补丁系列的封面信中包含一个 Git URL。

**测试**

在向维护者提交代码之前应该对代码进行测试。除了微小的改动之外，任何改动都应该构建、启动，并使用全面（且重量级）的内核调试选项进行测试。
这些调试选项可以在 `kernel/configs/x86_debug.config` 中找到，并可以通过运行以下命令添加到现有的内核配置中：

```bash
make x86_debug.config
```

其中一些选项是针对 x86 架构特定的，在其他架构上测试时可以忽略这些选项。

### 编码风格注意事项

#### 注释风格

- 注释中的句子以大写字母开头
- 单行注释：

  ```c
  /* 这是一个单行注释 */
  ```

- 多行注释：

  ```c
  /*
   * 这是一个格式正确的
   * 多行注释
  *
   * 较大的多行注释应分为段落
  */
  ```

- 不要使用尾注（参见下文）：

  请不要使用尾注。尾注几乎在所有上下文中都会干扰阅读流程，特别是在代码中：

  ```c
  if (somecondition_is_true) /* 不要在这种地方放置注释 */
      dostuff(); /* 也不要在这种地方放置注释 */

  seed = MAGIC_CONSTANT; /* 也不要在这里放注释 */
  ```

  而是使用独立的注释：

  ```c
  /* 如果没有注释这个条件可能不是很明显 */
  if (somecondition_is_true) {
      /* 这确实需要被记录下来 */
      dostuff();
  }

  /* 这种神奇的初始化需要注释。也许不需要？ */
  seed = MAGIC_CONSTANT;
  ```

  在头文件中使用 C++ 风格的尾注来记录结构体，以实现更紧凑的布局和更好的可读性：

  ```c
  // eax
  u32     x2apic_shift    :  5, // 将 APIC ID 向右移位的位数，用于下一级的拓扑ID
                              // 对于当前层级的处理器数量
                            : 27; // 保留

  // ebx
  u32     num_processors  : 16, // 当前层级的处理器数量
                            : 16; // 保留
  ```

  而不是：

  ```c
  /* eax */
          /*
           * 将 APIC ID 向右移位的位数，用于下一级的拓扑ID
           */
   u32     x2apic_shift    :  5,
           /* 保留 */
                     : 27;

  /* ebx */
   /* 当前层级的处理器数量 */
  u32     num_processors  : 16,
          /* 保留 */
                  : 16;
  ```

- 注释重要的事情：

  应在操作不明显的地方添加注释。记录显而易见的操作只会造成干扰：

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

  相反，注释应该解释不明显的细节，并记录约束：

  ```c
  if (refcount_dec_and_test(&p->refcnt)) {
      /*
       * 切实好的解释为什么下面的神奇操作必须完成，
       * 排序和锁定约束等。
      */
      do;
      lots;
      of;
      magic;
      /* 必须是最后一个操作，因为... */
      things;
  }
  ```

- 函数文档注释：

  为了记录函数及其参数，请使用 kernel-doc 格式，而不是自由形式的注释：

  ```c
  /**
   * magic_function - 做大量的神奇事情
   * @magic: 操作的神奇数据指针
   * @offset: @magic 数据数组中的偏移量
   *
   * 使用 @magic 执行神秘操作的深入解释
   * 以及返回值的文档
   *
   * 注意，上面的参数描述是表格形式排列的
   */
  ```

  这尤其适用于全局可见的函数和公共头文件中的内联函数。对于每个（静态）函数来说，如果只需要简短的解释，使用 kernel-doc 格式可能会有些过分。使用描述性的函数名称通常可以取代这些简短的注释。
始终运用常识  
记录锁要求  
^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^  

记录锁要求是一件好事，但注释不一定是最佳选择。请不要写成这样：  

	/* 调用者必须持有 foo->lock 锁 */
	void func(struct foo *foo)
	{
		..
	}

而应该写成这样：  

	void func(struct foo *foo)
	{
		lockdep_assert_held(&foo->lock);
		..
	}

在 PROVE_LOCKING 内核中，如果调用者没有持有锁，`lockdep_assert_held()` 会发出警告。注释做不到这一点。  
括号规则  
^^^^^^^^^^^^^  

只有当跟随 `if`, `for`, `while` 等的语句确实是单行时，才省略括号：  

	if (foo)
		do_something();

以下情况即使 C 语言不需要括号，也不被认为是单行语句：  

	for (i = 0; i < end; i++)
		if (foo[i])
			do_something(foo[i]);

在外层循环周围添加括号可以增强阅读流程：  

	for (i = 0; i < end; i++) {
		if (foo[i])
			do_something(foo[i]);
	}

变量声明  
^^^^^^^^^^^^^^^^^^^^^  

函数开始处变量声明的首选顺序是逆序松树形式：  

	struct long_struct_name *descriptive_name;
	unsigned long foo, bar;
	unsigned int tmp;
	int ret;

以上比反向顺序更快解析：  

	int ret;
	unsigned int tmp;
	unsigned long foo, bar;
	struct long_struct_name *descriptive_name;

也远比随机顺序更快解析：  

	unsigned long foo, bar;
	int ret;
	struct long_struct_name *descriptive_name;
	unsigned int tmp;

同时，请尽量将同一类型的变量聚合到一行。没有必要浪费屏幕空间：  

	unsigned long a;
	unsigned long b;
	unsigned long c;
	unsigned long d;

实际上这样做就足够了：  

	unsigned long a, b, c, d;

同时请避免在变量声明中引入行分割：  

	struct long_struct_name *descriptive_name = container_of(bar,
						      struct long_struct_name,
	                                              member);
	struct foobar foo;

最好是在声明之后将初始化移动到单独的一行：  

	struct long_struct_name *descriptive_name;
	struct foobar foo;

	descriptive_name = container_of(bar, struct long_struct_name, member);

变量类型  
^^^^^^^^^^^^^^  

对于描述硬件或作为访问硬件功能参数的变量，请使用正确的 u8, u16, u32, u64 类型。这些类型清晰地定义了位宽，并且避免了截断、扩展和 32/64 位混淆的问题。
u64 也被推荐用于代码中，当使用 'unsigned long' 可能会使 32 位内核变得模糊不清时。在这种情况下，虽然也可以使用 'unsigned long long'，但 u64 更短，并且明确显示操作需要独立于目标 CPU 的 64 位宽度。
请使用 'unsigned int' 而不是 'unsigned'。  
常量  
^^^^^^^^^  

请不要在代码或初始化器中使用字面的十进制或十六进制数字。  
要么使用具有描述性名称的适当定义，要么考虑使用枚举。  
结构体声明与初始化  
^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^  

结构体声明应以表格方式对齐结构体成员名称：  

	struct bar_order {
		unsigned int	guest_id;
		int		ordered_item;
		struct menu	*menu;
	};

请避免在声明中记录结构体成员，因为这通常会导致格式奇怪的注释，并使结构体成员变得模糊不清：  

	struct bar_order {
		unsigned int	guest_id; /* 唯一的客人 ID */
		int		ordered_item;
		/* 指向包含所有饮品的菜单实例 */
		struct menu	*menu;
	};

相反，请考虑在结构体声明前的注释中使用 kernel-doc 格式，这样更易于阅读，并且具有额外的好处，即可以将信息包含在内核文档中，例如：  

	/**
	 * struct bar_order - 酒吧订单描述
	 * @guest_id:		唯一的客人 ID
	 * @ordered_item:	从菜单上点的项目编号
	 * @menu:		指向所点项目的菜单
	 *
	 * 使用该结构体的补充信息
	 */
请注意，上述的结构体成员描述是以表格形式排列的。

```c
struct bar_order {
    unsigned int guest_id;   // 客户ID
    int ordered_item;        // 订单项目
    struct menu *menu;       // 菜单指针
};
```

静态结构体初始化必须使用C99初始化语法，并且也应该以表格形式对齐：

```c
static struct foo statfoo = {
    .a         = 0,
    .plain_integer = CONSTANT_DEFINE_OR_ENUM,
    .bar       = &statbar,
};
```

请注意，尽管C99语法允许省略最后一个逗号，但我们建议在最后一行使用逗号，因为这样做可以使得重排和添加新行更加容易，并且也使得将来的补丁更容易阅读。

**换行**
^^^^^^^^^^^

限制每行长度为80个字符会使深度缩进的代码难以阅读。考虑将代码分解到辅助函数中以避免过多的换行。
80个字符的规则不是严格的规则，请在换行时使用常识。特别是格式字符串不应该被分割。
当分割函数声明或函数调用时，请将第二行的第一个参数与第一行的第一个参数对齐：

```c
static int long_function_name(struct foobar *barfoo, unsigned int id,
                              unsigned int offset)
{
    if (!id) {
        ret = longer_function_name(barfoo, DEFAULT_BARFOO_ID,
                                   offset);
        ..
```

**命名空间**
^^^^^^^^^^

函数/变量命名空间提高了可读性并允许方便地进行grep搜索。这些命名空间是全局可见的函数和变量名称（包括内联函数）的字符串前缀，如'x86_comp_'、'sched_'、'irq_'和'mutex_'。
这也包括立即放入全局可见的驱动模板中的静态文件作用域函数——对于回溯可读性而言，这些符号携带一个好的前缀也是有用的。
命名空间前缀可以省略用于局部静态函数和变量。真正局部的函数，只被其他局部函数调用，可以有较短的描述性名称——我们的主要关注点在于grep搜索能力和回溯可读性。
请注意，'xxx_vendor_' 和 'vendor_xxx_' 前缀对于特定供应商文件中的静态函数没有帮助。毕竟，代码本身就是特定于供应商的。此外，供应商名称只应用于真正特定于供应商的功能。
始终应用常识并力求一致性和可读性。
提交通知
------------

提示树（tip tree）由一个机器人监控新的提交。对于每个新提交，该机器人会向专门的邮件列表（``linux-tip-commits@vger.kernel.org``）发送一封电子邮件，并将所有在提交标签中被提及的人作为抄送对象。它使用链接标签末尾处的电子邮件消息ID来设置“回复至”（In-Reply-To）电子邮件头，以便消息能与提交补丁的电子邮件正确地关联起来。
提示维护者和子维护者尝试在合并补丁时回复提交者，但他们有时会忘记或这不符合当时的操作流程。虽然机器人的消息完全是机械性的，但它也意味着一种“谢谢！已应用。”的信息。
