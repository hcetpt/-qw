SPDX 许可证标识符: GPL-2.0

.. _kfuncs-header-label:

=============================
BPF 内核函数 (kfuncs)
=============================

1. 引言
===============

BPF 内核函数，更通常被称为 kfuncs，是指在 Linux 内核中的函数，这些函数被暴露出来供 BPF 程序使用。与普通的 BPF 辅助函数不同，kfuncs 没有稳定的接口，并且可能会随着内核版本的更新而发生变化。因此，BPF 程序需要根据内核的变化进行相应的更新。更多关于 kfuncs 生命周期的信息，请参阅 :ref:`BPF_kfunc_lifecycle_expectations`。

2. 定义一个 kfunc
==================

将内核函数暴露给 BPF 程序有两种方法：一是使现有的内核函数可见；二是为 BPF 添加一个新的包装器函数。在这两种情况下，都必须确保 BPF 程序只能在有效的上下文中调用这些函数。为了强制这一点，可以针对不同的程序类型设置 kfunc 的可见性。如果你没有为现有的内核函数创建 BPF 包装器，则可以跳过到 :ref:`BPF_kfunc_nodef`。
2.1 创建包装器 kfunc
------------------------

定义包装器 kfunc 时，该包装器函数应具有外部链接属性。这样可以防止编译器优化掉未使用的代码，因为这个包装器 kfunc 并不在内核中任何地方被直接调用。不需要为包装器 kfunc 在头文件中提供原型声明。
下面是一个示例：

```c
        /* 阻止缺失原型警告 */
        __bpf_kfunc_start_defs();

        __bpf_kfunc struct task_struct *bpf_find_get_task_by_vpid(pid_t nr)
        {
                return find_get_task_by_vpid(nr);
        }

        __bpf_kfunc_end_defs();
```

当需要对 kfunc 的参数添加注释时，通常需要创建一个包装器 kfunc。否则，可以直接通过向 BPF 子系统注册的方式让 kfunc 对 BPF 程序可见。详情请参见 :ref:`BPF_kfunc_nodef`。
2.2 注释 kfunc 参数
-------------------

类似于 BPF 辅助函数，有时需要额外的上下文来帮助验证器更安全和更有用地使用内核函数。因此，可以通过在 kfunc 参数名后加上一个特定的标签（__tag）来注释参数，其中标签可以是支持的注释之一。
2.2.1 __sz 注解
------------------

此注解用于在参数列表中指示内存及其大小的对应关系。例如：

```c
        __bpf_kfunc void bpf_memzero(void *mem, int mem__sz)
        {
        ..
```
### 2.2.1 `__sz` 注解

在此处，验证器会将第一个参数视为 `PTR_TO_MEM`（指向内存的指针），而第二个参数则被视为该指针所指向数据的大小。默认情况下，如果没有使用 `__sz` 注解，将会采用指针类型本身的大小作为数据的大小。没有 `__sz` 注解的情况下，一个 `kfunc` 不能接受 `void` 类型的指针。

### 2.2.2 `__k` 注解

这个注解仅适用于标量参数，它表示验证器必须检查标量参数是否为已知常量，并且这个常量不表示大小参数，同时该常量的值对程序的安全性至关重要。

下面是一个示例：

```c
__bpf_kfunc void *bpf_obj_new(u32 local_type_id__k, ...)
{
    ...
}
```

在这个例子中，`bpf_obj_new` 使用 `local_type_id` 参数来查找程序 BTF 中对应类型的大小，并返回一个指向该类型大小的指针。每个类型 ID 都有其独特的大小，因此在验证器进行状态剪枝检查时，对于不同的值，每种调用都应被视为独立的。因此，每当一个 `kfunc` 接受一个非大小参数的常量标量参数，并且该常量的值对程序安全性至关重要时，应该使用 `__k` 后缀。

### 2.2.3 `__uninit` 注解

此注解用于指示参数将被视为未初始化。

下面是一个示例：

