SPDX 许可证标识符: GPL-2.0

============
时间戳
============

1. 控制接口
=====================

接收网络数据包的时间戳接口如下：

SO_TIMESTAMP
  为每个传入的数据包生成一个系统时间（不一定是单调递增的）的时间戳。通过 recvmsg() 在控制消息中以微秒精度报告该时间戳。
  SO_TIMESTAMP 被定义为 SO_TIMESTAMP_NEW 或 SO_TIMESTAMP_OLD，具体取决于架构类型和 libc 的 time_t 表示方式。
  控制消息格式为在结构体 __kernel_old_timeval 中（对于 SO_TIMESTAMP_OLD 选项）或在结构体 __kernel_sock_timeval 中（对于 SO_TIMESTAMP_NEW 选项）。

SO_TIMESTAMPNS
  与 SO_TIMESTAMP 相同的时间戳机制，但以纳秒精度通过 struct timespec 报告时间戳。
  SO_TIMESTAMPNS 被定义为 SO_TIMESTAMPNS_NEW 或 SO_TIMESTAMPNS_OLD，具体取决于架构类型和 libc 的 time_t 表示方式。
  控制消息格式为在 struct timespec 中（对于 SO_TIMESTAMPNS_OLD 选项）或在 struct __kernel_timespec 中（对于 SO_TIMESTAMPNS_NEW 选项）。

IP_MULTICAST_LOOP + SO_TIMESTAMP[NS]
  仅适用于多播：通过读取环回的数据包接收时间戳来获取近似的发送时间戳。

SO_TIMESTAMPING
  在接收、发送或两者都生成时间戳。支持多个时间戳来源，包括硬件。支持为流套接字生成时间戳。

1.1 SO_TIMESTAMP（也包括 SO_TIMESTAMP_OLD 和 SO_TIMESTAMP_NEW）
-------------------------------------------------------------

此套接字选项允许在接收路径上对数据报进行时间戳处理。由于在网络堆栈早期阶段可能不知道目标套接字（如果有的话），因此必须为所有数据包启用此功能。对于所有早期接收时间戳选项也是同样的情况。

关于接口详情，请参见 `man 7 socket`
### 始终使用 SO_TIMESTAMP_NEW 时间戳以始终获取 struct __kernel_sock_timeval 格式的时间戳
SO_TIMESTAMP_OLD 在 32 位机器上从 2038 年之后会返回错误的时间戳

#### 1.2 SO_TIMESTAMPNS（也包括 SO_TIMESTAMPNS_OLD 和 SO_TIMESTAMPNS_NEW）
--------------------------------------------------------------------------------

此选项与 SO_TIMESTAMP 相同，只是返回的数据类型不同。其 struct timespec 允许比 SO_TIMESTAMP 的 timeval（毫秒）更高的分辨率（纳秒）时间戳。
始终使用 SO_TIMESTAMPNS_NEW 时间戳以始终获取 struct __kernel_timespec 格式的时间戳。
SO_TIMESTAMPNS_OLD 在 32 位机器上从 2038 年之后会返回错误的时间戳。

#### 1.3 SO_TIMESTAMPING（也包括 SO_TIMESTAMPING_OLD 和 SO_TIMESTAMPING_NEW）
----------------------------------------------------------------------------------------

支持多种类型的时间戳请求。因此，此套接字选项接受一个标志位图，而不是布尔值。在以下代码中：

```c
err = setsockopt(fd, SOL_SOCKET, SO_TIMESTAMPING, &val, sizeof(val));
```

`val` 是一个整数，可以设置以下任意位。设置其他位将返回 EINVAL，并且不会改变当前状态。此套接字选项配置了单个 sk_buff 的时间戳生成（1.3.1）、向套接字的错误队列报告时间戳（1.3.2）以及选项（1.3.3）。时间戳生成也可以通过在单个 sendmsg 调用中使用 cmsg 来启用（1.3.4）。

##### 1.3.1 时间戳生成
^^^^^^^^^^^^^^^^^^^^^^^^^^

某些位是向内核请求尝试生成时间戳。它们的任何组合都是有效的。对这些位的更改仅适用于新创建的数据包，而不适用于已经在内核中的数据包。因此，可以通过在两个 setsockopt 调用之间嵌入一个 send() 调用来选择性地请求一组数据包的时间戳（例如，进行采样），一个用于启用时间戳生成，另一个用于禁用它。
时间戳也可能由于其他原因而生成，而不仅仅是应某个特定套接字的要求，例如当全局启用了接收时间戳时，如前面所述。
SOF_TIMESTAMPING_RX_HARDWARE:
  请求由网络适配器生成的接收时间戳
