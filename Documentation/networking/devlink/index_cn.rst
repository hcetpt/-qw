### Linux Devlink 文档

`devlink` 是一个用于暴露与任何特定设备类别不直接相关的设备信息和资源的 API，例如芯片级/交换 ASIC 级配置。

#### 锁定

目前面向驱动程序的 API 正在过渡以允许更明确的锁定。驱动程序可以使用现有的 `devlink_*` 一组 API 或者新的以 `devl_*` 开头的 API。旧的 API 在 `devlink` 核心中处理所有锁定，但不允许在主要的 `devlink` 对象注册后注册大多数子对象。新的 `devl_*` API 假定 `devlink` 实例锁已经被持有。驱动程序可以通过调用 `devl_lock()` 来获取实例锁。它也被保持在网络命令的所有回调中。
驱动程序被鼓励使用 `devlink` 实例锁满足它们自己的需求。
当同时获取 `devlink` 实例锁和 RTNL 锁时，驱动程序需要谨慎。`devlink` 实例锁需要首先获取，在那之后才能获取 RTNL 锁。

#### 嵌套实例

一些对象（如线路卡或端口功能）可能在其下创建另一个 `devlink` 实例。在这种情况下，驱动程序应确保遵守以下规则：

- 必须保持锁的顺序。如果驱动程序需要同时获取嵌套实例和父实例的实例锁，则应首先获取父实例的 `devlink` 实例锁，然后才能获取嵌套实例的实例锁。
- 驱动程序应使用特定于对象的帮助函数来设置嵌套关系：

    - `devl_nested_devlink_set()` — 被调用来设置 `devlink` -> 嵌套 `devlink` 的关系（可用于多个嵌套实例）
    - `devl_port_fn_devlink_set()` — 被调用来设置端口功能 -> 嵌套 `devlink` 的关系
    - `devlink_linecard_nested_dl_set()` — 被调用来设置线路卡 -> 嵌套 `devlink` 的关系

嵌套的 `devlink` 信息通过 `devlink` netlink 对象特定属性向用户空间暴露。

#### 接口文档

以下页面描述了通过 `devlink` 通常可用的各种接口：
下面是这段文字的中文翻译：

```markdown
目录树:: 
   :maxdepth: 1

   devlink-dpipe
   devlink-health
   devlink-info
   devlink-flash
   devlink-params
   devlink-port
   devlink-region
   devlink-resource
   devlink-reload
   devlink-selftests
   devlink-trap
   devlink-linecard
   devlink-eswitch-attr

特定驱动程序的文档
-------------------

实现了 `devlink` 的每个驱动程序都应记录其支持的参数、信息版本以及其他特性。
目录树:: 
   :maxdepth: 1

   bnxt
   etas_es58x
   hns3
   i40e
   ionic
   ice
   mlx4
   mlx5
   mlxsw
   mv88e6xxx
   netdevsim
   nfp
   qed
   ti-cpsw-switch
   am65-nuss-cpsw-switch
   prestera
   iosm
   octeontx2
   sfc
```

请注意，这里使用的“目录树”(`toctree`) 是 Sphinx 文档生成工具中的一个指令，用于组织子页面。在中文环境中使用时，通常保留英文原样。如果你需要将其翻译为中文，可能需要根据具体上下文和使用场景来决定如何处理这一部分。
