======================
AArch64 Linux 的可伸缩矢量扩展支持
======================

作者: Dave Martin <Dave.Martin@arm.com>

日期: 2017年8月4日

本文档简要概述了Linux为支持ARM 可伸缩矢量扩展（SVE）所提供的用户空间接口，包括与通过可伸缩矩阵扩展（SME）添加的流式SVE模式的交互。本文档仅概述最重要的特性和问题，并非详尽无遗。本文档并不旨在描述SVE架构或程序员模型。为了帮助理解，在附录A中包含了关于SVE相关程序员模型特性的最小描述。

1. 通用
--------------

* SVE寄存器Z0..Z31、P0..P15和FFR以及当前向量长度VL是按线程跟踪的。
* 在流式模式下，除非系统中存在HWCAP2_SME_FA64标志，否则无法访问FFR；当该标志不存在时，这些接口用于访问流式模式下的FFR时，FFR将被读取和写入为零。
* SVE的存在通过在辅助向量AT_HWCAP条目中的HWCAP_SVE报告给用户空间。此标志的存在意味着存在SVE指令和寄存器，以及本文档中描述的Linux特定系统接口。SVE会在/proc/cpuinfo中以"sve"的形式报告。
* 用户空间可以通过读取CPU ID寄存器ID_AA64PFR0_EL1使用MRS指令并检查SVE字段的值是否非零来检测执行SVE指令的支持。[3]
  
  这并不能保证以下各节中描述的系统接口的存在：需要验证这些接口存在的软件必须检查HWCAP_SVE。
* 在支持SVE2扩展的硬件上，HWCAP2_SVE2也会在AT_HWCAP2辅助向量条目中报告。除此之外，SVE2的可选扩展可以通过以下标志的存在来报告：

	HWCAP2_SVE2
	HWCAP2_SVEAES
	HWCAP2_SVEPMULL
	HWCAP2_SVEBITPERM
	HWCAP2_SVESHA3
	HWCAP2_SVESM4
	HWCAP2_SVE2P1

  随着SVE架构的发展，这个列表可能会随时间而扩展。
这些扩展也可以通过CPU ID寄存器ID_AA64ZFR0_EL1报告，用户空间可以使用MRS指令读取它。请参阅elf_hwcaps.txt和cpu-feature-registers.txt了解详细信息。
* 在支持SME扩展的硬件上，HWCAP2_SME也会在AT_HWCAP2辅助向量条目中报告。除了其他功能外，SME还增加了流式模式，该模式使用单独的SME向量长度和相同的Z/V寄存器提供SVE功能集的一个子集。更多细节请参见sme.rst。
* 调试器应仅通过NT_ARM_SVE寄存器集与目标进行交互。推荐的检测此寄存器集支持的方法是首先连接到目标进程，然后尝试执行ptrace(PTRACE_GETREGSET, pid, NT_ARM_SVE, &iov)。请注意，当SME存在且使用流式SVE模式时，FPSIMD寄存器子集将通过NT_ARM_SVE读取，并且对NT_ARM_SVE的写入会使目标退出流式模式。
* 当SVE可扩展寄存器值（Zn、Pn、FFR）在用户空间和内核之间通过内存交换时，寄存器值以字节序不变的布局编码在内存中，位[(8 * i + 7) : (8 * i)]编码在从内存表示开始的字节偏移量i处。这影响了例如信号帧（struct sve_context）和ptrace接口（struct user_sve_header）及其相关数据。
请注意，在大端系统上，这会导致不同于FPSIMD V-寄存器的字节顺序，后者作为单个主机字序的128位值存储，寄存器的位[(127 - 8 * i) : (120 - 8 * i)]编码在字节偏移量i处。（struct fpsimd_context, struct user_fpsimd_state）
2. 向量长度术语
------------------

SVE向量（Z）寄存器的大小称为“向量长度”为了避免表达向量长度时单位的混淆，内核采用以下约定：

* 向量长度（VL）= Z寄存器的字节数

* 向量四字组（VQ）= Z寄存器的128位单位数

（因此，VL = 16 * VQ。）

当底层粒度重要时，比如在数据结构定义中，使用VQ约定。在大多数其他情况下，使用VL约定。这与SVE指令集架构中的“VL”伪寄存器的意义一致。
3. 系统调用行为
-------------------