SOF_TIMESTAMPING_RX_SOFTWARE:
  请求数据进入内核时的接收时间戳。这些时间戳在设备驱动程序将数据包交给内核接收栈后立即生成
SOF_TIMESTAMPING_TX_HARDWARE:
  请求由网络适配器生成的发送时间戳。此标志可以通过套接字选项和控制消息启用
SOF_TIMESTAMPING_TX_SOFTWARE:
  请求数据离开内核时的发送时间戳。这些时间戳尽可能地靠近设备驱动程序生成，但总是在将数据包传递给网络接口之前。因此，它们需要驱动程序支持，并非所有设备都可用
此标志可以通过套接字选项和控制消息启用
SOF_TIMESTAMPING_TX_SCHED:
  请求数据包进入调度器前的发送时间戳。内核发送延迟如果较长，通常由排队延迟主导。此时间戳与在SOF_TIMESTAMPING_TX_SOFTWARE处获取的时间戳之间的差异可以暴露这种延迟，而不受协议处理的影响。如果存在协议处理延迟，可以通过从send()之前的用户空间时间戳中减去此时间戳来计算。在具有虚拟设备的机器上，传输的数据包会经过多个设备和多个数据包调度器，在每一层都会生成一个时间戳。这允许对排队延迟进行细粒度测量。此标志可以通过套接字选项和控制消息启用
SOF_TIMESTAMPING_TX_ACK:
  请求发送缓冲区中的所有数据被确认时的发送时间戳。这仅适用于可靠的协议。目前仅实现了TCP。对于该协议，可能会过高地报告测量结果，因为时间戳是在所有数据（包括send()时的数据）被确认时生成的：累积确认。该机制忽略了SACK和FACK
此标志可以通过套接字选项和控制消息启用

1.3.2 时间戳报告
^^^^^^^^^^^^^^^^^^^^^^^^^^

另外三个位控制生成的控制消息中将报告哪些时间戳。对这些位的更改会立即在堆栈中的时间戳报告位置生效。只有设置了相关时间戳请求的数据包才会报告时间戳
SOF_TIMESTAMPING_SOFTWARE:
  如果有软件时间戳，则报告任何软件时间戳
### SOF_TIMESTAMPING_SYS_HARDWARE:
此选项已弃用且被忽略。

### SOF_TIMESTAMPING_RAW_HARDWARE:
当可用时，报告由 `SOF_TIMESTAMPING_TX_HARDWARE` 生成的硬件时间戳。

#### 1.3.3 时间戳选项
^^^^^^^^^^^^^^^^^^^^^^^

接口支持以下选项：

### SOF_TIMESTAMPING_OPT_ID:
为每个数据包生成一个唯一标识符。一个进程可以同时有多个时间戳请求。在传输路径中，数据包可能会重新排序，例如在数据包调度器中。在这种情况下，时间戳将按与原始 `send()` 调用不同的顺序排队到错误队列中。仅凭时间戳顺序或有效载荷检查，有时无法唯一地将时间戳与原始 `send()` 调用匹配。此选项在 `send()` 时为每个数据包关联一个唯一标识符，并将其与时间戳一起返回。该标识符来源于每个套接字的一个 u32 计数器（会循环）。对于数据报套接字，计数器随着每个发送的数据包递增；对于流套接字，它随着每个字节递增。对于流套接字，还需设置 `SOF_TIMESTAMPING_OPT_ID_TCP`，详见下面的部分。
计数器从零开始。首次启用该套接字选项时进行初始化。每次启用该选项后都会重置计数器，即使之前已禁用过。重置计数器不会改变系统中现有数据包的标识符。
此选项仅针对发送时间戳实现。在那里，时间戳总是与 `struct sock_extended_err` 一起循环。
该选项修改字段 `ee_data`，以传递一个在整个可能并发的时间戳请求中唯一的标识符。

### SOF_TIMESTAMPING_OPT_ID_TCP:
对于新的TCP时间戳应用程序，请与 `SOF_TIMESTAMPING_OPT_ID` 一起使用此修饰符。`SOF_TIMESTAMPING_OPT_ID` 定义了流套接字中计数器的递增方式，但其起始点并不完全直观。此选项修复了这一点。
对于流套接字，如果设置了 `SOF_TIMESTAMPING_OPT_ID`，则也应始终设置此选项。对于数据报套接字，此选项无效。
合理的期望是，计数器会在系统调用时重置为零，以便随后写入 N 字节会产生计数器值为 N-1 的时间戳。`SOF_TIMESTAMPING_OPT_ID_TCP` 在所有条件下实现了这种行为。
SOF_TIMESTAMPING_OPT_ID 通常报告相同的时间戳，特别是在设置套接字选项时没有数据正在传输的情况下。如果有数据正在传输，则可能会因为输出队列（SIOCOUTQ）的长度而有所不同。

