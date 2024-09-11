I915 小 BAR RFC 节
==========================

从 DG2 开始，我们将支持设备本地内存（即 I915_MEMORY_CLASS_DEVICE）的可调整大小 BAR。但在某些情况下，最终的 BAR 大小可能仍然小于总探测大小。在这些情况下，只有部分 I915_MEMORY_CLASS_DEVICE 可以通过 CPU 访问（例如前 256MB），其余部分仅能通过 GPU 访问。
I915_GEM_CREATE_EXT_FLAG_NEEDS_CPU_ACCESS 标志
----------------------------------------------

新增的 gem_create_ext 标志告诉内核一个 BO 需要 CPU 访问。

当对象放置在 I915_MEMORY_CLASS_DEVICE 中时，这一点变得尤为重要，因为设备底层有一个小 BAR，这意味着只有其中的一部分可以通过 CPU 访问。如果没有这个标志，内核将假定不需要 CPU 访问，并优先使用 I915_MEMORY_CLASS_DEVICE 的非 CPU 可见部分。
.. kernel-doc:: Documentation/gpu/rfc/i915_small_bar.h
   :functions: __drm_i915_gem_create_ext

probed_cpu_visible_size 属性
-----------------------------

新的 struct __drm_i915_memory_region 属性返回特定区域的 CPU 可访问部分的总大小。这仅适用于 I915_MEMORY_CLASS_DEVICE。我们还报告了未分配的 CPU 可见大小以及未分配大小。

Vulkan 需要此信息来创建一个带有 VK_MEMORY_PROPERTY_HOST_VISIBLE_BIT 标志的单独 VkMemoryHeap，以表示 CPU 可见部分，堆的总大小需要被知晓。它还需要能够粗略估计内存可以如何潜在地分配。
.. kernel-doc:: Documentation/gpu/rfc/i915_small_bar.h
   :functions: __drm_i915_memory_region_info

错误捕获限制
--------------------------

在错误捕获方面，我们有两个新的限制：

1. 在小 BAR 系统上，错误捕获是尽力而为的；如果在捕获时刻页面不可通过 CPU 访问，则内核可以跳过尝试捕获它们。

2. 在独立和较新的集成平台上，我们现在拒绝在可恢复上下文中进行错误捕获。未来内核可能希望在某些内容当前不可通过 CPU 访问时，在错误捕获期间进行复制操作。