* 在系统调用时，V0..V31被保留（如同没有SVE）。因此，Z0..Z31的位[127:0]被保留。Z0..Z31的所有其他位以及P0..P15和FFR在从系统调用返回后变为0。
* SVE寄存器不用于传递系统调用的参数或接收其结果。
* 线程的所有其他SVE状态，包括当前配置的向量长度、PR_SVE_VL_INHERIT标志的状态以及延迟向量长度（如果有的话），在所有系统调用之间都被保留，但第6节中描述的execve()特定例外情况除外。
特别是，在fork()或clone()返回后，父进程和新创建的子进程或线程共享相同的SVE配置，与调用前父进程的配置相匹配。
4. 信号处理
--------------

* 新的信号帧记录sve_context在发送信号时编码SVE寄存器。[1]

* 此记录是对fpsimd_context的补充。FPSR和FPCR寄存器仅存在于fpsimd_context中。为了方便起见，V0..V31的内容在sve_context和fpsimd_context之间重复。
* 记录中包含一个标志字段，该字段包括一个 SVE_SIG_FLAG_SM 标志，如果设置，则表示线程处于流模式，并且向量长度和寄存器数据（如果存在）描述了流 SVE 数据和向量长度。
* 对于 SVE 的信号帧记录始终包含基本元数据，特别是线程的向量长度（在 sve_context.vl 中）。
* SVE 寄存器可能包含在记录中也可能不包含，这取决于这些寄存器对于线程是否处于活动状态。寄存器仅当满足以下条件时才存在：
  sve_context.head.size >= SVE_SIG_CONTEXT_SIZE(sve_vq_from_vl(sve_context.vl))
* 如果寄存器存在，记录的剩余部分具有依赖于 vl 的大小和布局。定义了 SVE_SIG_* 宏 [1] 来方便地访问成员。
* 每个可扩展寄存器（Zn、Pn、FFR）都以字节序不变的布局存储，位 [(8 * i + 7) : (8 * i)] 存储在从寄存器内存表示起始处的字节偏移 i 处。
* 如果 SVE 上下文太大无法放入 sigcontext.__reserved[] 中，则会在栈上分配额外的空间，在 __reserved[] 中写入一个 extra_context 记录来引用这个空间。然后将 sve_context 写入到这个额外空间中。关于这种机制的更多细节请参考 [1]。
5. 信号返回
------------

当从信号处理程序返回时：

* 如果信号帧中没有 sve_context 记录，或者记录虽然存在但如前一节所述不包含寄存器数据，则 SVE 寄存器/位变为非活动状态并取不确定的值。
* 如果信号帧中的 sve_context 存在并且包含完整的寄存器数据，则 SVE 寄存器变为活动状态并填充指定的数据。但是，出于向后兼容性的原因，Z0..Z31 的位 [127:0] 总是从 fpsimd_context.vregs[] 中对应的成员恢复而不是从 sve_context 中恢复。其余位则从 sve_context 中恢复。
* 不论 sve_context 是否存在，信号帧中包含 fpsimd_context 仍然是强制性的。
* 不能通过信号返回改变向量长度。如果信号帧中的 sve_context.vl 与当前向量长度不符，则尝试信号返回被视为非法，导致强制产生 SIGSEGV。
* 允许通过设置或清除 SVE_SIG_FLAG_SM 标志来进入或退出流模式，但应用程序应注意确保这样做时，sve_context.vl 和任何寄存器数据都适合新模式下的向量长度。
6.  prctl 扩展
--------------------

添加了一些新的 prctl() 调用以允许程序管理 SVE 向量长度：

prctl(PR_SVE_SET_VL, unsigned long arg)

    设置调用线程的向量长度及相关标志，其中 arg 等于 vl | flags。调用进程的其他线程不受影响。
vl 是期望的向量长度，其中必须有 sve_vl_valid(vl) 为真
标志：

	PR_SVE_VL_INHERIT

	    在 execve() 期间继承当前向量长度。否则，在 execve() 期间将向量长度重置为系统默认值。（参见第 9 节。）

	PR_SVE_SET_VL_ONEXEC

	    将请求的向量长度更改推迟到此线程执行的下一个 execve()
	    这相当于在该线程执行的下一个 execve()（如果有的话）之后立即隐式执行以下调用：

		prctl(PR_SVE_SET_VL, arg & ~PR_SVE_SET_VL_ONEXEC)

	    这允许使用不同的向量长度启动新程序，同时避免调用者运行时的副作用
如果没有 PR_SVE_SET_VL_ONEXEC，请求的更改会立即生效
返回值：成功时为非负数，出错时为负值：
	EINVAL: 不支持 SVE、请求了无效的向量长度或无效的标志