差异的原因在于基于 snd_una 还是 write_seq：
- `snd_una` 是对等方确认的流中的偏移量。这取决于进程控制之外的因素，例如网络往返时间（RTT）。
- `write_seq` 是进程写入的最后一个字节。这个偏移量不受外部输入的影响。

这种差异在初始创建套接字时配置且没有排队或发送的数据时不太可能被注意到。但无论何时设置套接字选项，SOF_TIMESTAMPING_OPT_ID_TCP 的行为都更稳健。

SOF_TIMESTAMPING_OPT_CMSG：
- 支持所有带时间戳的包的 recv() 控制消息。接收时间戳和 IPv6 包的传输时间戳已经无条件支持控制消息。此选项将其扩展到带有传输时间戳的 IPv4 包。一个用例是通过同时启用套接字选项 IP_PKTINFO 来关联包与其出站设备。

SOF_TIMESTAMPING_OPT_TSONLY：
- 仅适用于传输时间戳。使内核返回时间戳作为控制消息的一部分，而不是与原始包一起返回。这减少了套接字接收预算（SO_RCVBUF）中分配给该包的内存，并且即使 sysctl net.core.tstamp_allow_data 设置为 0 也能提供时间戳。
- 此选项禁用了 SOF_TIMESTAMPING_OPT_CMSG。

SOF_TIMESTAMPING_OPT_STATS：
- 可选统计信息，这些信息与传输时间戳一起获取。
- 必须与 SOF_TIMESTAMPING_OPT_TSONLY 一起使用。当传输时间戳可用时，统计信息会在单独的控制消息（类型为 SCM_TIMESTAMPING_OPT_STATS）中以 TLV 列表的形式提供。这些统计信息允许应用程序将各种传输层统计信息与传输时间戳相关联，例如某块数据受限于对等方接收窗口的时间长度。
### SOF_TIMESTAMPING_OPT_PKTINFO:
启用带有硬件时间戳的传入数据包的SCM_TIMESTAMPING_PKTINFO控制消息。该消息包含`struct scm_ts_pktinfo`，提供了接收到该数据包的真实接口索引及其在第二层的长度。只有当启用了`CONFIG_NET_RX_BUSY_POLL`并且驱动程序使用NAPI时，才会返回有效的（非零）接口索引。该结构还包含另外两个字段，但这些字段是保留且未定义的。

### SOF_TIMESTAMPING_OPT_TX_SWHW:
当同时启用了`SOF_TIMESTAMPING_TX_HARDWARE`和`SOF_TIMESTAMPING_TX_SOFTWARE`时，请求为传出的数据包生成硬件和软件时间戳。如果生成了两个时间戳，则会将两个独立的消息循环到套接字的错误队列中，每个消息仅包含一个时间戳。

新应用程序被鼓励传递`SOF_TIMESTAMPING_OPT_ID`来区分时间戳，并传递`SOF_TIMESTAMPING_OPT_TSONLY`以忽略`sysctl net.core.tstamp_allow_data`的设置。

一个例外是当进程需要额外的cmsg数据时，例如`SOL_IP/IP_PKTINFO`来检测出站网络接口。此时应传递选项`SOF_TIMESTAMPING_OPT_CMSG`。此选项依赖于访问原始数据包的内容，因此不能与`SOF_TIMESTAMPING_OPT_TSONLY`结合使用。

#### 1.3.4. 通过控制消息启用时间戳
^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^

除了套接字选项外，还可以通过cmsg按写操作请求时间戳生成，仅适用于`SOF_TIMESTAMPING_TX_*`（参见第1.3.1节）。使用此功能，应用程序可以通过`sendmsg()`逐个采样时间戳，而无需承担通过`setsockopt`启用和禁用时间戳的开销：

```c
struct msghdr *msg;
..
cmsg = CMSG_FIRSTHDR(msg);
cmsg->cmsg_level = SOL_SOCKET;
cmsg->cmsg_type = SO_TIMESTAMPING;
cmsg->cmsg_len = CMSG_LEN(sizeof(__u32));
*((__u32 *) CMSG_DATA(cmsg)) = SOF_TIMESTAMPING_TX_SCHED |
                              SOF_TIMESTAMPING_TX_SOFTWARE |
                              SOF_TIMESTAMPING_TX_ACK;
err = sendmsg(fd, msg, 0);
```

通过cmsg设置的`SOF_TIMESTAMPING_TX_*`标志将覆盖通过`setsockopt`设置的`SOF_TIMESTAMPING_TX_*`标志。此外，应用程序仍需通过`setsockopt`启用时间戳报告才能接收时间戳：

