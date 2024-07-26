下面是提供的英文内容翻译成中文的结果：

---

SPDX 许可证标识符：GPL-2.0

====================
mlx5 devlink 支持
====================

本文档描述了由 `mlx5` 设备驱动程序实现的 devlink 功能。

参数
======

.. list-table:: 实现的通用参数

   * - 名称
     - 模式
     - 验证
   * - `enable_roce`
     - 驱动初始化
     - 类型：布尔值

       如果设备支持 RoCE 禁用功能，RoCE 启用状态会控制设备对 RoCE 能力的支持。否则，该控制发生在驱动堆栈中。当在驱动级别禁用 RoCE 时，仅支持原始以太网 QP。
   * - `io_eq_size`
     - 驱动初始化
     - 范围为 64 到 4096
   * - `event_eq_size`
     - 驱动初始化
     - 范围为 64 到 4096
   * - `max_macs`
     - 驱动初始化
     - 范围为 1 到 2^31。只支持 2 的幂次值
`mlx5` 驱动还实现了以下特定于驱动的参数。

.. list-table:: 实现的特定于驱动的参数
   :widths: 5 5 5 85

   * - 名称
     - 类型
     - 模式
     - 描述
   * - `flow_steering_mode`
     - 字符串
     - 运行时
     - 控制驱动程序的流导向模式

       * `dmfs` 设备管理流导向。在 DMFS 模式下，硬件导向实体通过固件创建和管理
* `smfs` 软件管理流导向。在 SMFS 模式下，硬件导向实体通过驱动程序而不是固件干预来创建和管理
SMFS 模式比默认的 DMFS 模式更快，提供了更好的规则插入速率
   * - `fdb_large_groups`
     - u32
     - 驱动初始化
     - 控制 FDB 表中的大型组（大小 > 1）的数量
* 默认值为 15，范围在 1 到 1024 之间
* - ``esw_multiport``
     - 布尔值
     - 运行时
     - 控制 MultiPort E-Switch 的共享 FDB 模式
这是一种实验模式，其中单个 E-Switch 被使用，并且网卡上的所有虚拟端口 (vports) 和物理端口都连接到它
一个例子是从 PF0 上创建的 VF 发送流量到与 PF1 的上行链路本机关联的上行链路

       注意：未来设备，从 ConnectX-8 及以后的型号，最终将默认采用此模式以允许在单一 E-Switch 环境中的所有网卡端口间进行转发，而双 E-Switch 模式可能被弃用
默认：禁用
   * - ``esw_port_metadata``
     - 布尔值
     - 运行时
     - 在适用的情况下，禁用 Eswitch 元数据可以提高包速高达 20%，具体取决于使用情况和包大小
Eswitch 端口元数据状态控制是否内部标记包的元数据。对于多端口 RoCE、表示器间的故障转移以及堆叠设备而言，必须启用元数据。默认情况下，在 E-Switch 支持的设备上启用了元数据。元数据仅适用于 switchdev 模式的 E-Switch，当用户不会使用以下任何一种情况时，他们可以禁用元数据：
       1. HCA 处于双/多端口 RoCE 模式
2. VF/SF 表示器绑定（通常用于实时迁移）
       3. 堆叠设备

       当元数据被禁用时，如果用户尝试启用上述任一功能，则这些功能将无法初始化
注意：设置此参数不会立即生效。设置必须在传统模式下进行，并且 Eswitch 端口元数据在启用 switchdev 模式后才会生效
* - ``hairpin_num_queues``
     - u32
     - 驱动初始化
     - 我们将涉及转发的 TC 网卡规则称为“hairpin”
Hairpin 队列是 mlx5 硬件针对此类包硬件转发的具体实现
### 控制发夹队列的数量
* - `hairpin_queue_size`
     - u32
     - 驱动初始化
     - 控制发夹队列的大小（以数据包计）

`mlx5` 驱动支持通过 `DEVLINK_CMD_RELOAD` 进行重载。

### 版本信息

`mlx5` 驱动报告以下版本：

#### devlink 信息版本实现
| 名称 | 类型 | 描述 |
| --- | --- | --- |
| `fw.psid` | 固定 | 用于表示设备的板卡ID |
| `fw.version` | 存储、运行中 | 三位主要.次要.微小固件版本号 |

### 健康报告器

#### 发送报告器
发送报告器负责报告并从以下三种错误情况中恢复：

- 发送超时
    - 报告内核发送超时检测结果
    - 通过查找丢失的中断进行恢复
- 发送错误完成
    - 报告错误发送完成
    - 通过清空发送队列并重置它来恢复
- 发送PTP端口时间戳CQ不健康
    - 报告在端口时间戳CQ上未传递的CQE过多
    - 通过清空并重新创建所有PTP通道来恢复
TX Reporter还支持按需诊断回调，通过这种方式提供其发送队列状态的实时信息。
用户命令示例：

- 诊断发送队列的状态：

    ```shell
    $ devlink health diagnose pci/0000:82:00.0 reporter tx
    ```

    .. note::
       当接口处于活动状态时，此命令才会有有效输出；否则，命令输出为空。

