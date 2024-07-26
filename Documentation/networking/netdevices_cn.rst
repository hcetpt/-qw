SPDX 许可证标识符: GPL-2.0

=====================================
网络设备、内核与您！
=====================================

简介
============
以下是关于网络设备的一些随机文档集合，
以及 `struct net_device` 生命周期规则。

网络设备结构体即使在模块卸载后也需要保持存在，
并且必须使用 `alloc_netdev_mqs()` 及其相关函数进行分配。
如果设备已成功注册，则会在最后一次使用时通过 `free_netdev()` 进行释放。
这是为了干净地处理一些极端情况（例如：`rmmod mydriver </sys/class/net/myeth/mtu`）。

`alloc_netdev_mqs()` / `alloc_netdev()` 为驱动程序私有数据预留了额外空间，这些数据会在网络设备被释放时被释放。如果另外分配的数据通过 `netdev_priv()` 附加到网络设备上，则需要由模块退出处理器来负责释放这些数据。

有两个 API 组可以用于注册 `struct net_device`：
第一组可以在未持有 `rtnl_lock` 的正常上下文中使用：`register_netdev()`、`unregister_netdev()`；
第二组可以在已经持有 `rtnl_lock` 的情况下使用：`register_netdevice()`、`unregister_netdevice()`、`free_netdevice()`。

简单驱动程序
--------------

大多数驱动程序（尤其是设备驱动程序）在网络设备的生命周期管理中不会持有 `rtnl_lock`（例如，在驱动程序的探测和移除路径中）。
在这种情况下，`struct net_device` 的注册是通过 `register_netdev()` 和 `unregister_netdev()` 函数完成的：

```c
int probe()
{
    struct my_device_priv *priv;
    int err;

    dev = alloc_netdev_mqs(...);
    if (!dev)
        return -ENOMEM;
    priv = netdev_priv(dev);

    /* ... 在调用 register_netdev() 之前完成所有设备设置 ... */

    err = register_netdev(dev);
    if (err)
        goto err_undo;

    /* 网络设备现在对用户可见！ */

err_undo:
    /* ... 撤销设备设置 ... */
    free_netdev(dev);
    return err;
}

void remove()
{
    unregister_netdev(dev);
    free_netdev(dev);
}
```

请注意，在调用 `register_netdev()` 后，设备在系统中是可见的。
用户可以立即打开它并开始发送/接收流量或运行其他回调函数，因此所有的初始化工作都必须在注册前完成。
`unregister_netdev()`会关闭设备并等待所有用户完成使用。`struct net_device`本身的内存可能仍被sysfs引用，但对该设备的所有操作都将失败。
可以在`unregister_netdev()`返回后或`register_netdev()`失败时调用`free_netdev()`。
在RTNL下的设备管理
------------------------------

在已经持有`rtnl_lock`的上下文中注册`struct net_device`需要格外小心。在这种情况下，大多数驱动程序将希望利用`struct net_device`中的`needs_free_netdev`和`priv_destructor`成员来释放状态。
在`rtnl_lock`下处理netdev的一个示例流程：

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
        /* register_netdevice() 在失败时会调用析构函数 */
        goto err_free_dev;

    /* 如果现在有任何失败，unregister_netdevice()（或unregister_netdev()）
       将负责调用my_destructor和free_netdev() */

    return 0;

err_some_uninit:
    some_uninit(priv);