```c
__u32 val = SOF_TIMESTAMPING_SOFTWARE |
            SOF_TIMESTAMPING_OPT_ID /* 或其他任何标志 */;
err = setsockopt(fd, SOL_SOCKET, SO_TIMESTAMPING, &val, sizeof(val));
```

### 1.4 字节流时间戳
-------------------------

`SO_TIMESTAMPING`接口支持字节流的时间戳。每个请求被视为请求整个缓冲区内容经过时间戳点时的时间戳。也就是说，对于流选项`SOF_TIMESTAMPING_TX_SOFTWARE`将在所有字节到达设备驱动程序时记录时间戳，无论数据已被转换成多少个数据包。

一般来说，字节流没有自然的分隔符，因此将时间戳与数据关联是非平凡的。一段字节范围可能分布在多个段之间，任何段都可能合并（可能会合并之前独立的`send()`调用所关联的分段缓冲区的部分）。段可以重新排序，同一个字节范围可以在实现重传的协议中同时存在于多个段中。
确保所有时间戳实现相同的语义是非常重要的，无论这些可能的转换如何，否则它们将无法比较。对“罕见”的极端情况进行不同处理是不够的，因为性能调试通常需要关注这些异常情况。实际上，如果正确选择时间戳的语义和测量时间，则可以一致地将时间戳与字节流的各个部分相关联。这一挑战与决定IP分片策略没有区别。在那里，定义是只有第一个分片被打上时间戳。对于字节流，我们选择仅当所有字节通过某个点时才生成时间戳。SOF_TIMESTAMPING_TX_ACK 的定义易于实现和理解。考虑到 SACK 的实现会更复杂，因为可能存在传输空洞和乱序到达。

在主机上，TCP 也可能由于 Nagle 算法、cork、自动 cork、分段和 GSO 而打破缓冲区到 skb 的简单一对一映射。实现通过跟踪传递给 send() 的每个字节来确保所有情况下的正确性，即使在 skb 扩展或合并操作后它不再是最后一个字节。它将相关的序列号存储在 skb_shinfo(skb)->tskey 中。由于一个 skb 只有一个这样的字段，因此只能生成一个时间戳。

在极少数情况下，如果两个请求合并到同一个 skb 上，可能会错过时间戳请求。进程可以通过启用 SOF_TIMESTAMPING_OPT_ID 并比较发送时的字节偏移与每个时间戳返回的值来检测这种情况。可以通过在每次请求之间始终刷新 TCP 堆栈来防止这种情况，例如通过启用 TCP_NODELAY 并禁用 TCP_CORK 和自动 cork。从 Linux 4.7 开始，更好的防止合并的方法是在 sendmsg() 时使用 MSG_EOR 标志。

这些预防措施确保了在网络堆栈本身不对分段进行重排序的情况下，仅在所有字节通过时间戳点时才生成时间戳。堆栈确实试图避免重排序。唯一的例外受管理员控制：可以构建一个不同的包调度配置来延迟来自同一流的不同分段。这种设置很少见。

### 2 数据接口
#### 2.1 SCM_TIMESTAMPING 记录

时间戳是通过 recvmsg() 的辅助数据功能读取的。请参阅 `man 3 cmsg` 获取此接口的详细信息。socket 手册页 (`man 7 socket`) 描述了如何检索由 SO_TIMESTAMP 和 SO_TIMESTAMPNS 生成的时间戳。

#### 2.1.1 SCM_TIMESTAMPING 记录

这些时间戳以控制消息的形式返回，其中 cmsg_level 为 SOL_SOCKET，cmsg_type 为 SCM_TIMESTAMPING，并且有效载荷类型如下：

对于 SO_TIMESTAMPING_OLD：

```c
struct scm_timestamping {
    struct timespec ts[3];
};
```

对于 SO_TIMESTAMPING_NEW：

```c
struct scm_timestamping64 {
    struct __kernel_timespec ts[3];
};
```

始终使用 SO_TIMESTAMPING_NEW 时间戳以始终获取 struct scm_timestamping64 格式的时间戳。
SO_TIMESTAMPING_OLD 在 32 位机器上的 2038 年之后返回错误的时间戳。

该结构最多可返回三个时间戳。这是一个遗留特性。任何时候至少有一个字段非零。大多数时间戳都存储在 ts[0] 中。硬件时间戳存储在 ts[2] 中。
### 翻译：

#### 1. `ts[1]` 用于保存硬件时间戳转换为系统时间后的值

取而代之的是，直接将 NIC 上的硬件时钟设备暴露为一个硬件 PTP 时钟源，以便在用户空间进行时间转换，并可选地与用户空间中的 PTP 栈（如 linuxptp）同步系统时间。关于 PTP 时钟 API，请参阅 `Documentation/driver-api/ptp.rst`。

