### SPDX 许可证标识符: GPL-2.0

#### 时间戳

##### 1. 控制接口

接收网络数据包的时间戳接口包括：

- **SO_TIMESTAMP**
  - 为每个接收到的数据包生成时间戳（系统时间，不一定单调递增）。通过 `recvmsg()` 的控制消息报告时间戳，分辨率为微秒。
  - `SO_TIMESTAMP` 定义为 `SO_TIMESTAMP_NEW` 或 `SO_TIMESTAMP_OLD`，具体取决于架构类型和 libc 中 `time_t` 的表示方式。
  - 控制消息格式：对于 `SO_TIMESTAMP_OLD` 使用 `struct __kernel_old_timeval`；对于 `SO_TIMESTAMP_NEW` 选项使用 `struct __kernel_sock_timeval`。
- **SO_TIMESTAMPNS**
  - 与 `SO_TIMESTAMP` 相同的时间戳机制，但使用 `struct timespec` 报告时间戳，分辨率为纳秒。
  - `SO_TIMESTAMPNS` 定义为 `SO_TIMESTAMPNS_NEW` 或 `SO_TIMESTAMPNS_OLD`，具体取决于架构类型和 libc 中 `time_t` 的表示方式。
  - 控制消息格式：对于 `SO_TIMESTAMPNS_OLD` 使用 `struct timespec`；对于 `SO_TIMESTAMPNS_NEW` 选项使用 `struct __kernel_timespec`。
- **IP_MULTICAST_LOOP + SO_TIMESTAMP[NS]**
  - 仅适用于多播：通过读取循环数据包的接收时间戳来获取近似发送时间戳。
- **SO_TIMESTAMPING**
  - 在接收、发送或两者都生成时间戳。支持多种时间戳来源，包括硬件。支持为流套接字生成时间戳。

##### 1.1 SO_TIMESTAMP（也包括 SO_TIMESTAMP_OLD 和 SO_TIMESTAMP_NEW）

此套接字选项允许在接收路径上对数据报进行时间戳标记。由于在网络堆栈早期阶段可能还不知道目的套接字（如果有的话），因此需要为所有数据包启用该功能。所有早期接收时间戳选项都是如此。

有关接口详细信息，请参阅 `man 7 socket`。
始终使用 `SO_TIMESTAMP_NEW` 时间戳以始终获取 `struct __kernel_sock_timeval` 格式的时间戳。
`SO_TIMESTAMP_OLD` 在32位机器上2038年之后返回不正确的时间戳。

1.2 `SO_TIMESTAMPNS`（也包括 `SO_TIMESTAMPNS_OLD` 和 `SO_TIMESTAMPNS_NEW`）
-------------------------------------------------------------------

此选项与 `SO_TIMESTAMP` 相同，只是返回的数据类型不同。
其 `struct timespec` 允许比 `SO_TIMESTAMP` 的 `timeval`（毫秒级）更高的时间分辨率（纳秒级）。
始终使用 `SO_TIMESTAMPNS_NEW` 时间戳以始终获取 `struct __kernel_timespec` 格式的时间戳。
`SO_TIMESTAMPNS_OLD` 在32位机器上2038年之后返回不正确的时间戳。

1.3 `SO_TIMESTAMPING`（也包括 `SO_TIMESTAMPING_OLD` 和 `SO_TIMESTAMPING_NEW`）
----------------------------------------------------------------------

支持多种类型的时间戳请求。因此，此套接字选项需要一个标志位图，而不是布尔值。在以下代码中：

```c
err = setsockopt(fd, SOL_SOCKET, SO_TIMESTAMPING, &val, sizeof(val));
```

`val` 是一个整数，可以设置以下任何位。设置其他位将返回 `EINVAL` 并且不会改变当前状态。
该套接字选项配置了针对单个 `sk_buff` 的时间戳生成（1.3.1），向套接字的错误队列报告时间戳（1.3.2）以及选项（1.3.3）。也可以为每个 `sendmsg` 调用通过 `cmsg` 启用时间戳生成（1.3.4）。

1.3.1 时间戳生成
^^^^^^^^^^^^^^^^^^^^^^^^^^

某些位是向内核请求尝试生成时间戳。它们的任意组合都是有效的。对这些位的更改仅适用于新创建的数据包，而不适用于已经在内核中的数据包。因此，可以通过在两个 `setsockopt` 调用之间嵌入一个 `send()` 调用来有选择地请求一部分数据包的时间戳（例如，进行采样），一个用于启用时间戳生成，另一个用于禁用它。
此外，除了特定套接字请求之外，还可以基于其他原因生成时间戳，例如当全局启用了接收时间戳时，如前面所述。
### 时间戳请求
- **SOF_TIMESTAMPING_RX_HARDWARE:**
  请求由网络适配器生成的接收时间戳。
