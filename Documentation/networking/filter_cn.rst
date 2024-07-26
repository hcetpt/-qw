许可协议标识符：GPL-2.0

.. _网络过滤:

=======================================================
Linux 套接字过滤，即伯克利包过滤器（BPF）
=======================================================

注意
----

此文件过去用于记录与套接字过滤无关的 eBPF 格式和机制。关于 eBPF 的更多详细信息，请参阅 ../bpf/index.rst。

简介
----

Linux 套接字过滤（LSF）源自伯克利包过滤器（BPF）。尽管 BSD 和 Linux 内核过滤之间存在一些显著差异，但在讨论 Linux 上的 BPF 或 LSF 时，我们指的是 Linux 内核中的同一过滤机制。
BPF 允许用户空间程序将一个过滤器附加到任何套接字上，并允许或禁止某些类型的数据通过该套接字。LSF 完全遵循 BSD 的 BPF 的过滤代码结构，因此参考 BSD 的 bpf.4 手册页对于创建过滤器非常有帮助。
在 Linux 上，BPF 比 BSD 简单得多。你不必担心设备或其他类似问题。只需创建你的过滤代码，通过 SO_ATTACH_FILTER 选项将其发送给内核，如果过滤代码通过了内核的检查，那么你就可以立即开始对该套接字上的数据进行过滤。
你也可以通过 SO_DETACH_FILTER 选项从套接字中分离过滤器。这可能不会经常使用，因为当你关闭带有过滤器的套接字时，过滤器会自动移除。另一种不太常见的情况是，在同一个套接字上添加一个不同的过滤器，而另一个过滤器仍在运行：内核会负责移除旧的过滤器并放置新的过滤器，前提是新的过滤器已通过检查；否则，如果新过滤器未通过检查，旧的过滤器将继续保留在该套接字上。
SO_LOCK_FILTER 选项允许锁定附着于套接字的过滤器。一旦设置，过滤器就不能被移除或更改。这允许一个进程设置套接字，附加过滤器，锁定它，然后放弃特权，并确保过滤器将一直保持到套接字关闭。
libpcap 可能是这种结构的最大用户。发出一个高级过滤命令，如 `tcpdump -i em1 port 22`，会通过 libpcap 内部编译器生成一个最终可以通过 SO_ATTACH_FILTER 加载到内核的结构。`tcpdump -i em1 port 22 -ddd` 显示了放入该结构的内容。
虽然我们只讨论了套接字，但 Linux 中的 BPF 在很多其他地方都有应用。例如有用于 netfilter 的 xt_bpf、内核队列层的 cls_bpf、SECCOMP-BPF（SECure COMPuting [1]_），以及团队驱动器、PTP 代码等许多其他地方都使用了 BPF。
.. [1] 文档/userspace-api/seccomp_filter.rst

原始 BPF 论文：

Steven McCanne 和 Van Jacobson。1993年。伯克利包过滤器：一种新的用户级包捕获架构。在 USENIX Winter 1993 会议论文集（USENIX'93）中。USENIX 协会，加利福尼亚州伯克利，美国，2-2。[http://www.tcpdump.org/papers/bpf-usenix93.pdf]

结构
----

用户空间应用程序包含 `<linux/filter.h>`，其中包含了以下相关结构体::

    struct sock_filter {     /* 过滤块 */
        __u16 code;          /* 实际过滤代码 */
        __u8 jt;             /* 跳转真 */
        __u8 jf;             /* 跳转假 */
        __u32 k;             /* 通用多用途字段 */
    };

此类结构体以四元组数组的形式组装，包含 code、jt、jf 和 k 的值。jt 和 jf 是跳转偏移量，k 是提供的代码的一个通用值::

    struct sock_fprog {      /* SO_ATTACH_FILTER 所需 */
        unsigned short len;  /* 过滤块数量 */
        struct sock_filter __user *filter;
    };

为了套接字过滤，指向此结构体的指针（如后续示例所示）会被通过 setsockopt(2) 传递给内核。
以下是提供的示例代码及其解释的中文翻译：