注意，如果启用了 `SO_TIMESTAMP` 或 `SO_TIMESTAMPNS` 选项，并且与 `SO_TIMESTAMPING` 使用 `SOF_TIMESTAMPING_SOFTWARE` 一起使用时，在缺少真实的软件时间戳的情况下，`recvmsg()` 调用中将生成一个虚假的软件时间戳并将其存储在 `ts[0]` 中。这种情况也发生在硬件发送时间戳上。

#### 2.1.1 发送时间戳与 MSG_ERRQUEUE
^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^

对于发送时间戳，传出的数据包会被回环到套接字的错误队列中，并附带发送的时间戳。进程通过设置 `MSG_ERRQUEUE` 标志并提供足够大的 `msg_control` 缓冲区来接收相关元数据结构的方式调用 `recvmsg()`。`recvmsg` 调用返回原始的传出数据包，并附加两个辅助消息。

- 一个具有 `cm_level` SOL_IP(V6) 和 `cm_type` IP(V6)_RECVERR 的消息嵌入了一个 `struct sock_extended_err`。这定义了错误类型。对于时间戳，`ee_errno` 字段是 `ENOMSG`。
- 另一个辅助消息具有 `cm_level` SOL_SOCKET 和 `cm_type` SCM_TIMESTAMPING。这嵌入了一个 `struct scm_timestamping`。

#### 2.1.1.2 时间戳类型
~~~~~~~~~~~~~~~~~~~~~~~

三个 `struct timespec` 的语义由扩展错误结构中的字段 `ee_info` 定义。它包含一个 `SCM_TSTAMP_*` 类型的值，以定义实际传递给 `scm_timestamping` 的时间戳。

`SCM_TSTAMP_*` 类型与前面讨论的 `SOF_TIMESTAMPING_*` 控制字段是一一对应的，除了一个例外。由于历史原因，`SCM_TSTAMP_SND` 等于零，并且可以同时设置 `SOF_TIMESTAMPING_TX_HARDWARE` 和 `SOF_TIMESTAMPING_TX_SOFTWARE`。如果 `ts[2]` 不为零，则它是前者；否则，它是后者，此时时间戳存储在 `ts[0]` 中。

#### 2.1.1.3 分片
~~~~~~~~~~~~~~~~~~~~~

传出数据报分片的情况很少见，但确实可能发生，例如显式禁用 PMTU 发现。如果传出的数据包被分片，则只有第一个分片被打上时间戳并返回到发送套接字。

#### 2.1.1.4 数据包负载
~~~~~~~~~~~~~~~~~~~~~~

调用应用程序通常不关心接收其最初传递给堆栈的整个数据包负载：套接字错误队列机制只是用来附带时间戳的一种方法。

在这种情况下，应用程序可以选择使用较小的缓冲区读取数据报，甚至长度为 0 的缓冲区。相应地截断负载。然而，直到进程在错误队列上调用 `recvmsg()` 之前，完整的数据包都会排队，占用 `SO_RCVBUF` 预算。
### 2.1.1.5 阻塞读取
~~~~~~~~~~~~~~~~~~~~~

从错误队列中读取数据始终是非阻塞操作。为了等待时间戳，可以使用`poll`或`select`。如果错误队列中有任何数据准备好，`poll()`会在`pollfd.revents`中返回`POLLERR`。无需在`pollfd.events`中传递此标志，该标志会被忽略。更多信息请参阅`man 2 poll`。

### 2.1.2 接收时间戳
^^^^^^^^^^^^^^^^^^^^^^^^

在接收时，没有理由从套接字错误队列中读取数据。`SCM_TIMESTAMPING`辅助数据会与包数据一起通过普通的`recvmsg()`发送。由于这不是一个套接字错误，因此不会伴随有`SOL_IP(V6)/IP(V6)_RECVERROR`消息。在这种情况下，`struct scm_timestamping`中的三个字段的含义是隐式定义的。`ts[0]`保存软件时间戳（如果设置），`ts[1]`再次被废弃，`ts[2]`保存硬件时间戳（如果设置）。

### 3. 硬件时间戳配置：SIOCSHWTSTAMP 和 SIOCGHWTSTAMP
=======================================================

对于预期进行硬件时间戳的每个设备驱动程序，必须初始化硬件时间戳。参数在`include/uapi/linux/net_tstamp.h`中定义如下：

```c
struct hwtstamp_config {
    int flags;      /* 目前没有定义任何标志，必须为零 */
    int tx_type;    /* HWTSTAMP_TX_* */
    int rx_filter;  /* HWTSTAMP_FILTER_* */
};
```

