### SPDX 许可证标识符: GPL-2.0

#### 引言
====================

Intel 管理引擎（Intel ME）是一个位于特定 Intel 芯片组内的隔离且受保护的计算资源（协处理器）。Intel ME 提供对计算机/IT 管理和安全功能的支持。实际的功能集取决于 Intel 芯片组 SKU。Intel 管理引擎接口（Intel MEI，之前称为 HECI）是主机与 Intel ME 之间的接口。此接口以 PCI 设备的形式暴露给主机，实际上可能会暴露多个 PCI 设备。

Intel MEI 驱动负责处理主机应用程序与 Intel ME 功能之间的通信通道。每个 Intel ME 功能或 Intel ME 客户端都由一个唯一的 GUID 标识，并且每个客户端都有自己的协议。该协议基于消息，包含头部和有效载荷，其最大字节数由客户端在连接时声明。

#### Intel MEI 驱动
====================

该驱动程序提供了一个字符设备，其设备节点为 /dev/meiX。当打开 /dev/meiX 时，应用程序可以维持与 Intel ME 功能的通信。通过调用宏 `MEI_CONNECT_CLIENT_IOCTL` 并传递所需的 GUID 来绑定到特定的功能。

同一时间可以打开的 Intel ME 功能实例的数量取决于具体的 Intel ME 功能，但大多数功能仅允许一个实例。驱动程序对在固件功能和主机应用程序之间传输的数据是透明的。

由于某些 Intel ME 功能可以更改系统配置，因此默认情况下只允许特权用户访问驱动程序。
会话通过调用`:c:expr:`close(fd)`终止。
一个与Intel AMTHI客户端通信的应用程序的代码示例：

为了支持虚拟化或沙箱技术，一个受信任的监控器可以使用`:c:macro:`MEI_CONNECT_CLIENT_IOCTL_VTAG`来创建与Intel ME功能的虚拟通道。并非所有特性都支持虚拟通道；不支持的客户端将返回EOPNOTSUPP错误。
```C
struct mei_connect_client_data data;
fd = open(MEI_DEVICE);

data.d.in_client_uuid = AMTHI_GUID;

ioctl(fd, IOCTL_MEI_CONNECT_CLIENT, &data);

printf("Ver=%d, MaxLen=%ld\n",
       data.d.in_client_uuid.protocol_version,
       data.d.in_client_uuid.max_msg_length);

[...]

write(fd, amthi_req_data, amthi_req_data_len);

[...]

read(fd, &amthi_res_data, amthi_res_data_len);

[...]
close(fd);
```

用户空间API

IOCTL命令:
==========

Intel MEI驱动支持以下IOCTL命令：

IOCTL_MEI_CONNECT_CLIENT
-------------------------
连接到固件特性/客户端
```none
使用方法:

    struct mei_connect_client_data client_data;

    ioctl(fd, IOCTL_MEI_CONNECT_CLIENT, &client_data);

输入:

    struct mei_connect_client_data - 包含以下输入字段:

        in_client_uuid - 要连接的固件特性的GUID
输出:
    out_client_properties - 客户端属性：MTU和协议版本
错误返回:

        ENOTTY 不存在此类客户端（即错误的GUID）或不允许建立连接
EINVAL 错误的IOCTL编号
        ENODEV 设备或连接未初始化或未准备好
ENOMEM 无法为客户内部数据分配内存
EFAULT 致命错误（例如，无法访问用户输入数据）
        EBUSY 连接已打开

注:
    客户端属性中的max_msg_length (MTU) 描述了可发送或接收的最大数据量。（例如，如果MTU=2K，则可以发送最多2K字节的请求，并接收最多2K字节的响应）
IOCTL_MEI_CONNECT_CLIENT_VTAG:
------------------------------

```none
使用方法:

    struct mei_connect_client_data_vtag client_data_vtag;

    ioctl(fd, IOCTL_MEI_CONNECT_CLIENT_VTAG, &client_data_vtag);

输入:

    struct mei_connect_client_data_vtag - 包含以下输入字段:

            in_client_uuid - 需要连接的固件特性的GUID
```
### vtag - 虚拟标签 [1, 255]

#### 输出：
- `out_client_properties` - 客户端属性：MTU 和协议版本

#### 错误返回：

- `ENOTTY` - 无此类客户端（即错误的GUID）或连接不允许
- `EINVAL` - 错误的IOCTL编号或标签为0
- `ENODEV` - 设备或连接未初始化或未准备好
- `ENOMEM` - 无法为客户端内部数据分配内存
- `EFAULT` - 致命错误（例如无法访问用户输入数据）
- `EBUSY` - 连接已打开
- `EOPNOTSUPP` - 不支持vtag

### IOCTL_MEI_NOTIFY_SET
-----------------------
启用或禁用事件通知

#### 代码块：

    使用方法：

        uint32_t enable;

        ioctl(fd, IOCTL_MEI_NOTIFY_SET, &enable);

    uint32_t enable = 1;
    或
    uint32_t enable[禁用] = 0;

#### 错误返回：

- `EINVAL` - 错误的IOCTL编号
- `ENODEV` - 设备未初始化或客户端未连接
- `ENOMEM` - 无法为客户端内部数据分配内存
- `EFAULT` - 致命错误（例如无法访问用户输入数据）
- `EOPNOTSUPP` - 如果设备不支持该功能

#### 注意：
客户端必须连接才能启用通知事件。

### IOCTL_MEI_NOTIFY_GET
--------------------
获取事件

#### 代码块：

    使用方法：
        uint32_t event;
        ioctl(fd, IOCTL_MEI_NOTIFY_GET, &event);

#### 输出：
- `1` - 如果有事件待处理
- `0` - 如果没有待处理的事件

#### 错误返回：
- `EINVAL` - 错误的IOCTL编号
- `ENODEV` - 设备未初始化或客户端未连接
- `ENOMEM` - 无法为客户端内部数据分配内存
- `EFAULT` - 致命错误（例如无法访问用户输入数据）
- `EOPNOTSUPP` - 如果设备不支持该功能

#### 注意：
客户端必须连接且事件通知必须已启用，才能接收事件。

### 支持的芯片组
==================
82X38/X48 Express 及更新版本

联系邮箱：`linux-mei@linux.intel.com`
