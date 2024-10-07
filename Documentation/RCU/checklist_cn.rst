SPDX 许可证标识符: GPL-2.0

================================
RCU 补丁审查检查表
================================

本文档包含了一个用于生成和审查使用 RCU 的补丁的检查列表。违反下面列出的任何规则都会导致类似于遗漏锁定原语的问题。此列表基于长时间审查此类补丁的经验，但总是欢迎改进！

0. RCU 是否应用于读取为主的场景？如果数据结构的更新频率超过约 10%，则应强烈考虑其他方法，除非详细的性能测量显示 RCU 仍然是最佳工具。是的，RCU 通过增加写入侧开销来减少读取侧开销，这就是为什么正常的 RCU 使用会进行更多的读取而不是更新。
另一个例外情况是当性能不是问题时，而 RCU 提供了更简单的实现。例如，在 Linux 2.6 内核中（至少在 NMI 很少发生的架构上）动态 NMI 代码就是这种情况。
另一个例外是当 RCU 的读取侧原语具有关键的低实时延迟时。
最后一个例外是当 RCU 读取者用于防止无锁更新中的 ABA 问题（https://en.wikipedia.org/wiki/ABA_problem）。这确实会导致稍微反直觉的情况，即使用 rcu_read_lock() 和 rcu_read_unlock() 来保护更新，然而这种方法可以为某些类型的无锁算法提供与垃圾收集器相同的简化。

1. 更新代码是否具有适当的互斥性？

RCU 允许 *读取者* 几乎不加保护地运行，但 *写入者* 必须使用某种形式的互斥机制，如：

a. 锁定，
b. 原子操作，或
c. 将更新限制在一个任务中

如果你选择 b，请准备好解释你是如何处理弱序机器上的内存屏障（几乎所有的机器都如此——即使是 x86 也允许较晚的加载重新排序以先于较早的存储），并解释为什么这种额外的复杂性值得。如果你选择 c，请准备好解释为什么这个单一任务不会成为大型系统上的主要瓶颈（例如，如果该任务正在更新与其自身相关的信息，而其他任务可以读取这些信息，则理论上就不会有瓶颈）。请注意，“大型”系统的定义已经发生了显著变化：2000 年时八核 CPU 即为“大型”，而在 2017 年一百核 CPU 已经司空见惯。

2. RCU 读取侧临界区是否正确使用了 rcu_read_lock() 及其相关函数？这些原语是必需的，以防止恩典期提前结束，这可能导致数据在你的读取侧代码下被无礼地释放，从而大大增加内核的风险。

作为粗略的规则，任何对 RCU 保护指针的解引用必须由 rcu_read_lock()、rcu_read_lock_bh() 或 rcu_read_lock_sched() 覆盖，或者由相应的更新侧锁覆盖。
显式禁用抢占（例如使用 preempt_disable()）可以作为 rcu_read_lock_sched() 的替代方案，但这不太易读，并且阻止了 lockdep 检测锁定问题。获取自旋锁也会进入 RCU 读取侧临界区。

请注意，你 *不能* 依赖已知仅在不可抢占内核中构建的代码。这样的代码可能会并且将会出错，特别是在使用 CONFIG_PREEMPT_COUNT=y 构建的内核中。
让RCU保护的指针“泄露”出RCU读端临界区，就跟让它们从锁下泄露一样糟糕。当然，除非你在让它们离开RCU读端临界区之前已经安排了其他形式的保护，比如锁或引用计数。

3. 更新代码是否能容忍并发访问？

RCU的核心目的就是允许读者在没有任何锁或原子操作的情况下运行。这意味着读者将在更新正在进行时运行。根据具体情况，有多种方法来处理这种并发性：

a. 使用RCU变体的链表和哈希链表更新原语来添加、移除和替换RCU保护链表上的元素。或者，使用已添加到Linux内核中的其他RCU保护的数据结构。
这几乎是最好的方法。