- **SOF_TIMESTAMPING_RX_SOFTWARE:**
  当数据进入内核时请求接收时间戳。这些时间戳在设备驱动程序将数据包传递给内核接收堆栈之后立即生成。
- **SOF_TIMESTAMPING_TX_HARDWARE:**
  请求由网络适配器生成的发送时间戳。此标志既可以通过套接字选项也可以通过控制消息启用。
- **SOF_TIMESTAMPING_TX_SOFTWARE:**
  当数据离开内核时请求发送时间戳。这些时间戳尽可能接近、但总是在将数据包传递给网络接口之前，在设备驱动程序中生成。因此，它们需要驱动支持，并非所有设备都可用。此标志既可以通过套接字选项也可以通过控制消息启用。
- **SOF_TIMESTAMPING_TX_SCHED:**
  在数据包进入调度器之前请求发送时间戳。如果内核发送延迟较长，则通常由排队延迟主导。此时间戳与在`SOF_TIMESTAMPING_TX_SOFTWARE`处获取的时间戳之间的差异可以独立于协议处理暴露这一延迟。如果存在任何协议处理延迟，可以通过从这个时间戳中减去在调用`send()`之前的用户空间时间戳来计算。对于具有虚拟设备的机器，其中传输的数据包会经过多个设备以及多个数据包调度器，每一层都会生成一个时间戳。这允许对排队延迟进行精细测量。此标志既可以通过套接字选项也可以通过控制消息启用。
- **SOF_TIMESTAMPING_TX_ACK:**
  当发送缓冲区中的所有数据被确认时请求发送时间戳。这仅适用于可靠协议。目前仅针对TCP实现了这一点。对于该协议，它可能会过度报告测量值，因为时间戳是在所有直到并包括在`send()`时的缓冲区中的数据被确认时生成的：累积确认。该机制忽略了SACK和FACK。此标志既可以通过套接字选项也可以通过控制消息启用。

### 时间戳报告
#### 1.3.2 时间戳报告

另外三个位用于控制在生成的控制消息中报告哪些时间戳。对这些位的更改会立即在堆栈中的时间戳报告位置生效。只有设置了相关时间戳生成请求的数据包才会报告时间戳。

- **SOF_TIMESTAMPING_SOFTWARE:**
  如果可用，报告任何软件时间戳。
### 过时选项：SOF_TIMESTAMPING_SYS_HARDWARE:
该选项已被废弃且被忽略。

### SOF_TIMESTAMPING_RAW_HARDWARE:
当可用时，报告由 `SOF_TIMESTAMPING_TX_HARDWARE` 生成的硬件时间戳。

#### 1.3.3 时间戳选项
^^^^^^^^^^^^^^^^^^^^^^^

接口支持以下选项：

### SOF_TIMESTAMPING_OPT_ID:
为每个数据包生成一个唯一标识符。一个进程可能同时有多个时间戳请求。在传输路径中，数据包可能会被重新排序，例如在网络调度器中。在这种情况下，时间戳会按照与原始 `send()` 调用不同的顺序被放入错误队列。仅凭时间戳顺序或有效负载检查，有时无法唯一地将时间戳与原始 `send()` 调用匹配起来。此选项在 `send()` 时为每个数据包关联一个唯一标识符，并随同时间戳一起返回。该标识符来源于每个套接字的 u32 计数器（会溢出）。对于数据报套接字，计数器随着每次发送的数据包递增；对于流式套接字，计数器随着每个字节递增。对于流式套接字，还需设置 `SOF_TIMESTAMPING_OPT_ID_TCP`，请参阅下面的章节。
计数器从零开始。首次启用套接字选项时初始化计数器。每当选项被禁用后重新启用时，计数器都会重置。重置计数器不会改变系统中现有数据包的标识符。

此选项仅针对传输时间戳实现。在那里，时间戳总是与 `struct sock_extended_err` 结构体一起循环。
该选项修改字段 `ee_data` 来传递一个唯一标识符，该标识符在该套接字所有可能并发的时间戳请求中都是唯一的。

