SPDX 许可证标识符: (GPL-2.0+ 或 MIT)

===============
VM_BIND 锁定
===============

本文档试图描述如何正确实现 VM_BIND 锁定，包括 userptr mmu_notifier 的锁定。它还讨论了一些优化方法，以避免在最简单实现中循环遍历所有 userptr 映射和外部/共享对象映射。此外，还有一个章节描述了实现可恢复的页面错误所需的 VM_BIND 锁定。DRM GPUVM 辅助函数集
============================

有一套辅助函数用于实现 VM_BIND，并且这套辅助函数实现了本文档中描述的大部分锁定机制，但目前缺少 userptr 的实现。本文档不打算详细描述 DRM GPUVM 实现，具体信息请参阅 :ref:`其自身的文档 <drm_gpuvm>`。强烈建议任何实现 VM_BIND 的驱动程序使用 DRM GPUVM 辅助函数，并在缺少通用功能时进行扩展。

术语
============

* ``gpu_vm``：虚拟 GPU 地址空间的抽象，包含元数据。通常每个客户端（DRM 文件私有）或每个执行上下文有一个。
* ``gpu_vma``：gpu_vm 内的 GPU 地址范围的抽象，带有相关元数据。一个 gpu_vma 的支持存储可以是一个 GEM 对象或匿名或页缓存页面，这些页面也映射到进程的 CPU 地址空间。
* ``gpu_vm_bo``：抽象了一个 GEM 对象与 VM 的关联。GEM 对象维护一个 gpu_vm_bo 列表，每个 gpu_vm_bo 维护一个 gpu_vma 列表。
* ``userptr gpu_vma 或仅称 userptr``：一个 gpu_vma，其支持存储为上述的匿名或页缓存页面。
* ``revalidating``：重新验证一个 gpu_vma 意味着使最新版本的支持存储驻留，并确保 gpu_vma 的页表项指向该支持存储。
* ``dma_fence``：一种类似于 struct completion 的结构体，用于跟踪 GPU 活动。当 GPU 活动结束时，dma_fence 发出信号。详情请参阅 :doc:`dma-buf 文档 </driver-api/dma-buf>` 中的“DMA Fences”部分。
* ``dma_resv``：一个 struct dma_resv（即预约对象），用于跟踪 GPU 活动形式的多个 dma_fences 在 gpu_vm 或 GEM 对象上的情况。dma_resv 包含一个 dma_fences 的数组/列表，并且在向 dma_resv 添加更多 dma_fences 时需要持有锁。该锁允许以任意顺序安全地锁定多个 dma_resvs。详情请参阅 :doc:`dma-buf 文档 </driver-api/dma-buf>` 中的“Reservation Objects”部分。
* ``exec 函数``：一个 exec 函数负责重新验证所有受影响的 gpu_vmas，提交 GPU 命令批次，并将表示 GPU 命令活动的 dma_fence 注册到所有受影响的 dma_resvs。尽管本文档未涵盖，但值得一提的是，exec 函数也可能作为某些驱动程序在计算/长运行模式下使用的重新验证工作线程。
* ``本地对象``：一个仅在单个虚拟内存中映射的 GEM 对象。本地 GEM 对象共享 `gpu_vm` 的 `dma_resv`。
* ``外部对象``（也称为共享对象）：一个可能被多个 `gpu_vm` 共享，并且其底层存储也可能与其他驱动程序共享的 GEM 对象。

锁和锁顺序
===========

VM_BIND 的一个好处是，本地 GEM 对象共享 `gpu_vm` 的 `dma_resv` 对象及其锁。因此，即使有大量的本地 GEM 对象，也只需要一个锁来使执行序列原子化。

以下是一些使用的锁及其锁定顺序：

