SPDX 许可证标识符: GPL-2.0

=================
KVM VCPU 请求
=================

概述
========

KVM 支持一个内部API，使线程能够请求一个VCPU线程执行某些活动。例如，一个线程可以请求一个VCPU刷新其TLB。该API包含以下函数：

  /* 检查VCPU @vcpu 是否有任何待处理的请求。 */
  bool kvm_request_pending(struct kvm_vcpu *vcpu);

  /* 检查VCPU @vcpu 是否有待处理的请求 @req。 */
  bool kvm_test_request(int req, struct kvm_vcpu *vcpu);

  /* 清除VCPU @vcpu 的请求 @req。 */
  void kvm_clear_request(int req, struct kvm_vcpu *vcpu);

  /*
   * 检查VCPU @vcpu 是否有待处理的请求 @req。当请求待处理时，它将被清除，并发出一个内存屏障，该屏障与kvm_make_request()中的另一个屏障配对。
   */
  bool kvm_check_request(int req, struct kvm_vcpu *vcpu);

  /*
   * 向VCPU @vcpu 发出请求 @req。在设置请求之前，会发出一个内存屏障，该屏障与kvm_check_request()中的另一个屏障配对。
   */
  void kvm_make_request(int req, struct kvm_vcpu *vcpu);

  /* 向具有结构体kvm @kvm的所有虚拟机VCPUs发出请求 @req。 */
  bool kvm_make_all_cpus_request(struct kvm *kvm, unsigned int req);

通常情况下，请求者希望VCPU在发出请求后尽快执行活动。这意味着大多数请求（kvm_make_request()调用）后面会跟着一个kvm_vcpu_kick()调用，并且kvm_make_all_cpus_request()内置了对所有VCPU的唤醒功能。

VCPU 唤醒
----------

VCPU唤醒的目标是将VCPU线程从客户模式中带出以执行一些KVM维护操作。为此，发送一个IPI，强制退出客户模式。然而，在唤醒时，VCPU线程可能不在客户模式中。因此，根据VCPU线程的模式和状态，唤醒可能会采取另外两种动作。以下是三种可能的动作：

1) 发送一个IPI。这会强制退出客户模式。
2) 唤醒休眠的VCPU。休眠的VCPU是指那些不在客户模式下并且等待等待队列的VCPU线程。唤醒它们会将这些线程从等待队列中移除，允许线程再次运行。这种行为可以通过KVM_REQUEST_NO_WAKEUP来抑制。
3) 无操作。当VCPU不在客户模式下并且VCPU线程没有休眠时，则无需任何操作。

VCPU 模式
---------

VCPU有一个模式状态 `vcpu->mode`，用于跟踪客户是否在客户模式下运行，以及一些特定的非客户模式状态。架构可以使用 `vcpu->mode` 来确保VCPU请求被VCPU看到（见“确保请求被看到”），避免不必要的IPI发送（见“IPI减少”），甚至确保等待IPI确认（见“等待确认”）。以下定义了以下模式：

OUTSIDE_GUEST_MODE

  VCPU线程处于非客户模式
IN_GUEST_MODE

  VCPU线程处于客户模式
EXITING_GUEST_MODE

  VCPU线程正在从IN_GUEST_MODE过渡到OUTSIDE_GUEST_MODE
READING_SHADOW_PAGE_TABLES

  VCPU线程处于非客户模式，但它希望某些VCPU请求的发送方（特别是KVM_REQ_TLB_FLUSH）等待VCPU线程读取完页表。
VCPU 请求内部机制
======================

VCPU 请求只是 ``vcpu->requests`` 位图中的位索引。
这意味着一般位操作（如在 [atomic-ops]_ 中所记录的）也可以被使用，例如：

```c
clear_bit(KVM_REQ_UNBLOCK & KVM_REQUEST_MASK, &vcpu->requests);
```

然而，VCPU 请求用户应避免这样做，因为这会破坏抽象。前8位保留用于与架构无关的请求；所有额外的位可用于架构相关的请求。