---

:: 

    #include <sys/socket.h>
    #include <sys/types.h>
    #include <arpa/inet.h>
    #include <linux/if_ether.h>
    /* ... */

    /* 从上面的例子中：tcpdump -i em1 port 22 -dd */
    struct sock_filter code[] = {
	    { 0x28,  0,  0, 0x0000000c },
	    { 0x15,  0,  8, 0x000086dd },
	    { 0x30,  0,  0, 0x00000014 },
	    { 0x15,  2,  0, 0x00000084 },
	    { 0x15,  1,  0, 0x00000006 },
	    { 0x15,  0, 17, 0x00000011 },
	    { 0x28,  0,  0, 0x00000036 },
	    { 0x15, 14,  0, 0x00000016 },
	    { 0x28,  0,  0, 0x00000038 },
	    { 0x15, 12, 13, 0x00000016 },
	    { 0x15,  0, 12, 0x00000800 },
	    { 0x30,  0,  0, 0x00000017 },
	    { 0x15,  2,  0, 0x00000084 },
	    { 0x15,  1,  0, 0x00000006 },
	    { 0x15,  0,  8, 0x00000011 },
	    { 0x28,  0,  0, 0x00000014 },
	    { 0x45,  6,  0, 0x00001fff },
	    { 0xb1,  0,  0, 0x0000000e },
	    { 0x48,  0,  0, 0x0000000e },
	    { 0x15,  2,  0, 0x00000016 },
	    { 0x48,  0,  0, 0x00000010 },
	    { 0x15,  0,  1, 0x00000016 },
	    { 0x06,  0,  0, 0x0000ffff },
	    { 0x06,  0,  0, 0x00000000 },
    };

    struct sock_fprog bpf = {
	    .len = ARRAY_SIZE(code),
	    .filter = code,
    };

    int sock = socket(PF_PACKET, SOCK_RAW, htons(ETH_P_ALL));
    if (sock < 0)
	    /* ... 处理错误 ... */

    int ret = setsockopt(sock, SOL_SOCKET, SO_ATTACH_FILTER, &bpf, sizeof(bpf));
    if (ret < 0)
	    /* ... 处理错误 ... */

    /* ... */
    close(sock);

上述示例代码为PF_PACKET套接字附加了一个套接字过滤器，以允许所有端口22上的IPv4/IPv6数据包通过。其余的数据包将被丢弃。
`setsockopt(2)`调用SO_DETACH_FILTER不需要任何参数，而SO_LOCK_FILTER为了防止过滤器被卸载需要一个整数值0或1。
注意，套接字过滤器不仅限于PF_PACKET套接字，也可以用于其他套接字家族。
系统调用概览：

 * `setsockopt(sockfd, SOL_SOCKET, SO_ATTACH_FILTER, &val, sizeof(val));`
 * `setsockopt(sockfd, SOL_SOCKET, SO_DETACH_FILTER, &val, sizeof(val));`
 * `setsockopt(sockfd, SOL_SOCKET, SO_LOCK_FILTER,   &val, sizeof(val));`

通常，对于包套接字的套接字过滤，大多数使用场景都将由libpcap以高级语法覆盖，因此作为应用程序开发者，你应该坚持使用它。除非：i) 使用或链接到libpcap不是一个选项；ii) 所需的BPF过滤器使用了不被libpcap编译器支持的Linux扩展；iii) 过滤器可能更复杂，无法使用libpcap编译器清晰地实现；iv) 特定的过滤器代码应该以不同于libpcap内部编译器的方式进行优化。在这些情况下，手动编写这样的过滤器可以作为一个替代方案。例如，`xt_bpf`和`cls_bpf`用户可能有需求，这可能导致更复杂的过滤器代码，或者无法用libpcap表达（例如，不同的代码路径有不同的返回码）。此外，BPF JIT实现者可能希望手动编写测试案例，因此也需要对BPF代码的低级访问。
BPF引擎和指令集
------------------

