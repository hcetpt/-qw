SPDX 许可证标识符: GPL-2.0

===================
sfc devlink 支持
===================

本文档描述了针对 ef100 设备的 `sfc` 设备驱动程序所实现的 devlink 功能。
信息版本
=============

`sfc` 驱动报告以下版本：

.. list-table:: 实现的 devlink 信息版本
   :widths: 5 5 90

   * - 名称
     - 类型
     - 描述
   * - ``fw.mgmt.suc``
     - 运行中
     - 对于管理功能分布在多个控制单元的板卡，这是 SUC 控制单元的固件版本。
   * - ``fw.mgmt.cmc``
     - 运行中
     - 对于管理功能分布在多个控制单元的板卡，这是 CMC 控制单元的固件版本。
   * - ``fpga.rev``
     - 运行中
     - FPGA 设计修订版。
   * - ``fpga.app``
     - 运行中
     - 数据路径可编程逻辑版本。
   * - ``fw.app``
     - 运行中
     - 数据路径软件/微代码/固件版本。
   * - ``coproc.boot``
     - 运行中
     - SmartNIC 应用协处理器 (APU) 第一阶段引导加载程序版本。
   * - ``coproc.uboot``
     - 运行中
     - SmartNIC 应用协处理器 (APU) 协操作系统加载程序版本。
   * - ``coproc.main``
     - 运行中
     - SmartNIC 应用协处理器 (APU) 主操作系统版本。
   * - ``coproc.recovery``
     - 运行中
     - SmartNIC 应用协处理器 (APU) 恢复操作系统版本。
* - ``fw.exprom``
     - 运行中
     - 扩展ROM版本。对于扩展ROM被分割存储在多个镜像文件中的板卡（例如，PXE和UEFI），这里特指PXE启动ROM的版本。
* - ``fw.uefi``
     - 运行中
     - UEFI驱动程序版本（不支持UNDI）
