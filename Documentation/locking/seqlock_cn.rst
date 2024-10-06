======================================
序列计数器和顺序锁
======================================

介绍
============

序列计数器是一种读写一致性机制，具有无锁读者（只读重试循环），并且没有写入者饥饿。它们用于很少被写入的数据（例如系统时间），其中读者希望获取一组一致的信息，并且愿意在信息发生变化时重试。
当读取侧临界区开始时的序列计数为偶数，并且在临界区结束时再次读取相同的序列计数值时，数据集是一致的。集合中的数据必须在读取侧临界区内复制出来。如果序列计数在临界区开始和结束之间发生了变化，则读者必须重试。
写入者在其临界区开始和结束时递增序列计数。在开始临界区后，序列计数为奇数，这表明读者正在进行更新。在写入侧临界区结束时，序列计数再次变为偶数，从而允许读者继续前进。
序列计数器写入侧临界区决不能被读取侧临界区抢占或中断。否则，由于奇数序列计数值和被中断的写入者，读者将在整个调度周期内自旋。如果该读者属于实时调度类，则可能会永远自旋，导致内核死锁。
如果受保护的数据包含指针，则不能使用此机制，因为写入者可能会使读者正在跟踪的指针失效。

.. _seqcount_t:

序列计数器（``seqcount_t``）
==================================

这是原始的计数机制，不保护多个写入者。因此，写入侧临界区必须通过外部锁进行串行化。
如果写入串行化原语没有隐式禁用抢占，则必须在进入写入侧部分之前显式禁用抢占。如果读取部分可以在硬中断或软中断上下文中调用，则还必须分别在进入写入部分之前禁用中断或下半部。
如果希望自动处理写入者串行化和非抢占性所需的序列计数器要求，请改用 :ref:`seqlock_t`。
初始化示例：

```c
    /* 动态初始化 */
    seqcount_t foo_seqcount;
    seqcount_init(&foo_seqcount);

    /* 静态初始化 */
    static seqcount_t foo_seqcount = SEQCNT_ZERO(foo_seqcount);

    /* C99 结构体初始化 */
    struct {
        .seq = SEQCNT_ZERO(foo.seq),
    } foo;
```

写入路径示例：

```c
    /* 禁用抢占的串行上下文 */

    write_seqcount_begin(&foo_seqcount);

    /* ... [[写入侧临界区]] ... */

    write_seqcount_end(&foo_seqcount);
```

读取路径示例：

```c
    do {
        seq = read_seqcount_begin(&foo_seqcount);

        /* ... [[读取侧临界区]] ... */

    } while (read_seqcount_retry(&foo_seqcount, seq));
```

.. _seqcount_locktype_t:

带关联锁的序列计数器（``seqcount_LOCKNAME_t``）
-------------------------------------------------

如 :ref:`seqcount_t` 中所述，序列计数器写入侧临界区必须是串行化的且不可抢占的。这种序列计数器变体在初始化时关联了用于写入者串行化的锁，从而使锁依赖验证写入侧临界区是否正确串行化。
如果禁用了锁依赖，此锁关联将是一个空操作，既没有存储也没有运行时开销。如果启用了锁依赖，则锁指针将存储在 `struct seqcount` 中，并且锁依赖的“持有锁”断言将在写入侧临界区开始时注入，以验证其是否得到适当保护。
对于那些不会隐式禁用抢占的锁类型，在写入侧函数中强制执行抢占保护。
以下定义了与关联锁一起使用的序列计数器：

- ``seqcount_spinlock_t``
- ``seqcount_raw_spinlock_t``
- ``seqcount_rwlock_t``
- ``seqcount_mutex_t``
- ``seqcount_ww_mutex_t``

序列计数器的读取和写入 API 可以使用普通的 `seqcount_t` 或上述任何 `seqcount_LOCKNAME_t` 的变体。
初始化（将 "LOCKNAME" 替换为支持的锁之一）：

```c
/* 动态初始化 */
seqcount_LOCKNAME_t foo_seqcount;
seqcount_LOCKNAME_init(&foo_seqcount, &lock);

/* 静态初始化 */
static seqcount_LOCKNAME_t foo_seqcount =
    SEQCNT_LOCKNAME_ZERO(foo_seqcount, &lock);

/* C99 结构体初始化 */
struct {
    .seq = SEQCNT_LOCKNAME_ZERO(foo.seq, &lock),
} foo;
```

写入路径：与 `seqcount_t` 相同，但在获取关联的写入序列化锁的情况下运行。
读取路径：与 `seqcount_t` 相同。

### 带有闩锁的序列计数器 (`seqcount_latch_t`)
带有闩锁的序列计数器是一种多版本并发控制机制，其中嵌入的 `seqcount_t` 计数器的奇偶值用于在两个受保护的数据副本之间切换。这允许序列计数器的读取路径安全地中断其自身的写入侧临界区。
当写入侧部分不能受到读者中断的保护时，使用 `seqcount_latch_t`。这通常发生在读取侧可以从 NMI 处理程序调用的情况下。
更多信息请参阅 `raw_write_seqcount_latch()`。

### 序列锁 (`seqlock_t`)
这包含了前面讨论的 `seqcount_t` 机制，并且嵌入了一个用于写入序列化和非抢占性的自旋锁。
如果读取侧部分可以从硬中断或软中断上下文调用，则使用禁用中断或底半部的写入侧函数变体。
初始化：
```c
/* 动态初始化 */
seqlock_t foo_seqlock;
seqlock_init(&foo_seqlock);

/* 静态初始化 */
static DEFINE_SEQLOCK(foo_seqlock);

/* C99 结构体初始化 */
struct {
    .seql = __SEQLOCK_UNLOCKED(foo.seql)
} foo;
```

写入路径：
```c
write_seqlock(&foo_seqlock);

/* ... [写入侧临界区] ... */

write_sequnlock(&foo_seqlock);
```

读取路径，分为三类：

1. 普通序列读取者从不阻塞写入者，但如果写入者正在进行，则必须通过检测序列号的变化来重试。写入者不等待序列读取者：
   ```c
   do {
       seq = read_seqbegin(&foo_seqlock);

       /* ... [读取侧临界区] ... */

   } while (read_seqretry(&foo_seqlock, seq));
   ```

2. 锁定读取者将在写入者或其他锁定读取者正在进行时等待。一个正在进行的锁定读取者也会阻止写入者进入其临界区。这个读取锁是排他的。与 `rwlock_t` 不同，只有一个锁定读取者可以获取它：
   ```c
   read_seqlock_excl(&foo_seqlock);

   /* ... [读取侧临界区] ... */

   read_sequnlock_excl(&foo_seqlock);
   ```

3. 根据传递的标记进行条件无锁读取（如第 1 类）或锁定读取（如第 2 类）。这用于避免在写入活动激增时无锁读取者的饥饿问题（过多的重试循环）。首先尝试无锁读取（传递偶数标记）。如果该尝试失败（返回奇数序列计数器，用作下一次迭代的标记），则无锁读取转换为完整的锁定读取，无需重试循环：
   ```c
   /* 标记；偶数初始化 */
   int seq = 0;
   do {
       read_seqbegin_or_lock(&foo_seqlock, &seq);

       /* ... [读取侧临界区] ... */

   } while (need_seqretry(&foo_seqlock, seq));
   done_seqretry(&foo_seqlock, seq);
   ```

API 文档
========

.. kernel-doc:: include/linux/seqlock.h
