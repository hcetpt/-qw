SPDX 许可证标识符: GPL-2.0

====================
hns3 devlink 支持
====================

本文档描述了由 ``hns3`` 设备驱动程序实现的 devlink 功能。
``hns3`` 驱动程序支持通过 ``DEVLINK_CMD_RELOAD`` 进行重载。

信息版本
=============

``hns3`` 驱动程序报告以下版本：

.. list-table:: 实现的 devlink 信息版本
   :widths: 10 10 80

   * - 名称
     - 类型
     - 描述
   * - ``fw``
     - running
     - 用于表示固件版本
   * - ``fw.scc``
     - running
     - 用于表示 Soft Congestion Control (SCC) 固件版本
     - SCC 是一个固件组件，提供了多种 RDMA 拥塞控制算法，包括 DCQCN