err_free_dev:
    free_netdev(dev);
    return err;
}
```

如果设置了`struct net_device.priv_destructor`，核心将在`unregister_netdevice()`之后的某个时间调用它，如果`register_netdevice()`失败也会调用。这个回调函数可能在持有或不持有`rtnl_lock`的情况下被调用。
没有显式的构造函数回调，驱动程序在分配之后和注册之前“构造”私有的netdev状态。
设置`struct net_device.needs_free_netdev`会使核心在`unregister_netdevice()`之后并且当对设备的所有引用消失时自动调用`free_netdevice()`。只有在成功调用`register_netdevice()`之后才会生效，因此如果`register_netdevice()`失败，则驱动程序负责调用`free_netdev()`。
在错误路径上，在`unregister_netdevice()`之后或`register_netdevice()`失败时调用`free_netdev()`是安全的。netdev（注销/注册）过程的一部分发生在释放`rtnl_lock`之后，因此在这些情况下`free_netdev()`将延迟部分处理直到`rtnl_lock`被释放。
从`struct rtnl_link_ops`生成的设备绝不应该直接释放`struct net_device`。
.ndo_init 和 .ndo_uninit
~~~~~~~~~~~~~~~~~~~~~~~~~

`.ndo_init` 和 `.ndo_uninit` 回调函数在net_device注册和注销期间、在`rtnl_lock`下被调用。驱动程序可以利用这些回调，例如当它们的部分初始化过程需要在`rtnl_lock`下运行时。
``.ndo_init`` 在设备在系统中可见之前运行，而 ``.ndo_uninit`` 则在设备关闭后的注销过程中运行，此时其他子系统可能仍然持有对该网络设备的引用。

MTU
==
每个网络设备都有一个最大传输单元（MTU）。这里的MTU不包括任何链路层协议开销。上层协议不应将数据长度超过MTU的套接字缓冲区(skb)传递给设备以进行传输。需要注意的是，MTU不包括链路层头部开销，例如，在以太网中如果标准MTU为1500字节，则实际的skb可以包含高达1514字节的数据，因为包含了以太网头部。设备应该允许额外的4字节VLAN头部。

分段卸载（GSO, TSO）是这一规则的一个例外。上层协议可以将大型套接字缓冲区传递给设备的发送例程，而设备会根据当前的MTU将其拆分成多个单独的包。

MTU是对称的，适用于接收和发送。设备必须能够接收至少由MTU允许的最大尺寸的包。网络设备可能会使用MTU作为接收缓冲区大小的机制，但设备应该允许包含VLAN头部的包。对于标准以太网MTU为1500字节的情况，设备应该允许高达1518字节的包（1500 + 14字节头部 + 4字节标签）。设备可以丢弃、截断或传递超大包，但优选的做法是丢弃超大包。

`struct net_device` 同步规则
==============================
`ndo_open`：
    - 同步：rtnl_lock()信号量
    - 上下文：进程

`ndo_stop`：
    - 同步：rtnl_lock()信号量
    - 上下文：进程
    - 注意：netif_running()保证为假

`ndo_do_ioctl`：
    - 同步：rtnl_lock()信号量
    - 上下文：进程
    - 注意：这个函数仅被网络子系统内部调用，而不是用户空间通过ioctl调用的方式，这与linux-5.14之前的版本不同

`ndo_siocbond`：
    - 同步：rtnl_lock()信号量
    - 上下文：进程
    - 注意：此函数被bonding驱动程序用于处理SIOCBOND系列的ioctl命令
这段文本描述了Linux内核网络驱动程序中几个函数的同步机制和上下文。以下是中文翻译：

`ndo_siocwandev`：
- 同步：使用`rtnl_lock()`信号量
- 上下文：进程

由`drivers/net/wan`框架使用，处理通过`if_settings`结构体与`SIOCWANDEV` ioctl命令相关的操作。

`ndo_siocdevprivate`：
- 同步：使用`rtnl_lock()`信号量
- 上下文：进程

此函数用于实现`SIOCDEVPRIVATE` ioctl助手函数。
对于新驱动程序不应添加此类ioctl助手，因此不要使用它们。

`ndo_eth_ioctl`：
- 同步：使用`rtnl_lock()`信号量
- 上下文：进程

`ndo_get_stats`：
- 同步：使用`rtnl_lock()`信号量或RCU（Read-Copy-Update）
- 上下文：原子操作（在RCU下不能休眠）

`ndo_start_xmit`：
- 同步：使用`__netif_tx_lock`自旋锁
当驱动程序在`dev->features`中设置`NETIF_F_LLTX`时，该函数将在不持有`netif_tx_lock`的情况下被调用。在这种情况下，驱动程序需要根据需要自行锁定。
这里的锁定还应正确地保护`set_rx_mode`调用。**警告**：`NETIF_F_LLTX`的使用已被废弃。
不要在新驱动中使用它。

在禁用了BHs或BH（定时器）的过程中，
将被netconsole以中断禁用的方式调用。
返回码：

* NETDEV_TX_OK：一切正常
* NETDEV_TX_BUSY：无法发送数据包，稍后重试
通常这是一个bug，意味着驱动中的队列启动/停止流控存在问题。
注意：驱动程序必须不把skb放入其DMA环中。

ndo_tx_timeout:
同步：netif_tx_lock自旋锁；所有TX队列冻结
上下文：BHs禁用
注释：netif_queue_stopped()保证为真

ndo_set_rx_mode:
同步：netif_addr_lock自旋锁
上下文：BHs禁用

napi_struct结构体同步规则
============================
napi->poll:
同步：
NAPI_STATE_SCHED位在napi->state中。设备
驱动的ndo_stop方法会调用napi_disable()在
所有的NAPI实例上，这将对NAPI_STATE_SCHED napi->state位执行睡眠轮询，等待所有待处理的
NAPI活动结束
上下文：
软中断
将被netconsole以中断禁用的方式调用。
