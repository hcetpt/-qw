============= 
eBPF 验证器
=============

eBPF 程序的安全性通过两个步骤来确定：

第一步是执行有向无环图 (DAG) 检查以禁止循环和其他控制流图 (CFG) 的验证。特别是，它会检测出包含不可达指令的程序（尽管传统的 BPF 检查器允许这类指令存在）。

第二步从第一条指令开始，遍历所有可能的路径。它模拟每条指令的执行，并观察寄存器和栈的状态变化。在程序开始时，寄存器 R1 包含指向上下文的指针，并具有类型 PTR_TO_CTX。如果验证器看到一条如 R2=R1 的指令，则 R2 现在也具有 PTR_TO_CTX 类型，并且可以在表达式的右侧使用。如果 R1=PTR_TO_CTX 且指令为 R2=R1+R1，则 R2=SCALAR_VALUE，因为两个有效指针相加的结果是一个无效的指针（在“安全”模式下，验证器将拒绝任何形式的指针算术操作，以确保内核地址不会泄露给非特权用户）。

如果某个寄存器从未被写入，那么它是不可读的：

例如：
```
bpf_mov R0 = R2
bpf_exit
```

这样的程序会被拒绝，因为在程序开始时 R2 是不可读的。
在内核函数调用之后，R1 至 R5 会被重置为不可读状态，而 R0 则会包含函数的返回值类型。
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
通过一个回调函数可以定制验证器，以限制eBPF程序仅能访问ctx结构体中的某些字段，并且这些字段需要具有指定的大小和对齐方式。
例如，以下指令：
```assembly
bpf_ld R0 = *(u32 *)(R6 + 8)
```
意图是从地址R6 + 8处加载一个单词并将其存储到R0中。
如果R6为PTR_TO_CTX类型，那么通过`is_valid_access()`回调函数，验证器会知道偏移量8处的4字节可以被读取，否则验证器将拒绝该程序。
如果R6为PTR_TO_STACK类型，那么访问必须是对齐的并且位于栈界限[-MAX_BPF_STACK, 0)之内。在这个例子中，偏移量是8，因此它将无法通过验证，因为它超出了界限。
验证器只允许eBPF程序从栈中读取数据，前提是它之前已经写入了数据。
经典的BPF验证器对M[0-15]内存槽进行了类似的检查。
例如：
```assembly
bpf_ld R0 = *(u32 *)(R10 - 4)
bpf_exit
```
这是一个无效的程序。
虽然 R10 是正确的只读寄存器，且类型为栈指针（PTR_TO_STACK），并且 R10 - 4 也在栈的边界内，但并没有对该位置进行存储操作。
同时跟踪了指针寄存器的溢出和填充，因为四个（R6-R9）被调用者保存的寄存器可能对于某些程序来说不够用。
允许的函数调用通过 `bpf_verifier_ops->get_func_proto()` 进行定制。
eBPF 验证器会检查寄存器是否符合参数约束。
函数调用后，寄存器 R0 将被设置为该函数的返回类型。
函数调用是扩展 eBPF 程序功能的主要机制。
例如，套接字过滤器可以允许程序调用一组特定的函数，而追踪过滤器则可能允许完全不同的函数集。
如果一个函数被赋予 eBPF 程序访问权限，那么从安全角度来看需要仔细考虑。验证器将保证函数被有效参数调用。
对于传统 BPF，seccomp 和套接字过滤器有不同的安全限制。
seccomp 通过两阶段验证解决这个问题：首先是传统 BPF 验证器，然后是 seccomp 验证器。而在 eBPF 的情况下，一个可配置的验证器被用于所有使用场景。
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
然而，指针可能相对于这个基址有所偏移（由于指针运算的结果），并且这种偏移被分为两部分进行跟踪：'固定偏移'和'变量偏移'。前者用于当一个确切已知的值（例如，立即数操作数）被加到指针上时的情况，而后者用于那些不确切已知的值。变量偏移还用于SCALAR_VALUE中，以跟踪寄存器中可能值的范围。
验证器对于变量偏移的了解包括：

* 无符号的最小值和最大值
* 带符号的最小值和最大值

