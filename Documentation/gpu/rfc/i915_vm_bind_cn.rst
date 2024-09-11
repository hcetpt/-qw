==========================================
I915 VM_BIND 特性设计与使用案例
==========================================

VM_BIND 特性
================
DRM_I915_GEM_VM_BIND/UNBIND ioctl 调用允许用户模式驱动（UMD）在指定的地址空间（VM）上，以指定的 GPU 虚拟地址绑定或解绑 GEM 缓冲对象（BOs）或 BO 的部分区域。这些映射（也称为持久映射）将在多个 GPU 提交（execbuf 调用）中保持有效，而无需用户在每次提交时提供所有所需的映射列表（这是旧版 execbuf 模式所要求的）。VM_BIND/UNBIND 调用允许 UMD 请求一个时间线围栏（timeline out fence），用于指示绑定/解绑操作的完成。

VM_BIND 特性通过 I915_PARAM_VM_BIND_VERSION 向用户宣传。用户需要在创建地址空间（VM）时通过 I915_VM_CREATE_FLAGS_USE_VM_BIND 扩展选择启用 VM_BIND 模式的绑定。

在不同的 CPU 线程上并发执行的 VM_BIND/UNBIND ioctl 调用是无序的。此外，当指定了有效的输出围栏时，VM_BIND/UNBIND 操作的部分可以异步完成。

VM_BIND 特性包括：

* 多个虚拟地址（VA）映射可以指向同一物理页面的对象（别名）
* VA 映射可以指向 BO 的部分区域（部分绑定）
* 支持在 GPU 错误时捕获持久映射
* 支持 userptr GEM 对象（无需特殊 uapi）

TLB 刷新考虑
------------------------
i915 驱动程序会在每次提交和释放对象页面时刷新 TLB。VM_BIND/UNBIND 操作不会进行任何额外的 TLB 刷新。任何 VM_BIND 添加的映射都将在后续提交中的工作集中生效，并且不会在当前运行批次的工作集中生效（这将需要额外的 TLB 刷新，但不支持）。
### 执行缓冲 ioctl 在 VM_BIND 模式下

在 VM_BIND 模式下的 VM 不支持旧的 execbuf 模式的绑定。
VM_BIND 模式下的 execbuf ioctl 处理与旧的 execbuf2 ioctl（参见 `struct drm_i915_gem_execbuffer2`）有显著不同。
因此，添加了一个新的 execbuf3 ioctl 以支持 VM_BIND 模式。（参见 `struct drm_i915_gem_execbuffer3`）。execbuf3 ioctl 不接受任何 execlist。因此，不支持隐式同步。预计以下工作将能够支持所有用例中的对象依赖设置：