在`tools/bpf/`目录下有一个名为`bpf_asm`的小型辅助工具，可用于编写上文提及的示例场景中的低级过滤器。这里提到的汇编语言样式的语法已在`bpf_asm`中实现，并将用于进一步的解释（而不是直接处理可读性较低的操作码，原理相同）。该语法紧密模仿Steven McCanne和Van Jacobson的BPF论文。
BPF架构包含以下基本元素：

  =======          ====================================================
  元素              描述
  =======          ====================================================
  A                32位宽累加器
  X                32位宽X寄存器
  M[]              16个32位宽的杂项寄存器，即“临时存储”，可寻址范围从0到15
  =======          ====================================================

由`bpf_asm`转换成“操作码”的程序是一个数组，该数组由以下元素组成（如前所述）：

  op:16, jt:8, jf:8, k:32

元素`op`是一个16位宽的操作码，其中编码了特定的指令。`jt`和`jf`是两个8位宽的跳转目标，一个用于条件“真时跳转”，另一个用于“假时跳转”。最终，元素`k`包含一个杂项参数，其解释方式取决于`op`中给定的指令。
指令集包括加载、存储、分支、算术逻辑单元、杂项和返回指令，它们也在`bpf_asm`语法中表示。下表列出了所有可用的`bpf_asm`指令以及它们对应的在`linux/filter.h`中定义的操作码：

  ===========      ===================  =====================
  指令              寻址模式              描述
  ===========      ===================  =====================
  ld               1, 2, 3, 4, 12       将字加载到A
  ldi              4                    将字加载到A
  ldh              1, 2                 将半字加载到A
  ldb              1, 2                 将字节加载到A
  ldx              3, 4, 5, 12          将字加载到X
  ldxi             4                    将字加载到X
  ldxb             5                    将字节加载到X

  st               3                    将A存储到M[]
  stx              3                    将X存储到M[]

  jmp              6                    跳转到标签
  ja               6                    跳转到标签
  jeq              7, 8, 9, 10          如果A == <x>则跳转
  jneq             9, 10                如果A != <x>则跳转
  jne              9, 10                如果A != <x>则跳转
  jlt              9, 10                如果A <  <x>则跳转
  jle              9, 10                如果A <= <x>则跳转
  jgt              7, 8, 9, 10          如果A >  <x>则跳转
  jge              7, 8, 9, 10          如果A >= <x>则跳转
  jset             7, 8, 9, 10          如果A &  <x>则跳转

  add              0, 4                 A + <x>
  sub              0, 4                 A - <x>
  mul              0, 4                 A * <x>
  div              0, 4                 A / <x>
  mod              0, 4                 A % <x>
  neg                                   !A
  and              0, 4                 A & <x>
  or               0, 4                 A | <x>
  xor              0, 4                 A ^ <x>
  lsh              0, 4                 A << <x>
  rsh              0, 4                 A >> <x>

  tax                                   将A复制到X
  txa                                   将X复制到A

  ret              4, 11                返回
  ===========      ===================  =====================

下表显示了第二列中的寻址格式：

  ===============  ===================  ===============================================
  寻址模式         语法               描述
  ===============  ===================  ===============================================
   0               x/%x                 寄存器X
   1               [k]                  包中的字节偏移k处的BHW
   2               [x + k]              包中的偏移X + k处的BHW
   3               M[k]                 M[]中的偏移k处的字
   4               #k                   存储在k中的字面值
   5               4*([k]&0xf)          包中的字节偏移k处的较低四位 * 4
   6               L                    跳转标签L
   7               #k,Lt,Lf             如果为真，则跳转到Lt，否则跳转到Lf
   8               x/%x,Lt,Lf           如果为真，则跳转到Lt，否则跳转到Lf
   9               #k,Lt                如果谓词为真，则跳转到Lt
  10               x/%x,Lt              如果谓词为真，则跳转到Lt
  11               a/%a                 累加器A
  12               extension            BPF扩展
  ===============  ===================  ===============================================

