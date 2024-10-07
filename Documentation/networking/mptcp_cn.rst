SPDX 许可证标识符: GPL-2.0

=====================
多路径 TCP (MPTCP)
=====================

介绍
============

多路径 TCP 或 MPTCP 是对标准 TCP 的扩展，并在 `RFC 8684 (MPTCPv1) <https://www.rfc-editor.org/rfc/rfc8684.html>`_ 中进行了描述。它允许设备同时使用多个接口发送和接收 TCP 数据包，通过单一的 MPTCP 连接。MPTCP 可以聚合多个接口的带宽，或者优先选择延迟最低的一个接口。如果某条路径出现故障，它还支持切换到其他路径，使流量无缝重新注入。
关于 Linux 内核中的多路径 TCP 的更多详细信息，请参阅官方网站：`mptcp.dev <https://www.mptcp.dev>`_

用例
=========

由于 MPTCP 能够并行或同时使用多条路径，与传统的 TCP 相比，带来了新的应用场景：

- 无缝切换：在保持已建立连接的同时从一条路径切换到另一条路径，例如在移动设备（如智能手机）上使用
- 最佳网络选择：根据某些条件（如延迟、丢包率、成本、带宽等）选择“最佳”可用路径
- 网络聚合：同时使用多条路径来获得更高的吞吐量，例如结合固定和移动网络更快地传输文件

概念
============

技术上，当使用 ``IPPROTO_MPTCP`` 协议（Linux 特有）创建新套接字时，会创建一个 *子流*（或 *路径*）。这个 *子流* 包含一个常规的 TCP 连接，用于通过单个接口传输数据。
主机之间可以协商更多的 *子流*。为了使远程主机能够检测到 MPTCP 的使用，在底层 TCP *子流* 的 TCP *选项* 字段中添加了一个新字段。该字段包含一个 ``MP_CAPABLE`` 选项，告知另一端主机如果支持则使用 MPTCP。如果远程主机或中间任何设备不支持，则返回的 ``SYN+ACK`` 包中将不会包含 MPTCP 选项，这种情况下连接将“降级”为普通 TCP，并继续使用单路径。
这种行为是由两个内部组件实现的：路径管理器和包调度器。

路径管理器
------------

路径管理器负责 *子流* 的创建和删除，以及地址通告。通常，客户端发起子流，而服务器端通过 ``ADD_ADDR`` 和 ``REMOVE_ADDR`` 选项来通告额外的地址。
路径管理器由 ``net.mptcp.pm_type`` sysctl 参数控制——请参见 mptcp-sysctl.rst。有两种类型：内核内的（类型 ``0``），其中所有连接应用相同的规则（见：``ip mptcp``）；用户空间内的（类型 ``1``），由用户空间守护进程（如 `mptcpd <https://mptcpd.mptcp.dev/>`_）控制，可以为每个连接应用不同的规则。路径管理器可以通过 Netlink API 控制；请参见 netlink_spec/mptcp_pm.rst。
为了能够在主机上使用多个IP地址创建多个*子流*（路径），内核中的默认MPTCP路径管理器需要知道可以使用哪些IP地址。这可以通过`ip mptcp endpoint`命令来配置，例如。

### 数据包调度器

数据包调度器负责选择可用的*子流*之一来发送下一个数据包。它可以决定最大化利用可用带宽、仅选择延迟较低的路径，或者根据配置采用任何其他策略。
数据包调度器由`net.mptcp.scheduler` sysctl选项控制——详见mptcp-sysctl.rst。

### 套接字API

#### 创建MPTCP套接字

在Linux中，可以通过在创建`socket`时选择MPTCP而不是TCP来使用MPTCP：

```c
int sd = socket(AF_INET(6), SOCK_STREAM, IPPROTO_MPTCP);
```

请注意，`IPPROTO_MPTCP`被定义为`262`。
如果MPTCP不被支持，`errno`将设置为：

- `EINVAL`：（无效参数）：MPTCP不可用，在内核版本<5.6的情况下
- `EPROTONOSUPPORT`：（协议不支持）：MPTCP未被编译，在内核版本>=v5.6的情况下
- `ENOPROTOOPT`：（协议不可用）：通过`net.mptcp.enabled` sysctl选项禁用了MPTCP；详见mptcp-sysctl.rst

然后，MPTCP是可选的：应用程序需要明确请求使用它。需要注意的是，可以通过不同的技术强制应用程序使用MPTCP，例如`LD_PRELOAD`（参见`mptcpize`）、eBPF（参见`mptcpify`）、SystemTAP、`GODEBUG`（`GODEBUG=multipathtcp=1`）等。

从`IPPROTO_TCP`切换到`IPPROTO_MPTCP`对用户空间应用程序应该是尽可能透明的。
### Socket 选项

MPTCP 支持大多数由 TCP 处理的 socket 选项。一些不常见的选项可能不受支持，但欢迎贡献。通常情况下，相同的值会传播到所有子流，包括在调用 `setsockopt()` 之后创建的子流。可以使用 eBPF 来为每个子流设置不同的值。

有一些特定于 MPTCP 的 socket 选项位于 `SOL_MPTCP`（284）级别，用于获取信息。这些选项填充了 `getsockopt()` 系统调用中的 `optval` 缓冲区：

- `MPTCP_INFO`: 使用 `struct mptcp_info`
- `MPTCP_TCPINFO`: 使用 `struct mptcp_subflow_data`，后面跟着一个 `struct tcp_info` 数组
- `MPTCP_SUBFLOW_ADDRS`: 使用 `struct mptcp_subflow_data`，后面跟着一个 `mptcp_subflow_addrs` 数组
- `MPTCP_FULL_INFO`: 使用 `struct mptcp_full_info`，包含一个指向 `struct mptcp_subflow_info`（包括 `struct mptcp_subflow_addrs`）数组的指针和一个指向 `struct tcp_info` 数组的指针，后面是 `struct mptcp_info` 的内容

注意，在 TCP 层面，可以使用 `TCP_IS_MPTCP` socket 选项来判断是否正在使用 MPTCP：如果正在使用，则该值会被设置为 1。

### 设计选择

为 MPTCP 添加了一个新的 socket 类型，用于用户空间接口的 socket。内核负责创建子流 socket：这些是 TCP socket，其行为通过 TCP-ULP 进行修改。

当客户端连接请求没有要求使用 MPTCP 时，MPTCP 监听 socket 会创建“普通”的 *accepted* TCP socket，从而在默认启用 MPTCP 时对性能的影响最小化。
