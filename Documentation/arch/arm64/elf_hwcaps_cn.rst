### ARM64 ELF hwcaps 索引

================
ARM64 ELF hwcaps
================

本文档描述了 arm64 ELF hwcaps 的使用和语义。

1. **简介**
   ---------------

   某些硬件或软件特性仅在某些 CPU 实现中可用，或者在特定的内核配置下可用，但在 EL0 层次上没有架构定义的发现机制供用户空间代码使用。内核通过一组称为 hwcaps 的标志来向用户空间暴露这些特性的存在，这些标志通过辅助向量提供。
   
   用户空间软件可以通过获取辅助向量中的 AT_HWCAP 或 AT_HWCAP2 条目，并测试相关的标志是否设置来检测特性，例如：

   ```c
   bool floating_point_is_present(void)
   {
       unsigned long hwcaps = getauxval(AT_HWCAP);
       if (hwcaps & HWCAP_FP)
           return true;

       return false;
   }
   ```

   当软件依赖于由某个 hwcap 描述的特性时，它应该检查相应的 hwcap 标志以验证该特性是否存在，然后再尝试使用该特性。
   
   特性不能通过其他可靠的方式进行探测。当特性不可用时，尝试使用它可能会导致不可预测的行为，并且不保证会给出任何可靠的指示（如 SIGILL）表明该特性不可用。

2. **hwcaps 的解释**
   ------------------------------

   大多数 hwcaps 旨在指示那些通过架构定义的 ID 寄存器（EL0 层次上的用户空间代码无法访问）所描述的特性的存在。这些 hwcaps 根据 ID 寄存器字段定义，并应参考 ARM 架构参考手册 (ARM ARM) 中这些字段的定义来进行解读。
   
   这类 hwcaps 采用以下形式描述：
   
   ```
   由 idreg.field == val 所暗示的功能性
   ```
   
   这类 hwcaps 表示当 idreg.field 的值为 val 时，根据 ARM ARM 定义的特性可用性，但并不表示 idreg.field 恰好等于 val，也不表示其他值的 idreg.field 所暗示功能性的缺失。
   
   其他 hwcaps 可能指示那些不能仅通过 ID 寄存器描述的特性的存在。这类 hwcaps 可以不参考 ID 寄存器进行描述，并可能引用其他文档。

3. **AT_HWCAP 中暴露的 hwcaps**
   ---------------------------------

   - **HWCAP_FP**
     - 由 ID_AA64PFR0_EL1.FP == 0b0000 所暗示的功能性
   - **HWCAP_ASIMD**
     - 由 ID_AA64PFR0_EL1.AdvSIMD == 0b0000 所暗示的功能性
HWCAP_EVTSTRM
    通用定时器配置为以大约10KHz的频率生成事件。

HWCAP_AES
    由 ID_AA64ISAR0_EL1.AES == 0b0001 所暗示的功能。

HWCAP_PMULL
    由 ID_AA64ISAR0_EL1.AES == 0b0010 所暗示的功能。

HWCAP_SHA1
    由 ID_AA64ISAR0_EL1.SHA1 == 0b0001 所暗示的功能。

HWCAP_SHA2
    由 ID_AA64ISAR0_EL1.SHA2 == 0b0001 所暗示的功能。

HWCAP_CRC32
    由 ID_AA64ISAR0_EL1.CRC32 == 0b0001 所暗示的功能。

HWCAP_ATOMICS
    由 ID_AA64ISAR0_EL1.Atomic == 0b0010 所暗示的功能。

HWCAP_FPHP
    由 ID_AA64PFR0_EL1.FP == 0b0001 所暗示的功能。

HWCAP_ASIMDHP
    由 ID_AA64PFR0_EL1.AdvSIMD == 0b0001 所暗示的功能。

HWCAP_CPUID
    EL0 可访问某些 ID 寄存器，具体访问情况如文档 Documentation/arch/arm64/cpu-feature-registers.rst 中所述。