```c
__bpf_kfunc int bpf_dynptr_from_skb(..., struct bpf_dynptr_kern *ptr__uninit)
{
    ...
}
```

在此例中，`dynptr` 将被视为未初始化的 `dynptr`。如果没有这个注解，如果传递给函数的 `dynptr` 未被初始化，则验证器将拒绝该程序。

### 2.2.4 `__opt` 注解

此注解用于指示与 `__sz` 或 `__szk` 参数相关的缓冲区可能为 `null`。如果函数接收到指向缓冲区的 `nullptr`，验证器不会检查长度是否适合该缓冲区。`kfunc` 应负责在使用缓冲区之前检查其是否为 `null`。

下面是一个示例：

```c
__bpf_kfunc void *bpf_dynptr_slice(..., void *buffer__opt, u32 buffer__szk)
{
    ...
}
```
此处，缓冲区可能为null。如果缓冲区不为null，则其大小至少为buffer_szk。
无论如何，返回的缓冲区要么是NULL，要么大小为buffer_szk。如果没有这个
注解，验证器会在传递非零大小的空指针时拒绝该程序。
2.2.5 __str 注解
----------------------
此注解用于表明参数是一个常量字符串。
下面给出一个例子：

        __bpf_kfunc bpf_get_file_xattr(..., const char *name__str, ...)
        {
        ..
}

在这种情况下，可以这样调用`bpf_get_file_xattr()`：

        bpf_get_file_xattr(..., "xattr_name", ...);

或者：

        const char name[] = "xattr_name";  /* 这个需要是全局的 */
        int BPF_PROG(...)
        {
                ..
        bpf_get_file_xattr(..., name, ...);
                ..
}

.. _BPF_kfunc_nodef:

2.3 使用现有的内核函数
-------------------------------------

当现有的内核函数适合被BPF程序使用时，
可以直接注册到BPF子系统中。但是，仍然需要小心审查它在BPF程序中的调用上下文以及是否安全地进行调用。
2.4 注解kfuncs
---------------------

除了kfuncs的参数之外，验证器可能还需要更多关于注册到BPF子系统的kfunc类型的信息。为此，我们定义了一组kfuncs上的标志如下所示：

        BTF_KFUNCS_START(bpf_task_set)
        BTF_ID_FLAGS(func, bpf_get_task_pid, KF_ACQUIRE | KF_RET_NULL)
        BTF_ID_FLAGS(func, bpf_put_pid, KF_RELEASE)
        BTF_KFUNCS_END(bpf_task_set)

这组设置编码了上面列出的每个kfunc的BTF ID，并且与之编码了标志。当然，也可以不指定任何标志。
kfunc定义也应始终使用`__bpf_kfunc`宏进行注解。这可以防止诸如编译器将kfunc内联（如果它是静态内核函数）或在LTO构建中因未在其余内核中使用而被省略等问题。开发人员不应手动添加注解以防止这些问题。如果需要注解来防止您的kfunc出现此类问题，这是个bug，应该添加到宏的定义中以便其他kfuncs同样受到保护。下面给出一个例子：

        __bpf_kfunc struct task_struct *bpf_get_task_pid(s32 pid)
        {
        ..
}

2.4.1 KF_ACQUIRE 标志
----------------------

KF_ACQUIRE标志用于表明kfunc返回指向引用计数对象的指针。验证器将确保通过释放kfunc或通过引用kptr（调用bpf_kptr_xchg）将对象指针最终释放或将所有权转移到map中。否则，验证器会失败加载BPF程序，直到所有可能探索的程序状态中没有剩余的引用为止。
### 2.4.2 KF_RET_NULL 标志
----------------------

KF_RET_NULL 标志用于指示由 kfunc 返回的指针可能为 NULL。因此，它强制用户在使用该 kfunc 返回的指针（解引用或传递给其他辅助函数）之前进行 NULL 检查。此标志通常与 KF_ACQUIRE 标志一起使用，但二者是相互独立的。

### 2.4.3 KF_RELEASE 标志
---------------------

