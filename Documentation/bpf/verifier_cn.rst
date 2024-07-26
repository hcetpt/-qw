============= 
eBPF 验证器
=============

eBPF 程序的安全性通过两个步骤来确定：

第一步是执行有向无环图 (DAG) 检查以禁止循环和其他控制流图 (CFG) 的验证。特别是，它会检测出包含不可达指令的程序（尽管传统的 BPF 检查器允许这类指令存在）。

第二步从第一条指令开始，遍历所有可能的路径。它模拟每条指令的执行，并观察寄存器和栈的状态变化。在程序开始时，寄存器 R1 包含指向上下文的指针，并具有类型 PTR_TO_CTX。如果验证器看到一条如 R2=R1 的指令，则 R2 现在也具有类型 PTR_TO_CTX，并且可以在表达式的右侧使用。如果 R1 是 PTR_TO_CTX 类型，而指令为 R2=R1+R1，则 R2 将变为 SCALAR_VALUE 类型，因为两个有效指针的相加将得到一个无效的指针（在“安全”模式下，验证器将拒绝任何形式的指针运算，以确保内核地址不会泄露给非特权用户）。

如果某个寄存器从未被写入过，则其内容不可读：

```
bpf_mov R0 = R2
bpf_exit
```

上述代码将被拒绝，因为 R2 在程序开始时是不可读的。
在调用内核函数后，寄存器 R1 至 R5 将被重置为不可读状态，而 R0 将包含函数的返回值类型。
由于寄存器R6到R9是被调用者保存的，因此在函数调用过程中它们的状态会被保留。

以下程序是正确的：
```assembly
bpf_mov R6 = 1
bpf_call foo
bpf_mov R0 = R6
bpf_exit
```
如果这里使用的是R1而不是R6，则该程序将不会被接受。

加载和存储指令只能用于指针类型的寄存器，这些类型包括PTR_TO_CTX、PTR_TO_MAP和PTR_TO_STACK。这些指针需要进行边界和对齐检查。
例如：
```assembly
bpf_mov R1 = 1
bpf_mov R2 = 2
bpf_xadd *(u32 *)(R1 + 3) += R2
bpf_exit
```
这个程序将被拒绝，因为在执行`bpf_xadd`指令时，R1并不具有有效的指针类型。
在开始时，R1的类型是PTR_TO_CTX（即指向通用`struct bpf_context`结构体的指针）。
通过一个回调函数可以定制验证器，以限制eBPF程序仅能访问ctx结构体中特定大小和对齐方式的字段。
例如，以下指令：
```assembly
bpf_ld R0 = *(u32 *)(R6 + 8)
```
意图是从地址R6+8处加载一个单词，并将其存储到R0中。
如果R6=PTR_TO_CTX，通过`is_valid_access()`回调函数，验证器将知道偏移量8处的4字节数据是可以读取的，否则验证器会拒绝该程序。
如果R6=PTR_TO_STACK，则访问必须对齐并且位于栈的边界内，这些边界为[-MAX_BPF_STACK, 0)。在这个例子中，偏移量为8，所以它将无法通过验证，因为它超出了边界。
验证器只允许eBPF程序在写入栈之后从栈中读取数据。
经典BPF验证器也进行了类似的检查，针对M[0-15]内存槽。
例如：
```assembly
bpf_ld R0 = *(u32 *)(R10 - 4)
bpf_exit
```
是一个无效的程序。
虽然 R10 是正确的只读寄存器，类型为指向栈的指针（PTR_TO_STACK），并且 R10 - 4 也在栈的边界内，但是并没有对该位置进行存储操作。
还跟踪了指针寄存器的溢出/填充操作，因为四个（R6-R9）被调用者保存的寄存器对于某些程序来说可能不够用。
允许的函数调用通过 `bpf_verifier_ops->get_func_proto()` 进行定制。
eBPF 验证器会检查寄存器是否符合参数约束。
函数调用后，寄存器 R0 将被设置为该函数的返回类型。
函数调用是扩展 eBPF 程序功能的主要机制。
套接字过滤器可能允许程序调用一组特定的函数，而追踪过滤器则可能允许完全不同的函数集。
如果一个函数被赋予 eBPF 程序访问权限，那么从安全角度来看需要仔细考虑。验证器将保证该函数被传入有效的参数。
seccomp 与套接字过滤器对经典 BPF 有不同的安全限制。
seccomp 通过两阶段验证解决了这个问题：首先是经典的 BPF 验证器，然后是 seccomp 验证器。而在 eBPF 的情况下，一个可配置的验证器适用于所有使用场景。
有关 eBPF 验证器的详细信息，请参见 `kernel/bpf/verifier.c`。

