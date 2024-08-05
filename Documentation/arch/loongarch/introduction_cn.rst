### SPDX 许可证标识符: GPL-2.0

=========================
LoongArch 简介
=========================

LoongArch 是一种新的精简指令集架构（ISA），它类似于MIPS或RISC-V。目前有三种变体：简化版32位（LA32R）、标准32位（LA32S）和64位（LA64）。LoongArch定义了四个特权级别（PLV）：PLV0~PLV3，从高到低排列。内核在PLV0运行，而应用程序则在PLV3运行。本文档介绍了LoongArch的寄存器、基本指令集、虚拟内存和其他一些主题。

### 寄存器
#### LoongArch 寄存器包括通用寄存器（GPRs）、浮点寄存器（FPRs）、向量寄存器（VRs）以及特权模式（PLV0）中使用的控制状态寄存器（CSRs）。
##### 通用寄存器 (GPRs)

LoongArch包含32个GPRs（`$r0` ~ `$r31`）；在LA32中每个是32位宽，在LA64中则是64位宽。`$r0`被硬件固定为零值，其他寄存器在架构上没有特殊含义（除了`$r1`，它是BL指令的链接寄存器）。

内核使用了一种LoongArch寄存器约定的变体，如LoongArch ELF psABI规范所述：

| 名称 | 别名 | 用途 | 跨调用时保留 |
|------|------|------|--------------|
| `$r0` | `$zero` | 常数零 | 不使用 |
| `$r1` | `$ra` | 返回地址 | 否 |
| `$r2` | `$tp` | TLS/线程指针 | 不使用 |
| `$r3` | `$sp` | 栈指针 | 是 |
| `$r4`-`$r11` | `$a0`-`$a7` | 参数寄存器 | 否 |
| `$r4`-`$r5` | `$v0`-`$v1` | 返回值 | 否 |
| `$r12`-`$r20` | `$t0`-`$t8` | 临时寄存器 | 否 |
| `$r21` | `$u0` | 每个CPU基础地址 | 不使用 |
| `$r22` | `$fp` | 帧指针 | 是 |
| `$r23`-`$r31` | `$s0`-`$s8` | 静态寄存器 | 是 |

**注释**：
寄存器`$r21`在ELF psABI中是保留的，但Linux内核将其用于存储每个CPU的基础地址。它通常没有ABI名称，但在内核中称为`$u0`。您也可能在一些旧代码中看到`$v0`或`$v1`，但它们分别是`$a0`和`$a1`的过时别名。

##### 浮点寄存器 (FPRs)

当存在FPU时，LoongArch包含32个FPRs（`$f0` ~ `$f31`）。在LA64核心上，每个FPR是64位宽。

浮点寄存器约定与LoongArch ELF psABI规范中描述的一致：

| 名称 | 别名 | 用途 | 跨调用时保留 |
|------|------|------|--------------|
| `$f0`-`$f7` | `$fa0`-`$fa7` | 参数寄存器 | 否 |
| `$f0`-`$f1` | `$fv0`-`$fv1` | 返回值 | 否 |
| `$f8`-`$f23` | `$ft0`-`$ft15` | 临时寄存器 | 否 |
| `$f24`-`$f31` | `$fs0`-`$fs7` | 静态寄存器 | 是 |

**注释**：
您可能在一些旧代码中看到`$fv0`或`$fv1`，但它们分别是`$fa0`和`$fa1`的过时别名。

##### 向量寄存器 (VRs)

目前LoongArch有两个向量扩展：

- LSX（Loongson SIMD 扩展），具有128位向量，
- LASX（Loongson Advanced SIMD 扩展），具有256位向量。

LSX引入了`$v0` ~ `$v31`作为向量寄存器，而LASX引入了`$x0` ~ `$x31`。

向量寄存器与FPR重叠：例如，在实现LSX和LASX的核心上，`$x0`的较低128位与`$v0`共享，而`$v0`的较低64位与`$f0`共享；其他所有向量寄存器也是如此。

##### 控制状态寄存器 (CSRs)

CSRs只能从特权模式（PLV0）访问：

