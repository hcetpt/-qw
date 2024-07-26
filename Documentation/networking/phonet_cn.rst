### SPDX 许可证标识符: GPL-2.0
### 包含: <isonum.txt>

============================
Linux Phonet 协议族
============================

简介
------------

Phonet 是诺基亚蜂窝调制解调器用于进程间通信（IPC）和远程过程调用（RPC）的分组协议。通过 Linux Phonet 套接字族，Linux 主机进程可以从/向调制解调器或其他连接到调制解调器的外部设备接收和发送消息。调制解调器负责路由。Phonet 分组可以通过多种硬件连接进行交换，具体取决于设备类型，包括：

  - 使用 CDC Phonet 接口的 USB，
  - 红外线，
  - 蓝牙，
  - 具有专用“FBUS”线路纪律的 RS232 串行端口，
  - 与某些 TI OMAP 处理器配合使用的 SSI 总线。

分组格式
--------------

Phonet 分组具有如下所示的通用头部结构：

  ```c
  struct phonethdr {
    uint8_t  pn_media;  /* 媒体类型（链路层标识符） */
    uint8_t  pn_rdev;   /* 接收方设备 ID */
    uint8_t  pn_sdev;   /* 发送方设备 ID */
    uint8_t  pn_res;    /* 资源 ID 或功能 */
    uint16_t pn_length; /* 大端字节长度（减去 6） */
    uint8_t  pn_robj;   /* 接收方对象 ID */
    uint8_t  pn_sobj;   /* 发送方对象 ID */
  };
  ```

在 Linux 上，链路层头部包含 pn_media 字节（见下文）。接下来的 7 个字节是网络层头部的一部分。
设备 ID 被拆分：高 6 位构成设备地址，而低 2 位用于复用，如同 8 位的对象标识符一样。因此，可以将 Phonet 视为一个具有 6 位地址空间和 10 位传输协议（类似于 IP 中的端口号）的网络层。
调制解调器始终具有地址编号零。所有其他设备都有其唯一的 6 位地址。
链路层
----------

Phonet 链路始终是点对点链路。链路层头部由单个 Phonet 媒体类型字节组成。它从调制解调器的角度唯一地标识了分组传输的链路。每个 Phonet 网络设备都应根据需要添加并设置媒体类型字节。为了方便起见，提供了一个通用的 `phonet_header_ops` 链路层头部操作结构。它根据网络设备的硬件地址设置媒体类型。
Linux Phonet 网络接口支持一种专用的链路层数据包类型（ETH_P_PHONET），该类型超出了以太网类型范围。它们只能发送和接收 Phonet 数据包。
虚拟 TUN 隧道设备驱动程序也可以用于 Phonet。这需要使用 IFF_TUN 模式，并且 _不_ 设置 IFF_NO_PI 标志。在这种情况下，没有链路层头部，因此没有 Phonet 媒体类型字节。
请注意，Phonet 接口不允许重新排序数据包，因此只应使用（默认的）Linux FIFO qdisc 与之一起使用。
网络层
-------------

Phonet 套接字地址族映射了 Phonet 数据包头部如下所示：

  结构体 sockaddr_pn {
    sa_family_t spn_family;    /* AF_PHONET */
    uint8_t     spn_obj;       /* 对象 ID */
    uint8_t     spn_dev;       /* 设备 ID */
    uint8_t     spn_resource;  /* 资源或功能 */
    uint8_t     spn_zero[...]; /* 填充 */
  };

资源字段仅在发送和接收时使用；
bind() 和 getsockname() 将忽略它。
低级数据报协议
---------------------------

应用程序可以使用来自 PF_PHONET 家族的 Phonet 数据报套接字协议发送 Phonet 消息。每个套接字绑定到可用的 2^10 个对象 ID 中的一个，并且可以向任何其他对等方发送和接收数据包。

  结构体 sockaddr_pn addr = { .spn_family = AF_PHONET, };
  ssize_t len;
  socklen_t addrlen = sizeof(addr);
  int fd;

  fd = socket(PF_PHONET, SOCK_DGRAM, 0);
  bind(fd, (结构体 sockaddr *)&addr, sizeof(addr));
  /* ... */

  sendto(fd, msg, msglen, 0, (结构体 sockaddr *)&addr, sizeof(addr));
  len = recvfrom(fd, buf, sizeof(buf), 0,
                 (结构体 sockaddr *)&addr, &addrlen);