寄存器值跟踪
==============

为了确定 eBPF 程序的安全性，验证器必须跟踪每个寄存器中可能的值范围，以及栈中的每个槽位的值范围。
这是通过 `struct bpf_reg_state` 实现的，该结构定义在 `include/linux/bpf_verifier.h` 中，它统一了标量值和指针值的跟踪。每个寄存器状态都有一个类型，该类型可以是 NOT_INIT（寄存器未被写入），SCALAR_VALUE（某个不能作为指针使用的值），或是一个指针类型。指针类型的分类描述了它们的基础，如下：

    PTR_TO_CTX
            指向 bpf_context 的指针
    CONST_PTR_TO_MAP
            指向 bpf_map 结构体的指针。“常量”是因为禁止对这些指针进行算术运算
    PTR_TO_MAP_VALUE
            指向存储在 map 元素中的值的指针
    PTR_TO_MAP_VALUE_OR_NULL
            要么指向 map 值的指针，要么为 NULL；map 访问（参见 maps.rst）返回此类型，在检查不等于 NULL 时变为 PTR_TO_MAP_VALUE。禁止对这些指针进行算术运算
    PTR_TO_STACK
            栈帧指针
    PTR_TO_PACKET
            skb->data
    PTR_TO_PACKET_END
            skb->data + headlen；禁止进行算术运算
    PTR_TO_SOCKET
            指向 bpf_sock_ops 结构体的指针，隐式引用计数
    PTR_TO_SOCKET_OR_NULL
            要么指向一个套接字的指针，要么为 NULL；套接字查找返回此类型，在检查不等于 NULL 时变为 PTR_TO_SOCKET。PTR_TO_SOCKET 是引用计数的，因此程序必须在程序结束前通过套接字释放函数释放引用
禁止对这些指针进行算术运算
然而，指针可能从这个基址偏移（由于指针算术的结果），并且这种偏移被分为两部分进行跟踪：'固定偏移'和'变量偏移'。前者用于确切已知的值（例如，立即数操作数）与指针相加的情况，而后者则用于不完全确定的值。变量偏移也用于SCALAR_VALUE中，以跟踪寄存器中可能值的范围。
验证器对变量偏移的了解包括：

* 无符号的最小值和最大值
* 带符号的最小值和最大值

