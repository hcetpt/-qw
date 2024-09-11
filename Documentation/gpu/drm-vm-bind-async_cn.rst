SPDX 许可证标识符: (GPL-2.0+ 或 MIT)

====================
异步 VM_BIND
====================

术语定义:
=============

* ``VRAM``: 设备上的内存。有时也称为设备本地内存。
* ``gpu_vm``: 一个虚拟 GPU 地址空间。通常每个进程有一个，但也可以由多个进程共享。
* ``VM_BIND``: 通过 IOCTL 修改 gpu_vm 的操作或一系列操作。这些操作包括映射和取消映射系统或 VRAM 内存。
* ``syncobj``: 一个抽象同步对象的容器。这些同步对象可以是通用的，如 dma-fences，也可以是特定于驱动程序的。一个 syncobj 通常表示底层同步对象的类型。
* ``in-syncobj``: VM_BIND IOCTL 的参数，VM_BIND 操作在开始前等待这些同步对象。
* ``out-syncobj``: VM_BIND_IOCTL 的参数，VM_BIND 操作在绑定操作完成后会通知这些同步对象。
* ``dma-fence``: 跨驱动程序的同步对象。理解 dma-fences 是理解本文档的基础。请参阅 :doc:`dma-buf 文档 </driver-api/dma-buf>` 中的“DMA Fences”部分。
* ``memory fence``: 一种不同于 dma-fence 的同步对象。一个 memory fence 使用指定内存位置的值来确定其是否已通知状态。一个 memory fence 可以由 GPU 和 CPU 等待和通知。Memory fences 有时也称为 user-fences、userspace-fences 或 gpu futexes，并不一定遵守 dma-fence 规则中的“合理时间内通知”的规定。因此，内核应避免在持有锁的情况下等待 memory fences。
* ``长期运行的工作负载``：指可能需要超过当前规定的 dma-fence 最大信号延迟才能完成的工作负载，因此需要将 gpu_vm 或 GPU 执行上下文设置为某种模式，该模式不允许完成 dma-fence
* ``exec 函数``：exec 函数是一种函数，它重新验证所有受影响的 gpu_vmas，并提交一个 GPU 命令批次，然后将代表 GPU 命令活动的 dma_fence 注册到所有受影响的 dma_resvs。为了完整性，尽管不在本文档的覆盖范围内，值得一提的是，exec 函数也可能作为某些驱动程序在计算/长期运行模式中使用的重新验证工作线程
* ``绑定上下文``：用于 VM_BIND 操作的上下文标识符。使用相同绑定上下文的 VM_BIND 操作可以假定按提交顺序完成（在相关时）。对于使用不同绑定上下文的 VM_BIND 操作，不能做出这样的假设
* ``UMD``：用户模式驱动
* ``KMD``：内核模式驱动

同步/异步 VM_BIND 操作
========================

同步 VM_BIND
_____________
使用同步 VM_BIND 时，所有 VM_BIND 操作在 IOCTL 返回之前完成。同步 VM_BIND 不接受输入 fence 也不输出 fence。同步 VM_BIND 可能会阻塞并等待 GPU 操作；例如交换或清除操作，甚至之前的绑定操作

异步 VM_BIND
_____________
异步 VM_BIND 接受输入同步对象（in-syncobjs）和输出同步对象（out-syncobjs）。虽然 IOCTL 可能立即返回，但 VM_BIND 操作会在修改 GPU 页表前等待输入同步对象，并在修改完成后通过输出同步对象发出信号，这样下一个等待输出同步对象的 exec 函数可以看到这些更改。错误会同步报告
在低内存情况下，实现可能会阻塞，以同步方式执行 VM_BIND，因为可能没有足够的内存立即用于准备异步操作
如果 VM_BIND IOCTL 将一组操作或操作数组作为参数，则输入同步对象需要在第一个操作开始执行前发出信号，而输出同步对象在最后一个操作完成后发出信号。操作列表中的操作可以假定按顺序完成（在相关时）
由于异步 VM_BIND 操作可能会使用嵌入在输出同步对象中的 dma-fence 和 KMD 内部的 dma-fence 来发出绑定完成信号，因此任何作为 VM_BIND 输入 fence 的内存 fence 都需要在 VM_BIND ioctl 返回之前同步等待，因为为了在合理的时间内发出信号所需的 dma-fence 不能依赖于没有这种限制的内存 fence
异步 VM_BIND 操作的目的在于允许用户模式驱动程序对交错的 GPU_VM 修改和执行函数进行流水线处理。对于长时间运行的工作负载，不允许此类绑定操作的流水线处理，并且需要同步等待任何内部围栏。原因有两点：首先，任何由长时间运行工作负载控制并用作 VM_BIND 操作内部同步对象的内存围栏都需要同步等待（见上文）。其次，任何用于长时间运行工作负载 VM_BIND 操作的 DMA 围栏作为内部同步对象时，也无法实现流水线处理，因为长时间运行的工作负载不允许将 DMA 围栏作为外部同步对象使用。虽然理论上可行，但其使用是值得商榷的，应拒绝使用直到出现有价值的用例。请注意，这不是由 DMA 围栏规则强加的限制，而是为了简化 KMD 实现而施加的限制。它不影响将 DMA 围栏作为长时间运行工作负载本身的依赖项使用，这在 DMA 围栏规则下是允许的，但仅限于 VM_BIND 操作。