* `gpu_vm->lock`（可选地为一个读写信号量）。保护 `gpu_vm` 的数据结构，该结构用于跟踪 `gpu_vmas`。它还可以保护 `gpu_vm` 的用户指针 `gpu_vmas` 列表。用 CPU 内存管理类比，这相当于 `mmap_lock`。使用读写信号量可以允许多个读者同时遍历 VM 树，但这种并发的好处可能因驱动程序而异。
* `userptr_seqlock`。这个锁以读模式获取 `gpu_vm` 用户指针列表上的每个用户指针 `gpu_vma`，并在 MMU 通知器失效时以写模式获取。这不是一个真正的序列锁，但在 `mm/mmu_notifier.c` 中描述为“一种类似于序列计数的冲突重试读端/写端‘锁’。然而，这允许多个写端同时持有它。”读端临界区由 `mmu_interval_read_begin()` 和 `mmu_interval_read_retry()` 包围，其中 `mmu_interval_read_begin()` 在写端持有锁时会休眠。
* 写端由核心 MM 在调用 MMU 区间失效通知器时持有。
* `gpu_vm->resv` 锁。保护需要重新绑定的 `gpu_vmas` 列表以及所有 `gpu_vm` 本地 GEM 对象的驻留状态。
此外，它通常还保护已驱逐和外部 GEM 对象的列表。
* `gpu_vm->userptr_notifier_lock`。这是一个读写信号量，在执行期间以读模式获取，在 MMU 通知器失效期间以写模式获取。用户指针通知锁是按 `gpu_vm` 分配的。
* `gem_object->gpuva_lock`。这个锁保护 GEM 对象的 `gpu_vm_bo` 列表。这通常是 GEM 对象的 `dma_resv` 锁，但有些驱动程序以不同的方式保护这个列表，详见下面。
* `gpu_vm list spinlocks`。在某些实现中，它们是必需的，以便能够更新被驱逐的和外部对象的 `gpu_vm` 列表。对于这些实现，在操纵列表时需要获取自旋锁。然而，为了避免与 `dma_resv` 锁的锁定顺序冲突，在遍历列表时需要一个特殊的方案。
.. _gpu_vma 生命周期：

gpu_vm_bos 和 gpu_vmas 的保护与生命周期
=============================================

GEM 对象的 `gpu_vm_bos` 列表以及 `gpu_vm_bo` 的 `gpu_vmas` 列表由 `gem_object->gpuva_lock` 保护，这通常是 GEM 对象的 `dma_resv`，但如果驱动程序需要从 `dma_fence` 信号临界区内部访问这些列表，则可以选择使用单独的锁来保护它，这个锁可以在 `dma_fence` 信号临界区内上锁。这样的驱动程序在遍历 `gpu_vm_bo` 和 `gpu_vmas` 列表时，需要注意需要在循环内获取哪些锁以避免锁定顺序冲突。DRM GPUVM 辅助函数提供锁依赖断言，确保在相关情况下持有此锁，并且还提供了一种使其了解实际使用的锁的方法：:c:func:`drm_gem_gpuva_set_lock`。每个 `gpu_vm_bo` 持有一个指向底层 GEM 对象的引用计数指针，每个 `gpu_vma` 持有一个指向 `gpu_vm_bo` 的引用计数指针。当遍历 GEM 对象的 `gpu_vm_bos` 列表以及 `gpu_vm_bo` 的 `gpu_vmas` 列表时，`gem_object->gpuva_lock` 必须保持不释放，否则，附加到 `gpu_vm_bo` 上的 `gpu_vmas` 可能会无声无息地消失，因为它们不是引用计数的。驱动程序可以实现自己的方案来允许这样做，但代价是增加了复杂性，但这超出了本文档的范围。
在 DRM GPUVM 实现中，每个 `gpu_vm_bo` 和每个 `gpu_vma` 都对 `gpu_vm` 本身持有一个引用计数。由于这一点，并且为了避免循环引用计数，`gpu_vm` 的 `gpu_vmas` 清理工作不应在 `gpu_vm` 的析构函数中进行。驱动程序通常为这种清理实现一个 `gpu_vm` 关闭函数。`gpu_vm` 关闭函数将终止使用该 VM 的 GPU 执行，解除所有 `gpu_vmas` 的映射并释放页表内存。
本地对象的重新验证和驱逐
==========================================

