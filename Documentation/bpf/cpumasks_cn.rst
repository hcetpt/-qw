### SPDX 许可证标识符: GPL-2.0

### _cpumasks-header-label_

==================
BPF cpumask 内核函数
==================

1. 引言
======

`struct cpumask` 是内核中的位图数据结构，其索引反映了系统上的 CPU。通常，cpumask 用于跟踪任务与哪些 CPU 关联，但也可以用于跟踪调度域中的哪些核心、机器上哪些核心处于空闲状态等。
BPF 为程序提供了一组 :ref:`kfuncs-header-label`，可用于分配、修改、查询和释放 cpumask。

2. BPF cpumask 对象
==================

有两种不同类型的 cpumask 可供 BPF 程序使用。

2.1 `struct bpf_cpumask *`
--------------------------

`struct bpf_cpumask *` 是由 BPF 代表 BPF 程序分配的 cpumask，其生命周期完全由 BPF 控制。这些 cpumask 使用 RCU 保护，可以被修改，可以用作 kptr，并且可以安全地转换为 `struct cpumask *`。

2.1.1 `struct bpf_cpumask *` 生命周期
----------------------------------------

`struct bpf_cpumask *` 通过以下函数进行分配、获取和释放：

.. kernel-doc:: kernel/bpf/cpumask.c
  :identifiers: bpf_cpumask_create

.. kernel-doc:: kernel/bpf/cpumask.c
  :identifiers: bpf_cpumask_acquire

.. kernel-doc:: kernel/bpf/cpumask.c
  :identifiers: bpf_cpumask_release

例如：

.. code-block:: c

        struct cpumask_map_value {
                struct bpf_cpumask __kptr * cpumask;
        };

        struct array_map {
                __uint(type, BPF_MAP_TYPE_ARRAY);
                __type(key, int);
                __type(value, struct cpumask_map_value);
                __uint(max_entries, 65536);
        } cpumask_map SEC(".maps");

        static int cpumask_map_insert(struct bpf_cpumask *mask, u32 pid)
        {
                struct cpumask_map_value local, *v;
                long status;
                struct bpf_cpumask *old;
                u32 key = pid;

                local.cpumask = NULL;
                status = bpf_map_update_elem(&cpumask_map, &key, &local, 0);
                if (status) {
                        bpf_cpumask_release(mask);
                        return status;
                }

                v = bpf_map_lookup_elem(&cpumask_map, &key);
                if (!v) {
                        bpf_cpumask_release(mask);
                        return -ENOENT;
                }

                old = bpf_kptr_xchg(&v->cpumask, mask);
                if (old)
                        bpf_cpumask_release(old);

                return 0;
        }

        /**
         * 一个示例追踪点，展示如何查询任务的 cpumask 并将其作为 kptr 记录
*/
        SEC("tp_btf/task_newtask")
        int BPF_PROG(record_task_cpumask, struct task_struct *task, u64 clone_flags)
        {
                struct bpf_cpumask *cpumask;
                int ret;

                cpumask = bpf_cpumask_create();
                if (!cpumask)
                        return -ENOMEM;

                if (!bpf_cpumask_full(task->cpus_ptr))
                        bpf_printk("任务 %s 有 CPU 关联性", task->comm);

                bpf_cpumask_copy(cpumask, task->cpus_ptr);
                return cpumask_map_insert(cpumask, task->pid);
        }

---

2.1.1 `struct bpf_cpumask *` 作为 kptr
---------------------------------------

如前所述并举例说明，这些 `struct bpf_cpumask *` 对象也可以存储在映射中并用作 kptr。如果 `struct bpf_cpumask *` 存在于映射中，则可以通过 bpf_kptr_xchg() 从映射中移除引用，或者使用 RCU 机会性地获取引用：