* 对各个位的值的了解，形式为'tnum'：一个u64 '掩码'和一个u64 '值'。掩码中的1代表未知值的位；值中的1代表已知为1的位。已知为0的位在掩码和值中都为0；没有位应该同时为1。例如，如果从内存读取一个字节到寄存器中，那么该寄存器的高56位是已知为0的，而低8位是未知的——这表示为tnum (0x0; 0xff)。如果我们再与0x40做或运算，我们得到(0x40; 0xbf)，然后如果我们加上1，我们得到(0x0; 0x1ff)，这是因为可能存在的进位。
除了算术运算外，寄存器的状态也可以通过条件分支来更新。例如，如果一个SCALAR_VALUE与8进行比较大于8，在'True'分支中它的无符号最小值将是9，而在'False'分支中它的无符号最大值将是8。带符号的比较（使用BPF_JSGT或BPF_JSGE）将更新带符号的最小值和最大值。来自带符号和无符号边界的信息可以组合起来；例如，如果一个值首先被测试小于8，然后被测试带符号大于4，验证器将得出结论该值也大于4且带符号小于8，因为边界阻止了跨越符号界限。
带有变量偏移部分的PTR_TO_PACKET有一个'id'，这是所有共享相同变量偏移的指针所共有的。这对于包范围检查非常重要：在向包指针寄存器A添加一个变量后，如果你复制它到另一个寄存器B，然后给A加上常量4，两个寄存器将共享同一个'id'，但A将有一个固定偏移+4。然后如果A经过边界检查并且发现小于PTR_TO_PACKET_END，寄存器B现在已知至少有4个字节的安全范围。关于PTR_TO_PACKET范围的更多信息，请参见下面的“直接包访问”。
'id'字段也用于PTR_TO_MAP_VALUE_OR_NULL上，对于所有从映射查找返回的指针的副本都是通用的。这意味着当一个副本被检查并发现不是NULL时，所有副本都可以变成PTR_TO_MAP_VALUE。
除了范围检查之外，跟踪的信息还用于强制指针访问的对齐。例如，在大多数系统上，包指针是在4字节对齐后的2字节处。如果程序向其添加14个字节以跳过以太网头，然后读取IHL并加上(IHL * 4)，那么结果指针将有一个变量偏移，已知为4n+2的形式（其中n为某个值），因此加上2字节（NET_IP_ALIGN）就可以得到4字节对齐，从而通过该指针进行的字大小的访问是安全的。
'id'字段同样用于PTR_TO_SOCKET和PTR_TO_SOCKET_OR_NULL，对于所有从套接字查找返回的指针副本都是通用的。这与处理PTR_TO_MAP_VALUE_OR_NULL到PTR_TO_MAP_VALUE的行为类似，但它还包括了对指针的引用跟踪。PTR_TO_SOCKET隐式地表示对相应的`struct sock`的一个引用。为了确保不会泄露这个引用，必须检查该引用是否为NULL，并且在非NULL的情况下，将有效引用传递给套接字释放函数。
直接包访问
=============

在cls_bpf和act_bpf程序中，验证器允许通过skb->data和skb->data_end指针直接访问包数据。
例如：

    1:  r4 = *(u32 *)(r1 +80)  /* 加载 skb->data_end */
    2:  r3 = *(u32 *)(r1 +76)  /* 加载 skb->data */
    3:  r5 = r3
    4:  r5 += 14
    5:  if r5 > r4 goto pc+16
    R1=ctx R3=pkt(id=0,off=0,r=14) R4=pkt_end R5=pkt(id=0,off=14,r=14) R10=fp
    6:  r0 = *(u16 *)(r3 +12) /* 访问包的第12和13个字节 */

从包中进行的这2字节加载是安全的，因为程序作者在指令#5处进行了检查``if (skb->data + 14 > skb->data_end) goto err``，这意味着在继续执行的情况下，寄存器R3（指向skb->data）至少有14个可以直接访问的字节。验证器将其标记为R3=pkt(id=0,off=0,r=14)
id=0意味着没有额外的变量被加到该寄存器上。
翻译为中文：

`off=0` 表示没有添加额外的常量。
`r=14` 是安全访问的范围，意味着 `[R3, R3 + 14)` 这段字节是可访问的。
请注意，R5 被标记为 `R5=pkt(id=0,off=14,r=14)`。它也指向数据包的数据，但由于向寄存器中添加了常量 14，因此现在指向 `skb->data + 14`，并且可访问的范围是 `[R5, R5 + 14 - 14)`，即零字节。
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
    18:  如果 r2 > r1 则跳转到 pc+2
    R0=inv(id=0,umax_value=255,var_off=(0x0; 0xff)) R1=pkt_end R2=pkt(id=2,off=8,r=8) R3=pkt(id=2,off=0,r=8) R4=inv(id=0,umax_value=3570,var_off=(0x0; 0xfffe)) R5=pkt(id=0,off=14,r=14) R10=fp
    19:  r1 = *(u8 *)(r3 +4)

