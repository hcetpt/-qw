### SPDX 许可证标识符：GPL-2.0
### _VAS-API：

==============================================
Virtual Accelerator Switchboard (VAS) 用户空间 API
==============================================

#### 引言

Power9 处理器引入了 Virtual Accelerator Switchboard (VAS)，它允许用户空间和内核与协处理器（硬件加速器）进行通信，该协处理器被称为 Nest Accelerator (NX)。NX 单元包含一个或多个硬件引擎或协处理器类型，例如 842 压缩、GZIP 压缩和加密。在 Power9 上，用户空间应用程序只能访问 GZIP 压缩引擎，该引擎支持硬件中的 ZLIB 和 GZIP 压缩算法。

为了与 NX 进行通信，内核需要建立一个通道或窗口，然后可以无需内核参与直接提交请求。对 GZIP 引擎的请求必须格式化为协处理器请求块 (CRB)，这些 CRB 必须使用 COPY/PASTE 指令将 CRB 粘贴到与引擎请求队列相关的硬件地址。GZIP 引擎提供了两种优先级的请求：普通和高。目前仅支持来自用户空间的普通请求。

本文档解释了用于与内核交互以设置通道/窗口的用户空间 API，该通道/窗口可用于直接向 NX 加速器发送压缩请求。

#### 概览

应用程序通过 `/dev/crypto/nx-gzip` 设备节点访问 GZIP 引擎，该设备节点由 VAS/NX 设备驱动程序实现。应用程序必须打开 `/dev/crypto/nx-gzip` 设备以获取文件描述符 (fd)。然后应使用此 fd 发出 `VAS_TX_WIN_OPEN` ioctl 来建立与引擎的连接。这意味着为该进程在 GZIP 引擎上打开了发送窗口。一旦建立了连接，应用程序应该使用 `mmap()` 系统调用来将引擎请求队列的硬件地址映射到应用程序的虚拟地址空间中。

然后，应用程序可以通过使用 copy/paste 指令并将 CRB 粘贴到 `mmap()` 返回的虚拟地址（即 paste_address）来向引擎提交一个或多个请求。用户空间可以通过关闭文件描述符（`close(fd)`）或在进程退出时关闭已建立的连接或发送窗口。

请注意，应用程序可以使用同一个窗口发送多个请求，也可以建立多个窗口，但每个文件描述符对应一个窗口。以下各节提供了关于各个步骤的更多详细信息和参考资料。
NX-GZIP 设备节点
===================

系统中有一个 `/dev/crypto/nx-gzip` 节点，并且它提供了对系统内所有 GZIP 引擎的访问。在 `/dev/crypto/nx-gzip` 上仅有的有效操作是：

    * 以读写方式打开设备
* 发送 `VAS_TX_WIN_OPEN` ioctl
    * 将引擎的请求队列映射到应用程序的虚拟地址空间（即为协处理器引擎获取一个 paste_address）
* 关闭设备节点
对于此设备节点的其他文件操作是未定义的。
请注意，复制和粘贴操作直接发送到硬件，并不通过此设备。有关更多详细信息，请参阅 COPY/PASTE 文档。
虽然一个系统可能有多个 NX 协处理器引擎实例（通常，每个 P9 芯片一个），但系统中只有一个 `/dev/crypto/nx-gzip` 设备节点。当打开 nx-gzip 设备节点时，内核会在合适的 NX 加速器实例上打开发送窗口。它会找到执行用户进程的 CPU 并确定该 CPU 所属芯片对应的 NX 实例。

应用程序可以使用下面详细介绍的 `VAS_TX_WIN_OPEN` ioctl 中的 `vas_id` 字段来选择特定的 NX 协处理器实例。

一个用户空间库 `libnxz` 可在此处获得，但仍处于开发阶段：

     https://github.com/abalib/power-gzip

使用 inflate / deflate 调用的应用程序可以链接 `libnxz` 而不是 `libz`，并在无需任何修改的情况下使用 NX GZIP 压缩功能。

打开 `/dev/crypto/nx-gzip`
========================

应该以读写方式打开 nx-gzip 设备。打开设备不需要特殊权限。每个窗口对应一个文件描述符。因此，如果用户空间进程需要多个窗口，则需要发出多次打开调用。

请参阅 `open(2)` 系统调用的手册页以了解返回值、错误代码和其他限制等详细信息。
### VAS_TX_WIN_OPEN ioctl 的使用
应用程序应按照以下方式使用 VAS_TX_WIN_OPEN ioctl 来与 NX 协处理器引擎建立连接：

```plaintext
    struct vas_tx_win_open_attr {
        __u32   version;      // 版本号
        __s16   vas_id;       // 具体的 VAS 实例，或 -1 表示默认选择
        __u16   reserved1;    // 保留字段
        __u64   flags;        // 供未来使用的字段
        __u64   reserved2[6]; // 保留字段
    };

版本：
    版本字段当前必须设置为 1。

vas_id：
    如果传入 `-1`，内核将尽力为进程分配最优的 NX 实例。要选择特定的 VAS 实例，请参见“发现可用的 VAS 引擎”部分。
flags、reserved1 和 reserved2[6] 字段是为未来的扩展预留的，目前必须设为 0。

VAS_TX_WIN_OPEN ioctl 的属性 attr 定义如下：

```c
    #define VAS_MAGIC 'v'
    #define VAS_TX_WIN_OPEN _IOW(VAS_MAGIC, 1, struct vas_tx_win_open_attr)

    struct vas_tx_win_open_attr attr;
    rc = ioctl(fd, VAS_TX_WIN_OPEN, &attr);