### 与架构无关的请求
#### KVM_REQ_TLB_FLUSH

KVM 的通用MMU通知器可能需要刷新虚拟机的所有TLB条目，通过调用 `kvm_flush_remote_tlbs()` 来实现。选择使用通用 `kvm_flush_remote_tlbs()` 实现的架构需要处理这个VCPU请求。

#### KVM_REQ_VM_DEAD

此请求告知所有VCPU，虚拟机已死亡且不可用，例如由于致命错误或有意销毁了虚拟机的状态。

#### KVM_REQ_UNBLOCK

此请求告知vCPU退出 `kvm_vcpu_block`。例如，在主机上代表vCPU运行的定时器处理程序可能会使用它，或者为了更新中断路由并确保分配的设备能够唤醒vCPU。

#### KVM_REQ_OUTSIDE_GUEST_MODE

此“请求”确保目标vCPU在请求发送者继续之前已退出Guest模式。目标不需要采取任何行动，因此实际上不会为该目标记录任何请求。此请求类似于“踢出”，但与踢出不同的是，它保证vCPU实际上已经退出了Guest模式。踢出仅保证vCPU将在某个时刻退出，例如之前的踢出可能已经开始这一过程，但无法保证要被踢出的vCPU已经完全退出Guest模式。

### KVM_REQUEST_MASK

在使用位操作之前，VCPU请求应该通过 `KVM_REQUEST_MASK` 进行掩码。这是因为只有最低8位用于表示请求的编号。高位用作标志。目前只定义了两个标志。

#### VCPU 请求标志
##### KVM_REQUEST_NO_WAKEUP

此标志应用于只需要立即关注正在Guest模式下运行的VCPU的请求。也就是说，睡眠中的VCPU无需为这些请求被唤醒。睡眠中的VCPU会在因其他原因被唤醒时处理这些请求。

##### KVM_REQUEST_WAIT

当带有此标志的请求通过 `kvm_make_all_cpus_request()` 发出时，则调用者将等待每个VCPU确认其IPI后再继续。此标志仅适用于将接收IPI的VCPU。如果VCPU处于睡眠状态，因此不需要IPI，则请求线程不会等待。这意味着此标志可以安全地与 `KVM_REQUEST_NO_WAKEUP` 结合使用。有关带 `KVM_REQUEST_WAIT` 标志请求的更多信息，请参阅“等待确认”。
带有相关状态的VCPU请求
===================================

请求者希望接收VCPU处理新状态时，需要确保新写入的状态在接收VCPU线程的CPU观察到请求之前是可观察的。这意味着在写入新状态之后和设置VCPU请求位之前必须插入一个写内存屏障。此外，在接收VCPU线程的一侧，在读取请求位之后和继续读取与之相关的状态之前，必须插入相应的读屏障。请参见[lwn-mb]_中的场景3（消息和标志）以及内核文档[memory-barriers]_。
函数对kvm_check_request()和kvm_make_request()提供了内存屏障，允许这一要求由API内部处理。

确保请求被看到
==========================

当向VCPU发出请求时，我们希望避免接收VCPU在访客模式下执行任意长时间而不处理请求。只要确保VCPU线程在进入访客模式之前检查kvm_request_pending()并且在必要时踢出IPI以强制退出访客模式，我们可以确信这种情况不会发生。
必须格外注意VCPU线程最后一次kvm_request_pending()检查后和进入访客模式之前的这段时间，因为踢出IPI将仅触发处于访客模式或至少已禁用中断以准备进入访客模式的VCPU线程的访客模式退出。这意味着优化实现（见“IPI减少”）必须确定何时可以不发送IPI。一种解决方案（除了s390之外的所有架构都采用）是：

