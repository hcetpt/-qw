SPDX 许可证标识符: GPL-2.0

==================
AF_XDP 发送元数据
==================

本文档描述了如何在通过 :doc:`af_xdp` 发送数据包时启用卸载功能。有关如何在接收端访问类似元数据的信息，请参阅 :doc:`xdp-rx-metadata`。
总体设计
==============

元数据的头部空间通过 ``struct xdp_umem_reg`` 中的 ``tx_metadata_len`` 预留。因此，共享相同 umem 的每个套接字的元数据长度是相同的。元数据布局是一个固定的 UAPI，参见 ``include/uapi/linux/if_xdp.h`` 中的 ``union xsk_tx_metadata``。
因此，通常情况下，上面的 ``tx_metadata_len`` 字段应包含 ``sizeof(union xsk_tx_metadata)``。
头部空间和元数据本身应位于 umem 帧中 ``xdp_desc->addr`` 的正前方。在一个帧内，元数据布局如下所示：

           tx_metadata_len
     /                         \
    +-----------------+---------+----------------------------+
    | xsk_tx_metadata | padding |          payload           |
    +-----------------+---------+----------------------------+
                                ^
                                |
                          xdp_desc->addr

AF_XDP 应用程序可以请求大于 ``sizeof(struct xsk_tx_metadata)`` 的头部空间。内核会忽略填充部分（并且仍然使用 ``xdp_desc->addr - tx_metadata_len`` 来定位 ``xsk_tx_metadata``）。对于那些不需要携带任何元数据的帧（即没有 ``XDP_TX_METADATA`` 选项的帧），内核也会忽略元数据区域。
标志字段启用了特定的卸载功能：

- ``XDP_TXMD_FLAGS_TIMESTAMP``：请求设备将发送时间戳放入 ``union xsk_tx_metadata`` 中的 ``tx_timestamp`` 字段
- ``XDP_TXMD_FLAGS_CHECKSUM``：请求设备计算第 4 层校验和。``csum_start`` 指定了校验和开始的字节偏移量，而 ``csum_offset`` 指定了设备应该存储计算出的校验和的位置
除了上述标志外，为了触发卸载功能，第一个数据包的 ``struct xdp_desc`` 描述符应在 ``options`` 字段设置 ``XDP_TX_METADATA`` 标志。同时需要注意，在多缓冲区数据包中，只有第一块应该携带元数据。
软件发送校验和
====================

出于开发和测试目的，可以通过向 ``XDP_UMEM_REG`` UMEM 注册调用传递 ``XDP_UMEM_TX_SW_CSUM`` 标志来实现。
在这种情况下，在 ``XDK_COPY`` 模式下运行时，发送校验和将在 CPU 上计算。不要在生产环境中启用此选项，因为它会对性能产生负面影响。
查询设备能力
============================

每个设备都通过 netlink netdev 家族导出了其卸载功能。
参考 `Documentation/netlink/specs/netdev.yaml` 中的 ``xsk-flags`` 特性位掩码：
- ``tx-timestamp``：设备支持 ``XDP_TXMD_FLAGS_TIMESTAMP``
- ``tx-checksum``：设备支持 ``XDP_TXMD_FLAGS_CHECKSUM``

参阅 ``tools/net/ynl/samples/netdev.c`` 了解如何查询这些信息。
示例
=====

参见 ``tools/testing/selftests/bpf/xdp_hw_metadata.c``，这是一个处理 TX 元数据的示例程序。另外还可以参阅 https://github.com/fomichev/xskgen，这是一个更为基础的示例。
