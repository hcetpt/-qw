通过连接器的用户空间通信协议
===============================================

消息类型
=============

w1 核心与用户空间之间有三种类型的消息：

1. 事件。每当自动或请求搜索后找到新的主设备或从设备时生成。
2. 用户空间命令
3. 对用户空间命令的回复
协议
========

```
[struct cn_msg] - 连接器头
其长度字段等于附加数据的大小
[struct w1_netlink_msg] - w1 netlink 头
__u8 type 	- 消息类型
W1_LIST_MASTERS
                列出当前总线主设备
            W1_SLAVE_ADD/W1_SLAVE_REMOVE
                从设备添加/移除事件
            W1_MASTER_ADD/W1_MASTER_REMOVE
                主设备添加/移除事件
            W1_MASTER_CMD
                用户空间对总线主设备的命令
                （搜索/报警搜索）
            W1_SLAVE_CMD
                用户空间对从设备的命令
                （读取/写入/触碰）
        __u8 status	- 内核返回的错误指示
        __u16 len	- 附加到此头的数据的大小
union {
    __u8 id[8];			 - 从设备唯一设备ID
    struct w1_mst {
        __u32		id;	 - 主设备ID
        __u32		res;	 - 预留
    } mst;
} id;

[struct w1_netlink_cmd] - 给定主设备或从设备的命令
__u8 cmd	- 命令操作码
W1_CMD_READ 	- 读取命令
            W1_CMD_WRITE	- 写入命令
            W1_CMD_SEARCH	- 搜索命令
            W1_CMD_ALARM_SEARCH - 报警搜索命令
            W1_CMD_TOUCH	- 触碰命令
                （写入并采样数据回用户空间）
            W1_CMD_RESET	- 发送总线复位
            W1_CMD_SLAVE_ADD	- 将从设备添加到内核列表
            W1_CMD_SLAVE_REMOVE	- 从内核列表中移除从设备
            W1_CMD_LIST_SLAVES	- 从内核获取从设备列表
    __u8 res	- 预留
    __u16 len	- 此命令的数据长度
        对于读取命令，数据必须像写入命令一样分配
    __u8 data[0]	- 此命令的数据
```

每个连接器消息可以包含一个或多个 w1_netlink_msg，附带零个或多个嵌入式 w1_netlink_cmd 消息。
对于事件消息，没有嵌入的 w1_netlink_cmd 结构，只有连接器头和 w1_netlink_msg 结构，其中 "len" 字段为零，并填充了类型（事件类型之一）和 id：
要么是主机顺序下的8字节从设备唯一ID，
或者是在添加到 w1 核心时分配给总线主设备的主设备ID。
目前，仅针对读取命令请求生成用户空间命令的回复。对于每个`w1_netlink_cmd`读取请求，会生成一个确切的回复。发送时，回复不会被合并，即典型的回复消息看起来像这样：

```
[cn_msg][w1_netlink_msg][w1_netlink_cmd]
cn_msg.len = sizeof(struct w1_netlink_msg) +
             sizeof(struct w1_netlink_cmd) +
             cmd->len;
w1_netlink_msg.len = sizeof(struct w1_netlink_cmd) + cmd->len;
w1_netlink_cmd.len = cmd->len;
```

对`W1_LIST_MASTERS`的回复应向用户空间发送一条包含所有已注册主设备ID列表的消息，格式如下：

```
cn_msg (CN_W1_IDX.CN_W1_VAL作为id，长度等于struct w1_netlink_msg的大小加上主设备数量乘以4)
w1_netlink_msg (类型：W1_LIST_MASTERS，长度等于主设备数量乘以4（u32大小）)
id0 ... idN
```

每条消息的最大大小为4k，因此如果主设备的数量超过此限制，它将被拆分为多条消息。

`W1`搜索和报警搜索命令请求如下：

```
[cn_msg]
  [w1_netlink_msg type = W1_MASTER_CMD
  id等于用于搜索的总线主设备id]
  [w1_netlink_cmd cmd = W1_CMD_SEARCH或W1_CMD_ALARM_SEARCH]
```

