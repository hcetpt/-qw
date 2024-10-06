.. _kernel_hacking_lock:

===========================
不可靠的锁使用指南
===========================

:作者: Rusty Russell

简介
============

欢迎来到Rusty的极为不可靠的内核锁使用指南。本文档描述了Linux内核2.6中的锁系统。
随着HyperThreading和Linux内核中抢占功能的广泛应用，每个在内核上进行开发的人都需要了解SMP并发和锁的基本知识。

并发问题
============================

（如果你知道什么是竞态条件，可以跳过这一部分）
在一个普通的程序中，你可以像这样递增一个计数器：

::

          very_important_count++;

你期望发生的情况如下：

.. table:: 预期结果

  +------------------------------------+------------------------------------+
  | 实例1                              | 实例2                              |
  +====================================+====================================+
  | 读取very_important_count (5)       |                                    |
  +------------------------------------+------------------------------------+
  | 加1 (6)                            |                                    |
  +------------------------------------+------------------------------------+
  | 写入very_important_count (6)       |                                    |
  +------------------------------------+------------------------------------+
  |                                    | 读取very_important_count (6)       |
  +------------------------------------+------------------------------------+
  |                                    | 加1 (7)                            |
  +------------------------------------+------------------------------------+
  |                                    | 写入very_important_count (7)       |
  +------------------------------------+------------------------------------+

实际可能发生的情况如下：

.. table:: 可能的结果

  +------------------------------------+------------------------------------+
  | 实例1                              | 实例2                              |
  +====================================+====================================+
  | 读取very_important_count (5)       |                                    |
  +------------------------------------+------------------------------------+
  |                                    | 读取very_important_count (5)       |
  +------------------------------------+------------------------------------+
  | 加1 (6)                            |                                    |
  +------------------------------------+------------------------------------+
  |                                    | 加1 (6)                            |
  +------------------------------------+------------------------------------+
  | 写入very_important_count (6)       |                                    |
  +------------------------------------+------------------------------------+
  |                                    | 写入very_important_count (6)       |
  +------------------------------------+------------------------------------+

竞态条件与临界区
------------------------------------

这种重叠，其中结果依赖于多个任务之间的相对时间顺序，被称为竞态条件。包含并发问题的代码段称为临界区。尤其是在Linux开始运行在SMP机器上之后，它们成为了内核设计和实现中的主要问题之一。
抢占也可能产生相同的效果，即使只有一个CPU：通过在临界区期间抢占一个任务，我们也会遇到相同的竞态条件。在这种情况下，抢占的线程可能会自己运行临界区。
解决办法是识别这些同时访问发生的情况，并使用锁确保只有单个实例可以在任何时候进入临界区。Linux内核中有许多友好的原语帮助你实现这一点。当然也有一些不友好的原语，但我会假装它们不存在。

Linux内核中的锁
===========================

如果我能给你一条关于锁的建议：**保持简单**
尽量避免引入新的锁。

内核锁的两种主要类型：自旋锁和互斥锁
-----------------------------------------------------

内核锁主要有两种类型。基本类型是自旋锁（``include/asm/spinlock.h``），这是一种非常简单的单持有者锁：如果你无法获取自旋锁，你会不断尝试（自旋）直到成功。自旋锁非常小且快速，可以在任何地方使用。
第二种类型是互斥锁（``include/linux/mutex.h``）：它类似于自旋锁，但你可以阻塞持有互斥锁。如果你无法锁定一个互斥锁，你的任务会挂起，并在互斥锁被释放时被唤醒。这意味着在等待过程中，CPU可以做其他事情。有许多情况是你根本不能睡眠（参见`哪些函数可以在中断中调用？`_），因此必须使用自旋锁。
两种类型的锁都不是递归的：参见
`死锁：简单和高级`_

在单处理器内核中的锁
------------------------

对于编译时没有启用``CONFIG_SMP``并且没有启用``CONFIG_PREEMPT``的内核，自旋锁根本不存在。这是一个出色的设计决策：当没有任何其他进程可以同时运行时，没有必要使用锁。
如果内核编译时没有启用``CONFIG_SMP``，但启用了``CONFIG_PREEMPT``，那么自旋锁只是禁用抢占，这足以防止任何竞争条件。大多数情况下，我们可以将抢占视为等同于SMP，并且不必单独担心它。
你应该始终在启用了``CONFIG_SMP``和``CONFIG_PREEMPT``的情况下测试你的锁代码，即使你没有SMP测试机器，因为这样仍然可以捕捉到某些类型的锁错误。

互斥锁依然存在，因为它们是用户上下文间同步所必需的，如下所述。

仅在用户上下文中加锁
----------------------------

如果你有一个数据结构，它只在用户上下文中被访问，那么你可以使用一个简单的互斥锁（`include/linux/mutex.h`）来保护它。这是最简单的情况：初始化该互斥锁，
然后你可以调用`mutex_lock_interruptible()`来获取互斥锁，以及调用`mutex_unlock()`来释放它。还有一种`mutex_lock()`，应尽量避免使用，因为它在接收到信号时不会返回。
示例：`net/netfilter/nf_sockopt.c`允许注册新的`setsockopt()`和`getsockopt()`调用，通过`nf_register_sockopt()`进行注册。注册和注销仅在模块加载和卸载时进行（以及启动时，此时没有并发），而注册列表仅在处理未知的`setsockopt()`或`getsockopt()`系统调用时才被查询。`nf_sockopt_mutex`非常适合保护这一点，特别是因为`setsockopt`和`getsockopt`调用可能会休眠。

在用户上下文与软中断之间加锁
-----------------------------------------

如果软中断共享了用户上下文的数据，你有两个问题：
首先，当前用户上下文可能会被软中断中断；其次，临界区可能从另一个CPU进入。这就是使用`spin_lock_bh()`（`include/linux/spinlock.h`）的地方。它在这个CPU上禁用软中断，然后获取锁。
`spin_unlock_bh()` 执行相反的操作。（其中的 `_bh` 后缀是“Bottom Halves”的历史遗留，这是软件中断的老名称。在理想的世界里，它应该被称为 `spin_lock_softirq()`）
请注意，您也可以使用 `spin_lock_irq()` 或 `spin_lock_irqsave()`，这些也会停止硬件中断：请参见“硬中断上下文”。
这对于单处理器系统（UP）也完全适用：自旋锁消失，这个宏简化为 `local_bh_disable()`（在 `include/linux/interrupt.h` 中），从而保护您免受软中断被运行的影响。

