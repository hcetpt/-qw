==================
IP over InfiniBand
==================

  `ib_ipoib` 驱动是根据 IETF ipoib 工作组发布的 RFC 4391 和 4392 规定的 IP over InfiniBand 协议的实现。它是一种“原生”实现，即设置接口类型为 ARPHRD_INFINIBAND 并将硬件地址长度设为 20（早期的专有实现伪装成了以太网接口）。
分区和 P_Keys
=====================

  当加载 IPoIB 驱动时，它会使用索引 0 的 P_Key 为每个端口创建一个接口。要使用不同的 P_Key 创建接口，请将所需的 P_Key 写入主接口的 `/sys/class/net/<intf name>/create_child` 文件中。例如：

    ```
    echo 0x8001 > /sys/class/net/ib0/create_child
    ```

  这将创建名为 `ib0.8001`、P_Key 为 `0x8001` 的接口。要删除子接口，可使用 `delete_child` 文件：

    ```
    echo 0x8001 > /sys/class/net/ib0/delete_child
    ```

  任何接口的 P_Key 可通过 `pkey` 文件给出，而子接口对应的主接口则位于 `parent` 文件中。

  子接口的创建与删除也可通过 IPoIB 的 `rtnl_link_ops` 来完成，无论是哪种方式创建的子接口行为相同。
数据报模式与连接模式
===========================

  IPoIB 驱动支持两种操作模式：数据报模式和连接模式。模式可通过接口的 `/sys/class/net/<intf name>/mode` 文件进行设置和读取。
在数据报模式下，使用 IB UD（不可靠数据报）传输层，因此接口的 MTU 等于 IB 第二层 MTU 减去 IPoIB 封装头（4 字节）。例如，在具有 2K MTU 的典型 IB 网络中，IPoIB 的 MTU 为 2048 - 4 = 2044 字节。
在连接模式下，使用 IB RC（可靠连接）传输层。
连接模式利用了 IB 传输层的连接特性，允许 MTU 最大达到 IP 数据包的最大尺寸 64K，这减少了处理大型 UDP 数据报、TCP 分段等所需的 IP 数据包数量，提高了处理大型消息的性能。
在连接模式下，接口的 UD QP 仍用于多播以及与不支持连接模式的对等方通信。在这种情况下，通过 RX 模拟 ICMP PMTU 包来使网络堆栈为这些邻居使用较小的 UD MTU。
无状态卸载
==================

  如果 IB 硬件支持 IPoIB 无状态卸载，IPoIB 会向网络堆栈宣告支持 TCP/IP 校验和及/或大发送（LSO）卸载能力。
大型接收（LRO）卸载也被实现，并可通过 ethtool 调用来开启或关闭。目前 LRO 仅支持校验和卸载功能的设备。
无状态卸载仅在数据报模式下支持。
中断调节
====================

如果底层的 IB 设备支持 CQ 事件调节，可以使用 ethtool 设置中断缓解参数，从而减少处理中断所造成的开销。IPoIB 的主要代码路径不使用事件来指示 TX 完成信号，因此仅支持 RX 调节。
调试信息
=====================

通过将 IPoIB 驱动程序与 CONFIG_INFINIBAND_IPOIB_DEBUG 配置设置为 'y' 进行编译，可以将跟踪消息编译进驱动程序。通过将模块参数 `debug_level` 和 `mcast_debug_level` 设置为 1 可以启用这些消息。这些参数可以通过 `/sys/module/ib_ipoib/` 中的文件在运行时进行控制。

`CONFIG_INFINIBAND_IPOIB_DEBUG` 同时也启用了 debugfs 虚拟文件系统中的文件。通过挂载这个文件系统（例如使用下面命令）：

    ```bash
    mount -t debugfs none /sys/kernel/debug
    ```

可以从 `/sys/kernel/debug/ipoib/ib0_mcg` 等文件中获取关于多播组的统计信息。

此选项对性能的影响几乎可以忽略，因此在正常操作中可以安全地启用此选项，并将 `debug_level` 设置为 0。
`CONFIG_INFINIBAND_IPOIB_DEBUG_DATA` 在数据路径中启用了更多的调试输出，当 `data_debug_level` 设置为 1 时。但是即使在输出被禁用的情况下，启用此配置选项仍然会影响性能，因为它在快速路径中添加了测试。
参考文献
==========

- 通过 InfiniBand 传输 IP（IPoIB）(RFC 4391)
  [http://ietf.org/rfc/rfc4391.txt](http://ietf.org/rfc/rfc4391.txt)

- InfiniBand 上的 IP（IPoIB）架构 (RFC 4392)
  [http://ietf.org/rfc/rfc4392.txt](http://ietf.org/rfc/rfc4392.txt)

- InfiniBand 上的 IP：连接模式 (RFC 4755)
  [http://ietf.org/rfc/rfc4755.txt](http://ietf.org/rfc/rfc4755.txt)