请注意，在下面给出的所有代码示例中，我们使用简化的伪代码。特别是，省略了 `dma_resv` 死锁避免算法以及为 `dma_resv` 围栏预留内存的部分。
重新验证
_____________________
使用 VM_BIND 时，所有本地对象在 GPU 使用 `gpu_vm` 时必须是驻留状态，并且对象需要有有效的 `gpu_vmas` 设置指向它们。因此，通常每个 GPU 命令缓冲区提交之前都会有一个重新验证部分：

.. code-block:: C

   dma_resv_lock(gpu_vm->resv);

   // 验证部分从此开始
   for_each_gpu_vm_bo_on_evict_list(&gpu_vm->evict_list, &gpu_vm_bo) {
           validate_gem_bo(&gpu_vm_bo->gem_bo);

           // 下面的列表迭代需要持有 GEM 对象的 dma_resv（它保护了 `gpu_vm_bo` 的 `gpu_vmas` 列表，但由于本地 GEM 对象共享 `gpu_vm` 的 `dma_resv`，此时已经持有
           for_each_gpu_vma_of_gpu_vm_bo(&gpu_vm_bo, &gpu_vma)
                  move_gpu_vma_to_rebind_list(&gpu_vma, &gpu_vm->rebind_list);
   }

   for_each_gpu_vma_on_rebind_list(&gpu_vm->rebind_list, &gpu_vma) {
           rebind_gpu_vma(&gpu_vma);
           remove_gpu_vma_from_rebind_list(&gpu_vma);
   }
   // 验证部分结束，作业提交开始
   add_dependencies(&gpu_job, &gpu_vm->resv);
   job_dma_fence = gpu_submit(&gpu_job));

   add_dma_fence(job_dma_fence, &gpu_vm->resv);
   dma_resv_unlock(gpu_vm->resv);

拥有一个独立的 `gpu_vm` 重新绑定列表的原因是可能有一些用户指针 `gpu_vmas` 不映射缓冲对象但也需要重新绑定。
驱逐
---

对这些本地对象之一的驱逐将类似于以下过程：

```c
obj = get_object_from_lru();

dma_resv_lock(obj->resv);
for_each_gpu_vm_bo_of_obj(obj, &gpu_vm_bo)
        add_gpu_vm_bo_to_evict_list(&gpu_vm_bo, &gpu_vm->evict_list);

add_dependencies(&eviction_job, &obj->resv);
job_dma_fence = gpu_submit(&eviction_job);
add_dma_fence(&obj->resv, job_dma_fence);

dma_resv_unlock(&obj->resv);
put_object(obj);
```

请注意，由于该对象属于gpu_vm，因此它会共享gpu_vm的dma_resv锁，即 `obj->resv == gpu_vm->resv`。标记为驱逐的gpu_vm_bos将被放入gpu_vm的驱逐列表中，该列表由 `gpu_vm->resv` 保护。在驱逐期间，所有本地对象的dma_resv都会被锁定，并且由于上述等式，也会锁定保护gpu_vm驱逐列表的gpu_vm的dma_resv。使用VM_BIND时，无需在驱逐前解除gpu_vmas的绑定，因为驱动程序必须确保驱逐blit或复制等待GPU空闲或依赖于所有先前的GPU活动。此外，任何后续的GPU尝试通过gpu_vma访问已释放的内存都将由一个新的执行函数进行处理，该函数包含一个重新验证部分，以确保所有gpu_vmas都被重新绑定。持有对象的dma_resv并进行重新验证的驱逐代码将确保新的执行函数不会与驱逐竞争。驱动程序可以实现为在每次执行函数时只选择一部分vmas进行重新绑定。在这种情况下，所有未选择重新绑定的vmas必须在提交执行函数的工作负载之前解除绑定。

