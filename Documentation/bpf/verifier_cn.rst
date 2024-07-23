eBPF 验证器
===========

eBPF 程序的安全性通过两个步骤来确定：
第一步执行 DAG 检查，禁止循环以及其他控制流图验证。
特别地，它会检测那些包含不可达指令的程序（尽管传统的 BPF 检查器允许它们存在）。

第二步从第一条指令开始，遍历所有可能的路径。
它模拟每条指令的执行并观察寄存器和栈的状态变化。
在程序开始时，寄存器 R1 包含指向上下文的指针，其类型为 PTR_TO_CTX。
如果验证器看到一条将 R2 设为 R1 的指令，那么 R2 现在也具有 PTR_TO_CTX 类型，并且可以在表达式的右侧使用。
如果 R1 是 PTR_TO_CTX 类型，而指令是 R2=R1+R1，那么 R2 将变为 SCALAR_VALUE，
因为两个有效指针的加法会产生一个无效的指针。
（在“安全”模式下，验证器会拒绝任何形式的指针算术，以确保内核地址不会泄露给非特权用户）

如果一个寄存器从未被写入，它是不可读的：
例如：

```
bpf_mov R0 = R2
bpf_exit
```

将被拒绝，因为 R2 在程序开始时是不可读的。
在调用内核函数后，R1 至 R5 被重置为不可读，而 R0 则具有函数的返回类型。
由于寄存器R6到R9是被调用者保存的，因此在调用过程中它们的状态会被保留。以下是一个正确的程序示例：

```assembly
bpf_mov R6 = 1
bpf_call foo
bpf_mov R0 = R6
bpf_exit
```

如果这里使用的是R1而不是R6，则程序将不会被接受。

加载和存储指令仅允许对有效类型的寄存器使用，这些类型包括PTR_TO_CTX、PTR_TO_MAP、PTR_TO_STACK。它们会进行边界和对齐检查。例如：

```assembly
bpf_mov R1 = 1
bpf_mov R2 = 2
bpf_xadd *(u32 *)(R1 + 3) += R2
bpf_exit
```

这将被拒绝，因为当执行bpf_xadd指令时，R1并没有一个有效的指针类型。

开始时，R1的类型是PTR_TO_CTX（指向通用`struct bpf_context`的指针）。通过回调函数可以自定义验证器，以限制eBPF程序仅能访问ctx结构中特定字段，具有指定的大小和对齐方式。

例如，以下指令：

```assembly
bpf_ld R0 = *(u32 *)(R6 + 8)
```

意在从地址R6 + 8处读取一个字，并将其存储到R0中。如果R6 = PTR_TO_CTX，通过is_valid_access()回调，验证器将知道偏移量8处的4字节大小是可以用于读取的，否则验证器将拒绝该程序。

如果R6 = PTR_TO_STACK，那么访问应该对齐并且在堆栈范围内，范围为[-MAX_BPF_STACK, 0)。在这个例子中，偏移量是8，所以它将无法通过验证，因为它超出了范围。

验证器只允许eBPF程序在写入数据后从堆栈读取数据。经典BPF验证器对M[0-15]内存槽进行类似的检查。

例如：

```assembly
bpf_ld R0 = *(u32 *)(R10 - 4)
bpf_exit
```

这是一个无效的程序。
虽然R10是一个正确的只读寄存器，且其类型为PTR_TO_STACK，同时R10-4在栈的界限内，但是并没有对该位置进行任何存储操作。对于指针寄存器的溢出和填充也进行了跟踪，因为四个（R6-R9）被调用者保存的寄存器可能对某些程序来说是不够的。允许的函数调用是通过bpf_verifier_ops->get_func_proto()定制的。eBPF验证器会检查寄存器是否符合参数约束。函数调用后，寄存器R0将被设置为该函数的返回类型。函数调用是扩展eBPF程序功能的主要机制。套接字过滤器可能允许程序调用一组函数，而追踪过滤器则可能允许完全不同的函数集。如果一个函数被提供给eBPF程序访问，那么从安全角度来看，需要仔细考虑。验证器将保证函数被有效参数调用。

