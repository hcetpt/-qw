SPDX 许可证标识符: GPL-2.0

==================
AF_XDP 发送元数据
==================

本文档描述了如何在通过 :doc:`af_xdp` 发送数据包时启用卸载。关于如何在接收端访问类似的元数据，请参阅 :doc:`xdp-rx-metadata`
总体设计
==============

元数据的头部空间是通过 ``tx_metadata_len`` 在 ``struct xdp_umem_reg`` 中预留的。因此，对于共享同一 umem 的每个套接字，元数据长度相同。元数据布局是一个固定的 UAPI，参见 ``include/uapi/linux/if_xdp.h`` 中的 ``union xsk_tx_metadata``
因此，通常情况下，上述 ``tx_metadata_len`` 字段应包含 ``sizeof(union xsk_tx_metadata)``
头部空间和元数据本身应位于 umem 帧中 ``xdp_desc->addr`` 的正前方。在一个帧内，元数据布局如下所示::

           tx_metadata_len
     /                         \
    +-----------------+---------+----------------------------+
    | xsk_tx_metadata | padding |          payload           |
    +-----------------+---------+----------------------------+
                                ^
                                |
                          xdp_desc->addr

一个 AF_XDP 应用程序可以请求大于 ``sizeof(struct xsk_tx_metadata)`` 的头部空间。内核将忽略填充（并且仍然使用 ``xdp_desc->addr - tx_metadata_len`` 来定位 ``xsk_tx_metadata``）。对于那些不需要携带任何元数据的帧（即，没有 ``XDP_TX_METADATA`` 选项的帧），内核也会忽略元数据区域。
标志字段启用了特定的卸载：

- ``XDP_TXMD_FLAGS_TIMESTAMP``：请求设备将发送时间戳放入 ``union xsk_tx_metadata`` 的 ``tx_timestamp`` 字段
- ``XDP_TXMD_FLAGS_CHECKSUM``：请求设备计算第4层校验和。``csum_start`` 指定了校验和开始的字节偏移量，而 ``csum_offset`` 指定了设备存储计算出的校验和的位置
除了上述标志外，为了触发卸载，第一个数据包的 ``struct xdp_desc`` 描述符应在 ``options`` 字段中设置 ``XDP_TX_METADATA`` 位。此外，请注意，在多缓冲区数据包中，只有第一个分块应该携带元数据
软件 TX 校验和
====================

出于开发和测试目的，可以在 UMEM 注册调用 ``XDP_UMEM_REG`` 时传递 ``XDP_UMEM_TX_SW_CSUM`` 标志
在这种情况下，当运行在 ``XDK_COPY`` 模式下时，TX 校验和是在 CPU 上计算的。不要在生产环境中启用此选项，因为它会负面影响性能
查询设备功能
============================

每个设备都通过 netlink netdev 家族导出了其卸载功能
参考 `Documentation/netlink/specs/netdev.yaml` 中的 ``xsk-flags`` 特性位掩码：
- ``tx-timestamp``：设备支持 ``XDP_TXMD_FLAGS_TIMESTAMP``
- ``tx-checksum``：设备支持 ``XDP_TXMD_FLAGS_CHECKSUM``

查看 `tools/net/ynl/samples/netdev.c` 了解如何查询这些信息。
示例
=====

参见 `tools/testing/selftests/bpf/xdp_hw_metadata.c`，其中包含一个处理 TX 元数据的示例程序。另外，也可以查看 https://github.com/fomichev/xskgen 获取一个更基础的示例。