KF_RELEASE 标志用于指示 kfunc 释放传入的指针。只能传递一个被引用的指针。所有要释放的指针的副本在使用此标志调用 kfunc 后都将失效。带有 KF_RELEASE 的 kfunc 自动获得下面描述的 KF_TRUSTED_ARGS 标志所提供的保护。

### 2.4.4 KF_TRUSTED_ARGS 标志
--------------------------

KF_TRUSTED_ARGS 标志用于接受指针参数的 kfunc。它表示所有指针参数都是有效的，并且所有指向 BTF 对象的指针都以未修改的形式传递（即，在零偏移处，并且没有通过遍历其他指针获得，下面有一个例外）。

有两种类型的指向内核对象的指针被认为是“有效”的：

1. 作为追踪点（tracepoint）或 struct_ops 回调参数传递的指针。
2. 从带有 KF_ACQUIRE 标志的 kfunc 返回的指针。

指向非 BTF 对象（例如标量指针）也可以传递给带有 KF_TRUSTED_ARGS 标志的 kfunc，并且可以有非零偏移。

“有效”指针的定义随时可能改变，并且绝对没有任何 ABI 稳定性保证。

如上所述，从可信指针遍历得到的嵌套指针不再可信，除非有一个例外。如果一个结构类型有一个字段，只要其父指针有效，该字段就被保证有效（可信或 RCU，如下文 KF_RCU 描述），则可以使用以下宏向验证器表达这一点：

* `BTF_TYPE_SAFE_TRUSTED`
* `BTF_TYPE_SAFE_RCU`
* `BTF_TYPE_SAFE_RCU_OR_NULL`

例如，

```c
BTF_TYPE_SAFE_TRUSTED(struct socket) {
    struct sock *sk;
};
```

或者

```c
BTF_TYPE_SAFE_RCU(struct task_struct) {
    const cpumask_t *cpus_ptr;
    struct css_set __rcu *cgroups;
    struct task_struct __rcu *real_parent;
    struct task_struct *group_leader;
};
```

换句话说，你必须：

1. 使用 `BTF_TYPE_SAFE_*` 宏包装有效指针类型。
2. 指定有效嵌套字段的类型和名称。此字段必须与原始类型定义中的字段完全匹配。

由 `BTF_TYPE_SAFE_*` 宏声明的新类型也需要被发出以便出现在 BTF 中。例如，`BTF_TYPE_SAFE_TRUSTED(struct socket)` 在 `type_is_trusted()` 函数中如下发出：

```c
BTF_TYPE_EMIT(BTF_TYPE_SAFE_TRUSTED(struct socket));
```


### 2.4.5 KF_SLEEPABLE 标志
-----------------------

KF_SLEEPABLE 标志用于可能会睡眠的 kfunc。此类 kfunc 只能由允许睡眠的 BPF 程序（BPF_F_SLEEPABLE）调用。
### 2.4.6 KF_DESTRUCTIVE 标志

KF_DESTRUCTIVE 标志用于指示对系统具有破坏性的函数调用。例如，这样的调用可能会导致系统重启或陷入恐慌状态。由于这一特性，这些调用受到额外的限制。目前它们只需要具备 CAP_SYS_BOOT 的权限，但将来可能会增加更多的限制。

### 2.4.7 KF_RCU 标志

KF_RCU 标志是 KF_TRUSTED_ARGS 的较弱版本。标记为 KF_RCU 的 kfuncs 需要 PTR_TRUSTED 或 MEM_RCU 类型的参数。验证器保证对象的有效性，并确保不会出现使用后释放的问题。指针不为空，但对象的引用计数可能已经降为零。kfuncs 需要考虑进行 refcnt != 0 的检查，尤其是在返回一个 KF_ACQUIRE 指针时。此外，请注意，如果一个 KF_RCU 的 kfunc 返回 KF_ACQUIRE，则它很可能也应该标记为 KF_RET_NULL。

### 2.4.8 KF_DEPRECATED 标志