### SOF_TIMESTAMPING_OPT_ID_TCP:
与 `SOF_TIMESTAMPING_OPT_ID` 一同传递此修饰符用于新的TCP时间戳应用。`SOF_TIMESTAMPING_OPT_ID` 定义了流式套接字中计数器的递增方式，但其起始点并非完全直观。此选项修复了这一点。
对于流式套接字，如果设置了 `SOF_TIMESTAMPING_OPT_ID`，也应始终设置此选项。对于数据报套接字，此选项没有效果。
一个合理的期望是，计数器会在系统调用时重置为零，因此随后写入的 N 字节会产生计数器值为 N-1 的时间戳。`SOF_TIMESTAMPING_OPT_ID_TCP` 在所有条件下实现了这种行为。
SOF_TIMESTAMPING_OPT_ID 通常报告相同的结果，特别是在设置套接字选项时没有数据正在传输的情况下。如果有数据正在传输，则可能会因为输出队列（SIOCOUTQ）的长度而有所偏差。
这种差异是因为基于 `snd_una` 与 `write_seq` 的不同：
`snd_una` 是由对等方确认的流中的偏移量。这取决于进程控制之外的因素，例如网络往返时间（RTT）。
`write_seq` 是进程最后写入的一个字节。这个偏移量不会受到外部输入的影响。
当在创建初始套接字时配置该选项，并且没有数据排队或发送时，这种差异很微妙，不太可能被注意到。但无论何时设置套接字选项，SOF_TIMESTAMPING_OPT_ID_TCP 的行为都更加稳健。

SOF_TIMESTAMPING_OPT_CMSG：
支持为所有带有时间戳的包使用 recv() 控制消息。控制消息已经在所有带有接收时间戳的包和所有带有发送时间戳的 IPv6 包中无条件地得到支持。此选项将它们扩展到了带有发送时间戳的 IPv4 包。一个使用场景是通过同时启用套接字选项 IP_PKTINFO 来关联包与其出口设备。

SOF_TIMESTAMPING_OPT_TSONLY：
仅适用于发送时间戳。使内核以控制消息的形式返回时间戳，伴随一个空包，而不是伴随原始包。这减少了计入套接字接收预算（SO_RCVBUF）的内存数量，并确保即使 sysctl net.core.tstamp_allow_data 设置为 0 也能传递时间戳。
此选项禁用 SOF_TIMESTAMPING_OPT_CMSG。

SOF_TIMESTAMPING_OPT_STATS：
可选统计信息，这些信息与发送时间戳一起获取。
它必须与 SOF_TIMESTAMPING_OPT_TSONLY 一起使用。当发送时间戳可用时，统计信息会以类型为 SCM_TIMESTAMPING_OPT_STATS 的单独控制消息的形式提供，作为一个包含各种类型的 TLV（struct nlattr）的列表。这些统计信息允许应用程序将各种传输层统计信息与发送时间戳相关联，例如某块数据因对等方接收窗口限制的时间长度。
### SOF_TIMESTAMPING_OPT_PKTINFO:
为带有硬件时间戳的传入数据包启用SCM_TIMESTAMPING_PKTINFO控制消息。该消息包含结构scm_ts_pktinfo，提供了接收该数据包的实际接口的索引及其在第二层的长度。只有当CONFIG_NET_RX_BUSY_POLL被启用且驱动程序使用NAPI时，才会返回有效的（非零）接口索引。该结构还包含另外两个字段，但它们是预留且未定义的。

### SOF_TIMESTAMPING_OPT_TX_SWHW:
当同时启用了SOF_TIMESTAMPING_TX_HARDWARE和SOF_TIMESTAMPING_TX_SOFTWARE时，请求对传出的数据包进行硬件和软件时间戳处理。如果生成了两个时间戳，则会将两条单独的消息循环到套接字的错误队列中，每条消息仅包含一个时间戳。

新应用程序被鼓励传递SOF_TIMESTAMPING_OPT_ID以区分时间戳，并传递SOF_TIMESTAMPING_OPT_TSONLY以忽略sysctl net.core.tstamp_allow_data设置的影响。
特殊情况是当进程需要额外的cmsg数据时，例如SOL_IP/IP_PKTINFO来检测出口网络接口。此时应传递选项SOF_TIMESTAMPING_OPT_CMSG。此选项依赖于访问原始数据包的内容，因此不能与SOF_TIMESTAMPING_OPT_TSONLY结合使用。

### 1.3.4. 通过控制消息启用时间戳
除了套接字选项外，还可以通过cmsg按写操作请求时间戳生成，仅适用于SOF_TIMESTAMPING_TX_*（参见第1.3.1节）。利用此功能，应用程序可以在每个sendmsg()调用中采样时间戳，而无需承担通过setsockopt启用和禁用时间戳的开销：

```c
struct msghdr *msg;
// ...
cmsg = CMSG_FIRSTHDR(msg);
cmsg->cmsg_level = SOL_SOCKET;
cmsg->cmsg_type = SO_TIMESTAMPING;
cmsg->cmsg_len = CMSG_LEN(sizeof(__u32));
*((__u32 *) CMSG_DATA(cmsg)) = SOF_TIMESTAMPING_TX_SCHED | SOF_TIMESTAMPING_TX_SOFTWARE | SOF_TIMESTAMPING_TX_ACK;
err = sendmsg(fd, msg, 0);
```