b. 按照上述(a)进行，但同时也为每个元素维护锁（这些锁由读者和写者共同获取），以保护每个元素的状态。如果需要，可以使用其他仅由更新者获取的锁来保护读者不访问的字段。
这也工作得很好。

c. 让更新对读者来说显得是原子的。例如，对适当对齐的字段的指针更新将显得是原子的，同样单个原子原语也是如此。
在锁下执行的操作序列对于RCU读者来说不会显得是原子的，多个原子原语的序列也不会。一种替代方案是将多个单独字段移到一个单独的结构中，从而通过增加一层间接层次来解决多字段问题。
这可以工作，但开始变得有些复杂。

d. 小心地对更新和读取进行排序，以便读者在更新的所有阶段都能看到有效数据。这通常比听起来更难，特别是考虑到现代CPU倾向于重新排序内存引用。通常必须在代码中大量散布内存排序操作，使得代码难以理解和测试。在适用的地方，最好使用smp_store_release()和smp_load_acquire()等函数，但在某些情况下可能需要smp_mb()全内存屏障。
如前所述，通常最好是将更改的数据分组到一个单独的结构中，这样通过更新指向包含更新值的新结构的指针，使更改显得是原子的。
4. 弱序CPU带来了特殊的挑战。几乎所有的CPU都是弱序的——即使是x86 CPU也允许后续的加载操作重新排序到之前的存储操作之前。RCU代码必须采取以下所有措施来防止内存损坏问题：

   a. 读取者必须保持其内存访问的正确顺序。`rcu_dereference()`原语确保CPU在获取数据之前先获取指针。这对于Alpha CPU来说是必要的。
   
   `rcu_dereference()`原语也是一个很好的文档辅助工具，可以让阅读代码的人确切地知道哪些指针是由RCU保护的。
   
   请注意，编译器也会重新排序代码，并且它们在这方面变得越来越激进。因此，`rcu_dereference()`原语也能防止破坏性的编译器优化。然而，通过一些巧妙的创意，有可能错误处理`rcu_dereference()`的返回值。请参阅`rcu_dereference.rst`以获取更多信息。
   
   `rcu_dereference()`原语被各种“_rcu()”列表遍历原语使用，例如`list_for_each_entry_rcu()`。请注意，更新方代码使用`rcu_dereference()`和“_rcu()”列表遍历原语是完全合法的（尽管有些冗余）。这在读者和更新者共用的代码中特别有用。但是，如果在RCU读取临界区之外访问`rcu_dereference()`，lockdep会抱怨。请参阅`lockdep.rst`以了解如何处理这个问题。
   
   当然，`rcu_dereference()`原语和“_rcu()”列表遍历原语都不能替代良好的并发设计来协调多个更新者。

   b. 如果使用了列表宏，则必须使用`list_add_tail_rcu()`和`list_add_rcu()`原语来防止弱序机器错误地重新排序结构初始化和指针插入。
   
   同样，如果使用了hlist宏，则需要使用`hlist_add_head_rcu()`原语。
   
   c. 如果使用了列表宏，则必须使用`list_del_rcu()`原语来防止`list_del()`的指针毒化对并发读取者产生毒性影响。同样，如果使用了hlist宏，则需要使用`hlist_del_rcu()`原语。
   
   `list_replace_rcu()`和`hlist_replace_rcu()`原语可用于在各自的RCU保护列表类型中替换旧结构为新结构。
d. 类似于(4b)和(4c)的规则适用于RCU保护的链表类型"hlist_nulls"。

e. 更新必须确保给定结构的初始化发生在指向该结构的指针被公开之前。当公开一个可以被RCU读临界区遍历的结构的指针时，使用rcu_assign_pointer()原语。

5. 如果使用了call_rcu()、call_srcu()、call_rcu_tasks()、call_rcu_tasks_rude()或call_rcu_tasks_trace()中的任何一个函数，回调函数可能在软中断上下文中被调用，并且无论如何是在禁用了下半部的情况下调用的。特别是，这个回调函数不能阻塞。如果你需要回调函数阻塞，请将该代码放在从回调中调度的工作队列处理程序中运行。queue_rcu_work()函数在call_rcu()的情况下为你做了这件事。