KF_DEPRECATED 标志用于标记计划在后续内核版本中更改或移除的 kfuncs。带有 KF_DEPRECATED 标记的 kfunc 还应在内核文档中包含相关信息。这类信息通常包括 kfunc 预期的剩余生命周期、可用的新功能推荐（如果有的话），以及移除它的理由。

请注意，在某些情况下，带有 KF_DEPRECATED 标志的 kfunc 可能会继续得到支持，并且其 KF_DEPRECATED 标志可能会被移除，但一旦添加了该标志，要将其移除可能比一开始就防止添加该标志更加困难。如 :ref:`BPF_kfunc_lifecycle_expectations` 中所述，依赖特定 kfunc 的用户被鼓励尽早提出自己的使用案例，并参与到有关是否保留、更改、废弃或移除这些 kfuncs 的上游讨论中。

### 2.5 注册 kfuncs

一旦 kfunc 准备就绪，使其可见的最后一步是向 BPF 子系统注册它。注册是按 BPF 程序类型进行的。下面是一个示例：

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

验证器始终强制执行 BPF 程序传递给 kfunc 的指针的 BTF 类型与 kfunc 定义中的指针类型匹配。然而，验证器确实允许根据 C 标准等效的类型传递给同一个 kfunc 参数，即使它们的 BTF_ID 不同。

例如，对于以下类型定义：

```c
struct bpf_cpumask {
        cpumask_t cpumask;
        refcount_t usage;
};
```

验证器允许将 `struct bpf_cpumask *` 传递给接受 `cpumask_t *`（它是 `struct cpumask *` 的 typedef）的 kfunc。例如，`struct cpumask *` 和 `struct bpf_cpumask *` 都可以传递给 `bpf_cpumask_test_cpu()`。

在某些情况下，这种类型别名的行为并不总是所期望的。`struct nf_conn___init` 就是这样一个例子：

```c
struct nf_conn___init {
        struct nf_conn ct;
};
```

虽然 C 标准认为这些类型是等价的，但在某些情况下将任意类型传递给可信 kfunc 并不安全。`struct nf_conn___init` 表示一个已分配但尚未初始化的 `struct nf_conn` 对象，因此将 `struct nf_conn___init *` 传递给期望完全初始化的 `struct nf_conn *`（如 `bpf_ct_change_timeout()`）的 kfunc 是不安全的。

为了满足此类要求，如果两种类型的名称完全相同，其中一种以 `___init` 结尾，验证器将强制执行严格的 PTR_TO_BTF_ID 类型匹配。

### 3. kfunc 生命周期预期

kfuncs 提供了一个内核 <-> 内核的 API，因此不受与内核 <-> 用户 UAPI 相关的严格稳定性限制的约束。这意味着它们可以被认为类似于 EXPORT_SYMBOL_GPL，并且当需要时，定义它们的子系统的维护者可以对其进行修改或移除。

就像内核中的任何其他更改一样，维护者不会在没有合理理由的情况下更改或移除 kfunc。他们是否会更改一个 kfunc 最终取决于多种因素，例如 kfunc 的广泛使用程度、kfunc 在内核中存在的时间长度、是否存在替代 kfunc、相关子系统稳定性的标准是什么，当然还有继续支持该 kfunc 的技术成本。
这段文字可以翻译为：

有几个含义：

a) 广泛使用或在内核中存在时间较长的kfuncs将更难被维护者合理地更改或移除。换句话说，已知有很多用户并提供重要价值的kfuncs会促使维护者投入时间和复杂度来支持它们。因此，对于在BPF程序中使用kfuncs的开发者来说，沟通和解释如何及为何使用这些kfuncs，以及参与相关讨论至关重要。
b) 与标记为EXPORT_SYMBOL_GPL的常规内核符号不同，调用kfuncs的BPF程序通常不属于内核源代码树的一部分。这意味着当一个kfunc发生变化时，通常无法像更新上游驱动程序那样直接修改调用者。对于BPF符号而言，这种行为是预期的，并且使用kfuncs的外树BPF程序应被视为修改和删除这些kfuncs时的相关因素。BPF社区将在必要时积极参与上游讨论，以确保此类用户的观点得到考虑。
c) kfunc永远不会有任何硬性的稳定性保证。BPF API不会因为稳定性原因而硬性阻止内核中的任何变更。话虽如此，kfuncs是为了解决问题并向用户提供价值的功能。是否更改或移除某个kfunc的决定是一个多变量的技术决策，需要根据具体情况作出，并参考上述提到的数据点。虽然不发出警告就更改或移除kfunc的情况不会常见，也不会没有充分的理由发生，但这种可能性必须被接受，如果要使用kfuncs的话。

