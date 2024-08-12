### 公共邮箱框架

**作者：**贾西·布拉尔 <jaswinder.singh@linaro.org>

本文档旨在帮助开发人员为该API编写客户端和控制器驱动程序。但在开始之前，需要注意的是，客户端（尤其是）和控制器驱动程序很可能具有很强的平台特性，因为远程固件可能是专有的，并实现非标准协议。因此即使两个平台都使用了PL320控制器，客户端驱动程序也不能在它们之间共享。甚至PL320驱动程序也需要适应某些平台特有的特性。因此，此API的主要目的是避免为每个平台编写类似的代码副本。话虽如此，远程固件也可以基于Linux并使用相同的API。然而，这对我们本地并没有帮助，因为我们只处理客户端的协议级别。
一些实现选择是由于这个“公共”框架的独特性所导致的。

#### 控制器驱动程序（参见include/linux/mailbox_controller.h）

- 分配mbox_controller和mbox_chan数组
- 填充mbox_chan_ops，除了peek_data()外，其他都是必须的
- 控制器驱动程序可能通过IRQ或轮询某个硬件标志来知道消息已被远程端接收，或者它可能永远不知道（客户端通过协议知道）
- 方法按优先级排序为IRQ -> 轮询 -> 无，控制器驱动程序应通过'txdone_irq'或'txdone_poll'或两者都不设置

#### 客户端驱动程序（参见include/linux/mailbox_client.h）

客户端可能希望以阻塞模式（同步发送消息后再返回）或非阻塞/异步模式（提交消息和回调函数给API后立即返回）操作：

```c
struct demo_client {
    struct mbox_client cl;
    struct mbox_chan *mbox;
    struct completion c;
    bool async;
    /* ... */
};

/* 这是处理从远程端接收到的数据的处理器。行为完全取决于协议。这只是个例子 */
static void message_from_remote(struct mbox_client *cl, void *msg)
{
    struct demo_client *dc = container_of(cl, struct demo_client, cl);
    if (dc->async) {
        if (is_an_ack(msg)) {
            /* 我们上次发送的样本的ACK */
            return; /* 或者在这里做些其他事情 */
        } else { /* 来自远程的新消息 */
            queue_req(msg);
        }
    } else {
        /* 远程固件仅在此通道上发送ACK数据包 */
        return;
    }
}

static void sample_sent(struct mbox_client *cl, void *msg, int r)
{
    struct demo_client *dc = container_of(cl, struct demo_client, cl);
    complete(&dc->c);
}

static void client_demo(struct platform_device *pdev)
{
    struct demo_client *dc_sync, *dc_async;
    /* 控制器已经知道async_pkt和sync_pkt */
    struct async_pkt ap;
    struct sync_pkt sp;

    dc_sync = kzalloc(sizeof(*dc_sync), GFP_KERNEL);
    dc_async = kzalloc(sizeof(*dc_async), GFP_KERNEL);

    /* 填充非阻塞模式客户端 */
    dc_async->cl.dev = &pdev->dev;
    dc_async->cl.rx_callback = message_from_remote;
    dc_async->cl.tx_done = sample_sent;
    dc_async->cl.tx_block = false;
    dc_async->cl.tx_tout = 0; /* 这里不重要 */
    dc_async->cl.knows_txdone = false; /* 取决于协议 */
    dc_async->async = true;
    init_completion(&dc_async->c);

    /* 填充阻塞模式客户端 */
    dc_sync->cl.dev = &pdev->dev;
    dc_sync->cl.rx_callback = message_from_remote;
    dc_sync->cl.tx_done = NULL; /* 阻塞模式操作 */
    dc_sync->cl.tx_block = true;
    dc_sync->cl.tx_tout = 500; /* 半秒 */
    dc_sync->cl.knows_txdone = false; /* 取决于协议 */
    dc_sync->async = false;

    /* 异步邮箱在'mboxes'属性中列在第二位 */
    dc_async->mbox = mbox_request_channel(&dc_async->cl, 1);
    /* 填充数据包 */
    /* ap.xxx = 123; 等等 */
    /* 向远程发送异步消息 */
    mbox_send_message(dc_async->mbox, &ap);

    /* 同步邮箱在'mboxes'属性中列在第一位 */
    dc_sync->mbox = mbox_request_channel(&dc_sync->cl, 0);
    /* 填充数据包 */
    /* sp.abc = 123; 等等 */
    /* 以阻塞模式向远程发送消息 */
    mbox_send_message(dc_sync->mbox, &sp);
    /* 此时'sp'已被发送 */

    /* 现在等待异步通道完成 */
    wait_for_completion(&dc_async->c);
}
```
