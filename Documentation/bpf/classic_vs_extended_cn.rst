经典BPF与eBPF
=============

eBPF设计为具有1:1映射的即时编译（JIT），这也可以为GCC/LLVM编译器通过eBPF后端生成优化的eBPF代码打开可能性，其运行速度几乎与本地编译的代码一样快。从经典BPF到eBPF格式的一些核心变化包括：

- 寄存器数量从2个增加到10个：

  旧格式有A和X两个寄存器，以及一个隐藏的帧指针。新布局将此扩展为10个内部寄存器和一个只读帧指针。由于64位CPU通过寄存器传递函数参数，eBPF程序到内核函数的参数数量被限制为5个，并且一个寄存器用于接收来自内核函数的返回值。本地情况下，x86_64通过寄存器传递前6个参数；aarch64/sparcv9/mips64有7至8个寄存器用于参数；x86_64有6个被调用者保存的寄存器，而aarch64/sparcv9/mips64有11个或更多被调用者保存的寄存器。因此，在x86_64、aarch64等架构上，所有eBPF寄存器与硬件寄存器一一对应，eBPF调用约定直接映射到64位架构上内核使用的ABI。
在32位架构上，即时编译器可能仅映射使用32位算术的程序，并允许更复杂的程序被解释执行。
R0至R5是临时寄存器，如果需要，eBPF程序在调用之间必须进行寄存器的溢出和填充。需要注意的是，只有一个eBPF程序（即一个eBPF主例程），它不能调用其他eBPF函数，只能调用预定义的内核函数。
- 寄存器宽度从32位增加到64位：

  尽管如此，原始32位ALU操作的语义通过32位子寄存器得以保留。所有eBPF寄存器都是64位的，带有零扩展到64位的32位低位子寄存器，当它们被写入时。
这种行为直接映射到x86_64和arm64的子寄存器定义，但使得其他即时编译器更加困难。
32位架构通过解释器运行64位eBPF程序。
它们的即时编译器可能会将仅使用32位子寄存器的BPF程序转换为本机指令集，并让其余部分被解释执行。
操作是64位的，因为在64位架构上，指针也是64位宽，我们希望在内核函数中传入传出64位值，因此32位eBPF寄存器否则需要定义寄存器对ABI，因此，无法直接使用eBPF寄存器到硬件寄存器的映射，即时编译器将需要对每个寄存器进出函数进行组合/拆分/移动操作，这既复杂又容易出错且速度慢。
另一个原因是使用了原子的64位计数器。
- 将条件jt/jf目标替换为jt/穿透：

  原始设计中有如 ``if (cond) 跳转真; 否则 跳转假;`` 这样的结构，它们正在被替换成类似 ``if (cond) 跳转真; /* 否则 穿透 */`` 的替代结构，
- 引入了bpf_call指令和寄存器传递约定，用于零开销调用其他内核函数：

  在内核函数调用之前，eBPF程序需要将函数参数放入R1到R5寄存器以满足调用约定，然后解释器将从寄存器中取出这些参数并传递给内核函数。如果R1 - R5寄存器映射到在给定架构上用于参数传递的CPU寄存器，JIT编译器不需要发出额外的移动指令。函数参数将位于正确的寄存器中，而BPF_CALL指令将被JIT编译为单个'call'硬件指令。选择这种调用约定是为了在没有性能损失的情况下覆盖常见的调用情况。
在内核函数调用之后，R1 - R5将重置为不可读状态，而R0包含函数的返回值。由于R6 - R9是调用者保存的，它们的状态在调用期间得以保留。
例如，考虑三个C函数::

    u64 f1() { return (*_f2)(1); }
    u64 f2(u64 a) { return f3(a + 1, a); }
    u64 f3(u64 a, u64 b) { return a - b; }