6. 由于synchronize_rcu()可能会阻塞，因此不能从任何类型的中断上下文调用它。同样的规则也适用于synchronize_srcu()、synchronize_rcu_expedited()、synchronize_srcu_expedited()、synchronize_rcu_tasks()、synchronize_rcu_tasks_rude()和synchronize_rcu_tasks_trace()。

这些带加速形式的原语与非加速形式具有相同的语义，但加速形式对CPU更为密集。加速原语的使用应限于罕见的配置更改操作，通常不会在实时工作负载运行时进行。请注意，对IPI敏感的实时工作负载可以使用rcupdate.rcu_normal内核启动参数完全禁用加速宽限期，尽管这可能会有性能影响。

特别是，如果你发现自己在一个循环中反复调用其中一个加速原语，请为大家做个人情：重构你的代码，使其批量更新，允许单个非加速原语覆盖整个批处理。这很可能比包含加速原语的循环更快，并且对系统其他部分（尤其是实时工作负载）要容易得多。或者，改用异步原语，如call_rcu()。

7. 截至v4.20版本，给定的内核仅实现一种RCU变体，即对于PREEMPTION=n时为RCU-sched，对于PREEMPTION=y时为RCU-preempt。

如果更新者使用call_rcu()或synchronize_rcu()，那么相应的读取者可以使用：(1) rcu_read_lock()和rcu_read_unlock()；(2) 任何一对禁用和重新启用软中断的原语，例如rcu_read_lock_bh()和rcu_read_unlock_bh()；(3) 任何一对禁用和重新启用抢占的原语，例如rcu_read_lock_sched()和rcu_read_unlock_sched()。如果更新者使用synchronize_srcu()或call_srcu()，则相应的读取者必须使用srcu_read_lock()和srcu_read_unlock()，并且使用相同的srcu_struct。加速RCU宽限期等待原语的规则与其非加速对应物相同。
同样地，正确使用RCU Tasks的各种变体也是必要的：

a. 如果更新者使用了`synchronize_rcu_tasks()`或`call_rcu_tasks()`，那么读者必须避免执行自愿的上下文切换，也就是说，不能阻塞。
b. 如果更新者使用了`call_rcu_tasks_trace()`或`synchronize_rcu_tasks_trace()`，那么相应的读者必须使用`rcu_read_lock_trace()`和`rcu_read_unlock_trace()`。
c. 如果更新者使用了`call_rcu_tasks_rude()`或`synchronize_rcu_tasks_rude()`，那么相应的读者必须使用任何能够禁用抢占的手段，例如`preempt_disable()`和`preempt_enable()`。

混合使用这些方法会导致混乱并使内核出错，甚至导致可利用的安全问题。因此，在使用非显而易见的原语对时，添加注释是必不可少的。一个非显而易见配对的例子是网络中的XDP特性，它从网络驱动程序的NAPI（软中断）上下文中调用BPF程序。BPF对其数据结构的保护严重依赖于RCU，但由于BPF程序的调用完全在一个NAPI轮询周期内的`local_bh_disable()`部分中进行，这种使用方式是安全的。这种使用方式之所以安全的原因在于，当更新者使用`call_rcu()`或`synchronize_rcu()`时，读者可以使用任何禁用BH的方法。

8. 尽管`synchronize_rcu()`比`call_rcu()`慢，但它通常会生成更简单的代码。因此，除非更新性能至关重要、更新者不能阻塞，或者`synchronize_rcu()`的延迟在用户空间中可见，否则应优先使用`synchronize_rcu()`而不是`call_rcu()`。
此外，`kfree_rcu()`和`kvfree_rcu()`通常比`synchronize_rcu()`生成更简单的代码，并且没有`synchronize_rcu()`的多毫秒级延迟。因此，请在适用的情况下充分利用`kfree_rcu()`和`kvfree_rcu()`的“即发即忘”内存释放能力。

