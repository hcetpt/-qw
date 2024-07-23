SPDX 许可证标识符：GPL-2.0

.. _kfuncs-header-label:

=============================
BPF 内核函数（kfuncs）
=============================

1. 引言
===============

BPF 内核函数，更常见地被称为 kfuncs，是 Linux 内核中的函数，这些函数被公开供 BPF 程序使用。与普通的 BPF 辅助函数不同，kfuncs 没有稳定的接口，并且可以从一个内核版本到另一个版本发生变化。因此，BPF 程序需要根据内核的变化进行更新。更多信息请参阅 :ref:`BPF_kfunc_lifecycle_expectations`
2. 定义 kfunc
===================

将内核函数暴露给 BPF 程序有两种方式，一种是使内核中已存在的函数可见，另一种是为 BPF 添加一个新的包装器函数。在这两种情况下，都必须注意确保 BPF 程序只能在有效上下文中调用此类函数。为了强制执行这一点，kfunc 的可见性可以按程序类型设置。
如果你不是在为现有的内核函数创建 BPF 包装器，请跳过至 :ref:`BPF_kfunc_nodef`
2.1 创建 kfunc 包装器
----------------------------

在定义 kfunc 包装器时，包装器函数应具有外部链接性
这可以防止编译器优化掉死代码，因为这个包装器 kfunc 在内核自身中并未被调用。为包装器 kfunc 提供原型声明的头文件并不是必需的
下面给出一个例子：

        /* 禁止缺失原型警告 */
        __bpf_kfunc_start_defs();

        __bpf_kfunc struct task_struct *bpf_find_get_task_by_vpid(pid_t nr)
        {
                return find_get_task_by_vpid(nr);
        }

        __bpf_kfunc_end_defs();

当我们需要对 kfunc 参数进行注释时，通常需要创建一个包装器 kfunc。否则，可以直接通过向 BPF 子系统注册 kfunc 使其对 BPF 程序可见。详情见 :ref:`BPF_kfunc_nodef`
2.2 对 kfunc 参数进行注释
-------------------------------

与 BPF 辅助函数类似，有时需要额外的上下文信息来帮助验证器使内核函数的使用更加安全和有用
因此，我们可以通过在 kfunc 参数名称后加上一个 __tag 后缀来注释参数，其中 tag 可能是支持的注释之一
2.2.1 __sz 注释
---------------------

