```c
/**
 * 结构 __drm_i915_memory_region_info - 描述一个由驱动程序已知的内存区域
 *
 * 注意：这里同时使用了结构体 drm_i915_query_item 和 drm_i915_query
 * 对于这个新的查询，我们在 &drm_i915_query_item.query_id 中添加了新的查询 ID DRM_I915_QUERY_MEMORY_REGIONS
 */
struct __drm_i915_memory_region_info {
    /** @region: 类型:实例对编码 */
    struct drm_i915_gem_memory_class_instance region;

    /** @rsvd0: 必须为零（MBZ） */
    __u32 rsvd0;

    /**
     * @probed_size: 驱动程序探测到的内存大小
     *
     * 注意：这里永远不应该遇到零值，另外，当前没有哪种区域类型会返回 -1。
     * 虽然对于未来的区域类型，这可能是可能的。其他大小字段也适用同样的规则。
     */
    __u64 probed_size;

    /**
     * @unallocated_size: 剩余内存估计值
     *
     * 需要 CAP_PERFMON 或 CAP_SYS_ADMIN 权限才能获得可靠的统计信息。
     * 没有这些权限（或内核版本较旧时），这里的值将始终等于 @probed_size。
     * 注意：目前仅跟踪 I915_MEMORY_CLASS_DEVICE 区域（对于其他类型，这里的值将始终等于 @probed_size）。
     */
    __u64 unallocated_size;

    union {
        /** @rsvd1: 必须为零（MBZ） */
        __u64 rsvd1[8];

        struct {
            /**
             * @probed_cpu_visible_size: 驱动程序探测到的 CPU 可访问内存大小
             *
             * 这个值将始终 <= @probed_size，并且剩余部分（如果有）将不是 CPU 可访问的。
             *
             * 在没有小 BAR 的系统上，@probed_size 将始终等于 @probed_cpu_visible_size，
             * 因为所有这部分内存都是 CPU 可访问的。
             */
            __u64 probed_cpu_visible_size;
        };
    };
};
```
```c
/*
 * 请注意，这仅针对 I915_MEMORY_CLASS_DEVICE 区域进行跟踪（对于其他类型，该值始终等于 @probed_size）
 *
 * 如果返回的值为零，则表示这是旧内核，缺少相关的 small-bar uAPI 支持（包括 I915_GEM_CREATE_EXT_FLAG_NEEDS_CPU_ACCESS），但在这种系统上我们实际上不应该遇到 small BAR 配置，假设我们可以加载内核模块。因此，可以安全地将其视为与 @probed_cpu_visible_size 等于 @probed_size 的情况相同。
 */
__u64 probed_cpu_visible_size;

/**
 * @unallocated_cpu_visible_size: 剩余的 CPU 可见内存估计值
 *
 * 请注意，这仅针对 I915_MEMORY_CLASS_DEVICE 区域进行跟踪（对于其他类型，该值始终等于 @probed_cpu_visible_size）
 *
 * 需要 CAP_PERFMON 或 CAP_SYS_ADMIN 权限才能获得可靠的统计信息。如果没有这些权限，该值将始终等于 @probed_cpu_visible_size。请注意，目前这仅针对 I915_MEMORY_CLASS_DEVICE 区域进行跟踪（对于其他类型，该值也将始终等于 @probed_cpu_visible_size）
 *
 * 如果是旧内核，该值将为零，请参阅 @probed_cpu_visible_size
 */
__u64 unallocated_cpu_visible_size;
};

/**
 * struct __drm_i915_gem_create_ext - 现有的 gem_create 行为，增加了使用 struct i915_user_extension 的扩展支持
 *
 * 新的缓冲区标志应在此处添加，至少对于那些不可变的部分。以前我们会有两个 ioctl，一个用于用 gem_create 创建对象，另一个用于应用各种参数，但这对于被认为是不可变的参数造成了一些歧义。另外，我们正在逐步淘汰各种 SET/GET ioctl
 */
struct __drm_i915_gem_create_ext {
	/**
	 * @size: 对象请求的大小
	 *
	 * 对象分配的实际大小（页面对齐）将被返回
	 *
	 * 请注意，对于某些设备，我们可能有进一步的最小页面大小限制（大于 4K），例如对于设备本地内存
	 */
	__u64 size;
};
```
这段代码解释了 `__drm_i915_gem_create_ext` 结构体及其成员变量的含义和用法。
```c
/* 但是通常情况下，最终大小应该始终反映任何向上取整的情况，
 * 比如使用 I915_GEM_CREATE_EXT_MEMORY_REGIONS 扩展将对象放置在设备本地内存中。
 * 内核将始终选择所有可能放置位置中的最大最小页面大小作为向上取整 @size 的值。
 */
__u64 size;

/**
 * @handle: 返回的对象句柄
 *
 * 对象句柄是非零的
 */
__u32 handle;

/**
 * @flags: 可选标志
 *
 * 支持的值：
 *
 * I915_GEM_CREATE_EXT_FLAG_NEEDS_CPU_ACCESS - 通知内核该对象需要通过 CPU 访问
 *
 * 仅在将对象放置在 I915_MEMORY_CLASS_DEVICE 中时有效，并且仅在某些设备内存可以通过 CPU 直接访问（我们称之为小 BAR）的配置下严格要求，例如一些 DG2+ 系统。请注意，这是非常不理想的，但由于客户端 CPU、BIOS 等各种因素，我们在实际环境中可能会看到这种情况。参见 &__drm_i915_memory_region_info.probed_cpu_visible_size 来确定此系统是否适用。
 *
 * 注意，必须有一个放置位置是 I915_MEMORY_CLASS_SYSTEM，以确保内核可以将分配回退到系统内存，如果对象不能分配在可映射部分的 I915_MEMORY_CLASS_DEVICE 中。
 *
 * 此外，请注意，由于内核只支持只能放置在 I915_MEMORY_CLASS_DEVICE 中的对象的扁平 CCS，因此我们不支持 I915_GEM_CREATE_EXT_FLAG_NEEDS_CPU_ACCESS 与扁平 CCS 一起使用。
 *
 * 如果没有这个提示，内核会假设非可映射的 I915_MEMORY_CLASS_DEVICE 是首选的。请注意，内核仍然可以在最后尝试将对象迁移到可映射部分，如果用户空间曾经对这个对象进行 CPU 错误处理，但这可能是昂贵的，因此最好避免这种情况。
 *
 * 在较旧的内核中，缺少相关的小 BAR uAPI 支持（参见 &__drm_i915_memory_region_info.probed_cpu_visible_size），使用此标志会导致错误，但只要我们可以成功加载 i915 内核模块，则不可能出现小 BAR 配置。在这种情况下，整个 I915_MEMORY_CLASS_DEVICE 区域都可通过 CPU 访问，因此对象可以放置的位置没有任何限制。
 */
```
```c
#define I915_GEM_CREATE_EXT_FLAG_NEEDS_CPU_ACCESS (1 << 0)
__u32 flags;

/**
 * @extensions: 应用于该对象的扩展链
 *
 * 当我们需要支持多个不同的扩展，并且在创建对象时需要应用多个扩展时，这将在未来变得有用。参见 struct i915_user_extension。
 *
 * 如果我们不提供任何扩展，则会得到与旧的 gem_create 相同的行为。
 *
 * 对于 I915_GEM_CREATE_EXT_MEMORY_REGIONS 的使用，请参见 struct drm_i915_gem_create_ext_memory_regions。
 *
 * 对于 I915_GEM_CREATE_EXT_PROTECTED_CONTENT 的使用，请参见 struct drm_i915_gem_create_ext_protected_content。
 */
#define I915_GEM_CREATE_EXT_MEMORY_REGIONS 0
#define I915_GEM_CREATE_EXT_PROTECTED_CONTENT 1
__u64 extensions;
```

这是你提供的代码段的中文翻译。希望对你有帮助！如果还有其他问题，请随时告诉我。
