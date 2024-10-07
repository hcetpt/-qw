SPDX 许可声明标识符: GPL-2.0

====================
接口统计信息
====================

概述
========

本文档是关于 Linux 网络接口统计信息的指南。
Linux 中接口统计信息的主要来源有三个：

- 基于 `struct rtnl_link_stats64 <rtnl_link_stats64>` 的标准接口统计信息；
- 协议特定的统计信息；
- 通过 ethtool 可获取的驱动程序定义的统计信息。

标准接口统计信息
----------------------

有多重接口可以访问这些标准统计信息。最常用的是 `iproute2` 中的 `ip` 命令，例如：

```shell
$ ip -s -s link show dev ens4u1u1
6: ens4u1u1: <BROADCAST,MULTICAST,UP,LOWER_UP> mtu 1500 qdisc fq_codel state UP mode DEFAULT group default qlen 1000
    link/ether 48:2a:e3:4c:b1:d1 brd ff:ff:ff:ff:ff:ff
    RX: bytes  packets  errors  dropped overrun mcast
    74327665117 69016965 0       0       0       0
    RX errors: length   crc     frame   fifo    missed
               0        0       0       0       0
    TX: bytes  packets  errors  dropped carrier collsns
    21405556176 44608960 0       0       0       0
    TX errors: aborted  fifo   window heartbeat transns
               0        0       0       0       128
    altname enp58s0u1u1
```

注意 `-s` 指定了两次以显示 `struct rtnl_link_stats64 <rtnl_link_stats64>` 的所有成员。
如果只指定一次 `-s`，则不会显示详细的错误信息。
`ip` 命令支持通过 `-j` 选项进行 JSON 格式化输出。

队列统计信息
~~~~~~~~~~~

队列统计信息可以通过 netdev netlink 家族访问。
目前还没有广泛分发的命令行工具来访问这些统计信息。
内核开发工具（如 ynl）可用于实验这些功能，详见 `Documentation/userspace-api/netlink/intro-specs.rst`。

协议特定的统计信息
----------------------

协议特定的统计信息通过相关的接口暴露，与配置它们时使用的相同接口。
ethtool

Ethtool 暴露常见的低级统计信息
所有标准统计信息都应由设备维护，而不是驱动程序（与下一节中描述的由驱动程序定义的统计信息不同，后者混合了软件和硬件统计信息）。对于包含未管理交换机的设备（例如，传统的SR-IOV或多主机网卡），所计数的事件可能不仅限于发往本地主机接口的数据包。换句话说，这些事件可能在网络端口（MAC/PHY模块）处被计数，而不会针对不同的主机侧（PCIe）设备进行分离。当内部交换机由Linux管理时（即NICs的switchdev模式），这种模糊性不应存在。
通过用于配置的接口可以访问标准的ethtool统计信息。例如，用于配置暂停帧的ethtool接口可以报告相应的硬件计数器：

  $ ethtool --include-statistics -a eth0
  eth0 的暂停参数：
  自动协商：开启
  接收：开启
  发送：开启
  统计信息：
    发送暂停帧：1
    接收暂停帧：1

与任何特定功能无关的一般以太网统计信息可以通过指定`--groups`参数并通过`ethtool -S $ifc`来暴露：

  $ ethtool -S eth0 --groups eth-phy eth-mac eth-ctrl rmon
  eth0 的统计信息：
  eth-phy-SymbolErrorDuringCarrier: 0
  eth-mac-FramesTransmittedOK: 1
  eth-mac-FrameTooLongErrors: 1
  eth-ctrl-MACControlFramesTransmitted: 1
  eth-ctrl-MACControlFramesReceived: 0
  eth-ctrl-UnsupportedOpcodesReceived: 1
  rmon-etherStatsUndersizePkts: 1
  rmon-etherStatsJabbers: 0
  rmon-rx-etherStatsPkts64Octets: 1
  rmon-rx-etherStatsPkts65to127Octets: 0
  rmon-rx-etherStatsPkts128to255Octets: 0
  rmon-tx-etherStatsPkts64Octets: 2
  rmon-tx-etherStatsPkts65to127Octets: 3
  rmon-tx-etherStatsPkts128to255Octets: 0

由驱动程序定义的统计信息
------------------------------