期望的行为通过调用带有指向`struct ifreq`指针的`ioctl(SIOCSHWTSTAMP)`传递给内核和特定设备，其中`ifr_data`指向`struct hwtstamp_config`。`tx_type`和`rx_filter`是给驱动程序的提示，表明期望其执行的操作。如果请求的细粒度过滤不支持，则驱动程序可能会对不仅仅是请求类型的包打上时间戳。
驱动程序可以使用比请求更宽松的配置。预计驱动程序应仅直接实现能够支持的最通用模式。例如，如果硬件可以支持`HWTSTAMP_FILTER_PTP_V2_EVENT`，则通常应始终将`HWTSTAMP_FILTER_PTP_V2_L2_SYNC`升级，并以此类推，因为`HWTSTAMP_FILTER_PTP_V2_EVENT`更通用（并且对应用程序更有用）。
支持硬件时间戳的驱动程序应当更新结构体，以实际的、可能更宽松的配置。如果无法对请求的包打上时间戳，则不应进行任何更改并返回`ERANGE`（与返回`EINVAL`不同，后者表示`SIOCSHWTSTAMP`根本不支持）。
只有具有管理权限的进程才能更改配置。用户空间负责确保多个进程之间不互相干扰，并且设置已重置。
任何进程都可以通过将此结构体传递给`ioctl(SIOCGHWTSTAMP)`来读取实际配置。然而，并非所有驱动程序都实现了这一点。

```c
/* hwtstamp_config->tx_type 的可能值 */
enum {
    /* 不需要对任何出站包打硬件时间戳；如果收到要求打时间戳的包，将不会进行硬件时间戳 */
    HWTSTAMP_TX_OFF,

    /* 启用出站包的硬件时间戳；发送包的一方通过在发送包之前设置SOF_TIMESTAMPING_TX_SOFTWARE来决定哪些包需要打时间戳 */
    HWTSTAMP_TX_ON,
};

/* hwtstamp_config->rx_filter 的可能值 */
enum {
    /* 不对任何入站包打时间戳 */
    HWTSTAMP_FILTER_NONE,

    /* 对任何入站包打时间戳 */
    HWTSTAMP_FILTER_ALL,

    /* 返回值：对请求的所有包打时间戳，以及其他一些包 */
    HWTSTAMP_FILTER_SOME,

    /* PTP v1，UDP，任何类型的事件包 */
    HWTSTAMP_FILTER_PTP_V1_L4_EVENT,

    /* 有关完整值列表，请检查头文件include/uapi/linux/net_tstamp.h */
};
```

### 3.1 硬件时间戳实现：设备驱动程序
--------------------------------------------------------

支持硬件时间戳的驱动程序必须支持`SIOCSHWTSTAMP` ioctl，并根据`SIOCSHWTSTAMP`部分所述更新提供的`struct hwtstamp_config`中的实际值。它还应支持`SIOCGHWTSTAMP`。
时间戳必须存储在 `skb` 中。要获取 `skb` 的共享时间戳结构的指针，可以调用 `skb_hwtstamps()`。然后设置该结构中的时间戳：

    ```c
    struct skb_shared_hwtstamps {
        /* 硬件时间戳转换为自某一时间点以来的持续时间 */
        ktime_t hwtstamp;
    };
    ```

对于传出的数据包，应按照以下步骤生成时间戳：

- 在 `hard_start_xmit()` 中，检查 `(skb_shinfo(skb)->tx_flags & SKBTX_HW_TSTAMP)` 是否非零。如果非零，则驱动程序需要进行硬件时间戳处理。
- 如果 `skb` 支持并且请求了硬件时间戳，则通过设置 `skb_shinfo(skb)->tx_flags` 中的 `SKBTX_IN_PROGRESS` 标志来声明驱动程序正在执行时间戳处理，例如：
  
    ```c
    skb_shinfo(skb)->tx_flags |= SKBTX_IN_PROGRESS;
    ```

  您可能希望保留与之关联的 `skb` 指针以便下一步操作，并且不要释放 `skb`。不支持硬件时间戳的驱动程序则不会这样做。驱动程序绝不能触碰 `sk_buff::tstamp`！它由网络子系统用于存储软件生成的时间戳。
- 驱动程序应在将 `sk_buff` 传递给硬件之前尽可能接近地调用 `skb_tx_timestamp()`。如果请求了软件时间戳并且无法使用硬件时间戳（未设置 `SKBTX_IN_PROGRESS`），`skb_tx_timestamp()` 将提供一个软件时间戳。
- 一旦驱动程序发送了数据包并/或获得了硬件时间戳，则通过调用 `skb_tstamp_tx()` 并传入原始 `skb` 和原始硬件时间戳来传递时间戳。`skb_tstamp_tx()` 会克隆原始 `skb` 并添加时间戳，因此现在需要释放原始 `skb`。