| 地址 | 完整名称 | 缩写名称 |
|------|----------|----------|
| 0x0  | 当前模式信息 | CRMD |
| 0x1  | 异常前模式信息 | PRMD |
| 0x2  | 扩展单元使能 | EUEN |
| 0x3  | 杂项控制 | MISC |
| 0x4  | 异常配置 | ECFG |
| 0x5  | 异常状态 | ESTAT |
| 0x6  | 异常返回地址 | ERA |
| 0x7  | 故障虚拟地址 | BADV |
| 0x8  | 故障指令字 | BADI |
| 0xC  | 异常入口地址 | EENTRY |
| 0x10 | TLB索引 | TLBIDX |
| 0x11 | TLB条目高位 | TLBEHI |
| 0x12 | TLB条目低位0 | TLBELO0 |
| 0x13 | TLB条目低位1 | TLBELO1 |
| 0x18 | 地址空间标识符 | ASID |
| 0x19 | 下半地址空间全局目录地址 | PGDL |
| 0x1A | 上半地址空间全局目录地址 | PGDH |
| 0x1B | 全局目录地址 | PGD |
| 0x1C | 下半地址空间页表控制 | PWCL |
| 0x1D | 上半地址空间页表控制 | PWCH |
| 0x1E | STLB页大小 | STLBPS |
| 0x1F | 减少虚拟地址配置 | RVACFG |
| 0x20 | CPU标识 | CPUID |
| 0x21 | 特权资源配置1 | PRCFG1 |
| 0x22 | 特权资源配置2 | PRCFG2 |
| 0x23 | 特权资源配置3 | PRCFG3 |
| 0x30+n (0≤n≤15) | 保存数据寄存器 | SAVEn |
| 0x40 | 定时器标识符 | TID |
| 0x41 | 定时器配置 | TCFG |
| 0x42 | 定时器值 | TVAL |
| 0x43 | 定时器计数补偿 | CNTC |
| 0x44 | 定时器中断清除 | TICLR |
| 0x60 | LLBit控制 | LLBCTL |
| 0x80 | 实现特定控制1 | IMPCTL1 |
| 0x81 | 实现特定控制2 | IMPCTL2 |
| 0x88 | TLB刷新异常入口地址 | TLBRENTRY |
| 0x89 | TLB刷新异常故障虚拟地址 | TLBRBADV |
| 0x8A | TLB刷新异常返回地址 | TLBRERA |
| 0x8B | TLB刷新异常保存数据寄存器 | TLBRSAVE |
| 0x8C | TLB刷新异常条目低位0 | TLBRELO0 |
| 0x8D | TLB刷新异常条目低位1 | TLBRELO1 |
| 0x8E | TLB刷新异常条目高位 | TLBEHI |
| 0x8F | TLB刷新异常前模式信息 | TLBRPRMD |
| 0x90 | 机器错误控制 | MERRCTL |
| 0x91 | 机器错误信息1 | MERRINFO1 |
| 0x92 | 机器错误信息2 | MERRINFO2 |
| 0x93 | 机器错误异常入口地址 | MERRENTRY |
| 0x94 | 机器错误异常返回地址 | MERRERA |
| 0x95 | 机器错误异常保存数据寄存器 | MERRSAVE |
| 0x98 | 缓存标签 | CTAG |
| 0x180+n (0≤n≤3) | 直接映射配置窗口n | DMWn |
| 0x200+2n (0≤n≤31) | 性能监控配置n | PMCFGn |
| 0x201+2n (0≤n≤31) | 性能监控总体计数器n | PMCNTn |
| 0x300 | 内存读写监视点总体控制 | MWPC |
| 0x301 | 内存读写监视点总体状态 | MWPS |
| 0x310+8n (0≤n≤7) | 内存读写监视点n配置1 | MWPnCFG1 |
| 0x311+8n (0≤n≤7) | 内存读写监视点n配置2 | MWPnCFG2 |
| 0x312+8n (0≤n≤7) | 内存读写监视点n配置3 | MWPnCFG3 |
| 0x313+8n (0≤n≤7) | 内存读写监视点n配置4 | MWPnCFG4 |
| 0x380 | 指令获取监视点总体控制 | FWPC |
| 0x381 | 指令获取监视点总体状态 | FWPS |
| 0x390+8n (0≤n≤7) | 指令获取监视点n配置1 | FWPnCFG1 |
| 0x391+8n (0≤n≤7) | 指令获取监视点n配置2 | FWPnCFG2 |
| 0x392+8n (0≤n≤7) | 指令获取监视点n配置3 | FWPnCFG3 |
| 0x393+8n (0≤n≤7) | 指令获取监视点n配置4 | FWPnCFG4 |
| 0x500 | 调试寄存器 | DBG |
| 0x501 | 调试异常返回地址 | DERA |
| 0x502 | 调试异常保存数据寄存器 | DSAVE |

ERA、TLBRERA、MERRERA 和 DERA 有时也被称为 EPC、TLBREPC、MERREPC 和 DEPC。

