SPDX 许可证标识符: GPL-2.0

====================
mlx5 devlink 支持
====================

本文档描述了由 ``mlx5`` 设备驱动程序实现的 devlink 功能。
参数
==========

.. list-table:: 实现的通用参数

   * - 名称
     - 模式
     - 验证
   * - ``enable_roce``
     - driverinit
     - 类型: 布尔

       如果设备支持 RoCE 禁用，RoCE 启用状态将控制设备对 RoCE 能力的支持。否则，控制发生在驱动堆栈中。当在驱动级别禁用 RoCE 时，仅支持原始以太网 QP
* - ``io_eq_size``
     - driverinit
     - 范围为 64 到 4096
* - ``event_eq_size``
     - driverinit
     - 范围为 64 到 4096
* - ``max_macs``
     - driverinit
     - 范围为 1 到 2^31。仅支持 2 的幂值

``mlx5`` 驱动还实现了以下特定于驱动的参数：

.. list-table:: 实现的特定于驱动的参数
   :widths: 5 5 5 85

   * - 名称
     - 类型
     - 模式
     - 描述
   * - ``flow_steering_mode``
     - 字符串
     - 运行时
     - 控制驱动程序的流转向模式

       * ``dmfs`` 设备管理的流转向。在 DMFS 模式下，硬件转向实体通过固件创建和管理
* ``smfs`` 软件管理的流转向。在 SMFS 模式下，硬件转向实体通过驱动程序创建和管理，无需固件干预
SMFS 模式比默认的 DMFS 模式更快，并且提供了更好的规则插入率
* - ``fdb_large_groups``
     - u32
     - driverinit
     - 控制 FDB 表中大组（大小 > 1）的数量
* 默认值为15，范围在1到1024之间
* - ``esw_multiport``
     - 布尔值
     - 运行时
     - 控制多端口E-Switch共享FDB模式
这是一种实验模式，其中使用单个E-Switch连接NIC上的所有vport和物理端口
一个例子是从PF0上创建的VF发送流量到与PF1上行链路原生关联的上行链路

       注意：未来设备，从ConnectX-8及以后的版本，最终会将此模式作为默认模式，以允许在一个单E-Switch环境中所有NIC端口之间的转发，并且双E-Switch模式可能会被弃用
默认：禁用
   * - ``esw_port_metadata``
     - 布尔值
     - 运行时
     - 在适用的情况下，禁用交换机元数据可以提高高达20%的数据包速率，具体取决于使用场景和数据包大小
Eswitch端口元数据状态控制是否内部标记数据包。对于多端口RoCE、表示器之间的故障转移和堆叠设备，必须启用元数据标记。默认情况下，在E-Switch支持的设备上启用了元数据。元数据仅适用于switchdev模式下的E-Switch，当用户确定不会使用以下任何场景时，可以选择禁用它：
       1. HCA处于双/多端口RoCE模式
2. VF/SF表示器绑定（通常用于实时迁移）
       3. 堆叠设备

       当禁用元数据时，如果用户尝试启用上述功能，则这些功能将无法初始化
注意：设置此参数不会立即生效。设置必须在传统模式下进行，并且在启用switchdev模式后，E-Switch端口元数据才会生效
* - ``hairpin_num_queues``
     - u32
     - 驱动初始化
     - 我们将涉及转发的TC NIC规则称为“hairpin”
Hairpin队列是mlx5硬件针对此类数据包硬件转发的具体实现
控制发夹队列的数量
* - ``hairpin_queue_size``
     - u32
     - 驱动初始化
     - 控制发夹队列的大小（以数据包为单位）
`mlx5` 驱动通过 `DEVLINK_CMD_RELOAD` 支持重载

版本信息
========

`mlx5` 驱动报告以下版本：

.. list-table:: devlink 信息版本实现
   :widths: 5 5 90

   * - 名称
     - 类型
     - 描述
   * - ``fw.psid``
     - 固定
     - 用于表示设备的板卡ID
* - ``fw.version``
     - 存储，运行中
     - 三个数字的主要.次要.微小固件版本号

健康报告器
==========

TX 报告器
---------
TX 报告器负责报告和恢复以下三种错误场景：

- TX 超时
    报告内核TX超时检测结果
    通过查找丢失的中断来恢复
- TX 错误完成
    报告TX错误完成情况
    通过清空TX队列并重置队列来恢复
- TX PTP 端口时间戳CQ不健康
    报告端口时间戳CQ上未传递的CQE过多
    通过清空并重新创建所有PTP通道来恢复
Tx Reporter 还支持按需诊断回调，提供其发送队列状态的实时信息。

用户命令示例：

- 诊断发送队列状态：

    ```
    $ devlink health diagnose pci/0000:82:00.0 reporter tx
    ```

    .. note::
       此命令仅在接口处于活动状态时才有有效输出，否则命令输出为空。