外部缓冲对象的锁定
===================

由于外部缓冲对象可能被多个gpu_vm共享，它们不能与单个gpu_vm共享其预留对象。相反，它们需要有自己的预留对象。因此，使用一个或多个gpu_vmas绑定到gpu_vm的外部对象将被放入一个每gpu_vm的列表中，该列表由gpu_vm的dma_resv锁或 :ref:`gpu_vm 列表自旋锁 <Spinlock iteration>` 保护。一旦锁定gpu_vm的预留对象，就可以安全地遍历外部对象列表并锁定所有外部对象的dma_resvs。但是，如果使用了列表自旋锁，则需要更复杂的迭代方案。在驱逐时，需要将外部对象绑定的所有gpu_vm的gpu_vm_bos放入它们各自的gpu_vm驱逐列表中。然而，在驱逐外部对象时，通常不持有该对象绑定的gpu_vm的dma_resvs。只能保证持有对象的私有dma_resv。如果有ww_acquire上下文，我们可以在驱逐时获取这些dma_resvs，但这可能会导致昂贵的ww_mutex回滚。一个简单的选项是仅用一个布尔值`evicted`标记被驱逐的gem对象，该布尔值将在下次需要遍历相应的gpu_vm驱逐列表时检查。例如，在遍历外部对象列表并锁定它们时，此时同时持有gpu_vm的dma_resv和对象的dma_resv，然后可以将标记为已驱逐的gpu_vm_bo添加到gpu_vm的已驱逐gpu_vm_bos列表中。`evicted`布尔值正式上受对象的dma_resv保护。

执行函数变为：

```c
dma_resv_lock(gpu_vm->resv);

// 外部对象列表由gpu_vm->resv锁保护
for_each_gpu_vm_bo_on_extobj_list(gpu_vm, &gpu_vm_bo) {
        dma_resv_lock(gpu_vm_bo.gem_obj->resv);
        if (gpu_vm_bo_marked_evicted(&gpu_vm_bo))
                add_gpu_vm_bo_to_evict_list(&gpu_vm_bo, &gpu_vm->evict_list);
}

for_each_gpu_vm_bo_on_evict_list(&gpu_vm->evict_list, &gpu_vm_bo) {
        validate_gem_bo(&gpu_vm_bo->gem_bo);

        for_each_gpu_vma_of_gpu_vm_bo(&gpu_vm_bo, &gpu_vma)
                move_gpu_vma_to_rebind_list(&gpu_vma, &gpu_vm->rebind_list);
}

for_each_gpu_vma_on_rebind_list(&gpu_vm->rebind_list, &gpu_vma) {
        rebind_gpu_vma(&gpu_vma);
        remove_gpu_vma_from_rebind_list(&gpu_vma);
}

add_dependencies(&gpu_job, &gpu_vm->resv);
job_dma_fence = gpu_submit(&gpu_job);
add_dma_fence(job_dma_fence, &gpu_vm->resv);
for_each_external_obj(gpu_vm, &obj)
        add_dma_fence(job_dma_fence, &obj->resv);
dma_resv_unlock_all_resv_locks();
```

相应的共享对象感知的驱逐看起来像这样：

```c
obj = get_object_from_lru();

dma_resv_lock(obj->resv);
for_each_gpu_vm_bo_of_obj(obj, &gpu_vm_bo)
        if (object_is_vm_local(obj))
                add_gpu_vm_bo_to_evict_list(&gpu_vm_bo, &gpu_vm->evict_list);
        else
                mark_gpu_vm_bo_evicted(&gpu_vm_bo);

add_dependencies(&eviction_job, &obj->resv);
job_dma_fence = gpu_submit(&eviction_job);
add_dma_fence(&obj->resv, job_dma_fence);

dma_resv_unlock(&obj->resv);
put_object(obj);
```