- 显示指示的TX错误数量、成功结束的恢复流程数量、是否启用了自动恢复以及从上次恢复以来的宽限期：

    ```shell
    $ devlink health show pci/0000:82:00.0 reporter tx
    ```

RX Reporter
-----------
RX Reporter负责报告并恢复以下两种错误情况：

- RX队列初始化（填充）超时
    RX队列描述符在环初始化时通过触发中断在NAPI上下文中完成。如果无法获取到最小数量的描述符，则会发生超时，并且可以通过轮询EQ（事件队列）来恢复这些描述符。
- 带有错误的RX完成（由硬件在中断上下文中报告）
    报告RX完成错误
    如有必要，通过清空相关队列并重置队列来进行恢复。
RX Reporter还支持按需诊断回调，通过这种方式提供其接收队列状态的实时信息。
- 诊断RX队列及其对应的完成队列的状态：

    ```shell
    $ devlink health diagnose pci/0000:82:00.0 reporter rx
    ```

    .. note::
       当接口处于活动状态时，此命令才会有有效输出。否则，命令输出为空。

- 显示指示的RX错误数量、成功结束的恢复流程数量、是否启用了自动恢复以及从上次恢复以来的宽限期：

    ```shell
    $ devlink health show pci/0000:82:00.0 reporter rx
    ```

FW Reporter
-----------
FW Reporter实现了`诊断`和`转储`回调。
它会跟踪FW错误的症状，如通过触发FW核心转储并将结果存储到转储缓冲区中的FW综合征。
用户可以随时触发FW Reporter诊断命令以检查当前FW的状态。
用户命令示例：

- 检查固件（Firmware, 简称 FW）的健康状态：

    ```
    $ devlink health diagnose pci/0000:82:00.0 reporter fw
    ```

- 如果已存储FW的核心转储文件，则读取它，或者触发一个新的转储：

    ```
    $ devlink health dump show pci/0000:82:00.0 reporter fw
    ```

.. 注意::
   此命令只能在拥有FW追踪器所有权的物理功能(PF)上运行，
   在其他PF或任何虚拟功能(VF)上运行会返回"操作不允许"。
   
致命错误报告器(FW Fatal Reporter)
----------------------------------
致命错误报告器实现了`dump`和`recover`回调。
它通过CR-space的转储和恢复流程来跟踪致命错误指示。
CR-space转储使用的是VSC接口，即使在FW命令接口不可用的情况下也有效，这通常发生在大多数FW致命错误中。
恢复函数运行恢复流程，如果需要的话，该流程会重新加载驱动程序并触发FW重置。
在FW错误时，健康缓冲区的内容会被转储到dmesg中。日志级别取决于错误的严重性（健康缓冲区给出）。
用户命令示例：

- 手动运行FW恢复流程：

    ```
    $ devlink health recover pci/0000:82:00.0 reporter fw_fatal
    ```

- 如果已存储FW的CR-space转储文件，则读取它，或者触发一个新的转储：

    ```
    $ devlink health dump show pci/0000:82:00.1 reporter fw_fatal
    ```

.. 注意::
   此命令只能在物理功能(PF)上运行。

vNIC报告器
-----------
vNIC报告器仅实现了`diagnose`回调。
它负责从FW查询vNIC诊断计数器，并实时显示它们。
vNIC计数器的描述：

- `total_error_queues`
        由于异步错误或命令出错而处于错误状态的队列数量
- `send_queue_priority_update_flow`
        优先级队列/发送队列的优先级/服务等级更新事件的数量
- `cq_overrun`
        因溢出导致完成队列(CQ)进入错误状态的次数
- `async_eq_overrun`
        异步事件队列(EQ)被覆盖的次数
- `comp_eq_overrun`
        完成事件队列(EQ)被覆盖的次数
- `quota_exceeded_command`
        因配额超出而导致发出并失败的命令数量
- `invalid_command`
        因除配额超出之外的任何原因而导致发出并失败的命令数量
- `nic_receive_steering_discard`
        已完成接收流转向但因与流表不匹配而被丢弃的数据包数量
- `generated_pkt_steering_fail`
        由虚拟网络接口(VNIC)生成且在转向流程中经历意外转向失败的数据包数量
- `handled_pkt_steering_fail`
        由虚拟网络接口(VNIC)处理且在转向流程中经历意外转向失败的数据包数量（包括VNIC拥有的转向流程中的所有点，以及eswitch所有者的FDB）

用户命令示例：

- 诊断PF/VF的vnic计数器：

        ```bash
        $ devlink health diagnose pci/0000:82:00.1 reporter vnic
        ```

- 诊断代表端口(representor)的vnic计数器（通过提供代表端口的devlink端口号执行，该端口号可通过`devlink port`命令获取）：

        ```bash
        $ devlink health diagnose pci/0000:82:00.1/65537 reporter vnic
        ```

.. note::
   此命令可以在所有接口上运行，例如PF/VF和代表端口。
您没有提供需要翻译的文本。请提供需要翻译成中文的英文或其他语言的文本。