* 关于各个位值的知识，采用'tnum'形式：一个u64的'mask'和一个u64的'value'。mask中的1表示未知值的位；value中的1表示已知为1的位。已知为0的位在mask和value中都是0；没有位应该同时为1。例如，如果从内存读取一个字节到寄存器中，那么寄存器的高56位是已知为0的，而低8位是未知的——这表示为tnum (0x0; 0xff)。如果我们然后与0x40做或运算，我们得到(0x40; 0xbf)，接着如果我们加上1，则得到(0x0; 0x1ff)，这是因为可能产生的进位。
除了算术运算外，寄存器状态也可以通过条件分支来更新。例如，如果一个SCALAR_VALUE与8进行比较（大于8），在'true'分支中，它的无符号最小值将是9，而在'false'分支中，它的无符号最大值将是8。带符号的比较（使用BPF_JSGT或BPF_JSGE）将更新带符号的最小/最大值。来自带符号和无符号界限的信息可以结合起来；例如，如果一个值首先测试小于8，然后测试大于4（带符号），验证器会得出结论该值还大于4且小于8（带符号），因为这些界限阻止了跨越符号边界。
具有变量偏移部分的PTR_TO_PACKET有一个'id'，这是所有共享相同变量偏移的指针共有的。这对于包范围检查非常重要：在向包指针寄存器A添加一个变量后，如果你将它复制到另一个寄存器B，然后给A加上一个常数4，两个寄存器将共享相同的'id'，但A将有一个固定偏移+4。然后，如果A经过边界检查并发现小于PTR_TO_PACKET_END，那么寄存器B现在已知至少有4个字节的安全范围。有关PTR_TO_PACKET范围的更多信息，请参阅下面的“直接包访问”。
'id'字段也被用于PTR_TO_MAP_VALUE_OR_NULL上，这是所有从映射查找返回的指针副本共有的。这意味着当一个副本被检查并发现不是NULL时，所有副本都可以变为PTR_TO_MAP_VALUE。
除了范围检查外，跟踪的信息还用于强制执行指针访问的对齐。例如，在大多数系统中，包指针是在4字节对齐后的2字节处。如果程序向其添加14字节以跳过以太网头，然后读取IHL并加上(IHL * 4)，最终的指针将有一个变量偏移，已知为4n+2的形式（对于某个n），因此加上2字节（NET_IP_ALIGN）就得到了4字节对齐，这样通过该指针进行字大小的访问就是安全的。
'id'字段也被用于PTR_TO_SOCKET和PTR_TO_SOCKET_OR_NULL，这是所有从套接字查找返回的指针副本共有的。这类似于PTR_TO_MAP_VALUE_OR_NULL到PTR_TO_MAP_VALUE处理的行为，但它还处理了指针的引用跟踪。PTR_TO_SOCKET隐式地代表了指向相应的`struct sock`的引用。为了确保不会泄露该引用，必须对其进行NULL检查，并在非NULL的情况下，将有效的引用传递给套接字释放函数。

直接包访问
=============

在cls_bpf和act_bpf程序中，验证器允许通过skb->data和skb->data_end指针直接访问包数据。
例如：

    1:  r4 = *(u32 *)(r1 +80)  /* 加载 skb->data_end */
    2:  r3 = *(u32 *)(r1 +76)  /* 加载 skb->data */
    3:  r5 = r3
    4:  r5 += 14
    5:  如果 r5 > r4 跳转到 pc+16
    R1=ctx R3=pkt(id=0,off=0,r=14) R4=pkt_end R5=pkt(id=0,off=14,r=14) R10=fp
    6:  r0 = *(u16 *)(r3 +12) /* 访问包的第12和13字节 */

从包中加载这两个字节的操作是安全的，因为程序作者在指令#5中做了检查 `如果 (skb->data + 14 > skb->data_end) 跳转到 err`，这意味着在直接通过的路径中，寄存器R3（指向skb->data）至少有14个可直接访问的字节。验证器将其标记为 R3=pkt(id=0,off=0,r=14)
id=0意味着没有额外的变量被添加到寄存器中。
翻译为中文：

`off=0` 表示没有添加额外的常量。
`r=14` 是安全访问范围，意味着字节 `[R3, R3 + 14)` 是可接受的。
需要注意的是，R5 被标记为 `R5=pkt(id=0,off=14,r=14)`。它同样指向数据包的数据，但是向寄存器中添加了常量 14，因此现在指向 `skb->data + 14`，并且可访问范围是 `[R5, R5 + 14 - 14)`，即零字节。
更复杂的包访问可能如下所示：

    R0=inv1 R1=ctx R3=pkt(id=0,off=0,r=14) R4=pkt_end R5=pkt(id=0,off=14,r=14) R10=fp
    6:  r0 = *(u8 *)(r3 +7) /* 从数据包加载第 7 个字节 */
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
    R0=inv(id=0,umax_value=255,var_off=(0x0; 0xff)) R1=pkt_end R2=pkt(id=2,off=8,r=8) R3=pkt(id=2,off=0,r=8) R4=inv(id=0,umax_value=3570,var_off=(0x0; 0xfffe)) R5=pkt(id=0,off=14,r=14) R10=fp
    19:  r1 = *(u8 *)(r3 +4)