```

成功时，VAS_TX_WIN_OPEN ioctl 返回 0。出现错误时返回 -1 并设置 errno 变量来指示错误。

错误条件：

| 错误码 | 描述 |
|--------|------|
| EINVAL | fd 没有指向一个有效的 VAS 设备 |
| EINVAL | 无效的 vas ID |
| EINVAL | version 没有设置正确的值 |
| EEXIST | 给定 fd 的窗口已经打开 |
| ENOMEM | 分配窗口时内存不足 |
| ENOSPC | 系统上已打开的窗口（连接）太多 |
| EINVAL | 保留字段没有设为 0 |

更多细节、错误代码和限制请参考 ioctl(2) 手册页。

### NX-GZIP 设备的 mmap()
NX-GZIP 设备 fd 的 mmap() 系统调用返回一个 paste_address，应用程序可以利用该地址将其 CRB 复制到硬件引擎中：

```plaintext
    paste_addr = mmap(addr, size, prot, flags, fd, offset);
```

对于 NX-GZIP 设备 fd 的 mmap 限制如下：

- size 必须是 PAGE_SIZE
- offset 参数必须是 0ULL

有关其他细节和限制，请参阅 mmap(2) 手册页。

除了 mmap(2) 手册页中列出的错误条件外，还可能遇到以下错误：

| 错误码 | 描述 |
|--------|------|
| EINVAL | fd 未关联一个已打开的窗口（即 mmap() 不是在成功调用 VAS_TX_WIN_OPEN ioctl 后执行的） |
### `EINVAL`: offset field is not 0ULL

---

### 可用VAS引擎的发现
每个系统中的可用VAS实例都将有一个设备树节点，如 `/proc/device-tree/vas@*` 或 `/proc/device-tree/xscom@*/vas@*`。确定芯片或VAS实例，并使用该节点中的 `ibm,vas-id` 属性值来选择特定的VAS实例。

### 复制/粘贴操作
应用程序应使用复制和粘贴指令将CRB发送给NX。参考PowerISA第4.4节中的复制/粘贴指令：[https://openpowerfoundation.org/?resource_lib=power-isa-version-3-0](https://openpowerfoundation.org/?resource_lib=power-isa-version-3-0)

### CRB规范及使用NX
应用程序应使用协处理器请求块（CRB）格式化对协处理器的请求。参考NX-GZIP用户手册以了解CRB的格式，并从用户空间使用NX，例如发送请求和检查请求状态。

### NX错误处理
应用程序向NX发送请求并等待通过轮询协处理器状态块（CSB）标志的状态。NX在每次请求处理后更新CSB中的状态。参考NX-GZIP用户手册了解CSB和状态标志的格式。
如果NX在CSB地址或任何请求缓冲区上遇到翻译错误（称为NX页面错误），则会在CPU上引发中断以处理错误。如果应用程序传递了无效地址或请求缓冲区不在内存中，则可能会发生页面错误。操作系统通过以下数据更新CSB来处理错误：

```c
csb.flags = CSB_V;
csb.cc = CSB_CC_FAULT_ADDRESS;
csb.ce = CSB_CE_TERMINATION;
csb.address = fault_address;
```

当应用程序接收到翻译错误时，可以访问具有错误地址的页面，以便该页面将位于内存中。然后，应用程序可以重新发送此请求到NX。
如果由于无效的CSB地址操作系统无法更新CSB，则会向打开原始请求所在发送窗口的进程发送SEGV信号。此信号返回以下siginfo结构：

```c
siginfo.si_signo = SIGSEGV;
siginfo.si_errno = EFAULT;
siginfo.si_code = SEGV_MAPERR;
siginfo.si_addr = CSB 地址;
```

对于多线程应用，NX发送窗口可以在所有线程之间共享。例如，子线程可以打开一个发送窗口，但其他线程可以使用此窗口向NX发送请求。只要CSB地址有效，即使操作系统正在处理错误，这些请求也会成功。如果NX请求包含无效的CSB地址，则信号将被发送给打开窗口的子线程。但如果线程在不关闭窗口的情况下退出并且使用此窗口发出请求，则信号将被发送给线程组领导者（tgid）。是否忽略或处理这些信号取决于应用程序。
NX-GZIP 用户手册：[https://github.com/libnxz/power-gzip/blob/master/doc/power_nx_gzip_um.pdf](https://github.com/libnxz/power-gzip/blob/master/doc/power_nx_gzip_um.pdf)

### 简单示例

```c
int use_nx_gzip()
{
    int rc, fd;
    void *addr;
    struct vas_setup_attr txattr;

    fd = open("/dev/crypto/nx-gzip", O_RDWR);
    if (fd < 0) {
        fprintf(stderr, "open nx-gzip failed\n");
        return -1;
    }
    memset(&txattr, 0, sizeof(txattr));
    txattr.version = 1;
    txattr.vas_id = -1;
    rc = ioctl(fd, VAS_TX_WIN_OPEN, (unsigned long)&txattr);
    if (rc < 0) {
        fprintf(stderr, "ioctl() n %d, error %d\n", rc, errno);
        return rc;
    }
    addr = mmap(NULL, 4096, PROT_READ|PROT_WRITE, MAP_SHARED, fd, 0ULL);
    if (addr == MAP_FAILED) {
        fprintf(stderr, "mmap() failed, errno %d\n", errno);
        return -errno;
    }
    do {
        // 格式化带有压缩或解压的CRB请求
        // 参考vas_copy/vas_paste测试
        vas_copy((&crb, 0, 1);
        vas_paste(addr, 0, 1);
        // 使用超时轮询csb.flags
        // csb地址列在CRB中
    } while (true)
    close(fd) 或者窗口可以在进程退出时关闭
}
```
更多测试用例或使用场景，请参阅 [https://github.com/libnxz/power-gzip](https://github.com/libnxz/power-gzip)