对于传统BPF，seccomp与套接字过滤器有不同的安全限制。seccomp通过两阶段验证解决这个问题：首先是传统的BPF验证器，然后是seccomp验证器。在eBPF的情况下，一个可配置的验证器被共享用于所有使用场景。关于eBPF验证器的详细信息可以在kernel/bpf/verifier.c中找到。

寄存器值跟踪
=============

为了确定eBPF程序的安全性，验证器必须跟踪每个寄存器中的可能值范围，以及栈中的每个槽位。这涉及到监控和理解数据流，确保没有超出预期的边界或执行不安全的操作。这种跟踪对于防止缓冲区溢出、非法内存访问等潜在的安全漏洞至关重要。通过持续监控寄存器和栈空间的值，验证器可以确保程序在执行过程中不会导致系统不稳定或被恶意利用。
这是通过`struct bpf_reg_state`完成的，该结构在include/linux/bpf_verifier.h中定义，它统一了标量值和指针值的追踪。每个寄存器状态都有一个类型，该类型可能是NOT_INIT（寄存器尚未被写入），SCALAR_VALUE（某个不能作为指针使用的值），或是一种指针类型。指针的类型描述了它们的基地址，具体如下：

- PTR_TO_CTX
            指向bpf_context的指针
- CONST_PTR_TO_MAP
            指向bpf_map结构的指针。“常量”是因为禁止对这些指针进行算术运算
- PTR_TO_MAP_VALUE
            指向存储在映射元素中的值的指针
- PTR_TO_MAP_VALUE_OR_NULL
            要么是指向映射值的指针，要么是NULL；映射访问（参见maps.rst）返回此类型，当检查不等于NULL时，它变为PTR_TO_MAP_VALUE。禁止对这些指针进行算术运算
- PTR_TO_STACK
            帧指针
- PTR_TO_PACKET
            skb->data
- PTR_TO_PACKET_END
            skb->data + headlen；禁止进行算术运算
- PTR_TO_SOCKET
            指向隐式引用计数的bpf_sock_ops结构的指针
- PTR_TO_SOCKET_OR_NULL
            要么是指向套接字的指针，要么是NULL；套接字查找返回此类型，当检查不等于NULL时，它变为PTR_TO_SOCKET。PTR_TO_SOCKET是引用计数的，因此程序必须在程序结束前通过套接字释放函数释放引用

对这些指针进行算术运算是禁止的。
然而，指针可能从这个基址偏移（由于指针算术的结果），这在两部分中进行跟踪：'固定偏移'和'可变偏移'。前者在确切已知的值（例如，立即数操作数）被加到指针上时使用，而后者用于那些不完全已知的值。可变偏移也在SCALAR_VALUEs中使用，以追踪寄存器中可能值的范围。

验证器对可变偏移的知识包括：

* 作为无符号数的最小和最大值
* 作为有符号数的最小和最大值

* 对个别位值的了解，形式为'tnum'：一个u64'mask'和一个u64'value'。掩码中的1表示未知值的位；值中的1表示已知为1的位。已知为0的位在掩码和值中都为0；任何位都不应该同时为1。例如，如果一个字节从内存读入寄存器，那么寄存器的顶部56位是已知为零的，而低8位是未知的——这表示为tnum（0x0；0xff）。如果我们然后与0x40进行OR运算，我们得到（0x40；0xbf），然后如果我们加上1，我们得到（0x0；0x1ff），因为可能的进位。
除了算术，寄存器状态也可以通过条件分支更新。例如，如果一个SCALAR_VALUE与8比较大于，在'true'分支中，它的umin_value（无符号最小值）将是9，而在'false'分支中，它将有一个umax_value的8。带符号比较（使用BPF_JSGT或BPF_JSGE）将代替更新有符号的最小/最大值。来自有符号和无符号界限的信息可以组合；例如，如果一个值首先测试小于8，然后测试s>4，验证器会得出结论，该值也大于4且s<8，因为界限阻止了跨越符号边界。
具有可变偏移部分的PTR_TO_PACKETs有一个'id'，这是所有共享相同可变偏移的指针所共有的。这对包范围检查很重要：在向包指针寄存器A添加一个变量后，如果你将其复制到另一个寄存器B，然后向A添加一个常量4，两个寄存器都将共享相同的'id'，但A将有一个固定的+4偏移。然后，如果A的界限被检查，并发现小于一个PTR_TO_PACKET_END，那么寄存器B现在知道至少有4字节的安全范围。关于PTR_TO_PACKET范围的更多信息，请参阅下面的“直接包访问”。
'id'字段还用于PTR_TO_MAP_VALUE_OR_NULL上，所有从地图查找返回的指针副本都共享此字段。这意味着当一个副本被检查并发现非NULL时，所有副本都可以变成PTR_TO_MAP_VALUEs。
除了范围检查，跟踪的信息也被用于强制指针访问的对齐。例如，在大多数系统上，包指针在4字节对齐后的2字节处。如果程序向其添加14字节以跳过以太网头，然后读取IHL并添加（IHL * 4），结果指针将有一个可变偏移，已知为4n+2的某个n，所以加上2字节（NET_IP_ALIGN）给出4字节的对齐，因此通过该指针进行的单词大小的访问是安全的。
'id'字段也用于PTR_TO_SOCKET和PTR_TO_SOCKET_OR_NULL上，所有从套接字查找返回的指针副本都共享此字段。这类似于处理PTR_TO_MAP_VALUE_OR_NULL->PTR_TO_MAP_VALUE的行为，但它也处理指针的引用跟踪。PTR_TO_SOCKET隐式代表了对相应`struct sock`的引用。为了确保引用不会泄露，必须对引用进行NULL检查，并在非NULL情况下，将有效引用传递给套接字释放函数。