- 在禁用中断和最后一次kvm_request_pending()检查之间将`vcpu->mode`设置为IN_GUEST_MODE；
- 进入访客模式时原子启用中断。
此解决方案还需要在请求线程和接收VCPU中仔细放置内存屏障。通过内存屏障，我们可以排除VCPU线程在其最后一次检查时观察到!kvm_request_pending()然后没有接收到下一个请求的IPI的可能性，即使该请求是在检查之后立即发出的。这是通过Dekker内存屏障模式完成的（[lwn-mb]_中的场景10）。由于Dekker模式需要两个变量，因此此解决方案将`vcpu->mode`与`vcpu->requests`配对。将其代入模式得到：

  CPU1                                    CPU2
  =================                       =================
  local_irq_disable();
  WRITE_ONCE(vcpu->mode, IN_GUEST_MODE);  kvm_make_request(REQ, vcpu);
  smp_mb();                               smp_mb();
  if (kvm_request_pending(vcpu)) {        if (READ_ONCE(vcpu->mode) ==
                                              IN_GUEST_MODE) {
      ...阻止进入访客模式...                  ...发送IPI...
}                                       }

如上所述，IPI仅对于处于访客模式或已禁用中断的VCPU线程有用。这就是为什么这种特定的Dekker模式扩展到在将`vcpu->mode`设置为IN_GUEST_MODE之前禁用中断。使用WRITE_ONCE()和READ_ONCE()来严谨地实现内存屏障模式，保证编译器不会干扰对`vcpu->mode`的精心规划访问。

IPI减少
-------------

由于只需要一个IPI即可让VCPU检查任何/所有请求，因此它们可以合并。这可以通过第一个发送踢出IPI同时改变VCPU模式为非IN_GUEST_MODE轻松完成。过渡状态EXITING_GUEST_MODE用于此目的。

等待确认
----------------------------

一些请求，那些设置了KVM_REQUEST_WAIT标志的请求，即使目标VCPU线程处于非IN_GUEST_MODE模式下，也需要发送IPI并等待确认。例如，当目标VCPU线程处于READING_SHADOW_PAGE_TABLES模式时就是如此，该模式是在禁用中断之后设置的。为了支持这些情况，KVM_REQUEST_WAIT标志改变了发送IPI的条件，从检查VCPU是否处于IN_GUEST_MODE改为检查它是否不在OUTSIDE_GUEST_MODE。

无请求VCPU踢出
-----------------------

由于是否发送IPI的决定取决于两变量Dekker内存屏障模式，很明显无请求VCPU踢出几乎总是不正确的。如果没有保证非生成IPI的踢出仍然会导致接收VCPU采取行动，就像最终的kvm_request_pending()检查对于带有请求的踢出所做的那样，那么踢出可能根本没有任何作用。如果，例如，向即将将其模式设置为IN_GUEST_MODE的VCPU发出无请求踢出，意味着没有发送IPI，则VCPU线程可能会继续其入口而实际上没有完成踢出本应启动的任何操作。
一个例外是x86的发布中断机制。然而，在这种情况下，即使是无请求VCPU踢出也与上面描述的local_irq_disable() + smp_mb()模式相关联；发布中断描述符中的ON位（Outstanding Notification）充当`vcpu->requests`的角色。当发送发布中断时，PIR.ON在读取`vcpu->mode`之前设置；同样，在VCPU线程中，vmx_sync_pir_to_irr()在将`vcpu->mode`设置为IN_GUEST_MODE之后读取PIR。
附加考虑
=========================

休眠的 VCPU 线程
--------------

VCPU 线程可能需要在调用可能使其进入休眠状态的函数之前和/或之后考虑请求，例如 kvm_vcpu_block()。它们是否需要这样做，以及如果需要的话，哪些请求需要被考虑，这取决于具体架构。kvm_vcpu_block() 调用 kvm_arch_vcpu_runnable() 来检查是否应该唤醒。这样做的一个原因是为架构提供一个可以检查请求的函数，如果有必要的话。

参考文献
==========

.. [atomic-ops] 文档/atomic_bitops.txt 和 文档/atomic_t.txt
.. [memory-barriers] 文档/memory-barriers.txt
.. [lwn-mb] https://lwn.net/Articles/573436/