如果获取硬件时间戳失败，则驱动程序不应回退到软件时间戳。原因是这会在处理管道的较晚阶段发生，从而可能导致时间戳之间出现意外的差异。

### 3.2 堆叠的 PTP 硬件时钟的特殊考虑
------------------------------------------

存在某些情况，在数据包的数据路径中可能存在多个 PHC（PTP 硬件时钟）。内核没有明确机制允许用户选择用于以太网帧时间戳的 PHC。相反，默认假设最外层的 PHC 是最优的选择，并且内核驱动程序协作实现这一目标。目前有三种堆叠的 PHC 情况，详细如下：

#### 3.2.1 DSA（分布式交换架构）交换机
^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^

这些是以太网交换机，其中一个端口连接到一个完全不知情的主机以太网接口，并充当端口倍增器的角色，具有可选的转发加速功能。每个 DSA 交换机端口对用户来说都像是一个独立的（虚拟）网络接口，并且其网络 I/O 实际上是间接通过主机接口完成的（在发送时重定向到主机端口，在接收时拦截帧）。当 DSA 交换机连接到主机端口时，PTP 同步会受到影响，因为交换机的可变队列延迟会在主机端口和其 PTP 合作伙伴之间引入路径延迟抖动。为此，一些 DSA 交换机包含了自己的时间戳时钟，并能够在自己的 MAC 上执行网络时间戳处理，从而使路径延迟仅测量线路和 PHY 传播延迟。支持时间戳处理的 DSA 交换机在 Linux 中受到支持，并且暴露与任何其他网络接口相同的 ABI（除了 DSA 接口实际上在网络 I/O 方面是虚拟的，它们确实有自己的 PHC）。通常但不是必须，所有 DSA 交换机的接口共享同一个 PHC。

设计上，使用 DSA 交换机进行 PTP 时间戳处理不需要在其所连接的主机端口驱动程序中进行特殊处理。然而，当主机端口也支持 PTP 时间戳处理时，DSA 会负责拦截针对主机端口的 `.ndo_eth_ioctl` 调用，并阻止启用硬件时间戳处理。这是因为 SO_TIMESTAMPING API 不允许为同一数据包提供多个硬件时间戳，因此除了 DSA 交换机端口之外的其他任何端口都不得这样做。

在通用层中，DSA 提供了以下用于 PTP 时间戳处理的基础架构：

- `port_txtstamp()`：在从用户空间请求硬件 TX 时间戳处理前调用的一个钩子。
  这对于两步时间戳处理是必需的，因为在实际 MAC 发送后硬件时间戳才会可用，因此驱动程序必须准备将时间戳与原始数据包相关联，以便能够重新将数据包重新排队到套接字的错误队列中。为了保存数据包以待时间戳可用时使用，驱动程序可以调用 `skb_clone_skb`，将克隆指针保存在 `skb->cb` 中，并将 TX `skb` 队列入队。通常，交换机会有一个 PTP TX 时间戳寄存器（有时是一个 FIFO），其中时间戳会变得可用。如果是 FIFO，则硬件可能会存储 PTP 序列 ID/消息类型/域号与实际时间戳的键值对。为了正确关联等待时间戳处理的队列中的数据包与实际时间戳，驱动程序可以使用 BPF 分类器（`ptp_classify_raw`）来识别 PTP 传输类型，并使用 `ptp_parse_header` 来解释 PTP 头字段。可能会有一个在此时间戳可用时触发的 IRQ，或者驱动程序可能需要在向主机接口调用 `dev_queue_xmit()` 后进行轮询。
### 一步发送时间戳
一步发送时间戳不需要复制数据包，因为PTP协议不需要后续消息（由于TX时间戳是由MAC嵌入到数据包中的），因此用户空间不期望带有TX时间戳的数据包重新排队到其套接字的错误队列中。

- ``.port_rxtstamp()``：在接收（RX）时，DSA运行BPF分类器来识别PTP事件消息（其他所有数据包，包括PTP通用消息，都不会被打上时间戳）。原始的（也是唯一的）可打时间戳的`skb`被提供给驱动程序，以便立即打上时间戳（如果时间戳立即可用），或者延迟处理。在接收时，时间戳可能通过DSB头中的元数据或其他方式附加到数据包（即带内），或者通过另一个接收时间戳FIFO（即带外）获得。在接收时延迟处理通常是在获取时间戳需要睡眠上下文的情况下。在这种情况下，DSA驱动程序有责任在新打上时间戳的`skb`上调用`netif_rx()`。
  
