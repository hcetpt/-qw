.. _rcu_doc:

RCU 概念
============

RCU（Read-Copy-Update，读-复制-更新）背后的基本思想是将破坏性操作分成两个部分：一个部分防止任何人看到正在被销毁的数据项，另一个部分实际执行销毁。在这两部分之间必须有一个“宽限期”，这个宽限期必须足够长，以确保任何访问被删除项的读者已经释放了他们的引用。例如，在链表中进行RCU保护的删除操作时，首先会将该数据项从链表中移除，等待宽限期结束后再释放该元素。有关使用RCU与链表相关的更多信息，请参阅listRCU.rst。

常见问题解答
--------------------------

- 为什么有人会想使用RCU？

  RCU两阶段方法的优势在于RCU读取者无需获取任何锁、执行任何原子指令、写入共享内存或（在Alpha以外的CPU上）执行任何内存屏障。由于这些操作在现代CPU上非常耗时，因此RCU在读取密集型场景中具有性能优势。此外，RCU读取者无需获取锁还可以大大简化避免死锁的代码。

- 更新者如何知道宽限期何时完成，如果RCU读取者不给出任何完成的指示？

  就像自旋锁一样，RCU读取者不允许阻塞、切换到用户模式执行或进入空闲循环。因此，一旦观察到某个CPU通过这三个状态中的任何一个，我们就知道该CPU已经退出了之前的RCU读取侧临界区。因此，如果我们从链表中移除一个项，并等待所有CPU切换上下文、在用户模式下执行或在空闲循环中执行，那么我们就可以安全地释放该项。

  可抢占变种的RCU（CONFIG_PREEMPT_RCU）实现了相同的效果，但要求读取者操作CPU本地计数器。这些计数器允许在RCU读取侧临界区内进行有限类型的阻塞。SRCU也使用CPU本地计数器，并允许在RCU读取侧临界区内进行一般性的阻塞。这些RCU变种通过采样这些计数器来检测宽限期。

- 如果我在单处理器内核上运行，只能一次做一件事，为什么我还要等待宽限期？

  请参阅UP.rst获取更多信息。

- 如何查看Linux内核中当前RCU的使用情况？

  搜索 "rcu_read_lock"、"rcu_read_unlock"、"call_rcu"、"rcu_read_lock_bh"、"rcu_read_unlock_bh"、"srcu_read_lock"、"srcu_read_unlock"、"synchronize_rcu"、"synchronize_net"、"synchronize_srcu" 和其他RCU原语。或者从以下网址获取cscope数据库：

  (http://www.rdrop.com/users/paulmck/RCU/linuxusage/rculocktab.html)

- 编写使用RCU的代码时应该遵循哪些指导原则？

  请参阅checklist.rst。

- 名字“RCU”是什么意思？

  “RCU”代表“Read-Copy-Update”（读-复制-更新）。
`listRCU.rst` 中有更多的信息介绍这个名字的由来，搜索 "read-copy update" 即可找到相关信息。
- 我听说 RCU 被授予了专利？这是怎么回事？

  是的，确实如此。已知有多个与 RCU 相关的专利，可以在 `Documentation/RCU/RTFP.txt` 文件中搜索 "Patent" 字符串来找到这些专利。
  其中一项专利被受让人允许失效，其他专利则是在 GPL 许可下贡献给了 Linux 内核。
  这些专利中有许多（但不是全部）已经过期。
  现在也有基于 LGPL 的用户级 RCU 实现可用（参见 https://liburcu.org/）。
- 我听说 RCU 需要做一些工作才能支持实时内核？

  实时友好的 RCU 可以通过启用内核配置参数 `CONFIG_PREEMPTION` 来实现。
- 在哪里可以找到更多关于 RCU 的信息？

  请查看 `Documentation/RCU/RTFP.txt` 文件。
  或者在浏览器中访问以下链接：
  （https://docs.google.com/document/d/1X0lThx8OK0ZgLMqVoXiR4ZrGURHrXK6NyLRbeXe3Xac/edit）
  或者（https://docs.google.com/document/d/1GCdQC8SDbb54W1shjEXqGZ0Rq8a6kIeYutdSIajfpLA/edit?usp=sharing）。