GCC可以将f1、f3编译为x86_64::

    f1:
	movl $1, %edi
	movq _f2(%rip), %rax
	jmp  *%rax
    f3:
	movq %rdi, %rax
	subq %rsi, %rax
	ret

eBPF中的函数f2可能看起来像这样::

    f2:
	bpf_mov R2, R1
	bpf_add R1, 1
	bpf_call f3
	bpf_exit

如果f2被JIT编译且指针存储在``_f2``中，那么从f1到f2再到f3的调用和返回将是无缝的。如果没有JIT，__bpf_prog_run()解释器需要用来调用f2
出于实际原因，所有eBPF程序只有一个参数'ctx'，它已经放置在R1（例如，在__bpf_prog_run()启动时）中，并且程序可以调用最多具有5个参数的内核函数。目前不支持带有6个或更多参数的调用，但将来如果必要，这些限制可以解除。
在64位架构上，所有寄存器一对一映射到硬件寄存器。例如，x86_64 JIT编译器可以将它们映射为..
::

    R0 - rax
    R1 - rdi
    R2 - rsi
    R3 - rdx
    R4 - rcx
    R5 - r8
    R6 - rbx
    R7 - r13
    R8 - r14
    R9 - r15
    R10 - rbp

...因为x86_64 ABI规定rdi、rsi、rdx、rcx、r8、r9用于参数传递，而rbx、r12 - r15是调用者保存的。
然后以下eBPF伪程序::

    bpf_mov R6, R1 /* 保存ctx */
    bpf_mov R2, 2
    bpf_mov R3, 3
    bpf_mov R4, 4
    bpf_mov R5, 5
    bpf_call foo
    bpf_mov R7, R0 /* 保存foo()返回值 */
    bpf_mov R1, R6 /* 为下次调用恢复ctx */
    bpf_mov R2, 6
    bpf_mov R3, 7
    bpf_mov R4, 8
    bpf_mov R5, 9
    bpf_call bar
    bpf_add R0, R7
    bpf_exit

经过JIT到x86_64可能看起来像这样::

    push %rbp
    mov %rsp,%rbp
    sub $0x228,%rsp
    mov %rbx,-0x228(%rbp)
    mov %r13,-0x220(%rbp)
    mov %rdi,%rbx
    mov $0x2,%esi
    mov $0x3,%edx
    mov $0x4,%ecx
    mov $0x5,%r8d
    callq foo
    mov %rax,%r13
    mov %rbx,%rdi
    mov $0x6,%esi
    mov $0x7,%edx
    mov $0x8,%ecx
    mov $0x9,%r8d
    callq bar
    add %r13,%rax
    mov -0x228(%rbp),%rbx
    mov -0x220(%rbp),%r13
    leaveq
    retq

这在本例中等同于C中的::

    u64 bpf_filter(u64 ctx)
    {
	return foo(ctx, 2, 3, 4, 5) + bar(ctx, 6, 7, 8, 9);
    }

原型为u64 (*)(u64 arg1, u64 arg2, u64 arg3, u64 arg4, u64 arg5);的内核函数foo()和bar()将接收正确寄存器中的参数，并将其返回值置于``%rax``中，这是eBPF中的R0。
JIT发出的序言和尾声在解释器中是隐式的。R0-R5是工作寄存器，因此eBPF程序需要根据调用约定在调用之间保存它们。
例如，以下程序是无效的：

    bpf_mov R1, 1
    bpf_call foo
    bpf_mov R0, R1
    bpf_exit

调用之后，寄存器R1-R5包含垃圾值，无法读取。
内核中的验证器用于验证eBPF程序。
在新设计中，eBPF被限制为4096条指令，这意味着任何程序将迅速终止，并且只调用固定数量的内核函数。原始BPF和eBPF都是双操作数指令，
这有助于在JIT期间实现eBPF指令与x86指令之间的一对一映射。
调用解释器函数的输入上下文指针是通用的，其内容由特定的使用场景定义。对于seccomp，寄存器R1指向seccomp_data；对于转换后的BPF过滤器，R1指向skb。
内部翻译的程序由以下元素组成：

  op:16, jt:8, jf:8, k:32    ==>    op:8, dst_reg:4, src_reg:4, off:16, imm:32

