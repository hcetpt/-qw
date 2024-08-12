MMC 异步请求
=============

理由
=====

缓存维护开销有多重要？

这取决于具体情况。快速的 eMMC 和多级缓存以及推测性缓存预取使缓存开销相对显著。如果为下一个请求所做的 DMA 准备与当前传输并行进行，则 DMA 准备开销将不会影响 MMC 性能。非阻塞（异步）MMC 请求的目的在于最小化一个 MMC 请求结束到另一个 MMC 请求开始之间的时间。
使用 mmc_wait_for_req()，在 dma_map_sg 和 dma_unmap_sg 处理过程中，MMC 控制器处于空闲状态。使用非阻塞 MMC 请求可以在活动的 MMC 请求的同时准备下一个任务的缓存。
MMC 块驱动程序
===============

MMC 块驱动程序中的 mmc_blk_issue_rw_rq() 已改为非阻塞模式。
吞吐量的提升与请求准备时间（大部分准备工作包括 dma_map_sg() 和 dma_unmap_sg()）和内存速度成正比。MMC/SD 越快，请求准备时间的重要性就越高。在 L2 缓存平台上，对于大块写入预计性能提升大约为 5%，对于大块读取约为 10%。在节能模式下，当时钟以较低频率运行时，DMA 准备可能会更加耗时。只要这些较慢的准备操作与传输并行运行，性能就不会受到影响。
IOZone 和 mmc_test 的测量细节
=================================

https://wiki.linaro.org/WorkingGroups/Kernel/Specs/StoragePerfMMC-async-req

MMC 核心 API 扩展
==================

新增了一个公共函数 mmc_start_req()。
该函数为一个主机启动一个新的 MMC 命令请求。这个函数并非真正意义上的非阻塞：如果有正在进行的异步请求，它会等待该请求完成，然后启动新的请求并返回。它不会等待新请求完成。如果没有正在进行的请求，则立即启动新的请求并返回。
MMC 主机扩展
=============

mmc_host_ops 中有两个可选成员 pre_req() 和 post_req()，主机驱动程序可以实现它们，以便在实际调用 mmc_host_ops.request() 函数之前和之后执行工作。
在 DMA 情况下，pre_req() 可以执行 dma_map_sg() 并准备 DMA 描述符，而 post_req() 则运行 dma_unmap_sg()。
优化首次请求
================

一系列请求中的首个请求无法与前一个传输并行准备，因为没有前一个请求。
`is_first_req` 参数在 `pre_req()` 函数中表示没有之前的请求。主机驱动程序可以针对这种情况进行优化，以尽量减少性能损失。一种优化方法是将当前请求分成两部分，准备第一部分并开始请求，最后准备第二部分并启动传输。

处理 `is_first_req` 场景、以最小化准备开销的伪代码如下：

```pseudocode
if (is_first_req && req->size > 阈值)
    /* 启动完整的传输大小的 MMC 指令 */
    mmc_start_command(MMC_CMD_TRANSFER_FULL_SIZE);

    /*
     * 在 MMC 处理指令的同时开始准备 DMA
     * 第一部分请求的准备时间应该与“MMC 处理命令的时间”相同
     * 如果准备时间超过了 MMC 命令处理时间
     * 传输会被延迟，估计最多 4KB 作为第一部分的大小
     */
    prepare_1st_chunk_for_dma(req);
    /* 将待处理的描述符刷新到 DMA 控制器 (dmaengine.h) */
    dma_issue_pending(req->dma_desc);

    prepare_2nd_chunk_for_dma(req);
    /*
     * 第二次调用 issue_pending 应该在 MMC 处理完第一部分之前。
     * 如果 MMC 在这次调用前就处理完了第一部分数据，
     * 传输会被延迟
     */
    dma_issue_pending(req->dma_desc);
```

这里的关键在于通过并发执行 DMA 准备和 MMC 数据传输来减少等待时间，从而提高整体效率。```