`synchronize_rcu()`原语的一个特别重要的属性是它会自动自我限制：如果由于某种原因延迟了宽限期，那么`synchronize_rcu()`原语也会相应地延迟更新。相比之下，使用`call_rcu()`的代码应在宽限期延迟的情况下明确限制更新速率，因为不这样做可能导致过高的实时延迟甚至OOM状况。

在使用`call_rcu()`、`kfree_rcu()`或`kvfree_rcu()`时获得这种自我限制特性的方法包括：

a. 记录RCU保护的数据结构所使用的数据结构元素的数量，包括那些等待宽限期结束的元素。强制限制这个数量，在必要时暂停更新以允许之前推迟的释放完成。或者，仅限制等待推迟释放的数量，而不是元素的总数。
一种暂停更新的方法是获取更新侧的互斥锁。（不要尝试使用自旋锁——其他CPU自旋等待该锁可能会阻止宽限期结束。）另一种暂停更新的方法是在内存分配器周围使用一个包装函数，使得当有太多内存等待RCU宽限期时，该包装函数模拟OOM。当然还有许多其他的变化形式。

b. 限制更新速率。例如，如果更新每小时只发生一次，则不需要显式的速率限制，除非你的系统已经严重损坏。
旧版本的 dcache 子系统采用这种方法，通过全局锁保护更新，限制其速率。

- 可信更新 -- 如果更新只能由超级用户或其他受信任的用户手动完成，则可能不需要自动限制它们。这里的理论是超级用户已经有多种方法使机器崩溃。
- 定期调用 `rcu_barrier()`，允许每个宽限期进行有限数量的更新。

对于 `call_srcu()`、`call_rcu_tasks()`、`call_rcu_tasks_rude()` 和 `call_rcu_tasks_trace()` 的调用也适用同样的警告。这就是为什么分别存在 `srcu_barrier()`、`rcu_barrier_tasks()`、`rcu_barrier_tasks_rude()` 和 `rcu_barrier_tasks_rude()` 的原因。

请注意，尽管这些原语确实采取措施避免在任何给定 CPU 上回调过多而导致内存耗尽的情况，但一个有决心的用户或管理员仍然可以耗尽内存。

这尤其适用于具有大量 CPU 的系统，如果该系统被配置为将所有 RCU 回调卸载到单个 CPU 上，或者系统相对缺乏空闲内存的情况。

9. 所有的 RCU 列表遍历原语，包括 `rcu_dereference()`、`list_for_each_entry_rcu()` 和 `list_for_each_safe_rcu()`，必须位于 RCU 读取侧临界区内部或受到适当的更新侧锁保护。RCU 读取侧临界区由 `rcu_read_lock()` 和 `rcu_read_unlock()` 或类似原语如 `rcu_read_lock_bh()` 和 `rcu_read_unlock_bh()` 标记，在这种情况下，必须使用相应的 `rcu_dereference()` 原语（例如 `rcu_dereference_bh()`）以保持锁依赖（lockdep）的正确性。

允许在持有更新侧锁的情况下使用 RCU 列表遍历原语的原因是这样做有助于减少代码膨胀，尤其是在读者和更新者之间共享常见代码时。为此情况提供了额外的原语，具体讨论见 `lockdep.rst`。

此规则的一个例外是当数据仅添加到链接的数据结构中，并且在读者访问该结构的任何时候都不会被移除。在这种情况下，可以使用 `READ_ONCE()` 替代 `rcu_dereference()` 并省略读取侧标记（如 `rcu_read_lock()` 和 `rcu_read_unlock()`）。

10. 相反地，如果你处于 RCU 读取侧临界区，并且没有持有适当的更新侧锁，则 *必须* 使用列表宏的 `_rcu()` 变体。不这样做会破坏 Alpha 系统，导致激进编译器生成错误代码，并使试图理解你代码的人感到困惑。
11. 任何由RCU回调获取的锁必须在其他地方以禁用软中断的方式获取，例如通过spin_lock_bh()。如果在给定的锁获取过程中未能禁用软中断，那么一旦RCU软中断处理程序恰好在中断该获取的关键部分时运行你的RCU回调，将会导致死锁。

