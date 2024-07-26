经典BPF与eBPF
=============

eBPF被设计为具有一对一映射的即时编译（JIT），这也为GCC/LLVM编译器通过eBPF后端生成几乎和原生编译代码一样快的优化eBPF代码提供了可能性。从经典BPF到eBPF的一些核心变化包括：

- 寄存器数量从2个增加到10个：

  旧格式中有两个寄存器A和X，以及一个隐藏的帧指针。新布局扩展为10个内部寄存器和一个只读帧指针。由于64位CPU通过寄存器传递函数参数，eBPF程序向内核函数传递的参数数量被限制为5个，并且使用一个寄存器来接收来自内核函数的返回值。原生情况下，x86_64通过寄存器传递前6个参数，而aarch64/sparcv9/mips64则有7至8个寄存器用于参数；x86_64有6个调用者保存寄存器，而aarch64/sparcv9/mips64则有11个或更多的调用者保存寄存器。因此，在x86_64、aarch64等架构上，所有eBPF寄存器都一对一地映射到硬件寄存器上，eBPF调用约定直接映射到内核使用的64位架构上的应用程序二进制接口（ABI）。
在32位架构上，即时编译器可能会将仅使用32位算术的程序转换为原生指令集，并让更复杂的程序被解释执行。
R0至R5是临时寄存器，如果需要的话，eBPF程序在调用之间需要将它们填入或清空。需要注意的是，只有一个eBPF程序（即一个eBPF主例程），它不能调用其他eBPF函数，只能调用预定义的内核函数。
- 寄存器宽度从32位增加到64位：

  尽管如此，原始32位算术逻辑单元（ALU）操作的语义通过32位子寄存器得以保留。所有eBPF寄存器都是64位的，其中包含32位低位子寄存器，当写入时会零扩展到64位。
这种行为直接映射到x86_64和arm64子寄存器定义，但使得其他即时编译器更加复杂。
32位架构通过解释器运行64位eBPF程序。
它们的即时编译器可能将仅使用32位子寄存器的BPF程序转换为原生指令集，并让其余部分被解释执行。
操作是64位的，因为对于64位架构而言，指针也是64位宽的，并且我们希望在内核函数内外传递64位值。因此，如果使用32位eBPF寄存器，则需要定义寄存器对ABI，这样就无法使用直接的eBPF寄存器到硬件寄存器的映射，即时编译器将需要对每个寄存器进行组合/拆分/移动操作以进出函数，这既复杂又容易出错并且效率低下。
另一个原因是使用了原子的64位计数器 —— 将条件跳转jt/jf目标替换为jt/直接执行：

  在原始设计中存在诸如 `if (cond) jump_true; else jump_false;` 这样的结构，它们正被替换为类似 `if (cond) jump_true; /* else 直接执行 */` 的替代结构。
- 引入了bpf_call指令和寄存器传递约定以实现从/到其他内核函数调用时零开销的调用：

  在内核中的函数调用之前，eBPF程序需要将函数参数放置在R1至R5寄存器中以满足调用约定，然后解释器会从这些寄存器中取出参数并传递给内核中的函数。如果R1 - R5寄存器映射到了架构上用于参数传递的CPU寄存器，则JIT编译器无需发出额外的数据移动指令。函数参数将位于正确的寄存器中，并且BPF_CALL指令将被JIT编译为单一的'call'硬件指令。选择这种调用约定是为了覆盖常见的调用情况而不带来性能损失。
在内核函数调用之后，R1 - R5被重置为不可读状态，而R0则包含该函数的返回值。由于R6 - R9是被调用者保存的，因此它们的状态会在调用过程中得到保留。
例如，考虑三个C函数：

    u64 f1() { return (*_f2)(1); }
    u64 f2(u64 a) { return f3(a + 1, a); }
    u64 f3(u64 a, u64 b) { return a - b; }

GCC可以将f1、f3编译为x86_64架构下的代码：

    f1:
	movl $1, %edi
	movq _f2(%rip), %rax
	jmp  *%rax
    f3:
	movq %rdi, %rax
	subq %rsi, %rax
	ret

eBPF中的函数f2可能看起来像这样：

    f2:
	bpf_mov R2, R1
	bpf_add R1, 1
	bpf_call f3
	bpf_exit

如果f2被JIT编译并且指向存储在`_f2`中的指针，那么从f1到f2再到f3的调用以及返回将是无缝的。没有JIT的情况下，必须使用__bpf_prog_run()解释器来调用f2。
出于实际原因，所有eBPF程序都只有一个名为'ctx'的参数，它已经被放置在R1中（例如，在__bpf_prog_run()启动时），并且程序可以调用具有最多5个参数的内核函数。目前不支持具有6个或更多参数的调用，但如果必要的话，将来可以取消这些限制。
在64位架构上，所有寄存器一对一地映射到硬件寄存器。例如，x86_64 JIT编译器可以将它们映射为：
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