### 基本指令集
#### 指令格式

LoongArch指令为32位宽，属于9种基本指令格式（及其变体）：

| 格式名称 | 组成 |
|----------|------|
| 2R       | Opcode + Rj + Rd |
| 3R       | Opcode + Rk + Rj + Rd |
| 4R       | Opcode + Ra + Rk + Rj + Rd |
| 2RI8     | Opcode + I8 + Rj + Rd |
| 2RI12    | Opcode + I12 + Rj + Rd |
| 2RI14    | Opcode + I14 + Rj + Rd |
| 2RI16    | Opcode + I16 + Rj + Rd |
| 1RI21    | Opcode + I21L + Rj + I21H |
| I26      | Opcode + I26L + I26H |

其中Rd是目标寄存器操作数，而Rj、Rk和Ra（“a”代表“附加”）是源寄存器操作数。I8/I12/I14/I16/I21/I26是相应宽度的立即数操作数。较长的I21和I26在指令字中以分开的较高和较低部分存储，分别标记为“L”和“H”后缀。
指令列表
--------------

为了简洁，此处仅列出指令名称（助记符）；更多详细信息，请参见 :ref:`参考资料 <loongarch-references>`。

1. 算术指令::

    ADD.W SUB.W ADDI.W ADD.D SUB.D ADDI.D
    SLT SLTU SLTI SLTUI
    AND OR NOR XOR ANDN ORN ANDI ORI XORI
    MUL.W MULH.W MULH.WU DIV.W DIV.WU MOD.W MOD.WU
    MUL.D MULH.D MULH.DU DIV.D DIV.DU MOD.D MOD.DU
    PCADDI PCADDU12I PCADDU18I
    LU12I.W LU32I.D LU52I.D ADDU16I.D

2. 位移指令::

    SLL.W SRL.W SRA.W ROTR.W SLLI.W SRLI.W SRAI.W ROTRI.W
    SLL.D SRL.D SRA.D ROTR.D SLLI.D SRLI.D SRAI.D ROTRI.D

3. 位操作指令::

    EXT.W.B EXT.W.H CLO.W CLO.D SLZ.W CLZ.D CTO.W CTO.D CTZ.W CTZ.D
    BYTEPICK.W BYTEPICK.D BSTRINS.W BSTRINS.D BSTRPICK.W BSTRPICK.D
    REVB.2H REVB.4H REVB.2W REVB.D REVH.2W REVH.D BITREV.4B BITREV.8B BITREV.W BITREV.D
    MASKEQZ MASKNEZ

4. 分支指令::

    BEQ BNE BLT BGE BLTU BGEU BEQZ BNEZ B BL JIRL

5. 加载/存储指令::

    LD.B LD.BU LD.H LD.HU LD.W LD.WU LD.D ST.B ST.H ST.W ST.D
    LDX.B LDX.BU LDX.H LDX.HU LDX.W LDX.WU LDX.D STX.B STX.H STX.W STX.D
    LDPTR.W LDPTR.D STPTR.W STPTR.D
    PRELD PRELDX

6. 原子操作指令::

    LL.W SC.W LL.D SC.D
    AMSWAP.W AMSWAP.D AMADD.W AMADD.D AMAND.W AMAND.D AMOR.W AMOR.D AMXOR.W AMXOR.D
    AMMAX.W AMMAX.D AMMIN.W AMMIN.D

7. 屏障指令::

    IBAR DBAR

8. 特殊指令::

    SYSCALL BREAK CPUCFG NOP IDLE ERTN(ERET) DBCL(DBGCALL) RDTIMEL.W RDTIMEH.W RDTIME.D
    ASRTLE.D ASRTGT.D

9. 特权指令::

    CSRRD CSRWR CSRXCHG
    IOCSRRD.B IOCSRRD.H IOCSRRD.W IOCSRRD.D IOCSRWR.B IOCSRWR.H IOCSRWR.W IOCSRWR.D
    CACOP TLBP(TLBSRCH) TLBRD TLBWR TLBFILL TLBCLR TLBFLUSH INVTLB LDDIR LDPTE

虚拟内存
=============

LoongArch 支持直接映射虚拟内存和分页映射虚拟内存。
直接映射虚拟内存由 CSR.DMWn (n=0~3) 配置，它具有简单的虚拟地址 (VA) 和物理地址 (PA) 的关系::

    VA = PA + 固定偏移量