到目前为止，已经实现了87条eBPF指令。8位'op'操作码字段有空间容纳新的指令。其中一些可能使用16/24/32字节编码。新指令必须是8字节的倍数，以保持向后兼容性。
eBPF是一种通用的精简指令集。并非每个寄存器和每条指令在从原始BPF到eBPF的翻译过程中都会被使用。
例如，套接字过滤器不使用“排他加法”指令，但跟踪过滤器可能会这样做以维护事件计数器等。寄存器R9也不被套接字过滤器使用，但更复杂的过滤器可能会耗尽寄存器，并不得不转向堆栈进行溢出/填充。
eBPF可以用作通用汇编器，用于最后一步的性能优化，套接字过滤器和seccomp正作为汇编器使用它。跟踪过滤器可能将其用作汇编器，以从内核生成代码。在内核使用中可能不会受到安全考虑的限制，因为生成的eBPF代码可能正在优化内部代码路径，而不是暴露给用户空间。
eBPF的安全性可以来源于验证器。在如上所述的使用案例中，它可以作为一种安全的指令集来使用。
就像原始BPF一样，eBPF在一个受控环境中运行，具有确定性，内核可以轻松证明这一点。程序的安全性可以通过两个步骤确定：第一步执行深度优先搜索以禁止循环和其他控制流图验证；第二步从第一条指令开始，并遍历所有可能的路径。它模拟每条指令的执行并观察寄存器和堆栈的状态变化。
eBPF重用了大部分经典BPF的opcode编码方式，以简化从经典BPF到eBPF的转换。对于算术和跳转指令，8位的'code'字段被分为三部分：

```
+----------------+--------+--------------------+
|    4 位        |   1 位 |      3 位          |
| 操作代码       | 源码   | 指令类别           |
+----------------+--------+--------------------+
(MSB)                                        (LSB)
```

最后三个比特位存储了指令类别，其中包括：

```
====================     ===============
经典BPF类别            eBPF类别
====================     ===============
BPF_LD    0x00          BPF_LD    0x00
BPF_LDX   0x01          BPF_LDX   0x01
BPF_ST    0x02          BPF_ST    0x02
BPF_STX   0x03          BPF_STX   0x03
BPF_ALU   0x04          BPF_ALU   0x04
BPF_JMP   0x05          BPF_JMP   0x05
BPF_RET   0x06          BPF_JMP32 0x06
BPF_MISC  0x07          BPF_ALU64 0x07
====================     ===============
```

第四个比特位编码了源操作数：

```
BPF_K     0x00
BPF_X     0x08
```

* 在经典BPF中，这意味着：
    ```
    BPF_SRC(code) == BPF_X - 使用寄存器X作为源操作数
    BPF_SRC(code) == BPF_K - 使用32位立即数作为源操作数
    ```
* 在eBPF中，这意味着：
    ```
    BPF_SRC(code) == BPF_X - 使用'src_reg'寄存器作为源操作数
    BPF_SRC(code) == BPF_K - 使用32位立即数作为源操作数
    ```

最高四位比特位存储了操作代码。
如果`BPF_CLASS(code)`为BPF_ALU或BPF_ALU64（在eBPF中），`BPF_OP(code)`之一是：

```
BPF_ADD   0x00
BPF_SUB   0x10
BPF_MUL   0x20
BPF_DIV   0x30
BPF_OR    0x40
BPF_AND   0x50
BPF_LSH   0x60
BPF_RSH   0x70
BPF_NEG   0x80
BPF_MOD   0x90
BPF_XOR   0xa0
BPF_MOV   0xb0  /* 仅eBPF：reg至reg的移动 */
BPF_ARSH  0xc0  /* 仅eBPF：符号扩展右移 */
BPF_END   0xd0  /* 仅eBPF：字节序转换 */
```