“dma-buf：添加一个用于导出同步文件的 API”
(https://lwn.net/Articles/859290/)

新的 execbuf3 ioctl 只在 VM_BIND 模式下工作，并且 VM_BIND 模式只使用 execbuf3 ioctl 进行提交。所有通过 VM_BIND 调用映射到该 VM 的 BO 在 execbuf3 调用时被认为是该提交所必需的。
execbuf3 ioctl 直接指定批处理地址，而不是像 execbuf2 ioctl 那样使用对象句柄。execbuf3 ioctl 也不支持许多旧的功能，如 in/out/submit fences、fence 数组、默认的 gem 上下文等（参见 `struct drm_i915_gem_execbuffer3`）。
在 VM_BIND 模式下，VA 分配完全由用户管理，而不是由 i915 驱动程序管理。因此，在 VM_BIND 模式下，所有的 VA 分配、驱逐都不适用。此外，对于确定对象的有效性，VM_BIND 模式不会使用 i915_vma 的 active reference tracking。它将使用 dma-resv 对象来实现这一点（参见 `VM_BIND dma_resv 使用`）。
因此，许多现有的支持 execbuf2 ioctl 的代码，如重定位、VA 驱逐、VMA 查找表、隐式同步、VMA active reference tracking 等，都不适用于 execbuf3 ioctl。因此，所有 execbuf3 特定的处理应放在单独的文件中，并且只有这些 ioctl 共享的功能可以在可能的情况下共享。

### VM_PRIVATE 对象

默认情况下，BO 可以映射到多个 VM 并可以被 dma-buf 导出。因此这些 BO 称为共享 BO。
在每次 execbuf 提交时，请求的 fence 必须添加到所有映射到 VM 的共享 BO 的 dma-resv fence 列表中。
VM_BIND 功能引入了一种优化，用户可以通过在创建 BO 时使用 I915_GEM_CREATE_EXT_VM_PRIVATE 标志创建仅属于特定 VM 的私有 BO。与共享 BO 不同，这些 VM 私有 BO 只能映射到它们所属的 VM，并且不能被 dma-buf 导出。
所有 VM 的私有 BO 共享同一个 dma-resv 对象。因此，在每次 execbuf 提交时，只需要更新一个 dma-resv fence 列表。因此，在所需映射已经绑定的情况下（快速路径），提交延迟与 VM 私有 BO 的数量呈 O(1) 关系。
VM_BIND 锁定层次结构
-------------------------
这里的锁定设计支持旧的（基于 execlist）execbuf 模式、新的 VM_BIND 模式、带 GPU 页面错误的 VM_BIND 模式以及可能的未来系统分配器支持（参见“共享虚拟内存 (SVM) 支持”）。
旧的 execbuf 模式和不带页面错误的新 VM_BIND 模式使用 dma_fence 管理后端存储的驻留。带页面错误的 VM_BIND 模式和系统分配器支持则完全不使用任何 dma_fence。
VM_BIND 的锁定顺序如下：
1) Lock-A：一个 vm_bind 互斥锁保护 vm_bind 列表。此锁在 vm_bind/vm_unbind ioctl 调用中、在 execbuf 路径中以及释放映射时获取。
将来，当支持 GPU 页面错误时，我们可以潜在地使用读写信号量（rwsem），以便多个页面错误处理器可以获取读取侧锁来查找映射，并因此可以并行运行。
旧的 execbuf 绑定模式不需要这个锁。
2) Lock-B：对象的 dma-resv 锁保护 i915_vma 状态，在异步工作线程中绑定/解绑 vma 以及更新对象的 dma-resv 围栏列表时需要持有该锁。请注意，一个 VM 的私有 BO 将共享一个 dma-resv 对象。
未来的系统分配器支持将使用 HMM 规定的锁定机制。
3) Lock-C：自旋锁或保护 VM 的某些列表，如因驱逐和用户指针无效导致的无效 vma 列表等。
当支持 GPU 页面错误时，execbuf 路径不会获取这些锁。在这种情况下，我们只需将新的批处理缓冲区地址写入环形缓冲区，然后通知调度器运行它。锁的获取仅发生在页面错误处理器中，在这里我们需要以读取模式获取 lock-A，根据需要找到后端存储（对于 gem 对象为 dma_resv 锁，对于系统分配器为 hmm/core mm），以及一些额外的锁（lock-D）来处理页表竞争。页面错误模式不应需要修改 VM 列表，因此不需要 lock-C。
### VM_BIND LRU 处理
---------------------
我们需要确保 VM_BIND 映射的对象正确地打上 LRU 标签，以避免性能下降。我们还需要支持批量移动 VM_BIND 对象的 LRU 机制，以避免在 execbuf 路径中增加额外的延迟。
页表页与 VM_BIND 映射的对象类似（见“可驱逐的页表分配”），并且每个 VM 都维护这些页表页。当 VM 变为活动状态时（即，在带有该 VM 的 execbuf 调用时），需要将它们固定在内存中。因此，批量移动页表页的 LRU 机制也是必需的。

