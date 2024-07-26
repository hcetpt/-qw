SPDX 许可证标识符: GPL-2.0

=====================
软网络驱动问题
=====================

探测指导原则
==================

地址验证
------------------

对于你的设备所获取的任何硬件层地址都应进行验证。例如，对于以太网，可以使用 `linux/etherdevice.h:is_valid_ether_addr()` 进行检查。

关闭/停止指导原则
=====================

静默状态
----------

在调用 `ndo_stop` 常规函数后，硬件不应接收或传输任何数据。所有正在飞行中的数据包必须被中止。如果有必要，可以轮询或等待任何重置命令的完成。

自动关闭
----------

如果设备仍处于活动状态，`ndo_stop` 常规函数将由 `unregister_netdevice` 调用。

发送路径指导原则
========================

提前停止队列
----------------------

`ndo_start_xmit` 方法在正常情况下不应返回 `NETDEV_TX_BUSY`。除非你的设备无法事先判断其发送功能何时会变得繁忙，否则这被认为是一个严重错误。
相反，它必须正确维护队列。例如，对于实现了散集操作的驱动程序，这意味着：

.. code-block:: c

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
            netdev_warn(dev, "发送环在队列唤醒时已满!\n");
            return NETDEV_TX_BUSY;
        }

        //... 将数据包排队到卡上 ..
        netdev_tx_sent_queue(txq, skb->len);

        //... 使用 WRITE_ONCE() 更新发送生产者索引 ..
        if (!netif_txq_maybe_stop(txq, drv_tx_avail(dr),
                                  MAX_SKB_FRAGS + 1, 2 * MAX_SKB_FRAGS))
            dr->stats.stopped++;

        //..
        return NETDEV_TX_OK;
    }

然后，在处理完TX回收事件之后：

.. code-block:: c

    //... 使用 WRITE_ONCE() 更新发送消费者索引 ..
    netif_txq_completed_wake(txq, cmpl_pkts, cmpl_bytes,
                             drv_tx_avail(dr), 2 * MAX_SKB_FRAGS);

无锁队列停止/唤醒辅助宏
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

.. kernel-doc:: include/net/netdev_queues.h
   :doc: 无锁队列停止/唤醒辅助宏
没有独占所有权
----------------------

`ndo_start_xmit` 方法不得修改克隆的SKB的共享部分。
及时完成
------------

请记住，一旦你在 `ndo_start_xmit` 方法中返回 `NETDEV_TX_OK`，那么释放相应的套接字缓冲区（SKB）的责任就落在了你的驱动程序上，并且必须在有限的时间内完成。
例如，这意味着如果你的发送（TX）缓解策略允许发送的数据包永远停留在发送环中而不被回收（假设没有新的发送数据包），这是不允许的。
这种错误可能会导致等待发送缓冲区空间被释放的套接字出现死锁。
如果你在 `ndo_start_xmit` 方法中返回 `NETDEV_TX_BUSY`，则你不应该保留该套接字缓冲区的任何引用，并且不应该试图释放它。