### 在用户上下文和任务线程之间的锁定

这与上面的情况完全相同，因为任务线程实际上是通过软中断运行的。
### 在用户上下文和定时器之间的锁定

这也与上面的情况完全相同，因为定时器实际上是通过软中断运行的。从锁定的角度来看，任务线程和定时器是相同的。
### 在任务线程/定时器之间的锁定

有时一个任务线程或定时器可能希望与其他任务线程或定时器共享数据。

#### 相同的任务线程/定时器

由于任务线程不会同时在两个 CPU 上运行，因此您不必担心您的任务线程是可重入的（即同时运行两次），即使是在对称多处理（SMP）系统中也是如此。

#### 不同的任务线程/定时器

如果另一个任务线程/定时器希望与您的任务线程或定时器共享数据，则双方都需要使用 `spin_lock()` 和 `spin_unlock()` 调用。这里不需要 `spin_lock_bh()`，因为您已经在任务线程中，同一 CPU 上不会有其他任务线程运行。

### 在软中断之间的锁定

通常一个软中断可能希望与自身或其他任务线程/定时器共享数据。

#### 相同的软中断

相同的软中断可以在其他 CPU 上运行：您可以使用每 CPU 数组（参见“每 CPU 数据”）以获得更好的性能。如果您已经使用了软中断，那么您可能足够关心可扩展性性能，以至于可以承受额外的复杂性。
您需要使用 `spin_lock()` 和 `spin_unlock()` 来保护共享数据，无论这些数据是定时器、任务项（tasklet）、不同的软中断（softirq）还是相同的或另一个软中断：它们中的任何一个都可能在不同的 CPU 上运行。

### 不同的软中断
~~~~~~~~~~~~~~~~~~

您需要使用 `spin_lock()` 和 `spin_unlock()` 来保护共享数据，无论是定时器、任务项、不同的软中断还是相同的或另一个软中断：它们中的任何一个都可能在不同的 CPU 上运行。

### 硬中断上下文
================

硬件中断通常与一个任务项或软中断进行通信。这通常涉及将工作放入队列中，然后由软中断取出处理。

### 在硬中断和软中断/任务项之间的锁定
----------------------------------------------

如果硬件中断处理器与软中断共享数据，您有两个主要关注点。首先，软中断处理可能会被硬件中断中断；其次，在另一个 CPU 上可能会进入关键区域。这时就需要使用 `spin_lock_irq()`。它定义为禁用该 CPU 上的中断，然后再获取锁。
`spin_unlock_irq()` 则执行相反的操作。

中断处理器不需要使用 `spin_lock_irq()`，因为当中断处理器正在运行时，软中断不会运行：它可以使用 `spin_lock()`，这稍微快一些。唯一的例外是，如果另一个不同的硬件中断处理器使用相同的锁，则需要使用 `spin_lock_irq()` 来阻止其中断我们。

这对于单处理器系统（UP）也完全适用：自旋锁消失，并且这个宏仅仅变成了 `local_irq_disable()`（位于 `include/asm/smp.h`），用于保护您免受软中断/任务项/底半部（bottom half，BH）的运行干扰。

`spin_lock_irqsave()`（位于 `include/linux/spinlock.h`）是一个变体，它保存了中断是否已开启或关闭的状态，并将此状态传递给 `spin_unlock_irqrestore()`。这意味着同样的代码可以在硬中断处理器内部（其中断已经关闭）和软中断中（其中断需要关闭）使用。

请注意，软中断（以及因此任务项和定时器）会在从硬件中断返回时运行，因此 `spin_lock_irq()` 也会阻止这些操作。从这个意义上讲，`spin_lock_irqsave()` 是最通用和强大的锁定函数。
### 在两个硬中断处理程序之间加锁
-------------------------------------

在两个中断处理程序之间共享数据的情况很少见，但如果你确实需要这样做，应该使用 `spin_lock_irqsave()`。是否在中断处理程序内部禁用所有中断取决于具体的架构。
锁定速查表
=======================

Pete Zaitcev 提供了以下总结：

- 如果你在进程上下文中（任何系统调用）并希望锁定其他进程，使用互斥锁。你可以获取一个互斥锁并休眠（如 `copy_from_user()` 或 `kmalloc(x, GFP_KERNEL)`）
- 否则（== 数据可以在中断中被访问），使用 `spin_lock_irqsave()` 和 `spin_unlock_irqrestore()`
- 避免持有自旋锁超过五行代码，并且不要在函数调用（除了像 `readb()` 这样的访问器）之间持有自旋锁
最小要求表
-----------------------------

下表列出了各种上下文之间的**最低**加锁要求。在某些情况下，相同的上下文只能在一个 CPU 上运行，因此不需要为该上下文加锁（例如，特定的线程只能在一个 CPU 上运行，但如果它需要与其他线程共享数据，则需要加锁）。
记住上面的建议：你始终可以使用 `spin_lock_irqsave()`，它是所有其他自旋锁原语的超集。
============== ============= ============= ========= ========= ========= ========= ======= ======= ============== ==============
.              IRQ Handler A IRQ Handler B Softirq A Softirq B Tasklet A Tasklet B Timer A Timer B User Context A User Context B
============== ============= ============= ========= ========= ========= ========= ======= ======= ============== ==============
IRQ Handler A  None
IRQ Handler B  SLIS          None
Softirq A      SLI           SLI           SL
Softirq B      SLI           SLI           SL        SL
Tasklet A      SLI           SLI           SL        SL        None
Tasklet B      SLI           SLI           SL        SL        SL        None
Timer A        SLI           SLI           SL        SL        SL        SL        None
Timer B        SLI           SLI           SL        SL        SL        SL        SL      None
User Context A SLI           SLI           SLBH      SLBH      SLBH      SLBH      SLBH    SLBH    None
User Context B SLI           SLI           SLBH      SLBH      SLBH      SLBH      SLBH    SLBH    MLI            None
============== ============= ============= ========= ========= ========= ========= ======= ======= ============== ==============

