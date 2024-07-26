`devlink` 提供了一种能力，使得驱动程序可以暴露设备参数以实现低级别的设备功能。由于 `devlink` 可以在设备整体级别上运行，因此它可以用于提供可能影响单个设备上多个端口的配置。

本文档描述了一系列通用参数，这些参数被多个驱动程序所支持。每个驱动程序也可以自由添加自己的参数。每个驱动程序必须记录其支持的具体参数，无论这些参数是否为通用参数。

### 配置模式

参数可以在不同的配置模式下设置。
.. list-table:: 可能的配置模式
   :widths: 5 90

   * - 名称
     - 描述
   * - ``runtime``
     - 在驱动程序运行时设置，并立即生效。无需重启
   * - ``driverinit``
     - 在驱动程序初始化过程中应用。需要用户使用 `devlink` 的重载命令重新启动驱动程序
   * - ``permanent``
     - 写入设备的非易失性内存中。需要硬重启才能使其生效

### 重载

为了让 `driverinit` 参数生效，驱动程序必须通过 `devlink-reload` 命令支持重载。此命令将请求重新加载设备驱动程序。

### 通用配置参数

以下是驱动程序可以添加的一系列通用配置参数列表。建议使用通用参数而不是让每个驱动程序创建自己的名称。
.. list-table:: 通用参数列表
   :widths: 5 5 90

   * - 名称
     - 类型
     - 描述
   * - ``enable_sriov``
     - 布尔值
     - 在设备中启用单一根 I/O 虚拟化（SRIOV）
   * - ``ignore_ari``
     - 布尔值
     - 忽略备选路由ID解释（ARI）功能。如果启用，适配器即使平台已经启用了 ARI 支持也会忽略 ARI 功能。设备将创建与平台不支持 ARI 时相同数量的分区。
* - ``msix_vec_per_pf_max``
     - u32
     - 提供设备能够创建的MSI-X中断的最大数量。该值在设备中的所有物理功能（PFs）上是相同的。
* - ``msix_vec_per_pf_min``
     - u32
     - 提供设备初始化所需的MSI-X中断的最小数量。该值在设备中的所有物理功能（PFs）上是相同的。
* - ``fw_load_policy``
     - u8
     - 控制设备的固件加载策略。
- ``DEVLINK_PARAM_FW_LOAD_POLICY_VALUE_DRIVER`` (0)
          加载驱动程序偏好的固件版本。
- ``DEVLINK_PARAM_FW_LOAD_POLICY_VALUE_FLASH`` (1)
          加载当前存储在闪存中的固件。
- ``DEVLINK_PARAM_FW_LOAD_POLICY_VALUE_DISK`` (2)
          加载当前可在主机磁盘上获取的固件。
* - ``reset_dev_on_drv_probe``
     - u8
     - 控制在驱动程序探测时设备的重置策略。
- ``DEVLINK_PARAM_RESET_DEV_ON_DRV_PROBE_VALUE_UNKNOWN`` (0)
          未知或无效的值。
- ``DEVLINK_PARAM_RESET_DEV_ON_DRV_PROBE_VALUE_ALWAYS`` (1)
          在驱动程序探测时始终重置设备。
- ``DEVLINK_PARAM_RESET_DEV_ON_DRV_PROBE_VALUE_NEVER`` (2)
          在驱动程序探测时从不重置设备。
- `DEVLINK_PARAM_RESET_DEV_ON_DRV_PROBE_VALUE_DISK` (3)
  - 在文件系统中找到固件时仅重置设备

* - `enable_roce`
     - 布尔值
     - 启用设备处理 RoCE (远程直接内存访问通过以太网) 交通
* - `enable_eth`
     - 布尔值
     - 启用后，设备驱动程序将为 devlink 设备实例化以太网特定的辅助设备
* - `enable_rdma`
     - 布尔值
     - 启用后，设备驱动程序将为 devlink 设备实例化 RDMA (远程直接内存访问) 特定的辅助设备
* - `enable_vnet`
     - 布尔值
     - 启用后，设备驱动程序将为 devlink 设备实例化 VDPA (虚拟数据路径加速) 网络特定的辅助设备
* - `enable_iwarp`
     - 布尔值
     - 启用设备处理 iWARP (Internet 协议 over RDMA) 交通
* - `internal_err_reset`
     - 布尔值
     - 启用后，设备驱动程序将在内部错误发生时重置设备
* - `max_macs`
     - 无符号 32 位整数 (u32)
     - 通常情况下，macvlan 和 vlan 网络设备的 MAC 地址也会被编程到其父网络设备的功能接收过滤器中。此参数限制了从该设备的每个以太网端口接收流量的单播 MAC 地址过滤器的最大数量
* - `region_snapshot_enable`
     - 布尔值
     - 启用 `devlink-region` 快照的捕获
* - `enable_remote_dev_reset`
     - 布尔值
     - 允许远程主机重置设备。如果该参数未设置，则设备驱动程序将拒绝任何其他主机尝试重置设备的操作。此参数对于设备由多个主机共享的情况（如多主机配置）非常有用。
* - ``io_eq_size``
     - u32
     - 控制 I/O 完成事件队列的大小
* - ``event_eq_size``
     - u32
     - 控制异步控制事件队列的大小