### 3.2.2 以太网PHY设备
这些设备通常在网络栈中承担第1层的角色，因此它们不像DSA交换机那样具有网络接口表示。然而，为了性能原因，PHY设备可能能够检测并打上PTP数据包的时间戳：尽可能接近线路上的时间戳有可能带来更稳定和精确的同步。
支持PTP时间戳的PHY驱动程序必须创建一个`struct mii_timestamper`结构，并将其指针添加到`phydev->mii_ts`中。网络栈会检查这个指针的存在性。
由于PHY设备没有网络接口表示，因此其时间戳和ethtool ioctl操作需要由相应的MAC驱动程序代理。因此，与DSA交换机不同，每个单独的MAC驱动程序都需要进行修改以支持PHY时间戳功能。这涉及：

- 在``.ndo_eth_ioctl``中检查`phy_has_hwtstamp(netdev->phydev)`是否为真。如果是，则MAC驱动程序不应处理此请求，而应使用`phy_mii_ioctl()`将其传递给PHY。
- 在接收（RX）时，可能需要特殊干预，具体取决于用于将skb向上传递给网络栈的函数。在使用简单的`netif_rx()`及其类似函数的情况下，MAC驱动程序必须检查是否需要调用`skb_defer_rx_timestamp(skb)`——如果需要，则根本不调用`netif_rx()`。如果启用了`CONFIG_NETWORK_PHY_TIMESTAMPING`配置项，并且存在`skb->dev->phydev->mii_ts`，则其`.rxtstamp()`钩子现在将被调用，以确定是否需要延迟处理RX时间戳。同样地，当时间戳可用时，PHY驱动程序有责任将数据包向上发送到堆栈。
对于其他skb接收函数，如`napi_gro_receive`和`netif_receive_skb`，堆栈会自动检查是否需要调用`skb_defer_rx_timestamp()`，因此驱动程序内部不需要这种检查。
- 在发送（TX）时，同样可能需要特殊干预。调用`mii_ts->txtstamp()`钩子的函数名为`skb_clone_tx_timestamp()`。该函数可以直接调用（在这种情况下确实需要显式的MAC驱动程序支持），但该函数也可以从许多MAC驱动程序已经执行的软件时间戳`skb_tx_timestamp()`调用中继承。因此，如果MAC支持软件时间戳，则在这个阶段无需进一步操作。

### 3.2.3 MII总线窥探设备
这些设备的作用与时间戳以太网PHY相同，只是它们是独立设备，因此即使PHY不支持时间戳也可以与其一起使用。在Linux中，它们可以通过Device Tree发现并与`struct phy_device`关联，并且其余部分使用相同的mii_ts基础设施。更多细节请参阅`Documentation/devicetree/bindings/ptp/timestamper.txt`。

### 3.2.4 其他MAC驱动程序注意事项
堆叠的PHC，特别是DSA（但不仅限于DSA）——由于其不需要对MAC驱动程序进行任何修改，因此确保所有可能代码路径的正确性更加困难——它们揭示了以前无法触发的bug。一个例子与以下代码行有关，之前已介绍过：

```c
skb_shinfo(skb)->tx_flags |= SKBTX_IN_PROGRESS;
```

任何TX时间戳逻辑，无论是简单的MAC驱动程序、DSA交换机驱动程序、PHY驱动程序还是MII总线窥探设备驱动程序，都应设置此标志。
但是一个不了解PHC堆叠的MAC驱动可能会因为其他实体设置了这个标志而出现问题，并传递一个重复的时间戳。例如，一个典型的TX时间戳驱动设计可能分为两部分：

1. **TX**：检查是否通过`ndo_eth_ioctl`（`priv->hwtstamp_tx_enabled == true`）启用了PTP时间戳，并且当前的skb需要TX时间戳（`skb_shinfo(skb)->tx_flags & SKBTX_HW_TSTAMP`）。如果这些条件都满足，它会设置`skb_shinfo(skb)->tx_flags |= SKBTX_IN_PROGRESS`标志。注意：如上所述，在堆叠的PHC系统中，这种情况不应该触发，因为这个MAC肯定不是最外层的PHC。但这并不是典型问题所在。传输继续进行。

2. **TX确认**：传输已经完成。驱动程序检查是否需要收集任何TX时间戳。这里就是典型问题所在：MAC驱动采取了一个捷径，只检查`skb_shinfo(skb)->tx_flags & SKBTX_IN_PROGRESS`是否被设置。在堆叠的PHC系统中，这是不正确的，因为这个MAC驱动不是TX数据路径中唯一可能启用SKBTX_IN_PROGRESS的实体。

解决这个问题的正确方法是在MAC驱动的“TX确认”部分进行复合检查，不仅检查`skb_shinfo(skb)->tx_flags & SKBTX_IN_PROGRESS`，还要检查`priv->hwtstamp_tx_enabled == true`。由于系统的其余部分确保除了最外层的PHC之外，其他地方都不会启用PTP时间戳，因此这种增强的检查将避免向用户空间传递重复的TX时间戳。
