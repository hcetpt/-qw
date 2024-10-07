SPDX许可证标识符: GPL-2.0

=========================
netdevsim devlink 支持
=========================

本文档描述了 `netdevsim` 设备驱动程序支持的 `devlink` 功能。
参数
======

.. list-table:: 实现的一般参数

   * - 名称
     - 模式
   * - ``max_macs``
     - driverinit

`netdevsim` 驱动程序还实现了以下驱动程序特定参数：
.. list-table:: 实现的驱动程序特定参数
   :widths: 5 5 5 85

   * - 名称
     - 类型
     - 模式
     - 描述
   * - ``test1``
     - 布尔值
     - driverinit
     - 测试参数，用于展示如何实现一个驱动程序特定的 devlink 参数
`netdevsim` 驱动程序通过 `DEVLINK_CMD_RELOAD` 支持重载。

区域
=======

`netdevsim` 驱动程序暴露了一个 `dummy` 区域作为 devlink 区域接口工作方式的一个示例。每当写入 `take_snapshot` 的调试文件时都会创建快照。
资源
=========

`netdevsim` 驱动程序暴露了一些资源来控制驱动程序允许的 FIB 条目数、FIB 规则条目数和下一跳的数量。
.. code:: shell

    $ devlink resource set netdevsim/netdevsim0 path /IPv4/fib size 96
    $ devlink resource set netdevsim/netdevsim0 path /IPv4/fib-rules size 16
    $ devlink resource set netdevsim/netdevsim0 path /IPv6/fib size 64
    $ devlink resource set netdevsim/netdevsim0 path /IPv6/fib-rules size 16
    $ devlink resource set netdevsim/netdevsim0 path /nexthops size 16
    $ devlink dev reload netdevsim/netdevsim0

速率对象
============

`netdevsim` 驱动程序支持速率对象管理，包括：

- 注册/注销每个 VF devlink 端口的叶速率对象；
- 创建/删除节点速率对象；
- 设置任何速率对象类型的 tx_share 和 tx_max 速率值；
- 设置任何速率对象类型的父节点

速率节点及其参数在 `netdevsim` 的调试文件系统中以只读模式暴露。例如，创建名为 `some_group` 的速率节点：

.. code:: shell

    $ ls /sys/kernel/debug/netdevsim/netdevsim0/rate_groups/some_group
    rate_parent  tx_max  tx_share

相同参数也在相应端口目录中的叶对象中暴露。例如：

.. code:: shell

    $ ls /sys/kernel/debug/netdevsim/netdevsim0/ports/1
    dev  ethtool  rate_parent  tx_max  tx_share

驱动程序特定的陷阱
=====================

.. list-table:: `netdevsim` 注册的驱动程序特定陷阱列表
   :widths: 5 5 90

   * - 名称
     - 类型
     - 描述
   * - ``fid_miss``
     - ``exception``
     - 当数据包进入设备时，它会根据入站端口和 VLAN 被分类到过滤标识符（FID）。此陷阱用于捕获那些无法找到 FID 的数据包。
