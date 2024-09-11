/* SPDX-License-Identifier: MIT */

/*
 * 版权所有 © 2022 英特尔公司
 */

/**
 * DOC: I915_PARAM_VM_BIND_VERSION
 *
 * 支持的 VM_BIND 特性版本
 * 参见 typedef drm_i915_getparam_t param
 *
 * 指定支持的 VM_BIND 特性版本
 * 已定义了以下版本的 VM_BIND：
 *
 * 0：不支持 VM_BIND
 *
 * 1：在 VM_UNBIND 调用中，用户模式驱动程序（UMD）必须指定之前使用 VM_BIND 创建的确切映射，
 *    ioctl 不支持解除多个映射或拆分映射。类似地，VM_BIND 调用不会替换任何现有的映射
 *
 * 2：解除部分或多个映射的限制被取消，类似地，在给定范围内绑定将替换任何映射
 *
 * 参见 struct drm_i915_gem_vm_bind 和 struct drm_i915_gem_vm_unbind
 */
#define I915_PARAM_VM_BIND_VERSION 57

/**
 * DOC: I915_VM_CREATE_FLAGS_USE_VM_BIND
 *
 * 在创建 VM 时选择使用 VM_BIND 模式的标志
 * 参见 struct drm_i915_gem_vm_control flags
 *
 * 较旧的 execbuf2 ioctl 不支持 VM_BIND 操作模式
 */
* 对于 VM_BIND 模式，我们引入了一个新的 execbuf3 ioctl，该 ioctl 不接受任何 execlist（详见结构体 drm_i915_gem_execbuffer3）

```c
#define I915_VM_CREATE_FLAGS_USE_VM_BIND	(1 << 0)

/* 与 VM_BIND 相关的 ioctl 定义 */
#define DRM_I915_GEM_VM_BIND		0x3d
#define DRM_I915_GEM_VM_UNBIND		0x3e
#define DRM_I915_GEM_EXECBUFFER3	0x3f

#define DRM_IOCTL_I915_GEM_VM_BIND		DRM_IOWR(DRM_COMMAND_BASE + DRM_I915_GEM_VM_BIND, struct drm_i915_gem_vm_bind)
#define DRM_IOCTL_I915_GEM_VM_UNBIND		DRM_IOWR(DRM_COMMAND_BASE + DRM_I915_GEM_VM_UNBIND, struct drm_i915_gem_vm_bind)
#define DRM_IOCTL_I915_GEM_EXECBUFFER3		DRM_IOWR(DRM_COMMAND_BASE + DRM_I915_GEM_EXECBUFFER3, struct drm_i915_gem_execbuffer3)

/**
 * struct drm_i915_gem_timeline_fence - 时间线围栏输入或输出结构
 *
 * 操作将等待输入围栏信号
 *
 * 返回的输出围栏将在操作完成后被标记
 */
struct drm_i915_gem_timeline_fence {
	/** @handle: 用户用于等待或标记的 drm_syncobj 句柄。 */
	__u32 handle;

	/**
	 * @flags: 支持的标志包括：
	 *
	 * I915_TIMELINE_FENCE_WAIT:
	 * 在操作前等待输入围栏
	 *
	 * I915_TIMELINE_FENCE_SIGNAL:
	 * 将操作完成的围栏作为输出返回
	 */
	__u32 flags;
#define I915_TIMELINE_FENCE_WAIT            (1 << 0)
#define I915_TIMELINE_FENCE_SIGNAL          (1 << 1)
#define __I915_TIMELINE_FENCE_UNKNOWN_FLAGS (-(I915_TIMELINE_FENCE_SIGNAL << 1))

	/**
	 * @value: 时间线上的一个点
	 * 对于二进制 drm_syncobj，值必须为 0。对于时间线 drm_syncobj，值为 0 是无效的，因为它会将 drm_syncobj 转换为二进制形式。
	 */
	__u64 value;
};

/**
 * struct drm_i915_gem_vm_bind - 用于绑定的 VA 到对象映射
 *
 * 此结构体传递给 VM_BIND ioctl，并指定 GPU 虚拟地址（VA）范围到应绑定在指定地址空间（VM）设备页表中的对象部分。
 */
```
```c
/* 指定的VA范围必须是唯一的（即，未绑定的），并且可以映射到整个对象或对象的一部分（部分绑定）
 * 可以为同一对象部分创建多个VA映射（别名）
 * 
 * @start、@offset 和 @length 必须以4K页对齐。然而，DG2 对设备本地内存使用64K页大小并具有紧凑页表。在该平台上，对于绑定设备本地内存对象，@start、@offset 和 @length 必须以64K对齐。此外，UMD 不应在相同的2M范围内混合使用本地内存的64K页和系统内存的4K页绑定
 * 
 * 如果 @start、@offset 和 @length 没有正确对齐，则返回错误代码 -EINVAL。在版本1中（参见 I915_PARAM_VM_BIND_VERSION），如果指定的VA范围无法预留，则返回错误代码 -ENOSPC
 * 
 * 在不同CPU线程上并发执行的 VM_BIND/UNBIND ioctl 调用是没有顺序的。此外，如果指定了有效的 @fence，则 VM_BIND 操作的部分可以异步完成
 */

struct drm_i915_gem_vm_bind {
	/** @vm_id: 绑定的VM（地址空间）ID */
	__u32 vm_id;

	/** @handle: 对象句柄 */
	__u32 handle;

	/** @start: 绑定的虚拟地址起始位置 */
	__u64 start;

	/** @offset: 对象中的偏移量 */
	__u64 offset;

	/** @length: 映射长度 */
	__u64 length;

	/**
	 * @flags: 支持的标志包括：
	 *
	 * I915_GEM_VM_BIND_CAPTURE:
	 * 在GPU错误时捕获此映射
	 *
	 * 注意：@fence 携带其自身的标志
	 */
	__u64 flags;
#define I915_GEM_VM_BIND_CAPTURE	(1 << 0)

	/**
	 * @fence: 绑定完成信号的时间线围栏
	 *
	 * 时间线围栏的格式为 struct drm_i915_gem_timeline_fence
	 *
	 * 它是一个输出围栏，因此使用 I915_TIMELINE_FENCE_WAIT 标志是无效的，并将返回错误
	 */
};
```
```c
/*
 * 如果未设置 I915_TIMELINE_FENCE_SIGNAL 标志，则外部围栏（fence）未被请求，绑定操作将同步完成
 */
struct drm_i915_gem_timeline_fence fence;

/**
 * @extensions: 扩展链表，以零结尾
 *
 * 用于未来的扩展。参见 struct i915_user_extension
 */
__u64 extensions;

/**
 * struct drm_i915_gem_vm_unbind - 用于解除绑定的 VA 到对象映射
 *
 * 此结构体传递给 VM_UNBIND ioctl，指定要从指定地址空间（VM）的设备页表中解除绑定的 GPU 虚拟地址（VA）范围。
 * VM_UNBIND 将强制从设备页表中解除指定范围的绑定，无需等待任何 GPU 任务完成。
 * 在调用 VM_UNBIND 之前，UMD（用户模式驱动）需要确保该映射不再被使用。
 *
 * 如果未找到指定的映射，ioctl 将简单地返回而不报错。
 *
 * 在不同 CPU 线程上并发执行的 VM_BIND/UNBIND ioctl 调用是无序的。此外，如果指定了有效的 @fence，则 VM_UNBIND 操作的部分可以异步完成。
 */
struct drm_i915_gem_vm_unbind {
    /** @vm_id: 要解除绑定的 VM（地址空间）ID */
    __u32 vm_id;

    /** @rsvd: 预留，MBZ（必须为零） */
    __u32 rsvd;

    /** @start: 要解除绑定的虚拟地址起始位置 */
    __u64 start;

    /** @length: 要解除绑定的映射长度 */
    __u64 length;

    /**
     * @flags: 目前预留，MBZ（必须为零）
     *
     * 注意：@fence 有自己的标志位
     */
};
```
```c
__u64 flags;

/**
 * @fence: 用于解绑完成信号的时间线围栏
 *
 * 时间线围栏的格式为 struct drm_i915_gem_timeline_fence
 *
 * 这是一个输出围栏，因此使用 I915_TIMELINE_FENCE_WAIT 标志是无效的，并且会返回错误
 *
 * 如果未设置 I915_TIMELINE_FENCE_SIGNAL 标志，则不请求输出围栏，并且解绑操作同步完成
 */
struct drm_i915_gem_timeline_fence fence;

/**
 * @extensions: 扩展链表（以零结尾）
 *
 * 用于未来的扩展。参见 struct i915_user_extension
 */
__u64 extensions;
};

/**
 * struct drm_i915_gem_execbuffer3 - DRM_I915_GEM_EXECBUFFER3 ioctl 结构体
 *
 * DRM_I915_GEM_EXECBUFFER3 ioctl 只在 VM_BIND 模式下工作，而 VM_BIND 模式仅通过此 ioctl 进行提交
 * 参见 I915_VM_CREATE_FLAGS_USE_VM_BIND
 */
struct drm_i915_gem_execbuffer3 {
    /**
     * @ctx_id: 上下文 ID
     *
     * 只允许具有用户引擎映射的上下文
     */
};
```
以下是给定代码段的中文翻译：