表：加锁要求表

+--------+----------------------------+
| SLIS   | spin_lock_irqsave          |
+--------+----------------------------+
| SLI    | spin_lock_irq              |
+--------+----------------------------+
| SL     | spin_lock                  |
+--------+----------------------------+
| SLBH   | spin_lock_bh               |
+--------+----------------------------+
| MLI    | mutex_lock_interruptible   |
+--------+----------------------------+

表：加锁要求表图例

尝试加锁函数
=====================

有一些函数试图一次立即获取锁，并立即返回一个值来指示是否成功获取锁。
如果在其他线程持有锁时你不需要访问受锁保护的数据，可以使用这些函数。如果之后你需要访问受锁保护的数据，则应在稍后获取锁。
`spin_trylock()` 不会自旋，而是在第一次尝试时获取自旋锁返回非零值，否则返回 0。此函数可以在所有上下文中使用，就像 `spin_lock()` 一样：你必须禁用可能中断你的上下文并获取自旋锁。
`mutex_trylock()` 不会挂起你的任务，而是在第一次尝试时获取互斥锁返回非零值，否则返回 0。此函数不能安全地用于硬件或软件中断上下文中，尽管它不会睡眠。
常见示例
===============

让我们逐步分析一个简单的示例：一个数字到名称映射的缓存。
该缓存记录了每个对象被使用的次数，并在缓存满时移除最少使用的对象。
所有操作都在用户上下文中
-------------------

对于我们的第一个示例，我们假设所有操作都在用户上下文（即来自系统调用）中进行，因此我们可以使用休眠。这意味着我们可以使用互斥锁来保护缓存及其内部的所有对象。以下是代码：

```c
#include <linux/list.h>
#include <linux/slab.h>
#include <linux/string.h>
#include <linux/mutex.h>
#include <asm/errno.h>

struct object {
    struct list_head list;
    int id;
    char name[32];
    int popularity;
};

/* 保护缓存、cache_num 及其内部的对象 */
static DEFINE_MUTEX(cache_lock);
static LIST_HEAD(cache);
static unsigned int cache_num = 0;
#define MAX_CACHE_SIZE 10

/* 必须持有 cache_lock */
static struct object *__cache_find(int id) {
    struct object *i;

    list_for_each_entry(i, &cache, list)
        if (i->id == id) {
            i->popularity++;
            return i;
        }
    return NULL;
}

/* 必须持有 cache_lock */
static void __cache_delete(struct object *obj) {
    BUG_ON(!obj);
    list_del(&obj->list);
    kfree(obj);
    cache_num--;
}

/* 必须持有 cache_lock */
static void __cache_add(struct object *obj) {
    list_add(&obj->list, &cache);
    if (++cache_num > MAX_CACHE_SIZE) {
        struct object *i, *outcast = NULL;
        list_for_each_entry(i, &cache, list) {
            if (!outcast || i->popularity < outcast->popularity)
                outcast = i;
        }
        __cache_delete(outcast);
    }
}

int cache_add(int id, const char *name) {
    struct object *obj;

    if ((obj = kmalloc(sizeof(*obj), GFP_KERNEL)) == NULL)
        return -ENOMEM;

    strscpy(obj->name, name, sizeof(obj->name));
    obj->id = id;
    obj->popularity = 0;

    mutex_lock(&cache_lock);
    __cache_add(obj);
    mutex_unlock(&cache_lock);
    return 0;
}

void cache_delete(int id) {
    mutex_lock(&cache_lock);
    __cache_delete(__cache_find(id));
    mutex_unlock(&cache_lock);
}

int cache_find(int id, char *name) {
    struct object *obj;
    int ret = -ENOENT;

    mutex_lock(&cache_lock);
    obj = __cache_find(id);
    if (obj) {
        ret = 0;
        strcpy(name, obj->name);
    }
    mutex_unlock(&cache_lock);
    return ret;
}
```

请注意，我们在添加、删除或查找缓存时始终确保持有 `cache_lock`：缓存基础设施本身和对象的内容都受到该锁的保护。在这种情况下，这是很容易做到的，因为我们为用户提供数据副本，从不让他们直接访问对象。

这里有一个常见的优化：在 `cache_add()` 中，我们在获取锁之前设置对象字段。这是安全的，因为直到我们将它放入缓存之前，其他任何人都无法访问它。

从中断上下文访问
----------------------

现在考虑 `cache_find()` 可以从中断上下文（硬件中断或软中断）调用的情况：例如定时器删除缓存中的对象。

下面展示了变更内容，采用标准补丁格式：`-` 表示删除的行，`+` 表示添加的行：

```diff
--- cache.c.usercontext 2003-12-09 13:58:54.000000000 +1100
+++ cache.c.interrupt   2003-12-09 14:07:49.000000000 +1100
@@ -12,7 +12,7 @@
         int popularity;
 };

-static DEFINE_MUTEX(cache_lock);
+static DEFINE_SPINLOCK(cache_lock);
 static LIST_HEAD(cache);
 static unsigned int cache_num = 0;
 #define MAX_CACHE_SIZE 10
@@ -55,6 +55,7 @@
 int cache_add(int id, const char *name) {
         struct object *obj;
 +       unsigned long flags;

         if ((obj = kmalloc(sizeof(*obj), GFP_KERNEL)) == NULL)
                 return -ENOMEM;
@@ -63,30 +64,33 @@
         obj->id = id;
         obj->popularity = 0;

 -       mutex_lock(&cache_lock);
 +       spin_lock_irqsave(&cache_lock, flags);
         __cache_add(obj);
 -       mutex_unlock(&cache_lock);
 +       spin_unlock_irqrestore(&cache_lock, flags);
         return 0;
 }

 void cache_delete(int id) {
 -       mutex_lock(&cache_lock);
 +       unsigned long flags;
 +
 +       spin_lock_irqsave(&cache_lock, flags);
         __cache_delete(__cache_find(id));
 -       mutex_unlock(&cache_lock);
 +       spin_unlock_irqrestore(&cache_lock, flags);
 }

 int cache_find(int id, char *name) {
         struct object *obj;
         int ret = -ENOENT;
 +       unsigned long flags;

 -       mutex_lock(&cache_lock);
 +       spin_lock_irqsave(&cache_lock, flags);
         obj = __cache_find(id);
         if (obj) {
                 ret = 0;
                 strcpy(name, obj->name);
         }
 -       mutex_unlock(&cache_lock);
 +       spin_unlock_irqrestore(&cache_lock, flags);
         return ret;
 }
```

