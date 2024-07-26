SPDX 许可证标识符: GPL-2.0

====================
bnxt devlink 支持
====================

本文档描述了由 `bnxt` 设备驱动程序实现的 devlink 特性。
参数
==========

.. list-table:: 实现的通用参数

   * - 名称
     - 模式
   * - ``enable_sriov``
     - 固定
   * - ``ignore_ari``
     - 固定
   * - ``msix_vec_per_pf_max``
     - 固定
   * - ``msix_vec_per_pf_min``
     - 固定
   * - ``enable_remote_dev_reset``
     - 运行时

`bnxt` 驱动程序还实现了以下特定于驱动程序的参数。

.. list-table:: 实现的驱动程序特定参数
   :widths: 5 5 5 85

   * - 名称
     - 类型
     - 模式
     - 描述
   * - ``gre_ver_check``
     - 布尔值
     - 固定
     - 在设备中启用通用路由封装 (GRE) 版本检查。如果禁用，设备将跳过对传入数据包的版本检查。

信息版本
=============

`bnxt_en` 驱动程序报告以下版本。

.. list-table:: 实现的 devlink 信息版本
      :widths: 5 5 90

   * - 名称
     - 类型
     - 描述
   * - ``board.id``
     - 固定
     - 标识板卡设计的部件编号
   * - ``asic.id``
     - 固定
     - ASIC 设计标识符
   * - ``asic.rev``
     - 固定
     - ASIC 设计修订版
   * - ``fw.psid``
     - 存储、运行
     - 板卡固件参数集版本
   * - ``fw``
     - 存储、运行
     - 整体板卡固件版本
   * - ``fw.mgmt``
     - 存储、运行
     - 网络接口卡硬件资源管理固件版本
   * - ``fw.mgmt.api``
     - 运行
     - 驱动程序与固件之间支持的最低固件接口规范版本
   * - ``fw.nsci``
     - 存储、运行
     - 通用平台管理固件版本
   * - ``fw.roce``
     - 存储、运行
     - RoCE 管理固件版本
