SPDX 许可证标识符: GPL-2.0

=====================================
网络设备、内核和你！
=====================================

介绍
============
以下是关于网络设备的一些随机文档集合：
`struct net_device` 生命周期规则
================================
即使在模块卸载后，网络设备结构也需要持续存在，并且必须使用 `alloc_netdev_mqs()` 及其相关函数进行分配。如果设备已成功注册，则会在最后一次使用时通过 `free_netdev()` 进行释放。这是为了处理一些极端情况（例如：`rmmod mydriver </sys/class/net/myeth/mtu>`）。

`alloc_netdev_mqs()` 和 `alloc_netdev()` 会为驱动程序私有数据预留额外空间，当网络设备被释放时，这些数据也会被释放。如果单独分配的数据被附加到网络设备上（通过 `netdev_priv()`），则需要由模块退出处理程序来释放这些数据。

有两组 API 用于注册 `struct net_device`：
第一组可以在未持有 `rtnl_lock` 的正常上下文中使用：`register_netdev()` 和 `unregister_netdev()`。
第二组可以在已经持有 `rtnl_lock` 的情况下使用：`register_netdevice()`、`unregister_netdevice()` 和 `free_netdevice()`。

简单驱动程序
--------------

大多数驱动程序（特别是设备驱动程序）在网络设备生命周期的处理中不会持有 `rtnl_lock`（例如，在驱动程序探测和移除路径中）。在这种情况下，使用 `register_netdev()` 和 `unregister_netdev()` 函数来进行 `struct net_device` 的注册：

```c
int probe()
{
    struct my_device_priv *priv;
    int err;

    dev = alloc_netdev_mqs(...);
    if (!dev)
        return -ENOMEM;
    priv = netdev_priv(dev);

    /* 在调用 register_netdev() 之前完成所有设备设置 */

    err = register_netdev(dev);
    if (err)
        goto err_undo;

    /* 网络设备对用户可见！ */

err_undo:
    /* 撤销设备设置 */
    free_netdev(dev);
    return err;
}

void remove()
{
    unregister_netdev(dev);
    free_netdev(dev);
}
```

请注意，在调用 `register_netdev()` 之后，设备在系统中变得可见。用户可以立即打开它并开始发送/接收流量或运行其他回调，因此所有初始化都必须在注册之前完成。
`unregister_netdev()` 会关闭设备并等待所有用户完成使用。`struct net_device` 本身的内存可能仍会被 sysfs 引用，但对该设备的所有操作都将失败。`free_netdev()` 可以在 `unregister_netdev()` 返回后或 `register_netdev()` 失败时调用。

RTNL 下的设备管理
-------------------

在已经持有 `rtnl_lock` 的上下文中注册 `struct net_device` 需要格外小心。在这种情况下，大多数驱动程序希望利用 `struct net_device` 中的 `needs_free_netdev` 和 `priv_destructor` 成员来释放状态。
在 `rtnl_lock` 下处理 netdev 的示例流程：

```c
static void my_setup(struct net_device *dev)
{
    dev->needs_free_netdev = true;
}

static void my_destructor(struct net_device *dev)
{
    some_obj_destroy(priv->obj);
    some_uninit(priv);
}

int create_link()
{
    struct my_device_priv *priv;
    int err;

    ASSERT_RTNL();

    dev = alloc_netdev(sizeof(*priv), "net%d", NET_NAME_UNKNOWN, my_setup);
    if (!dev)
        return -ENOMEM;
    priv = netdev_priv(dev);

    /* 隐式构造函数 */
    err = some_init(priv);
    if (err)
        goto err_free_dev;

    priv->obj = some_obj_create();
    if (!priv->obj) {
        err = -ENOMEM;
        goto err_some_uninit;
    }
    /* 构造函数结束，设置析构函数： */
    dev->priv_destructor = my_destructor;

    err = register_netdevice(dev);
    if (err)
        /* register_netdevice() 在失败时调用析构函数 */
        goto err_free_dev;

    /* 如果现在有任何失败，unregister_netdevice()（或unregister_netdev()）
       将负责调用 my_destructor 和 free_netdev() */

    return 0;

err_some_uninit:
    some_uninit(priv);
err_free_dev:
    free_netdev(dev);
    return err;
}
```

如果设置了 `struct net_device.priv_destructor`，它将在 `unregister_netdevice()` 之后的某个时间由内核核心调用，如果 `register_netdevice()` 失败也会被调用。该回调可能会在持有或不持有 `rtnl_lock` 的情况下被调用。
没有显式的构造函数回调，驱动程序在分配后并在注册前“构造”私有的 netdev 状态。
设置 `struct net_device.needs_free_netdev` 使得核心在 `unregister_netdevice()` 后自动调用 `free_netdev()`，当所有对设备的引用消失时。它只有在成功调用 `register_netdevice()` 后才生效，因此如果 `register_netdevice()` 失败，则驱动程序需要负责调用 `free_netdev()`。
`free_netdev()` 在错误路径中，在 `unregister_netdevice()` 或 `register_netdevice()` 失败后调用是安全的。部分 netdev 注册/注销过程发生在 `rtnl_lock` 释放之后，因此在这种情况下 `free_netdev()` 会将一些处理推迟到 `rtnl_lock` 释放之后。
从 `struct rtnl_link_ops` 生成的设备不应直接释放 `struct net_device`。

