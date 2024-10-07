.. SPDX 许可证标识符: GPL-2.0
.. include:: <isonum.txt>

===============================
通用 TUN/TAP 设备驱动程序
===============================

版权所有 |copy| 1999-2000 Maxim Krasnyansky <max_mk@yahoo.com>

  Linux 和 Solaris 驱动程序
  版权所有 |copy| 1999-2000 Maxim Krasnyansky <max_mk@yahoo.com>

  FreeBSD TAP 驱动程序
  版权所有 |copy| 1999-2000 Maksim Yevmenkin <m_evmenkin@yahoo.com>

  本文档修订于 2002 年，由 Florian Thiel <florian.thiel@gmx.net> 完成

1. 描述
==============

  TUN/TAP 为用户空间程序提供数据包接收和传输功能。
  可以将其视为一个简单的点对点或以太网设备，它不是从物理介质接收数据包，
  而是从用户空间程序接收数据包，并且不是通过物理介质发送数据包，
  而是将它们写入用户空间程序。为了使用该驱动程序，程序需要打开 /dev/net/tun 并发出相应的 ioctl() 来向内核注册网络设备。
  网络设备将根据所选选项显示为 tunXX 或 tapXX。当程序关闭文件描述符时，网络设备及其所有相关路由将消失。
  根据所选设备类型，用户空间程序需要读取/写入 IP 数据包（使用 tun）或以太网帧（使用 tap）。
  使用哪一种取决于 ioctl() 所给定的标志。
  从 http://vtun.sourceforge.net/tun 下载的包包含两个简单的示例，说明如何使用 tun 和 tap 设备。
  这两个程序都像两网络接口之间的桥接器一样工作：
  br_select.c - 基于 select 系统调用的桥接器
  br_sigio.c  - 基于异步 I/O 和 SIGIO 信号的桥接器
  不过，最好的例子是 VTun (http://vtun.sourceforge.net) ：))

2. 配置
================

  创建设备节点：

     如果还没有创建 /dev/net 目录，请创建它
     mknod /dev/net/tun c 10 200

  设置权限：

     例如：chmod 0666 /dev/net/tun

  允许非 root 用户访问该设备没有任何危害，因为创建网络设备或连接到不属于当前用户的网络设备需要 CAP_NET_ADMIN 权限。
  如果您希望创建持久设备并将其所有权分配给非特权用户，则需要让 /dev/net/tun 设备对这些用户可用。
  驱动模块自动加载

     确保在您的内核中启用了“内核模块加载器” - 模块自动加载支持。内核应在首次访问时加载它。
手动加载

    手动插入模块：

    modprobe tun

  如果你采用后一种方式，每次需要时都必须手动加载模块。而采用前一种方式，则会在打开 /dev/net/tun 时自动加载模块。

3. 程序接口
===========

3.1 网络设备分配
------------------

`char *dev` 应该是设备的名称格式字符串（例如 "tun%d"），但据我所见，这可以是任何有效的网络设备名称。注意，字符指针会被实际的设备名称（例如 "tun0"）覆盖：

  ```c
  #include <linux/if.h>
  #include <linux/if_tun.h>

  int tun_alloc(char *dev)
  {
      struct ifreq ifr;
      int fd, err;

      if( (fd = open("/dev/net/tun", O_RDWR)) < 0 )
          return tun_alloc_old(dev);

      memset(&ifr, 0, sizeof(ifr));

      /* 标志：IFF_TUN   - TUN 设备（无以太网报头）
       *         IFF_TAP   - TAP 设备
       *
       *         IFF_NO_PI - 不提供包信息
       */
      ifr.ifr_flags = IFF_TUN;
      if( *dev )
          strscpy_pad(ifr.ifr_name, dev, IFNAMSIZ);

      if( (err = ioctl(fd, TUNSETIFF, (void *) &ifr)) < 0 ){
          close(fd);
          return err;
      }
      strcpy(dev, ifr.ifr_name);
      return fd;
  }
  ```

3.2 帧格式
------------

如果未设置 IFF_NO_PI 标志，每个帧的格式如下：

     标志 [2 字节]
     协议 [2 字节]
     原始协议（IP、IPv6 等）帧

3.3 多队列 tuntap 接口
----------------------

从 3.8 版本开始，Linux 支持多队列 tuntap，可以使用多个文件描述符（队列）来并行发送或接收数据包。设备分配与之前相同，如果用户希望创建多个队列，必须多次调用带有相同设备名称的 TUNSETIFF，并且需要带上 IFF_MULTI_QUEUE 标志。
`char *dev` 应该是设备的名称，`queues` 是要创建的队列数量，`fds` 用于存储并返回给调用者创建的文件描述符（队列）。每个文件描述符都是一个队列的接口，可以在用户空间中访问：

  ```c
  #include <linux/if.h>
  #include <linux/if_tun.h>

  int tun_alloc_mq(char *dev, int queues, int *fds)
  {
      struct ifreq ifr;
      int fd, err, i;

      if (!dev)
          return -1;

      memset(&ifr, 0, sizeof(ifr));
      /* 标志：IFF_TUN   - TUN 设备（无以太网报头）
       *         IFF_TAP   - TAP 设备
       *
       *         IFF_NO_PI - 不提供包信息
       *         IFF_MULTI_QUEUE - 创建一个多队列设备
       */
      ifr.ifr_flags = IFF_TAP | IFF_NO_PI | IFF_MULTI_QUEUE;
      strcpy(ifr.ifr_name, dev);

      for (i = 0; i < queues; i++) {
          if ((fd = open("/dev/net/tun", O_RDWR)) < 0)
              goto err;
          err = ioctl(fd, TUNSETIFF, (void *)&ifr);
          if (err) {
              close(fd);
              goto err;
          }
          fds[i] = fd;
      }

      return 0;
  err:
      for (--i; i >= 0; i--)
          close(fds[i]);
      return err;
  }
  ```

引入了一个新的 ioctl (TUNSETQUEUE) 来启用或禁用队列。当调用它时带上 IFF_DETACH_QUEUE 标志，队列将被禁用；而带上 IFF_ATTACH_QUEUE 标志则会启用队列。队列在通过 TUNSETIFF 创建后默认是启用状态。
`fd` 是我们要启用或禁用的文件描述符（队列），当 `enable` 为真时我们启用它，否则禁用它：

  ```c
  #include <linux/if.h>
  #include <linux/if_tun.h>

  int tun_set_queue(int fd, int enable)
  {
      struct ifreq ifr;

      memset(&ifr, 0, sizeof(ifr));

      if (enable)
          ifr.ifr_flags = IFF_ATTACH_QUEUE;
      else
          ifr.ifr_flags = IFF_DETACH_QUEUE;

      return ioctl(fd, TUNSETQUEUE, (void *)&ifr);
  }
  ```

通用 TUN/TAP 设备驱动常见问题解答
==================================

1. TUN/TAP 驱动支持哪些平台？

目前该驱动已为以下三个 Unix 平台编写：

  - Linux 内核 2.2.x, 2.4.x
  - FreeBSD 3.x, 4.x, 5.x
  - Solaris 2.6, 7.0, 8.0

2. TUN/TAP 驱动用于什么？

如上所述，TUN/TAP 驱动的主要用途是隧道。它被 VTun（http://vtun.sourceforge.net）所使用。
另一个使用 TUN/TAP 的有趣应用是 pipsecd（http://perso.enst.fr/~beyssac/pipsec/），这是一个用户空间的 IPSec 实现，可以使用完整的内核路由（与 FreeS/WAN 不同）。
3. 虚拟网络设备是如何工作的？

虚拟网络设备可以看作是一个简单的点对点或以太网设备，与从物理介质接收数据包不同，它从用户空间程序接收数据包；与通过物理介质发送数据包不同，它将数据包发送到用户空间程序。假设你在 tap0 上配置了 IPv6，那么每当内核向 tap0 发送一个 IPv6 数据包时，这个数据包就会传递给应用程序（例如 VTun）。该应用程序会对数据包进行加密、压缩，并通过 TCP 或 UDP 发送到另一端。另一端的应用程序接收到数据后进行解压和解密，并将数据包写入 TAP 设备，内核会像处理来自真实物理设备的数据包一样处理这些数据包。

4. TUN 驱动和 TAP 驱动之间的区别是什么？

TUN 处理 IP 帧，而 TAP 处理以太网帧。
这意味着当你使用 TUN 时需要读写 IP 数据包，而在使用 TAP 时则需要读写以太网帧。

5. BPF 和 TUN/TAP 驱动之间的区别是什么？

BPF 是一种高级的数据包过滤器。它可以附加到现有的网络接口上，但不提供虚拟网络接口。而 TUN/TAP 驱动则提供了虚拟网络接口，并且可以在该接口上附加 BPF。

6. TAP 驱动是否支持内核以太网桥接？

是的。Linux 和 FreeBSD 的驱动支持以太网桥接。
