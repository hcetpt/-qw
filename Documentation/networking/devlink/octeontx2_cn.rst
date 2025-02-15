SPDX 许可证标识符: GPL-2.0

=========================
OcteonTX2 devlink 支持
=========================

本文档描述了由 ``OcteonTX2 AF、PF 和 VF`` 设备驱动程序实现的 devlink 功能。
参数
==========

``OcteonTX2 PF 和 VF`` 驱动程序实现了以下特定于驱动程序的参数：

.. list-table:: 实现的驱动程序特定参数
   :widths: 5 5 5 85

   * - 名称
     - 类型
     - 模式
     - 描述
   * - ``mcam_count``
     - u16
     - 运行时
     - 选择为接口分配的匹配 CAM 条目数量
对于接口的 n-tuple 过滤器也使用相同设置。被 PF 和 VF 驱动程序支持

``OcteonTX2 AF`` 驱动程序实现了以下特定于驱动程序的参数：

.. list-table:: 实现的驱动程序特定参数
   :widths: 5 5 5 85

   * - 名称
     - 类型
     - 模式
     - 描述
   * - ``dwrr_mtu``
     - u32
     - 运行时
     - 用于设置硬件在各个发送队列之间进行调度时所使用的量子值
硬件采用加权 DWRR 算法在所有发送队列之间进行调度

``OcteonTX2 PF`` 驱动程序实现了以下特定于驱动程序的参数：

.. list-table:: 实现的驱动程序特定参数
   :widths: 5 5 5 85

   * - 名称
     - 类型
     - 模式
     - 描述
   * - ``unicast_filter_count``
     - u8
     - 运行时
     - 设置可以为设备编程的最大单播过滤器数量。这可用于更好地利用设备资源，避免过度消耗未使用的 MCAM 表项