成功时：

    * 要么是调用线程的向量长度，要么是将在下一次由线程执行的 execve() 时应用的延迟向量长度（取决于 arg 中是否包含 PR_SVE_SET_VL_ONEXEC），会被设置为小于或等于 vl 的系统支持的最大值。如果 vl == SVE_VL_MAX，则设置的值将是系统支持的最大值
* 取消调用线程中先前存在的任何延迟向量长度更改
* 返回的值描述了结果配置，编码方式与 PR_SVE_GET_VL 相同。此值中报告的向量长度是此线程的新当前向量长度（如果 arg 中不包含 PR_SVE_SET_VL_ONEXEC）；否则，报告的向量长度是将在下一次由调用线程执行的 execve() 时应用的延迟向量长度
* 更改向量长度会导致所有 P0..P15、FFR 以及除 Z0 的 [127:0] 位至 Z31 的 [127:0] 位之外的所有 Z0..Z31 位变为未指定。通过 `prctl(PR_SVE_SET_VL)` 设置与当前线程的向量长度相等的 vl，或带有 `PR_SVE_SET_VL_ONEXEC` 标志调用 `prctl(PR_SVE_SET_VL)`，对于这个目的来说，并不构成向量长度的变化。
`prctl(PR_SVE_GET_VL)`

    获取调用线程的向量长度
以下标志可以与结果进行按位或操作：

    `PR_SVE_VL_INHERIT`

        向量长度将在 `execve()` 跨进程继承
没有方法来确定是否有待处理的延迟向量长度更改（这通常只会在 `fork()` 或 `vfork()` 与对应的 `execve()` 之间发生）
要从结果中提取向量长度，请使用按位与操作和 `PR_SVE_VL_LEN_MASK`
返回值：成功时为非负值，失败时为负值：
    `EINVAL`: 不支持 SVE
7.  ptrace 扩展
---------------------

* 定义了新的寄存器集 NT_ARM_SVE 和 NT_ARM_SSVE 用于 `PTRACE_GETREGSET` 和 `PTRACE_SETREGSET`。NT_ARM_SSVE 描述了流模式下的 SVE 寄存器，而 NT_ARM_SVE 描述了非流模式下的 SVE 寄存器。
在此描述中，当目标处于适当的流或非流模式并使用超出与 FPSIMD Vn 寄存器共享子集的数据时，称寄存器集为“活动”状态
具体定义请参考 [2]
寄存器集数据以 `struct user_sve_header` 开始，其中包含：

    `size`

        完整寄存器集的大小，以字节为单位
这段文本的中文翻译如下：

这取决于`vl`，并且将来可能还取决于其他因素。
如果对`PTRACE_GETREGSET`的调用请求的数据少于`size`的值，调用者可以分配一个更大的缓冲区并重新尝试以读取完整的寄存器集（regset）的最大尺寸。

`max_size`

目标线程的寄存器集（regset）能够增长到的最大字节数。即使目标线程改变其向量长度等，寄存器集也不会增长得比这个值更大。

`vl`

目标线程当前的向量长度，以字节为单位。

`max_vl`

目标线程可能的最大向量长度。

`flags`

最多包含以下之一：

    `SVE_PT_REGS_FPSIMD`

表示SVE寄存器不是活动的（GETREGSET）或者要被设为非活动的（SETREGSET）。有效载荷类型为`struct user_fpsimd_state`，与`NT_PRFPREG`具有相同的含义，从`user_sve_header`结构起始位置偏移`SVE_PT_FPSIMD_OFFSET`开始。未来可能会追加额外数据：应使用`SVE_PT_FPSIMD_SIZE(vq, flags)`来获取有效载荷的大小。

`vq`应该通过`sve_vq_from_vl(vl)`获得。

或者

    `SVE_PT_REGS_SVE`

表示SVE寄存器是活动的（GETREGSET）或者要被设为活动的（SETREGSET）。
有效载荷包含 SVE 寄存器数据，从 `user_sve_header` 开始处的偏移量 `SVE_PT_SVE_OFFSET` 开始，并且大小为 `SVE_PT_SVE_SIZE(vq, flags)`。

... 或者与以下一个或多个标志进行按位或操作，这些标志具有与相应的 `PR_SET_VL_*` 标志相同的含义和行为：

    `SVE_PT_VL_INHERIT`

    `SVE_PT_VL_ONEXEC`（仅限 `SETREGSET`）

