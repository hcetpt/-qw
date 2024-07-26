### SPDX 许可证标识符: GPL-2.0
### 包含: <isonum.txt>

=================================
通用 TUN/TAP 设备驱动程序
=================================

版权所有 |copy| 1999-2000 Maxim Krasnyansky <max_mk@yahoo.com>

  * Linux 和 Solaris 驱动程序
  版权所有 |copy| 1999-2000 Maxim Krasnyansky <max_mk@yahoo.com>

  * FreeBSD TAP 驱动程序
  版权所有 |copy| 1999-2000 Maksim Yevmenkin <m_evmenkin@yahoo.com>

  * 本文档修订于 2002 年，由 Florian Thiel <florian.thiel@gmx.net>

1. 描述
========

  TUN/TAP 为用户空间程序提供数据包的接收和传输功能。
  它可以被视为一个简单的点对点或以太网设备，它不从物理介质接收数据包，
  而是从用户空间程序接收，并且不是通过物理介质发送数据包，而是写入到用户空间程序。
  为了使用此驱动程序，程序需要打开 `/dev/net/tun` 并发出相应的 `ioctl()` 来向内核注册一个网络设备。
  网络设备将根据所选选项显示为 `tunXX` 或 `tapXX`。
  当程序关闭文件描述符时，网络设备及其所有相关路由将会消失。
  根据所选择的设备类型，用户空间程序需要读取/写入 IP 数据包（使用 tun）或以太网帧（使用 tap）。
  使用哪一种取决于 `ioctl()` 中给出的标志。
  来自 `http://vtun.sourceforge.net/tun` 的包包含两个简单的示例，说明了如何使用 tun 和 tap 设备。
  这两个程序都像两个网络接口之间的桥接器一样工作：
  * `br_select.c` - 基于 `select` 系统调用的桥接器
  * `br_sigio.c` - 基于异步 I/O 和 `SIGIO` 信号的桥接器
  然而，最好的示例是 VTun (`http://vtun.sourceforge.net`)。:))

2. 配置
========

  创建设备节点：

    ```
    mkdir /dev/net （如果尚不存在）
    mknod /dev/net/tun c 10 200
    ```

  设置权限：

    ```
    例如：chmod 0666 /dev/net/tun
    ```

  允许非 root 用户访问该设备没有任何危害，因为创建网络设备或连接不属于当前用户的网络设备都需要 `CAP_NET_ADMIN` 能力。
  如果你希望创建持久性设备并将其所有权授予非特权用户，则需要使 `/dev/net/tun` 设备可供这些用户使用。

  驱动模块自动加载

    确保在你的内核中已启用“内核模块加载器” - 模块自动加载支持。
    内核应该会在首次访问时加载它。
### 手动加载

通过手动插入模块：

```sh
modprobe tun
```

如果你采用后一种方式，你需要在每次需要时手动加载模块。而如果采用另一种方式，当 `/dev/net/tun` 被打开时，模块将自动加载。

3. 程序接口
===========

3.1 网络设备分配
-----------------

`char *dev` 应该是设备名称的格式字符串（例如 "tun%d"），但（就我所见）这可以是任何有效的网络设备名称。请注意，字符指针会被实际的设备名称（例如 "tun0"）覆盖：

```c
#include <linux/if.h>
#include <linux/if_tun.h>

int tun_alloc(char *dev)
{
    struct ifreq ifr;
    int fd, err;

    if((fd = open("/dev/net/tun", O_RDWR)) < 0)
        return tun_alloc_old(dev);

    memset(&ifr, 0, sizeof(ifr));

    /* 标志：IFF_TUN - TUN 设备（没有以太网头部）
     *         IFF_TAP - TAP 设备
     *
     *         IFF_NO_PI - 不提供包信息
     */
    ifr.ifr_flags = IFF_TUN;
    if(*dev)
        strscpy_pad(ifr.ifr_name, dev, IFNAMSIZ);

    if((err = ioctl(fd, TUNSETIFF, (void *) &ifr)) < 0){
        close(fd);
        return err;
    }
    strcpy(dev, ifr.ifr_name);
    return fd;
}
```

3.2 帧格式
----------

如果未设置 IFF_NO_PI 标志，则每个帧格式为：

```plaintext
标志 [2 字节]
协议 [2 字节]
原始协议（IP、IPv6 等）帧
```

3.3 多队列 tuntap 接口
----------------------

