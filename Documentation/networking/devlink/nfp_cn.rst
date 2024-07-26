SPDX 许可证标识符: GPL-2.0

===================
NFP Devlink 支持
===================

本文档描述了由 ``nfp`` 设备驱动程序实现的 Devlink 特性。
参数
==========

.. list-table:: 实现的通用参数

   * - 名称
     - 模式
   * - ``fw_load_policy``
     - 永久
   * - ``reset_dev_on_drv_probe``
     - 永久

信息版本
=============

``nfp`` 驱动报告以下版本信息。

.. list-table:: 实现的 Devlink 信息版本
   :widths: 5 5 90

   * - 名称
     - 类型
     - 描述
   * - ``board.id``
     - 固定
     - 板卡设计的标识符
   * - ``board.rev``
     - 固定
     - 板卡设计的修订版本
   * - ``board.manufacture``
     - 固定
     - 板卡设计的供应商
   * - ``board.model``
     - 固定
     - 板卡设计的型号名称
   * - ``board.part_number``
     - 固定
     - 板卡及其组件的部件编号
   * - ``fw.bundle_id``
     - 存储、运行
     - 固件包 ID
   * - ``fw.mgmt``
     - 存储、运行
     - 管理固件的版本
   * - ``fw.cpld``
     - 存储、运行
     - CPLD 固件组件的版本
   * - ``fw.app``
     - 存储、运行
     - APP 固件组件的版本
   * - ``fw.undi``
     - 存储、运行
     - UNDI 固件组件的版本
   * - ``fw.ncsi``
     - 存储、运行
     - NCSI 固件组件的版本
   * - ``chip.init``
     - 存储、运行
     - CFGR 固件组件的版本