这些ID寄存器可能意味着某些特性的可用性：
HWCAP_ASIMDRDM
    当ID_AA64ISAR0_EL1.RDM等于0b0001时所暗示的功能
HWCAP_JSCVT
    当ID_AA64ISAR1_EL1.JSCVT等于0b0001时所暗示的功能
HWCAP_FCMA
    当ID_AA64ISAR1_EL1.FCMA等于0b0001时所暗示的功能
HWCAP_LRCPC
    当ID_AA64ISAR1_EL1.LRCPC等于0b0001时所暗示的功能
HWCAP_DCPOP
    当ID_AA64ISAR1_EL1.DPB等于0b0001时所暗示的功能
HWCAP_SHA3
    当ID_AA64ISAR0_EL1.SHA3等于0b0001时所暗示的功能
HWCAP_SM3
    当ID_AA64ISAR0_EL1.SM3等于0b0001时所暗示的功能
HWCAP_SM4
    当ID_AA64ISAR0_EL1.SM4等于0b0001时所暗示的功能
HWCAP_ASIMDDP
    当ID_AA64ISAR0_EL1.DP等于0b0001时所暗示的功能
HWCAP_SHA512  
    由ID_AA64ISAR0_EL1.SHA2 == 0b0010所暗示的功能

HWCAP_SVE  
    由ID_AA64PFR0_EL1.SVE == 0b0001所暗示的功能

HWCAP_ASIMDFHM  
    由ID_AA64ISAR0_EL1.FHM == 0b0001所暗示的功能

HWCAP_DIT  
    由ID_AA64PFR0_EL1.DIT == 0b0001所暗示的功能

HWCAP_USCAT  
    由ID_AA64MMFR2_EL1.AT == 0b0001所暗示的功能

HWCAP_ILRCPC  
    由ID_AA64ISAR1_EL1.LRCPC == 0b0010所暗示的功能

HWCAP_FLAGM  
    由ID_AA64ISAR0_EL1.TS == 0b0001所暗示的功能

HWCAP_SSBS  
    由ID_AA64PFR1_EL1.SSBS == 0b0010所暗示的功能

HWCAP_SB  
    由ID_AA64ISAR1_EL1.SB == 0b0001所暗示的功能

HWCAP_PACA  
    由ID_AA64ISAR1_EL1.APA == 0b0001或ID_AA64ISAR1_EL1.API == 0b0001所暗示的功能，如在
    文档Documentation/arch/arm64/pointer-authentication.rst中所述。
HWCAP_PACG  
    如《Documentation/arch/arm64/pointer-authentication.rst》中所述，由ID_AA64ISAR1_EL1.GPA == 0b0001 或 ID_AA64ISAR1_EL1.GPI == 0b0001 所暗示的功能。

HWCAP2_DCPODP  
    由ID_AA64ISAR1_EL1.DPB == 0b0010 所暗示的功能。

HWCAP2_SVE2  
    由ID_AA64ZFR0_EL1.SVEver == 0b0001 所暗示的功能。

HWCAP2_SVEAES  
    由ID_AA64ZFR0_EL1.AES == 0b0001 所暗示的功能。

HWCAP2_SVEPMULL  
    由ID_AA64ZFR0_EL1.AES == 0b0010 所暗示的功能。

HWCAP2_SVEBITPERM  
    由ID_AA64ZFR0_EL1.BitPerm == 0b0001 所暗示的功能。

HWCAP2_SVESHA3  
    由ID_AA64ZFR0_EL1.SHA3 == 0b0001 所暗示的功能。

HWCAP2_SVESM4  
    由ID_AA64ZFR0_EL1.SM4 == 0b0001 所暗示的功能。

HWCAP2_FLAGM2  
    由ID_AA64ISAR0_EL1.TS == 0b0010 所暗示的功能。

HWCAP2_FRINT  
    由ID_AA64ISAR1_EL1.FRINTTS == 0b0001 所暗示的功能。
HWCAP2_SVEI8MM  
    由ID_AA64ZFR0_EL1.I8MM == 0b0001所暗示的功能

