============= 
MSG_ZEROCOPY 
============= 

简介
===== 

MSG_ZEROCOPY 标志为套接字发送调用启用了复制避免功能。
此特性当前已在TCP、UDP和VSOCK（使用virtio传输）套接字中实现。
机遇与注意事项
---------------- 

在用户进程与内核之间复制大型缓冲区可能会很昂贵。Linux支持多种可以避免复制的接口，例如sendfile和splice。MSG_ZEROCOPY标志将底层的复制避免机制扩展到了常见的套接字发送调用上。
复制避免并非免费午餐。如当前实现所示，通过页面固定，它将每字节复制的成本替换为页面记账和完成通知开销。因此，通常只有当写入大小超过大约10KB时，MSG_ZEROCOPY才有效。
页面固定还会改变系统调用的语义。它会暂时在进程与网络堆栈之间共享缓冲区。与复制不同，在系统调用返回后，进程不能立即覆盖缓冲区，否则可能会修改正在传输的数据。内核完整性不会受到影响，但有bug的程序可能会破坏其自身数据流。
内核会在数据安全可被修改时返回一个通知。
将现有应用程序转换为使用MSG_ZEROCOPY并不总是像仅仅传递该标志那样简单。
更多信息
--------- 

本文档的大部分内容来源于在netdev 2.1上发表的一篇较长论文。要了解更深入的信息，请参阅那篇论文和演讲、LWN.net上的出色报道或阅读原始代码论文、幻灯片、视频：
    https://netdevconf.org/2.1/session.html?debruijn

  LWN文章
    https://lwn.net/Articles/726917/

  补丁集
    [PATCH net-next v4 0/9] socket sendmsg MSG_ZEROCOPY
    https://lore.kernel.org/netdev/20170803202945.70750-1-willemdebruijn.kernel@gmail.com

接口
===== 

传递MSG_ZEROCOPY标志是启用复制避免最明显的步骤，但并非唯一步骤。
套接字设置
------------ 

内核在应用程序向send系统调用传递未定义的标志时表现得很宽容。默认情况下，它会简单地忽略这些标志。为了避免为那些已经错误地传递此标志的旧版进程启用复制避免模式，进程必须首先通过设置套接字选项来表明意图：

```
if (setsockopt(fd, SOL_SOCKET, SO_ZEROCOPY, &one, sizeof(one)))
    error(1, errno, "setsockopt zerocopy");
```

传输
------------ 

对send（或sendto、sendmsg、sendmmsg）本身的更改非常简单。
传递新标志：

```c
ret = send(fd, buf, sizeof(buf), MSG_ZEROCOPY);
```

零复制失败会返回-1，并设置errno为ENOBUFS。这发生在套接字超出其optmem限制或用户超出锁定页面的ulimit时。

### 避免复制与复制的混合使用

许多工作负载混合了大缓冲区和小缓冲区。因为对于小数据包而言，避免复制比实际复制更昂贵，因此该功能是通过一个标志来实现的。将带有该标志的调用与不带该标志的调用混合使用是安全的。

### 通知

内核必须在可以安全地重用之前传递的缓冲区时通知进程。它会在套接字错误队列上排队完成通知，类似于传输时间戳接口。
通知本身是一个简单的标量值。每个套接字维护一个内部无符号32位计数器。每次带有`MSG_ZEROCOPY`标志的`send`调用成功发送数据时，计数器都会递增。在失败的情况下或者被调用时长度为零，则不会递增计数器。

计数器计算的是系统调用的调用次数，而不是字节数。在`UINT_MAX`次调用后计数器会回绕。

### 通知接收

下面的代码片段展示了API的使用。最简单的情况下，每次`send`系统调用之后跟着一次对错误队列的`poll`和`recvmsg`调用。

从错误队列读取总是非阻塞操作。`poll`调用在那里是为了在有错误待处理时阻塞，并且会在输出标志中设置`POLLERR`。该标志不必在`events`字段中设置。错误无条件地被触发。

```c
pfd.fd = fd;
pfd.events = 0;
if (poll(&pfd, 1, -1) != 1 || pfd.revents & POLLERR == 0)
    error(1, errno, "poll");

ret = recvmsg(fd, &msg, MSG_ERRQUEUE);
if (ret == -1)
    error(1, errno, "recvmsg");

read_notification(msg);
```

