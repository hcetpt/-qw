SPDX 许可证标识符: GPL-2.0

=====================
多路径TCP (MPTCP)
=====================

介绍
============

多路径TCP或MPTCP是对标准TCP的扩展，并在`RFC 8684 (MPTCPv1) <https://www.rfc-editor.org/rfc/rfc8684.html>`_中进行了描述。它允许一个设备同时利用多个接口来通过单一MPTCP连接发送和接收TCP数据包。MPTCP可以汇聚多个接口的带宽，或者优先选择延迟最低的那个。如果一条路径断开，它还支持故障转移，并将流量无缝地重新注入到其他路径上。
对于Linux内核中的多路径TCP的更多详细信息，请参阅官方网站：`mptcp.dev <https://www.mptcp.dev>`_
使用场景
=========

得益于MPTCP，能够并行或同时使用多条路径带来了与TCP相比新的使用场景：

- 无缝切换：从一条路径切换到另一条路径的同时保持已建立的连接，例如用于移动性使用案例，如智能手机
- 最佳网络选择：根据某些条件（如延迟、丢包率、成本、带宽等）使用“最佳”可用路径
- 网络汇聚：同时使用多条路径以获得更高的吞吐量，例如结合固定和移动网络来更快地传输文件
概念
========

技术上讲，当用``IPPROTO_MPTCP``协议（特定于Linux）创建一个新的套接字时，会创建一个*子流*（或*路径*）。这个*子流*就是一个常规的TCP连接，用来通过一个接口传输数据。
后续可以在主机之间协商额外的*子流*。为了让远程主机能够检测到MPTCP的使用，在基础TCP*子流*的TCP*选项*字段中添加了一个新字段。该字段包含，除其他外，一个``MP_CAPABLE``选项，告诉另一端主机如果支持的话就使用MPTCP。如果远程主机或中间任何中间盒不支持，则返回的``SYN+ACK``数据包中TCP*选项*字段不会包含MPTCP选项。在这种情况下，连接将“降级”为普通的TCP，并且继续使用单个路径。
这种行为由两个内部组件实现：路径管理器和数据包调度器。
路径管理器
------------

路径管理器负责*子流*，从创建到删除，也包括地址通告。通常，是客户端一方发起子流，而服务器一方通过``ADD_ADDR``和``REMOVE_ADDR``选项来宣布额外的地址。
路径管理器由``net.mptcp.pm_type`` sysctl旋钮控制——参见mptcp-sysctl.rst。有两种类型：内核中的类型（类型``0``），其中对所有连接应用相同的规则（参见：``ip mptcp``）；以及用户空间中的类型（类型``1``），由用户空间守护进程（例如`mptcpd <https://mptcpd.mptcp.dev/>`_）控制，可以根据每个连接应用不同的规则。路径管理器可以通过Netlink API进行控制；参见netlink_spec/mptcp_pm.rst。
为了能够在主机上使用多个IP地址来创建多个*子流*（路径），内核中的默认MPTCP路径管理器需要知道可以使用哪些IP地址。这可以通过`ip mptcp endpoint`进行配置，例如。

### 数据包调度器

数据包调度器负责选择可用的*子流*之一来发送下一个数据包。它可以决定最大化利用可用带宽、仅选择延迟较低的路径，或者根据配置采用任何其他策略。

数据包调度器由`net.mptcp.scheduler` sysctl旋钮控制 -- 参见mptcp-sysctl.rst。

### 套接字API

#### 创建MPTCP套接字

在Linux上，可以通过在创建`socket`时选择MPTCP而不是TCP来使用MPTCP：

```C
int sd = socket(AF_INET(6), SOCK_STREAM, IPPROTO_MPTCP);
```

请注意`IPPROTO_MPTCP`被定义为`262`。

如果系统不支持MPTCP，则`errno`将设置为：

- `EINVAL`：(*无效参数*)：在内核版本<5.6时MPTCP不可用。
- `EPROTONOSUPPORT`：(*协议不受支持*)：MPTCP未被编译，在内核版本>=v5.6时。
- `ENOPROTOOPT`：(*协议不可用*)：通过`net.mptcp.enabled` sysctl旋钮禁用了MPTCP；参见mptcp-sysctl.rst。

然后，MPTCP是选择性的：应用程序需要明确请求它。需要注意的是，应用程序可以被强制使用MPTCP的不同技术，例如`LD_PRELOAD`（参见`mptcpize`）、eBPF（参见`mptcpify`）、SystemTAP、`GODEBUG` (`GODEBUG=multipathtcp=1`)等。

从`IPPROTO_TCP`切换到`IPPROTO_MPTCP`应该尽可能对用户空间的应用程序透明。
### Socket 选项

多路径TCP (MPTCP) 支持大多数由TCP处理的套接字选项。一些不常见的选项可能不受支持，但我们欢迎贡献。通常，相同的值会被传播到所有子流中，包括在调用 `setsockopt()` 之后创建的子流。可以使用 eBPF 来为每个子流设置不同的值。

有一些特定于 MPTCP 的套接字选项位于 `SOL_MPTCP`（284）级别，用于检索信息。它们填充 `getsockopt()` 系统调用中的 `optval` 缓冲区：

- `MPTCP_INFO`：使用 `struct mptcp_info`
- `MPTCP_TCPINFO`：使用 `struct mptcp_subflow_data`，后面跟着一个 `struct tcp_info` 数组
- `MPTCP_SUBFLOW_ADDRS`：使用 `struct mptcp_subflow_data`，后面跟着一个 `mptcp_subflow_addrs` 数组
- `MPTCP_FULL_INFO`：使用 `struct mptcp_full_info`，包含指向 `struct mptcp_subflow_info` 数组的一个指针（包括 `struct mptcp_subflow_addrs`），以及指向 `struct tcp_info` 数组的一个指针，随后是 `struct mptcp_info` 的内容

请注意，在TCP级别，可以通过 `TCP_IS_MPTCP` 套接字选项来判断是否正在使用 MPTCP：如果正在使用，则其值将被设置为 1。

### 设计选择

为面向用户空间的套接字添加了一个新的类型。内核负责创建子流套接字：这些是TCP套接字，其行为通过TCP-ULP进行修改。

当客户端连接请求没有要求使用 MPTCP 时，MPTCP 监听套接字会创建“普通”的已接受的TCP套接字，这样即使默认启用了 MPTCP，对性能的影响也很小。
