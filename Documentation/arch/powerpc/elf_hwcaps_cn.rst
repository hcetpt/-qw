### POWERPC ELF HWCAPs

#### 1. 引言

一些硬件或软件特性仅在某些CPU实现中可用，或者需要特定的内核配置，但用户空间代码没有其他发现这些特性的机制。内核通过一组称为HWCAP的标志向用户空间暴露这些特性的存在，这些标志通过辅助向量传递。
用户空间软件可以通过获取辅助向量中的`AT_HWCAP`或`AT_HWCAP2`条目，并检查相关标志是否设置来测试特性，例如：

```c
bool floating_point_is_present(void)
{
    unsigned long HWCAPs = getauxval(AT_HWCAP);
    if (HWCAPs & PPC_FEATURE_HAS_FPU)
        return true;

    return false;
}
```

如果软件依赖于由HWCAP描述的一个特性，它应该在尝试使用该特性之前检查相关的HWCAP标志以确认该特性是否存在。
HWCAP是检测特性存在与否的首选方法，而不是通过其他可能不可靠或可能导致不可预测行为的方式进行探测。
针对特定平台开发的软件不一定必须测试所需或隐含的特性。例如，如果程序要求FPU、VMX、VSX等特性，则不需要测试这些HWCAPs，而且如果编译器生成了依赖这些特性的代码，那么可能无法进行这样的测试。

#### 2. 设施

Power ISA使用“设施”这一术语来描述一类指令、寄存器、中断等。设施的存在与否表明这类功能是否可以使用，但具体的细节取决于ISA版本。例如，如果VSX设施可用，则在v3.0B和v3.1B ISA版本之间可使用的VSX指令会有所不同。

#### 3. 类别

Power ISA在v3.0之前的版本使用“类别”来描述某些指令类和操作模式，它们可能是可选的或互斥的。HWCAP标志的确切含义可能取决于上下文，例如，BOOKE特性的存在意味着服务器类别并未实现。

#### 4. HWCAP分配

HWCAP的分配遵循Power Architecture 64-Bit ELF V2 ABI Specification（这将反映在内核的uapi头文件中）。

#### 5. 在AT_HWCAP中暴露的HWCAPs

- `PPC_FEATURE_32`
  - 32位CPU

- `PPC_FEATURE_64`
  - 64位CPU（用户空间可能运行在32位模式下）

- `PPC_FEATURE_601_INSTR`
  - 处理器为PowerPC 601
自提交 f0ed73f3fa2c ("powerpc: 移除 PowerPC 601") 后，内核中未再使用：

PPC_FEATURE_HAS_ALTIVEC  
    表示向量（又名 Altivec, VMX）功能可用。

PPC_FEATURE_HAS_FPU  
    表示浮点运算功能可用。

PPC_FEATURE_HAS_MMU  
    表示内存管理单元存在且已启用。

PPC_FEATURE_HAS_4xxMAC  
    表示处理器属于 40x 或 44x 系列。

PPC_FEATURE_UNIFIED_CACHE  
    表示处理器具有统一的 L1 缓存用于指令和数据，如 NXP e200 中所见。
自从提交 39c8bf2b3cc1 ("powerpc: 停用 e200 核心 (mpc555x 处理器)") 后，内核中未再使用。

PPC_FEATURE_HAS_SPE  
    表示信号处理引擎功能可用。

PPC_FEATURE_HAS_EFP_SINGLE  
    表示嵌入式浮点单精度操作可用。

PPC_FEATURE_HAS_EFP_DOUBLE  
    表示嵌入式浮点双精度操作可用。

PPC_FEATURE_NO_TB  
    表示时间基设施（mftb 指令）不可用。
这是特定于 601 的硬件功能标志，因此如果通过其他硬件功能标志或其他方式已经确定运行中的处理器不是 601，则在使用时间基之前无需检测此位。
这些是与PowerPC架构相关的处理器特性标志。下面是翻译后的中文版本：

