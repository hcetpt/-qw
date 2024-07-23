SPDX 许可证标识符：GPL-2.0

.. _cpumasks-header-label:

==================
BPF cpumask 内核函数
==================

1. 引言
===============

`struct cpumask` 是内核中的一种位图数据结构，其索引反映了系统上的CPU。通常，cpumask用于跟踪任务与哪些CPU关联，但它们也可以用于例如跟踪调度域关联的哪些核心，机器上哪些核心处于空闲状态等。
BPF为程序提供了一组 :ref:`kfuncs-header-label` ，可用于分配、修改、查询和释放cpumasks。

2. BPF cpumask 对象
======================

有两类不同的cpumasks可以被BPF程序使用：

2.1 `struct bpf_cpumask *`
----------------------------

`struct bpf_cpumask *` 是由BPF代表BPF程序分配的cpumask，其生命周期完全由BPF控制。这些cpumask受到RCU保护，可以被修改，可以用作kptr，并且可以安全地转换为`struct cpumask *`。

2.1.1 `struct bpf_cpumask *` 生命周期
----------------------------------------

`struct bpf_cpumask *` 使用以下函数进行分配、获取和释放：

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
         * 一个示例追踪点，展示如何查询并记录任务的cpumask作为kptr
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
                        bpf_printk("task %s has CPU affinity", task->comm);

                bpf_cpumask_copy(cpumask, task->cpus_ptr);
                return cpumask_map_insert(cpumask, task->pid);
        }

---

2.1.1 `struct bpf_cpumask *` 作为kptrs
---------------------------------------

如上所述和所示，这些 `struct bpf_cpumask *` 对象也可以存储在map中并用作kptrs。如果一个 `struct bpf_cpumask *` 存在于map中，可以通过bpf_kptr_xchg()从map中移除引用，或者使用RCU机会性地获取它：

.. code-block:: c

	/* 包含存储在map中的struct bpf_cpumask kptr的结构体。 */
	struct cpumasks_kfunc_map_value {
		struct bpf_cpumask __kptr * bpf_cpumask;
	};

	/* 包含struct cpumasks_kfunc_map_value条目的map。 */
	struct {
		__uint(type, BPF_MAP_TYPE_ARRAY);
		__type(key, int);
		__type(value, struct cpumasks_kfunc_map_value);
		__uint(max_entries, 1);
	} cpumasks_kfunc_map SEC(".maps");

	/* ... */

	/**
	 * 一个简单的追踪点程序示例，展示如何使用RCU保护将
	 * 存储在map中的struct bpf_cpumask * kptr传递给kfuncs
*/
	SEC("tp_btf/cgroup_mkdir")
	int BPF_PROG(cgrp_ancestor_example, struct cgroup *cgrp, const char *path)
	{
		struct bpf_cpumask *kptr;
		struct cpumasks_kfunc_map_value *v;
		u32 key = 0;

		/* 假设之前已将bpf_cpumask * kptr存储在map中。 */
		v = bpf_map_lookup_elem(&cpumasks_kfunc_map, &key);
		if (!v)
			return -ENOENT;

		bpf_rcu_read_lock();
		/* 获取已经存储在map中的bpf_cpumask * kptr的引用。 */
		kptr = v->cpumask;
		if (!kptr) {
			/* 如果map中没有bpf_cpumask，那是因为我们正在与另一个CPU竞争，
			 * 它在bpf_map_lookup_elem()上面的bpf_kptr_xchg()之间将其删除了。
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
----------------------

`struct cpumask` 是实际包含被查询、修改等的cpumask位图的对象。`struct bpf_cpumask` 包装了一个`struct cpumask`，这就是为什么可以安全地将其转换为`struct cpumask *`（但是请注意，将`struct cpumask *`转换为`struct bpf_cpumask *`是**不安全**的，并且验证器会拒绝任何尝试这样做的程序）
如下面所见，任何修改其cpumask参数的kfunc将以`struct bpf_cpumask *`作为该参数。任何仅仅查询cpumask的参数将取而代之以`struct cpumask *`。

3. cpumask 内核函数
=================

上面描述了可用于分配、获取、释放等`struct bpf_cpumask *`的kfunc。文档的这一部分将描述用于修改和查询cpumasks的kfunc。
### 3.1 修改CPU掩码

一些CPU掩码kfuncs是“只读”的，意味着它们不会修改任何参数，而其他kfuncs至少会修改一个参数（这意味着参数必须是一个`struct bpf_cpumask *`类型，如上所述）。本节将描述所有至少修改一个参数的CPU掩码kfuncs。:ref:`cpumasks-querying-label`下面描述了只读kfuncs。

#### 3.1.1 设置和清除CPU

`bpf_cpumask_set_cpu()`和`bpf_cpumask_clear_cpu()`可以分别用于在`struct bpf_cpumask`中设置和清除一个CPU：

.. kernel-doc:: kernel/bpf/cpumask.c
   :identifiers: bpf_cpumask_set_cpu bpf_cpumask_clear_cpu

这些kfuncs非常直观，例如，可以这样使用：

.. code-block:: c

        /**
         * 一个示例追踪点展示如何查询cpumask
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
                        /* 不应该发生。 */
                        goto release_exit;

                bpf_cpumask_clear_cpu(0, cpumask);
                if (bpf_cpumask_test_cpu(0, cast(cpumask)))
                        /* 不应该发生。 */
                        goto release_exit;

                /* struct cpumask * 指针，如 task->cpus_ptr 也可以被查询。 */
                if (bpf_cpumask_test_cpu(0, task->cpus_ptr))
                        bpf_printk("任务 %s 可以使用 CPU %d", task->comm, 0);

        release_exit:
                bpf_cpumask_release(cpumask);
                return 0;
        }

---

`bpf_cpumask_test_and_set_cpu()`和`bpf_cpumask_test_and_clear_cpu()`是互补的kfuncs，允许调用者原子性地测试和设置（或清除）CPU：

.. kernel-doc:: kernel/bpf/cpumask.c
   :identifiers: bpf_cpumask_test_and_set_cpu bpf_cpumask_test_and_clear_cpu

---

我们还可以使用`bpf_cpumask_setall()`和`bpf_cpumask_clear()`一次性设置和清除整个`struct bpf_cpumask *`对象：

.. kernel-doc:: kernel/bpf/cpumask.c
   :identifiers: bpf_cpumask_setall bpf_cpumask_clear

#### 3.1.2 CPU掩码之间的操作

除了在一个单独的cpumask中设置和清除单个CPU，调用者还可以使用`bpf_cpumask_and()`、`bpf_cpumask_or()`和`bpf_cpumask_xor()`在多个cpumasks之间执行位操作：

.. kernel-doc:: kernel/bpf/cpumask.c
   :identifiers: bpf_cpumask_and bpf_cpumask_or bpf_cpumask_xor

以下是一个使用方法的示例。请注意，这个示例中显示的一些kfuncs将在下面更详细地介绍：

.. code-block:: c

        /**
         * 一个示例追踪点展示如何使用位运算符（以及查询）来修改cpumask
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

                // ...安全创建另外两个掩码... */

                bpf_cpumask_set_cpu(0, mask1);
                bpf_cpumask_set_cpu(1, mask2);
                bpf_cpumask_and(dst1, (const struct cpumask *)mask1, (const struct cpumask *)mask2);
                if (!bpf_cpumask_empty((const struct cpumask *)dst1))
                        /* 不应该发生。 */
                        goto release_exit;

                bpf_cpumask_or(dst1, (const struct cpumask *)mask1, (const struct cpumask *)mask2);
                if (!bpf_cpumask_test_cpu(0, (const struct cpumask *)dst1))
                        /* 不应该发生。 */
                        goto release_exit;

                if (!bpf_cpumask_test_cpu(1, (const struct cpumask *)dst1))
                        /* 不应该发生。 */
                        goto release_exit;

                bpf_cpumask_xor(dst2, (const struct cpumask *)mask1, (const struct cpumask *)mask2);
                if (!bpf_cpumask_equal((const struct cpumask *)dst1,
                                       (const struct cpumask *)dst2))
                        /* 不应该发生。 */
                        goto release_exit;

         release_exit:
                bpf_cpumask_release(mask1);
                bpf_cpumask_release(mask2);
                bpf_cpumask_release(dst1);
                bpf_cpumask_release(dst2);
                return 0;
        }