如果`BPF_CLASS(code)`为BPF_JMP或BPF_JMP32（在eBPF中），`BPF_OP(code)`之一是：

```
BPF_JA    0x00  /* 仅BPF_JMP */
BPF_JEQ   0x10
BPF_JGT   0x20
BPF_JGE   0x30
BPF_JSET  0x40
BPF_JNE   0x50  /* 仅eBPF：不等于跳转 */
BPF_JSGT  0x60  /* 仅eBPF：有符号大于 */
BPF_JSGE  0x70  /* 仅eBPF：有符号大于等于 */
BPF_CALL  0x80  /* 仅eBPF BPF_JMP：函数调用 */
BPF_EXIT  0x90  /* 仅eBPF BPF_JMP：函数返回 */
BPF_JLT   0xa0  /* 仅eBPF：无符号小于 */
BPF_JLE   0xb0  /* 仅eBPF：无符号小于等于 */
BPF_JSLT  0xc0  /* 仅eBPF：有符号小于 */
BPF_JSLE  0xd0  /* 仅eBPF：有符号小于等于 */
```

因此，BPF_ADD | BPF_X | BPF_ALU意味着在经典BPF和eBPF中都是32位加法。经典BPF中只有两个寄存器，这意味着A += X；而在eBPF中意味着`dst_reg = (u32) dst_reg + (u32) src_reg`；同样地，BPF_XOR | BPF_K | BPF_ALU在经典BPF中意味着A ^= imm32，在eBPF中则意味着`src_reg = (u32) src_reg ^ (u32) imm32`。

经典BPF使用BPF_MISC类来表示A = X和X = A的移动。eBPF使用BPF_MOV | BPF_X | BPF_ALU代码代替。由于eBPF中没有BPF_MISC操作，所以类别7被用作BPF_ALU64，意味着与BPF_ALU完全相同的运算，只是操作数宽度为64位。因此，BPF_ADD | BPF_X | BPF_ALU64意味着64位加法，即：`dst_reg = dst_reg + src_reg`。

经典BPF浪费了一个完整的BPF_RET类来表示单一的`ret`操作。经典BPF_RET | BPF_K意味着将imm32复制到返回寄存器并执行函数退出。eBPF设计为匹配CPU，所以BPF_JMP | BPF_EXIT在eBPF中仅仅意味着函数退出。eBPF程序需要在进行BPF_EXIT之前将返回值存储到寄存器R0中。类别6在eBPF中被用作BPF_JMP32，意味着与BPF_JMP完全相同的运算，但比较操作的宽度为32位。

对于加载和存储指令，8位的'code'字段的划分如下：

```
+--------+--------+-------------------+
|  3 位  |  2 位  |    3 位           |
| 模式   | 大小   | 指令类别          |
+--------+--------+-------------------+
(MSB)                              (LSB)
```

大小修饰符之一是：

```
BPF_W   0x00    /* 字 */
BPF_H   0x08    /* 半字 */
BPF_B   0x10    /* 字节 */
BPF_DW  0x18    /* 仅eBPF，双字 */
```

这编码了加载/存储操作的大小：

```
B  - 1字节
H  - 2字节
W  - 4字节
DW - 8字节（仅eBPF）
```

模式修饰符之一是：

```
BPF_IMM     0x00  /* 用于经典BPF中的32位mov和eBPF中的64位 */
BPF_ABS     0x20
BPF_IND     0x40
BPF_MEM     0x60
BPF_LEN     0x80  /* 仅经典BPF，eBPF中保留 */
BPF_MSH     0xa0  /* 仅经典BPF，eBPF中保留 */
BPF_ATOMIC  0xc0  /* 仅eBPF，原子操作 */
```