Linux内核还有一些BPF扩展，它们与加载指令类一起使用，通过使用负偏移加上特定的扩展偏移来“重载”参数`k`。这种BPF扩展的结果被加载到A中。
可能的BPF扩展如下表所示：

  ===================================   =================================================
  扩展                             描述
  ===================================   =================================================
  len                                   skb->len
  proto                                 skb->protocol
  type                                  skb->pkt_type
  poff                                  有效负载开始偏移
  ifidx                                 skb->dev->ifindex
  nla                                   类型X的Netlink属性，偏移量为A
  nlan                                  类型X的嵌套Netlink属性，偏移量为A
  mark                                  skb->mark
  queue                                 skb->queue_mapping
  hatype                                skb->dev->type
  rxhash                                skb->hash
  cpu                                   raw_smp_processor_id()
  vlan_tci                              skb_vlan_tag_get(skb)
  vlan_avail                            skb_vlan_tag_present(skb)
  vlan_tpid                             skb->vlan_proto
  rand                                  get_random_u32()
  ===================================   =================================================

这些扩展也可以以'#'开头。

下面是一些低级BPF的示例：

**ARP数据包**:

```
ldh [12]
jne #0x806, drop
ret #-1
drop: ret #0
```

**IPv4 TCP数据包**:

```
ldh [12]
jne #0x800, drop
ldb [23]
jneq #6, drop
ret #-1
drop: ret #0
```

**ICMP随机数据包采样，每四个取一个**:

```
ldh [12]
jne #0x800, drop
ldb [23]
jneq #1, drop
# 获取一个随机uint32数字
ld rand
mod #4
jneq #1, drop
ret #-1
drop: ret #0
```

**SECCOMP过滤器示例**:

```
ld [4]                  /* offsetof(struct seccomp_data, arch) */
jne #0xc000003e, bad    /* AUDIT_ARCH_X86_64 */
ld [0]                  /* offsetof(struct seccomp_data, nr) */
jeq #15, good           /* __NR_rt_sigreturn */
jeq #231, good          /* __NR_exit_group */
jeq #60, good           /* __NR_exit */
jeq #0, good            /* __NR_read */
jeq #1, good            /* __NR_write */
jeq #5, good            /* __NR_fstat */
jeq #9, good            /* __NR_mmap */
jeq #14, good           /* __NR_rt_sigprocmask */
jeq #13, good           /* __NR_rt_sigaction */
jeq #35, good           /* __NR_nanosleep */
bad: ret #0             /* SECCOMP_RET_KILL_THREAD */
good: ret #0x7fff0000   /* SECCOMP_RET_ALLOW */
```

低级BPF扩展的示例：

**接口索引为13的数据包**:

```
ld ifidx
jneq #13, drop
ret #-1
drop: ret #0
```

**带有ID 10的VLAN（加速）**:

```
ld vlan_tci
jneq #10, drop
ret #-1
drop: ret #0
```

上述示例代码可以放在一个文件中（此处称为"foo"），然后传递给`bpf_asm`工具以生成操作码，这是`xt_bpf`和`cls_bpf`能够理解并可以直接加载的输出。例如，使用上面的ARP代码：

```
$ ./bpf_asm foo
4,40 0 0 12,21 0 1 2054,6 0 0 4294967295,6 0 0 0,
```

C风格的复制和粘贴输出：

```
$ ./bpf_asm -c foo
{ 0x28,  0,  0, 0x0000000c },
{ 0x15,  0,  1, 0x00000806 },
{ 0x06,  0,  0, 0xffffffff },
{ 0x06,  0,  0, 0000000000 },
```

特别是，由于使用`xt_bpf`或`cls_bpf`可能会导致更复杂的BPF过滤器，这些过滤器可能一开始并不明显，所以在将其附加到实际系统之前，最好先测试过滤器。为此目的，在内核源代码目录下的`tools/bpf/`中有一个名为`bpf_dbg`的小工具。这个调试器允许针对给定的pcap文件测试BPF过滤器，逐步执行pcap数据包上的BPF代码，并进行BPF机器寄存器转储。
启动 bpf_dbg 非常简单，只需执行如下命令：

    # ./bpf_dbg

