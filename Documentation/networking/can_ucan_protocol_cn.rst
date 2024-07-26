UCAN 协议
=========

UCAN 是微控制器基础上的 USB-CAN 适配器所使用的协议，这种适配器集成在 Theobroma Systems 的模块系统（System-on-Modules）中，并且也可以作为独立的 USB 棒提供。UCAN 协议设计时考虑了硬件独立性，其模型紧密地模仿了 Linux 内部表示 CAN 设备的方式。所有多字节整数都以小端格式编码。本文档中提到的所有结构体定义在 `drivers/net/can/usb/ucan.c` 文件中。

USB 端点
========

UCAN 设备使用三个 USB 端点：

- 控制端点：驱动程序通过此端点发送设备管理命令。
- 输入端点：设备通过此端点发送 CAN 数据帧和 CAN 错误帧。
- 输出端点：驱动程序通过输出端点发送 CAN 数据帧。

控制消息
=========

UCAN 设备通过控制管道上的供应商请求进行配置。为了支持单个 USB 设备中的多个 CAN 接口，所有的配置命令都针对 USB 描述符中的相应接口。驱动程序使用 `ucan_ctrl_command_in/out` 和 `ucan_device_request_in` 向设备传递命令。

设置包
------

| 字段          | 描述                                                      |
|---------------|-----------------------------------------------------------|
| `bmRequestType` | 方向 | 供应商 | (接口或设备) |
| `bRequest`     | 命令编号                                                |
| `wValue`       | 子命令编号（16 位）或不使用时为 0                       |
| `wIndex`       | USB 接口索引（对于设备命令为 0）                         |
| `wLength`      | * 主机到设备 - 需要传输的字节数<br>* 设备到主机 - 最大接收字节数。如果设备发送更少，则采用通用的零长度数据包(ZLP)语义 |

错误处理
--------

设备通过阻塞管道来指示失败的控制命令。

设备命令
--------

### UCAN_DEVICE_GET_FW_STRING
*从设备到主机；可选*

请求设备固件字符串
### 接口命令

#### UCAN_COMMAND_START
*主机到设备；必需*

启动 CAN 接口
**有效载荷格式**
  ``ucan_ctl_payload_t.cmd_start``

====  ============================
模式  或 ``UCAN_MODE_*`` 的掩码
====  ============================

#### UCAN_COMMAND_STOP
*主机到设备；必需*

停止 CAN 接口
**有效载荷格式**
  *空*

#### UCAN_COMMAND_RESET
*主机到设备；必需*

重置 CAN 控制器（包括错误计数器）
**有效载荷格式**
  *空*

#### UCAN_COMMAND_GET
*主机到设备；必需*

从设备获取信息

##### 子命令

**UCAN_COMMAND_GET_INFO**
  请求设备信息结构 ``ucan_ctl_payload_t.device_info``
请参阅 ``device_info`` 字段了解详细信息，并参见
  ``uapi/linux/can/netlink.h`` 获取关于
  ``can_bittiming`` 字段的解释。
**有效载荷格式**
    ``ucan_ctl_payload_t.device_info``

**UCAN_COMMAND_GET_PROTOCOL_VERSION**
  请求设备协议版本
  ``ucan_ctl_payload_t.protocol_version``。当前协议版本为3
**有效载荷格式**
    ``ucan_ctl_payload_t.protocol_version``

.. 注意:: 不支持此命令的设备使用旧协议版本1

#### UCAN_COMMAND_SET_BITTIMING
*主机到设备；必需*

通过发送结构 ``ucan_ctl_payload_t.cmd_set_bittiming`` 设置位定时（请参阅 ``struct bittiming`` 获取详情）
**有效载荷格式**
  ``ucan_ctl_payload_t.cmd_set_bittiming``

#### UCAN_SLEEP/WAKE
*主机到设备；可选*

配置睡眠和唤醒模式。驱动程序目前不支持该功能

#### UCAN_FILTER
*主机到设备；可选*

设置硬件 CAN 过滤器。驱动程序目前不支持该功能

#### 允许的接口命令

==================  ===================  ==================
合法设备状态  命令              新设备状态
==================  ===================  ==================
已停止             SET_BITTIMING        已停止
已停止             START                启动
已启动             STOP 或 RESET        已停止
已停止             STOP 或 RESET        已停止
已启动             RESTART              已启动
任意               GET                  *不变*
==================  ===================  ==================

#### 输入消息格式