寄存器 R3 的状态为 R3=pkt(id=2,off=0,r=8)
`id=2` 表示观察到了两个 `r3 += rX` 指令，所以 r3 指向数据包内的某个偏移量，并且由于程序作者在指令 #18 中做了 `如果 (r3 + 8 > r1) 则跳转到 err`，安全范围是 `[R3, R3 + 8)`。
验证器仅允许对数据包寄存器进行 '加'/'减' 操作。任何其他操作都会将寄存器状态设置为 'SCALAR_VALUE' 并且无法直接用于数据包访问。
`r3 += rX` 可能会导致溢出并变得小于原始的 `skb->data`，因此验证器必须防止这种情况发生。因此当它看到 `r3 += rX` 指令并且 rX 大于 16 位值时，任何后续对 r3 和 `skb->data_end` 的边界检查都不会给出“范围”信息，试图通过该指针读取数据将会得到“无效访问数据包”的错误。
例如，在指令 `r4 = *(u8 *)(r3 +12)`（如上所述的指令 #7）之后，r4 的状态为 R4=inv(id=0,umax_value=255,var_off=(0x0; 0xff))，这意味着寄存器的高 56 位保证为零，并且关于低 8 位的信息未知。在执行指令 `r4 *= 14` 之后，状态变为 R4=inv(id=0,umax_value=3570,var_off=(0x0; 0xfffe))，因为将一个 8 位值乘以常数 14 将保持高 52 位为零，同时最低有效位也将为零，因为 14 是偶数。同样地，`r2 >>= 48` 将使 R2=inv(id=0,umax_value=65535,var_off=(0x0; 0xffff))，因为移位不扩展符号。这种逻辑实现在 `adjust_reg_min_max_vals()` 函数中，该函数调用 `adjust_ptr_min_max_vals()` 来处理指针与标量的加法（或反之亦然），以及 `adjust_scalar_min_max_vals()` 来处理两个标量的操作。
最终结果是 BPF 程序作者可以使用标准 C 代码直接访问数据包，如下所示：

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

这使得此类程序比使用 LD_ABS 指令更容易编写，并且显著更快。
剪枝
=====

验证器实际上并不会遍历程序中的所有可能路径。对于每个新分支的分析，验证器会查看之前在这一指令上所处的所有状态。如果其中任何一个状态包含了当前状态的一个子集，则该分支被“剪枝”，也就是说，先前状态被认为是安全的这一事实意味着当前状态也是安全的。例如，如果在先前状态下 r1 包含一个数据包指针，并且在当前状态下 r1 同样包含一个至少具有相同严格对齐要求、长度相等或更长的数据包指针，则 r1 是安全的。类似地，如果 r2 在先前状态下为 NOT_INIT，则从那一点开始的任何路径都不可能使用 r2，因此 r2 中的任何值（包括另一个 NOT_INIT）都是安全的。实现位于 `regsafe()` 函数中。
剪枝不仅考虑寄存器，还考虑堆栈（及其可能持有的任何溢出寄存器）。所有这些都必须是安全的才能剪枝。
这是在 `states_equal()` 中实现的。
关于状态剪枝实现的一些技术细节可以在下面找到：
注册存活状态追踪
-------------------

为了使状态剪枝有效，每个寄存器和栈槽的存活状态都会被追踪。基本思想是追踪哪些寄存器和栈槽在程序后续执行直至程序退出时实际被使用。从未被使用的寄存器和栈槽可以从缓存的状态中移除，从而使得更多的状态与已缓存的状态等效。这一点可以通过以下程序来说明：

  0: 调用 bpf_get_prandom_u32()
  1: r1 = 0
  2: 如果 r0 == 0 则跳转至 +1
  3: r0 = 1
  --- 检查点 ---
  4: r0 = r1
  5: 退出

假设在指令 #4 创建了一个状态缓存条目（这些条目在下面的文字中也被称为“检查点”）。验证器可以带着两种可能的寄存器状态到达该指令：

* r0 = 1, r1 = 0
* r0 = 0, r1 = 0

然而，只有寄存器 `r1` 的值对于成功完成验证是重要的。存活追踪算法的目标就是发现这一事实，并确定这两种状态实际上是等效的。
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

* `REG_LIVE_NONE` 是在创建新的验证状态时分配给 `->live` 字段的初始值；

