SPDX 许可证标识符: GPL-2.0

=================
KVM 锁概述
=================

1. 获取顺序
---------------------

互斥锁的获取顺序如下：

- cpus_read_lock() 在 kvm_lock 外部获取。

- kvm->lock 在 vcpu->mutex 外部获取。

- kvm->lock 在 kvm->slots_lock 和 kvm->irq_lock 外部获取。

- kvm->slots_lock 在 kvm->irq_lock 外部获取，尽管同时获取它们的情况很少。
- kvm->mn_active_invalidate_count 确保成对的 invalidate_range_start() 和 invalidate_range_end() 回调使用相同的 memslots 数组。在修改 memslots 时，kvm->slots_lock 和 kvm->slots_arch_lock 在等待侧获取，因此 MMU 通知器不得获取 kvm->slots_lock 或 kvm->slots_arch_lock。
对于 SRCU：

- ``synchronize_srcu(&kvm->srcu)`` 被调用在 kvm->lock、vcpu->mutex 和 kvm->slots_lock 的临界区内部。这些锁不能在 kvm->srcu 读取侧临界区内获取；也就是说，以下操作是错误的：

      srcu_read_lock(&kvm->srcu);
      mutex_lock(&kvm->slots_lock);

- kvm->slots_arch_lock 而是在调用 ``synchronize_srcu()`` 之前释放。因此可以在 kvm->srcu 读取侧临界区内获取，例如在处理 vmexit 时。
在 x86 上：

- vcpu->mutex 在 kvm->arch.hyperv.hv_lock 和 kvm->arch.xen.xen_lock 外部获取。

- kvm->arch.mmu_lock 是一个读写锁；kvm->arch.tdp_mmu_pages_lock 和 kvm->arch.mmu_unsync_pages_lock 的临界区也必须获取 kvm->arch.mmu_lock。

其他所有锁都是叶节点：在临界区内不获取任何其他锁。

2. 例外情况
------------

快速页面故障：

快速页面故障是在 x86 上 mmu-lock 之外修复访客页面故障的快速路径。目前，页面故障可以在以下两种情况下快速处理：

1. 访问跟踪：SPTE（影子页表条目）不存在，但被标记为访问跟踪。这意味着我们需要恢复保存的 R/X 位。这将在下面详细描述。
2. 写保护：SPTE 存在且故障由写保护引起。这意味着我们只需更改 SPTE 的 W 位即可。

我们用来避免所有竞态的方法是 SPTE 上的主机可写位和 MMU 可写位：

- 主机可写意味着 gfn 在主机内核页表及其 KVM memslot 中是可写的。
- MMU 可写意味着 gfn 在访客的 MMU 中是可写的，并且没有通过影子页写保护来写保护。

在快速页面故障路径中，我们将使用 cmpxchg 原子地设置 SPTE 的 W 位，如果 SPTE.HOST_WRITEABLE = 1 且 SPTE.WRITE_PROTECT = 1，则恢复访问跟踪 SPTE 的保存 R/X 位，或两者都进行。这是安全的，因为每次更改这些位都可以通过 cmpxchg 检测到。

但我们需要仔细检查这些情况：

1) gfn 到 pfn 的映射

gfn 到 pfn 的映射可能会发生变化，因为我们只能确保在 cmpxchg 期间 pfn 不变。这是一个 ABA 问题，例如，下面的情况会发生：