此注释用于指示参数列表中的内存和大小对
下面给出一个例子：

        __bpf_kfunc void bpf_memzero(void *mem, int mem__sz)
        {
        ..
### 2.2.1 `__sz` 注解

在这里，验证器会将第一个参数视为一个`PTR_TO_MEM`（指向内存的指针），而第二个参数则被视为该指针所指向内存区域的大小。默认情况下，如果没有使用`__sz`注解，那么将采用指针类型本身的大小作为其大小。没有`__sz`注解的情况下，`kfunc`无法接受`void`类型的指针。

### 2.2.2 `__k` 注解

-------------------

此注解仅适用于标量参数，它指示验证器必须检查标量参数是否为已知常数，且该常数不表示大小参数，常数值对程序的安全性有重要影响。

下面是一个例子：

```c
__bpf_kfunc void *bpf_obj_new(u32 local_type_id__k, ...)
{
    ...
}
```

在此例中，`bpf_obj_new` 使用`local_type_id` 参数来查找程序BTF中的该类型ID的大小，并返回指向该大小的指针。每个类型ID都有其独特的大小，因此在验证器状态修剪检查过程中，当值不匹配时，将每次调用视为独立的处理至关重要。

因此，每当`kfunc` 接收一个非大小参数的常数标量参数，且该常数值对于程序安全性至关重要时，应使用`__k`后缀。

### 2.2.3 `__uninit` 注解

----------------------

此注解用于表明参数应被视为未初始化的。

下面是一个例子：

```c
__bpf_kfunc int bpf_dynptr_from_skb(..., struct bpf_dynptr_kern *ptr__uninit)
{
    ...
}
```

这里，`dynptr` 将被视为未初始化的`dynptr`。如果没有这个注解，如果传递给函数的`dynptr`未被初始化，验证器将拒绝执行该程序。

### 2.2.4 `__opt` 注解

----------------------

此注解用于指示与`__sz`或`__szk`参数关联的缓冲区可能为`null`。如果函数接收到`nullptr`代替缓冲区，验证器不会检查长度是否适合于缓冲区。`kfunc`负责在使用前检查此缓冲区是否为`null`。

下面是一个例子：

```c
__bpf_kfunc void *bpf_dynptr_slice(..., void *buffer__opt, u32 buffer__szk)
{
    ...
}
```
### 缓冲区注解

此处，缓冲区可能为null。如果缓冲区不为null，则其大小至少为buffer_szk。无论如何，返回的缓冲区要么是NULL，要么大小为buffer_szk。没有这个注解，验证器会在非零大小与空指针一同传入时拒绝程序。

#### `__str` 注解

此注解用于指示参数是一个常量字符串。下面给出了一个示例：

```c
__bpf_kfunc bpf_get_file_xattr(..., const char *name__str, ...)
{
    ...
}
```

在这种情况下，`bpf_get_file_xattr()` 可以这样调用：

```c
bpf_get_file_xattr(..., "xattr_name", ...);
```

或者：

```c
const char name[] = "xattr_name";  /* 这需要是全局的 */
int BPF_PROG(...)
{
    ...
    bpf_get_file_xattr(..., name, ...);
    ...
}
```

### 使用现有的内核函数

当现有内核中的函数适合被BPF程序使用时，可以直接注册到BPF子系统中。然而，仍需谨慎审查BPF程序调用该函数的上下文以及是否安全进行调用。

### 注解kfuncs

除了kfuncs的参数外，验证器可能还需要关于注册给BPF子系统的kfunc类型的更多信息。为此，我们定义了如下的一系列kfuncs的标志：

```c
BTF_KFUNCS_START(bpf_task_set)
BTF_ID_FLAGS(func, bpf_get_task_pid, KF_ACQUIRE | KF_RET_NULL)
BTF_ID_FLAGS(func, bpf_put_pid, KF_RELEASE)
BTF_KFUNCS_END(bpf_task_set)
```

这组设置编码了上述列出的每个kfunc的BTF ID，并且与其一起编码了标志。当然，也可以指定无标志。kfunc定义也应该始终使用`__bpf_kfunc`宏进行注解。这可以防止诸如编译器将kfunc内联（如果它是静态内核函数）或在LTO构建中由于在内核其他部分未使用而被省略等问题。开发人员不应手动添加注解来避免这些问题。如果需要注解来阻止你的kfunc出现此类问题，那是一个bug，应该添加到宏的定义中，以便其他kfuncs也得到类似保护。下面给出一个示例：

```c
__bpf_kfunc struct task_struct *bpf_get_task_pid(s32 pid)
{
    ...
}
```

#### KF_ACQUIRE 标志

KF_ACQUIRE标志用于指示kfunc返回一个指向引用计数对象的指针。然后，验证器将确保使用释放kfunc最终释放对象的指针，或者使用引用kptr通过调用bpf_kptr_xchg将其转移到map中。如果不这样做，验证器会在所有可能探索的程序状态中不再存在悬留引用之前失败加载BPF程序。
2.4.2 KF_RET_NULL 标志
----------------------

KF_RET_NULL 标志用于指示由 kfunc 返回的指针可能为 NULL。因此，它强制用户在使用该指针（解引用或传递给另一个辅助函数）之前对从 kfunc 返回的指针进行 NULL 检查。此标志通常与 KF_ACQUIRE 标志一起使用，但两者是相互独立的。

2.4.3 KF_RELEASE 标志
---------------------

KF_RELEASE 标志用于指示 kfunc 释放传入的指针。只能传递一个被引用的指针。所有要释放的指针的副本在调用带有此标志的 kfunc 后将失效。KF_RELEASE kfuncs 自动获得下面描述的 KF_TRUSTED_ARGS 标志所提供的保护。

2.4.4 KF_TRUSTED_ARGS 标志
--------------------------

KF_TRUSTED_ARGS 标志用于 kfuncs 接受指针参数的情况。它表明所有指针参数都是有效的，并且所有指向 BTF 对象的指针都以未修改的形式传递（即，在零偏移量处，且没有通过遍历另一个指针获得，下面有一个例外）。
有两种类型的指向内核对象的指针被认为是“有效”的：

1. 作为跟踪点或 struct_ops 回调参数传递的指针
2. 从 KF_ACQUIRE kfunc 返回的指针
指向非 BTF 对象（例如标量指针）的指针也可以传递给 KF_TRUSTED_ARGS kfuncs，并且可以有非零偏移量。
“有效”指针的定义随时可能会改变，并且完全没有 ABI 稳定性保证。
如上所述，从遍历可信指针获得的嵌套指针不再可信，但有一个例外。如果一个结构类型有一个字段，只要其父指针有效，该字段就保证有效（可信或 rcu，如下文中的 KF_RCU 描述），以下宏可用于向验证器表达这一点：

* ``BTF_TYPE_SAFE_TRUSTED``
* ``BTF_TYPE_SAFE_RCU``
* ``BTF_TYPE_SAFE_RCU_OR_NULL``

例如，

.. code-block:: c

    BTF_TYPE_SAFE_TRUSTED(struct socket) {
        struct sock *sk;
    };

或者

.. code-block:: c

    BTF_TYPE_SAFE_RCU(struct task_struct) {
        const cpumask_t *cpus_ptr;
        struct css_set __rcu *cgroups;
        struct task_struct __rcu *real_parent;
        struct task_struct *group_leader;
    };

换句话说，你必须：

1. 使用 ``BTF_TYPE_SAFE_*`` 宏包装有效的指针类型
2. 指定有效嵌套字段的类型和名称。这个字段必须与原始类型定义中的字段完全匹配
由 ``BTF_TYPE_SAFE_*`` 宏声明的新类型也需要被发出，以便出现在 BTF 中。例如，``BTF_TYPE_SAFE_TRUSTED(struct socket)`` 在 ``type_is_trusted()`` 函数中按如下方式发出：

.. code-block:: c

    BTF_TYPE_EMIT(BTF_TYPE_SAFE_TRUSTED(struct socket));

2.4.5 KF_SLEEPABLE 标志
-----------------------

KF_SLEEPABLE 标志用于可能休眠的 kfuncs。此类 kfuncs 只能由可休眠的 BPF 程序（BPF_F_SLEEPABLE）调用。
### 2.4.6 KF_DESTRUCTIVE 标志

KF_DESTRUCTIVE 标志用于指示对系统具有破坏性的函数调用。例如，这样的调用可能导致系统重启或崩溃。因此，这些调用受到额外的限制。目前，它们仅要求具备CAP_SYS_BOOT权限，但将来可能会增加更多限制。

### 2.4.7 KF_RCU 标志

KF_RCU 标志是KF_TRUSTED_ARGS 的较弱版本。标记为 KF_RCU 的 kfuncs 预期接收 PTR_TRUSTED 或 MEM_RCU 参数。验证器保证对象有效且不存在使用后释放的问题。指针不为空，但对象的引用计数可能已降至零。kfuncs 需要考虑进行 refcnt != 0 的检查，特别是在返回 KF_ACQUIRE 指针时。同样需要注意的是，如果一个 KF_RCU 的 KF_ACQUIRE kfunc 很可能也应该是 KF_RET_NULL。

### 2.4.8 KF_DEPRECATED 标志

KF_DEPRECATED 标志用于标记计划在后续内核版本中更改或移除的 kfuncs。被标记为 KF_DEPRECATED 的 kfunc 应该在其内核文档中捕获任何相关信息。此类信息通常包括 kfunc 的预期剩余寿命、可替代的新功能推荐（如果有的话），以及移除它的理由。
值得注意的是，在某些情况下，KF_DEPRECATED kfunc 可能会继续得到支持，并且其 KF_DEPRECATED 标志会被移除，但这很可能比一开始就防止添加该标志要困难得多。如 :ref:`BPF_kfunc_lifecycle_expectations` 中所述，依赖特定 kfuncs 的用户应尽早让自己的使用案例为人所知，并参与关于保留、更改、废弃或移除这些 kfuncs 的上游讨论，如果此类讨论发生的话。

### 2.5 注册 kfuncs

一旦 kfunc 准备就绪，使其可见的最后一步就是将其注册到 BPF 子系统中。注册按 BPF 程序类型进行。下面是一个示例：

```c
BTF_KFUNCS_START(bpf_task_set)
BTF_ID_FLAGS(func, bpf_get_task_pid, KF_ACQUIRE | KF_RET_NULL)
BTF_ID_FLAGS(func, bpf_put_pid, KF_RELEASE)
BTF_KFUNCS_END(bpf_task_set)

static const struct btf_kfunc_id_set bpf_task_kfunc_set = {
        .owner = THIS_MODULE,
        .set   = &bpf_task_set,
};

static int init_subsystem(void)
{
        return register_btf_kfunc_id_set(BPF_PROG_TYPE_TRACING, &bpf_task_kfunc_set);
}
late_initcall(init_subsystem);
```

### 2.6 使用 ___init 指定无转换别名

验证器将始终强制执行 BPF 程序传递给 kfunc 的指针的 BTF 类型与 kfunc 定义中指定的指针类型相匹配。然而，验证器确实允许根据 C 标准等效的类型被传递给同一 kfunc 参数，即使它们的 BTF_ID 不同。
例如，对于以下类型定义：

```c
struct bpf_cpumask {
    cpumask_t cpumask;
    refcount_t usage;
};
```

验证器将允许 `struct bpf_cpumask *` 被传递给接受 `cpumask_t *` （这是 `struct cpumask *` 的类型定义）的 kfunc。例如，`struct cpumask *` 和 `struct bpf_cpumask *` 都可以传递给 bpf_cpumask_test_cpu()。
在某些情况下，这种类型别名行为是不需要的。`struct nf_conn___init` 就是这样一个例子：

```c
struct nf_conn___init {
    struct nf_conn ct;
};
```

C 标准认为这些类型是等价的，但在某些情况下，将任一类型传递给可信的 kfunc 并不总是安全的。`struct nf_conn___init` 表示一个已经分配但尚未初始化的 `struct nf_conn` 对象，因此将其 `struct nf_conn___init *` 传递给期望完全初始化的 `struct nf_conn *`（如 `bpf_ct_change_timeout()`）的 kfunc 是不安全的。
为了满足此类需求，如果两个类型具有完全相同的名字，其中一个以 `___init` 结尾，验证器将强制执行严格的 PTR_TO_BTF_ID 类型匹配。

### 3. kfunc 生命周期期望值

kfuncs 提供了一个内核 <-> 内核 API，因此不受任何与内核 <-> 用户 UAPI 相关的严格稳定性限制。这意味着它们可以被视为类似于 EXPORT_SYMBOL_GPL，并且当被认为必要时，定义它们的子系统维护者可以修改或删除它们。
就像内核中的任何其他更改一样，维护者不会在没有合理理由的情况下更改或删除 kfunc。他们是否选择更改 kfunc 最终取决于多种因素，比如 kfunc 的广泛使用程度、kfunc 在内核中存在的时间长度、是否存在替代 kfunc、对于所涉及子系统的稳定性规范是什么，当然还有继续支持 kfunc 的技术成本。
以下是给定英文文本的中文翻译：

这有几个含义：

a）被广泛使用或在内核中存在很长时间的kfuncs（内核函数），维护者更改或移除它们的理由将更难以成立。换句话说，已知有很多用户并提供重大价值的kfuncs会为维护者投入时间和复杂度以支持它们提供更强的动力。因此，对于在BPF程序中使用kfuncs的开发者来说，与他人沟通和解释如何以及为何使用这些kfuncs，并在上游讨论发生时参与关于这些kfuncs的讨论，这一点至关重要。

b）与标记为EXPORT_SYMBOL_GPL的常规内核符号不同，调用kfuncs的BPF程序通常不在内核树中。这意味着当kfunc发生变化时，通常不能像更新内核符号时那样就地改变调用者，例如，上游驱动程序在内核符号变化时就地得到更新。与常规内核符号不同，这是BPF符号预期的行为，而且使用kfuncs的树外BPF程序应被视为修改和删除这些kfuncs讨论和决策的相关部分。BPF社区将在必要时积极参与上游讨论，以确保考虑到此类用户的视角。

c）kfunc永远不会有任何硬性的稳定性保证。BPF API不会因为稳定性原因纯粹阻止内核中的任何更改。话虽如此，kfuncs是旨在解决问题并向用户提供价值的功能。是否更改或移除kfunc的决定是一个多变量的技术决策，根据具体情况做出，并且由上述提到的数据点等信息指导。预计没有预警就移除或更改kfunc不会是常见的现象，也不会在没有合理理由的情况下发生，但必须接受这种可能性，如果要使用kfuncs的话。

3.1 kfunc的弃用
------------------

如上所述，虽然有时维护者可能会发现一个kfunc必须立即更改或移除以适应其子系统的一些变化，通常情况下，kfuncs能够适应更长且更审慎的弃用过程。例如，如果出现了一个新kfunc，它提供的功能优于现有kfunc，那么现有kfunc可能会被标记为废弃一段时间，以便用户可以将其BPF程序迁移到使用新的kfunc。或者，如果一个kfunc没有任何已知用户，可能在一段弃用期后决定移除该kfunc（不提供替代API），从而为用户提供一个窗口，如果事实证明kfunc实际上正在被使用，则可以通知kfunc维护者。

预计常见的情况是，kfuncs将经历一个弃用期，而不是在没有警告的情况下被更改或移除。如在“KF_deprecated_flag”中所述，kfunc框架为kfunc开发者提供了KF_DEPRECATED标志，以向用户发出kfunc已被废弃的信号。一旦kfunc被标记为KF_DEPRECATED，将遵循以下程序进行移除：

1. 对于废弃的kfuncs，所有相关信息都记录在其内核文档中。此文档通常包括kfunc预期的剩余生命周期、推荐的新功能以替换废弃函数的使用（或解释为什么不存在此类替代方案）等。
2. 在首次标记为废弃之后，废弃的kfunc将在内核中保留一段时间。这一时间长度将基于具体情况而定，通常取决于kfunc的使用范围、在内核中存在的时间以及转向替代品的难度。这个弃用时间段是“尽力而为”的，如上所述，情况有时可能需要在完整的预期弃用周期结束前移除kfunc。
3. 弃用期结束后，将移除kfunc。此时，调用该kfunc的BPF程序将被验证器拒绝。
4. 核心kfuncs
==================

BPF子系统提供了一系列“核心”kfuncs，它们可能适用于各种不同的潜在用途和程序。
这些kfuncs在此处有详细文档说明。
### 4.1 `struct task_struct *` 相关内核函数

存在多个内核函数（kfuncs）允许将 `struct task_struct *` 对象作为 kptr 使用：

这些内核函数在你想要获取或释放一个作为例如跟踪点参数或结构操作回调参数传递的 `struct task_struct *` 的引用时非常有用。例如：

```c
/**
 * 一个简单的示例跟踪点程序，展示如何获取和释放 struct task_struct * 指针
*/
SEC("tp_btf/task_newtask")
int BPF_PROG(task_acquire_release_example, struct task_struct *task, u64 clone_flags)
{
    struct task_struct *acquired;

    acquired = bpf_task_acquire(task);
    if (acquired)
        /*
         * 在典型的程序中，你可能像这样将任务存储到映射中，
         * 映射稍后会自动释放它。这里我们手动释放。
*/
        bpf_task_release(acquired);
    return 0;
}
```

在 `struct task_struct *` 对象上获取的引用受到 RCU 保护。因此，在 RCU 读区域中，你可以获得嵌入在映射值中的任务指针而无需获取引用：

```c
#define private(name) SEC(".data." #name) __hidden __attribute__((aligned(8)))
private(TASK) static struct task_struct *global;

/**
 * 一个简单的示例，展示如何使用 RCU 访问存储在映射中的任务
*/
SEC("tp_btf/task_newtask")
int BPF_PROG(task_rcu_read_example, struct task_struct *task, u64 clone_flags)
{
    struct task_struct *local_copy;

    bpf_rcu_read_lock();
    local_copy = global;
    if (local_copy)
        /*
         * 我们也可以在这里将 local_copy 传递给内核函数或帮助函数，
         * 因为我们保证 local_copy 在退出下面的 RCU 读区域之前都是有效的
*/
        bpf_printk("全局任务 %s 是有效的", local_copy->comm);
    else
        bpf_printk("未找到全局任务");
    bpf_rcu_read_unlock();

    /* 到这一点我们不能再引用 local_copy。 */

    return 0;
}
```

---

BPF 程序还可以从 PID 查找任务。如果调用者没有可以使用 bpf_task_acquire() 获取引用的可信 `struct task_struct *` 指针，则这很有用。

以下是一个使用它的示例：

```c
SEC("tp_btf/task_newtask")
int BPF_PROG(task_get_pid_example, struct task_struct *task, u64 clone_flags)
{
    struct task_struct *lookup;

    lookup = bpf_task_from_pid(task->pid);
    if (!lookup)
        /* 应该始终能找到任务，因为 %task 是跟踪点参数。 */
        return -ENOENT;

    if (lookup->pid != task->pid) {
        /* bpf_task_from_pid() 通过其在 init_pid_ns 中的全局唯一 PID 查找任务。
         * 因此，查找任务的 PID 应始终与输入任务相同
*/
        bpf_task_release(lookup);
        return -EINVAL;
    }

    /* bpf_task_from_pid() 返回已获取的引用，
     * 所以必须在返回跟踪点处理程序前将其释放
*/
    bpf_task_release(lookup);
    return 0;
}
```

### 4.2 `struct cgroup *` 相关内核函数

`struct cgroup *` 对象也有获取和释放函数：

这些内核函数的使用方式与 bpf_task_acquire() 和 bpf_task_release() 完全相同，所以我们不会为它们提供示例。

---

还有其他可用的内核函数用于与 `struct cgroup *` 对象交互，如 bpf_cgroup_ancestor() 和 bpf_cgroup_from_id()，分别允许调用者访问控制组的祖先并根据其 ID 找到控制组。两者都返回一个 cgroup kptr。
在内核文档中，`kernel/bpf/helpers.c` 文件中标识符 `bpf_cgroup_ancestor` 和 `bpf_cgroup_from_id` 的说明如下：

最终，BPF应该被更新以允许程序本身通过正常的内存加载来实现这一操作。目前，在验证器中没有做更多工作的情况下，这是不可能的。`bpf_cgroup_ancestor()` 可以按照以下方式使用：

```c
/**
 * 简单的tracepoint示例，展示了如何使用bpf_cgroup_ancestor()访问cgroup的祖先
 */
SEC("tp_btf/cgroup_mkdir")
int BPF_PROG(cgrp_ancestor_example, struct cgroup *cgrp, const char *path)
{
    struct cgroup *parent;

    /* 父cgroup位于当前cgroup层级前一个层级的位置 */
    parent = bpf_cgroup_ancestor(cgrp, cgrp->level - 1);
    if (!parent)
        return -ENOENT;

    bpf_printk("父id是 %d", parent->self.id);

    /* 返回上面获取的父cgroup */
    bpf_cgroup_release(parent);
    return 0;
}
```

4.3 struct cpumask * kfuncs
---------------------------

BPF提供了一套kfuncs，可以用于查询、分配、修改和销毁struct cpumask *对象。更多细节请参考 :ref:`cpumasks-header-label`。