请注意，`spin_lock_irqsave()` 会关闭中断（如果它们已打开），否则什么也不做（如果我们已经在中断处理程序中），因此这些函数可以在任何上下文中安全调用。

不幸的是，`cache_add()` 调用了带有 `GFP_KERNEL` 标志的 `kmalloc()`，这仅在用户上下文中是合法的。我假设 `cache_add()` 仍然只在用户上下文中调用，否则这应该成为 `cache_add()` 的参数。

将对象暴露给此文件之外
----------------------------------

如果我们对象包含更多信息，则仅仅复制信息可能不够：代码的其他部分可能希望保持对这些对象的指针，而不是每次查找 id。这会产生两个问题。

第一个问题是，我们使用 `cache_lock` 来保护对象：我们需要将其设为非静态以便其余代码可以使用它。
这使得加锁变得更加复杂，因为现在对象不再集中在一个地方。

第二个问题是生命周期问题：如果另一个结构体持有一个对象的指针，那么它显然期望这个指针保持有效。不幸的是，这一点只有在你持有锁的时候才能保证，否则可能会有人调用 `cache_delete()`，甚至更糟的是，添加另一个对象并重用相同的地址。

由于只有一个锁，你不能永远持有它，否则其他人将无法完成任何工作。

解决这个问题的方法是使用引用计数：每个持有对象指针的人都会在首次获取对象时增加引用计数，并在完成后减少引用计数。当引用计数减为零时，就知道该对象不再被使用，可以实际删除它。

以下是代码：

```diff
--- cache.c.interrupt   2003-12-09 14:25:43.000000000 +1100
+++ cache.c.refcnt  2003-12-09 14:33:05.000000000 +1100
@@ -7,6 +7,7 @@
 struct object
 {
         struct list_head list;
+        unsigned int refcnt;
         int id;
         char name[32];
         int popularity;
@@ -17,6 +18,35 @@
 static unsigned int cache_num = 0;
 #define MAX_CACHE_SIZE 10

+static void __object_put(struct object *obj)
+{
+        if (--obj->refcnt == 0)
+                kfree(obj);
+}
+
+static void __object_get(struct object *obj)
+{
+        obj->refcnt++;
+}
+
+void object_put(struct object *obj)
+{
+        unsigned long flags;
+
+        spin_lock_irqsave(&cache_lock, flags);
+        __object_put(obj);
+        spin_unlock_irqrestore(&cache_lock, flags);
+}
+
+void object_get(struct object *obj)
+{
+        unsigned long flags;
+
+        spin_lock_irqsave(&cache_lock, flags);
+        __object_get(obj);
+        spin_unlock_irqrestore(&cache_lock, flags);
+}
+
 /* 必须持有 cache_lock */
 static struct object *__cache_find(int id)
 {
@@ -35,6 +65,7 @@
 {
         BUG_ON(!obj);
         list_del(&obj->list);
+        __object_put(obj);
         cache_num--;
 }
 
@@ -63,6 +94,7 @@
         strscpy(obj->name, name, sizeof(obj->name));
         obj->id = id;
         obj->popularity = 0;
+        obj->refcnt = 1; /* 缓存持有引用 */

         spin_lock_irqsave(&cache_lock, flags);
         __cache_add(obj);
@@ -79,18 +111,15 @@
         spin_unlock_irqrestore(&cache_lock, flags);
 }
 
-int cache_find(int id, char *name)
+struct object *cache_find(int id)
 {
         struct object *obj;
-        int ret = -ENOENT;
         unsigned long flags;
 
         spin_lock_irqsave(&cache_lock, flags);
         obj = __cache_find(id);
-        if (obj) {
-                ret = 0;
-                strcpy(name, obj->name);
-        }
+        if (obj)
+                __object_get(obj);
         spin_unlock_irqrestore(&cache_lock, flags);
-        return ret;
+        return obj;
 }
 
我们将引用计数封装在标准的 `get` 和 `put` 函数中。现在我们可以从 `cache_find()` 返回对象本身，这样用户可以在持有对象时休眠（例如，将数据复制到用户空间）。
另一个需要注意的点是，我提到应该为每个指向对象的指针持有一个引用，因此当对象首次插入缓存时，引用计数为 1。在某些版本中，框架不持有引用计数，但这些版本更加复杂。

使用原子操作进行引用计数
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

实际上，通常会使用 `atomic_t` 类型来表示引用计数。在 `include/asm/atomic.h` 中定义了许多原子操作：这些操作在系统的所有 CPU 上都是原子的，因此不需要锁。在这种情况下，使用原子操作比使用自旋锁更简单，尽管对于复杂的操作使用自旋锁更清晰。使用 `atomic_inc()` 和 `atomic_dec_and_test()` 替代标准的增减操作符，并且不再使用锁来保护引用计数本身。

```diff
--- cache.c.refcnt  2003-12-09 15:00:35.000000000 +1100
+++ cache.c.refcnt-atomic   2003-12-11 15:49:42.000000000 +1100
@@ -7,7 +7,7 @@
 struct object
 {
         struct list_head list;
-        unsigned int refcnt;
+        atomic_t refcnt;
         int id;
         char name[32];
         int popularity;
@@ -18,33 +18,15 @@
 static unsigned int cache_num = 0;
 #define MAX_CACHE_SIZE 10
 
-static void __object_put(struct object *obj)
-{
-        if (--obj->refcnt == 0)
-                kfree(obj);
-}
-
-static void __object_get(struct object *obj)
-{
-        obj->refcnt++;
-}
-
 void object_put(struct object *obj)
 {
-        unsigned long flags;
-
-        spin_lock_irqsave(&cache_lock, flags);
-        __object_put(obj);
-        spin_unlock_irqrestore(&cache_lock, flags);
+        if (atomic_dec_and_test(&obj->refcnt))
+                kfree(obj);
 }
 
 void object_get(struct object *obj)
 {
-        unsigned long flags;
-
-        spin_lock_irqsave(&cache_lock, flags);
-        __object_get(obj);
-        spin_unlock_irqrestore(&cache_lock, flags);
+        atomic_inc(&obj->refcnt);
 }
 
 /* 必须持有 cache_lock */
@@ -65,7 +47,7 @@
 {
         BUG_ON(!obj);
         list_del(&obj->list);
-        __object_put(obj);
+        object_put(obj);
         cache_num--;
 }
 
@@ -94,7 +76,7 @@
         strscpy(obj->name, name, sizeof(obj->name));
         obj->id = id;
         obj->popularity = 0;
-        obj->refcnt = 1; /* 缓存持有引用 */
+        atomic_set(&obj->refcnt, 1); /* 缓存持有引用 */
 
         spin_lock_irqsave(&cache_lock, flags);
         __cache_add(obj);
@@ -119,7 +101,7 @@
         spin_lock_irqsave(&cache_lock, flags);
         obj = __cache_find(id);
         if (obj)
-                __object_get(obj);
+                object_get(obj);
         spin_unlock_irqrestore(&cache_lock, flags);
         return obj;
 }
