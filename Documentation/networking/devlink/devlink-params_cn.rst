SPDX 许可证标识符: GPL-2.0

==============
Devlink 参数
==============

``devlink`` 提供了让驱动程序暴露设备参数以实现低级别设备功能的能力。由于 devlink 可以在设备整体层面运行，因此可以用来提供可能影响单个设备上多个端口的配置。
本文档描述了一系列通用参数，这些参数得到了多个驱动程序的支持。每个驱动程序也可以自由添加自己的参数。每个驱动程序必须记录它们支持的具体参数，无论这些参数是否为通用参数。

配置模式
===================

参数可以在不同的配置模式下设置。
.. list-table:: 可能的配置模式
   :widths: 5 90

   * - 名称
     - 描述
   * - ``runtime``
     - 在驱动程序运行时设置，并立即生效。无需重置
   * - ``driverinit``
     - 在驱动程序初始化过程中应用。需要用户使用 ``devlink`` 重载命令重启驱动程序
   * - ``permanent``
     - 写入设备的非易失性内存。需要硬重置才能生效

重载
---------

为了让 ``driverinit`` 参数生效，驱动程序必须支持通过 ``devlink-reload`` 命令进行重载。此命令将请求重新加载设备驱动程序。
.. _devlink_params_generic:

通用配置参数
================================
以下是一些驱动程序可以添加的通用配置参数列表。建议使用通用参数，而不是每个驱动程序创建自己的名称。
.. list-table:: 通用参数列表
   :widths: 5 5 90

   * - 名称
     - 类型
     - 描述
   * - ``enable_sriov``
     - 布尔值
     - 启用设备中的单根I/O虚拟化（SRIOV）
   * - ``ignore_ari``
     - 布尔值
     - 忽略替代路由ID解释（ARI）功能。如果启用，适配器将忽略 ARI 功能，即使平台已启用了支持。设备将创建与平台不支持 ARI 时相同数量的分区。
* - ``msix_vec_per_pf_max``
     - u32
     - 提供设备可以创建的最大数量的MSI-X中断。该值在设备的所有物理功能（PF）中相同。
* - ``msix_vec_per_pf_min``
     - u32
     - 提供设备初始化所需的最小数量的MSI-X中断。该值在设备的所有物理功能（PF）中相同。
* - ``fw_load_policy``
     - u8
     - 控制设备的固件加载策略
- ``DEVLINK_PARAM_FW_LOAD_POLICY_VALUE_DRIVER`` (0)
          加载驱动程序首选的固件版本
- ``DEVLINK_PARAM_FW_LOAD_POLICY_VALUE_FLASH`` (1)
          加载当前存储在闪存中的固件
- ``DEVLINK_PARAM_FW_LOAD_POLICY_VALUE_DISK`` (2)
          加载当前在主机磁盘上可用的固件
* - ``reset_dev_on_drv_probe``
     - u8
     - 控制在驱动程序探测时设备的重置策略
- ``DEVLINK_PARAM_RESET_DEV_ON_DRV_PROBE_VALUE_UNKNOWN`` (0)
          未知或无效的值
- ``DEVLINK_PARAM_RESET_DEV_ON_DRV_PROBE_VALUE_ALWAYS`` (1)
          在驱动程序探测时始终重置设备
- ``DEVLINK_PARAM_RESET_DEV_ON_DRV_PROBE_VALUE_NEVER`` (2)
          在驱动程序探测时从不重置设备
- ``DEVLINK_PARAM_RESET_DEV_ON_DRV_PROBE_VALUE_DISK`` (3)
  - 仅当在文件系统中找到固件时重置设备

* - ``enable_roce``
    - 布尔值
    - 启用设备中的 RoCE 流量处理
* - ``enable_eth``
    - 布尔值
    - 启用后，设备驱动程序将实例化 devlink 设备的以太网特定辅助设备
* - ``enable_rdma``
    - 布尔值
    - 启用后，设备驱动程序将实例化 devlink 设备的 RDMA 特定辅助设备
* - ``enable_vnet``
    - 布尔值
    - 启用后，设备驱动程序将实例化 devlink 设备的 VDPA 网络特定辅助设备
* - ``enable_iwarp``
    - 布尔值
    - 启用设备中的 iWARP 流量处理
* - ``internal_err_reset``
    - 布尔值
    - 启用后，设备驱动程序将在内部错误时重置设备
* - ``max_macs``
    - u32
    - 通常，macvlan 和 vlan 网络设备的 MAC 地址也会在其父网络设备的功能接收滤波器中编程。此参数限制每个以太网端口从该设备接收流量的单播 MAC 地址过滤器的最大数量
* - ``region_snapshot_enable``
    - 布尔值
    - 启用 ``devlink-region`` 快照的捕获
* - ``enable_remote_dev_reset``
    - 布尔值
    - 启用远程主机对设备的重置。未启用时，设备驱动程序将拒绝任何其他主机尝试重置设备的操作。此参数适用于设备由多个主机共享的情况，例如多主机环境。
* - ``io_eq_size``
     - u32
     - 控制 I/O 完成事件队列（EQ）的大小
* - ``event_eq_size``
     - u32
     - 控制异步控制事件队列（EQ）的大小