异步 VM_BIND 操作可能需要相当长的时间来完成并发出外部围栏信号。特别是在该操作与其他 VM_BIND 操作和通过执行函数提交的工作负载深度流水线化的情况下。在这种情况下，UMD 可能希望避免后续的 VM_BIND 操作排队在第一个之后，如果没有明确的依赖关系。为了避免此类排队，VM_BIND 实现可以允许创建 VM_BIND 上下文。对于每个上下文，VM_BIND 操作将按提交顺序保证完成，但对于不同 VM_BIND 上下文上执行的 VM_BIND 操作则不保证顺序。相反，KMD 将尝试并行执行这些 VM_BIND 操作，但不能保证它们实际上会被并行执行。可能存在只有 KMD 知道的内部隐式依赖关系，例如页表结构的变化。一种尝试避免这些内部依赖关系的方法是让不同的 VM_BIND 上下文使用 VM 的不同区域。

对于长时间运行的 GPU_VM，用户模式驱动程序通常应选择内存围栏作为外部围栏，因为这样可以为内核模式驱动程序提供更大的灵活性，在绑定/解绑操作中插入其他操作。例如，在批量缓冲区中插入断点。然后可以轻松地在绑定完成之后使用内存外部围栏作为 UMD 嵌入工作负载中的 GPU 信号量的信号条件来流水线化工作负载执行。

异步 VM_BIND 和同步 VM_BIND 支持的操作或多操作支持之间没有区别。

多操作 VM_BIND IOCTL 错误处理和中断
=======================================

VM_BIND 操作可能会因各种原因出错，例如由于缺乏完成操作所需的资源或中断等待。

在这种情况下，UMD 应尽可能在采取适当行动后重新启动 IOCTL。
如果 UMD 超分配了内存资源，则会返回 -ENOSPC 错误，此时 UMD 可以解除未使用的资源并重新运行 IOCTL。在 -EINTR 情况下，UMD 应简单地重新运行 IOCTL；在 -ENOMEM 情况下，用户空间可以选择释放已知系统内存资源或失败。如果 UMD 决定由于错误返回而失败绑定操作，则无需额外的操作来清理失败的操作，VM 保持在失败 IOCTL 之前的状态。

解绑操作保证不会因资源约束返回错误，但可能会因无效参数或 GPU_VM 被禁用等原因返回错误。

如果在异步绑定过程中发生意外错误，GPU_VM 将被禁用，并且在禁用后试图使用它将返回 -ENOENT。
示例：Xe VM_BIND 用户空间API
============================