:ref:`Spinlock iteration`:

在不持有dma_resv锁的情况下访问gpu_vm的列表
=================================================

一些驱动程序在访问gpu_vm的驱逐列表和外部对象列表时会持有gpu_vm的dma_resv锁。然而，有些驱动程序需要在不持有dma_resv锁的情况下访问这些列表，例如由于在dma_fence信号关键路径中的异步状态更新。在这种情况下，可以使用自旋锁来保护列表的操作。然而，由于在遍历列表时需要为每个列表项获取高级睡眠锁，已经遍历过的项需要临时移动到一个私有列表并在处理每个项时释放自旋锁：

```c
struct list_head still_in_list;

INIT_LIST_HEAD(&still_in_list);

spin_lock(&gpu_vm->list_lock);
do {
        struct list_head *entry = list_first_entry_or_null(&gpu_vm->list, head);

        if (!entry)
                break;

        list_move_tail(&entry->head, &still_in_list);
        list_entry_get_unless_zero(entry);
        spin_unlock(&gpu_vm->list_lock);

        process(entry);

        spin_lock(&gpu_vm->list_lock);
        list_entry_put(entry);
} while (true);

list_splice_tail(&still_in_list, &gpu_vm->list);
spin_unlock(&gpu_vm->list_lock);
```

由于额外的锁定和原子操作，能够避免在dma_resv锁之外访问gpu_vm列表的驱动程序可能也想避免这种迭代方案。特别是如果驱动程序预期列表项数量较大。对于预期列表项数量较小、列表迭代不经常发生或每次迭代有显著附加成本的列表，此类迭代的原子操作开销很可能可以忽略不计。请注意，如果使用此方案，必须确保此列表迭代受到外层锁或信号量的保护，因为在迭代过程中列表项会被临时移除，并且值得一提的是，本地列表`still_in_list`也应该被视为受`gpu_vm->list_lock`保护，因此在列表迭代时也可以从本地列表中并发移除项目。

请参阅 :ref:`DRM GPUVM锁定部分 <drm_gpuvm_locking>` 及其内部 :c:func:`get_next_vm_bo_from_list` 函数。
`userptr gpu_vma` 是一种 `gpu_vma`，它不是将缓冲区对象映射到 GPU 虚拟地址范围，而是直接映射 CPU 的匿名或文件页缓存页面的内存管理（mm）范围。

一个非常简单的做法是在绑定时使用 `pin_user_pages()` 将页面固定，并在解绑时取消固定，但这会产生拒绝服务（DoS）攻击向量，因为单个用户空间进程能够固定所有系统内存，这是不可取的。（对于特殊用例，并假设适当的计费机制，固定页面仍然可能是一个可取的功能）。一般情况下我们需要做的是获取所需的页面引用，在页面被 CPU mm 即将解除映射之前通过 MMU 通知器来接收通知，如果页面不是以只读方式映射到 GPU，则标记它们为脏页，然后释放引用。

当我们通过 MMU 通知器得知 CPU mm 即将释放这些页面时，我们需要通过等待 MMU 通知器中的 VM 空闲来停止 GPU 对这些页面的访问，并确保在下一次 GPU 尝试访问当前 CPU mm 范围内的内容之前，从 GPU 页表中解除旧页面的映射并重复获取新页面引用的过程。（参见下面的 :ref:`通知器示例 <Invalidation example>`）。请注意，当核心内存管理决定回收页面时，我们会收到这样的解除映射 MMU 通知，并且可以在下次 GPU 访问前再次标记这些页面为脏页。我们还会收到类似的 NUMA 计费相关的 MMU 通知，但 GPU 驱动程序实际上不需要关心这些通知，不过迄今为止排除某些通知已被证明是困难的。

