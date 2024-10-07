.. SPDX-License-Identifier: GPL-2.0 OR Linux-OpenIB
.. include:: <isonum.txt>

================
Ethtool 计数器
================

:版权: |copy| 2023，NVIDIA CORPORATION & AFFILIATES。保留所有权利。
内容
========

- `概述`_
- `组`_
- `类型`_
- `描述`_

概述
========

根据计数器所在的位置，有多个计数器组。此外，每个计数器组可能有不同的计数器类型。这些计数器组基于网络设置中的某个组件（如下图所示）来描述：

```
                                                  ----------------------------------------
                                                  |                                      |
    ----------------------------------------    ---------------------------------------- |
    |              虚拟机监控器              |    |                  虚拟机                  | |
    |                                      |    |                                      | |
    | -------------------  --------------- |    | -------------------  --------------- | |
    | | 以太网驱动程序 |  | RDMA 驱动程序 | |    | | 以太网驱动程序 |  | RDMA 驱动程序 | | |
    | -------------------  --------------- |    | -------------------  --------------- | |
    |           |                 |        |    |           |                 |        | |
    |           -------------------        |    |           -------------------        | |
    |                   |                  |    |                   |                  |--
    ----------------------------------------    ----------------------------------------
                        |                                           |
            -------------               -----------------------------
            |                           |
         ------                      ------ ------ ------         ------      ------      ------
    -----| PF |----------------------| VF |-| VF |-| VF |-----  --| PF |--- --| PF |--- --| PF |---
    |    ------                      ------ ------ ------    |  | ------  | | ------  | | ------  |
    |                                                        |  |         | |         | |         |
    |                                                        |  |         | |         | |         |
    |                                                        |  |         | |         | |         |
    | eSwitch                                                |  | eSwitch | | eSwitch | | eSwitch |
    ----------------------------------------------------------  ----------- ----------- -----------
               -------------------------------------------------------------------------------
               |                                                                             |
               |                                                                             |
               | 上行链路（无计数器）                                                        |
               -------------------------------------------------------------------------------
                       ---------------------------------------------------------------
                       |                                                             |
                       |                                                             |
                       | MPFS（无计数器）                                          |
                       ---------------------------------------------------------------
                                                     |
                                                     |
                                                     | 端口

组
======

环形缓冲区
  由驱动堆栈填充的软件计数器
网络设备
  软件环形缓冲区计数器的汇总
vPort 计数器
  因转向或无缓冲区而导致的流量计数器和丢包。可能表明 NIC 存在问题。这些计数器包括以太网流量计数器（包括原始以太网）和 RDMA/RoCE 流量计数器
物理端口计数器
  收集有关 PF 和 VF 的统计信息的计数器。可能表明 NIC、链路或网络存在问题。此测量点包含标准化计数器的信息，如 IEEE 802.3、RFC2863、RFC 2819、RFC 3635 以及更多额外计数器，如流控制、FEC 等。物理端口计数器不会暴露给虚拟机
优先级端口计数器
  每个优先级每个端口的一组物理端口计数器

类型
=====

计数器分为三种类型：
流量信息计数器
  计算流量的计数器。这些计数器可用于负载估算或一般调试
流量加速计数器
  计算由 Mellanox 驱动程序或硬件加速的流量的计数器。这些计数器是信息计数器集的附加层，并且相同的流量同时在信息计数器和加速计数器中被计算
.. [#accel] 流量加速计数器
错误计数器
  这些计数器的增加可能表明存在问题。每个计数器都有相应的解释和纠正措施。
统计信息可以通过 `ip link` 或 `ethtool` 命令获取。`ethtool` 提供更详细的信息。

    ip –s link show <if-name>
    ethtool -S <if-name>

描述
============

XSK、PTP 和 QoS 计数器与之前定义的计数器类似，将不再单独列出。例如，`ptp_tx[i]_packets` 不会明确记录，因为 `tx[i]_packets` 已经描述了这两种计数器的行为，不同之处在于 `ptp_tx[i]_packets` 只在使用精确时间协议时进行计数。

环/网卡计数器
----------------------------
以下计数器按环或软件端口提供：

这些计数器提供了有关由 NIC 加速的流量数量的信息。计数器除了标准计数器（已对其进行计数）之外还对加速流量进行计数（即加速流量被计数两次）。下表中的计数器名称同时指环计数器和端口计数器。环计数器的表示包括不带括号的 [i] 索引。端口计数器的表示不包括 [i]。计数器名称 `rx[i]_packets` 对于环 0 将显示为 `rx0_packets`，对于软件端口则显示为 `rx_packets`。

.. flat-table:: 环/软件端口计数器表
   :widths: 2 3 1

   * - 计数器
     - 描述
     - 类型

   * - `rx[i]_packets`
     - 在环 i 上接收到的数据包数量
     - 信息性

   * - `rx[i]_bytes`
     - 在环 i 上接收到的字节数量
     - 信息性

   * - `tx[i]_packets`
     - 在环 i 上发送的数据包数量
     - 信息性

   * - `tx[i]_bytes`
     - 在环 i 上发送的字节数量
     - 信息性
- 信息统计

   * - `tx[i]_recover`
     - 发送队列 i 上 SQ 恢复的次数
- 错误

   * - `tx[i]_cqes`
     - 发送队列 i 上 SQ 触发的 CQE 事件数
- 信息统计

   * - `tx[i]_cqe_err`
     - 发送队列 i 上 SQ 遇到的错误 CQE 数量
- 错误

   * - `tx[i]_tso_packets`
     - 发送队列 i 上发送的 TSO 数据包数量 [#accel]_
- 加速

   * - `tx[i]_tso_bytes`
     - 发送队列 i 上发送的 TSO 字节数 [#accel]_
- 加速

   * - `tx[i]_tso_inner_packets`
     - 发送队列 i 上发送的带有内部封装的 TSO 数据包数量 [#accel]_
- 加速

   * - `tx[i]_tso_inner_bytes`
     - 发送队列 i 上发送的带有内部封装的 TSO 字节数 [#accel]_
- 加速

   * - `rx[i]_gro_packets`
     - 使用硬件加速 GRO 处理的接收数据包数量。接收队列 i 上硬件 GRO 卸载的数据包数量。仅计算真正的 GRO 数据包：即在具有 GRO 计数大于 1 的 SKB 中的数据包
- 加速

   * - `rx[i]_gro_bytes`
     - 使用硬件加速 GRO 处理的接收字节数。接收队列 i 上硬件 GRO 卸载的字节数。仅计算真正的 GRO 数据包：即在具有 GRO 计数大于 1 的 SKB 中的数据包
- 加速

   * - `rx[i]_gro_skbs`
     - 从硬件加速 GRO 构建的 GRO SKB 数量。仅计算 GRO 计数大于 1 的 SKB
- 信息性

   * - `rx[i]_gro_large_hds`
     - 使用硬件加速的GRO接收的大头部数据包数量，这些数据包需要额外分配内存

- 信息性

   * - `rx[i]_hds_nodata_packets`
     - 在头/数据分离模式下仅包含头部的数据包数量

- 信息性

   * - `rx[i]_hds_nodata_bytes`
     - 在头/数据分离模式下仅包含头部的数据包字节数量

- 信息性

   * - `rx[i]_lro_packets`
     - 在环i上接收到的LRO数据包数量

- 加速

   * - `rx[i]_lro_bytes`
     - 在环i上接收到的LRO字节数量

- 加速

   * - `rx[i]_ecn_mark`
     - 接收到的带有ECN标记的数据包数量

- 信息性

   * - `rx_oversize_pkts_buffer`
     - 由于长度超出设备为传入流量分配的软件缓冲区大小而在接收队列中被丢弃的数据包数量。这可能意味着设备的MTU大于软件缓冲区大小

- 错误

   * - `rx_oversize_pkts_sw_drop`
     - 由于CQE数据大于MTU大小而在软件中被丢弃的接收到的数据包数量

- 错误

   * - `rx[i]_csum_unnecessary`
     - 在环i上接收到的带有`CHECKSUM_UNNECESSARY`标记的数据包数量

- 加速

   * - `rx[i]_csum_unnecessary_inner`
     - 在环i上接收到的内层封装带有`CHECKSUM_UNNECESSARY`标记的数据包数量
- 加速

   * - `rx[i]_csum_none`
     - 在环路 i 上接收到的带有 `CHECKSUM_NONE` 的数据包 [#accel]_
- 加速

   * - `rx[i]_csum_complete`
     - 在环路 i 上接收到的带有 `CHECKSUM_COMPLETE` 的数据包 [#accel]_
- 加速

   * - `rx[i]_csum_complete_tail`
     - 接收到的数据包数量，这些数据包已经计算了校验和，可能需要填充，并且能够使用 `CHECKSUM_PARTIAL` 进行填充
- 信息

   * - `rx[i]_csum_complete_tail_slow`
     - 需要超过八字节填充以进行校验和计算的接收数据包数量
- 信息

   * - `tx[i]_csum_partial`
     - 在环路 i 上发送的带有 `CHECKSUM_PARTIAL` 的数据包 [#accel]_
- 加速

   * - `tx[i]_csum_partial_inner`
     - 在环路 i 上发送的带有内部封装和 `CHECKSUM_PARTIAL` 的数据包 [#accel]_
- 加速

   * - `tx[i]_csum_none`
     - 在环路 i 上发送的没有硬件校验和加速的数据包
- 信息

   * - `tx[i]_stopped` / `tx_queue_stopped` [#ring_global]_
     - 环路 i 上发送队列（SQ）已满的事件。如果此计数器增加，请检查分配用于传输的缓冲区数量
- 信息

   * - `tx[i]_wake` / `tx_queue_wake` [#ring_global]_
     - 环路 i 上发送队列（SQ）已满后又变得不满的事件
- 信息

   * - `tx[i]_dropped` / `tx_queue_dropped` [#ring_global]_
     - 在环路 i 上由于 DMA 映射失败而被丢弃的发送数据包。如果此计数器增加，请检查分配用于传输的缓冲区数量
- 错误

   * - `tx[i]_nop`
     - 由于循环缓冲区末尾到达而插入到 SQ（与环 i 相关）中的 nop WQE（空 WQE）的数量。当接近循环缓冲区的末尾时，驱动程序可能会添加这些空 WQE 以避免处理一个 WQE 开始于队列末尾并结束于队列开头的状态。这是一种正常情况。

- 信息

   * - `tx[i]_timestamps`
     - 在设备的 DMA 层被硬件时间戳的发送数据包数量。
   
- 信息

   * - `tx[i]_added_vlan_packets`
     - 发送的数据包中，VLAN 标签插入卸载到硬件的数量。
   
- 加速

   * - `rx[i]_removed_vlan_packets`
     - 接收的数据包中，VLAN 标签剥离卸载到硬件的数量。
   
- 加速

   * - `rx[i]_wqe_err`
     - 环 i 上接收到的错误操作码的数量。
   
- 错误

   * - `rx[i]_mpwqe_frag`
     - 由于未能分配复合页面而使用了分段 MPWQE（多数据包 WQE）的 WQE 数量。如果此计数器增加，可能表明没有足够的内存来分配大页面，驱动程序分配了分段页面。这不是异常状况。
   
- 信息

   * - `rx[i]_mpwqe_filler_cqes`
     - 环 i 上发出的填充 CQE 事件的数量。
   
- 信息

   * - `rx[i]_mpwqe_filler_strides`
     - 环 i 上由填充 CQE 消耗的步长数量。
   
- 信息

   * - `tx[i]_mpwqe_blks`
     - 从 Multi-Packet WQEs (mpwqe) 处理的发送块数量。
   
- 信息

   * - `tx[i]_mpwqe_pkts`
     - 从 Multi-Packet WQEs (mpwqe) 处理的发送数据包数量。
### 信息统计

* - `rx[i]_cqe_compress_blks`
  - 环i上带有CQE压缩的接收块数量 [#accel]_

### 加速

* - `rx[i]_cqe_compress_pkts`
  - 环i上带有CQE压缩的接收数据包数量 [#accel]_

* - `rx[i]_arfs_add`
  - 添加到设备用于直接RQ导向的aRFS流规则数量（环i） [#accel]_

* - `rx[i]_arfs_request_in`
  - 请求移动到环i用于直接RQ导向的流规则数量 [#accel]_

* - `rx[i]_arfs_request_out`
  - 请求从环i移出的流规则数量 [#accel]_

* - `rx[i]_arfs_expired`
  - 已过期并移除的流规则数量 [#accel]_

* - `tx[i]_xmit_more`
  - 设置了`xmit_more`标志且未触发门铃的发送数据包数量（环i） [#accel]_

* - `ch[i]_poll`
  - 通道i上的NAPI轮询调用次数

### 错误

* - `rx[i]_arfs_err`
  - 添加到流表失败的流规则数量

* - `rx[i]_recover`
  - RQ恢复次数

* - `rx[i]_arfs_err`
  - 添加到流表失败的流规则数量

* - `rx[i]_recover`
  - RQ恢复次数
- 信息统计

   * - `ch[i]_arm`
     - 在通道 i 上，NAPI 轮询函数完成并启动完成队列的次数
- 信息统计

   * - `ch[i]_aff_change`
     - 在通道 i 上，由于亲和性变化，NAPI 轮询函数显式停止在一个 CPU 上执行的次数
- 信息统计

   * - `ch[i]_events`
     - 在通道 i 的完成队列上的硬中断事件数
- 信息统计

   * - `ch[i]_eq_rearm`
     - EQ 恢复的次数
- 错误

   * - `ch[i]_force_irq`
     - 通过向 ICOSQ 发送 NOP 触发 NAPI 的次数（由 XSK 唤醒引起）
- 加速

   * - `rx[i]_congst_umr`
     - 在环 i 上，由于拥塞导致的未完成 UMR 请求被延迟的次数
- 信息统计

   * - `rx_pp_alloc_fast`
     - 成功的快速路径分配次数
- 信息统计

   * - `rx_pp_alloc_slow`
     - 慢速路径的第 0 级分配次数
- 信息统计

   * - `rx_pp_alloc_slow_high_order`
     - 慢速路径的高级分配次数
- 信息统计

   * - `rx_pp_alloc_empty`
     - 当指针环为空时，计数器增加，因此被迫进行慢速路径分配
- 信息性

   * - `rx_pp_alloc_refill`
     - 当触发缓存填充的分配发生时，计数器递增

- 信息性

   * - `rx_pp_alloc_waive`
     - 当从指针环中获取的页面由于NUMA不匹配而无法添加到缓存时，计数器递增

- 信息性

   * - `rx_pp_recycle_cached`
     - 当回收页面池缓存中的页面时，计数器递增

- 信息性

   * - `rx_pp_recycle_cache_full`
     - 当页面池缓存已满时，计数器递增

- 信息性

   * - `rx_pp_recycle_ring`
     - 当页面放入指针环时，计数器递增

- 信息性

   * - `rx_pp_recycle_ring_full`
     - 当指针环已满导致页面从页面池释放时，计数器递增

- 信息性

   * - `rx_pp_recycle_released_ref`
     - 当引用计数大于1时页面被释放（未回收）时，计数器递增

- 信息性

   * - `rx[i]_xsk_buff_alloc_err`
     - 在XSK RQ上下文中分配skb或XSK缓冲区失败的次数

- 错误

   * - `rx[i]_xdp_tx_xmit`
     - 由于XDP程序执行`XDP_TX`操作（反弹）而转发回端口的数据包数量。这些数据包不会被其他软件计数器统计，但会被物理端口和vPort计数器统计

- 信息性

   * - `rx[i]_xdp_tx_mpwqe`
     - 在RQ上下文中由网卡传输并由网卡执行`XDP_TX`操作的多包WQE的数量
- 加速

  * - `rx[i]_xdp_tx_inlnw`
    - 在 WQE 中可以内联数据并在接收队列上下文中通过 `XDP_TX` 发送的数据段数量

- 加速

  * - `rx[i]_xdp_tx_nops`
    - 接收到并发布到 XDP 发送队列的 NOP WQEBB（WQE 构建块）的数量

- 加速

  * - `rx[i]_xdp_tx_full`
    - 本应由于 `XDP_TX` 动作而转发回端口但由于发送队列已满而被丢弃的数据包数量。这些数据包不计入其他软件计数器。这些数据包由物理端口和虚拟端口计数器统计。您可以通过增加接收队列数量并将流量分散到所有队列上，或者增大接收环大小来解决这个问题。

- 错误

  * - `rx[i]_xdp_tx_err`
    - 在 RX 环或 `XDP_TX` 环上发生 `XDP_TX` 错误（如帧太长或帧太短）的次数

- 错误

  * - `rx[i]_xdp_tx_cqes` / `rx_xdp_tx_cqe` [#ring_global]_
    - 在 `XDP_TX` 环的完成队列上接收到的完成数量

- 信息

  * - `rx[i]_xdp_drop`
    - 由于 XDP 程序执行 `XDP_DROP` 动作而被丢弃的数据包数量。这些数据包不计入其他软件计数器。这些数据包由物理端口和虚拟端口计数器统计

- 信息

  * - `rx[i]_xdp_redirect`
    - 在环 i 上触发 XDP 重定向动作的次数

- 加速

  * - `tx[i]_xdp_xmit`
    - 被重定向到接口（由于 XDP 重定向）的数据包数量。这些数据包不计入其他软件计数器。这些数据包由物理端口和虚拟端口计数器统计

- 信息

  * - `tx[i]_xdp_full`
    - 由于 XDP 重定向而被重定向到接口但因发送队列已满而被丢弃的数据包数量。这些数据包不计入其他软件计数器。您可以增加发送队列的大小以解决这个问题。
- 信息统计

   * - `tx[i]_xdp_mpwqe`
     - 被卸载到网卡的多包工作队列条目（WQEs），这些条目是从其他网络设备通过 `XDP_REDIRECT` 重定向过来的
- 加速

   * - `tx[i]_xdp_inlnw`
     - 数据段能够内联在 WQE 中的工作队列数据段数量，这些数据段是从其他网络设备通过 `XDP_REDIRECT` 重定向过来的
- 加速

   * - `tx[i]_xdp_nops`
     - 被发布到发送队列（SQ）的空操作（NOP）WQEBBs（WQE构建块）的数量，这些WQEBBs是从其他网络设备通过 `XDP_REDIRECT` 重定向过来的
- 加速

   * - `tx[i]_xdp_err`
     - 因为 `XDP_REDIRECT` 重定向到接口但由于错误（如帧太长或太短）而被丢弃的数据包数量
- 错误

   * - `tx[i]_xdp_cqes`
     - 在完成队列（CQ）上接收到的重定向到接口的数据包完成数量（由于 XDP 重定向）
- 信息统计

   * - `tx[i]_xsk_xmit`
     - 使用 XSK 零拷贝功能传输的数据包数量
- 加速

   * - `tx[i]_xsk_mpwqe`
     - 被卸载到网卡的多包工作队列条目（WQEs），这些条目是从其他网络设备通过 `XDP_REDIRECT` 重定向过来的
- 加速

   * - `tx[i]_xsk_inlnw`
     - 数据段能够内联在 WQE 中的工作队列数据段数量，这些数据段是使用 XSK 零拷贝功能传输的
- 加速

   * - `tx[i]_xsk_full`
     - 在 XSK 零拷贝模式下，当发送队列（SQ）满时触发门铃的次数
- 错误

   * - `tx[i]_xsk_err`
     - 在 XSK 零拷贝模式下发生的错误数量，例如数据大小超过最大传输单元（MTU）大小的情况
- 错误

   * - `tx[i]_xsk_cqes`
     - 在 XSK 零复制模式下处理的 CQE 数量

- 加速

   * - `tx_tls_ctx`
     - 添加到设备用于加密的 TLS 发送硬件卸载上下文数量
- 加速

   * - `tx_tls_del`
     - 从设备中移除的 TLS 发送硬件卸载上下文数量（连接已关闭）
- 加速

   * - `tx_tls_pool_alloc`
     - 在 TLS 硬件卸载池中成功分配工作单元的次数
- 加速

   * - `tx_tls_pool_free`
     - 在 TLS 硬件卸载池中释放工作单元的次数
- 加速

   * - `rx_tls_ctx`
     - 添加到设备用于解密的 TLS 接收硬件卸载上下文数量
- 加速

   * - `rx_tls_del`
     - 从设备中删除的 TLS 接收硬件卸载上下文数量（连接已完成）
- 加速

   * - `rx[i]_tls_decrypted_packets`
     - 成功解密的属于 TLS 流的接收数据包数量
- 加速

   * - `rx[i]_tls_decrypted_bytes`
     - 成功解密的 TLS 负载字节数量
- 加速

   * - `rx[i]_tls_resync_req_pkt`
     - 收到的带有重新同步请求的 TLS 数据包数量
- 加速

   * - `rx[i]_tls_resync_req_start`
     - TLS 异步重同步请求开始的次数
- 加速

   * - `rx[i]_tls_resync_req_end`
     - TLS 异步重同步请求成功结束并提供硬件跟踪的 TCP 序列号的次数
- 加速

   * - `rx[i]_tls_resync_req_skip`
     - TLS 异步重同步请求过程开始但未成功结束的次数
- 错误

   * - `rx[i]_tls_resync_res_ok`
     - TLS 重同步响应调用驱动程序成功处理的次数
- 加速

   * - `rx[i]_tls_resync_res_retry`
     - 当 ICOSQ 满时，TLS 重同步响应调用驱动程序重新尝试的次数
- 错误

   * - `rx[i]_tls_resync_res_skip`
     - TLS 重同步响应调用驱动程序未能成功终止的次数
- 错误

   * - `rx[i]_tls_err`
     - CQE TLS 卸载出现问题的次数
- 错误

   * - `tx[i]_tls_encrypted_packets`
     - 由内核进行 TLS 加密的发送数据包数量
- 加速

   * - `tx[i]_tls_encrypted_bytes`
     - 由内核进行 TLS 加密的发送字节数量
- 加速

   * - `tx[i]_tls_ooo`
     - 在环 i 上处理乱序的 TLS SQE 分片的次数
### 加速

* - `tx[i]_tls_dump_packets`
  - 通过直接内存访问（DMA）从网卡复制的已解密TLS数据包数量

* - `tx[i]_tls_dump_bytes`
  - 通过直接内存访问（DMA）从网卡复制的已解密TLS字节数量

* - `tx[i]_tls_resync_bytes`
  - 请求重新同步以便进行解密的TLS字节数量

* - `tx[i]_tls_skip_no_sync_data`
  - 可以安全跳过的或不需要解密的TLS发送数据数量

* - `tx[i]_tls_drop_no_sync_data`
  - 由于TLS数据重传而丢弃的TLS发送数据数量

* - `ptp_cq[i]_abort`
  - 在精确时间协议中，由于端口时间戳与CQE时间戳之间的偏差大于128秒而导致需要跳过CQE的次数

### 错误

* - `ptp_cq[i]_abort_abs_diff_ns`
  - 在精确时间协议中，当端口时间戳与CQE时间戳之间的差异大于128秒时的时间差累积

* - `ptc_cq[i]_late_cqe`
  - 当CQE在预期时间内未到达PTP时间戳队列时的次数，通常设备会确保在此时间段内不发布CQE

* - `ptp_cq[i]_lost_cqe`
  - 由于时间差导致预期不会在PTP时间戳队列中接收到CQE的次数；如果此类CQE被接收到，则`ptp_cq[i]_late_cqe`计数器会递增

### 注释

.. [#ring_global] 对应的环形缓冲区和全局计数器名称不同（即没有遵循通用命名方案）
vPort 计数器
--------------
连接到 eSwitch 的 NIC 端口上的计数器

.. flat-table:: vPort 计数器表
   :widths: 2 3 1

   * - 计数器
     - 描述
     - 类型

   * - `rx_vport_unicast_packets`
     - 接收到的单播数据包，导向端口，包括原始以太网 QP/DPDK 流量，不包括 RDMA 流量
- 参考信息

   * - `rx_vport_unicast_bytes`
     - 接收到的单播字节，导向端口，包括原始以太网 QP/DPDK 流量，不包括 RDMA 流量
- 参考信息

   * - `tx_vport_unicast_packets`
     - 发送的单播数据包，从端口导向，包括原始以太网 QP/DPDK 流量，不包括 RDMA 流量
- 参考信息

   * - `tx_vport_unicast_bytes`
     - 发送的单播字节，从端口导向，包括原始以太网 QP/DPDK 流量，不包括 RDMA 流量
- 参考信息

   * - `rx_vport_multicast_packets`
     - 接收到的组播数据包，导向端口，包括原始以太网 QP/DPDK 流量，不包括 RDMA 流量
- 参考信息

   * - `rx_vport_multicast_bytes`
     - 接收到的组播字节，导向端口，包括原始以太网 QP/DPDK 流量，不包括 RDMA 流量
- 参考信息

   * - `tx_vport_multicast_packets`
     - 发送的组播数据包，从端口导向，包括原始以太网 QP/DPDK 流量，不包括 RDMA 流量
- 参考信息

   * - `tx_vport_multicast_bytes`
     - 发送的组播字节，从端口导向，包括原始以太网 QP/DPDK 流量，不包括 RDMA 流量
- 参考信息

   * - `rx_vport_broadcast_packets`
     - 接收到的广播数据包，导向端口，包括原始以太网 QP/DPDK 流量，不包括 RDMA 流量
- 参考信息
- 信息性

   * - `rx_vport_broadcast_bytes`
     - 接收到的广播字节数，导向端口，包括原始以太网 QP/DPDK 流量，不包括 RDMA 流量
- 信息性

   * - `tx_vport_broadcast_packets`
     - 从端口发出的广播数据包数，包括原始以太网 QP/DPDK 流量，不包括 RDMA 流量
- 信息性

   * - `tx_vport_broadcast_bytes`
     - 从端口发出的广播字节数，包括原始以太网 QP/DPDK 流量，不包括 RDMA 流量
- 信息性

   * - `rx_vport_rdma_unicast_packets`
     - 接收到的 RDMA 单播数据包数，导向端口（计数器统计 RoCE/UD/RC 流量）[#accel]_
- 加速

   * - `rx_vport_rdma_unicast_bytes`
     - 接收到的 RDMA 单播字节数，导向端口（计数器统计 RoCE/UD/RC 流量）[#accel]_
- 加速

   * - `tx_vport_rdma_unicast_packets`
     - 从端口发出的 RDMA 单播数据包数（计数器统计 RoCE/UD/RC 流量）[#accel]_
- 加速

   * - `tx_vport_rdma_unicast_bytes`
     - 从端口发出的 RDMA 单播字节数（计数器统计 RoCE/UD/RC 流量）[#accel]_
- 加速

   * - `rx_vport_rdma_multicast_packets`
     - 接收到的 RDMA 组播数据包数，导向端口（计数器统计 RoCE/UD/RC 流量）[#accel]_
- 加速

   * - `rx_vport_rdma_multicast_bytes`
     - 接收到的 RDMA 组播字节数，导向端口（计数器统计 RoCE/UD/RC 流量）[#accel]_
- 加速

   * - `tx_vport_rdma_multicast_packets`
     - 从端口发出的 RDMA 组播数据包数（计数器统计 RoCE/UD/RC 流量）[#accel]_
- 加速

   * - `tx_vport_rdma_multicast_bytes`
     - 从端口传输的RDMA组播字节数（计数器统计RoCE/UD/RC流量）[#accel]_
- 加速

   * - `vport_loopback_packets`
     - 环回的单播、组播和广播数据包（接收并传输），IB/Eth [#accel]_
- 加速

   * - `vport_loopback_bytes`
     - 环回的单播、组播和广播字节数（接收并传输），IB/Eth [#accel]_
- 加速

   * - `rx_steer_missed_packets`
     - 被NIC接收到但因未匹配NIC流表中的任何流而被丢弃的数据包数量
- 错误

   * - `rx_packets`
     - 仅代表：由hypervisor处理的接收数据包
- 信息

   * - `rx_bytes`
     - 仅代表：由hypervisor处理的接收字节数
- 信息

   * - `tx_packets`
     - 仅代表：由hypervisor处理的传输数据包
- 信息

   * - `tx_bytes`
     - 仅代表：由hypervisor处理的传输字节数
- 信息

   * - `dev_internal_queue_oob`
     - 由于内部设备接收队列缺少接收WQE而导致丢弃的数据包数量
- 错误

物理端口计数器
----------------------
物理端口计数器是指连接适配器到网络的外部端口上的计数器。这个测量点包含标准化计数器信息，如IEEE 802.3、RFC2863、RFC 2819、RFC 3635以及更多其他计数器，例如流控制、FEC等。
物理端口计数器表
-----------------

| 计数器 | 描述 | 类型 |
| --- | --- | --- |
| `rx_packets_phy` | 物理端口接收到的数据包数量。此计数器不包括因FCS、帧大小等类似错误而丢弃的数据包 | 信息 |
| `tx_packets_phy` | 物理端口传输的数据包数量 | 信息 |
| `rx_bytes_phy` | 物理端口接收到的字节数，包括以太网头和FCS | 信息 |
| `tx_bytes_phy` | 物理端口传输的字节数 | 信息 |
| `rx_multicast_phy` | 物理端口接收到的组播数据包数量 | 信息 |
| `tx_multicast_phy` | 物理端口传输的组播数据包数量 | 信息 |
| `rx_broadcast_phy` | 物理端口接收到的广播数据包数量 | 信息 |
| `tx_broadcast_phy` | 物理端口传输的广播数据包数量 | 信息 |
| `rx_crc_errors_phy` | 因FCS（帧校验序列）错误而丢弃的物理端口接收数据包数量。如果此计数器以高速增加，请使用下面的`rx_symbol_error_phy`和`rx_corrected_bits_phy`计数器检查链路质量 | 错误 |
| `rx_in_range_len_errors_phy` | 因长度/类型错误而丢弃的物理端口接收到的数据包数量 | 信息 |
- 错误

   * - `rx_out_of_range_len_phy`
     - 由于接收到的数据包长度超过物理端口允许的长度而导致丢弃的数据包数量。如果此计数器在增加，表明连接到适配器的对等方配置了更大的MTU。使用相同的MTU配置可以解决此问题。
- 错误

   * - `rx_oversize_pkts_phy`
     - 由于数据包长度超过物理端口上的MTU大小而被丢弃的接收数据包数量。如果此计数器在增加，表明连接到适配器的对等方配置了更大的MTU。使用相同的MTU配置可以解决此问题。
- 错误

   * - `rx_symbol_err_phy`
     - 由于物理端口上的物理编码错误（符号错误）而导致丢弃的接收数据包数量。
- 错误

   * - `rx_mac_control_phy`
     - 在物理端口上接收到的MAC控制数据包的数量。
- 信息

   * - `tx_mac_control_phy`
     - 在物理端口上传输的MAC控制数据包的数量。
- 信息

   * - `rx_pause_ctrl_phy`
     - 在物理端口上接收到的链路层暂停数据包的数量。如果此计数器在增加，表明网络拥塞，无法吸收来自适配器的流量。
- 信息

   * - `tx_pause_ctrl_phy`
     - 在物理端口上传输的链路层暂停数据包的数量。如果此计数器在增加，表明NIC拥塞，无法吸收来自网络的流量。
- 信息

   * - `rx_unsupported_op_phy`
     - 在物理端口上接收到的带有不支持的操作码的MAC控制数据包的数量。
- 错误

   * - `rx_discards_phy`
     - 由于物理端口缺少缓冲区而导致丢弃的接收数据包数量。如果此计数器在增加，表明适配器拥塞，无法吸收来自网络的流量。
- 错误

   * - `tx_discards_phy`
     - 即使未检测到错误，在传输过程中被丢弃的数据包数量。丢弃可能由于链路处于断开状态、队列头部丢弃、来自网络的暂停等原因造成。
- 错误

   * - `tx_errors_phy`
     - 由于物理端口上的传输数据包长度超过MTU大小而导致丢弃的数据包数量
- 错误

   * - `rx_undersize_pkts_phy`
     - 由于长度短于64字节而在物理端口上被丢弃的接收数据包数量。如果此计数器在增加，表明连接到适配器的对端配置了非标准MTU或收到了畸形数据包
- 错误

   * - `rx_fragments_phy`
     - 由于长度短于64字节且存在FCS错误而在物理端口上被丢弃的接收数据包数量。如果此计数器在增加，表明连接到适配器的对端配置了非标准MTU
- 错误

   * - `rx_jabbers_phy`
     - 由于长度超过64字节且存在FCS错误而在物理端口上被丢弃的接收数据包数量
- 信息

   * - `rx_64_bytes_phy`
     - 在物理端口上接收到的大小为64字节的数据包数量
- 信息

   * - `rx_65_to_127_bytes_phy`
     - 在物理端口上接收到的大小为65至127字节的数据包数量
- 信息

   * - `rx_128_to_255_bytes_phy`
     - 在物理端口上接收到的大小为128至255字节的数据包数量
- 信息

   * - `rx_256_to_511_bytes_phy`
     - 在物理端口上接收到的大小为256至512字节的数据包数量
- 信息

   * - `rx_512_to_1023_bytes_phy`
     - 在物理端口上接收到的大小为512至1023字节的数据包数量
- 信息

   * - `rx_1024_to_1518_bytes_phy`
     - 在物理端口上接收到的大小为1024至1518字节的数据包数量
- 信息性

   * - `rx_1519_to_2047_bytes_phy`
     - 物理端口接收到的大小在 1519 到 2047 字节之间的数据包数量
- 信息性

   * - `rx_2048_to_4095_bytes_phy`
     - 物理端口接收到的大小在 2048 到 4095 字节之间的数据包数量
- 信息性

   * - `rx_4096_to_8191_bytes_phy`
     - 物理端口接收到的大小在 4096 到 8191 字节之间的数据包数量
- 信息性

   * - `rx_8192_to_10239_bytes_phy`
     - 物理端口接收到的大小在 8192 到 10239 字节之间的数据包数量
- 信息性

   * - `link_down_events_phy`
     - 链路工作状态变为断开的次数。如果这个计数器在增加，可能表明端口在频繁切换。您可能需要更换线缆/收发器
- 错误

   * - `rx_out_of_buffer`
     - 接收队列没有为适配器的传入流量分配软件缓冲区的次数
- 错误

   * - `module_bus_stuck`
     - 模块的 I²C 总线（数据或时钟）短路被检测到的次数。您可能需要更换线缆/收发器
- 错误

   * - `module_high_temp`
     - 模块温度过高的次数。如果此问题持续存在，您可能需要检查环境温度或更换线缆/收发器模块
- 错误

   * - `module_bad_shorted`
     - 模块线缆短路的次数。您可能需要更换线缆/收发器模块
- 错误

   * - `module_unplug`
     - 模块被拔出的次数
- 信息性

   * - `rx_buffer_passed_thres_phy`
     - 端口接收缓冲区超过85%满的事件数量
- 信息性

   * - `tx_pause_storm_warning_events`
     - 设备长时间发送暂停帧的次数
- 信息性

   * - `tx_pause_storm_error_events`
     - 设备长时间发送暂停帧并达到超时，导致禁用暂停帧传输的次数。在暂停帧被禁用期间，可能会发生丢包
- 错误

   * - `rx[i]_buff_alloc_err`
     - 在环i上分配接收数据包（或SKB）缓冲区失败
- 错误

   * - `rx_bits_phy`
     - 此计数器提供有关可以接收的总流量的信息，并可用于衡量`rx_pcs_symbol_err_phy`和`rx_corrected_bits_phy`中的错误流量比例
- 信息性

   * - `rx_pcs_symbol_err_phy`
     - 此计数器统计未被FEC校正算法纠正的符号错误数量，或者此接口上的FEC算法未激活。如果此计数器增加，意味着NIC与网络之间的链路遭受高误码率（BER），且流量丢失。您可能需要更换电缆/收发器。误码率是在特定时间框架内`rx_pcs_symbol_err_phy`除以`rx_bits_phy`的数量
- 错误

   * - `rx_corrected_bits_phy`
     - 根据激活的FEC（RS/FC）算法，此端口上已纠正的位数。如果此计数器增加，意味着NIC与网络之间的链路遭受高误码率（BER）。纠正位率是在特定时间框架内`rx_corrected_bits_phy`除以`rx_bits_phy`的数量
- 错误

   * - `rx_err_lane_[l]_phy`
     - 每条通道l索引的物理原始错误数量。此计数器统计FEC校正前的错误。如果此计数器增加，意味着NIC与网络之间的链路遭受高误码率（BER），且流量可能丢失。您可能需要更换电缆/收发器。请根据`rx_corrected_bits_phy`进行检查
- 错误

   * - `rx_global_pause`
     - 物理端口接收到的暂停帧数量。如果此计数器增加，意味着网络拥塞，无法吸收来自适配器的流量。注意：此计数器仅在启用全局暂停模式时有效
- 信息性指标

   * - `rx_global_pause_duration`
     - 物理端口接收到的暂停时间（以微秒为单位）。该计数器表示端口未发送任何流量的时间。如果此计数器在增加，这意味着网络拥塞，无法吸收来自适配器的流量。注意：此计数器仅在全局暂停模式启用时才启用。
- 信息性指标

   * - `tx_global_pause`
     - 物理端口传输的暂停数据包数量。如果此计数器在增加，这意味着适配器拥塞，无法吸收来自网络的流量。注意：此计数器仅在全局暂停模式启用时才启用。
- 信息性指标

   * - `tx_global_pause_duration`
     - 物理端口上的暂停传输时间（以微秒为单位）。注意：此计数器仅在全局暂停模式启用时才启用。
- 信息性指标

   * - `rx_global_pause_transition`
     - 物理端口上从Xoff到Xon状态转换的次数。注意：此计数器仅在全局暂停模式启用时才启用。
- 信息性指标

   * - `rx_if_down_packets`
     - 因接口关闭而丢弃的接收数据包数量。

优先级端口计数器
----------------------
以下计数器是按L2优先级（0-7）统计的物理端口计数器。
**注意：** 计数器名称中的`p`代表优先级。

.. flat-table:: 优先级端口计数器表
   :widths: 2 3 1

   * - 计数器
     - 描述
     - 类型

   * - `rx_prio[p]_bytes`
     - 在物理端口上接收到的具有优先级p的字节数
- 信息性指标

   * - `rx_prio[p]_packets`
     - 在物理端口上接收到的具有优先级p的数据包数量
- 信息性指标

   * - `tx_prio[p]_bytes`
     - 在物理端口上以优先级 p 发送的字节数
- 信息性指标

   * - `tx_prio[p]_packets`
     - 在物理端口上以优先级 p 发送的数据包数
- 信息性指标

   * - `rx_prio[p]_pause`
     - 在物理端口上接收到的带有优先级 p 的暂停数据包数。如果此计数器增加，表明网络拥塞，无法吸收来自适配器的流量。注意：此计数器仅在优先级 p 启用了 PFC 时可用。
- 信息性指标

   * - `rx_prio[p]_pause_duration`
     - 在物理端口上接收到的暂停持续时间（微秒）。该计数器表示端口在此优先级下未发送任何流量的时间。如果此计数器增加，表明网络拥塞，无法吸收来自适配器的流量。注意：此计数器仅在优先级 p 启用了 PFC 时可用。
- 信息性指标

   * - `rx_prio[p]_pause_transition`
     - 物理端口上优先级 p 从 Xoff 到 Xon 的转换次数。注意：此计数器仅在优先级 p 启用了 PFC 时可用。
- 信息性指标

   * - `tx_prio[p]_pause`
     - 在物理端口上以优先级 p 发送的暂停数据包数。如果此计数器增加，表明适配器拥塞，无法吸收来自网络的流量。注意：此计数器仅在优先级 p 启用了 PFC 时可用。
- 信息性指标

   * - `tx_prio[p]_pause_duration`
     - 在物理端口上以优先级 p 发送的暂停持续时间（微秒）。注意：此计数器仅在优先级 p 启用了 PFC 时可用。
- 信息性指标

   * - `rx_prio[p]_buf_discard`
     - 由于缺少每个主机接收缓冲区而被设备丢弃的数据包数
### 信息性指标

* - `rx_prio[p]_cong_discard`
  - 因主机拥塞而被设备丢弃的数据包数量

* - `rx_prio[p]_marked`
  - 因主机拥塞而被设备标记为ECN的数据包数量

* - `rx_prio[p]_discards`
  - 因接收缓冲区不足而被设备丢弃的数据包数量

### 设备计数器
--------------------
.. flat-table:: 设备计数器表
   :widths: 2 3 1

   * - 计数器
     - 描述
     - 类型

   * - `rx_pci_signal_integrity`
     - 计数物理层PCIe信号完整性错误，包括由于帧错误和CRC（dlp和tlp）导致的恢复转换次数。如果此计数器上升，请尝试将适配器卡移动到不同的插槽以排除坏的PCI插槽。验证是否使用了最新版本的固件和服务器BIOS。
- 信息性

   * - `tx_pci_signal_integrity`
     - 计数物理层PCIe信号完整性错误，包括由对端发起的恢复转换次数（因接收到TS/EIEOS而进入恢复状态）。如果此计数器上升，请尝试将适配器卡移动到不同的插槽以排除坏的PCI插槽。验证是否使用了最新版本的固件和服务器BIOS。
- 错误

   * - `outbound_pci_buffer_overflow`
     - 因PCI缓冲区溢出而丢弃的数据包数量。如果此计数器以高频率上升，可能表明主机的接收流量速率超过了PCIe总线，从而导致拥塞。
- 信息性

   * - `outbound_pci_stalled_rd`
     - 在过去一秒内NIC有非发布读请求但因发布信用不足而无法执行操作的时间百分比（范围在0到100之间）
- 信息性

   * - `outbound_pci_stalled_wr`
     - 在过去一秒内NIC有发布写请求但因发布信用不足而无法执行操作的时间百分比（范围在0到100之间）
- 信息性

   * - `outbound_pci_stalled_rd_events`
     - `outbound_pci_stalled_rd`超过30%的时间秒数
- 信息性

   * - `outbound_pci_stalled_wr_events`
     - `outbound_pci_stalled_wr`超过30%的时间秒数
- 信息性
### 信息

* - `dev_out_of_buffer`
  - 设备所有队列因分配的缓冲区不足而导致的次数

- 错误