.. code-block:: c

	/* 包含存储在映射中的 struct bpf_cpumask kptr 的结构体。 */
	struct cpumasks_kfunc_map_value {
		struct bpf_cpumask __kptr * bpf_cpumask;
	};

	/* 包含 struct cpumasks_kfunc_map_value 条目的映射。 */
	struct {
		__uint(type, BPF_MAP_TYPE_ARRAY);
		__type(key, int);
		__type(value, struct cpumasks_kfunc_map_value);
		__uint(max_entries, 1);
	} cpumasks_kfunc_map SEC(".maps");

	/* ... */

	/**
	 * 一个简单的示例追踪点程序，展示如何使用 RCU 保护将
	 * 存储在映射中的 struct bpf_cpumask * kptr 传递给 kfuncs
*/
	SEC("tp_btf/cgroup_mkdir")
	int BPF_PROG(cgrp_ancestor_example, struct cgroup *cgrp, const char *path)
	{
		struct bpf_cpumask *kptr;
		struct cpumasks_kfunc_map_value *v;
		u32 key = 0;

		/* 假设之前已将 bpf_cpumask * kptr 存储在映射中。 */
		v = bpf_map_lookup_elem(&cpumasks_kfunc_map, &key);
		if (!v)
			return -ENOENT;

		bpf_rcu_read_lock();
		/* 获取已存储在映射中的 bpf_cpumask * kptr 的引用。 */
		kptr = v->cpumask;
		if (!kptr) {
			/* 如果映射中不存在 bpf_cpumask，那是因为
			 * 我们与其他 CPU 发生竞争，在 bpf_map_lookup_elem()
			 * 上面的调用与我们从映射加载指针之间的某个时刻，
			 * 另一个 CPU 使用 bpf_kptr_xchg() 移除了它
*/
			bpf_rcu_read_unlock();
			return -EBUSY;
		}

		bpf_cpumask_setall(kptr);
		bpf_rcu_read_unlock();

		return 0;
	}

---

2.2 `struct cpumask`
-------------------

`struct cpumask` 是实际包含正在查询、修改等的 cpumask 位图的对象。`struct bpf_cpumask` 包含一个 `struct cpumask`，这就是为什么它可以安全地转换为该类型（但是请注意，将 `struct cpumask *` 转换为 `struct bpf_cpumask *` 是 **不安全** 的，并且验证器会拒绝任何试图这样做的程序）。
如下所述，任何修改其 cpumask 参数的 kfunc 都会以 `struct bpf_cpumask *` 作为参数。而任何仅仅查询 cpumask 的参数则会采用 `struct cpumask *`。

3. cpumask 内核函数
==================

上面描述了可以用于分配、获取、释放等 `struct bpf_cpumask *` 的内核函数。本节将描述用于修改和查询 cpumask 的内核函数。
### 3.1 修改 CPU 面具
---------------------

一些 CPU 面具 kfuncs 是“只读”的，意味着它们不会修改任何参数；而其他的一些则至少会修改一个参数（这意味着该参数必须是一个 `struct bpf_cpumask *` 类型，如上所述）。本节将描述所有至少修改一个参数的 CPU 面具 kfuncs。关于只读 kfuncs 的详细信息，请参见下面的 :ref:`cpumasks-querying-label`。

#### 3.1.1 设置和清除 CPU
-------------------------------

`bpf_cpumask_set_cpu()` 和 `bpf_cpumask_clear_cpu()` 可以分别用来设置或清除 `struct bpf_cpumask` 中的一个 CPU：

.. kernel-doc:: kernel/bpf/cpumask.c
   :identifiers: bpf_cpumask_set_cpu bpf_cpumask_clear_cpu

这些 kfuncs 直观易懂，例如可以这样使用：

.. code-block:: c

        /**
         * 一个示例追踪点，展示如何查询 CPU 面具
*/
        SEC("tp_btf/task_newtask")
        int BPF_PROG(test_set_clear_cpu, struct task_struct *task, u64 clone_flags)
        {
                struct bpf_cpumask *cpumask;

                cpumask = bpf_cpumask_create();
                if (!cpumask)
                        return -ENOMEM;

                bpf_cpumask_set_cpu(0, cpumask);
                if (!bpf_cpumask_test_cpu(0, cast(cpumask)))
                        /* 不应该发生这种情况。 */
                        goto release_exit;

                bpf_cpumask_clear_cpu(0, cpumask);
                if (bpf_cpumask_test_cpu(0, cast(cpumask)))
                        /* 不应该发生这种情况。 */
                        goto release_exit;

                /* 如 task->cpus_ptr 这样的 struct cpumask * 指针也可以被查询。 */
                if (bpf_cpumask_test_cpu(0, task->cpus_ptr))
                        bpf_printk("任务 %s 可以使用 CPU %d", task->comm, 0);

        release_exit:
                bpf_cpumask_release(cpumask);
                return 0;
        }

---

`bpf_cpumask_test_and_set_cpu()` 和 `bpf_cpumask_test_and_clear_cpu()` 是互补的 kfuncs，允许调用者原子地测试并设置（或清除）CPU：

.. kernel-doc:: kernel/bpf/cpumask.c
   :identifiers: bpf_cpumask_test_and_set_cpu bpf_cpumask_test_and_clear_cpu

---

我们还可以使用 `bpf_cpumask_setall()` 和 `bpf_cpumask_clear()` 来一次性设置或清除整个 `struct bpf_cpumask *` 对象：

.. kernel-doc:: kernel/bpf/cpumask.c
   :identifiers: bpf_cpumask_setall bpf_cpumask_clear