使用 MMU 通知器进行设备 DMA（以及其他方法）在 :ref:`pin_user_pages() 文档 <mmu-notifier-registration-case>` 中有描述。

现在，使用 `get_user_pages()` 获取 `struct page` 引用的方法不幸地不能在 `dma_resv` 锁下使用，因为这会违反 `dma_resv` 锁与解决 CPU 页面错误时获得的 `mmap_lock` 之间的锁定顺序。这意味着 `gpu_vm` 的 `userptr gpu_vma` 列表需要由一个外部锁保护，在下面的例子中，这个锁是 `gpu_vm->lock`。

对于 `userptr gpu_vma` 的 MMU 区间序列锁的使用如下：

```C
// 仅当存在失效的 userptr gpu_vma 时，此处的独占锁定模式才是严格必需的，以避免对同一 userptr gpu_vma 的并发重新验证
down_write(&gpu_vm->lock);
retry:

// 注意：mmu_interval_read_begin() 会阻塞直到没有无效化通知器正在运行
seq = mmu_interval_read_begin(&gpu_vma->userptr_interval);
if (seq != gpu_vma->saved_seq) {
        obtain_new_page_pointers(&gpu_vma);
        dma_resv_lock(&gpu_vm->resv);
        add_gpu_vma_to_revalidate_list(&gpu_vma, &gpu_vm);
        dma_resv_unlock(&gpu_vm->resv);
        gpu_vma->saved_seq = seq;
}

// 通常的重新验证过程在这里
// 最终的 userptr 序列验证必须在 MMU 无效化通知器的 POV 下添加提交的 dma_fence 到 gpu_vm 的 resv 之后发生。因此需要 userptr_notifier_lock 来使它们看起来是原子操作
add_dependencies(&gpu_job, &gpu_vm->resv);
down_read(&gpu_vm->userptr_notifier_lock);
if (mmu_interval_read_retry(&gpu_vma->userptr_interval, gpu_vma->saved_seq)) {
       up_read(&gpu_vm->userptr_notifier_lock);
       goto retry;
}

job_dma_fence = gpu_submit(&gpu_job));

add_dma_fence(job_dma_fence, &gpu_vm->resv);

for_each_external_obj(gpu_vm, &obj)
        add_dma_fence(job_dma_fence, &obj->resv);

dma_resv_unlock_all_resv_locks();
up_read(&gpu_vm->userptr_notifier_lock);
up_write(&gpu_vm->lock);
```

`mmu_interval_read_begin()` 和 `mmu_interval_read_retry()` 之间的代码标记了我们称之为 `userptr_seqlock` 的读端临界区。实际上，会遍历 `gpu_vm` 的 `userptr gpu_vma` 列表，并检查其所有的 `userptr gpu_vma`，尽管这里只展示了其中一个。
用户指针 GPU VMA MMU 无效化通知器可能在回收上下文中被调用，并且为了避免锁定顺序违规，我们不能在此过程中获取任何 `dma_resv` 锁或 `gpu_vm->lock`。

.. _无效化示例：
.. code-block:: C

  bool gpu_vma_userptr_invalidate(userptr_interval, cur_seq)
  {
          // 确保执行函数要么看到新的序列号并退出，要么我们等待 `dma-fence`：

          down_write(&gpu_vm->userptr_notifier_lock);
          mmu_interval_set_seq(userptr_interval, cur_seq);
          up_write(&gpu_vm->userptr_notifier_lock);

          // 到此为止，执行函数无法成功提交新任务，因为 `cur_seq` 是一个无效的序列号，总会导致重试。当所有无效化回调完成时，MMU 通知核心会将序列号切换为有效值。然而我们需要在此处停止 GPU 访问旧页面
          dma_resv_wait_timeout(&gpu_vm->resv, DMA_RESV_USAGE_BOOKKEEP,
                                false, MAX_SCHEDULE_TIMEOUT);
          return true;
  }

