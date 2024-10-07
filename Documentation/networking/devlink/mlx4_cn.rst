SPDX 许可证标识符: GPL-2.0

====================
mlx4 devlink 支持
====================

本文档描述了由 ``mlx4`` 设备驱动程序实现的 devlink 功能。

参数
======

.. list-table:: 实现的通用参数

   * - 名称
     - 模式
   * - ``internal_err_reset``
     - driverinit, runtime
   * - ``max_macs``
     - driverinit
   * - ``region_snapshot_enable``
     - driverinit, runtime

``mlx4`` 驱动程序还实现了以下驱动程序特定参数：

.. list-table:: 实现的驱动程序特定参数
   :widths: 5 5 5 85

   * - 名称
     - 类型
     - 模式
     - 描述
   * - ``enable_64b_cqe_eqe``
     - 布尔值
     - driverinit
     - 如果固件支持，则启用 64 字节 CQEs/EQEs
   * - ``enable_4k_uar``
     - 布尔值
     - driverinit
     - 启用使用 4k UAR

``mlx4`` 驱动程序支持通过 ``DEVLINK_CMD_RELOAD`` 进行重载。

区域
=======

``mlx4`` 驱动程序支持在关键固件问题时转储固件 PCI 配置空间和健康缓冲区。
如果固件命令超时、固件卡住或灾难性缓冲区出现非零值，驱动程序将拍摄快照。
``cr-space`` 区域将包含固件 PCI 配置空间的内容。``fw-health`` 区域将包含设备固件的健康缓冲区内容。
这两个区域的快照在相同的事件触发器下拍摄。