### VM_BIND dma_resv 使用
-----------------------
所有 VM_BIND 映射的对象都需要添加围栏。每次提交 execbuf 时，都会使用 DMA_RESV_USAGE_BOOKKEEP 用途来防止过度同步（见枚举 dma_resv_usage）。在显式设置对象依赖关系时，可以覆盖为 DMA_RESV_USAGE_READ 或 DMA_RESV_USAGE_WRITE 用途。
请注意，DRM_I915_GEM_WAIT 和 DRM_I915_GEM_BUSY ioctl 不会检查 DMA_RESV_USAGE_BOOKKEEP 用途，因此不应用于批处理结束检查。相反，应使用 execbuf3 输出围栏进行批处理结束检查（见结构体 drm_i915_gem_execbuffer3）。
此外，在 VM_BIND 模式下，使用 dma-resv API 来确定对象是否活跃（见 dma_resv_test_signaled() 和 dma_resv_wait_timeout()），不要使用已弃用的 i915_vma 活跃引用跟踪。这应该更容易与当前的 TTM 后端配合工作。

### Mesa 用例
--------------
VM_BIND 有可能减少 Mesa（包括 Vulkan 和 Iris）中的 CPU 开销，从而提高 CPU 限制型应用的性能。它还允许我们实现 Vulkan 的稀疏资源。随着 GPU 硬件性能的提升，减少 CPU 开销变得更加重要。

### 其他 VM_BIND 用例
========================

#### 长时间运行的计算上下文
------------------------------
dma-fence 的使用期望它们在合理的时间内完成。然而，计算任务可能会长时间运行。因此，对于计算任务来说，使用用户/内存围栏是合适的（见“用户/内存围栏”），而 dma-fence 的使用应仅限于内核内部消费。
在没有 GPU 页错误的情况下，当缓冲区无效化时，内核驱动程序将启动长时间运行上下文的挂起（抢占），完成无效化，重新验证 BO，然后恢复计算上下文。这是通过每个上下文的抢占围栏实现的，当有人试图等待这个围栏时，会触发上下文的抢占。

#### 用户/内存围栏
~~~~~~~~~~~~~~~~~~
用户/内存围栏是一个 `<地址, 值>` 对。要信号化用户围栏，将在指定虚拟地址处写入指定值，并唤醒等待进程。用户围栏可以通过 GPU 或内核异步工作者（如绑定完成后）信号化。用户可以通过新的用户围栏等待 ioctl 等待用户围栏。
以下是一些相关工作的链接：
https://patchwork.freedesktop.org/patch/349417/

低延迟提交
~~~~~~~~~~~~
允许计算用户模式驱动（UMD）直接提交GPU任务，而不是通过execbuf ioctl。这是通过VM_BIND不与execbuf同步实现的。VM_BIND允许直接提交任务所需的映射绑定和解除绑定。

调试器
--------
通过调试事件接口，用户空间进程（调试器）能够跟踪并处理由另一个进程（被调试进程）创建并通过vm_bind接口附加到GPU上的资源。

GPU页面错误
--------------
当支持GPU页面错误时（未来），将仅在VM_BIND模式下支持。虽然旧的execbuf模式和新的VM_BIND绑定模式都需要使用dma-fence来确保驻留性，但当支持GPU页面错误模式时，不会使用任何dma-fence，因为驻留性完全通过安装和移除/失效页面表项来管理。

页面级别的提示设置
---------------------
VM_BIND允许每个映射设置任意提示信息，而不是针对每个BO。可能的提示信息包括放置位置和原子性。随着即将推出的GPU按需页面错误支持，子BO级别的放置提示将更加相关。

页面级别的缓存/CLOS设置
-------------------------
VM_BIND允许每个映射设置缓存/CLOS设置，而不是针对每个BO。

可驱逐的页面表分配
----------------------
使页面表分配可驱逐，并像管理VM_BIND映射对象一样管理它们。页面表页类似于VM中的持久映射（不同之处在于页面表页没有i915_vma结构，并且在交换回页面后需要更新父页面链接）。

共享虚拟内存（SVM）支持
-------------------------
可以使用HMM接口通过VM_BIND接口直接映射系统内存（无需gem BO抽象）。SVM仅在启用GPU页面错误时支持。

VM_BIND 用户API
=================

.. kernel-doc:: Documentation/gpu/rfc/i915_vm_bind.h