如果输入和输出不等于标准输入/输出（stdin/stdout），bpf_dbg 将接受一个替代的标准输入源作为第一个参数，以及一个替代的标准输出目标作为第二个参数，例如 `./bpf_dbg test_in.txt test_out.txt`。
除此之外，可以通过文件 "~/.bpf_dbg_init" 设置特定的 libreadline 配置，并且命令历史记录将存储在文件 "~/.bpf_dbg_history" 中。
在 bpf_dbg 中的交互是通过一个带有自动补全功能的 shell 进行的（后续示例中的命令以 '>' 开头表示 bpf_dbg shell）。
通常的工作流程包括：
* 加载 bpf 6,40 0 0 12,21 0 3 2048,48 0 0 23,21 0 1 1,6 0 0 65535,6 0 0 0
  从 bpf_asm 的标准输出加载 BPF 过滤器，或者通过例如 ``tcpdump -iem1 -ddd port 22 | tr '\n' ','`` 转换。需要注意的是，在 JIT 调试（下一节）中，此命令会创建一个临时套接字并将 BPF 代码加载到内核中。因此，这对于 JIT 开发者也非常有用。
* 加载 pcap 文件 foo.pcap

  加载标准的 tcpdump pcap 文件
* 运行 [<n>]

bpf passes:1 fails:9
  对 pcap 中的所有数据包进行遍历，统计过滤器会产生多少次通过和失败。可以指定要遍历的数据包数量上限
* 反汇编::

	l0:	ldh [12]
	l1:	jeq #0x800, l2, l5
	l2:	ldb [23]
	l3:	jeq #0x1, l4, l5
	l4:	ret #0xffff
	l5:	ret #0

  输出 BPF 代码的反汇编结果
* 导出::

	/* { op, jt, jf, k }, */
	{ 0x28,  0,  0, 0x0000000c },
	{ 0x15,  0,  3, 0x00000800 },
	{ 0x30,  0,  0, 0x00000017 },
	{ 0x15,  0,  1, 0x00000001 },
	{ 0x06,  0,  0, 0x0000ffff },
	{ 0x06,  0,  0, 0000000000 },

  输出 C 样式的 BPF 代码
* 断点 0::

	断点位于: l0:	ldh [12]

* 断点 1::

	断点位于: l1:	jeq #0x800, l2, l5

...
在特定的BPF指令处设置断点。发出`run`命令将会从当前数据包继续遍历pcap文件，并在遇到断点时停止（再次执行`run`将从当前活动断点开始执行下一条指令）：

* run::
  
  -- 寄存器转储 --
  pc:       [0]                       <-- 程序计数器
  code:     [40] jt[0] jf[0] k[12]    <-- 当前指令的纯BPF代码
  curr:     l0:	ldh [12]              <-- 当前指令的反汇编
  A:        [00000000][0]             <-- A的内容（十六进制，十进制）
  X:        [00000000][0]             <-- X的内容（十六进制，十进制）
  M[0,15]:  [00000000][0]             <-- M的内容（十六进制，十进制）
  -- 数据包转储 --                   <-- 来自pcap的当前数据包（十六进制）
  len: 42
      0: 00 19 cb 55 55 a4 00 14 a4 43 78 69 08 06 00 01
     16: 08 00 06 04 00 01 00 14 a4 43 78 69 0a 3b 01 26
     32: 00 00 00 00 00 00 0a 3b 01 01
  (断点)
  >

* breakpoint::

  断点：0 1

  显示已设置的断点
* step [-<n>, +<n>]

  从当前程序计数器偏移量开始单步执行BPF程序。因此，在每次调用step时，上述寄存器转储都会被输出。
  这可以向前或向后移动时间，简单的`step`将在下一个BPF指令处中断，即+1。（这里不需要发出`run`命令。）