* `REG_LIVE_WRITTEN` 表示寄存器（或栈槽）的值由当前验证状态的父状态与该验证状态之间的某条指令定义；

* `REG_LIVE_READ{32,64}` 表示寄存器（或栈槽）的值由该验证状态的某个子状态读取；

* `REG_LIVE_DONE` 是一个标记，用于 `clean_verifier_state()` 避免多次处理相同的验证状态，并用于某些合理性检查；

* `->live` 字段的值是通过位或操作组合 `enum bpf_reg_liveness` 值形成的。
为了在父状态和子状态之间传播信息，会建立一个*注册父链*。每个寄存器或栈槽都通过一个`->parent`指针链接到其父状态中的相应寄存器或栈槽。这种链接在`is_state_visited()`中创建状态时建立，并且可能由从`__check_func_call()`调用的`set_callee_state()`修改。寄存器/栈槽之间的对应规则如下：

* 对于当前栈帧，新状态中的寄存器和栈槽与具有相同索引的父状态中的寄存器和栈槽相连。
* 对于外部栈帧，只有保存者的寄存器（r6-r9）和栈槽与具有相同索引的父状态中的寄存器和栈槽相连。
* 当处理函数调用时，分配一个新的`struct bpf_func_state`实例，它封装了一组新的寄存器和栈槽。对于这个新帧，r6-r9和栈槽的父链接设置为nil，而r1-r5的父链接则设置为匹配调用者r1-r5的父链接。

这可以通过以下图表来说明（箭头代表`->parent`指针）：

```
...                    ; 帧#0，某些指令
--- 检查点 #0 ---
1 : r6 = 42                ; 帧#0
--- 检查点 #1 ---
2 : 调用 foo()             ; 帧#0
      ...                    ; 帧#1，来自foo()的指令
--- 检查点 #2 ---
      ...                    ; 帧#1，来自foo()的指令
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
                               r6读取标记通过这些链接一直传播到检查点#1
                               检查点#1包含对r6的写入标记
                               因为指令(1)，因此读取传播不会到达检查点#0（参见下面的章节）
```

活跃性标记追踪
~~~~~~~~~~~~~~~~~~~~~~~

对于每个处理过的指令，验证器跟踪读取和写入的寄存器及栈槽。算法的主要思想是读取标记沿状态父链向后传播，直到遇到写入标记为止，该写入标记“屏蔽”了之前的读取。关于读取的信息由`mark_reg_read()`函数传播，该函数可以总结如下：

```
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
```

注意事项：

* 读取标记应用于**父**状态，而写入标记应用于**当前**状态。寄存器或栈槽上的写入标记意味着它被从父状态到当前状态的直线代码中的某个指令更新。
* 关于REG_LIVE_READ32的详细信息被省略。
* 函数`propagate_liveness()`（参见：:ref:`read_marks_for_cache_hits`节）可能会覆盖第一个父链接。请参阅`propagate_liveness()`和`mark_reg_read()`源代码中的注释以获取更多细节。
由于栈写入可能有不同的大小，`REG_LIVE_WRITTEN`标记保守地应用：仅当写入大小与寄存器大小相对应时，栈槽才被标记为已写入，例如参见`save_register_state()`函数。
如上所述，考虑以下示例：

  0: (*u64)(r10 - 8) = 0   ; 定义8字节的fp-8
  --- 检查点 #0 ---
  1: (*u32)(r10 - 8) = 1   ; 重新定义较低的4字节
  2: r1 = (*u32)(r10 - 8)  ; 读取在(1)处定义的较低4字节
  3: r2 = (*u32)(r10 - 4)  ; 读取在(0)处定义的较高4字节

如上所述，在(1)处的写入不被视为“REG_LIVE_WRITTEN”。如果否则的话，上述算法将无法从(3)传播读取标记到检查点#0。
一旦达到“BPF_EXIT”指令，“update_branch_counts()”函数被调用以更新每个验证器状态链中验证器状态的“->branches”计数。当“->branches”计数变为零时，该验证器状态就成为缓存的验证器状态集合中的有效条目。
缓存中的每个验证器状态条目都由函数“clean_live_states()”进行后处理。此函数将所有没有“REG_LIVE_READ{32,64}”标记的寄存器和栈槽标记为“NOT_INIT”或“STACK_INVALID”。
这样标记的寄存器/栈槽在从“states_equal()”调用的“stacksafe()”函数中被忽略，当考虑一个状态缓存条目与当前状态等价时。
现在可以解释本节开始的例子是如何工作的：

  0: 调用bpf_get_prandom_u32()
  1: r1 = 0
  2: 如果r0 == 0则跳转+1
  3: r0 = 1
  --- 检查点[0] ---
  4: r0 = r1
  5: 退出

