Linux Devlink 文档
===========================

`devlink` 是一个用于暴露设备信息和资源的 API，这些信息和资源与任何特定的设备类别无关，例如芯片范围/交换 ASIC 范围的配置。

锁定
-------

面向驱动程序的 API 目前正在过渡以允许更明确的锁定。驱动程序可以使用现有的 `devlink_*` 系列 API，或者使用新的以 `devl_*` 为前缀的 API。较旧的 API 在 `devlink` 核心中处理所有锁定，但不允许在主要的 `devlink` 对象注册后注册大多数子对象。新的 `devl_*` API 假定 `devlink` 实例锁已经被持有。驱动程序可以通过调用 `devl_lock()` 来获取实例锁。所有 `devlink` Netlink 命令的回调中也持有该锁。驱动程序被鼓励使用 `devlink` 实例锁来满足自身需求。驱动程序在同时获取 `devlink` 实例锁和 RTNL 锁时需要谨慎。`devlink` 实例锁需要首先获取，之后才能获取 RTNL 锁。

嵌套实例
----------------

某些对象（如线路卡或端口功能）可能在其下创建另一个 `devlink` 实例。在这种情况下，驱动程序应确保遵循以下规则：

- 应保持锁的顺序。如果驱动程序需要同时获取嵌套实例和父实例的实例锁，则应首先获取父实例的 `devlink` 实例锁，然后才能获取嵌套实例的实例锁。
- 驱动程序应使用特定于对象的辅助函数来设置嵌套关系：

  - `devl_nested_devlink_set()` - 用于设置 `devlink` 到嵌套 `devlink` 的关系（可用于多个嵌套实例）
  - `devl_port_fn_devlink_set()` - 用于设置端口功能到嵌套 `devlink` 的关系
  - `devlink_linecard_nested_dl_set()` - 用于设置线路卡到嵌套 `devlink` 的关系

嵌套 `devlink` 的信息通过 `devlink` Netlink 的特定对象属性暴露给用户空间。

接口文档
-----------------------

以下页面描述了通过 `devlink` 可用的各种接口：
.. toctree::
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

每个实现“devlink”的驱动程序都应记录其支持的参数、信息版本和其他功能。
.. toctree::
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