* select <n>

  选择pcap文件中的指定数据包来继续执行。因此，在下一个`run`或`step`中，BPF程序将针对用户预先选择的数据包进行评估。编号与Wireshark相同，从索引1开始。
* quit

  退出bpf_dbg
即时编译器
------------

Linux内核为x86_64、SPARC、PowerPC、ARM、ARM64、MIPS、RISC-V、s390和ARC内置了一个BPF即时编译器，并且可以通过CONFIG_BPF_JIT启用它。如果由root先前启用，则该即时编译器会透明地对从用户空间附加的每个过滤器或内核内部用户执行编译：

  echo 1 > /proc/sys/net/core/bpf_jit_enable

对于即时编译器开发者、审计等操作，每次编译运行都可以通过以下方式将生成的指令映像输出到内核日志：

  echo 2 > /proc/sys/net/core/bpf_jit_enable

dmesg示例输出：

    [ 3389.935842] flen=6 proglen=70 pass=3 image=ffffffffa0069c8f
    [ 3389.935847] JIT code: 00000000: 55 48 89 e5 48 83 ec 60 48 89 5d f8 44 8b 4f 68
    [ 3389.935849] JIT code: 00000010: 44 2b 4f 6c 4c 8b 87 d8 00 00 00 be 0c 00 00 00
    [ 3389.935850] JIT code: 00000020: e8 1d 94 ff e0 3d 00 08 00 00 75 16 be 17 00 00
    [ 3389.935851] JIT code: 00000030: 00 e8 28 94 ff e0 83 f8 01 75 07 b8 ff ff 00 00
    [ 3389.935852] JIT code: 00000040: eb 02 31 c0 c9 c3

当CONFIG_BPF_JIT_ALWAYS_ON被启用时，bpf_jit_enable永久设置为1，并且设置任何其他值都将导致失败。这同样适用于将bpf_jit_enable设置为2的情况，因为将最终的即时编译图像输出到内核日志是不推荐的，而通过bpftool（位于tools/bpf/bpftool/下）进行检查是一般推荐的方法。
在内核源码树下的tools/bpf/目录中，有一个bpf_jit_disasm工具用于根据内核日志的十六进制转储生成反汇编输出：

	# ./bpf_jit_disasm
	70 bytes emitted from JIT compiler (pass:3, flen:6)
	ffffffffa0069c8f + <x>:
	0:	push   %rbp
	1:	mov    %rsp,%rbp
	4:	sub    $0x60,%rsp
	8:	mov    %rbx,-0x8(%rbp)
	c:	mov    0x68(%rdi),%r9d
	10:	sub    0x6c(%rdi),%r9d
	14:	mov    0xd8(%rdi),%r8
	1b:	mov    $0xc,%esi
	20:	callq  0xffffffffe0ff9442
	25:	cmp    $0x800,%eax
	2a:	jne    0x0000000000000042
	2c:	mov    $0x17,%esi
	31:	callq  0xffffffffe0ff945e
	36:	cmp    $0x1,%eax
	39:	jne    0x0000000000000042
	3b:	mov    $0xffff,%eax
	40:	jmp    0x0000000000000044
	42:	xor    %eax,%eax
	44:	leaveq
	45:	retq

	使用选项`-o`将会把指令编码标注到结果的汇编指令上，这对即时编译器开发者来说非常有用：

	# ./bpf_jit_disasm -o
	70 bytes emitted from JIT compiler (pass:3, flen:6)
	ffffffffa0069c8f + <x>:
	0:	push   %rbp
	    55
	1:	mov    %rsp,%rbp
	    48 89 e5
	4:	sub    $0x60,%rsp
	    48 83 ec 60
	8:	mov    %rbx,-0x8(%rbp)
	    48 89 5d f8
	c:	mov    0x68(%rdi),%r9d
	    44 8b 4f 68
	10:	sub    0x6c(%rdi),%r9d
	    44 2b 4f 6c
	14:	mov    0xd8(%rdi),%r8
	    4c 8b 87 d8 00 00 00
	1b:	mov    $0xc,%esi
	    be 0c 00 00 00
	20:	callq  0xffffffffe0ff9442
	    e8 1d 94 ff e0
	25:	cmp    $0x800,%eax
	    3d 00 08 00 00
	2a:	jne    0x0000000000000042
	    75 16
	2c:	mov    $0x17,%esi
	    be 17 00 00 00
	31:	callq  0xffffffffe0ff945e
	    e8 28 94 ff e0
	36:	cmp    $0x1,%eax
	    83 f8 01
	39:	jne    0x0000000000000042
	    75 07
	3b:	mov    $0xffff,%eax
	    b8 ff ff 00 00
	40:	jmp    0x0000000000000044
	    eb 02
	42:	xor    %eax,%eax
	    31 c0
	44:	leaveq
	    c9
	45:	retq