直接包访问
===========

在cls_bpf和act_bpf程序中，验证器允许通过skb->data和skb->data_end指针直接访问包数据。

示例::

    1:  r4 = *(u32 *)(r1 +80)  /* 加载 skb->data_end */
    2:  r3 = *(u32 *)(r1 +76)  /* 加载 skb->data */
    3:  r5 = r3
    4:  r5 += 14
    5:  如果 r5 > r4 跳转到 pc+16
    R1=ctx R3=pkt(id=0,off=0,r=14) R4=pkt_end R5=pkt(id=0,off=14,r=14) R10=fp
    6:  r0 = *(u16 *)(r3 +12) /* 访问包的第12和13字节 */

这个从包中加载的2字节是安全的，因为程序作者在指令#5处做了检查``如果 (skb->data + 14 > skb->data_end) 跳转到 err``，这意味着在fall-through的情况下，寄存器R3（指向skb->data）至少有14个可以直接访问的字节。验证器将其标记为R3=pkt(id=0,off=0,r=14)
id=0意味着没有额外的变量被添加到寄存器中。
关闭(off=0)意味着没有添加额外的常量。
r=14是安全访问的范围，这意味着[R3, R3 + 14)字节是可以访问的。
请注意，R5被标记为R5=pkt(id=0,off=14,r=14)。它也指向数据包的数据，但是向寄存器添加了常量14，因此现在指向"skb->data + 14"，可访问的范围是[R5, R5 + 14 - 14)，即零字节。

更复杂的包访问可能如下所示：

    R0=inv1 R1=ctx R3=pkt(id=0,off=0,r=14) R4=pkt_end R5=pkt(id=0,off=14,r=14) R10=fp
    6:  r0 = *(u8 *)(r3 +7) /* 从包中加载第7个字节 */
    7:  r4 = *(u8 *)(r3 +12)
    8:  r4 *= 14
    9:  r3 = *(u32 *)(r1 +76) /* 加载 skb->data */
    10:  r3 += r4
    11:  r2 = r1
    12:  r2 <<= 48
    13:  r2 >>= 48
    14:  r3 += r2
    15:  r2 = r3
    16:  r2 += 8
    17:  r1 = *(u32 *)(r1 +80) /* 加载 skb->data_end */
    18:  如果 r2 > r1 跳转到 pc+2

寄存器R3的状态是 R3=pkt(id=2,off=0,r=8)
id=2表示观察到了两个“r3 += rX”指令，所以r3指向包内的某个偏移量，并且因为程序作者在指令#18处做了“如果(r3 + 8 > r1) goto err”，安全范围是[R3, R3 + 8)。