从版本 3.8 开始，Linux 支持多队列 tuntap，它可以使用多个文件描述符（队列）来并行化发送或接收数据包。设备分配与之前相同，如果用户想要创建多个队列，则必须多次调用带有相同设备名称的 TUNSETIFF，并且带有 IFF_MULTI_QUEUE 标志。
`char *dev` 应该是设备名称，queues 是要创建的队列数量，fds 用于存储并返回给调用者创建的文件描述符（队列）。每个文件描述符作为队列的接口，可供用户空间访问：

```c
#include <linux/if.h>
#include <linux/if_tun.h>

int tun_alloc_mq(char *dev, int queues, int *fds)
{
    struct ifreq ifr;
    int fd, err, i;

    if(!dev)
        return -1;

    memset(&ifr, 0, sizeof(ifr));
    /* 标志：IFF_TUN - TUN 设备（没有以太网头部）
     *         IFF_TAP - TAP 设备
     *
     *         IFF_NO_PI - 不提供包信息
     *         IFF_MULTI_QUEUE - 创建一个多队列设备的队列
     */
    ifr.ifr_flags = IFF_TAP | IFF_NO_PI | IFF_MULTI_QUEUE;
    strcpy(ifr.ifr_name, dev);

    for(i = 0; i < queues; i++) {
        if((fd = open("/dev/net/tun", O_RDWR)) < 0)
            goto err;
        err = ioctl(fd, TUNSETIFF, (void *)&ifr);
        if(err) {
            close(fd);
            goto err;
        }
        fds[i] = fd;
    }

    return 0;
err:
    for(--i; i >= 0; i--)
        close(fds[i]);
    return err;
}
```

引入了一个新的 ioctl(TUNSETQUEUE) 来启用或禁用一个队列。当带有 IFF_DETACH_QUEUE 标志调用它时，队列被禁用；当带有 IFF_ATTACH_QUEUE 标志调用它时，队列被启用。队列在通过 TUNSETIFF 创建后默认是启用的。
fd 是我们想要启用或禁用的文件描述符（队列），当 enable 为真时我们启用它，否则我们禁用它：

```c
#include <linux/if.h>
#include <linux/if_tun.h>

int tun_set_queue(int fd, int enable)
{
    struct ifreq ifr;

    memset(&ifr, 0, sizeof(ifr));

    if(enable)
        ifr.ifr_flags = IFF_ATTACH_QUEUE;
    else
        ifr.ifr_flags = IFF_DETACH_QUEUE;

    return ioctl(fd, TUNSETQUEUE, (void *)&ifr);
}

### 通用 TUN/TAP 设备驱动程序常见问题解答
======================================

1. TUN/TAP 驱动支持哪些平台？

目前，该驱动已经为三种 Unix 系统编写：

  - Linux 内核 2.2.x, 2.4.x
  - FreeBSD 3.x, 4.x, 5.x
  - Solaris 2.6, 7.0, 8.0

2. TUN/TAP 驱动用于什么？

如上所述，TUN/TAP 驱动的主要用途是隧道传输。
它被 VTun（[http://vtun.sourceforge.net](http://vtun.sourceforge.net)）使用。
另一个有趣的应用是 pipsecd（[http://perso.enst.fr/~beyssac/pipsec/](http://perso.enst.fr/~beyssac/pipsec/)），一个用户空间的 IPSec 实现，可以使用完整的内核路由（不像 FreeS/WAN）。
3. 虚拟网络设备是如何实际工作的？

虚拟网络设备可以被视为一个简单的点对点或以太网设备，它不是从物理介质接收数据包，而是从用户空间程序接收数据包；它不是通过物理介质发送数据包，而是将数据包发送到用户空间程序。假设你在 tap0 上配置了 IPv6，那么每当内核向 tap0 发送 IPv6 数据包时，这个数据包就会传递给应用（例如 VTun）。该应用会对数据包进行加密、压缩，并通过 TCP 或 UDP 发送到另一端。另一端的应用则会解压和解密接收到的数据，并将其写入 TAP 设备中，内核处理这些数据包就像它们来自真实的物理设备一样。

4. TUN 驱动与 TAP 驱动之间的区别是什么？

TUN 处理 IP 帧。TAP 处理以太网帧。
这意味着当你使用 tun 时需要读取/写入 IP 数据包，而使用 tap 时需要处理以太网帧。

5. BPF 与 TUN/TAP 驱动之间的区别是什么？

BPF 是一种高级的包过滤器。它可以附加到现有的网络接口上。但它不提供虚拟网络接口。
而 TUN/TAP 驱动提供了虚拟网络接口，并且可以在该接口上附加 BPF。

6. TAP 驱动是否支持内核级别的以太网桥接？

是的。Linux 和 FreeBSD 的驱动都支持以太网桥接功能。
