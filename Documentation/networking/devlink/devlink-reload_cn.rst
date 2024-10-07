SPDX 许可证标识符: GPL-2.0

==============
Devlink 重载
==============

`devlink-reload` 提供了一种重新初始化驱动程序实体的机制，应用新的 `devlink-params` 和 `devlink-resources` 值。它还提供了一种激活固件的机制。

重载操作
==============

用户可以选择一个重载操作
默认选择 `driver_reinit` 操作

.. list-table:: 可能的重载操作
   :widths: 5 90

   * - 名称
     - 描述
   * - `driver-reinit`
     - Devlink 驱动程序实体的重新初始化，包括将新值应用于在驱动程序加载期间使用的 Devlink 实体：

       * 在配置模式 `driverinit` 下的 `devlink-params`
       * `devlink-resources`

       其他 Devlink 实体可能在重新初始化过程中保持不变：

       * `devlink-health-reporter`
       * `devlink-region`

       其余的 Devlink 实体需要被移除并重新添加。
   * - `fw_activate`
     - 固件激活。如果存储了待激活的新固件映像，则激活该新固件。如果没有指定限制，此操作可能会涉及固件重置。如果没有新的映像待激活，此操作将重新加载当前固件映像。

请注意，即使用户请求了特定的操作，驱动程序实现可能需要执行其他操作。例如，某些驱动程序不支持在没有固件激活的情况下进行驱动程序重新初始化。因此，`devlink reload` 命令返回实际执行的操作列表。

重载限制
=============

默认情况下，重载操作不受限制，驱动程序实现可以根据需要包含重置或停机时间。
然而，一些驱动程序支持操作限制，这些限制将操作实现限制在特定约束内。

.. list-table:: 可能的重载限制
   :widths: 5 90

   * - 名称
     - 描述
   * - `no_reset`
     - 不允许重置，不允许停机时间，不允许链路抖动，并且不会丢失配置

更改命名空间
================

netns 选项允许用户在 `devlink reload` 操作期间将 Devlink 实例移动到命名空间中。
默认情况下，所有 devlink 实例都在 init_net 中创建并保持在那里。

示例用法
--------

.. code:: shell

    $ devlink dev reload help
    $ devlink dev reload DEV [ netns { PID | NAME | ID } ] [ action { driver_reinit | fw_activate } ] [ limit no_reset ]

    # 运行 reload 命令以重新初始化 devlink 驱动实体：
    $ devlink dev reload pci/0000:82:00.0 action driver_reinit
    reload_actions_performed:
      driver_reinit

    # 运行 reload 命令以激活固件：
    # 注意 mlx5 驱动在激活固件时会重新加载驱动
    $ devlink dev reload pci/0000:82:00.0 action fw_activate
    reload_actions_performed:
      driver_reinit fw_activate