验证器只允许对包寄存器执行'加'/'减'操作。任何其他操作将把寄存器状态设置为'SCALAR_VALUE'，并且不会直接用于包访问。
“r3 += rX”操作可能会溢出并变得小于原始的skb->data，因此验证器必须阻止这种情况。因此，当它看到“r3 += rX”指令且rX大于16位值时，任何后续的r3与skb->data_end的边界检查都不会给我们'范围'信息，因此试图通过指针读取将给出“无效访问包”的错误。

例如，在指令“r4 = *(u8 *)(r3 +12)”（上面的指令#7）之后，r4的状态是
R4=inv(id=0,umax_value=255,var_off=(0x0; 0xff))，这意味着寄存器的高56位保证为零，关于低8位我们一无所知。在指令“r4 *= 14”之后，状态变为
R4=inv(id=0,umax_value=3570,var_off=(0x0; 0xfffe))，因为将一个8位值乘以常数14会保持高52位为零，同时最低有效位也将为零，因为14是偶数。类似地，“r2 >>= 48”会使
R2=inv(id=0,umax_value=65535,var_off=(0x0; 0xffff))，因为该移位不是符号扩展的。此逻辑实现在adjust_reg_min_max_vals()函数中，它调用adjust_ptr_min_max_vals()来添加指针到标量（或反之亦然），以及adjust_scalar_min_max_vals()来处理两个标量的操作。

最终结果是bpf程序作者可以直接使用正常的C代码访问包，如：

  void *data = (void *)(long)skb->data;
  void *data_end = (void *)(long)skb->data_end;
  struct eth_hdr *eth = data;
  struct iphdr *iph = data + sizeof(*eth);
  struct udphdr *udp = data + sizeof(*eth) + sizeof(*iph);

  如果 (data + sizeof(*eth) + sizeof(*iph) + sizeof(*udp) > data_end)
          返回 0;
  如果 (eth->h_proto != htons(ETH_P_IP))
          返回 0;
  如果 (iph->protocol != IPPROTO_UDP || iph->ihl != 5)
          返回 0;
  如果 (udp->dest == 53 || udp->source == 9)
          ...;

这使得此类程序比使用LD_ABS指令编写起来更容易，而且显著更快。

修剪
=====

验证器实际上并不会遍历程序的所有可能路径。对于每个新的分支进行分析时，验证器会查看在此指令下所有之前的状态。如果其中任何一个包含当前状态的子集，则该分支将被'修剪' - 即，先前状态被接受的事实意味着当前状态也会如此。例如，如果在先前状态中，r1持有一个包指针，而在当前状态下，r1持有一个范围相同或更长、至少同样严格对齐的包指针，则r1是安全的。同样，如果r2之前是NOT_INIT，那么它不可能在那一点后的任何路径中被使用，因此r2中的任何值（包括另一个NOT_INIT）都是安全的。实现是在regsafe()函数中。

修剪不仅考虑寄存器，还考虑堆栈（及其可能持有的任何溢出寄存器）。它们都必须是安全的才能修剪分支。
这是在states_equal()中实现的。
关于状态剪枝实现的一些技术细节可以在下面找到：
寄存器存活追踪
-------------------

为了使状态剪枝有效，每个寄存器和栈槽的存活状态都会被追踪。基本思想是追踪哪些寄存器和栈槽在程序后续执行直至程序退出时实际被使用。从未被使用的寄存器和栈槽可以从缓存的状态中移除，从而使得更多状态与一个缓存状态等价。这可以通过以下程序来说明：

  0: 调用bpf_get_prandom_u32()
  1: r1 = 0
  2: 如果r0 == 0则跳转+1
  3: r0 = 1
  --- 检查点 ---
  4: r0 = r1
  5: 退出

假设在指令#4处创建了一个状态缓存条目（这些条目在下面的文本中也被称为“检查点”）。验证器可以带着两种可能的寄存器状态到达该指令：

* r0 = 1, r1 = 0
* r0 = 0, r1 = 0

然而，只有寄存器``r1``的值对于成功完成验证是重要的。存活追踪算法的目标是发现这一事实，并确定这两个状态实际上是等价的。

数据结构
~~~~~~~~~~~~~~~

存活状态通过以下数据结构进行追踪：

```c
  enum bpf_reg_liveness {
	REG_LIVE_NONE = 0,
	REG_LIVE_READ32 = 0x1,
	REG_LIVE_READ64 = 0x2,
	REG_LIVE_READ = REG_LIVE_READ32 | REG_LIVE_READ64,
	REG_LIVE_WRITTEN = 0x4,
	REG_LIVE_DONE = 0x8,
  };
```