```

保护对象本身
------------------

在这些示例中，我们假设对象（除了引用计数）一旦创建后就不会改变。如果我们希望允许名称改变，有三种可能性：

-  可以使 `cache_lock` 非静态，并告诉人们在更改任何对象的名称之前获取该锁。
-  可以提供一个 `cache_obj_rename()` 函数，该函数获取锁并为调用者更改名称，并告诉所有人使用该函数。
-  可以使 `cache_lock` 仅保护缓存本身，并使用另一个锁来保护名称。
理论上，你可以将锁细分到每个对象的每个字段。实际上，最常见的变体有：

- 一个保护基础设施（在这个例子中是 `cache` 列表）和所有对象的锁。这是我们迄今为止所做过的。
- 一个保护基础设施（包括对象内部的列表指针）的锁，以及一个在对象内部保护该对象其余部分的锁。
- 多个保护基础设施的锁（例如，每个哈希链一个锁），可能还包括每个对象的单独锁。

以下是“每个对象一个锁”的实现：

```
--- cache.c.refcnt-atomic   2003-12-11 15:50:54.000000000 +1100
+++ cache.c.perobjectlock   2003-12-11 17:15:03.000000000 +1100
@@ -6,11 +6,17 @@

 struct object
 {
+        /* 这两个由 cache_lock 保护。*/
         struct list_head list;
+        int popularity;
+
         atomic_t refcnt;
+        
+        /* 创建后不再改变。*/
         int id;
+        
+        spinlock_t lock; /* 保护 name 字段 */
         char name[32];
-        int popularity;
 };

 static DEFINE_SPINLOCK(cache_lock);
@@ -77,6 +84,7 @@
         obj->id = id;
         obj->popularity = 0;
         atomic_set(&obj->refcnt, 1); /* 缓存持有引用 */
+        spin_lock_init(&obj->lock);

         spin_lock_irqsave(&cache_lock, flags);
         __cache_add(obj);