寄存器 R3 的状态为 `R3=pkt(id=2,off=0,r=8)`。
`id=2` 表示已经看到了两个 `r3 += rX` 指令，因此 r3 指向某个数据包内的偏移位置，并且因为程序作者在指令 #18 中执行了 `if (r3 + 8 > r1) goto err`，所以安全范围是 `[R3, R3 + 8)`。
验证器只允许对数据包寄存器执行 '加法'/'减法' 操作。任何其他操作都会将寄存器状态设置为 'SCALAR_VALUE'，并且它将无法用于直接的数据包访问。
`r3 += rX` 可能会导致溢出并变得小于原始的 `skb->data`，因此验证器必须防止这种情况发生。因此，当它看到 `r3 += rX` 指令并且 rX 大于 16 位值时，任何后续对 r3 与 `skb->data_end` 进行的边界检查都不会给出 '范围' 信息，因此尝试通过该指针读取数据将导致“无效访问数据包”的错误。
例如，在指令 `r4 = *(u8 *)(r3 +12)`（上述指令 #7）之后，r4 的状态为 `R4=inv(id=0,umax_value=255,var_off=(0x0; 0xff))`，这意味着寄存器的高 56 位保证为零，而关于低 8 位的信息未知。在指令 `r4 *= 14` 之后，状态变为 `R4=inv(id=0,umax_value=3570,var_off=(0x0; 0xfffe))`，因为将一个 8 位的值乘以常数 14 将保持高 52 位为零，并且最低有效位也将为零，因为 14 是偶数。类似地，`r2 >>= 48` 将使 `R2=inv(id=0,umax_value=65535,var_off=(0x0; 0xffff))`，因为该移位不会扩展符号。此逻辑在 `adjust_reg_min_max_vals()` 函数中实现，该函数调用 `adjust_ptr_min_max_vals()` 来处理指针与标量相加（或反之亦然），以及调用 `adjust_scalar_min_max_vals()` 来处理两个标量的操作。
最终结果是 BPF 程序编写者可以直接使用标准的 C 代码来访问数据包，如下面所示：

  void *data = (void *)(long)skb->data;
  void *data_end = (void *)(long)skb->data_end;
  struct eth_hdr *eth = data;
  struct iphdr *iph = data + sizeof(*eth);
  struct udphdr *udp = data + sizeof(*eth) + sizeof(*iph);

  if (data + sizeof(*eth) + sizeof(*iph) + sizeof(*udp) > data_end)
      return 0;
  if (eth->h_proto != htons(ETH_P_IP))
      return 0;
  if (iph->protocol != IPPROTO_UDP || iph->ihl != 5)
      return 0;
  if (udp->dest == 53 || udp->source == 9)
      ...;

这种方式使得编写此类程序比使用 LD_ABS 指令更容易，而且显著更快。

### 剪枝

验证器实际上并不会遍历程序中的所有可能路径。对于每个新的分支进行分析时，验证器会查看之前在该指令时的所有状态。如果其中任何一个状态包含当前状态的子集，则该分支被“剪枝”——也就是说，由于先前的状态已经被接受，这意味着当前的状态也会被接受。例如，如果在先前的状态中 r1 持有一个数据包指针，而在当前状态中 r1 也持有相同或更长范围的数据包指针，并且具有至少同样严格的对齐，则 r1 是安全的。同样地，如果 r2 在之前的状态中为 NOT_INIT，则从那个点开始它不可能被任何路径使用，因此 r2 中的任何值（包括另一个 NOT_INIT）都是安全的。实现这一点的函数是 `regsafe()`。
剪枝不仅考虑寄存器，还考虑栈（以及栈中可能持有的任何溢出寄存器）。所有这些都必须是安全的才能剪枝该分支。
这是在 `states_equal()` 中实现的。
关于状态剪枝实现的一些技术细节可以在下面找到：
注册存活状态追踪
-------------------