通过cmsg设置的SOF_TIMESTAMPING_TX_*标志会覆盖通过setsockopt设置的SOF_TIMESTAMPING_TX_*标志。
此外，应用程序仍需通过setsockopt启用时间戳报告以接收时间戳：
```c
__u32 val = SOF_TIMESTAMPING_SOFTWARE | SOF_TIMESTAMPING_OPT_ID; // 或其他任何标志
err = setsockopt(fd, SOL_SOCKET, SO_TIMESTAMPING, &val, sizeof(val));
```

### 1.4 字节流时间戳
SO_TIMESTAMPING接口支持字节流中的时间戳。每个请求被视为请求整个缓冲区内容经过某个时间戳点的时间。也就是说，对于流式选项SOF_TIMESTAMPING_TX_SOFTWARE，无论数据已转换成多少个数据包，都会记录所有字节到达设备驱动程序的时间。
一般来说，字节流没有自然的分隔符，因此将时间戳与数据相关联并不简单。一组字节可能跨多个段分割，任何段都可能合并（可能合并之前独立send()调用所关联的分段缓冲区的部分）。段可以重新排序，相同的一组字节可能存在于多个段中，对于实现重传的协议尤其如此。
### 关键时间戳实现的一致性至关重要

无论可能发生的转换如何，所有的时间戳都必须实现相同的意义，否则它们将无法比较。仅仅以不同方式处理“罕见”的极端情况（与简单的1:1映射从缓冲区到skb的情况相比）是不够的，因为性能调试通常需要关注这些异常值。实际上，如果正确选择了时间戳的意义和测量时间点，那么时间戳可以与字节流段保持一致的相关性。这一挑战与决定IP分片策略并无二致。在那里，定义仅对第一个分片进行时间戳标记。对于字节流，我们选择仅在所有字节通过某一点时生成时间戳。SOF_TIMESTAMPING_TX_ACK的定义易于实现且易于理解。而如果需要考虑SACK，则实现会更复杂，因为可能存在传输空洞和乱序到达。

在主机上，TCP也可能由于Nagle算法、软木塞（cork）、自动软木塞（autocork）、分段和GSO等因素打破简单的1:1映射关系从缓冲区到skb。实现确保在所有情况下保持正确性，通过跟踪传递给send()的每个最后一个字节，即使在skb扩展或合并操作后它不再是最后一个字节。它将相关的序列号存储在skb_shinfo(skb)->tskey中。由于skb只有一个这样的字段，因此只能生成一个时间戳。

在极少数情况下，如果两个时间戳请求被压缩到同一个skb上，可能会错过一个时间戳请求。进程可以通过启用SOF_TIMESTAMPING_OPT_ID并比较发送时的字节偏移与每个时间戳返回的值来检测这种情况。可以通过始终在请求之间刷新TCP堆栈来避免这种情况，例如通过启用TCP_NODELAY并禁用TCP_CORK和自动软木塞。自Linux 4.7之后，更好的防止压缩的方法是在sendmsg()时使用MSG_EOR标志。

这些预防措施确保了只有当所有字节经过时间戳点时才生成时间戳，假设网络堆栈本身不会重新排序这些段。堆栈确实试图避免重新排序。唯一例外受管理员控制：可以通过构建不同的包调度器配置来延迟来自同一流的不同段。这种设置是不常见的。

### 2 数据接口

#### 2.1 SCM_TIMESTAMPING记录

这些时间戳通过recvmsg()的辅助数据功能读取。参阅`man 3 cmsg`了解此接口的详细信息。socket手册页(`man 7 socket`)描述了如何检索使用SO_TIMESTAMP和SO_TIMESTAMPNS生成的时间戳记录。

对于SO_TIMESTAMPING_OLD:

```c
struct scm_timestamping {
    struct timespec ts[3];
};
```

对于SO_TIMESTAMPING_NEW:

```c
struct scm_timestamping64 {
    struct __kernel_timespec ts[3];
};
```

始终使用SO_TIMESTAMPING_NEW时间戳以始终获取struct scm_timestamping64格式的时间戳。
SO_TIMESTAMPING_OLD在32位机器上的2038年后返回错误的时间戳。

结构体最多可返回三个时间戳。这是一个遗留特性。任何时候至少有一个字段非零。大多数时间戳传递在ts[0]中。硬件时间戳传递在ts[2]中。
### 翻译