```c
  struct bpf_reg_state {
 	..
struct bpf_reg_state *parent;
 	..
enum bpf_reg_liveness live;
 	..
};
```

```c
  struct bpf_stack_state {
	struct bpf_reg_state spilled_ptr;
	..
};
```

```c
  struct bpf_func_state {
	struct bpf_reg_state regs[MAX_BPF_REG];
        ..
struct bpf_stack_state *stack;
  }
```

```c
  struct bpf_verifier_state {
	struct bpf_func_state *frame[MAX_CALL_FRAMES];
	struct bpf_verifier_state *parent;
        ..
}
```

* ``REG_LIVE_NONE``是在创建新的验证器状态时分配给``->live``字段的初始值；

* ``REG_LIVE_WRITTEN``意味着寄存器（或栈槽）的值由这个验证器状态的父级和自身之间的某条已验证指令定义；

* ``REG_LIVE_READ{32,64}``意味着寄存器（或栈槽）的值被此验证器状态的某个子状态读取；

* ``REG_LIVE_DONE``是``clean_verifier_state()``用于避免多次处理同一个验证器状态以及进行一些合理性检查的标记；

* ``->live``字段的值是由使用位或组合``enum bpf_reg_liveness``值形成的。
为了在父状态和子状态之间传播信息，会建立一个*注册父链*。每个寄存器或栈槽都通过一个`->parent`指针链接到其父状态中的相应寄存器或栈槽。这种链接在`is_state_visited()`中创建状态时建立，并且可能由从`__check_func_call()`调用的`set_callee_state()`修改。寄存器/栈槽之间的对应规则如下：

* 对于当前栈帧，新状态中的寄存器和栈槽与父状态中相同索引的寄存器和栈槽相连。
* 对于外部栈帧，只有保存者寄存器（r6-r9）和栈槽与父状态中相同索引的寄存器和栈槽相连。
* 当处理函数调用时，会分配一个新的`struct bpf_func_state`实例，它封装了一组新的寄存器和栈槽。对于这个新帧，r6-r9和栈槽的父链接设置为nil，r1-r5的父链接则匹配调用者的r1-r5的父链接。

这可以通过以下图示来说明（箭头代表`->parent`指针）：

      ...                    ; 帧#0，一些指令
  --- 检查点 #0 ---
  1 : r6 = 42                ; 帧#0
  --- 检查点 #1 ---
  2 : 调用 foo()             ; 帧#0
      ...                    ; 帧#1，foo()中的指令
  --- 检查点 #2 ---
      ...                    ; 帧#1，foo()中的指令
  --- 检查点 #3 ---
      返回                  ; 帧#1，从foo()返回
  3 : r1 = r6                ; 帧#0  <- 当前状态

             +-------------------------------+-------------------------------+
             |           帧 #0            |           帧 #1            |
  检查点 +-------------------------------+-------------------------------+
  #0         | r0 | r1-r5 | r6-r9 | fp-8 ... |
             +-------------------------------+
                ^    ^       ^       ^
                |    |       |       |
  检查点 +-------------------------------+
  #1         | r0 | r1-r5 | r6-r9 | fp-8 ... |
             +-------------------------------+
                     ^       ^       ^
                     |_______|_______|_______________
                             |       |               |
               nil  nil      |       |               |      nil     nil
                |    |       |       |               |       |       |
  检查点 +-------------------------------+-------------------------------+
  #2         | r0 | r1-r5 | r6-r9 | fp-8 ... | r0 | r1-r5 | r6-r9 | fp-8 ... |
             +-------------------------------+-------------------------------+
                             ^       ^               ^       ^       ^
               nil  nil      |       |               |       |       |
                |    |       |       |               |       |       |
  检查点 +-------------------------------+-------------------------------+
  #3         | r0 | r1-r5 | r6-r9 | fp-8 ... | r0 | r1-r5 | r6-r9 | fp-8 ... |
             +-------------------------------+-------------------------------+
                             ^       ^
               nil  nil      |       |
                |    |       |       |
  当前    +-------------------------------+
  状态      | r0 | r1-r5 | r6-r9 | fp-8 ... |
             +-------------------------------+
                             \
                               r6读取标记通过这些链接传播
                               直到达检查点#1