回复如下：

```
[cn_msg, ack = 1并递增，0意味着最后一条消息，
seq等于请求seq]
[w1_netlink_msg type = W1_MASTER_CMD]
[w1_netlink_cmd cmd = W1_CMD_SEARCH或W1_CMD_ALARM_SEARCH
len等于ID数量乘以8]
[64位-id0 ... 64位-idN]
```

每个头中的长度对应于其后数据的大小，所以`w1_netlink_cmd->len = N * 8`；其中N是此消息中的ID数量。
可以为零：
```
w1_netlink_msg->len = sizeof(struct w1_netlink_cmd) + N * 8;
cn_msg->len = sizeof(struct w1_netlink_msg) +
              sizeof(struct w1_netlink_cmd) +
              N*8;
```

`W1`重置命令如下：

```
[cn_msg]
  [w1_netlink_msg type = W1_MASTER_CMD
  id等于用于搜索的总线主设备id]
  [w1_netlink_cmd cmd = W1_CMD_RESET]
```

### 命令状态回复

每个命令（无论是根、主还是从命令，无论是否带有`w1_netlink_cmd`结构）都将由`w1`核心确认。回复的格式与请求消息相同，只是长度参数不包括用户请求的数据，即读/写/触碰IO请求将不包含数据，因此`w1_netlink_cmd.len`将为0，`w1_netlink_msg.len`将是`w1_netlink_cmd`结构的大小，而`cn_msg.len`将等于`struct w1_netlink_msg`和`struct w1_netlink_cmd`大小的总和。
如果回复是为主或根命令生成的（这些命令没有附加`w1_netlink_cmd`），回复将只包含`cn_msg`和`w1_netlink_msg`结构。
`w1_netlink_msg.status`字段将携带正值错误（例如EINVAL）或在成功情况下为零。
所有其他结构中的字段将镜像请求消息中相同的参数（除了上面描述的长度）。
为`w1_netlink_msg`中嵌入的每个`w1_netlink_cmd`生成状态回复，如果没有`w1_netlink_cmd`结构，将为`w1_netlink_msg`生成回复。
`w1_netlink_msg`中的所有`w1_netlink_cmd`命令结构都会被处理，即使有错误，只有长度不匹配才会中断消息处理。
### 在收到新命令时 w1 核心的操作步骤
=======================================================

当接收到新的消息（w1_netlink_msg）时，w1 核心会检测该消息是主设备请求还是从设备请求，这一判断依据 w1_netlink_msg 的 `type` 字段。
- 然后，根据请求类型搜索相应的主设备或从设备。
- 找到后，锁定请求的主设备（如果是请求的从设备，则锁定包含该从设备的主设备）。
- 如果是请求从设备命令，则开始重置/选择过程以选择指定的设备。
- 接着依次执行 w1_netlink_msg 中请求的所有操作。
- 如果命令需要回复（如读取命令），则在命令完成后发送回复。
- 当所有命令（w1_netlink_cmd）处理完毕后，解锁主设备，并开始处理下一个 w1_netlink_msg 标头。

### 连接器 [1] 特定文档
====================================

每个连接器消息都包括两个 u32 类型的字段作为“地址”：
- w1 使用在 `include/linux/connector.h` 头文件中定义的 `CN_W1_IDX` 和 `CN_W1_VAL`。
- 每个消息还包括序列号和确认号。
- 事件消息的序列号对应于通过该主设备发送的每个事件消息递增的适当总线主设备序列号。
用户空间请求的序列号由用户空间应用程序设定。
回复的序列号与请求中的相同，
确认号则设置为seq+1。

额外的文档，源代码示例
==============================================

1. 文档/driver-api/connector.rst
2. http://www.ioremap.net/archive/w1

   该存档包括了用户空间应用程序w1d.c，它使用读/写/搜索命令对总线上找到的所有主/从设备进行操作。