`ts[1]`过去用于保存转换为系统时间的硬件时间戳。
相反，直接将NIC上的硬件时钟设备暴露为HW PTP时钟源，以允许在用户空间中进行时间转换，并可选地使用如`linuxptp`之类的用户空间PTP堆栈与系统时间同步。对于PTP时钟API，请参阅`Documentation/driver-api/ptp.rst`。
需要注意的是，如果同时启用了`SO_TIMESTAMP`或`SO_TIMESTAMPNS`选项以及使用`SOF_TIMESTAMPING_SOFTWARE`的`SO_TIMESTAMPING`，则在缺少实际软件时间戳的情况下，`recvmsg()`调用中会在`ts[0]`生成一个错误的软件时间戳。这种情况也会发生在硬件发送时间戳上。

#### 2.1.1 使用`MSG_ERRQUEUE`的发送时间戳
^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^

对于发送时间戳，出站数据包被循环回送至套接字的错误队列，并附带发送的时间戳。进程通过设置`MSG_ERRQUEUE`标志并提供足够大的`msg_control`缓冲区来接收相关元数据结构的方式，调用`recvmsg()`来接收时间戳。`recvmsg`调用返回带有两个附加辅助消息的原始出站数据包：
- 一个具有`SOL_IP(V6)`级别和`IP(V6)_RECVERR`类型的辅助消息嵌入了一个`struct sock_extended_err`。这定义了错误类型。对于时间戳，`ee_errno`字段为`ENOMSG`。
- 另一个辅助消息具有`SOL_SOCKET`级别和`SCM_TIMESTAMPING`类型。这个辅助消息嵌入了`struct scm_timestamping`。

#### 2.1.1.2 时间戳类型
~~~~~~~~~~~~~~~~~~~~~~~

三个`struct timespec`的语义由扩展错误结构中的`ee_info`字段定义。它包含一个`SCM_TSTAMP_*`类型的值来定义`scm_timestamping`中传递的实际时间戳。
`SCM_TSTAMP_*`类型与前面讨论的`SOF_TIMESTAMPING_*`控制字段是1:1匹配的，除了一个例外。由于历史原因，`SCM_TSTAMP_SND`等于零，并且可以为`SOF_TIMESTAMPING_TX_HARDWARE`和`SOF_TIMESTAMPING_TX_SOFTWARE`两者设置。如果`ts[2]`非零，则它是前者；否则为后者，在这种情况下时间戳存储在`ts[0]`中。

#### 2.1.1.3 分片
~~~~~~~~~~~~~~~~~~~~~

出站数据报分片很少发生，但有可能出现，例如，通过明确禁用PMTU发现。如果一个出站数据包被分片，则只有第一个分片被时间戳并返回到发送套接字。

#### 2.1.1.4 数据包负载
~~~~~~~~~~~~~~~~~~~~~~

调用应用程序通常不关心接收其最初传递给内核的数据包的全部负载：套接字错误队列机制只是用来附带时间戳的方法。
在这种情况下，应用程序可以选择使用较小的缓冲区（甚至长度为0）读取数据报。相应地截断负载。然而，直到进程在错误队列上调用`recvmsg()`之前，整个数据包都会被排队，占用`SO_RCVBUF`的预算。
### 2.1.1.5 阻塞读取
~~~~~~~~~~~~~~~~~~~~~

从错误队列中读取数据始终是非阻塞操作。为了等待时间戳，可以使用`poll`或`select`。如果错误队列中有任何数据准备好，`poll()`将在`pollfd.revents`中返回`POLLERR`。在`pollfd.events`中不需要传递这个标志。请求时此标志将被忽略。更多信息请参阅`man 2 poll`。
#### 2.1.2 接收时间戳
^^^^^^^^^^^^^^^^^^^^^^^^

在接收过程中，没有理由从套接字错误队列读取数据。`SCM_TIMESTAMPING`辅助数据会与数据包一起通过正常的`recvmsg()`发送。因为这不是一个套接字错误，所以它不会伴随着一个`SOL_IP(V6)/IP(V6)_RECVERROR`消息。在这种情况下，`struct scm_timestamping`中的三个字段的含义是隐含定义的：`ts[0]`如果设置了则持有软件时间戳；`ts[1]`再次被废弃；`ts[2]`如果设置了则持有硬件时间戳。

### 3. 硬件时间戳配置：SIOCSHWTSTAMP 和 SIOCGHWTSTAMP
=======================================================

对于预期进行硬件时间戳的每个设备驱动程序，必须初始化硬件时间戳。参数在`include/uapi/linux/net_tstamp.h`中定义为：

```c
struct hwtstamp_config {
    int flags;        // 目前没有任何标志定义，必须为零
    int tx_type;      // HWTSTAMP_TX_*
    int rx_filter;    // HWTSTAMP_FILTER_*
};
```