HWCAP2_SVEF32MM  
    由ID_AA64ZFR0_EL1.F32MM == 0b0001所暗示的功能

HWCAP2_SVEF64MM  
    由ID_AA64ZFR0_EL1.F64MM == 0b0001所暗示的功能

HWCAP2_SVEBF16  
    由ID_AA64ZFR0_EL1.BF16 == 0b0001所暗示的功能

HWCAP2_I8MM  
    由ID_AA64ISAR1_EL1.I8MM == 0b0001所暗示的功能

HWCAP2_BF16  
    由ID_AA64ISAR1_EL1.BF16 == 0b0001所暗示的功能

HWCAP2_DGH  
    由ID_AA64ISAR1_EL1.DGH == 0b0001所暗示的功能

HWCAP2_RNG  
    由ID_AA64ISAR0_EL1.RNDR == 0b0001所暗示的功能

HWCAP2_BTI  
    由ID_AA64PFR1_EL1.BT == 0b0001所暗示的功能

HWCAP2_MTE  
    由ID_AA64PFR1_EL1.MTE == 0b0010所暗示的功能，如文档中描述的那样  
    文档位置: Documentation/arch/arm64/memory-tagging-extension.rst
HWCAP2_ECV  
    由ID_AA64MMFR0_EL1.ECV == 0b0001所暗示的功能

HWCAP2_AFP  
    由ID_AA64MMFR1_EL1.AFP == 0b0001所暗示的功能

HWCAP2_RPRES  
    由ID_AA64ISAR2_EL1.RPRES == 0b0001所暗示的功能

HWCAP2_MTE3  
    由ID_AA64PFR1_EL1.MTE == 0b0011所暗示的功能，如文档  
    `Documentation/arch/arm64/memory-tagging-extension.rst`中所述

HWCAP2_SME  
    由ID_AA64PFR1_EL1.SME == 0b0001所暗示的功能，如文档  
    `Documentation/arch/arm64/sme.rst`中所述

HWCAP2_SME_I16I64  
    由ID_AA64SMFR0_EL1.I16I64 == 0b1111所暗示的功能

HWCAP2_SME_F64F64  
    由ID_AA64SMFR0_EL1.F64F64 == 0b1所暗示的功能

HWCAP2_SME_I8I32  
    由ID_AA64SMFR0_EL1.I8I32 == 0b1111所暗示的功能

HWCAP2_SME_F16F32  
    由ID_AA64SMFR0_EL1.F16F32 == 0b1所暗示的功能

HWCAP2_SME_B16F32  
    由ID_AA64SMFR0_EL1.B16F32 == 0b1所暗示的功能
HWCAP2_SME_F32F32  
    由ID_AA64SMFR0_EL1.F32F32 == 0b1所暗示的功能

HWCAP2_SME_FA64  
    由ID_AA64SMFR0_EL1.FA64 == 0b1所暗示的功能

HWCAP2_WFXT  
    由ID_AA64ISAR2_EL1.WFXT == 0b0010所暗示的功能

HWCAP2_EBF16  
    由ID_AA64ISAR1_EL1.BF16 == 0b0010所暗示的功能

HWCAP2_SVE_EBF16  
    由ID_AA64ZFR0_EL1.BF16 == 0b0010所暗示的功能

HWCAP2_CSSC  
    由ID_AA64ISAR2_EL1.CSSC == 0b0001所暗示的功能

HWCAP2_RPRFM  
    由ID_AA64ISAR2_EL1.RPRFM == 0b0001所暗示的功能

HWCAP2_SVE2P1  
    由ID_AA64ZFR0_EL1.SVEver == 0b0010所暗示的功能

HWCAP2_SME2  
    由ID_AA64SMFR0_EL1.SMEver == 0b0001所暗示的功能

HWCAP2_SME2P1  
    由ID_AA64SMFR0_EL1.SMEver == 0b0010所暗示的功能
这些标识符代表了特定的硬件功能，它们与ARM架构处理器中的特定寄存器位相关。下面是对这些标识符及其含义的中文翻译：