此协议遵循 SOCK_DGRAM 的无连接语义，
然而，connect() 和 getpeername() 不受支持，因为它们对于 Phonet 使用情况似乎没有用处（可以轻松添加）。
资源订阅
---------------------

一个 Phonet 数据报套接字可以订阅任意数量的 8 位 Phonet 资源，如下所示：

  uint32_t res = 0xXX;
  ioctl(fd, SIOCPNADDRESOURCE, &res);

使用 SIOCPNDELRESOURCE I/O 控制请求取消订阅，或者当套接字关闭时也会取消订阅。
值得注意的是，任何时候都不能有超过一个套接字订阅给定资源。否则，ioctl() 将返回 EBUSY。
Phonet 管道协议
--------------------

Phonet 管道协议是一个简单的有序数据包协议，具有端到端拥塞控制。它使用被动监听套接字范式。监听套接字绑定到一个唯一的空闲对象 ID。每个监听套接字可以处理多达 255 个同时连接，每个 accept() 的套接字一个。

  int lfd, cfd;

  lfd = socket(PF_PHONET, SOCK_SEQPACKET, PN_PROTO_PIPE);
  listen (lfd, INT_MAX);

  /* ... */
  cfd = accept(lfd, NULL, NULL);
  for (;;)
  {
    char buf[...];
    ssize_t len = read(cfd, buf, sizeof(buf));

    /* ... */

    write(cfd, msg, msglen);
  }

传统上，两个端点之间的连接是由一个“第三方”应用建立的。这意味着两个端点都是被动的。
从 Linux 内核版本 2.6.39 开始，也可以直接使用 connect() 在主动端连接两个端点。这旨在支持较新的诺基亚无线调制解调器 API，例如在诺基亚 Slim 调制解调器中找到的，在 ST-Ericsson U8500 平台上。

  结构体 sockaddr_spn spn;
  int fd;

  fd = socket(PF_PHONET, SOCK_SEQPACKET, PN_PROTO_PIPE);
  memset(&spn, 0, sizeof(spn));
  spn.spn_family = AF_PHONET;
  spn.spn_obj = ...;
  spn.spn_dev = ...;
  spn.spn_resource = 0xD9;
  connect(fd, (结构体 sockaddr *)&spn, sizeof(spn));
  /* 正常 I/O 操作 ... */
  close(fd);

.. 注意:

   当轮询已连接的管道套接字以进行写入时，存在一种内在的竞争条件，即在轮询和写入系统调用之间可能会失去可写性。在这种情况下，除非启用非阻塞模式，否则套接字将一直阻塞直到再次能够写入。
管道协议在 SOL_PNPIPE 层面提供了两种套接字选项：

  PNPIPE_ENCAP 接受一个整数值 (int)，包括：

    PNPIPE_ENCAP_NONE:
      套接字正常运行（默认）
PNPIPE_ENCAP_IP:  
   该套接字被用作虚拟IP接口的后端。这需要具备CAP_NET_ADMIN权限。诺基亚调制解调器上的GPRS数据支持可以使用此功能。请注意，在这种模式下，无法可靠地对该套接字进行poll()或read()操作。

PNPIPE_IFINDEX  
   是一个只读整数值。它包含了由PNPIPE_ENCAP创建的网络接口的接口索引，如果未启用封装，则其值为零。

PNPIPE_HANDLE  
   是一个只读整数值。它包含了底层标识符（"管道句柄"）的值。这个值仅对已经连接或正在连接的套接字描述符有定义。

作者
------
Linux Phonet 最初由Sakari Ailus编写。
其他贡献者包括Mikä Liljeberg、Andras Domokos、Carlos Chinea和Rémi Denis-Courmont。

版权所有 © 2008 诺基亚公司