通过调用`ioctl(SIOCSHWTSTAMP)`并传递指向`struct ifreq`的指针（其`ifr_data`指向`struct hwtstamp_config`）来将所需行为传递给内核和特定设备。`tx_type`和`rx_filter`是对驱动程序期望执行的任务的提示。如果请求的对传入数据包的细粒度过滤不被支持，则驱动程序可能对超出请求类型的其他类型的数据包进行时间戳。
驱动程序可以使用比请求配置更为宽松的配置。期望驱动程序只直接实现能够支持的最通用模式。例如，如果硬件可以支持`HWTSTAMP_FILTER_PTP_V2_EVENT`，那么它通常应该总是上行扩展`HWTSTAMP_FILTER_PTP_V2_L2_SYNC`等，因为`HWTSTAMP_FILTER_PTP_V2_EVENT`更通用（且对应用程序更有用）。
支持硬件时间戳的驱动程序应更新该结构以反映实际的、可能更宽松的配置。如果无法对请求的数据包进行时间戳，则不应更改任何内容，并应返回`ERANGE`（与返回`EINVAL`不同，后者表示根本不支持`SIOCSHWTSTAMP`）。
只有具有管理员权限的进程才能更改配置。用户空间负责确保多个进程之间不会相互干扰并且设置会被重置。
任何进程都可以通过以相同方式将此结构传递给`ioctl(SIOCGHWTSTAMP)`来读取实际配置。然而，并非所有驱动程序都实现了这一点。

```c
/* struct hwtstamp_config->tx_type 的可能值 */
enum {
    /* 不对任何发出的数据包进行硬件时间戳；如果到达的数据包请求时间戳，则不会进行硬件时间戳 */
    HWTSTAMP_TX_OFF,

    /* 对发出的数据包启用硬件时间戳；发送数据包的一方决定哪些数据包需要通过设置SOF_TIMESTAMPING_TX_SOFTWARE进行时间戳，然后发送数据包 */
    HWTSTAMP_TX_ON,
};

/* struct hwtstamp_config->rx_filter 的可能值 */
enum {
    /* 不对任何传入的数据包进行时间戳 */
    HWTSTAMP_FILTER_NONE,

    /* 对任何传入的数据包进行时间戳 */
    HWTSTAMP_FILTER_ALL,

    /* 返回值：对所有请求的数据包以及其他一些数据包进行时间戳 */
    HWTSTAMP_FILTER_SOME,

    /* PTP v1，UDP，任何类型的事件数据包 */
    HWTSTAMP_FILTER_PTP_V1_L4_EVENT,

    /* 完整的值列表，请检查头文件 include/uapi/linux/net_tstamp.h */
};
```

### 3.1 硬件时间戳实现：设备驱动程序
--------------------------------------------------------

支持硬件时间戳的驱动程序必须支持`SIOCSHWTSTAMP ioctl`并根据`SIOCSHWTSTAMP`部分所述更新提供的`struct hwtstamp_config`的实际值。它还应支持`SIOCGHWTSTAMP`。
接收的数据包的时间戳必须存储在`skb`中。要获取`skb`共享时间戳结构的指针，请调用`skb_hwtstamps()`。然后在该结构中设置时间戳：

    struct skb_shared_hwtstamps {
	    /* 硬件时间戳转换为自某个任意时间点以来的持续时间 */
	    ktime_t hwtstamp;
    };

对于发送的数据包，时间戳应按以下方式生成：

- 在`hard_start_xmit()`函数中，检查`(skb_shinfo(skb)->tx_flags & SKBTX_HW_TSTAMP)`是否非零。如果是，则驱动程序应该执行硬件时间戳操作。
- 如果对`skb`可能且被请求进行时间戳操作，则通过设置`skb_shinfo(skb)->tx_flags`中的`SKBTX_IN_PROGRESS`标志来声明驱动程序正在执行时间戳操作，例如： 

      skb_shinfo(skb)->tx_flags |= SKBTX_IN_PROGRESS;

  您可能希望保留与之关联的`skb`的指针以供下一步使用，并不释放`skb`。不支持硬件时间戳的驱动程序不会这样做。驱动程序绝不能触碰`sk_buff::tstamp`！它由网络子系统用于存储软件生成的时间戳。
- 驱动程序应在尽可能接近将`sk_buff`传递给硬件时调用`skb_tx_timestamp()`。如果请求了软件时间戳并且无法实现硬件时间戳(`SKBTX_IN_PROGRESS`未设置)，`skb_tx_timestamp()`会提供一个软件时间戳。
- 只要驱动程序发送了数据包并/或为其获得了硬件时间戳，它就通过调用`skb_tstamp_tx()`并将原始`skb`和原始硬件时间戳传递回去。`skb_tstamp_tx()`克隆原始`skb`并添加时间戳，因此现在需要释放原始`skb`。
如果以某种方式获取硬件时间戳失败，则驱动程序不应回退到软件时间戳。原因是这会在处理管线的较晚阶段发生，从而可能导致时间戳之间的意外差异。