12. RCU回调可以并行执行。在许多情况下，回调代码只是简单地包装了kfree()，因此这不是一个问题（或者更准确地说，如果是问题的话，内存分配器的锁定机制会处理它）。然而，如果回调对共享数据结构进行了操作，它们必须使用所需的任何锁或其他同步机制来安全地访问和/或修改该数据结构。

不要假设RCU回调将在执行相应call_rcu()、call_srcu()、call_rcu_tasks()、call_rcu_tasks_rude()或call_rcu_tasks_trace()的同一CPU上执行。例如，如果某个CPU在有RCU回调待执行的情况下下线，则该RCU回调将在某个存活的CPU上执行。（如果情况不是这样，自生成的RCU回调将阻止受害CPU下线。）此外，由rcu_nocbs=指定的CPU可能始终在其RCU回调在其他CPU上执行，实际上，在某些实时工作负载中，这是使用rcu_nocbs=内核启动参数的全部目的。

此外，不要假设按顺序排队的回调会按该顺序被调用，即使它们都在同一个CPU上排队。另外，不要假设同一CPU上的回调会被串行调用。例如，在最近的内核版本中，CPU可以在卸载和非卸载回调调用之间切换，并且当一个CPU正在进行这种切换时，其回调可能会由该CPU的软中断处理程序和该CPU的rcuo kthread并发调用。在这种情况下，该CPU的回调可能会同时并发执行并且顺序错乱。

13. 与大多数RCU变种不同，允许在SRCU读端临界区（由srcu_read_lock()和srcu_read_unlock()标记）中阻塞，这就是“SRCU”：可睡眠的RCU。

请注意，如果你不需要在读端临界区中睡眠，你应该使用RCU而不是SRCU，因为RCU几乎总是比SRCU更快且更容易使用。

与其他形式的RCU不同，需要在构建时通过DEFINE_SRCU()或DEFINE_STATIC_SRCU()或在运行时通过init_srcu_struct()和cleanup_srcu_struct()进行显式初始化和清理。后两者需要传递一个定义了特定SRCU域范围的"struct srcu_struct"。一旦初始化，srcu_struct将传递给srcu_read_lock()、srcu_read_unlock()、synchronize_srcu()、synchronize_srcu_expedited()和call_srcu()。一个给定的synchronize_srcu()仅等待通过相同srcu_struct传递的srcu_read_lock()和srcu_read_unlock()调用所管理的SRCU读端临界区。这一特性使得在读端临界区中睡眠变得可接受——一个给定子系统只会延迟自身的更新，而不会延迟使用SRCU的其他子系统的更新。因此，SRCU比RCU更不容易导致系统出现内存不足的情况，如果RCU的读端临界区允许睡眠的话。

在读端临界区中睡眠的能力并不是免费的。首先，相应的srcu_read_lock()和srcu_read_unlock()调用必须传递相同的srcu_struct。其次，恩惠期检测开销仅在共享给定srcu_struct的更新之间分摊，而不是像其他形式的RCU那样全局分摊。

因此，只有在极其读密集的情况下，或者需要SRCU的读端死锁免疫性或低读端实时延迟的情况下，才应优先使用SRCU而非rw_semaphore。当你需要轻量级读者时，还应考虑percpu_rw_semaphore。
SRCU的快速原语（synchronize_srcu_expedited()）从不向其他CPU发送IPI，因此在实时工作负载方面比synchronize_rcu_expedited()更友好。

在RCU Tasks Trace读端临界区中允许睡眠，这些临界区由rcu_read_lock_trace()和rcu_read_unlock_trace()界定。然而，这是一种专门化的RCU形式，在使用之前应先与当前用户确认。在大多数情况下，你应该改用SRCU。