USB 输入端点上的数据包包含一个或多个 ``ucan_message_in`` 值。如果多个消息被批量放入 USB 数据包中，可以使用 ``len`` 字段跳转到下一个 ``ucan_message_in`` 值（注意验证 ``len`` 值与实际数据大小的一致性）。

##### `len` 字段

每个 ``ucan_message_in`` 必须对齐到 4 字节边界（相对于数据缓冲区的起始位置）。这意味着在多个 ``ucan_message_in`` 值之间可能存在填充字节：

.. 代码块::

    +----------------------------+ < 0
    |                            |
    |   struct ucan_message_in   |
    |                            |
    +----------------------------+ < len
              [填充]
    +----------------------------+ < round_up(len, 4)
    |                            |
    |   struct ucan_message_in   |
    |                            |
    +----------------------------+
                [...]

##### `type` 字段

`type` 字段指定了消息的类型

**UCAN_IN_RX**
~~~~~~~~~~
**子类型**
  零

从 CAN 总线接收到的数据（ID + 负载）
### UCAN_IN_TX_COMPLETE

``subtype``
  零

CAN 设备已向 CAN 总线发送了一条消息。它会以一系列元组 `<echo-ids, 标志>` 的形式作出响应。其中 `echo-id` 用于识别该帧（回显先前 `UCAN_OUT_TX` 消息中的 ID）。标志表示传输的结果，其中位 0 设置为 1 表示成功。其他所有位均保留并设置为零。

#### 流控制

在接收 CAN 消息时，USB 缓冲区上没有流控制。驱动程序必须足够快地处理传入的消息以避免丢弃。如果设备缓冲区溢出，则通过发送相应的错误帧来报告此条件（参见“[CAN UCAN 错误处理]”）。

### 输出消息格式

USB 输出端点上的数据包包含一个或多个 `struct ucan_message_out` 值。如果将多条消息批量放入一个数据包中，设备使用 `len` 字段跳转到下一个 `ucan_message_out` 值。每个 `ucan_message_out` 必须相对于数据缓冲区的起始位置对齐到 4 字节。这一机制与“[CAN UCAN 输入消息长度]”中描述的相同。
```plaintext
+----------------------------+ < 0
|                            |
|   struct ucan_message_out  |
|                            |
+----------------------------+ < len
              [填充]
+----------------------------+ < round_up(len, 4)
|                            |
|   struct ucan_message_out  |
|                            |
+----------------------------+
                [...]
```

#### `type` 字段

在协议版本 3 中，仅定义了 `UCAN_OUT_TX`，其他字段仅由旧版设备（协议版本 1）使用。

##### UCAN_OUT_TX

``subtype``
  要在 `CAN_IN_TX_COMPLETE` 消息中回复的回显 ID

发送一条 CAN 帧。（参数：`id`，`data`）

#### 流控制

当设备输出缓冲区已满时，它开始在 `OUT` 管道上发送 *NAKs* 直到有更多的缓冲区可用。当一定数量的输出数据包未完成时，驱动程序停止队列。

### CAN 错误处理

如果启用了错误报告，设备会将错误编码到 CAN 错误帧中（参见 `uapi/linux/can/error.h`），并使用输入端点发送这些帧。驱动程序更新其错误统计信息并转发这些帧。

尽管 UCAN 设备可以完全抑制错误帧，但在 Linux 中，驱动程序始终感兴趣。因此，设备始终启动时带有 `UCAN_MODE_BERR_REPORT` 设置。对于用户空间过滤这些消息的操作由驱动程序完成。

#### 总线关闭

- 设备不会自动从总线关闭状态恢复。
- 总线关闭由错误帧指示（参见 `uapi/linux/can/error.h`）。
- 通过 `UCAN_COMMAND_RESTART` 开始总线关闭恢复。
- 完成总线关闭恢复后，设备发送一个错误帧，表明它处于 ERROR-ACTIVE 状态。
- 在总线关闭期间，设备不发送任何帧。
在总线关闭期间，主机的传输请求会立即完成，但不会设置成功标志。

示例对话
========

#) 设备连接到USB
#) 主机发送命令 `UCAN_COMMAND_RESET`，子命令为0
#) 主机发送命令 `UCAN_COMMAND_GET`，子命令为 `UCAN_COMMAND_GET_INFO`
#) 设备发送 `UCAN_IN_DEVICE_INFO`
#) 主机发送命令 `UCAN_OUT_SET_BITTIMING`
#) 主机发送命令 `UCAN_COMMAND_START`，子命令为0，模式为 `UCAN_MODE_BERR_REPORT`