检查点#1包含r6的写入标记
                               因为有指令(1)，因此读取传播
                               不会达到检查点#0（参见下面的部分）
活跃性标记跟踪
~~~~~~~~~~~~~~~~~~~~~~~

对于每个处理过的指令，验证器跟踪被读取和写入的寄存器和栈槽。该算法的主要思想是：读取标记沿状态父链反向传播，直到遇到写入标记，后者“屏蔽”了更早的状态不受读取影响。关于读取的信息通过函数`mark_reg_read()`传播，可以总结如下：

  `mark_reg_read(struct bpf_reg_state *state, ...):`
      parent = state->parent
      while parent:
          if state->live & REG_LIVE_WRITTEN:
              break
          if parent->live & REG_LIVE_READ64:
              break
          parent->live |= REG_LIVE_READ64
          state = parent
          parent = state->parent

注释：

* 读取标记应用于**父**状态，而写入标记应用于**当前**状态。寄存器或栈槽上的写入标记意味着它被从父状态到当前状态的直线代码中的某个指令更新。
* 关于`REG_LIVE_READ32`的细节被省略。
* 函数`propagate_liveness()`（参见`read_marks_for_cache_hits`部分）可能会覆盖第一个父链接。请参考`propagate_liveness()`和`mark_reg_read()`源代码中的注释以获取更多细节。
由于栈写入可能有不同的大小，`REG_LIVE_WRITTEN`标记保守地应用：仅当写入大小对应于寄存器大小时，栈槽才被标记为已写入，例如参见`save_register_state()`函数。
考虑以下示例：

  0: (*u64)(r10 - 8) = 0   ; 定义8字节的fp-8
  --- 检查点 #0 ---
  1: (*u32)(r10 - 8) = 1   ; 重新定义低4字节
  2: r1 = (*u32)(r10 - 8)  ; 读取在(1)中定义的低4字节
  3: r2 = (*u32)(r10 - 4)  ; 读取在(0)中定义的高4字节

如上所述，(1)处的写操作不计入"REG_LIVE_WRITTEN"。如果
情况相反，上述算法将无法从(3)传播读标记到检查点#0。
一旦到达"BPF_EXIT"指令，将调用"update_branch_counts()"来更新
每个验证状态链中的"->branches"计数器。当"->branches"计数器变为零时，
验证状态成为缓存验证状态集的有效条目。
缓存中的每个验证状态条目都由函数"clean_live_states()"进行后处理。
此函数将所有没有"REG_LIVE_READ{32,64}"标记的寄存器和栈槽标记为"NOT_INIT"
或"STACK_INVALID"。
以这种方式标记的寄存器/栈槽在从"states_equal()"调用的"stacksafe()"函数中被忽略，
当考虑将状态缓存条目与当前状态等效时。

现在可以解释本节开头的例子是如何工作的：

  0: 调用bpf_get_prandom_u32()
  1: r1 = 0
  2: 如果r0 == 0则跳转+1
  3: r0 = 1
  --- 检查点[0] ---
  4: r0 = r1
  5: 退出

* 在指令#2处达到分支点，状态"{ r0 == 0, r1 == 0, pc == 4 }"
  被推入状态处理队列（pc代表程序计数器）
* 在指令#4处：

  * 创建"检查点[0]"的状态缓存条目："{ r0 == 1, r1 == 0, pc == 4 }";
  * "检查点[0].r0"被标记为已写入；
  * "检查点[0].r1"被标记为已读取；

* 在指令#5处达到退出，现在"检查点[0]"可以由"clean_live_states()"
  处理。经过此处理后，"检查点[0].r1"具有读取标记，而所有其他寄存器和栈槽都被标记为"NOT_INIT"
  或"STACK_INVALID"

* 状态"{ r0 == 0, r1 == 0, pc == 4 }"从状态队列中弹出，并与缓存状态"{ r1 == 0, pc == 4 }"进行比较，
  认为这些状态是等效的。

.. _read_marks_for_cache_hits:

缓存命中时的读取标记传播
~~~~~~~~~~~~~~~~~~~~~~~~~~

