=============
MSG_ZEROCOPY
=============

简介
=====

MSG_ZEROCOPY 标志使得套接字发送调用能够避免复制。目前该功能已实现在 TCP、UDP 和带有 virtio 传输的 VSOCK 套接字中。

机会与注意事项
-----------------------

在用户进程和内核之间复制大量缓冲区可能会非常昂贵。Linux 支持多种可以避免复制的接口，例如 sendfile 和 splice。MSG_ZEROCOPY 标志将底层的避免复制机制扩展到了常见的套接字发送调用中。

避免复制并不是免费午餐。如当前实现的那样，通过页面固定（page pinning），它将每字节复制成本替换为页面管理和完成通知开销。因此，MSG_ZEROCOPY 通常只有在写入量超过约 10 KB 时才有效。

页面固定还会改变系统调用语义。它暂时在进程和网络堆栈之间共享缓冲区。与复制不同的是，在系统调用返回后，进程不能立即覆盖缓冲区，否则可能会修改正在传输中的数据。内核完整性不会受到影响，但有缺陷的程序可能会破坏其自身数据流。

内核会在数据可以安全修改时返回一个通知。

将现有应用程序转换为 MSG_ZEROCOPY 并不总是像仅仅传递该标志那么简单。

更多信息
---------

本文档大部分内容来自 netdev 2.1 中的一篇较长论文。如需深入了解，请参阅该论文和演讲、LWN.net 的优秀报道或阅读原始代码论文、幻灯片和视频：

    https://netdevconf.org/2.1/session.html?debruijn

  LWN 文章
    https://lwn.net/Articles/726917/

  补丁集
    [PATCH net-next v4 0/9] socket sendmsg MSG_ZEROCOPY
    https://lore.kernel.org/netdev/20170803202945.70750-1-willemdebruijn.kernel@gmail.com

接口
=====

传递 MSG_ZEROCOPY 标志是启用避免复制最明显的步骤，但这并不是唯一的一个步骤。

套接字设置
------------

内核对应用程序传递未定义的标志到 send 系统调用是宽容的，默认情况下会忽略这些标志。为了避免使那些已经意外传递此标志的传统进程启用避免复制模式，进程必须首先通过设置套接字选项来表明意图：

::

    if (setsockopt(fd, SOL_SOCKET, SO_ZEROCOPY, &one, sizeof(one)))
        error(1, errno, "setsockopt zerocopy");

传输
------------

对 send（或 sendto、sendmsg、sendmmsg）本身的更改非常简单。
传递新的标志
::

    ret = send(fd, buf, sizeof(buf), MSG_ZEROCOPY);

零拷贝失败将返回-1，并设置errno为ENOBUFS。这发生在套接字超出其optmem限制或用户超出锁定页面的ulimit时。
混合使用避免拷贝和拷贝
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

许多工作负载包含大量和少量缓冲区的混合。由于对于小数据包而言，避免拷贝比直接拷贝更昂贵，因此该功能是通过一个标志来实现的。与带有标志的调用混合同不带标志的调用是安全的。
通知
-------------

内核需要在可以安全重用之前传递的缓冲区时通知进程。它在套接字错误队列上排队完成通知，类似于传输时间戳接口。
通知本身是一个简单的标量值。每个套接字维护一个内部的32位无符号计数器。每次带有MSG_ZEROCOPY标志且成功发送数据的send调用都会递增这个计数器。如果调用失败或长度为零，则不会递增计数器。
计数器统计的是系统调用的次数，而不是字节数。在UINT_MAX次调用后，计数器会回绕。
通知接收
~~~~~~~~~~~~~~~~~~~~~~

下面的代码片段展示了API的使用。在最简单的情况下，每个send系统调用之后跟着一次poll和在错误队列上的recvmsg操作。
从错误队列读取始终是非阻塞操作。poll调用在那里是为了在有错误待处理时阻塞，并在输出标志中设置POLLERR。这个标志不需要在事件字段中设置，因为错误总是无条件地被信号量通知。
::

    pfd.fd = fd;
    pfd.events = 0;
    if (poll(&pfd, 1, -1) != 1 || (pfd.revents & POLLERR) == 0)
        error(1, errno, "poll");

    ret = recvmsg(fd, &msg, MSG_ERRQUEUE);
    if (ret == -1)
        error(1, errno, "recvmsg");

    read_notification(msg);