* 在指令#2处到达分支点，并将状态`{ r0 == 0, r1 == 0, pc == 4 }`推送到状态处理队列（pc代表程序计数器）
* 在指令#4处：

  * 创建“检查点[0]”的状态缓存条目：`{ r0 == 1, r1 == 0, pc == 4 }`；
  * “检查点[0].r0”被标记为已写入；
  * “检查点[0].r1”被标记为已读取；

* 在指令#5处到达退出，并且现在可以由“clean_live_states()”处理“检查点[0]”。经过这个处理后，“检查点[0].r1”有一个读取标记，而其他所有寄存器和栈槽都被标记为“NOT_INIT”或“STACK_INVALID”。

* 状态`{ r0 == 0, r1 == 0, pc == 4 }`从状态队列弹出并与缓存状态`{ r1 == 0, pc == 4 }`进行比较，这些状态被认为等价。
.. _read_marks_for_cache_hits:

对于缓存命中时读取标记的传播
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

另一个要点是在找到之前已验证的状态时如何处理读取标记。在缓存命中时，验证器必须表现得如同当前状态已经验证到了程序退出一样。这意味着必须将缓存状态中的所有读取标记沿当前状态的父级链向上传播。下面的示例展示了为什么这是重要的。“propagate_liveness()”函数处理这种情况。
考虑以下状态的父级链（S是起始状态，A-E是派生状态，->箭头表示哪个状态是从哪个状态派生的）：

                   r1 读取
            <-------------                A[r1] == 0
                                          C[r1] == 0
      S ---> A ---> B ---> 退出           E[r1] == 1
      |
      ` ---> C ---> D
      |
      ` ---> E      ^
                    |___   假设所有这些
             ^           状态都在insn #Y
             |
      假设所有这些
    状态都在insn #X

* 首先验证状态链`S -> A -> B -> 退出`
* 当验证`B -> 退出`时，寄存器`r1`被读取，此读取标记被向上传播至状态`A`
* 当验证状态链`C -> D`时，发现状态`D`与状态`B`等价
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

  不可达指令 1

读取未初始化寄存器的程序::

  BPF_MOV64_REG(BPF_REG_0, BPF_REG_2),
  BPF_EXIT_INSN(),

错误::

  0: (bf) r0 = r2
  R2 未正确读取

在退出前未初始化 R0 的程序::

  BPF_MOV64_REG(BPF_REG_2, BPF_REG_1),
  BPF_EXIT_INSN(),

错误::

  0: (bf) r2 = r1
  1: (95) exit
  R0 未正确读取

访问超出堆栈范围的程序::

    BPF_ST_MEM(BPF_DW, BPF_REG_10, 8, 0),
    BPF_EXIT_INSN(),

错误::

    0: (7a) *(u64 *)(r10 +8) = 0
    堆栈偏移越界 off=8 size=8

在传递其地址给函数之前未初始化堆栈的程序::

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
  从堆栈间接读取越界 off -8+0 size 8

调用 map_lookup_elem() 函数时使用了无效的 map_fd=0 的程序::

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

在访问映射元素前未检查 map_lookup_elem() 返回值的程序::

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
  R0 无效的内存访问 'map_value_or_null'

正确检查 map_lookup_elem() 返回值是否为 NULL，但以不正确的对齐方式访问内存的程序::

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
   R0=映射指针 R10=帧指针
  6: (7a) *(u64 *)(r0 +4) = 0
  访问不对齐 off 4 size 8

正确检查 map_lookup_elem() 返回值是否为 NULL 并在一侧的 'if' 分支中以正确的对齐方式访问内存，但在另一侧的 'if' 分支中未能做到这一点的程序::

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
   R0=映射指针 R10=帧指针
  6: (7a) *(u64 *)(r0 +0) = 0
  7: (95) exit

  从 5 到 8: R0=常量0 R10=帧指针
  8: (7a) *(u64 *)(r0 +0) = 1
  R0 无效的内存访问 '常量'

执行套接字查找然后设置指针为 NULL 而未进行检查的程序::

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
  未释放引用 id=1, alloc_insn=7

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
  未释放引用 id=1, alloc_insn=7