### 3.2 对于堆叠式PTP硬件时钟的特殊考虑
----------------------------------------------------------

存在一些情况下，在数据包的数据路径中可能存在多个PHC（PTP硬件时钟）。内核没有明确机制允许用户选择用于以太网帧时间戳的PHC。相反，假设最外层的PHC始终是最优选的，并且内核驱动程序协作以达成这一目标。目前有三种堆叠PHC的情况，具体如下：

#### 3.2.1 DSA（分布式交换架构）交换机
^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^

这些是以太网交换机，其中一个端口连接到（否则完全不知情的）主机以太网接口，并扮演端口倍增器的角色，具有可选的转发加速功能。每个DSA交换机端口对用户来说都是一个独立的（虚拟）网络接口，并且其网络I/O实际上间接通过主机接口完成（在TX时重定向到主机端口，在RX时拦截帧）
当DSA交换机连接到主机端口时，PTP同步会受到影响，因为交换机的可变排队延迟在主机端口与其PTP伙伴之间引入了路径延迟抖动。为此，某些DSA交换机包括了自己的时间戳时钟，并且有能力在其MAC上执行网络时间戳，使得路径延迟仅测量线路和PHY传播延迟。支持时间戳的DSA交换机在Linux中得到支持，并且暴露与其他任何网络接口相同的ABI（除了DSA接口在网络I/O方面实际上是虚拟的，它们确实有自己的PHC）。通常但不是强制性的，DSA交换机的所有接口共享同一个PHC。
设计上，使用DSA交换机进行PTP时间戳不需要在它所连接的主机端口的驱动程序中做任何特殊处理。然而，当主机端口也支持PTP时间戳时，DSA将负责拦截指向主机端口的`ndo_eth_ioctl`调用，并阻止尝试在其上启用硬件时间戳。这是因为SO_TIMESTAMPING API不允许为同一数据包交付多个硬件时间戳，所以除了DSA交换机端口之外的任何人不得这样做。
在通用层中，DSA为PTP时间戳提供了以下基础设施：

- `port_txtstamp()`：一个钩子，在从用户空间请求硬件TX时间戳之前调用
这对于两步时间戳是必需的，因为硬件时间戳在实际MAC传输之后才可用，因此驱动程序必须准备好将时间戳与原始数据包相关联，以便它可以重新将数据包队列化回到套接字的错误队列中。为了保存时间戳可用时的数据包，驱动程序可以调用`skb_clone_sk`，在`skb->cb`中保存克隆指针，并将TX `skb`队列入队。通常，交换机有一个PTP TX时间戳寄存器（有时是一个FIFO），其中时间戳变得可用。在FIFO的情况下，硬件可能会存储PTP序列ID/消息类型/域编号和实际时间戳的关键值对。为了正确地在等待时间戳的数据包队列和实际时间戳之间建立关联，驱动程序可以使用BPF分类器（`ptp_classify_raw`）来识别PTP传输类型，并使用`ptp_parse_header`来解释PTP头字段。可能有一个在该时间戳可用时触发的IRQ，或者驱动程序可能需要在向主机接口调用`dev_queue_xmit()`之后轮询。
一阶段的TX时间戳不需要数据包克隆，因为PTP协议不需要后续消息（因为TX时间戳是由MAC嵌入到数据包中的），因此用户空间不期望带有TX时间戳的数据包重新排队到其套接字的错误队列中。

- ``.port_rxtstamp()``：在接收（RX）时，DSA运行BPF分类器来识别PTP事件消息（任何其他数据包，包括PTP通用消息，都不进行时间戳）。原始的（也是唯一的）可时间戳的skb被提供给驱动程序，以便立即添加时间戳（如果可用）或推迟处理。在接收时，时间戳可能通过带内方式获得（通过DSA头元数据或其他方式附加到数据包），或者通过非带内方式（通过另一个RX时间戳FIFO）。在RX时的延迟通常是必要的，当检索时间戳需要睡眠上下文时。在这种情况下，DSA驱动程序负责在新打上时间戳的skb上调用``netif_rx()``。
3.2.2 以太网PHY设备
^^^^^^^^^^^^^^^^^^^

这些设备通常在网络堆栈中扮演第1层的角色，因此它们不像DSA交换机那样具有网络接口表示。然而，PHY设备可能能够检测并为PTP数据包打上时间戳，出于性能原因：尽可能靠近线路获取的时间戳有可能带来更稳定和精确的同步。
支持PTP时间戳的PHY驱动程序必须创建一个``struct mii_timestamper``结构，并将指向它的指针添加到``phydev->mii_ts``中。网络堆栈会检查这个指针的存在。
由于PHY没有网络接口表示，因此它们的时间戳和ethtool ioctl操作需要由各自的MAC驱动程序进行中介。因此，与DSA交换机不同，每个单独的MAC驱动程序都需要进行修改以支持PHY时间戳功能。这包括：