因为x86_64 ABI规定rdi、rsi、rdx、rcx、r8、r9用于参数传递，并且rbx、r12 - r15是被调用者保存的。
接下来，以下eBPF伪程序：

    bpf_mov R6, R1 /* 保存ctx */
    bpf_mov R2, 2
    bpf_mov R3, 3
    bpf_mov R4, 4
    bpf_mov R5, 5
    bpf_call foo
    bpf_mov R7, R0 /* 保存foo()返回值 */
    bpf_mov R1, R6 /* 为下一次调用恢复ctx */
    bpf_mov R2, 6
    bpf_mov R3, 7
    bpf_mov R4, 8
    bpf_mov R5, 9
    bpf_call bar
    bpf_add R0, R7
    bpf_exit

经过JIT编译到x86_64后可能看起来像这样：

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

这在本例中等同于C语言中的：

    u64 bpf_filter(u64 ctx)
    {
	return foo(ctx, 2, 3, 4, 5) + bar(ctx, 6, 7, 8, 9);
    }

内核函数foo()和bar()的原型为：u64 (*)(u64 arg1, u64 arg2, u64 arg3, u64 arg4, u64 arg5)；将接收正确寄存器中的参数，并将它们的返回值放置到`%rax`中，即eBPF中的R0。
序言和尾声是由JIT生成的，并在解释器中是隐式的。R0-R5是临时寄存器，所以eBPF程序需要根据调用约定在调用过程中保持它们的状态。
以下程序是无效的：

    bpf_mov R1, 1
    bpf_call foo
    bpf_mov R0, R1
    bpf_exit

调用之后，寄存器R1-R5包含无用值，不能被读取。
内核中的验证器（verifier.rst）用于验证eBPF程序。
在新设计中，eBPF限制为4096条指令，这意味着任何程序都会迅速终止，并且只能调用固定数量的内核函数。原始BPF和eBPF都是双操作数指令，
这有助于在JIT过程中实现eBPF指令与x86指令之间的一对一映射。
调用解释器函数的输入上下文指针是通用的，其内容由特定用途案例定义。对于seccomp，寄存器R1指向seccomp_data；对于转换后的BPF过滤器，R1指向skb。

内部翻译的程序由以下元素组成：

  op:16, jt:8, jf:8, k:32    ==>    op:8, dst_reg:4, src_reg:4, off:16, imm:32

到目前为止，已经实现了87条eBPF指令。8位'op'操作码字段还有空间添加新的指令。其中一些可能使用16/24/32字节编码。新的指令必须是8字节的倍数以保持向后兼容性。
eBPF是一种通用的精简指令集（RISC）。并非每个寄存器和每条指令在从原始BPF翻译到eBPF的过程中都会被使用。
例如，套接字过滤器不会使用`exclusive add`指令，但追踪过滤器可能会使用该指令来维护事件计数器等。寄存器R9没有被套接字过滤器使用，但更复杂的过滤器可能会耗尽寄存器，并不得不借助于堆栈的溢出/填充。
eBPF可以用作通用汇编器进行最后阶段的性能优化。套接字过滤器和seccomp将其用作汇编器。追踪过滤器可能将其用作汇编器来从内核生成代码。在内核使用中可能不受安全考虑的限制，因为生成的eBPF代码可能是优化内部代码路径，并不暴露给用户空间。
eBPF的安全性可以来源于验证器（verifier.rst）。在上述情况下，它可以作为一种安全的指令集使用。
就像原始BPF一样，eBPF在一个受控环境中运行，是确定性的，内核可以很容易地证明这一点。程序的安全性可以通过两个步骤来确定：第一步采用深度优先搜索禁止循环和其他控制流图（CFG）验证；第二步从第一条指令开始，并遍历所有可能的路径。它模拟每条指令的执行并观察寄存器和堆栈的状态变化。
eBPF重用了大部分经典BPF的指令编码方式以简化从经典BPF到eBPF的转换。
对于算术和跳转指令，8位的`code`字段被分为三部分：

  +----------------+--------+--------------------+
  |   4 位         |  1 位  |   3 位             |
  | 操作码         | 源     | 指令类别           |
  +----------------+--------+--------------------+
  (最高有效位)                                        (最低有效位)

最低三位存储指令类别，其中包括：

  ===================     ===============
  经典BPF类别             eBPF类别
  ===================     ===============
  BPF_LD    0x00          BPF_LD    0x00
  BPF_LDX   0x01          BPF_LDX   0x01
  BPF_ST    0x02          BPF_ST    0x02
  BPF_STX   0x03          BPF_STX   0x03
  BPF_ALU   0x04          BPF_ALU   0x04
  BPF_JMP   0x05          BPF_JMP   0x05
  BPF_RET   0x06          BPF_JMP32 0x06
  BPF_MISC  0x07          BPF_ALU64 0x07
  ===================     ===============