+------------------------------------------------------------------------+
| 在开始时::                                                               |
|                                                                         |
|   gpte = gfn1                                                      |
|   gfn1 在主机上映射到 pfn1                                       |
|   spte 是与 gpte 对应的影子页表条目，且 spte = pfn1                          |
+------------------------------------------------------------------------+
| 在快速页面故障路径上:                                                    |
+------------------------------------+-----------------------------------+
| CPU 0:                             | CPU 1:                            |
+------------------------------------+-----------------------------------+
| ::                                 |                                   |
|                                     |                                   |
|   old_spte = *spte;                |                                   |
+------------------------------------+-----------------------------------+
|                                     | pfn1 被交换出::                   |
|                                     |                                   |
|                                     |    spte = 0;                      |
|                                     |                                   |
|                                     | pfn1 被重新分配给 gfn2。          |
|                                     |                                   |
|                                     | 访客将 gpte 更改为指向 gfn2::     |
|                                     |                                   |
|                                     |    spte = pfn1;                   |
+------------------------------------+-----------------------------------+
| ::                                                                 |
|                                                                         |
|   if (cmpxchg(spte, old_spte, old_spte+W)                            |
|   mark_page_dirty(vcpu->kvm, gfn1)                                   |
|            OOPS!!!                                                   |
+------------------------------------------------------------------------+

我们为 gfn1 记录脏日志，这意味着 gfn2 在脏位图中丢失了。
对于直接 SP（shadow page table entry），我们可以轻松避免它，因为直接 SP 的 SPT 入口固定到 GFN（guest physical address）。对于间接 SP，为了简化起见，我们禁用了快速页错误。对于间接 SP 的解决方案可以是在 cmpxchg 之前使用 `kvm_vcpu_gfn_to_pfn_atomic` 将 GFN 固定。固定后：

- 我们持有了 PFN 的引用计数；这意味着 PFN 不会被释放并被重用于其他 GFN。
- PFN 是可写的，因此它不能被 KSM 在不同的 GFN 之间共享。
这样，我们可以确保 GFN 的脏位图正确设置。
2）脏位跟踪

在原始代码中，如果 SPT 条目是只读的且 Accessed 位已经被设置，则 SPT 可以快速更新（非原子操作），因为 Accessed 位和 Dirty 位不会丢失。但在快速页错误之后，这不再成立，因为在读取 SPT 和更新 SPT 之间的这段时间内，SPT 可能被标记为可写。如下所示：

```
+------------------------------------------------------------------------+
| 初始状态：                                                             |
|                                                                        |
|   spte.W = 0                                                           |
|   spte.Accessed = 1                                                    |
+------------------------------------+-----------------------------------+
| CPU 0:                               | CPU 1:                            |
+------------------------------------+-----------------------------------+
| 在 mmu_spte_clear_track_bits() 中： |                                  |
|                                     |                                  |
|   old_spte = *spte;                 |                                  |
|                                     |                                  |
|                                     |                                  |
|   /* 'if' 条件满足。*/               |                                  |
|   if (old_spte.Accessed == 1 &&     |                                  |
|        old_spte.W == 0)              |                                  |
|      spte = 0ull;                    |                                  |
+------------------------------------+-----------------------------------+
|                                     | 快速页错误路径：                 |
|                                     |                                  |
|                                     |   spte.W = 1                     |
|                                     |                                  |
|                                     | 对 SPT 写入内存：                |
|                                     |                                  |
|                                     |   spte.Dirty = 1                 |
+------------------------------------+-----------------------------------+
|                                     |                                  |
|   否则                               |                                  |
|     old_spte = xchg(spte, 0ull)      |                                  |
|   if (old_spte.Accessed == 1)        |                                  |
|     kvm_set_pfn_accessed(spte.pfn);  |                                  |
|   if (old_spte.Dirty == 1)           |                                  |
|     kvm_set_pfn_dirty(spte.pfn);     |                                  |
|     啊哦！！！                       |                                  |
+------------------------------------+-----------------------------------+
```

在这种情况下，Dirty 位丢失了。
为了避免这类问题，如果 SPT 可能在 mmu 锁之外被更新，我们将始终将其视为“volatile”[参见 spte_has_volatile_bits()]；这意味着在这种情况下 SPT 总是以原子方式更新。
3）由于 SPT 更新而刷新 TLB

如果 SPT 从可写更新为只读，我们应该刷新所有 TLB，否则 rmap_write_protect 可能会发现一个只读的 SPT，即使可写的 SPT 可能被缓存在某个 CPU 的 TLB 中。
如前所述，在快速页错误路径上，SPT 可能在 mmu 锁之外被更新为可写。为了便于审计该路径，我们在 mmu_spte_update() 中检查是否需要由于这个原因刷新 TLB，因为这是一个更新 SPT 的通用函数（存在 -> 存在）。
由于如果 SPT 可能在 mmu 锁之外被更新，我们将始终以原子方式更新 SPT，并且由此导致的快速页错误竞争可以被避免。
参见 `spte_has_volatile_bits()` 和 `mmu_spte_update()` 中的注释：
无锁访问跟踪：

此功能用于使用EPT但不支持EPT A/D位的Intel CPU。在这种情况下，页表项（PTE）被标记为A/D禁用（使用被忽略的位），当KVM MMU通知器被调用来跟踪对页面的访问时（通过`kvm_mmu_notifier_clear_flush_young`），它会通过清除PTE中的RWX位来将PTE标记为硬件中不可见，并将原始的R和X位存储在更多的未使用/被忽略的位中。当虚拟机稍后尝试访问该页面时，会生成一个故障，并使用上述快速页面故障机制以原子方式将PTE恢复到Present状态。在标记PTE进行访问跟踪时不会保存W位，在恢复到Present状态时，根据是否为写入访问来设置W位。如果不是写入访问，则W位将保持清零状态，直到发生写入访问，此时将使用上述脏位跟踪机制将其设置。
3. 参考
------------

``kvm_lock``
^^^^^^^^^^^^

类型：互斥锁  
架构：任何  
保护内容：- vm_list  
         - kvm_usage_count  
         - 硬件虚拟化启用/禁用  
备注：KVM也在启用/禁用期间通过`cpus_read_lock()`禁用CPU热插拔  
``kvm->mn_invalidate_lock``
^^^^^^^^^^^^^^^^^^^^^^^^^^^

类型：自旋锁  
架构：任何  
保护内容：mn_active_invalidate_count, mn_memslots_update_rcuwait  
``kvm_arch::tsc_write_lock``
^^^^^^^^^^^^^^^^^^^^^^^^^^^^

类型：raw自旋锁  
架构：x86  
保护内容：- kvm_arch::{last_tsc_write,last_tsc_nsec,last_tsc_offset}  
           - vmcb中的TSC偏移量  
备注：'raw'是因为更新TSC偏移量时不能被抢占  
``kvm->mmu_lock``
^^^^^^^^^^^^^^^^^

类型：自旋锁或读写锁  
架构：任何  
保护内容：影子页/影子TLB条目  
备注：由于它在MMU通知器中使用，因此是自旋锁  
``kvm->srcu``
^^^^^^^^^^^^^

类型：SRCU锁  
架构：任何  
保护内容：- kvm->memslots  
         - kvm->buses  
备注：在访问memslots（例如使用gfn_to_*函数时）以及访问内核MMIO/PIO地址到设备结构映射（kvm->buses）时必须持有SRCU读锁  
可以在每个vcpu的`kvm_vcpu->srcu_idx`中存储SRCU索引，如果需要在多个函数中使用  
``kvm->slots_arch_lock``
^^^^^^^^^^^^^^^^^^^^^^^^

类型：互斥锁  
架构：任何（仅在x86上需要）  
保护内容：在`kvm->srcu`读侧临界区中需要修改的memslots的任何架构特定字段  
备注：必须在读取当前memslots指针之前持有该锁，直到所有对memslots的更改完成  
``wakeup_vcpus_on_cpu_lock``
^^^^^^^^^^^^^^^^^^^^^^^^^^^^

类型：自旋锁  
架构：x86  
保护内容：wakeup_vcpus_on_cpu  
备注：这是每个CPU的锁，并用于VT-d发布的中断处理
当支持 VT-d 中断发布（posted-interrupts）并且虚拟机已分配设备时，我们会将被阻塞的 vCPU 放到由 `blocked_vcpu_on_cpu_lock` 保护的 `blocked_vcpu_on_cpu` 列表中。当 VT-d 硬件由于来自已分配设备的外部中断发出唤醒通知事件时，我们将从列表中找到该 vCPU 并将其唤醒。

``vendor_module_lock``
^^^^^^^^^^^^^^^^^^^^^^^^^^^^
- 类型：互斥锁（mutex）
- 架构：x86
- 保护内容：加载供应商模块（kvm_amd 或 kvm_intel）
- 说明：存在原因是使用 kvm_lock 会导致死锁。cpu_hotplug_lock 在 kvm_lock 之外获取，例如在 KVM 的 CPU 在线/离线回调中，许多操作在加载供应商模块时需要获取 cpu_hotplug_lock，例如更新静态调用。
