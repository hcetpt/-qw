### SPDX 许可证标识符: GPL-2.0

=============
页面池 API
=============

.. kernel-doc:: include/net/page_pool/helpers.h
   :doc: 页面池分配器

架构概述
=====================

.. code-block:: none

    +------------------+
    |       驱动程序     |
    +------------------+
            ^
            |
            |
            |
            v
    +--------------------------------------------+
    |                请求内存                     |
    +--------------------------------------------+
        ^                                  ^
        |                                  |
        | 池为空                         | 池有条目
        |                                  |
        v                                  v
    +-----------------------+     +------------------------+
    | 分配(并映射)页面 |     |  从缓存获取页面   |
    +-----------------------+     +------------------------+
                                    ^                    ^
                                    |                    |
                                    | 缓存可用           | 没有条目，重新填充
                                    |                    | 来自指针环
                                    |                    |
                                    v                    v
                          +-----------------+     +------------------+
                          |   快速缓存    |     |  指针环缓存  |
                          +-----------------+     +------------------+

监控
=====
有关系统上页面池的信息可以通过 netdev genetlink 家族（参见文档/netlink/specs/netdev.yaml）的 API 接口访问。

API接口
=============
创建的池的数量**必须**与硬件队列的数量相匹配，除非硬件限制使得这不可能。否则就会违背页面池的目的，即能够快速地从缓存中分配页面而无需锁定。
这种无锁保证自然来源于在 NAPI 软中断上下文中运行。
保护措施不必严格是 NAPI，只要能确保分配页面时不会产生竞态条件的任何保证就足够了。
.. kernel-doc:: net/core/page_pool.c
   :identifiers: page_pool_create

.. kernel-doc:: include/net/page_pool/types.h
   :identifiers: struct page_pool_params

.. kernel-doc:: include/net/page_pool/helpers.h
   :identifiers: page_pool_put_page page_pool_put_full_page
                 page_pool_recycle_direct page_pool_free_va
                 page_pool_dev_alloc_pages page_pool_dev_alloc_frag
                 page_pool_dev_alloc page_pool_dev_alloc_va
                 page_pool_get_dma_addr page_pool_get_dma_dir

.. kernel-doc:: net/core/page_pool.c
   :identifiers: page_pool_put_page_bulk page_pool_get_stats

DMA 同步
--------
驱动程序始终负责为 CPU 同步页面。
驱动程序可以选择自行处理设备的同步，
或者设置 `PP_FLAG_DMA_SYNC_DEV` 标志来请求从页面池分配的页面已经为设备同步。
如果设置了 `PP_FLAG_DMA_SYNC_DEV`，则驱动程序必须告知核心需要同步缓冲区的哪部分。这允许核心避免当驱动程序知道设备只访问了页面的一部分时同步整个页面。
大多数驱动程序会在帧前面保留一些空间。这部分缓冲区不会被设备触及，因此为了避免同步这部分内容，驱动程序可以适当设置 `struct page_pool_params` 中的 `offset` 字段。
对于在 XDP 发送和 skb 路径中回收的页面，页面池将使用 `struct page_pool_params` 中的 `max_len` 成员来决定需要同步多少页面（从 `offset` 开始）。
当直接在驱动程序中释放页面（page_pool_put_page()）时，`dma_sync_size` 参数指定了需要同步的缓冲区大小。
### 如果有疑问，请将`offset`设置为0，`max_len`设置为`PAGE_SIZE`，并将`dma_sync_size`传递为-1。这种参数组合总是正确的。
请注意，同步参数适用于整个页面。
当使用碎片（`PP_FLAG_PAGE_FRAG`）时，这一点非常重要记住，因为分配的缓冲区可能小于一个完整的页面。
除非驱动程序作者真正理解页面池内部工作原理，否则建议始终使用`offset = 0`、`max_len = PAGE_SIZE`与碎片化的页面池。
### 统计API和结构体
如果内核配置了`CONFIG_PAGE_POOL_STATS=y`，则可以使用API `page_pool_get_stats()`和下面描述的结构体。
它需要一个指向`struct page_pool`的指针和一个由调用者分配的指向`struct page_pool_stats`的指针。
较旧的驱动程序通过ethtool或debugfs暴露页面池统计信息。
相同的统计信息可以通过netlink netdev家族以驱动程序独立的方式访问。
```c
.. kernel-doc:: include/net/page_pool/types.h
   :identifiers: struct page_pool_recycle_stats
		 struct page_pool_alloc_stats
		 struct page_pool_stats
```

### 编码示例

#### 注册
```c
/* 页面池注册 */
struct page_pool_params pp_params = { 0 };
struct xdp_rxq_info xdp_rxq;
int err;

pp_params.order = 0;
/* 内部DMA映射在page_pool中 */
pp_params.flags = PP_FLAG_DMA_MAP;
pp_params.pool_size = DESC_NUM;
pp_params.nid = NUMA_NO_NODE;
pp_params.dev = priv->dev;
pp_params.napi = napi; /* 只有当锁定与NAPI相关联时才需要 */
pp_params.dma_dir = xdp_prog ? DMA_BIDIRECTIONAL : DMA_FROM_DEVICE;
page_pool = page_pool_create(&pp_params);

err = xdp_rxq_info_reg(&xdp_rxq, ndev, 0);
if (err)
    goto err_out;

err = xdp_rxq_info_reg_mem_model(&xdp_rxq, MEM_TYPE_PAGE_POOL, page_pool);
if (err)
    goto err_out;
```

#### NAPI轮询器
```c
/* NAPI接收轮询器 */
enum dma_data_direction dma_dir;

dma_dir = page_pool_get_dma_dir(dring->page_pool);
while (done < budget) {
    if (some error)
        page_pool_recycle_direct(page_pool, page);
    if (packet_is_xdp) {
        if (XDP_DROP):
            page_pool_recycle_direct(page_pool, page);
    } else (packet_is_skb) {
        skb_mark_for_recycle(skb);
        new_page = page_pool_dev_alloc_pages(page_pool);
    }
}
```

#### 统计信息
```c
#ifdef CONFIG_PAGE_POOL_STATS
/* 获取统计信息 */
struct page_pool_stats stats = { 0 };
if (page_pool_get_stats(page_pool, &stats)) {
    /* 也许驱动程序通过ethtool报告统计信息 */
    ethtool_print_allocation_stats(&stats.alloc_stats);
    ethtool_print_recycle_stats(&stats.recycle_stats);
}
#endif
```

#### 驱动卸载
```c
/* 驱动卸载 */
page_pool_put_full_page(page_pool, page, false);
xdp_rxq_info_unreg(&xdp_rxq);
```