对于BPF即时编译器开发者而言，bpf_jit_disasm、bpf_asm和bpf_dbg提供了一套有用的工具链来开发和测试内核的即时编译器。
BPF内核内部实现
--------------------

在内核解释器内部，使用了一种与之前段落中描述的BPF类似但格式不同的指令集。然而，该指令集格式更接近底层架构以模仿原生指令集，从而能够获得更好的性能（更多细节稍后）。这种新的指令集被称为eBPF。详情请参见../bpf/index.rst。（注：起源于[e]xtended BPF的eBPF与BPF扩展不同！虽然eBPF是一种指令集，但BPF扩展追溯到了经典BPF的'BPF_LD | BPF_{B,H,W} | BPF_ABS'指令的“重载”。）

新指令集最初设计时考虑了可能的目标，即编写“受限C”程序并将其编译为eBPF，可选地使用GCC/LLVM后端，以便只需两步就能即时映射到现代64位CPU上，性能开销最小，即C -> eBPF -> 原生代码。
目前，新格式用于运行用户BPF程序，包括seccomp BPF、经典套接字过滤器、cls_bpf流量分类器、team驱动程序的负载均衡模式下的分类器、netfilter的xt_bpf扩展、PTP解包器/分类器等等。它们都被内核内部转换为新指令集表示，并在eBPF解释器中运行。对于内核处理程序，使用bpf_prog_create()设置过滤器以及使用bpf_prog_destroy()销毁过滤器都是透明的。函数bpf_prog_run(filter, ctx)透明地调用eBPF解释器或即时编译代码来运行过滤器。'filter'是指向我们从bpf_prog_create()获取的struct bpf_prog的指针，而'ctx'是给定的上下文（例如skb指针）。所有约束和限制在转换为新布局之前都适用于bpf_check_classic()！

目前，经典BPF格式用于大多数32位架构上的即时编译，而x86-64、aarch64、s390x、powerpc64、sparc64、arm32、riscv64、riscv32、loongarch64、arc则从eBPF指令集进行即时编译。
测试
-------

除了 BPF 工具链之外，内核还附带了一个测试模块，其中包含针对经典和 eBPF 的多种测试用例，这些用例可以在 BPF 解释器和 JIT 编译器上执行。该测试模块位于 `lib/test_bpf.c` 中，并可通过 Kconfig 进行启用：

```
CONFIG_TEST_BPF=m
```

在模块构建并安装后，可以通过 `insmod` 或 `modprobe` 针对 'test_bpf' 模块来运行测试套件。测试用例的结果（包括纳秒级的时间记录）可以在内核日志（`dmesg`）中找到。

其他
----

此外，Trinity，Linux 系统调用模糊测试工具，也内置了对 BPF 和 SECCOMP-BPF 内核模糊测试的支持。

作者
----------

本文档由以下人员撰写，旨在为潜在的 BPF 黑客或安全审计者提供一个更好的架构概览：

- Jay Schulist <jschlst@samba.org>
- Daniel Borkmann <daniel@iogearbox.net>
- Alexei Starovoitov <ast@kernel.org>