分页映射虚拟内存具有任意的 VA 和 PA 关系，这些关系记录在 TLB 和页表中。LoongArch 的 TLB 包括完全关联的 MTLB（多页大小 TLB）和部分关联的 STLB（单页大小 TLB）。
默认情况下，LA32 的整个虚拟地址空间配置如下：

============ =========================== =============================
名称          地址范围                    属性
============ =========================== =============================
``UVRANGE``  ``0x00000000 - 0x7FFFFFFF`` 分页映射，可缓存，PLV0~3
``KPRANGE0`` ``0x80000000 - 0x9FFFFFFF`` 直接映射，不可缓存，PLV0
``KPRANGE1`` ``0xA0000000 - 0xBFFFFFFF`` 直接映射，可缓存，PLV0
``KVRANGE``  ``0xC0000000 - 0xFFFFFFFF`` 分页映射，可缓存，PLV0
============ =========================== =============================

用户模式 (PLV3) 只能访问 UVRANGE。对于直接映射的 KPRANGE0 和 KPRANGE1，PA 等于 VA 清除位 30~31 后的结果。例如，0x00001000 的不可缓存直接映射 VA 是 0x80001000，而其可缓存直接映射 VA 是 0xA0001000。
默认情况下，LA64 的整个虚拟地址空间配置如下：

============ ====================== ======================================
名称          地址范围              属性
============ ====================== ======================================
``XUVRANGE`` ``0x0000000000000000 - 分页映射，可缓存，PLV0~3
             0x3FFFFFFFFFFFFFFF``
``XSPRANGE`` ``0x4000000000000000 - 直接映射，可缓存 / 不可缓存，PLV0
             0x7FFFFFFFFFFFFFFF``
``XKPRANGE`` ``0x8000000000000000 - 直接映射，可缓存 / 不可缓存，PLV0
             0xBFFFFFFFFFFFFFFF``
``XKVRANGE`` ``0xC000000000000000 - 分页映射，可缓存，PLV0
             0xFFFFFFFFFFFFFFFF``
============ ====================== ======================================

用户模式 (PLV3) 只能访问 XUVRANGE。对于直接映射的 XSPRANGE 和 XKPRANGE，PA 等于 VA 清除位 60~63 后的结果，并且缓存属性由 VA 中的位 60~61 配置：0 表示强序不可缓存，1 表示一致可缓存，2 表示弱序不可缓存。
目前我们只使用 XKPRANGE 进行直接映射，而 XSPRANGE 保留未用。
举例来说：0x00000000_00001000 的强序不可缓存直接映射 VA（在 XKPRANGE 内）是 0x80000000_00001000，一致可缓存直接映射 VA（在 XKPRANGE 内）是 0x90000000_00001000，而弱序不可缓存直接映射 VA（在 XKPRANGE 内）是 0xA0000000_00001000。

龙芯与 LoongArch 的关系
======================================

LoongArch 是一种不同于任何现有架构的精简指令集架构 (RISC)，而龙芯是一系列处理器家族。龙芯包括三个系列：龙芯-1 是 32 位处理器系列，龙芯-2 是低端 64 位处理器系列，龙芯-3 是高端 64 位处理器系列。旧版龙芯基于 MIPS，而新版龙芯则基于 LoongArch。以龙芯-3 为例：龙芯-3A1000/3B1500/3A2000/3A3000/3A4000 是 MIPS 兼容的，而龙芯-3A5000（及其后续版本）都是基于 LoongArch 的。

.. _loongarch-references:

参考资料
==========

龙芯科技有限公司官方网站:

  http://www.loongson.cn/

龙芯及 LoongArch 开发者网站（软件和文档）:

  http://www.loongnix.cn/

  https://github.com/loongson/

  https://loongson.github.io/LoongArch-Documentation/

LoongArch 指令集体系结构文档:

  https://github.com/loongson/LoongArch-Documentation/releases/latest/download/LoongArch-Vol1-v1.10-CN.pdf （中文）

  https://github.com/loongson/LoongArch-Documentation/releases/latest/download/LoongArch-Vol1-v1.10-EN.pdf （英文）

LoongArch ELF psABI 文档:

  https://github.com/loongson/LoongArch-Documentation/releases/latest/download/LoongArch-ELF-ABI-v2.01-CN.pdf （中文）

  https://github.com/loongson/LoongArch-Documentation/releases/latest/download/LoongArch-ELF-ABI-v2.01-EN.pdf （英文）

龙芯及 LoongArch Linux 内核仓库:

  https://git.kernel.org/pub/scm/linux/kernel/git/chenhuacai/linux-loongson.git