注意，rcu_assign_pointer()对于SRCU和其他形式的RCU是一样的，但是你应该使用srcu_dereference()而不是rcu_dereference()，以避免lockdep问题。

14. call_rcu()、synchronize_rcu()及其相关函数的目的在于等待所有现有读者完成操作之后再执行某些具有破坏性的操作。因此，至关重要的是首先移除任何可能受破坏性操作影响的读者路径，然后再调用call_rcu()、synchronize_rcu()或其相关函数。

由于这些原语只等待现有读者，因此调用者有责任保证任何后续读者能够安全执行。

15. 各种RCU读端原语不一定包含内存屏障。因此，你应该计划好CPU和编译器可以自由地将代码重排进出RCU读端临界区。处理这种情况是RCU更新端原语的责任。

对于SRCU读者，你可以在srcu_read_unlock()之后立即使用smp_mb__after_srcu_read_unlock()来获得一个完整的内存屏障。

16. 使用CONFIG_PROVE_LOCKING、CONFIG_DEBUG_OBJECTS_RCU_HEAD以及__rcu sparse检查来验证你的RCU代码。这些可以帮助发现以下问题：

- CONFIG_PROVE_LOCKING：
  检查对RCU保护的数据结构的访问是否在适当的RCU读端临界区内进行，并且持有正确的锁组合，或者满足其他适当条件。

- CONFIG_DEBUG_OBJECTS_RCU_HEAD：
  检查是否在上次将相同对象传递给call_rcu()（或其相关函数）之后的一个RCU宽限期结束之前再次将该对象传递给call_rcu()（或其相关函数）。

- CONFIG_RCU_STRICT_GRACE_PERIOD：
  结合KASAN检查指针是否泄露出RCU读端临界区。此Kconfig选项对性能和可扩展性要求很高，因此仅限于四CPU系统。
__rcu 稀疏检查：
    使用 __rcu 标记指向 RCU 保护的数据结构的指针，如果在没有使用 rcu_dereference() 变体之一的情况下访问该指针，稀疏检查会警告你。
这些调试辅助工具可以帮助你找到其他方式难以发现的问题。

17. 如果你在模块中定义了一个回调函数，并将其传递给 call_rcu()、call_srcu()、call_rcu_tasks()、call_rcu_tasks_rude() 或 call_rcu_tasks_trace()，那么在卸载该模块之前需要等待所有待处理的回调被调用。

请注意，仅仅等待一个优雅周期是绝对不够的！例如，synchronize_rcu() 的实现不保证等待通过 call_rcu() 在其他 CPU 上注册的回调。即使是在当前 CPU 上也是如此，如果该 CPU 最近下线后又重新上线。

相反，你需要使用以下屏障函数之一：

    - call_rcu() -> rcu_barrier()
    - call_srcu() -> srcu_barrier()
    - call_rcu_tasks() -> rcu_barrier_tasks()
    - call_rcu_tasks_rude() -> rcu_barrier_tasks_rude()
    - call_rcu_tasks_trace() -> rcu_barrier_tasks_trace()

然而，这些屏障函数绝对不能保证等待一个优雅周期。例如，如果系统中没有任何 call_rcu() 回调排队，rcu_barrier() 会立即返回。

因此，如果你需要等待一个优雅周期以及所有现有的回调，你需要调用两个函数，具体取决于 RCU 的类型：

    - 要么使用 synchronize_rcu() 或 synchronize_rcu_expedited()，加上 rcu_barrier()
    - 要么使用 synchronize_srcu() 或 synchronize_srcu_expedited()，加上 srcu_barrier()
    - 使用 synchronize_rcu_tasks() 和 rcu_barrier_tasks()
    - 使用 synchronize_tasks_rude() 和 rcu_barrier_tasks_rude()
    - 使用 synchronize_tasks_trace() 和 rcu_barrier_tasks_trace()

如有必要，你可以使用类似工作队列的方法来并发执行所需的函数对。

更多信息请参见 rcubarrier.rst。