使用`ethtool -S $ifc`可以转储由驱动程序定义的ethtool统计信息，例如：

  $ ethtool -S ens4u1u1
  网卡统计信息：
     发送单次碰撞：0
     发送多次碰撞：0

uAPIs
=====

procfs
------

历史上的`/proc/net/dev`文本接口可以访问接口列表及其统计信息
请注意，尽管此接口在内部使用:c:type:`struct rtnl_link_stats64 <rtnl_link_stats64>`，但它合并了一些字段
sysfs
-----

sysfs中的每个设备目录包含一个`statistics`目录（例如`/sys/class/net/lo/statistics/`），其中的文件对应于:c:type:`struct rtnl_link_stats64 <rtnl_link_stats64>`的成员
这个简单的接口特别适用于没有工具访问权限的受限/嵌入式环境。然而，在读取多个统计信息时效率较低，因为它在内部执行了:c:type:`struct rtnl_link_stats64 <rtnl_link_stats64>`的完整转储，并且仅报告所访问文件对应的统计信息
sysfs文件在`Documentation/ABI/testing/sysfs-class-net-statistics`中有文档说明
netlink
-------

`rtnetlink` (`NETLINK_ROUTE`)是访问:c:type:`struct rtnl_link_stats64 <rtnl_link_stats64>`统计信息的首选方法
统计信息在对链路信息请求（`RTM_GETLINK`）和统计信息请求（`RTM_GETSTATS`，当请求的`.filter_mask`中设置了`IFLA_STATS_LINK_64`位时）的响应中报告
netdev (netlink)
~~~~~~~~~~~~~~~~

`netdev`通用Netlink家族允许访问页面池和每个队列的统计信息
ethtool
-------

Ethtool IOCTL接口允许驱动程序报告特定于实现的统计信息。历史上，它也被用于报告其他API不存在的统计信息，例如每个设备队列的统计信息或基于标准的统计信息（例如RFC 2863）。统计信息及其字符串标识符是分别获取的：通过`ETHTOOL_GSTRINGS`获取标识符，并将`string_set`设置为`ETH_SS_STATS`；通过`ETHTOOL_GSTATS`获取值。用户空间应使用`ETHTOOL_GDRVINFO`来获取统计信息的数量（`.n_stats`）
ethtool-netlink
---------------

Ethtool Netlink是旧的IOCTL接口的替代方案。可以通过在get命令中设置`ETHTOOL_A_HEADER_FLAGS`中的`ETHTOOL_FLAG_STATS`标志来请求与协议相关的统计信息。目前，以下命令支持统计信息：

  - `ETHTOOL_MSG_PAUSE_GET`
  - `ETHTOOL_MSG_FEC_GET`
  - `ETHTOOL_MSG_MM_GET`

debugfs
-------

一些驱动程序通过`debugfs`暴露额外的统计信息
struct rtnl_link_stats64
========================

.. kernel-doc:: include/uapi/linux/if_link.h
    :identifiers: rtnl_link_stats64

给驱动程序作者的注意事项
========================

驱动程序应仅通过`.ndo_get_stats64`报告所有具有匹配成员的统计信息。通过ethtool或debugfs报告此类标准统计信息将不被接受。
驱动程序必须确保尽可能符合`struct rtnl_link_stats64`。
请注意，例如详细的错误统计信息必须添加到通用的`rx_error` / `tx_error`计数器中。
`.ndo_get_stats64` 回调不能睡眠，因为通过 `/proc/net/dev` 访问的原因。如果驱动程序在从设备检索统计信息时可以睡眠，则应定期异步进行，并且只从 `.ndo_get_stats64` 返回最近的副本。如果需要，ethtool 中断合并接口允许设置刷新统计信息的频率。
获取 ethtool 统计信息是一个多系统调用的过程，建议驱动程序保持统计信息的数量不变，以避免与用户空间尝试读取它们时出现的竞争条件。
统计信息必须在常规操作（如接口上下切换）中保持一致。

内核内部数据结构
-------------------

以下结构是内核内部的，其成员在转储时会被转换为 netlink 属性。驱动程序不应将其未报告的统计信息覆盖为 0。
- ethtool_pause_stats()
- ethtool_fec_stats()