为了使状态剪枝有效，每个寄存器和栈槽的存活状态都会被追踪。基本思想是追踪哪些寄存器和栈槽在程序后续执行直至程序退出的过程中实际被使用。从未被使用的寄存器和栈槽可以从缓存的状态中移除，这样就可以使更多的状态与已缓存的状态等效。这一点可以通过以下程序来说明：

  0: 调用 bpf_get_prandom_u32()
  1: r1 = 0
  2: 如果 r0 == 0 跳转至 +1
  3: r0 = 1
  --- 检查点 ---
  4: r0 = r1
  5: 退出

假设在指令 #4 处创建了一个状态缓存条目（这样的条目也被称为“检查点”）。验证器可以带着两种可能的寄存器状态到达该指令：

* r0 = 1, r1 = 0
* r0 = 0, r1 = 0

然而，只有寄存器 `r1` 的值对于成功完成验证至关重要。存活追踪算法的目标就是识别出这一事实，并确定这两种状态实际上是等效的。
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

  struct bpf_reg_state {
 	..
struct bpf_reg_state *parent;
 	..
enum bpf_reg_liveness live;
 	..
};

  struct bpf_stack_state {
	struct bpf_reg_state spilled_ptr;
	..
};

  struct bpf_func_state {
	struct bpf_reg_state regs[MAX_BPF_REG];
        ..
struct bpf_stack_state *stack;
  }

  struct bpf_verifier_state {
	struct bpf_func_state *frame[MAX_CALL_FRAMES];
	struct bpf_verifier_state *parent;
        ..
}
```

* `REG_LIVE_NONE` 是在创建新的验证状态时为 `->live` 字段分配的初始值；

* `REG_LIVE_WRITTEN` 表示某个寄存器（或栈槽）的值由当前验证状态的父状态与该验证状态之间的某条指令定义；

* `REG_LIVE_READ{32,64}` 表示某个寄存器（或栈槽）的值被此验证状态的一个子状态读取；

* `REG_LIVE_DONE` 是一个标记，用于 `clean_verifier_state()` 避免多次处理同一个验证状态，并用于某些合理性检查；

* `->live` 字段的值是通过位或操作组合 `enum bpf_reg_liveness` 的值形成的。
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

对于每个处理过的指令，验证器都会追踪读取和写入的寄存器及栈槽。该算法的主要思想是：读取标记沿状态父链反向传播，直到遇到写入标记，后者“屏蔽”了更早的状态不受读取影响。关于读取的信息是由`mark_reg_read()`函数传播的，可以总结如下：

  mark_reg_read(struct bpf_reg_state *state, ...):
      parent = state->parent
      while parent:
          if state->live & REG_LIVE_WRITTEN:
              break
          if parent->live & REG_LIVE_READ64:
              break
          parent->live |= REG_LIVE_READ64
          state = parent
          parent = state->parent

注解：

* 读取标记应用于**父**状态，而写入标记应用于**当前**状态。寄存器或栈槽上的写入标记意味着它被某个指令更新，该指令位于从父状态到当前状态的直线代码中。
* 关于REG_LIVE_READ32的详细信息被省略。
* 函数`propagate_liveness()`（参见 :ref:`read_marks_for_cache_hits` 部分）可能会覆盖第一个父链接。请参阅`propagate_liveness()`和`mark_reg_read()`源代码中的注释以获取更多详细信息。
由于栈写入可能有不同的大小，`REG_LIVE_WRITTEN`标记保守地应用：只有当写入大小与寄存器大小相对应时，栈槽才被标记为已写入，例如参见`save_register_state()`函数。
如上所述，考虑以下示例：

  0: (*u64)(r10 - 8) = 0   ; 定义8字节的fp-8
  --- 检查点 #0 ---
  1: (*u32)(r10 - 8) = 1   ; 重新定义低4字节
  2: r1 = (*u32)(r10 - 8)  ; 读取在(1)处定义的低4字节
  3: r2 = (*u32)(r10 - 4)  ; 读取在(0)处定义的高4字节

如上所述，在(1)处的写入不被视为“REG_LIVE_WRITTEN”。如果情况相反，则上述算法将无法从(3)传播读取标记到检查点#0。
一旦到达“BPF_EXIT”指令，“update_branch_counts()”函数会被调用以更新每个父级验证状态链中“->branches”的计数器。当“->branches”计数器达到零时，该验证状态变为缓存验证状态集中的有效条目。
缓存中的每个验证状态条目都由函数“clean_live_states()”进行后处理。此函数会将所有没有“REG_LIVE_READ{32,64}”标记的寄存器和栈槽标记为“NOT_INIT”或“STACK_INVALID”。
以这种方式标记的寄存器/栈槽在从“states_equal()”调用的“stacksafe()”函数中被忽略，当考虑将缓存条目与当前状态等价时。
现在可以解释本节开头的例子是如何工作的：

  0: 调用 bpf_get_prandom_u32()
  1: r1 = 0
  2: 如果 r0 == 0 则跳转 +1
  3: r0 = 1
  --- 检查点[0] ---
  4: r0 = r1
  5: 退出

* 在指令#2处达到分支点，并将状态`{ r0 == 0, r1 == 0, pc == 4 }`推送到状态处理队列（pc代表程序计数器）
* 在指令#4处：

  * 创建“检查点[0]”的状态缓存条目：`{ r0 == 1, r1 == 0, pc == 4 }`;
  * “检查点[0].r0”被标记为已写入；
  * “检查点[0].r1”被标记为已读取；

* 在指令#5处达到退出点，“检查点[0]”现在可以被“clean_live_states()”处理。经过此处理后，“检查点[0].r1”具有读取标记，而所有其他寄存器和栈槽都被标记为“NOT_INIT”或“STACK_INVALID”。

* 状态`{ r0 == 0, r1 == 0, pc == 4 }`从状态队列中弹出，并与缓存状态`{ r1 == 0, pc == 4 }`进行比较，这两个状态被认为是等价的。
.. _read_marks_for_cache_hits:

缓存命中时读取标记的传播
~~~~~~~~~~~~~~~~~~~~~~~~~~

另一个要点是在找到之前已验证的状态时如何处理读取标记。在缓存命中时，验证器必须像当前状态已被验证到程序退出那样行为。这意味着缓存状态中的所有寄存器和栈槽上的读取标记必须沿着当前状态的父级链传播。下面的例子展示了这一点的重要性。“propagate_liveness()”函数处理这种情况。
考虑以下状态父级链（S是初始状态，A-E是派生状态，->箭头表示哪个状态是从哪个状态派生而来）：

                   r1 读取
            <-------------                A[r1] == 0
                                          C[r1] == 0
      S ---> A ---> B ---> 退出           E[r1] == 1
      |
      ` ---> C ---> D
      |
      ` ---> E      ^
                    |___   假设所有这些
             ^           状态都在指令#Y处
             |
      假设所有这些
    状态都在指令#X处

* 验证状态链“S -> A -> B -> 退出”首先进行
* 当验证“B -> 退出”时，寄存器“r1”被读取，并且此读取标记被传播到状态“A”
* 当验证状态链“C -> D”时，发现状态“D”与状态“B”等价
* 对于 `r1` 的读取标记必须传播到状态 `C`，否则状态 `C` 可能被错误地标记为与状态 `E` 等价，尽管寄存器 `r1` 在 `C` 和 `E` 之间有不同的值。
理解 eBPF 验证器的消息
====================================

以下是几个无效的 eBPF 程序及其在日志中显示的验证器错误消息示例：

含有不可达指令的程序::

  static struct bpf_insn prog[] = {
  BPF_EXIT_INSN(),
  BPF_EXIT_INSN(),
  };

错误::

  不可达的指令 1

读取未初始化寄存器的程序::

  BPF_MOV64_REG(BPF_REG_0, BPF_REG_2),
  BPF_EXIT_INSN(),

错误::

  0: (bf) r0 = r2
  R2 未正确读取

退出前未初始化 R0 的程序::

  BPF_MOV64_REG(BPF_REG_2, BPF_REG_1),
  BPF_EXIT_INSN(),

错误::

  0: (bf) r2 = r1
  1: (95) exit
  R0 未正确读取

访问超出栈界限的程序::

  BPF_ST_MEM(BPF_DW, BPF_REG_10, 8, 0),
  BPF_EXIT_INSN(),

错误::

  0: (7a) *(u64 *)(r10 +8) = 0
  栈访问越界 off=8 size=8

调用函数前未初始化栈的程序::

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
  从栈间接读取时栈访问越界 off -8+0 size 8

调用 map_lookup_elem() 函数时使用无效的 map_fd=0 的程序::

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
  文件描述符 0 没有指向有效的 bpf_map

在访问映射元素之前没有检查 map_lookup_elem() 返回值的程序::

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
  R0 无效内存访问 'map_value_or_null'

正确检查了 map_lookup_elem() 返回值是否为 NULL，但以不正确的对齐方式访问内存的程序::

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
  5: (15) 如果 r0 == 0x0 则跳转到 pc+1
   R0=map_ptr R10=fp
  6: (7a) *(u64 *)(r0 +4) = 0
  访问错位 off 4 size 8

在 'if' 分支的一侧正确检查了 map_lookup_elem() 返回值是否为 NULL 并且以正确的对齐方式访问内存，但在另一侧分支未能这样做的程序::

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
  5: (15) 如果 r0 == 0x0 则跳转到 pc+2
   R0=map_ptr R10=fp
  6: (7a) *(u64 *)(r0 +0) = 0
  7: (95) exit

  从 5 到 8: R0=imm0 R10=fp
  8: (7a) *(u64 *)(r0 +0) = 1
  R0 无效内存访问 'imm'

执行套接字查找然后将指针设置为 NULL 而未进行检查的程序::

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
  1: (63) *(u32 *)(r10 -8) = r2
  2: (bf) r2 = r10
  3: (07) r2 += -8
  4: (b7) r3 = 4
  5: (b7) r4 = 0
  6: (b7) r5 = 0
  7: (85) call bpf_sk_lookup_tcp#65
  8: (b7) r0 = 0
  9: (95) exit
  未释放的引用 id=1, alloc_insn=7

执行套接字查找但未对返回值进行 NULL 检查的程序::

  BPF_MOV64_IMM(BPF_REG_2, 0),
  BPF_STX_MEM(BPF_W, BPF_REG_10, BPF_REG_2, -8),
  BPF_MOV64_REG(BPF_REG_2, BPF_REG_10),
  BPF_ALU64_IMM(BPF_ADD, BPF_REG_2, -8),
  BPF_MOV64_IMM(BPF_REG_3, 4),
  BPF_MOV64_IMM(BPF_REG_4, 0),
  BPF_MOV64_IMM(BPF_REG_5, 0),
  BPF_EMIT_CALL(BPF_FUNC_sk_lookup_tcp),
  BPF_EXIT_INSN(),

错误::

  0: (b7) r2 = 0
  1: (63) *(u32 *)(r10 -8) = r2
  2: (bf) r2 = r10
  3: (07) r2 += -8
  4: (b7) r3 = 4
  5: (b7) r4 = 0
  6: (b7) r5 = 0
  7: (85) call bpf_sk_lookup_tcp#65
  8: (95) exit
  未释放的引用 id=1, alloc_insn=7