- `PPC_FEATURE_POWER4`  
  处理器为 POWER4 或 PPC970/FX/MP。
  自从提交 `471d7ff8b51b`（"powerpc/64s: 移除对 POWER4 的支持"）后，内核中不再支持 POWER4。

- `PPC_FEATURE_POWER5`  
  处理器为 POWER5。

- `PPC_FEATURE_POWER5_PLUS`  
  处理器为 POWER5+。

- `PPC_FEATURE_CELL`  
  处理器为 Cell。

- `PPC_FEATURE_BOOKE`  
  处理器实现了嵌入式类别（"BookE"）架构。

- `PPC_FEATURE_SMT`  
  处理器实现了同时多线程（SMT）。

- `PPC_FEATURE_ICACHE_SNOOP`  
  处理器的指令缓存与数据缓存保持一致性，并且可以通过指令存储实现与数据存储的一致性以执行指令，例如在 POWER9 处理器用户手册中的 4.6.2.2 节“指令缓存块无效（icbi）”描述的过程：
  ```
  sync
  icbi (任一地址)
  isync
  ```

- `PPC_FEATURE_ARCH_2_05`  
  处理器支持 v2.05 用户级架构。支持更晚架构的处理器不会设置此特性。

- `PPC_FEATURE_PA6T`  
  处理器为 PA6T。

- `PPC_FEATURE_HAS_DFP`  
  支持 DFP 功能。

- `PPC_FEATURE_POWER6_EXT`  
  处理器为 POWER6。
以下是提供的英文描述翻译成中文：

### PPC_FEATURE_ARCH_2_06
处理器支持v2.06用户级架构。支持后续架构的处理器也会设置此特性。

### PPC_FEATURE_HAS_VSX
VSX设施可用。

### PPC_FEATURE_PSERIES_PERFMON_COMPAT
处理器支持在0xE0-0xFF范围内的体系结构PMU事件。

### PPC_FEATURE_TRUE_LE
处理器支持真正的字节序小端模式。

### PPC_FEATURE_PPC_LE
处理器支持“PowerPC 小端字节序”，该模式通过地址转换使得存储访问表现为小端字节序，但数据以一种不适合其他非此模式运行代理访问的格式存储。

### 在AT_HWCAP2中暴露的HWCAPs

#### PPC_FEATURE2_ARCH_2_07
处理器支持v2.07用户级架构。支持后续架构的处理器也会设置此特性。

#### PPC_FEATURE2_HTM
事务内存特性可用。

#### PPC_FEATURE2_DSCR
DSCR设施可用。

#### PPC_FEATURE2_EBB
EBB设施可用。

#### PPC_FEATURE2_ISEL
isel指令可用。此特性已被ARCH_2_07及后续版本取代。
以下是您提供的英文文本翻译成中文：

PPC_FEATURE2_TAR  
    支持TAR功能

PPC_FEATURE2_VEC_CRYPTO  
    支持v2.07版本的密码学指令

PPC_FEATURE2_HTM_NOSC  
    如果在事务状态下调用系统调用，则会失败，详情请参阅  
    文档/arch/powerpc/syscall64-abi.rst

PPC_FEATURE2_ARCH_3_00  
    处理器支持v3.0B/v3.0C用户级架构。支持后续架构的处理器也会设置此特性

PPC_FEATURE2_HAS_IEEE128  
    支持IEEE 128位二进制浮点数，通过VSX四精度指令和数据类型实现

PPC_FEATURE2_DARN  
    支持darn指令

PPC_FEATURE2_SCV  
    可以使用scv 0指令进行系统调用，详情请参阅  
    文档/arch/powerpc/syscall64-abi.rst

PPC_FEATURE2_HTM_NO_SUSPEND  
    支持有限的事务内存功能，但不支持挂起，详情请参阅  
    文档/arch/powerpc/transactional_memory.rst

PPC_FEATURE2_ARCH_3_1  
    处理器支持v3.1用户级架构。支持后续架构的处理器也会设置此特性

PPC_FEATURE2_MMA  
    支持MMA功能