当此无效化通知器返回时，GPU 不再能够访问用户指针 GPU VMA 的旧页面，并且需要重新绑定页面才能使新的 GPU 提交成功。

高效的用户指针 GPU VMA 执行函数迭代
________________________________________________

如果 `gpu_vm` 的用户指针 GPU VMA 列表变得很大，在每次执行函数中遍历完整的用户指针列表来检查每个用户指针 GPU VMA 的保存序列号是否过期是低效的。解决方法是将所有 *已无效化* 的用户指针 GPU VMA 放在一个单独的 `gpu_vm` 列表上，并且仅在每次执行函数中检查该列表中的 GPU VMA。这个列表非常适合使用自旋锁锁定方案，该方案 :ref:`在自旋锁迭代部分进行了描述 <Spinlock iteration>`，因为在 MMU 通知器中，我们将无效化的 GPU VMA 添加到列表时，无法获取外部锁如 `gpu_vm->lock` 或 `gpu_vm->resv` 锁。请注意，在迭代时仍然需要获取 `gpu_vm->lock` 来确保列表完整，正如该部分所述。
如果使用这样的无效化用户指针列表，则执行函数中的重试检查简单地变为检查无效化列表是否为空。

绑定和解绑时的锁定
===============================

在绑定时，假设是一个 GEM 对象支持的 GPU VMA，每个 GPU VMA 需要与一个 `gpu_vm_bo` 关联，并且该 `gpu_vm_bo` 又需要添加到 GEM 对象的 `gpu_vm_bo` 列表中，可能还需要添加到 `gpu_vm` 的外部对象列表中。这被称为 *链接* GPU VMA，通常需要持有 `gpu_vm->lock` 和 `gem_object->gpuva_lock`。当解除链接 GPU VMA 时，同样需要持有这些锁，这确保了在遍历 `gpu_vmas` 时（无论是在 `gpu_vm->resv` 下还是 GEM 对象的 `dma_resv` 下），只要不释放我们遍历的锁，GPU VMA 就保持存活。对于用户指针 GPU VMA，同样要求在销毁 VMA 期间持有外部 `gpu_vm->lock`，否则在遍历前一节描述的无效化用户指针列表时，没有任何东西能保证这些用户指针 GPU VMA 存活。

可恢复页错误的页表更新锁定
=====================================================

对于可恢复页错误，我们需要确保两件重要的事情：

* 在我们将页面归还给系统/分配器以供重用时，不应存在剩余的 GPU 映射，并且任何 GPU TLB 都必须已被刷新
* GPU VMA 的解除映射和映射不应发生竞争

由于 GPU PTE 的解除映射（或清除）通常发生在很难甚至不可能获取任何外层锁的地方，我们必须引入一个新的锁，在映射和解除映射时都持有该锁，或者查看我们在解除映射时持有的锁，并确保在映射时也持有这些锁。对于用户指针 GPU VMA，`userptr_seqlock` 在 MMU 无效化通知器中以写模式持有，其中发生清除操作。因此，如果在映射时以读模式持有 `userptr_seqlock` 以及 `gpu_vm->userptr_notifier_lock`，则不会与清除发生竞争。对于 GEM 对象支持的 GPU VMA，清除将在 GEM 对象的 `dma_resv` 下进行，确保在填充指向 GEM 对象的任何 GPU VMA 的页表时也持有 `dma_resv`，同样可以确保无竞争。

如果映射的任何部分在释放这些锁的情况下异步在 `dma-fence` 下执行，则清除需要在相关锁下等待该 `dma-fence` 触发信号，然后开始修改页表。
由于以释放页表内存的方式修改页表结构可能还需要外层锁，因此GPU页表项（PTEs）的清除通常仅集中在将页表或页目录项清零以及刷新TLB上，而释放页表内存的操作则被推迟到解绑定或重新绑定时进行。
