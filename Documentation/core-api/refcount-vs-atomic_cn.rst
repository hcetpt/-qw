======================
refcount_t API 与 atomic_t 的比较
======================

.. contents:: 目录
   :local:

介绍
============

refcount_t API 的目标是为实现对象的引用计数提供一个最小化的 API。虽然来自 lib/refcount.c 的通用、架构无关的实现底层使用了原子操作，但在内存排序保证方面，某些 `refcount_*()` 和 `atomic_*()` 函数之间存在一些差异。本文档概述了这些差异，并提供了相应的示例，以便维护者根据这些内存排序保证的变化验证其代码。
本文档中使用的术语试图遵循 tools/memory-model/Documentation/explanation.txt 中定义的形式化 LKMM（Linux Kernel Memory Model）。memory-barriers.txt 和 atomic_t.txt 提供了关于一般内存排序以及原子操作具体方面的更多背景信息。

相关的内存排序类型
==================

.. note:: 以下部分仅涵盖与原子操作和引用计数器相关的一些内存排序类型，这些类型在本文档中被使用。对于更广泛的视角，请参阅 memory-barriers.txt 文档。

在没有任何内存排序保证的情况下（即完全无序），原子操作和引用计数器只提供原子性和程序顺序（po）关系（在同一 CPU 上）。它保证每个 `atomic_*()` 和 `refcount_*()` 操作都是原子性的，并且指令在同一 CPU 上按程序顺序执行。这是通过 READ_ONCE()/WRITE_ONCE() 和比较-交换原语实现的。

强（全）内存排序保证所有先前的加载和存储（所有 po-更早的指令）在同一 CPU 上完成，然后才执行任何 po-之后的指令。它还保证所有 po-更早的存储在同一 CPU 上以及从其他 CPU 传播的所有存储必须传播到所有其他 CPU，然后才执行原始 CPU 上的任何 po-之后的指令（A-累积属性）。这是通过 smp_mb() 实现的。

RELEASE 内存排序保证所有先前的加载和存储（所有 po-更早的指令）在同一 CPU 上完成，然后再进行该操作。它还保证所有 po-更早的存储在同一 CPU 上以及从其他 CPU 传播的所有存储必须传播到所有其他 CPU，然后才执行 RELEASE 操作（A-累积属性）。这是通过 smp_store_release() 实现的。
ACQUIRE内存排序保证在同一CPU上所有后续的加载和存储（所有po-later指令）在获取操作完成后完成。它还保证了同一CPU上的所有po-later存储操作必须在执行获取操作后传播到所有其他CPU。这是通过`smp_acquire__after_ctrl_dep()`实现的。

对引用计数器的成功操作（如果成功获取了对象的引用，即引用计数增加或添加发生，函数返回true）的控制依赖性保证进一步的存储操作会按照这个操作排序。

存储操作的控制依赖性不是通过任何显式的屏障实现的，而是依赖于CPU不对存储进行推测。这仅是一种单CPU的关系，并不对其他CPU提供任何保证。

函数比较
========

情况1) - 非“读取/修改/写入”(RMW)操作
--------------------------------------------

函数变化：

* `atomic_set()` → `refcount_set()`
* `atomic_read()` → `refcount_read()`

内存排序保证的变化：

* 无（两者都是完全无序的）

情况2) - 基于递增的操作，不返回值
------------------------------------------

函数变化：

* `atomic_inc()` → `refcount_inc()`
* `atomic_add()` → `refcount_add()`

内存排序保证的变化：

* 无（两者都是完全无序的）

情况3) - 基于递减的RMW操作，不返回值
---------------------------------------------

函数变化：

* `atomic_dec()` → `refcount_dec()`

内存排序保证的变化：

* 完全无序 → RELEASE排序

情况4) - 基于递增的RMW操作，返回一个值
--------------------------------------------

函数变化：

* `atomic_inc_not_zero()` → `refcount_inc_not_zero()`
* 没有对应的原子操作 → `refcount_add_not_zero()`

内存排序保证的变化：

* 完全有序 → 成功时对存储操作的控制依赖性

.. 注意:: 我们这里真的假设必要的排序是由于获得了指向该对象的指针而提供的！

情况5) - 通用基于递减的RMW操作，返回一个值
--------------------------------------------------

函数变化：

* `atomic_dec_and_test()` → `refcount_dec_and_test()`
* `atomic_sub_and_test()` → `refcount_sub_and_test()`

内存排序保证的变化：

* 完全有序 → RELEASE排序 + 成功时的ACQUIRE排序

情况6) - 其他基于递减的RMW操作，返回一个值
----------------------------------------------

函数变化：

* 没有对应的原子操作 → `refcount_dec_if_one()`
* `atomic_add_unless(&var, -1, 1)` → `refcount_dec_not_one(&var)`

内存排序保证的变化：

* 完全有序 → RELEASE排序 + 控制依赖性

.. 注意:: `atomic_add_unless()`只在成功时提供完全排序

情况7) - 基于锁的RMW
------------------------

函数变化：

* `atomic_dec_and_lock()` → `refcount_dec_and_lock()`
* `atomic_dec_and_mutex_lock()` → `refcount_dec_and_mutex_lock()`

内存排序保证的变化：

* 完全有序 → RELEASE排序 + 控制依赖性 + 在成功时持有spin_lock()
