### SPDX 许可证标识符: GPL-2.0

=========================
Octeon TX2 devlink 支持
=========================

本文档描述了由 `OcteonTX2 CPT` 设备驱动程序实现的 devlink 功能。

参数
==========

`octeontx2` 驱动实现了以下驱动特定参数：

.. list-table:: 实现的驱动特定参数
   :widths: 5 5 5 85

   * - 名称
     - 类型
     - 模式
     - 描述
   * - `t106_mode`
     - u8
     - 运行时
     - 用于配置 CN10KA B0/CN10KB CPT 以作为 CN10KA A0/A1 工作
