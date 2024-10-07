SPDX 许可证标识符: GPL-2.0

=====================
软网络驱动问题
=====================

探测指南
==================

地址验证
------------------

您为设备获取的任何硬件层地址都应进行验证。例如，对于以太网，可以使用 `linux/etherdevice.h:is_valid_ether_addr()` 进行检查。

关闭/停止指南
=====================

静默
----------

在调用 `ndo_stop` 函数之后，硬件不应接收或传输任何数据。所有在途的数据包必须被中止。如有必要，轮询或等待任何重置命令的完成。

自动关闭
----------

如果设备仍然处于 UP 状态，`ndo_stop` 函数将由 `unregister_netdevice` 调用。

发送路径指南
========================

提前停止队列
----------------------

在任何正常情况下，`ndo_start_xmit` 方法不得返回 `NETDEV_TX_BUSY`。除非设备无法提前判断其发送功能何时会变得繁忙，否则这被视为一个严重错误。
相反，它必须正确维护队列。例如，对于实现分散-聚集（scatter-gather）的驱动程序，这意味着：

```c
static u32 drv_tx_avail(struct drv_ring *dr)
{
    u32 used = READ_ONCE(dr->prod) - READ_ONCE(dr->cons);

    return dr->tx_ring_size - (used & bp->tx_ring_mask);
}

static netdev_tx_t drv_hard_start_xmit(struct sk_buff *skb,
                                       struct net_device *dev)
{
    struct drv *dp = netdev_priv(dev);
    struct netdev_queue *txq;
    struct drv_ring *dr;
    int idx;

    idx = skb_get_queue_mapping(skb);
    dr = dp->tx_rings[idx];
    txq = netdev_get_tx_queue(dev, idx);

    //..
    /* 这应该是一个非常罕见的竞争条件 - 记录日志。 */
    if (drv_tx_avail(dr) <= skb_shinfo(skb)->nr_frags + 1) {
        netif_stop_queue(dev);
        netdev_warn(dev, "Tx Ring full when queue awake!\n");
        return NETDEV_TX_BUSY;
    }

    //... 将数据包排队到网卡 ..
    netdev_tx_sent_queue(txq, skb->len);

    //... 使用 WRITE_ONCE() 更新发送生产者索引 ..
    if (!netif_txq_maybe_stop(txq, drv_tx_avail(dr),
                              MAX_SKB_FRAGS + 1, 2 * MAX_SKB_FRAGS))
        dr->stats.stopped++;

    //..
    return NETDEV_TX_OK;
}
```

然后，在处理完您的 TX 回收事件后：

```c
//... 使用 WRITE_ONCE() 更新发送消费者索引 ..
netif_txq_completed_wake(txq, cmpl_pkts, cmpl_bytes,
                         drv_tx_avail(dr), 2 * MAX_SKB_FRAGS);
```

无锁队列停止/唤醒宏助手
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

.. kernel-doc:: include/net/netdev_queues.h
   :doc: 无锁队列停止/唤醒助手

无独占所有权
----------------------

`ndo_start_xmit` 方法不得修改克隆的 SKB 的共享部分。
及时完成
------------------

请记住，一旦你在 `ndo_start_xmit` 方法中返回 `NETDEV_TX_OK`，你的驱动程序就有责任在有限的时间内释放 SKB。
例如，这意味着不允许你的 TX 缓解方案让 TX 数据包永远停留在 TX 环中而不被回收，如果不再发送新的 TX 数据包的话。
这种错误可能会导致等待发送缓冲区空间释放的套接字死锁。
如果你在 `ndo_start_xmit` 方法中返回 `NETDEV_TX_BUSY`，你不得保留对该 SKB 的任何引用，并且不得尝试释放它。