- 在``.ndo_eth_ioctl``中检查``phy_has_hwtstamp(netdev->phydev)``是否为真。如果是，则MAC驱动程序不应处理此请求，而应使用``phy_mii_ioctl()``将其传递给PHY。
- 在RX时，可能需要特殊干预，也可能不需要，这取决于用于向上递送skb的网络堆栈的功能。在使用纯``netif_rx()``及其类似功能的情况下，MAC驱动程序必须检查是否需要调用``skb_defer_rx_timestamp(skb)`` —— 如果需要，则完全不要调用``netif_rx()``。如果启用了``CONFIG_NETWORK_PHY_TIMESTAMPING``，并且存在``skb->dev->phydev->mii_ts``，则其``.rxtstamp()``钩子现在将被调用，以确定是否需要延迟RX时间戳，逻辑与DSA非常相似。再次像DSA一样，当时间戳可用时，PHY驱动程序负责将数据包发送到堆栈。
对于其他skb接收函数，如``napi_gro_receive``和``netif_receive_skb``，堆栈自动检查是否需要调用``skb_defer_rx_timestamp()``，因此驱动程序内部不需要这种检查。
- 在TX时，同样可能需要特殊干预，也可能不需要。调用``mii_ts->txtstamp()``钩子的函数名为``skb_clone_tx_timestamp()``。这个函数可以直接调用（在这种情况下确实需要显式的MAC驱动程序支持），但该函数也依赖于许多MAC驱动程序已经执行的用于软件时间戳目的的``skb_tx_timestamp()``调用。因此，如果一个MAC支持软件时间戳，那么在这个阶段就不需要做进一步的工作。
3.2.3 MII总线监听设备
^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^

这些设备执行与时间戳以太网PHY相同的作用，只是它们是独立设备，因此可以与任何不支持时间戳的PHY一起使用。在Linux中，它们可以通过设备树发现并与``struct phy_device``关联，其余部分它们使用相同的mii_ts基础设施。更多细节请参阅Documentation/devicetree/bindings/ptp/timestamper.txt。
3.2.4 对于MAC驱动程序的其他注意事项
^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^

堆叠的PHC，特别是DSA（但不仅限于此）——因为它不需要对MAC驱动程序进行任何修改，所以更难以确保所有可能代码路径的正确性——暴露出之前不存在堆叠PTP时钟时无法触发的bug。一个例子与前面提到过的这段代码有关：

      skb_shinfo(skb)->tx_flags |= SKBTX_IN_PROGRESS;

任何TX时间戳逻辑，无论是简单的MAC驱动程序、DSA交换机驱动程序、PHY驱动程序还是MII总线监听设备驱动程序，都应该设置这个标志。
但一个未意识到PHC堆叠的MAC驱动可能会因为除了自身之外的其他实体设置了这个标志而出现问题，并传递一个重复的时间戳。
例如，对于发送时间戳功能的典型驱动设计可能是将其分为两个部分：

1. "TX"：检查是否之前已经通过``.ndo_eth_ioctl``（即"``priv->hwtstamp_tx_enabled == true``"）启用了PTP时间戳，并且当前的skb需要一个TX时间戳（"``skb_shinfo(skb)->tx_flags & SKBTX_HW_TSTAMP``"）。如果这是真的，它会设置"``skb_shinfo(skb)->tx_flags |= SKBTX_IN_PROGRESS``"标志。注意：如上所述，在堆叠的PHC系统中，这种情况不应该触发，因为这个MAC肯定不是最外层的PHC。但这并不是典型问题所在的地方。然后继续传输这个数据包。
2. "TX确认"：传输已经完成。驱动检查是否需要为该数据包收集任何TX时间戳。这里就是典型的出问题的地方：MAC驱动采取了一个捷径，仅检查"``skb_shinfo(skb)->tx_flags & SKBTX_IN_PROGRESS``"是否被设置。在堆叠的PHC系统中，这是不正确的，因为这个MAC驱动不是TX数据路径中唯一可能最初启用SKBTX_IN_PROGRESS的实体。

解决这个问题的正确方法是让MAC驱动在其"TX确认"部分进行复合检查，不仅检查"``skb_shinfo(skb)->tx_flags & SKBTX_IN_PROGRESS``"，还要检查"``priv->hwtstamp_tx_enabled == true``"。因为系统的其余部分确保除了最外层的PHC之外，PTP时间戳不会为其他任何东西启用，因此这种增强的检查将避免向用户空间提供重复的TX时间戳。