第四个位编码源操作数：
::

    BPF_K     0x00
    BPF_X     0x08

 * 在经典BPF中，这意味着：
 
    BPF_SRC(code) == BPF_X - 使用寄存器X作为源操作数
    BPF_SRC(code) == BPF_K - 使用32位立即数作为源操作数

 * 在eBPF中，这意味着：
 
    BPF_SRC(code) == BPF_X - 使用'src_reg'寄存器作为源操作数
    BPF_SRC(code) == BPF_K - 使用32位立即数作为源操作数

... 最高四位存储操作码
如果BPF_CLASS(code) == BPF_ALU 或 BPF_ALU64 [在eBPF中]，则BPF_OP(code)可以是以下之一：

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
  BPF_MOV   0xb0  /* 仅eBPF: 寄存器到寄存器的移动 */
  BPF_ARSH  0xc0  /* 仅eBPF: 符号扩展右移 */
  BPF_END   0xd0  /* 仅eBPF: 字节序转换 */

如果BPF_CLASS(code) == BPF_JMP 或 BPF_JMP32 [在eBPF中]，则BPF_OP(code)可以是以下之一：

  BPF_JA    0x00  /* 仅BPF_JMP */
  BPF_JEQ   0x10
  BPF_JGT   0x20
  BPF_JGE   0x30
  BPF_JSET  0x40
  BPF_JNE   0x50  /* 仅eBPF: 不等于跳转 */
  BPF_JSGT  0x60  /* 仅eBPF: 带符号大于 */
  BPF_JSGE  0x70  /* 仅eBPF: 带符号大于等于 */
  BPF_CALL  0x80  /* 仅eBPF BPF_JMP: 函数调用 */
  BPF_EXIT  0x90  /* 仅eBPF BPF_JMP: 函数返回 */
  BPF_JLT   0xa0  /* 仅eBPF: 无符号小于 */
  BPF_JLE   0xb0  /* 仅eBPF: 无符号小于等于 */
  BPF_JSLT  0xc0  /* 仅eBPF: 带符号小于 */
  BPF_JSLE  0xd0  /* 仅eBPF: 带符号小于等于 */

因此，BPF_ADD | BPF_X | BPF_ALU 在经典BPF和eBPF中都表示32位加法。由于经典BPF中只有两个寄存器，这意呈着A += X;
在eBPF中它意味着 dst_reg = (u32) dst_reg + (u32) src_reg; 同样地，
BPF_XOR | BPF_K | BPF_ALU 在经典BPF中意味着 A ^= imm32，并且在eBPF中有类似的含义：src_reg = (u32) src_reg ^ (u32) imm32
经典BPF使用BPF_MISC类来表示A = X 和 X = A的移动操作。
eBPF使用BPF_MOV | BPF_X | BPF_ALU代码代替。由于eBPF中没有BPF_MISC操作，所以类别7被用作BPF_ALU64来表示与BPF_ALU完全相同的运算，
但使用的是64位宽的操作数。因此，BPF_ADD | BPF_X | BPF_ALU64 表示64位加法，即：dst_reg = dst_reg + src_reg。

经典BPF浪费了整个BPF_RET类来表示单一的`ret`操作。经典BPF_RET | BPF_K 意味着将imm32复制到返回寄存器并执行函数退出。
eBPF被设计为与CPU匹配，因此BPF_JMP | BPF_EXIT 在eBPF中仅仅意味着函数退出。eBPF程序需要在执行BPF_EXIT之前将返回值存储到寄存器R0中。
类别6在eBPF中被用作BPF_JMP32，其含义与BPF_JMP完全相同，但比较操作使用的操作数宽度为32位。

对于加载和存储指令，8位的`code`字段被划分如下：

  +--------+--------+-------------------+
  | 3 位   | 2 位   |   3 位            |
  | 模式   | 大小   | 指令类别          |
  +--------+--------+-------------------+
  (最高有效位)                                            (最低有效位)

大小修饰符包括：
::

  BPF_W   0x00    /* 字 */
  BPF_H   0x08    /* 半字 */
  BPF_B   0x10    /* 字节 */
  BPF_DW  0x18    /* 仅eBPF，双字 */

... 这些编码了加载/存储操作的大小：

 B  - 1 字节
 H  - 2 字节
 W  - 4 字节
 DW - 8 字节（仅eBPF）

模式修饰符包括：

  BPF_IMM     0x00  /* 用于32位mov的经典BPF和64位的eBPF */
  BPF_ABS     0x20
  BPF_IND     0x40
  BPF_MEM     0x60
  BPF_LEN     0x80  /* 仅经典BPF，eBPF中保留 */
  BPF_MSH     0xa0  /* 仅经典BPF，eBPF中保留 */
  BPF_ATOMIC  0xc0  /* 仅eBPF，原子操作 */