从 VM_BIND 操作结构体开始，IOCTL 调用可以接收零个、一个或多个此类操作。零个操作意味着仅执行 IOCTL 的同步部分：异步 VM_BIND 更新同步对象，而同步 VM_BIND 等待隐式依赖关系被满足。
.. code-block:: c

   struct drm_xe_vm_bind_op {
	/**
	 * @obj: 要操作的 GEM 对象，对于 MAP_USERPTR 和 UNMAP 均为必须为空（MBZ）
	 */
	__u32 obj;

	/** @pad: 必须为空（MBZ） */
	__u32 pad;

	union {
		/**
		 * @obj_offset: 对象中的偏移量，用于 MAP
		 */
		__u64 obj_offset;

		/** @userptr: 用户虚拟地址，用于 MAP_USERPTR */
		__u64 userptr;
	};

	/**
	 * @range: 绑定到 addr 的对象字节数，UNMAP_ALL 时必须为空（MBZ）
	 */
	__u64 range;

	/** @addr: 要操作的地址，UNMAP_ALL 时必须为空（MBZ） */
	__u64 addr;

	/**
	 * @tile_mask: 用于创建绑定的瓷砖掩码，0 表示所有瓷砖，仅适用于创建新的 VMA
	 */
	__u64 tile_mask;

       /* 将对象（部分）映射到 GPU 虚拟地址范围 */
#define XE_VM_BIND_OP_MAP		0x0
        /* 取消映射 GPU 虚拟地址范围 */
    #define XE_VM_BIND_OP_UNMAP		0x1
        /*
	 * 将 CPU 虚拟地址范围映射到 GPU 虚拟地址范围
	 */
    #define XE_VM_BIND_OP_MAP_USERPTR	0x2
        /* 从 VM 中取消映射 GEM 对象 */
    #define XE_VM_BIND_OP_UNMAP_ALL	0x3
        /*
	 * 如果可能，使某个地址范围的后端内存驻留。注意这不会锁定后端内存
	 */
    #define XE_VM_BIND_OP_PREFETCH	0x4

        /* 使 GPU 映射只读 */
    #define XE_VM_BIND_FLAG_READONLY	(0x1 << 16)
	/*
	 * 仅在故障 VM 上有效，立即执行 MAP 操作而不是将 MAP 推迟到页面错误处理器
	 */
    #define XE_VM_BIND_FLAG_IMMEDIATE	(0x1 << 17)
	/*
	 * 当设置了 NULL 标志时，页表会设置一个特殊位，表示写入被丢弃且所有读取返回零。未来，NULL 标志仅对 XE_VM_BIND_OP_MAP 操作有效，BO 句柄必须为空（MBZ），BO 偏移也必须为空（MBZ）。此标志旨在实现 VK 稀疏绑定
	 */
    #define XE_VM_BIND_FLAG_NULL	(0x1 << 18)
	/** @op: 要执行的操作（低 16 位）和标志（高 16 位） */
	__u32 op;

	/** @mem_region: 预取 VMA 到的内存区域，实例而非掩码 */
	__u32 region;

	/** @reserved: 保留 */
	__u64 reserved[2];
   };

VM_BIND IOCTL 参数本身如下所示。注意，在同步 VM_BIND 中，num_syncs 和 syncs 字段必须为零。这里的 `exec_queue_id` 字段是之前讨论的 VM_BIND 上下文，用于实现乱序 VM_BIND。
.. code-block:: c

    struct drm_xe_vm_bind {
	/** @extensions: 指向第一个扩展结构的指针，如果有的话 */
	__u64 extensions;

	/** @vm_id: 要绑定的 VM 的 ID */
	__u32 vm_id;

	/**
	 * @exec_queue_id: 执行队列 ID，必须属于 DRM_XE_ENGINE_CLASS_VM_BIND 类，并且执行队列必须具有相同的 vm_id。如果为零，则使用默认的 VM 绑定引擎
	 */
	__u32 exec_queue_id;

	/** @num_binds: 此 IOCTL 中的绑定数量 */
	__u32 num_binds;

        /* 如果设置，执行异步 VM_BIND，否则执行同步 VM_BIND */
    #define XE_VM_BIND_IOCTL_FLAG_ASYNC	(0x1 << 0)

	/** @flag: 控制此 IOCTL 中所有操作的标志 */
	__u32 flags;

	union {
		/** @bind: 如果 num_binds == 1 时使用 */
		struct drm_xe_vm_bind_op bind;

		/**
		 * @vector_of_binds: 如果 num_binds > 1 时指向 drm_xe_vm_bind_op 结构数组的用户指针
		 */
		__u64 vector_of_binds;
	};

	/** @num_syncs: 等待完成时要等待或发出信号的同步数量 */
	__u32 num_syncs;

	/** @pad2: 必须为空（MBZ） */
	__u32 pad2;

	/** @syncs: 指向 drm_xe_sync 结构数组的指针 */
	__u64 syncs;

	/** @reserved: 保留 */
	__u64 reserved[2];
    };
