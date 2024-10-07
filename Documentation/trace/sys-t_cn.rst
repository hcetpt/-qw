SPDX 许可证标识符: GPL-2.0

===================
MIPI SyS-T 在 STP 上的应用
===================

MIPI SyS-T 协议驱动程序可以与 STM 类设备一起使用，以生成标准化的跟踪流。除了是一个标准之外，它还提供了更好的跟踪源识别和时间戳关联功能。为了在您的 STM 设备上使用 MIPI SyS-T 协议驱动程序，首先需要配置 `CONFIG_STM_PROTO_SYS_T`。

现在，在为您的 STM 设备创建策略时，您可以通过指定策略名称来选择要使用的协议驱动程序：

```
# mkdir /config/stp-policy/dummy_stm.0:p_sys-t.my-policy/
```

换句话说，策略名称格式扩展如下：

```
<device_name>:<protocol_name>.<policy_name>
```

例如，使用 Intel TH 时，它可以是 `"0-sth:p_sys-t.my-policy"`。
如果省略了协议名称，则 STM 类会使用最先加载的协议驱动程序。
您还可以通过以下命令检查是否一切正常：

```
# cat /config/stp-policy/dummy_stm.0:p_sys-t.my-policy/protocol
p_sys-t
```

现在，使用 MIPI SyS-T 协议驱动程序后，configfs 中的每个策略节点都会获得一些额外属性，这些属性决定了特定于协议的每源参数：

```
# mkdir /config/stp-policy/dummy_stm.0:p_sys-t.my-policy/default
# ls /config/stp-policy/dummy_stm.0:p_sys-t.my-policy/default
channels
clocksync_interval
do_len
masters
ts_interval
uuid
```

其中最重要的属性是 "uuid"，它决定了用于标记来自该源的所有数据的 UUID。当创建新节点时，它会自动生成，但您可能希望更改它。
`do_len` 控制 MIPI SyS-T 消息头中附加的 "有效负载长度" 字段的开关。默认情况下它是关闭的，因为 STP 已经标记了消息边界。
`ts_interval` 和 `clocksync_interval` 分别确定在消息头中包含协议（而非传输层，即 STP）时间戳或发送 CLOCKSYNC 数据包之前可以经过多少毫秒的时间。

更多详细信息，请参阅 `Documentation/ABI/testing/configfs-stp-policy-p_sys-t`。
* [1] https://www.mipi.org/specifications/sys-t
