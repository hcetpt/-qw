I915 GuC 提交/DRM 调度器部分
=========================================

上游计划
=============
对于上游，GuC 提交的落地及与 DRM 调度器集成的整体计划如下：

* 合并基本的 GuC 提交
    * 为所有 Gen11 及以上平台提供基本提交支持
    * 默认情况下在任何当前平台上均不启用，但可通过模块参数 `enable_guc` 启用
    * 需要进行大量重构以与 DRM 调度器集成，因此无需对代码中的每一处细节进行挑剔，只要功能完备、无重大编码风格或分层错误，并且不回退 execlists 即可
    * 根据需要更新 IGT（Intel Graphics Test）/ 自测以适应 GuC 提交
    * 在支持的平台上启用 CI（持续集成）以建立基线
    * 按需重构/确保 CI 健康以支持 GuC 提交
* 合并新的并行提交用户空间 API（uAPI）
    * 现有的绑定 uAPI 完全不兼容 GuC 提交，此外其设计存在严重问题，这是我们无论如何都要弃用它的原因
    * 新的 uAPI 添加了 `I915_CONTEXT_ENGINES_EXT_PARALLEL` 上下文设置步骤，用于配置包含 N 个上下文的槽位
    * 在 `I915_CONTEXT_ENGINES_EXT_PARALLEL` 之后，用户可以在单个 execbuf IOCTL 中向一个槽位提交 N 个批次，并且这些批次在 GPU 上并行运行
    * 最初仅适用于 GuC 提交，如果需要也可以支持 execlists
* 将 i915 转换为使用 DRM 调度器
    * GuC 提交后端完全集成到 DRM 调度器中
        * 移除所有请求队列（例如，所有背压处理都由 DRM 调度器完成）
        * 重置/取消钩子在 DRM 调度器中实现
        * 看门狗钩子进入 DRM 调度器
        * 一旦与 DRM 调度器集成，GuC 后端的大量复杂性可以被简化（例如状态机变得更简单，锁定变得更简单等……）
    * execlists 后端将尽可能地挂钩到 DRM 调度器
        * 传统接口
        * 如时间分片/抢占/虚拟引擎等功能难以与 DRM 调度器集成，而这些功能对于 GuC 提交不是必需的，因为 GuC 已经为我们处理了这些问题
        * 完整集成的回报率低
        * 完整集成将增加 DRM 调度器的复杂性
    * 在 DRM 调度器中移植 i915 的优先级继承/提升功能
        * 用于 i915 页面翻转，可能对其他 DRM 驱动程序也有用
        * 将成为 DRM 调度器中的可选功能
    * 从 DRM 调度器中移除顺序完成假设
        * 即使使用 DRM 调度器，后端也会处理抢占、时间分片等，因此作业有可能乱序完成
    * 移除 i915 优先级级别并使用 DRM 优先级级别
    * 按需优化 DRM 调度器

GuC 提交上游待办事项
======================
* 需要更新 GuC 固件/i915 以启用错误状态捕获
* 开源工具来解码 GuC 日志
* 公开 GuC 规范

基本 GuC 提交的新 uAPI
====================
基本 GuC 提交所需的 uAPI 无重大更改。唯一的更改是一个新的调度属性：`I915_SCHEDULER_CAP_STATIC_PRIORITY_MAP`
此属性表示 2K i915 用户优先级级别静态映射为以下三个级别：

* -1K 到 -1：低优先级
* 0：中优先级
* 1 到 1K：高优先级

这是因为 GuC 只有四个优先级带宽。最高优先级带宽由内核保留。这也与 DRM 调度器优先级级别一致。
规范参考：
----------------
* https://www.khronos.org/registry/EGL/extensions/IMG/EGL_IMG_context_priority.txt
* https://www.khronos.org/registry/vulkan/specs/1.2-extensions/html/chap5.html#devsandqueues-priority
* https://spec.oneapi.com/level-zero/latest/core/api.html#ze-command-queue-priority-t

新的并行提交 uAPI
=================
现有的绑定 uAPI 在 GuC 提交时是完全断裂的，因为在通过 `I915_SUBMIT_FENCE` 激活的 execbuf 时间之前，无法确定提交是一个单一上下文提交还是并行提交。为了使用 GuC 并行提交多个上下文，必须显式地注册 N 个上下文，并且所有 N 个上下文必须在一个命令中提交给 GuC。GuC 接口不支持像绑定 uAPI 那样动态切换 N 个上下文。因此需要一个新的并行提交接口。此外，传统的绑定 uAPI 相当混乱且不直观。而且 `I915_SUBMIT_FENCE` 本质上是一个未来的围栏，所以我们不应该继续支持它。
新的并行提交 uAPI 包括三个部分：

* 导出引擎逻辑映射
* 一个 'set_parallel' 扩展以配置上下文进行并行提交
* 扩展 execbuf2 IOCTL 以支持在单个 IOCTL 中提交 N 个 BB

导出引擎逻辑映射
------------------
某些用例要求 BB 按照逻辑顺序放置在引擎实例上（例如 Gen11+ 的拆帧）。根据融合情况，引擎实例的逻辑映射可能会改变。为了避免让 UMD（用户模式驱动）意识到融合，只需通过现有的查询引擎信息 IOCTL 暴露逻辑映射即可。另外，GuC 提交接口目前只支持按逻辑顺序向引擎提交多个上下文，这是与 execlists 相比的一个新需求。
最后，所有当前平台最多只有两个引擎实例，并且逻辑顺序与 uAPI 顺序相同。这将在具有超过两个引擎实例的平台上发生变化。
将在 `drm_i915_engine_info.flags` 中添加一个标志位，表示逻辑实例已被返回，并且新字段 `drm_i915_engine_info.logical_instance` 返回逻辑实例。

一个 'set_parallel' 扩展以配置上下文进行并行提交
------------------------------------------------------------------------
'`set_parallel`' 扩展用于配置槽位进行 N 个 BB 的并行提交。
这是一个设置步骤，必须在使用任何上下文之前调用。参见类似的现有示例 `I915_CONTEXT_ENGINES_EXT_LOAD_BALANCE` 或 `I915_CONTEXT_ENGINES_EXT_BOND`。
一旦槽位配置为并行提交，就可以通过调用 execbuf2 IOCTL 提交 N 个 BB。最初仅支持 GuC 提交，如果需要，可以稍后添加对 execlists 的支持。
向 uAPI 添加 `I915_CONTEXT_ENGINES_EXT_PARALLEL_SUBMIT` 和 `drm_i915_context_engines_parallel_submit` 以实现此扩展。
扩展 execbuf2 IOCTL 以支持在单个 IOCTL 中提交 N 个 BB
-----------------------------------------------------------
使用 'set_parallel' 扩展配置的上下文只能在单个 execbuf2 IOCTL 中提交 N 个 BB。这些 BB 要么是 drm_i915_gem_exec_object2 列表中的最后 N 个对象，要么是如果设置了 I915_EXEC_BATCH_FIRST，则是列表中的前 N 个对象。BB 的数量是根据提交的槽位及其由 'set_parallel' 或其他扩展配置的方式隐式确定的。execbuf2 IOCTL 不需要对用户 API 进行任何更改。