```

请注意，我决定让流行度计数由 `cache_lock` 而不是每个对象的锁来保护：这是因为流行度计数（如同对象内部的 `struct list_head` 类型一样）从逻辑上讲属于基础设施的一部分。这样，在 `__cache_add()` 中寻找最不流行的对象时，我不需要获取每个对象的锁。
我还决定 `id` 成员是不可更改的，因此在 `__cache_find()` 中检查 `id` 时不需要获取每个对象的锁：对象锁仅由希望读取或写入 `name` 字段的调用者使用。
同样需要注意的是，我添加了一个注释来描述哪些数据由哪个锁保护。这是极其重要的，因为它描述了代码在运行时的行为，并且很难仅仅通过阅读代码获得。正如 Alan Cox 所说，“锁定数据，而不是代码”。

常见问题
==========

死锁：简单和高级
------------------

有一个编程错误是一段代码尝试两次获取同一个自旋锁：它将无限循环等待锁被释放（Linux 中的自旋锁、读写锁和互斥锁都不是递归的）。这个诊断非常简单：不是那种要连续熬夜五天与毛茸茸的小兔子对话的问题。
对于稍微复杂一点的情况，想象你有一个区域被软中断和用户上下文共享。如果你使用 `spin_lock()` 来保护它，那么当用户上下文持有锁时可能会被软中断打断，而软中断将会无限循环试图获取同一个锁。
这两种情况都称为死锁，如上所述，即使是在单 CPU 上也会发生（虽然在 UP 编译下不会，因为自旋锁在 `CONFIG_SMP`=n 的内核编译中消失。你仍然会在第二个示例中得到数据损坏）。
这种完全的死锁很容易诊断：在多处理器系统（SMP）机器上，看门狗定时器或编译时设置 `DEBUG_SPINLOCK`（`include/linux/spinlock.h`）会立即显示出这个问题。
一个更复杂的问题是所谓的“致命拥抱”，涉及两个或更多的锁。假设你有一个哈希表：表中的每个条目都是一个自旋锁，以及一个哈希对象链。在软中断处理程序中，有时你需要将一个对象从哈希表的一个位置移动到另一个位置：你获取旧哈希链的自旋锁和新哈希链的自旋锁，然后从旧链中删除该对象，并将其插入新链。

这里有两个问题。首先，如果你的代码试图将对象移动到同一个链上，它会在尝试两次锁定时自我死锁。其次，如果另一个CPU上的相同软中断正在尝试反向移动另一个对象，可能会发生以下情况：

+-----------------------+-----------------------+
| CPU 1                 | CPU 2                 |
+=======================+=======================+
| 获取锁 A -> 成功      | 获取锁 B -> 成功      |
+-----------------------+-----------------------+
| 获取锁 B -> 自旋等待  | 获取锁 A -> 自旋等待  |
+-----------------------+-----------------------+

表：后果

这两个CPU将永远自旋等待，直到对方释放锁。这看起来、闻起来、感觉就像是崩溃了。

防止死锁
-------------------

教科书会告诉你，如果你总是以相同的顺序锁定，你就永远不会遇到这种类型的死锁。然而实践会告诉你，这种方法并不实用：当我创建一个新的锁时，我不了解内核足够多的信息来确定它在5000个锁层次结构中的位置。

最好的锁是封装的：它们永远不会暴露在头文件中，并且在调用同一文件之外的非平凡函数时也不会持有这些锁。你可以阅读这段代码并发现它永远不会死锁，因为它在获取一个锁时不会尝试获取另一个锁。使用你的代码的人甚至不需要知道你在使用锁。

一个经典的问题是在提供回调或钩子时：如果你在持有锁的情况下调用这些回调，你可能会遇到简单的死锁或致命拥抱（谁知道回调会做什么？）

过度预防死锁
~~~~~~~~~~~~~~~~~~~~~~~~~

死锁是有问题的，但数据损坏更糟糕。一段代码获取读锁，搜索一个列表，未能找到想要的内容，释放读锁，获取写锁并插入对象，这种情况下存在竞争条件。

竞态定时器：内核爱好
-------------------------------

定时器可以产生其特有的竞争问题。考虑一组对象（列表、哈希等），每个对象都有一个定时器，定时器到期后会销毁该对象。

如果你想销毁整个集合（比如在模块移除时），你可能会这样做：

            /* 这段代码非常非常非常非常差：如果再差一点就会使用匈牙利命名法 */
            spin_lock_bh(&list_lock);

            while (list) {
                    struct foo *next = list->next;
                    timer_delete(&list->timer);
                    kfree(list);
                    list = next;
            }

            spin_unlock_bh(&list_lock);

迟早会在SMP系统上崩溃，因为一个定时器可能刚刚在spin_lock_bh()之前触发，并且它只能在我们spin_unlock_bh()之后才获得锁，然后尝试释放这个元素（而这个元素已经被释放了）！

这可以通过检查timer_delete()的结果来避免：如果返回1，则定时器已被删除；如果返回0，则表示（在这种情况下）定时器当前正在运行，因此我们可以这样做：

            retry:
                    spin_lock_bh(&list_lock);

                    while (list) {
                            struct foo *next = list->next;
                            if (!timer_delete(&list->timer)) {
                                    /* 给定时器一个机会来删除这个元素 */
                                    spin_unlock_bh(&list_lock);
                                    goto retry;
                            }
                            kfree(list);
                            list = next;
                    }

                    spin_unlock_bh(&list_lock);

另一个常见问题是删除那些会重启自身的定时器（通过在其定时器函数末尾调用add_timer()）。
因为这是一个非常常见的容易出现竞争条件的情况，你应该使用 `timer_delete_sync()`（位于 "include/linux/timer.h"）来处理这种情况。在释放定时器之前，应该调用 `timer_shutdown()` 或 `timer_shutdown_sync()`，以防止它被重新启动。任何后续尝试重新启动定时器都将被核心代码默默地忽略。

### 锁定速度

考虑锁定代码的速度时，主要有三个问题需要注意。首先是并发性：当其他人持有锁时，有多少任务会等待。第二是实际获取和释放无争用锁所需的时间。第三是使用更少或更智能的锁。我假设这个锁被频繁使用；否则你不会关心效率。

并发性取决于通常持有锁的时间长度：你应该持有锁足够长的时间，但不要过长。在缓存示例中，我们总是在不持有锁的情况下创建对象，然后仅在准备将对象插入列表时才获取锁。

获取时间取决于锁操作对流水线（pipeline stalls）的影响程度以及这台CPU是否是最后一个获取锁的概率（即，这个锁是否对这台CPU来说是热缓存锁）：在更多CPU的机器上，这种概率迅速下降。以700MHz的Intel Pentium III为例：一条指令大约需要0.7纳秒，原子递增大约需要58纳秒，如果这个锁在这台CPU上是热缓存锁，则获取锁需要160纳秒，而从另一台CPU传输缓存行则需要额外的170到360纳秒。（这些数据来自Paul McKenney的《Linux Journal RCU文章》）

这两个目标是有冲突的：通过将锁拆分成多个部分（如最终的对象锁示例），可以缩短持有锁的时间，但这增加了锁的获取次数，结果往往比使用单个锁更慢。这是提倡锁定简单性的另一个原因。

第三个关注点如下所述：有一些方法可以减少需要进行的锁定操作。

### 读写锁变体

自旋锁和互斥锁都有读写变体：`rwlock_t` 和 :c:type:`struct rw_semaphore <rw_semaphore>`。这些锁将用户分为两类：读者和写者。如果你只是读取数据，你可以获取一个读锁，但要写入数据则需要写锁。许多用户可以持有读锁，但写者必须是唯一的持有者。

如果你的代码清晰地分为读者和写者（就像我们的缓存代码一样），并且锁由读者长时间持有，那么使用这些锁会有帮助。不过，它们比普通锁稍微慢一些，因此实际上 `rwlock_t` 并不总是值得使用。

### 避免锁：读复制更新

有一种特殊的读写锁定方法叫做读复制更新（Read Copy Update）。
使用RCU，读者可以完全避免获取锁：由于我们期望缓存的读取次数多于更新次数（否则缓存就是浪费时间），因此这是一个优化的候选对象。
我们如何摆脱读锁？摆脱读锁意味着写入者可能会在读者读取时更改列表。这其实很简单：如果写入者非常小心地添加元素，我们可以在元素被添加的同时读取链表。例如，向名为`list`的单链表中添加一个新元素`new`：

            new->next = list->next;
            wmb();
            list->next = new;

这里的`wmb()`是一个写内存屏障。它确保第一个操作（设置新元素的`next`指针）已经完成，并且所有CPU都能看到这个操作，然后才执行第二个操作（将新元素放入列表）。这是很重要的，因为现代编译器和现代CPU都会重新排序指令，除非另有指示：我们希望读者要么完全看不到新元素，要么看到新元素并正确指向列表其余部分的`next`指针。

幸运的是，有一个函数可以处理标准的`struct list_head`列表：
`list_add_rcu()` (`include/linux/list.h`)。

从列表中移除一个元素更简单：我们将旧元素的指针替换为其后继元素的指针，读者要么会看到它，要么会跳过它：

            list->next = old->next;

有一个`list_del_rcu()` (`include/linux/list.h`)函数可以做到这一点（普通版本会毒化旧对象，这不是我们想要的）。

读者也必须小心：一些CPU会在`next`指针改变之前通过`next`指针开始读取下一个元素的内容，但当`next`指针变化时，它们没有意识到预取的内容是错误的。再次强调，有一个`list_for_each_entry_rcu()` (`include/linux/list.h`)函数可以帮助你。当然，写入者可以使用`list_for_each_entry()`，因为不可能有两个同时写入者。

我们最后的困境是：何时可以实际销毁已移除的元素？记住，可能有一个读者正在遍历这个元素：如果我们释放这个元素并且`next`指针变化了，读者将会跳到垃圾数据并崩溃。我们需要等到我们知道所有在删除元素时遍历列表的读者都完成了。我们使用`call_rcu()`来注册一个回调函数，一旦所有现有的读者完成，就会实际销毁对象。

或者，可以使用`synchronize_rcu()`来阻塞直到所有现有读者完成。

那么，RCU是如何知道读者何时完成的呢？方法如下：首先，读者总是在`rcu_read_lock()`和`rcu_read_unlock()`对之间遍历列表：这些函数只是禁用抢占，因此读者在读取列表时不会进入睡眠状态。
RCU然后等待其他每个CPU至少睡眠一次：由于读者不能睡眠，我们知道在删除期间遍历列表的任何读者都已经完成，回调函数会被触发。
真实的Read-Copy-Update（RCU）代码比这更加优化，但这是其基本思想。

    --- cache.c.perobjectlock   2003-12-11 17:15:03.000000000 +1100
    +++ cache.c.rcupdate    2003-12-11 17:55:14.000000000 +1100
    @@ -1,15 +1,18 @@
    #include <linux/list.h>
    #include <linux/slab.h>
    #include <linux/string.h>
    +#include <linux/rcupdate.h>
    #include <linux/mutex.h>
    #include <asm/errno.h>

    struct object
    {
    -        /* 这两个成员受cache_lock保护。 */
    +        /* 这个成员受RCU保护 */
             struct list_head list;
             int popularity;

    +        struct rcu_head rcu;
    +
             atomic_t refcnt;

             /* 创建后不再改变。 */
    @@ -40,7 +43,7 @@
     {
             struct object *i;

    -        list_for_each_entry(i, &cache, list) {
    +        list_for_each_entry_rcu(i, &cache, list) {
                     if (i->id == id) {
                             i->popularity++;
                             return i;
    @@ -49,19 +52,25 @@
             return NULL;
     }

    +/* 最终的删除操作在确定没有读者访问时完成。 */
    +static void cache_delete_rcu(void *arg)
    +{
    +        object_put(arg);
    +}
    +
     /* 必须持有cache_lock */
     static void __cache_delete(struct object *obj)
     {
             BUG_ON(!obj);
    -        list_del(&obj->list);
    -        object_put(obj);
    +        list_del_rcu(&obj->list);
             cache_num--;
    +        call_rcu(&obj->rcu, cache_delete_rcu);
     }

     /* 必须持有cache_lock */
     static void __cache_add(struct object *obj)
     {
    -        list_add(&obj->list, &cache);
    +        list_add_rcu(&obj->list, &cache);
             if (++cache_num > MAX_CACHE_SIZE) {
                     struct object *i, *outcast = NULL;
                     list_for_each_entry(i, &cache, list) {
    @@ -104,12 +114,11 @@
     struct object *cache_find(int id)
     {
             struct object *obj;
    -        unsigned long flags;

    -        spin_lock_irqsave(&cache_lock, flags);
    +        rcu_read_lock();
             obj = __cache_find(id);
             if (obj)
                     object_get(obj);
    -        spin_unlock_irqrestore(&cache_lock, flags);
    +        rcu_read_unlock();
             return obj;
     }

注意，读取者会在`__cache_find()`中修改`popularity`成员，并且现在它不持有锁。一种解决方案是将其设为`atomic_t`类型，但对于这种用途，我们并不关心竞争条件：近似的结果就足够了，所以我没有改变它。
结果是`cache_find()`不需要与其他任何函数同步，因此在SMP系统上几乎和UP系统上一样快。
这里还有一个可能的优化：记住我们最初的缓存代码，在其中没有引用计数，调用者在使用对象时只需持有锁即可。这仍然是可行的：如果你持有锁，没有人可以删除该对象，所以你不需要获取和释放引用计数。
现在，因为RCU中的“读锁”只是禁用了抢占，一个始终在调用`cache_find()`和`object_put()`之间禁用抢占的调用者不需要实际获取和释放引用计数：我们可以将`__cache_find()`公开为非静态函数，这样的调用者可以直接调用它。
这样做的好处是不会写入引用计数：对象不会以任何方式被修改，这对于SMP机器来说由于缓存的原因会更快。

### 每CPU数据

另一种广泛使用的避免加锁的技术是为每个CPU复制信息。例如，如果你想统计一个常见的条件，你可以使用自旋锁和一个单一的计数器。简单明了。
如果这种方法太慢（通常不会，但如果你有一个很大的测试机器并且能够证明这一点），你可以为每个CPU使用一个计数器，那么它们都不需要独占锁。参见`DEFINE_PER_CPU()`、`get_cpu_var()`和`put_cpu_var()`（`include/linux/percpu.h`）。
对于简单的每CPU计数器，特别有用的是`local_t`类型以及`cpu_local_inc()`和其他相关函数，在某些架构上这些函数比简单的代码更高效（`include/asm/local.h`）。
请注意，没有简单可靠的方法在不引入更多锁的情况下获得此类计数器的确切值。对于某些用途这不是问题。
数据主要由 IRQ 处理程序使用
----------------------------------------

如果数据始终在同一个 IRQ 处理程序中被访问，那么你根本不需要加锁：内核已经保证 IRQ 处理程序不会在多个 CPU 上同时运行。Manfred Spraul 指出，即使数据偶尔在用户上下文或软中断/任务中被访问，你仍然可以这样做。IRQ 处理程序不使用锁，并且所有其他访问都按照以下方式进行：

```c
mutex_lock(&lock);
disable_irq(irq);
..
enable_irq(irq);
mutex_unlock(&lock);
```

`disable_irq()` 防止 IRQ 处理程序运行（如果它当前在其他 CPU 上运行，则等待其完成）。自旋锁防止在同一时间发生任何其他访问。显然，这比单纯的 `spin_lock_irq()` 调用要慢，因此只有在这种类型的访问极其罕见时才有意义。

哪些函数可以在中断中安全调用？
================================

内核中的许多函数直接或间接地睡眠（即调用 `schedule()`）：你永远不能在持有自旋锁或抢占禁用的情况下调用它们。这也意味着你需要处于用户上下文中：从中断中调用它们是非法的。

一些会睡眠的函数
--------------------------

下面列出了一些常见的函数，但通常你需要阅读代码以确定其他调用是否安全。如果所有其他调用者都可以睡眠，那么你也可能需要能够睡眠。特别是，注册和注销函数通常期望从用户上下文调用，并且可以睡眠。
- 访问用户空间：
  - `copy_from_user()`
  - `copy_to_user()`
  - `get_user()`
  - `put_user()`
- `kmalloc(GP_KERNEL)`
- `mutex_lock_interruptible()` 和 `mutex_lock()`
  - 有一个 `mutex_trylock()` 不会睡眠，但它不能在中断上下文中使用，因为其实现对该上下文不安全。`mutex_unlock()` 也永远不会睡眠，但由于互斥锁必须由获取它的同一任务释放，因此也不能在中断上下文中使用。

一些不会睡眠的函数
--------------------------

有些函数可以从任何上下文安全调用，或持有几乎任何锁。
### 互斥锁 API 参考
===================

.. kernel-doc:: include/linux/mutex.h
   :internal:

.. kernel-doc:: kernel/locking/mutex.c
   :export:

### Futex API 参考
===================

.. kernel-doc:: kernel/futex/core.c
   :internal:

.. kernel-doc:: kernel/futex/futex.h
   :internal:

.. kernel-doc:: kernel/futex/pi.c
   :internal:

.. kernel-doc:: kernel/futex/requeue.c
   :internal:

.. kernel-doc:: kernel/futex/waitwake.c
   :internal:

### 进一步阅读
===============

-  ``Documentation/locking/spinlocks.rst``：Linus Torvalds 在内核源码中的自旋锁教程
-  Unix Systems for Modern Architectures: Symmetric Multiprocessing and Caching for Kernel Programmers:

   Curt Schimmel 的非常好的内核级锁定介绍（虽然不是为 Linux 编写的，但几乎所有的内容都适用）。这本书虽然价格昂贵，但对于理解 SMP 锁定来说非常值得 [ISBN: 0201633388]

### 感谢
======

感谢 Telsa Gwynne 对文档的整理、美化和添加样式。
感谢 Martin Pool, Philipp Rumpf, Stephen Rothwell, Paul Mackerras, Ruedi Aschwanden, Alan Cox, Manfred Spraul, Tim Waugh, Pete Zaitcev, James Morris, Robert Love, Paul McKenney, John Ashby 提供审阅、校正、评论和反馈。
感谢“智囊团”对本文档没有施加任何影响。

### 术语表
========

抢占
  在 2.5 版本之前，或者当 `CONFIG_PREEMPT` 未设置时，在内核中运行的用户进程不会互相抢占（即你拥有该 CPU 直到你放弃它，除了中断）。从 2.5.4 版本增加了 `CONFIG_PREEMPT` 后，这种情况发生了变化：在用户上下文中，优先级更高的任务可以“插队”：自旋锁被修改以禁用抢占，即使是在单处理器上也是如此。
bh
  底层处理：由于历史原因，带有 '_bh' 的函数现在通常指任何软件中断，例如 `spin_lock_bh()` 会阻止当前 CPU 上的任何软件中断。底层处理已经被弃用，并将最终被任务项取代。任何时候只有一个底层处理在运行。
硬件中断 / 硬件 IRQ
  硬件中断请求。`in_hardirq()` 在硬件中断处理程序中返回 true。
中断上下文
  不是用户上下文：正在处理硬件 IRQ 或软件 IRQ。由 `in_interrupt()` 宏返回 true 表示。
SMP
  对称多处理器：编译用于多 CPU 机器的内核。
``CONFIG_SMP=y``
软件中断 / softirq
  软件中断处理程序。`in_hardirq()` 返回 `false`；`in_softirq()` 返回 `true`。Tasklets 和 softirq 都属于“软件中断”的范畴。
严格来说，softirq 是最多 32 个枚举的软件中断之一，可以在多个 CPU 上同时运行。有时也用来指代 tasklets（即所有的软件中断）。
tasklet
  动态注册的软件中断，保证一次只在一个 CPU 上运行。
定时器
  动态注册的软件中断，在特定时间（或接近特定时间）运行。运行时与 tasklet 类似（实际上，它们是从 `TIMER_SOFTIRQ` 调用的）。
UP
  单处理器：非 SMP。（`CONFIG_SMP=n`）
用户上下文
  内核代表某个特定进程（例如系统调用或陷阱）或内核线程执行。可以通过 `current` 宏知道是哪个进程。不要与用户空间混淆。可以被软件或硬件中断打断。
用户空间
  在内核之外执行自己代码的进程。