`.ndo_init` 和 `.ndo_uninit`
~~~~~~~~~~~~~~~~~~~~~~~~~

`.ndo_init` 和 `.ndo_uninit` 回调函数在 net_device 注册和注销期间，在 `rtnl_lock` 下被调用。驱动程序可以使用这些回调，例如当其初始化过程的一部分需要在 `rtnl_lock` 下运行时。
``.ndo_init`` 在设备在系统中可见之前运行，``.ndo_uninit`` 在设备关闭后但在其他子系统可能仍持有对网卡引用时运行。

### 最大传输单元（MTU）
每个网络设备都有一个最大传输单元（MTU）。MTU 不包括任何链路层协议开销。上层协议不应将超过 MTU 大小的数据的套接字缓冲区（skb）传递给设备进行传输。MTU 不包括链路层头部开销，因此例如在以太网上，如果标准 MTU 是 1500 字节，则实际的 skb 可能包含最多 1514 字节的数据，因为包含了以太网头部。设备应允许 4 字节的 VLAN 头部。

分段卸载（GSO、TSO）是这一规则的一个例外。上层协议可以将一个大的套接字缓冲区传递给设备的传输例程，而设备会根据当前的 MTU 将其拆分成多个独立的数据包。

MTU 是对称的，适用于接收和发送。设备必须能够接收至少由 MTU 允许的最大大小的数据包。网络设备可以使用 MTU 作为设置接收缓冲区大小的机制，但设备应允许带有 VLAN 头部的数据包。对于标准以太网 MTU 为 1500 字节的情况，设备应允许最多 1518 字节的数据包（1500 + 14 头部 + 4 标签）。设备可以选择丢弃、截断或传递超大数据包，但丢弃超大数据包是首选的做法。

### `struct net_device` 同步规则
#### ndo_open:
- **同步**: 使用 `rtnl_lock()` 信号量
- **上下文**: 进程

#### ndo_stop:
- **同步**: 使用 `rtnl_lock()` 信号量
- **上下文**: 进程
  - 注意: `netif_running()` 被保证为假

#### ndo_do_ioctl:
- **同步**: 使用 `rtnl_lock()` 信号量
- **上下文**: 进程
  - 仅由网络子系统内部调用，而不是用户空间通过 ioctl 调用，这是从 Linux 5.14 版本开始的

#### ndo_siocbond:
- **同步**: 使用 `rtnl_lock()` 信号量
- **上下文**: 进程
  - 用于绑定驱动程序处理 SIOCBOND 系列的 ioctl 命令
```markdown
ndo_siocwandev:
    同步：rtnl_lock() 信号量
上下文：进程

    由 drivers/net/wan 框架使用，处理 SIOCWANDEV ioctl 调用与 if_settings 结构体

ndo_siocdevprivate:
    同步：rtnl_lock() 信号量
上下文：进程

    用于实现 SIOCDEVPRIVATE ioctl 辅助函数
这些函数不应添加到新驱动程序中，因此不要使用

ndo_eth_ioctl:
    同步：rtnl_lock() 信号量
上下文：进程

ndo_get_stats:
    同步：rtnl_lock() 信号量或 RCU
上下文：原子（在 RCU 下不能休眠）

ndo_start_xmit:
    同步：__netif_tx_lock 自旋锁
当驱动程序在 dev->features 中设置 NETIF_F_LLTX 时，该函数将在不持有 netif_tx_lock 的情况下被调用。在这种情况下，驱动程序需要根据需要自行加锁
那里的锁定也应适当保护 set_rx_mode 的调用。警告：NETIF_F_LLTX 的使用已被弃用
```
不要用于新驱动程序

上下文：在禁用 BH（底半部）或 BH（定时器）的情况下处理，将由 netconsole 禁用中断后调用
返回码：

* NETDEV_TX_OK：一切正常
* NETDEV_TX_BUSY：无法发送数据包，稍后再试
通常这是一个错误，表示驱动程序中的队列启动/停止流控制有问题。注意：驱动程序不得将 skb 放入其 DMA 环中

ndo_tx_timeout：
同步：netif_tx_lock 自旋锁；所有 TX 队列被冻结
上下文：BH（底半部）被禁用
注释：netif_queue_stopped() 被保证为真

ndo_set_rx_mode：
同步：netif_addr_lock 自旋锁
上下文：BH（底半部）被禁用

struct napi_struct 同步规则
==========================
napi->poll：
同步：
NAPI_STATE_SCHED 位在 napi->state 中。设备驱动程序的 ndo_stop 方法将在所有 NAPI 实例上调用 napi_disable()，这将对 NAPI_STATE_SCHED 位进行睡眠轮询，等待所有待处理的 NAPI 活动结束
上下文：
softirq
将由 netconsole 禁用中断后调用