如果没有提供 FPSIMD 或 SVE 标志，则没有可用的寄存器有效载荷，这仅在实现 SME 的情况下才可能发生。
* 更改向量长度和/或标志的效果等同于 `PR_SVE_SET_VL` 中记录的效果。
调用方如果需要知道 `SETREGSET` 实际设置的 VL 是什么，则必须进行进一步的 `GETREGSET` 调用，除非已事先知道请求的 VL 是支持的。
* 在 `SVE_PT_REGS_SVE` 情况下，有效载荷的大小和布局取决于头部字段。提供了 `SVE_PT_SVE_*()` 宏来方便地访问成员。
* 在任何一种情况下，对于 `SETREGSET` 来说，允许省略有效载荷，在这种情况下只更改向量长度和标志（以及由此产生的任何后果）。
* 在支持 SME 的系统中，当处于流模式时，`NT_REG_SVE` 的 `GETREGSET` 只会返回 `user_sve_header` 而不包含任何寄存器数据；类似地，当不在流模式时，`NT_REG_SSVE` 的 `GETREGSET` 不会返回任何寄存器数据。
* `NT_ARM_SSVE` 的 `GETREGSET` 永远不会返回 `SVE_PT_REGS_FPSIMD`。
* 对于 `SETREGSET`，如果存在 `SVE_PT_REGS_SVE` 有效载荷且请求的 VL 不被支持，则其效果将如同省略了有效载荷一样，只是会报告一个 EIO 错误。不会尝试将有效载荷数据转换为实际设置的向量长度的正确布局。线程的 FPSIMD 状态得以保留，但 SVE 寄存器的剩余位则变为未指定。由调用方负责将有效载荷布局转换为实际的 VL 并重试。
* 在实现 SME 的情况下，在流模式下无法获取常规 SVE 的寄存器状态，也不可以在常规模式下获取流模式的寄存器状态，无论硬件的实现定义的行为如何处理这两种模式之间的数据共享。
* 对于任何涉及NT_ARM_SVE的SETREGSET操作，如果目标原先处于流模式，则会退出该模式；对于任何涉及NT_ARM_SSVE的SETREGSET操作，如果目标原先不处于流模式，则会进入流模式。
* 写入部分、不完整的有效载荷的效果未作规定。
8.  ELF 核心转储扩展
---------------------------

* 对于每个被转储进程的每个线程，都将添加NT_ARM_SVE和NT_ARM_SSVE的注释。这些内容等同于在生成核心转储时对每个线程执行相应类型的PTRACE_GETREGSET命令所读取的数据。
9. 系统运行时配置
-------------------

* 为了缓解信号帧扩展对ABI的影响，为管理员、发行版维护者和开发者提供了一种策略机制来设置用户空间进程的默认向量长度：

/proc/sys/abi/sve_default_vector_length

    将整数的文本表示形式写入此文件将把系统的默认向量长度设置为指定值，并按照与通过PR_SVE_SET_VL设置向量长度相同的规则将其四舍五入到支持的值。
    可以通过重新打开文件并读取其内容来确定结果。
    在启动时，默认向量长度最初设置为64或最大支持的向量长度中的较小值。这决定了init进程（PID 1）的初始向量长度。
    从该文件读取返回当前系统的默认向量长度。
* 每次调用execve()时，新进程的新向量长度将被设置为系统默认向量长度，除非

    * 调用线程设置了PR_SVE_VL_INHERIT（或等效地SVE_PT_VL_INHERIT），或者

    * 通过PR_SVE_SET_VL_ONEXEC标志（或SVE_PT_VL_ONEXEC）建立了一个待处理的向量长度更改。
* 修改系统默认向量长度不会影响任何未进行execve()调用的现有进程或线程的向量长度。
10. Perf 扩展
------------------------------

* 针对arm64特定的DWARF标准[5]在索引46处新增了VG（向量粒度）寄存器。当可变长度SVE寄存器被推送到栈上时，此寄存器用于DWARF反汇编。
其值等同于当前SVE向量长度（VL）以比特为单位除以64。

- 如果设置了`PERF_SAMPLE_REGS_USER`，并且样本寄存器掩码`sample_regs_user`中的第46位被设置，则该值会被包含在性能样本的`regs[46]`字段中。
- 该值是取样时的当前值，并且会随时间变化。
- 如果系统在调用`perf_event_open`使用这些设置时不支持SVE，则该事件将无法打开。