```c
__u32 ctx_id;

/**
 * @engine_idx: 引擎索引
 *
 * 这是通过 @ctx_id 指定的上下文中的用户引擎映射的索引
*/
__u32 engine_idx;

/**
 * @batch_address: 批处理 GPU 虚拟地址
 *
 * 对于普通提交，这是批处理缓冲区的 GPU 虚拟地址。对于并行提交，它是指向一个批处理缓冲区 GPU 虚拟地址数组的指针，数组大小等于参与该提交的（并行）引擎数量（参见结构体 i915_context_engines_parallel_submit）
*/
__u64 batch_address;

/** @flags: 当前保留，MBZ */
__u64 flags;

/** @rsvd1: 保留，MBZ */
__u32 rsvd1;

/** @fence_count: @timeline_fences 数组中的围栏数量 */
__u32 fence_count;

/**
 * @timeline_fences: 指向时间线围栏数组的指针
 *
 * 时间线围栏的格式为 struct drm_i915_gem_timeline_fence
*/
__u64 timeline_fences;

/** @rsvd2: 保留，MBZ */
__u64 rsvd2;

/**
 * @extensions: 零终止的扩展链表
 *
 * 用于未来的扩展。参见结构体 i915_user_extension
*/
__u64 extensions;
};

/**
 * struct drm_i915_gem_create_ext_vm_private - 将对象设置为特定 VM 的私有扩展
 *
 * 参见 struct drm_i915_gem_create_ext
*/
struct drm_i915_gem_create_ext_vm_private {
#define I915_GEM_CREATE_EXT_VM_PRIVATE         2
    /** @base: 扩展链接。参见 struct i915_user_extension */
    struct i915_user_extension base;

    /** @vm_id: 对象私有的 VM 的 ID */
    __u32 vm_id;
};
```

希望这对你有所帮助！如果你有任何其他问题，请随时告诉我。
