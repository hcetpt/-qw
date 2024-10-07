SPDX 许可证标识符: GPL-2.0

===============
XDP RX 元数据
===============

本文档描述了如何使用一组辅助函数来访问与数据包相关的硬件元数据，以及如何将这些元数据传递给其他消费者。
通用设计
==============

XDP 可以通过一组 kfuncs 来操作 XDP 帧中的元数据
每个希望暴露额外数据包元数据的设备驱动程序可以实现这些 kfuncs。这组 kfuncs 在 `include/net/xdp.h` 中通过 `XDP_METADATA_KFUNC_xxx` 声明
目前支持以下 kfuncs。未来随着更多元数据的支持，这个集合将会扩大：

.. kernel-doc:: net/core/xdp.c
   :identifiers: bpf_xdp_metadata_rx_timestamp

.. kernel-doc:: net/core/xdp.c
   :identifiers: bpf_xdp_metadata_rx_hash

.. kernel-doc:: net/core/xdp.c
   :identifiers: bpf_xdp_metadata_rx_vlan_tag

一个 XDP 程序可以使用这些 kfuncs 将元数据读入栈变量中供自身使用。或者，为了将元数据传递给其他消费者，XDP 程序可以将其存储在数据包前的数据元数据区域中。并不是所有数据包都会包含请求的元数据，在这种情况下，驱动程序会返回 `-ENODATA`
并不是所有的 kfuncs 都需要由设备驱动程序实现；如果没有实现，则默认返回 `-EOPNOTSUPP` 的 kfuncs 将被用来指示设备驱动程序未实现此 kfunc
在一个 XDP 帧中，元数据布局（通过 `xdp_buff` 访问）如下所示：

```
  +----------+-----------------+------+
  | headroom | custom metadata | data |
  +----------+-----------------+------+
             ^                 ^
             |                 |
   xdp_buff->data_meta   xdp_buff->data
```

XDP 程序可以选择将单个元数据项存储到这个 `data_meta` 区域中的任何格式。元数据的后续消费者必须通过某种外部协议达成一致（如 AF_XDP 使用案例，请参见下文）

AF_XDP
======

:doc:`af_xdp` 使用案例意味着 BPF 程序将 XDP 帧重定向到 `AF_XDP` 套接字 (`XSK`) 与最终消费者之间存在合同关系。因此，BPF 程序通过 `bpf_xdp_adjust_meta` 手动分配固定数量的元数据字节，并调用一组 kfuncs 来填充它。用户空间的 `XSK` 消费者计算 `xsk_umem__get_data() - METADATA_SIZE` 来定位该元数据
注意，`xsk_umem__get_data` 定义在 `libxdp` 中，而 `METADATA_SIZE` 是应用程序特定的常量（`AF_XDP` 接收描述符不明确携带元数据大小）
以下是 `AF_XDP` 消费者的布局（注意缺少 `data_meta` 指针）：

```
  +----------+-----------------+------+
  | headroom | custom metadata | data |
  +----------+-----------------+------+
                               ^
                               |
                        rx_desc->address
```

XDP_PASS
========

这是 XDP 程序处理后的数据包传递到内核的路径。内核根据 `xdp_buff` 内容创建 `skb`。目前，每个驱动程序都有自定义内核代码来解析描述符并填充 `skb` 元数据，当进行 `xdp_buff->skb` 转换时，内核不会使用 XDP 元数据来构建 `skbs`。然而，TC-BPF 程序可以通过 `data_meta` 指针访问 XDP 元数据区域
未来，我们希望支持一种情况，即 XDP 程序可以覆盖用于构建 `skbs` 的一些元数据。
### bpf_redirect_map
``bpf_redirect_map`` 可以将帧重定向到不同的设备。
某些设备（如虚拟以太网链路）支持在重定向后运行第二个 XDP 程序。然而，最终的消费者无法访问原始硬件描述符，也无法访问任何原始元数据。同样的规则适用于安装在 devmaps 和 cpumaps 中的 XDP 程序。
这意味着对于重定向的数据包，目前只支持自定义元数据，这些元数据需要由初始 XDP 程序在重定向之前准备好。如果帧最终传递给内核，则从该帧创建的 ``skb`` 不会填充任何硬件元数据。如果这样的数据包之后被重定向到一个 ``XSK`` 中，那么这个 ``XSK`` 也只会访问到自定义元数据。

### bpf_tail_call
将访问元数据 kfuncs 的程序添加到 ``BPF_MAP_TYPE_PROG_ARRAY`` 目前是不支持的。

### 支持的设备
可以通过 netlink 查询特定 netdev 实现了哪些 kfunc。详见 ``Documentation/netlink/specs/netdev.yaml`` 中的 ``xdp-rx-metadata-features`` 属性集。

### 示例
有关处理 XDP 元数据的 BPF 程序示例，请参见 ``tools/testing/selftests/bpf/progs/xdp_metadata.c`` 和 ``tools/testing/selftests/bpf/prog_tests/xdp_metadata.c``。