另一个要点是在找到之前已验证的状态时如何处理读取标记。
在缓存命中时，验证器的行为必须如同当前状态已被验证至程序退出一样。
这意味着必须将缓存状态上的所有读取标记沿当前状态的父级链传播。
下面的示例说明了这一点的重要性。函数"propagate_liveness()"处理这种情况。
考虑以下状态父级链（S是起始状态，A-E是派生状态，->箭头显示哪个状态是从哪个派生的）：

                   r1读取
            <-------------                A[r1] == 0
                                          C[r1] == 0
      S ---> A ---> B ---> 退出           E[r1] == 1
      |
      ` ---> C ---> D
      |
      ` ---> E      ^
                    |___   假设所有这些
             ^           状态都在insn #Y处
             |
      假设所有这些
    状态都在insn #X处

* 首先验证状态链"S -> A -> B -> 退出"
* 当"B -> 退出"被验证时，寄存器"r1"被读取，这个读取标记向上传播到状态"A"
* 当验证状态链"C -> D"时，状态"D"结果与状态"B"等效
* 对于`r1`的读取标记必须传播到状态`C`，否则状态`C`可能会被错误地标记为与状态`E`等价，尽管`C`和`E`之间`r1`寄存器的值不同。
理解eBPF验证器消息

以下是一些无效的eBPF程序及其在日志中看到的验证器错误消息的例子：

含有不可达指令的程序::

  static struct bpf_insn prog[] = {
  BPF_EXIT_INSN(),
  BPF_EXIT_INSN(),
  };

错误::

  不可达指令1

读取未初始化寄存器的程序::

  BPF_MOV64_REG(BPF_REG_0, BPF_REG_2),
  BPF_EXIT_INSN(),

错误::

  0: (bf) r0 = r2
  R2!read_ok

在退出前未初始化R0的程序::

  BPF_MOV64_REG(BPF_REG_2, BPF_REG_1),
  BPF_EXIT_INSN(),

错误::

  0: (bf) r2 = r1
  1: (95) exit
  R0!read_ok

访问堆栈越界的程序::

    BPF_ST_MEM(BPF_DW, BPF_REG_10, 8, 0),
    BPF_EXIT_INSN(),

错误::

    0: (7a) *(u64 *)(r10 +8) = 0
    堆栈偏移量无效off=8 size=8

在传递堆栈地址到函数前未初始化堆栈的程序::

  BPF_MOV64_REG(BPF_REG_2, BPF_REG_10),
  BPF_ALU64_IMM(BPF_ADD, BPF_REG_2, -8),
  BPF_LD_MAP_FD(BPF_REG_1, 0),
  BPF_RAW_INSN(BPF_JMP | BPF_CALL, 0, 0, 0, BPF_FUNC_map_lookup_elem),
  BPF_EXIT_INSN(),

错误::

  0: (bf) r2 = r10
  1: (07) r2 += -8
  2: (b7) r1 = 0x0
  3: (85) call 1
  从堆栈间接读取无效off -8+0 size 8

调用map_lookup_elem()函数时使用了无效的map_fd=0的程序::

  BPF_ST_MEM(BPF_DW, BPF_REG_10, -8, 0),
  BPF_MOV64_REG(BPF_REG_2, BPF_REG_10),
  BPF_ALU64_IMM(BPF_ADD, BPF_REG_2, -8),
  BPF_LD_MAP_FD(BPF_REG_1, 0),
  BPF_RAW_INSN(BPF_JMP | BPF_CALL, 0, 0, 0, BPF_FUNC_map_lookup_elem),
  BPF_EXIT_INSN(),

错误::

  0: (7a) *(u64 *)(r10 -8) = 0
  1: (bf) r2 = r10
  2: (07) r2 += -8
  3: (b7) r1 = 0x0
  4: (85) call 1
  文件描述符0没有指向有效的bpf_map

在访问映射元素前未检查map_lookup_elem()返回值的程序::

  BPF_ST_MEM(BPF_DW, BPF_REG_10, -8, 0),
  BPF_MOV64_REG(BPF_REG_2, BPF_REG_10),
  BPF_ALU64_IMM(BPF_ADD, BPF_REG_2, -8),
  BPF_LD_MAP_FD(BPF_REG_1, 0),
  BPF_RAW_INSN(BPF_JMP | BPF_CALL, 0, 0, 0, BPF_FUNC_map_lookup_elem),
  BPF_ST_MEM(BPF_DW, BPF_REG_0, 0, 0),
  BPF_EXIT_INSN(),

