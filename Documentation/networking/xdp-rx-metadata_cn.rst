### XDP RX 元数据

本文档描述了如何使用一组辅助函数使 eXpress Data Path (XDP) 程序能够访问与数据包相关的硬件元数据，以及如何将这些元数据传递给其他消费者。

#### 总体设计

XDP 可以通过一组内核函数（kfuncs）来操作 XDP 帧中的元数据。每个希望暴露额外数据包元数据的设备驱动程序都可以实现这些 kfuncs。这些 kfuncs 在 `include/net/xdp.h` 中通过 `XDP_METADATA_KFUNC_xxx` 定义。
目前支持以下 kfuncs。未来随着更多元数据的支持，这个集合将会扩展：

- `bpf_xdp_metadata_rx_timestamp`
- `bpf_xdp_metadata_rx_hash`
- `bpf_xdp_metadata_rx_vlan_tag`

一个 XDP 程序可以使用这些 kfuncs 将元数据读入栈变量中供自己使用。或者，为了将元数据传递给其他消费者，XDP 程序可以将其存储在数据包前面携带的元数据区域中。并非所有数据包都必须提供请求的元数据，在这种情况下，驱动程序返回 `-ENODATA`。
并非所有 kfuncs 都需要由设备驱动程序实现；当未实现时，默认返回 `-EOPNOTSUPP` 的 kfuncs 将被用来指示设备驱动程序未实现该 kfunc。
在一个 XDP 帧中，通过 `xdp_buff` 访问的元数据布局如下所示：

```
+----------+-----------------+------+
| headroom | custom metadata | data |
+----------+-----------------+------+
             ^                 ^
             |                 |
   xdp_buff->data_meta   xdp_buff->data
```

XDP 程序可以选择任意格式将单个元数据项存储到这个 `data_meta` 区域中。元数据的后续消费者必须通过某种协议外的方式（如 AF_XDP 使用案例中所述）同意该格式。

#### AF_XDP

`af_xdp` 使用案例意味着存在一个合同，即重定向 XDP 帧到 `AF_XDP` 套接字 (`XSK`) 的 BPF 程序和最终消费者之间的合同。因此，BPF 程序通过 `bpf_xdp_adjust_meta` 手动分配固定数量的元数据字节，并调用一部分 kfuncs 来填充它。用户空间 `XSK` 消费者计算 `xsk_umem__get_data() - METADATA_SIZE` 来定位这些元数据。
注意，`xsk_umem__get_data` 在 `libxdp` 中定义，而 `METADATA_SIZE` 是一个应用程序特定的常量（`AF_XDP` 接收描述符并未显式携带元数据的大小）。
以下是 `AF_XDP` 消费者的布局（注意缺少 `data_meta` 指针）：

```
+----------+-----------------+------+
| headroom | custom metadata | data |
+----------+-----------------+------+
                               ^
                               |
                        rx_desc->address
```

#### XDP_PASS

这是经过 XDP 程序处理的数据包传递到内核的路径。内核从 `xdp_buff` 内容创建 `skb`。目前，每个驱动程序都有自定义的内核代码来解析描述符并填充 `skb` 元数据，当进行 `xdp_buff->skb` 转换时，XDP 元数据不会被内核用于构建 `skbs`。然而，TC-BPF 程序可以通过 `data_meta` 指针访问 XDP 元数据区域。
将来，我们希望支持一种情况，即 XDP 程序可以覆盖一些用于构建 `skbs` 的元数据。
``bpf_redirect_map`` 可以将帧重定向到不同的设备。某些设备（如虚拟以太网链路）支持在重定向之后运行第二个XDP程序。然而，最终的消费者无法访问原始的硬件描述符，也无法访问任何原始元数据。同样的规则也适用于安装在devmaps和cpumaps中的XDP程序。

这意味着对于被重定向的数据包，目前仅支持自定义元数据，这些元数据需要由初始的XDP程序在重定向之前准备好。如果帧最终传递给内核，则从该帧创建的``skb``中不会填充任何硬件元数据。如果这样的数据包稍后被重定向到一个``XSK``中，那么它也只能访问自定义元数据。

### bpf_tail_call

目前不支持将访问元数据kfuncs的程序添加到``BPF_MAP_TYPE_PROG_ARRAY``中。

### 支持的设备

可以通过netlink查询特定netdev实现的kfunc。参见``Documentation/netlink/specs/netdev.yaml``中的``xdp-rx-metadata-features``属性集。

### 示例

参见``tools/testing/selftests/bpf/progs/xdp_metadata.c``和``tools/testing/selftests/bpf/prog_tests/xdp_metadata.c``，了解处理XDP元数据的BPF程序示例。