HWCAP2_SMEI16I32  
    由 `ID_AA64SMFR0_EL1.I16I32` 的值为 `0b0101` 所暗示的功能。

HWCAP2_SMEBI32I32  
    由 `ID_AA64SMFR0_EL1.BI32I32` 的值为 `0b1` 所暗示的功能。

HWCAP2_SMEB16B16  
    由 `ID_AA64SMFR0_EL1.B16B16` 的值为 `0b1` 所暗示的功能。

HWCAP2_SMEF16F16  
    由 `ID_AA64SMFR0_EL1.F16F16` 的值为 `0b1` 所暗示的功能。

HWCAP2_MOPS  
    由 `ID_AA64ISAR2_EL1.MOPS` 的值为 `0b0001` 所暗示的功能。

HWCAP2_HBC  
    由 `ID_AA64ISAR2_EL1.BC` 的值为 `0b0001` 所暗示的功能。

HWCAP2_SVE_B16B16  
    由 `ID_AA64ZFR0_EL1.B16B16` 的值为 `0b0001` 所暗示的功能。

HWCAP2_LRCPC3  
    由 `ID_AA64ISAR1_EL1.LRCPC` 的值为 `0b0011` 所暗示的功能。

HWCAP2_LSE128  
    由 `ID_AA64ISAR0_EL1.Atomic` 的值为 `0b0011` 所暗示的功能。

HWCAP2_FPMR  
    由 `ID_AA64PFR2_EL1.FMR` 的值为 `0b0001` 所暗示的功能。

HWCAP2_LUT  
    由 `ID_AA64ISAR2_EL1.LUT` 的值为 `0b0001` 所暗示的功能。

HWCAP2_FAMINMAX  
    由 `ID_AA64ISAR3_EL1.FAMINMAX` 的值为 `0b0001` 所暗示的功能。

HWCAP2_F8CVT  
    由 `ID_AA64FPFR0_EL1.F8CVT` 的值为 `0b1` 所暗示的功能。

HWCAP2_F8FMA  
    由 `ID_AA64FPFR0_EL1.F8FMA` 的值为 `0b1` 所暗示的功能。

请注意，这里的每个标识符都指向ARM架构中某个特定寄存器的一个或多个位，这些位的值指示着是否支持某些特定的功能。
HWCAP2_F8DP4  
    当ID_AA64FPFR0_EL1.F8DP4的值为0b1时所暗示的功能

HWCAP2_F8DP2  
    当ID_AA64FPFR0_EL1.F8DP2的值为0b1时所暗示的功能

HWCAP2_F8E4M3  
    当ID_AA64FPFR0_EL1.F8E4M3的值为0b1时所暗示的功能

HWCAP2_F8E5M2  
    当ID_AA64FPFR0_EL1.F8E5M2的值为0b1时所暗示的功能

HWCAP2_SME_LUTV2  
    当ID_AA64SMFR0_EL1.LUTv2的值为0b1时所暗示的功能

HWCAP2_SME_F8F16  
    当ID_AA64SMFR0_EL1.F8F16的值为0b1时所暗示的功能

HWCAP2_SME_F8F32  
    当ID_AA64SMFR0_EL1.F8F32的值为0b1时所暗示的功能

HWCAP2_SME_SF8FMA  
    当ID_AA64SMFR0_EL1.SF8FMA的值为0b1时所暗示的功能

HWCAP2_SME_SF8DP4  
    当ID_AA64SMFR0_EL1.SF8DP4的值为0b1时所暗示的功能

HWCAP2_SME_SF8DP2  
    当ID_AA64SMFR0_EL1.SF8DP2的值为0b1时所暗示的功能
HWCAP2_SME_SF8DP4  
ID_AA64SMFR0_EL1.SF8DP4 == 0b1 所暗示的功能  
4. 未使用的 AT_HWCAP 位  
----------------------------  

为了与用户空间进行互操作，内核保证返回的 AT_HWCAP 的第 62 位和第 63 位总是为 0。