附录 A. SVE 程序员模型（信息性）

本节提供了一个最小化的描述，涉及SVE对ARMv8-A程序员模型所做的与本文档相关的补充内容。  
注意：本节仅为提供信息之用，并不打算完整或替代任何架构规范。

A.1 寄存器

在A64状态下，SVE增加了以下内容：

- 32个8VL位的向量寄存器 Z0至Z31
  - 对于每个Zn，Zn的比特位[127:0]等同于ARMv8-A向量寄存器Vn
  - 使用Vn寄存器名进行寄存器写入操作会将对应的Zn中除了比特位[127:0]以外的所有位清零。
- 16个VL位的谓词寄存器 P0至P15
- 1个VL位的特殊用途谓词寄存器FFR（“首次故障寄存器”）
- 一个确定每个向量寄存器大小的VL“伪寄存器”

SVE指令集架构没有直接写入VL的方法。相反，只能通过EL1及以上层级，通过写入适当的系统寄存器来修改它。
* VL的值可以在EL1及以上层级在运行时进行配置：
  16 <= VL <= VLmax，其中VL必须是16的倍数
* 最大的向量长度由硬件决定：
  16 <= VLmax <= 256
（SVE架构指定了256作为上限，但允许未来的架构修订提高这个限制。）

* FPSR和FPCR继承自ARMv8-A，并且与SVE浮点运算交互的方式类似于它们与ARMv8浮点运算交互的方式：

         8VL-1                       128               0  位索引
        +----          ////            -----------------+
     Z0 |                               :       V0      |
      :                                          :
     Z7 |                               :       V7      |
     Z8 |                               :     * V8      |
      :                                       :  :
    Z15 |                               :     *V15      |
    Z16 |                               :      V16      |
      :                                          :
    Z31 |                               :      V31      |
        +----          ////            -----------------+
                                                 31    0
         VL-1                  0                +-------+
        +----       ////      --+          FPSR |       |
     P0 |                       |               +-------+
      : |                       |         *FPCR |       |
    P15 |                       |               +-------+
        +----       ////      --+
    FFR |                       |               +-----+
        +----       ////      --+            VL |     |
                                                +-----+

(*) 保留给被调用者保存：
    这仅适用于Z-/V寄存器中[63:0]的位
FPCR包含被调用者保存和调用者保存的位。具体细节请参见[4]
A.2.  过程调用标准
------------------------------

对于额外的SVE寄存器状态，ARMv8-A基础过程调用标准做了如下扩展：

* 所有不与FP/SIMD共享的SVE寄存器位都是调用者保存
* Z8位[63:0] ~ Z15位[63:0]是被调用者保存
这源于这些位映射到V8~V15的方式，在基础过程调用标准中V8~V15是调用者保存
附录B.  ARMv8-A FP/SIMD程序员模型
=====================================

注意：本节仅供信息参考，并非完整描述或替代任何架构规范
更多信息请参阅[4]
ARMv8-A定义了以下浮点/向量寄存器状态：

* 32个128位向量寄存器V0~V31
* 2个32位状态/控制寄存器FPSR、FPCR

::

         127           0  位索引
        +---------------+
     V0 |               |
      : :               :
     V7 |               |
   * V8 |               |
   :  : :               :
   *V15 |               |
    V16 |               |
      : :               :
    V31 |               |
        +---------------+

                 31    0
                +-------+
           FPSR |       |
                +-------+
          *FPCR |       |
                +-------+

(*) 保留给被调用者保存：
    这仅适用于V寄存器中[63:0]的位
FPCR包含了一种调用者保存（callee-save）和被调用者保存（caller-save）位的混合。

参考资料
========

[1] arch/arm64/include/uapi/asm/sigcontext.h  
    AArch64 林纳克斯信号处理应用程序二进制接口定义

[2] arch/arm64/include/uapi/asm/ptrace.h  
    AArch64 林纳克斯跟踪调试应用程序二进制接口定义

[3] Documentation/arch/arm64/cpu-feature-registers.rst

[4] ARM IHI0055C  
    http://infocenter.arm.com/help/topic/com.arm.doc.ihi0055c/IHI0055C_beta_aapcs64.pdf  
    http://infocenter.arm.com/help/topic/com.arm.doc.subset.swdev.abi/index.html  
    ARM 64位架构（AArch64）的过程调用标准

[5] https://github.com/ARM-software/abi-aa/blob/main/aadwarf64/aadwarf64.rst