错误::

  0: (7a) *(u64 *)(r10 -8) = 0
  1: (bf) r2 = r10
  2: (07) r2 += -8
  3: (b7) r1 = 0x0
  4: (85) call 1
  5: (7a) *(u64 *)(r0 +0) = 0
  R0无效内存访问'map_value_or_null'

正确检查了map_lookup_elem()返回值是否为NULL，但以不正确的对齐方式访问内存的程序::

  BPF_ST_MEM(BPF_DW, BPF_REG_10, -8, 0),
  BPF_MOV64_REG(BPF_REG_2, BPF_REG_10),
  BPF_ALU64_IMM(BPF_ADD, BPF_REG_2, -8),
  BPF_LD_MAP_FD(BPF_REG_1, 0),
  BPF_RAW_INSN(BPF_JMP | BPF_CALL, 0, 0, 0, BPF_FUNC_map_lookup_elem),
  BPF_JMP_IMM(BPF_JEQ, BPF_REG_0, 0, 1),
  BPF_ST_MEM(BPF_DW, BPF_REG_0, 4, 0),
  BPF_EXIT_INSN(),

错误::

  0: (7a) *(u64 *)(r10 -8) = 0
  1: (bf) r2 = r10
  2: (07) r2 += -8
  3: (b7) r1 = 1
  4: (85) call 1
  5: (15) if r0 == 0x0 goto pc+1
   R0=map_ptr R10=fp
  6: (7a) *(u64 *)(r0 +4) = 0
  访问错位off 4 size 8

在一侧的'if'分支中正确检查了map_lookup_elem()返回值是否为NULL并以正确的对齐方式访问内存，但在另一侧的'if'分支中未能做到这一点的程序::

  BPF_ST_MEM(BPF_DW, BPF_REG_10, -8, 0),
  BPF_MOV64_REG(BPF_REG_2, BPF_REG_10),
  BPF_ALU64_IMM(BPF_ADD, BPF_REG_2, -8),
  BPF_LD_MAP_FD(BPF_REG_1, 0),
  BPF_RAW_INSN(BPF_JMP | BPF_CALL, 0, 0, 0, BPF_FUNC_map_lookup_elem),
  BPF_JMP_IMM(BPF_JEQ, BPF_REG_0, 0, 2),
  BPF_ST_MEM(BPF_DW, BPF_REG_0, 0, 0),
  BPF_EXIT_INSN(),
  BPF_ST_MEM(BPF_DW, BPF_REG_0, 0, 1),
  BPF_EXIT_INSN(),

错误::

  0: (7a) *(u64 *)(r10 -8) = 0
  1: (bf) r2 = r10
  2: (07) r2 += -8
  3: (b7) r1 = 1
  4: (85) call 1
  5: (15) if r0 == 0x0 goto pc+2
   R0=map_ptr R10=fp
  6: (7a) *(u64 *)(r0 +0) = 0
  7: (95) exit

  从5到8: R0=imm0 R10=fp
  8: (7a) *(u64 *)(r0 +0) = 1
  R0无效内存访问'imm'

执行套接字查找后设置指针为NULL而未进行检查的程序::

  BPF_MOV64_IMM(BPF_REG_2, 0),
  BPF_STX_MEM(BPF_W, BPF_REG_10, BPF_REG_2, -8),
  BPF_MOV64_REG(BPF_REG_2, BPF_REG_10),
  BPF_ALU64_IMM(BPF_ADD, BPF_REG_2, -8),
  BPF_MOV64_IMM(BPF_REG_3, 4),
  BPF_MOV64_IMM(BPF_REG_4, 0),
  BPF_MOV64_IMM(BPF_REG_5, 0),
  BPF_EMIT_CALL(BPF_FUNC_sk_lookup_tcp),
  BPF_MOV64_IMM(BPF_REG_0, 0),
  BPF_EXIT_INSN(),

错误::

  0: (b7) r2 = 0
  1: (63) *(u32 *)(r10 -8) =