#### 3.1.2 CPU 面具间的操作
---------------------------------

除了在单一的 CPU 面具中设置或清除单个 CPU 外，调用者还可以使用 `bpf_cpumask_and()`、`bpf_cpumask_or()` 和 `bpf_cpumask_xor()` 在多个 CPU 面具之间进行位操作：

.. kernel-doc:: kernel/bpf/cpumask.c
   :identifiers: bpf_cpumask_and bpf_cpumask_or bpf_cpumask_xor

以下是一个示例，展示了它们的使用方法。请注意，这个示例中的部分 kfuncs 将在后面更详细地介绍：
.. code-block:: c

        /**
         * 一个示例追踪点，展示如何使用位运算符来修改 CPU 面具（并查询）
*/
        SEC("tp_btf/task_newtask")
        int BPF_PROG(test_and_or_xor, struct task_struct *task, u64 clone_flags)
        {
                struct bpf_cpumask *mask1, *mask2, *dst1, *dst2;

                mask1 = bpf_cpumask_create();
                if (!mask1)
                        return -ENOMEM;

                mask2 = bpf_cpumask_create();
                if (!mask2) {
                        bpf_cpumask_release(mask1);
                        return -ENOMEM;
                }

                // ...安全创建另外两个面具... */

                bpf_cpumask_set_cpu(0, mask1);
                bpf_cpumask_set_cpu(1, mask2);
                bpf_cpumask_and(dst1, (const struct cpumask *)mask1, (const struct cpumask *)mask2);
                if (!bpf_cpumask_empty((const struct cpumask *)dst1))
                        /* 不应该发生这种情况。 */
                        goto release_exit;

                bpf_cpumask_or(dst1, (const struct cpumask *)mask1, (const struct cpumask *)mask2);
                if (!bpf_cpumask_test_cpu(0, (const struct cpumask *)dst1))
                        /* 不应该发生这种情况。 */
                        goto release_exit;

                if (!bpf_cpumask_test_cpu(1, (const struct cpumask *)dst1))
                        /* 不应该发生这种情况。 */
                        goto release_exit;

                bpf_cpumask_xor(dst2, (const struct cpumask *)mask1, (const struct cpumask *)mask2);
                if (!bpf_cpumask_equal((const struct cpumask *)dst1,
                                       (const struct cpumask *)dst2))
                        /* 不应该发生这种情况。 */
                        goto release_exit;

         release_exit:
                bpf_cpumask_release(mask1);
                bpf_cpumask_release(mask2);
                bpf_cpumask_release(dst1);
                bpf_cpumask_release(dst2);
                return 0;
        }

---

整个 CPU 面具的内容可以通过 `bpf_cpumask_copy()` 复制到另一个面具：

.. kernel-doc:: kernel/bpf/cpumask.c
   :identifiers: bpf_cpumask_copy

---

.. _cpumasks-querying-label:

### 3.2 查询 CPU 面具
---------------------

除了上述 kfuncs 外，还有一组只读 kfuncs 可用于查询 CPU 面具的内容：

.. kernel-doc:: kernel/bpf/cpumask.c
   :identifiers: bpf_cpumask_first bpf_cpumask_first_zero bpf_cpumask_first_and
                 bpf_cpumask_test_cpu bpf_cpumask_weight

.. kernel-doc:: kernel/bpf/cpumask.c
   :identifiers: bpf_cpumask_equal bpf_cpumask_intersects bpf_cpumask_subset
                 bpf_cpumask_empty bpf_cpumask_full

.. kernel-doc:: kernel/bpf/cpumask.c
   :identifiers: bpf_cpumask_any_distribute bpf_cpumask_any_and_distribute

---

上面已经展示了一些查询 kfuncs 的使用示例，这里不再重复。然而，所有上述提到的 kfuncs 都已在 `tools/testing/selftests/bpf/progs/cpumask_success.c`_ 中进行了测试，如果你想要更多的使用示例，请参考那里。
.. _tools/testing/selftests/bpf/progs/cpumask_success.c:
   https://git.kernel.org/pub/scm/linux/kernel/git/stable/linux.git/tree/tools/testing/selftests/bpf/progs/cpumask_success.c

### 4. 添加 BPF CPU 面具 kfuncs
============================

当前支持的 BPF CPU 面具 kfuncs 并不是与 `include/linux/cpumask.h` 中的 CPU 面具操作完全一一对应。当需要时，任何这些 CPU 面具操作都可以很容易地封装成一个新的 kfunc。如果你希望支持一个新的 CPU 面具操作，请随时提交补丁。如果你确实添加了一个新的 CPU 面具 kfunc，请在此处记录，并向 CPU 面具自测套件添加任何相关的自测试案例。