这个例子仅用于演示目的。实际上，更高效的做法是在几次`send`调用之间不等待通知，而是进行非阻塞读取。

通知可以与套接字上的其他操作乱序处理。通常，如果套接字上有错误排队，那么会阻止其他操作直到错误被读取。然而，零复制通知具有零错误码，以确保不阻止`send`和`recv`调用。
### 通知批处理

可以使用`recvmmsg`调用一次性读取多个待处理的数据包。这通常并不需要。在每个消息中，内核返回的不是一个单一的值，而是一个范围。当有一个错误队列上的待接收的通知时，它会合并连续的通知。当一个新的通知即将被加入队列时，它会检查新的值是否扩展了队列尾部通知的范围。如果是这样，它会丢弃新的通知数据包，并增加待处理通知的范围上限值。
对于像TCP这样的按顺序确认数据的协议，每个通知都可以被压缩到前一个通知中，因此任何时候最多只有一个通知是待处理的。
有序交付是常见的情况，但并不能保证。在重传和套接字拆除时，通知可能会无序到达。

### 通知解析

下面的代码片段展示了如何解析控制消息：即上一个代码片段中的`read_notification()`调用。一个通知采用标准的错误格式编码，即`sock_extended_err`。
在控制数据中的`level`和`type`字段是特定于协议族的，如`IP_RECVERR`或`IPV6_RECVERR`（针对TCP或UDP套接字）。
对于VSOCK套接字，`cmsg_level`将是`SOL_VSOCK`，而`cmsg_type`将是`VSOCK_RECVERR`。
错误来源是一个新的类型`SO_EE_ORIGIN_ZEROCOPY`。`ee_errno`为零，如前所述，以避免阻塞在套接字上的读写系统调用。
32位的通知范围编码为`[ee_info, ee_data]`。这个范围是包含式的。结构体中的其他字段必须被视为未定义的，除了`ee_code`，如下所述：
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

printf("完成: %u..%u\n", serr->ee_info, serr->ee_data);
```

### 延迟复制

传递标志`MSG_ZEROCOPY`是给内核的一个提示，要求应用复制避免，并且是一个合同约定，即内核将排队一个完成通知。但这并不是复制被跳过的保证。
避免复制并不总是可行的。不支持分散/集中 I/O 的设备无法发送由内核生成的协议头加上零拷贝用户数据组成的报文。有时可能需要将报文转换为栈深处的数据私有副本，例如为了计算校验和。

在所有这些情况下，当内核释放对共享页面的控制时，会返回一个完成通知。该通知可能会在（已拷贝的）数据完全传输之前到达。零拷贝完成通知并不是传输完成通知，因此如果数据不再缓存中保持热态，则延迟拷贝可能比立即在系统调用中进行拷贝更昂贵。进程还会因无益的通知处理而产生成本。出于这个原因，如果数据是通过拷贝完成的，内核会在返回时设置 `ee_code` 字段中的 `SO_EE_CODE_ZEROCOPY_COPIED` 标志来发出信号。
一个进程可以利用此信号来停止在同一套接字上的后续请求中传递 `MSG_ZEROCOPY` 标志。

实现
====

环回
----

对于TCP和UDP：
发送到本地套接字的数据可以无限期排队，直到接收进程读取其套接字。不可接受无界的通知延迟。因此，所有使用 `MSG_ZEROCOPY` 生成并循环到本地套接字的报文都将产生延迟拷贝。这包括循环到包套接字（例如tcpdump）和tun设备的情况。
对于VSOCK：
发送到本地套接字的数据路径与非本地套接字相同。

测试
====

更现实的示例代码可以在内核源码的 `tools/testing/selftests/net/msg_zerocopy.c` 中找到。
请注意环回约束。测试可以在一对主机之间运行。但如果在一个本地进程对之间运行，例如在命名空间间的veth对之间使用 `msg_zerocopy.sh` 运行时，测试将不会显示出任何改进。为了测试，可以通过使 `skb_orphan_frags_rx` 与 `skb_orphan_frags` 相同来暂时放宽环回限制。
对于VSOCK类型的套接字示例可以在 `tools/testing/vsock/vsock_test_zerocopy.c` 中找到。