3.1 kfunc的弃用
----------------------

如上所述，虽然有时维护者可能需要立即更改或移除一个kfunc以适应其子系统的变化，但通常情况下，kfuncs能够经历一个更长、更审慎的弃用过程。例如，如果出现一个新的kfunc，其功能优于现有的kfunc，则现有kfunc可能会被暂时标记为弃用，以便用户迁移他们的BPF程序以使用新的kfunc。或者，如果某个kfunc没有已知用户，可以在经过一段时间的弃用期后决定移除该kfunc（不提供替代API），以给用户提供一个窗口通知kfunc的维护者，如果实际情况证明该kfunc实际上正在被使用的话。
预计常见的做法是kfuncs会经历一个弃用期，而不是毫无预警地更改或移除。如在:ref:`KF_deprecated_flag`中所述，kfunc框架为kfunc开发者提供了KF_DEPRECATED标志，用于向用户表明一个kfunc已被弃用。一旦kfunc被标记为KF_DEPRECATED，将遵循以下流程进行移除：

1. 对于被弃用的kfuncs，相关的文档会被记录在其内核文档中。这些文档通常包括该kfunc预计剩余的生命期、推荐的新功能以替换弃用函数的使用（或解释为什么不存在这样的替代方案）等信息。
2. 被弃用的kfunc在首次标记为弃用后会在内核中保留一段时间。这一时间段将基于具体情况而定，通常取决于该kfunc使用的广泛程度、它在内核中存在的时间长度以及迁移到替代方案的难度。这个弃用期是“尽力而为”的，并且如上所述，在某些情况下，kfunc可能在完整的预期弃用期结束之前就被移除。
3. 在弃用期结束后，kfunc将被移除。此时，调用该kfunc的BPF程序将被验证器拒绝。
4. 核心kfuncs
=================

BPF子系统提供了一系列“核心”kfuncs，这些kfuncs可能适用于各种不同的使用场景和程序。这些kfuncs在此处进行了记录。
### 4.1 `struct task_struct *` KFuncs

---

有许多KFuncs允许将`struct task_struct *`对象作为KPtr使用：

.. kernel-doc:: kernel/bpf/helpers.c
   :identifiers: bpf_task_acquire bpf_task_release

当您需要获取或释放通过例如追踪点参数或struct_ops回调参数传递的`struct task_struct *`引用时，这些KFuncs非常有用。例如：

.. code-block:: c

    /**
     * 一个简单的示例追踪点程序，展示如何获取和释放struct task_struct *指针
     */
    SEC("tp_btf/task_newtask")
    int BPF_PROG(task_acquire_release_example, struct task_struct *task, u64 clone_flags)
    {
        struct task_struct *acquired;

        acquired = bpf_task_acquire(task);
        if (acquired)
            /*
             * 在典型的程序中，您可能像这样将任务存储在映射表中，
             * 映射表会自动在稍后释放它。这里，我们手动释放它
             */
            bpf_task_release(acquired);
        return 0;
    }

对`struct task_struct *`对象获取的引用受到RCU保护。因此，在RCU读取区域内，您可以从映射值中获取指向任务的指针而无需获取引用：