---

整个cpumask的内容可以通过`bpf_cpumask_copy()`复制到另一个中：

.. kernel-doc:: kernel/bpf/cpumask.c
   :identifiers: bpf_cpumask_copy

---

.. _cpumasks-querying-label:

#### 3.2 查询CPU掩码

除了上述kfuncs外，还有一组只读kfuncs可用于查询cpumasks的内容
.. kernel-doc:: kernel/bpf/cpumask.c
   :identifiers: bpf_cpumask_first bpf_cpumask_first_zero bpf_cpumask_first_and
                 bpf_cpumask_test_cpu bpf_cpumask_weight

.. kernel-doc:: kernel/bpf/cpumask.c
   :identifiers: bpf_cpumask_equal bpf_cpumask_intersects bpf_cpumask_subset
                 bpf_cpumask_empty bpf_cpumask_full

.. kernel-doc:: kernel/bpf/cpumask.c
   :identifiers: bpf_cpumask_any_distribute bpf_cpumask_any_and_distribute

---

上面展示了一些这些查询kfuncs的示例用法。我们在这里不重复那些示例。但是，请注意，所有上述kfuncs都在`tools/testing/selftests/bpf/progs/cpumask_success.c`_中进行了测试，因此如果你正在寻找更多关于如何使用它们的示例，请查看那里。
.. _tools/testing/selftests/bpf/progs/cpumask_success.c:
   https://git.kernel.org/pub/scm/linux/kernel/git/stable/linux.git/tree/tools/testing/selftests/bpf/progs/cpumask_success.c


### 4. 添加BPF CPU掩码kfuncs

支持的BPF CPU掩码kfuncs集与include/linux/cpumask.h中的CPU掩码操作还不完全匹配。如果需要，可以轻松地将任何这些CPU掩码操作封装为一个新的kfunc。如果你想支持一个新的CPU掩码操作，请随时提交补丁。如果你确实添加了一个新的CPU掩码kfunc，请在此处记录它，并向CPU掩码自测套件添加任何相关的自测用例。