- 显示指示的 TX 错误数量、成功结束的恢复流程数量、是否启用了自动恢复以及自上次恢复以来的宽限期：

    ```
    $ devlink health show pci/0000:82:00.0 reporter tx
    ```

Rx Reporter
-----------
Rx Reporter 负责报告和恢复以下两种错误情况：

- Rx 队列初始化（填充）超时
    在初始化环时，通过触发中断在 NAPI 上下文中填充 Rx 队列描述符。如果未能获取到最小数量的描述符，则会发生超时，可以通过轮询 EQ（事件队列）来恢复这些描述符。
- 带有错误的 Rx 完成（由硬件在中断上下文报告）
    报告 Rx 完成错误，并在必要时通过刷新相关队列并重置来恢复。

Rx Reporter 同样支持按需诊断回调，提供其接收队列状态的实时信息。

- 诊断接收队列状态及其对应的完成队列：

    ```
    $ devlink health diagnose pci/0000:82:00.0 reporter rx
    ```

    .. note::
       此命令仅在接口处于活动状态时才有有效输出。否则，命令输出为空。

- 显示指示的 Rx 错误数量、成功结束的恢复流程数量、是否启用了自动恢复以及自上次恢复以来的宽限期：

    ```
    $ devlink health show pci/0000:82:00.0 reporter rx
    ```

Fw Reporter
-----------
Fw Reporter 实现了 `diagnose` 和 `dump` 回调。它通过触发 Fw 核心转储并将转储存储到缓冲区来跟踪 Fw 错误症状，如 Fw 综合征。

用户可以随时触发 Fw Reporter 诊断命令以检查当前的 Fw 状态。
用户命令示例：

- 检查固件健康状态：

    ```shell
    $ devlink health diagnose pci/0000:82:00.0 reporter fw
    ```

- 读取已存储的固件核心转储或触发新的转储：

    ```shell
    $ devlink health dump show pci/0000:82:00.0 reporter fw
    ```

.. note::
   此命令只能在拥有固件追踪器所有权的PF上运行，在其他PF或任何VF上运行将返回“操作不被允许”。

固件致命错误报告器
-----------------
固件致命错误报告器实现了`dump`和`recover`回调。
它通过CR-space转储和恢复流程跟踪致命错误指示。
CR-space转储使用的是vsc接口，即使在固件命令接口不可用的情况下（这是大多数固件致命错误的情况），该接口仍然有效。
恢复函数执行恢复流程，如果需要的话会重新加载驱动程序并触发固件重置。
在固件错误时，健康缓冲区的内容会被转储到dmesg中。日志级别由错误的严重性（在健康缓冲区中给出）决定。

用户命令示例：

- 手动运行固件恢复流程：

    ```shell
    $ devlink health recover pci/0000:82:00.0 reporter fw_fatal
    ```

- 读取已存储的固件CR-space转储或触发新的转储：

    ```shell
    $ devlink health dump show pci/0000:82:00.1 reporter fw_fatal
    ```

.. note::
   此命令只能在PF上运行。

VNIC报告器
-------------
VNIC报告器仅实现了`diagnose`回调。
它负责从固件查询VNIC诊断计数器并在实时显示它们。

VNIC计数器描述：

- `total_error_queues`
        因异步错误或错误命令而处于错误状态的队列数量
### 翻译

#### 监控指标说明：

- `send_queue_priority_update_flow`
    - 更新QP/SQ优先级/SL事件的数量
- `cq_overrun`
    - 因溢出导致CQ进入错误状态的次数
- `async_eq_overrun`
    - 异步事件映射的EQ溢出的次数
- `comp_eq_overrun`
    - 完成事件映射的EQ溢出的次数
- `quota_exceeded_command`
    - 由于配额超出而发出并失败的命令数量
- `invalid_command`
    - 由于其他原因（而非配额超出）发出并失败的命令数量
- `nic_receive_steering_discard`
    - 完成了接收流（RX）转向但因流表不匹配而被丢弃的数据包数量
- `generated_pkt_steering_fail`
    - VNIC生成的数据包在转向过程中出现意外失败的数量（转向流程中的任何阶段）
- `handled_pkt_steering_fail`
    - VNIC处理的数据包在转向过程中出现意外失败的数量（包括VNIC拥有的转向流程，以及eswitch所有者的FDB）

#### 用户命令示例：

- 诊断PF/VF VNIC计数器：

        ```sh
        $ devlink health diagnose pci/0000:82:00.1 reporter vnic
        ```

- 诊断代表端口（representor）的VNIC计数器（通过`devlink port`命令获取代表端口的devlink端口）：

        ```sh
        $ devlink health diagnose pci/0000:82:00.1/65537 reporter vnic
        ```

.. note::
   此命令可以在所有接口上运行，如PF/VF和代表端口。
当然，请提供你需要翻译的文本。