示例仅用于演示目的。实际上，更高效的做法是不等待通知，而是在几次send调用之后非阻塞地读取。
通知可以与其他套接字操作乱序处理。通常情况下，有错误排队的套接字会阻止其他操作直到错误被读取。然而，零拷贝通知具有零错误码，以确保不会阻止send和recv调用。
### 通知批处理

可以使用`recvmmsg`调用一次读取多个未决的数据包。这通常不需要。内核在每个消息中返回的不是一个单一的值，而是一个范围。当有一个未决的通知等待错误队列接收时，它会合并连续的通知。当一个新的通知即将入队时，它会检查新的值是否扩展了队列尾部通知的范围。如果是这样，它会丢弃新的通知数据包，并增加未决通知的范围上限值。对于像TCP这样的按顺序确认数据的协议，每个通知都可以被压缩到前一个通知中，因此在任何时刻都不会有超过一个未决的通知。有序交付是常见的情况，但不能保证。通知可能会在重传和套接字拆除时无序到达。

### 通知解析

下面的代码片段展示了如何解析控制消息：上一个片段中的`read_notification()`调用。通知是以标准错误格式`sock_extended_err`编码的。控制数据中的`level`和`type`字段是协议族特定的，例如`IP_RECVERR`或`IPV6_RECVERR`（对于TCP或UDP套接字）。对于VSOCK套接字，`cmsg_level`将是`SOL_VSOCK`，`cmsg_type`将是`VSOCK_RECVERR`。错误来源是新的类型`SO_EE_ORIGIN_ZEROCOPY`。如前所述，`ee_errno`为零，以避免阻塞套接字上的读写系统调用。32位通知范围编码为`[ee_info, ee_data]`。这个范围是包含式的。结构体中的其他字段必须被视为未定义，除了`ee_code`，如下所述：

```c
struct sock_extended_err *serr;
struct cmsghdr *cm;

cm = CMSG_FIRSTHDR(msg);
if (cm->cmsg_level != SOL_IP &&
    cm->cmsg_type != IP_RECVERR)
    error(1, 0, "cmsg");

serr = (void *) CMSG_DATA(cm);
if (serr->ee_errno != 0 ||
    serr->ee_origin != SO_EE_ORIGIN_ZEROCOPY)
    error(1, 0, "serr");

printf("completed: %u..%u\n", serr->ee_info, serr->ee_data);
```

### 延迟复制

传递标志`MSG_ZEROCOPY`是给内核的一个提示，要求应用复制避免，并且是一个合同，即内核将排队一个完成通知。这不是一个保证复制会被省略。
避免复制并不总是可行的。不支持分散/集中I/O（scatter-gather I/O）的设备无法发送由内核生成的协议头加上零复制用户数据组成的报文。有时，报文可能需要在堆栈深处转换为私有数据副本，例如为了计算校验和。

在所有这些情况下，当内核释放共享页面时会返回一个完成通知。这个通知可能在（已复制的）数据完全传输之前到达。因此，零复制完成通知并不是传输完成通知。如果数据在缓存中不再热，延迟复制可能会比立即在系统调用中复制更昂贵。此外，进程还会因为没有实际收益而承担通知处理的成本。因此，内核会在数据通过复制完成时设置标志SO_EE_CODE_ZEROCOPY_COPIED，并在返回时将其设置在ee_code字段中。

进程可以利用此信号停止在同一套接字上的后续请求中传递标志MSG_ZEROCOPY。

实现
====

环回
----

对于TCP和UDP：
发送到本地套接字的数据可以在接收进程未读取其套接字的情况下无限排队。这种无界的通知延迟是不可接受的。因此，所有使用MSG_ZEROCOPY生成并环回到本地套接字的报文都会触发延迟复制。这包括环回到包套接字（例如tcpdump）和tun设备的情况。

对于VSOCK：
发送到本地套接字的数据路径与非本地套接字相同。

测试
====

更现实的示例代码可以在内核源码中的`tools/testing/selftests/net/msg_zerocopy.c`找到。
请注意环回限制。测试可以在一对主机之间运行。但如果在本地的一对进程中运行，例如通过msg_zerocopy.sh在命名空间之间的veth对之间运行，测试将不会显示任何改进。为了测试，可以通过使`skb_orphan_frags_rx`与`skb_orphan_frags`相同来暂时放宽环回限制。

对于VSOCK类型的套接字示例，可以在`tools/testing/vsock/vsock_test_zerocopy.c`中找到。