.. code-block:: c

    #define private(name) SEC(".data." #name) __hidden __attribute__((aligned(8)))
    private(TASK) static struct task_struct *global;

    /**
     * 一个简单的示例，展示如何使用RCU访问存储在映射中的任务
     */
    SEC("tp_btf/task_newtask")
    int BPF_PROG(task_rcu_read_example, struct task_struct *task, u64 clone_flags)
    {
        struct task_struct *local_copy;

        bpf_rcu_read_lock();
        local_copy = global;
        if (local_copy)
            /*
             * 我们还可以在这里将local_copy传递给KFuncs或辅助函数，
             * 因为我们保证local_copy将在退出下面的RCU读取区域之前始终有效
             */
            bpf_printk("Global task %s is valid", local_copy->comm);
        else
            bpf_printk("No global task found");
        bpf_rcu_read_unlock();

        /* 到这一点，我们不能再引用local_copy。 */

        return 0;
    }

---

BPF程序也可以根据进程ID查找任务。如果调用者没有一个可以信任的指向`struct task_struct *`对象的指针（可以通过`bpf_task_acquire()`获取引用），这可能会很有用。
.. kernel-doc:: kernel/bpf/helpers.c
   :identifiers: bpf_task_from_pid

下面是一个使用它的示例：

.. code-block:: c

    SEC("tp_btf/task_newtask")
    int BPF_PROG(task_get_pid_example, struct task_struct *task, u64 clone_flags)
    {
        struct task_struct *lookup;

        lookup = bpf_task_from_pid(task->pid);
        if (!lookup)
            /* 应该总能找到一个任务，因为%task是一个追踪点参数。 */
            return -ENOENT;

        if (lookup->pid != task->pid) {
            /* bpf_task_from_pid()通过其在init_pid_ns中的全局唯一PID查找任务，
             * 因此，查找的任务的PID应该始终与输入任务相同
             */
            bpf_task_release(lookup);
            return -EINVAL;
        }

        /* bpf_task_from_pid()返回一个已获取的引用，
         * 因此必须在从追踪点处理器返回前释放
         */
        bpf_task_release(lookup);
        return 0;
    }

### 4.2 `struct cgroup *` KFuncs

---

`struct cgroup *`对象也有获取和释放函数：

.. kernel-doc:: kernel/bpf/helpers.c
   :identifiers: bpf_cgroup_acquire bpf_cgroup_release

这些KFuncs的使用方式与`bpf_task_acquire()`和`bpf_task_release()`完全相同，所以我们不再提供示例。

---

其他可用于与`struct cgroup *`对象交互的KFuncs包括`bpf_cgroup_ancestor()`和`bpf_cgroup_from_id()`，它们分别允许调用者访问cgroup的祖先并根据其ID查找cgroup。两者都返回cgroup KPtr。
下面是您提供的文档段落的中文翻译：

``kernel-doc:: kernel/bpf/helpers.c``
   :identifiers: bpf_cgroup_ancestor

``kernel-doc:: kernel/bpf/helpers.c``
   :identifiers: bpf_cgroup_from_id

最终，BPF应该被更新以允许在程序本身中通过正常的内存加载来实现这一功能。目前，如果不进行更多的验证器工作，这是不可能的。`bpf_cgroup_ancestor()` 可以如下使用：

```c
/**
 * 简单的追踪点示例，说明如何使用 `bpf_cgroup_ancestor()` 访问 cgroup 的祖先
 */
SEC("tp_btf/cgroup_mkdir")
int BPF_PROG(cgrp_ancestor_example, struct cgroup *cgrp, const char *path)
{
    struct cgroup *parent;

    /* 父 cgroup 位于当前 cgroup 级别之前的级别上。 */
    parent = bpf_cgroup_ancestor(cgrp, cgrp->level - 1);
    if (!parent)
        return -ENOENT;

    bpf_printk("父标识是 %d", parent->self.id);

    /* 返回上面获取的父 cgroup。 */
    bpf_cgroup_release(parent);
    return 0;
}
```

4.3 结构体 cpumask * 的 kfuncs
------------------------------

BPF 提供了一组 kfuncs，可用于查询、分配、修改和销毁 `struct cpumask *` 对象。请参考 :ref:`cpumasks-header-label` 获取更多细节。
