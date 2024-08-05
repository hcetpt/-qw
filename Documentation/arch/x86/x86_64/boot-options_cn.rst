SPDX 许可证标识符: GPL-2.0

===========================
AMD64 特定启动选项
===========================

存在许多其他选项（通常在驱动程序文档中有说明），但此处仅列出与 AMD64 相关的选项。

机器检查
===========================
请参阅 `Documentation/arch/x86/x86_64/machinecheck.rst` 了解 sysfs 运行时可调参数。
mce=off
		禁用机器检查
mce=no_cmci
		禁用 Intel 处理器支持的 CMCI（Corrected Machine Check Interrupt，校正的机器检查中断）。通常不推荐禁用此功能，但如果硬件出现问题时，这可能会有所帮助。
请注意，没有 CMCI 时可能会遇到更多问题，因为共享的错误寄存器可能导致重复的日志记录。
mce=dont_log_ce
		不对已校正的错误进行日志记录。所有报告为已校正的事件将被操作系统静默清除。
如果对任何已校正的错误都不感兴趣，则此选项会很有用。
mce=ignore_ce
		禁用针对已校正错误的功能，例如轮询计时器和 CMCI。所有报告为已校正的事件不会被操作系统清除，并保留在其错误寄存器中。
通常不推荐禁用此功能，但是如果存在检查/清除已校正错误的代理（例如 BIOS 或硬件监控应用程序）与操作系统的错误处理发生冲突，并且无法停用该代理，则此选项会有所帮助。
mce=no_lmce
		不选择本地 MCE 传输。使用传统的广播 MCE 的方法。
mce=bootlog
		启用记录从启动过程中遗留下来的机器检查。
默认情况下在AMD Fam10h及更早的系统上禁用，因为某些BIOS会留下错误的信息。
如果你的BIOS不这样做，最好启用它以确保记录导致重启的所有机器检查事件。在Intel系统上，默认情况下它是启用的。
mce=nobootlog
    禁用启动时的机器检查日志记录
mce=monarchtimeout (数字)
    monarchtimeout:
    设置在机器检查时等待其他CPU的时间（单位：微秒）。设置为0表示禁用。
mce=bios_cmci_threshold
    不覆盖BIOS设置的CMCI阈值。此启动选项防止Linux覆盖由BIOS设置的CMCI阈值。如果不使用此选项，Linux总是将CMCI阈值设置为1。如果BIOS为内存错误设置了阈值，则启用此选项可能会降低内存预测故障分析的有效性，因为我们无法看到所有错误的详细信息。
mce=recovery
    强制启用可恢复的机器检查代码路径

   nomce （为了与i386兼容）
    与mce=off相同

   其他所有内容现在都在sysfs中
APICs
=====

   apic
   使用IO-APIC。默认设置。

   noapic
   不使用IO-APIC
disableapic
   不使用本地APIC

   nolapic
     不使用本地APIC（为与i386兼容的别名）

   pirq=..
请参阅Documentation/arch/x86/i386/IO-APIC.rst

   noapictimer
   不设置APIC计时器

   no_timer_check
   不检查IO-APIC计时器。这可以解决一些主板上因计时器初始化不正确的问题
apicpmtimer
   使用pmtimer进行APIC计时器校准。意味着启用apicmaintimer。当你的PIT计时器完全损坏时很有用。
### 定时
####

  notsc  
    已废弃，取而代之使用 `tsc=unstable`  
  nohpet  
    不要使用 HPET 计时器  
### 空闲循环
####

  idle=poll  
    在空闲循环中不要使用HLT进行节能操作，而是轮询调度事件。这会让CPU消耗更多电力，但在多处理器基准测试中可能会获得略微更好的性能。它还使基于性能计数器的一些性能剖析更准确。  
请注意，在支持 MONITOR/MWAIT（如 Intel EM64T 处理器）的系统上，此选项与普通空闲循环相比在性能上没有优势。  
它也可能与超线程产生不良交互。  
### 重启
####

   reboot=b[ios] | t[riple] | k[bd] | a[cpi] | e[fi] | p[ci] [, [w]arm | [c]old]  
      bios  
        使用 CPU 的重启向量进行热重置  
      warm  
        不设置冷重启标志  
      cold  
        设置冷重启标志  
      triple  
        强制触发三重故障（初始化）  
      kbd  
        使用键盘控制器进行冷重启（默认）  
      acpi  
        使用 ACPI 表中的 RESET_REG 进行重启。如果未配置 ACPI 或 ACPI 重启不起作用，则重启路径会尝试使用键盘控制器进行重启  
      efi  
        使用 EFI 的 reset_system 运行时服务进行重启。如果未配置 EFI 或 EFI 重启不起作用，则重启路径会尝试使用键盘控制器进行重启  
      pci  
        通过写入 PCI 配置空间寄存器 0xcf9 触发重启  
使用热重启将更快，特别是在大内存系统上，因为 BIOS 不会执行内存检查。  
缺点是并非所有硬件都会在重启时完全重新初始化，因此某些系统可能会遇到启动问题。
### 重启相关选项

#### `reboot=force`
在重启时不阻止其他CPU的运行。这在某些情况下可以使重启过程更加可靠。

#### `reboot=default`
系统内置了一些针对特定平台的特殊处理逻辑，你可能会看到这样的信息：
“检测到`<name>`系列主板。为重启选择`<type>`类型。”
如果你认为这种特殊处理有误（例如，你使用的是更新的BIOS或更新的主板），使用此选项将忽略内置的特殊处理表，并采用通用默认重启动作。

### NUMA 相关选项

#### `numa=off`
仅设置一个覆盖所有内存的NUMA节点。

#### `numa=noacpi`
不解析SRAT表以进行NUMA配置。

#### `numa=nohmat`
不解析HMAT表以进行NUMA配置，也不进行软预留内存分区。

#### `numa=fake=<size>[MG]`
如果作为内存单位给出，则用大小为`<size>`的节点填充整个系统的RAM，这些节点在物理节点之间交错分布。

#### `numa=fake=<N>`
如果作为整数给出，则用`<N>`个假节点填充整个系统的RAM，这些节点在物理节点之间交错分布。

#### `numa=fake=<N>U`
如果作为整数后跟`U`给出，则将每个物理节点划分为`<N>`个模拟节点。

### ACPI 相关选项

#### `acpi=off`
不启用ACPI。

#### `acpi=ht`
使用ACPI引导表解析，但不启用ACPI解释器。

#### `acpi=force`
强制启用ACPI（目前不需要）。

#### `acpi=strict`
禁用超出规范的ACPI补救措施。

#### `acpi_sci={edge,level,high,low}`
设置ACPI SCI中断。

#### `acpi=noirq`
不路由中断。

#### `acpi=nocmcff`
禁用纠正错误时的固件优先模式。这会禁用解析HEST CMC错误源以检查固件是否设置了FF标志。这可能导致重复报告纠正后的错误。
### PCI (外围部件互连)

```
pci=off
```
- 不使用 PCI

```
pci=conf1
```
- 使用 conf1 访问方式

```
pci=conf2
```
- 使用 conf2 访问方式

```
pci=rom
```
- 分配 ROM

```
pci=assign-busses
```
- 分配总线

```
pci=irqmask=MASK
```
- 将 PCI 中断掩码设置为 MASK

```
pci=lastbus=NUMBER
```
- 扫描至 NUMBER 总线，无论 MPT 表如何定义

```
pci=noacpi
```
- 不使用 ACPI 来设置 PCI 中断路由

### I/O 内存管理单元 (IOMMU)
#### 存在多种 x86-64 PCI-DMA 映射实现方案，例如：

1. `<kernel/dma/direct.c>`: 完全不使用硬件/软件 IOMMU（例如：因为内存小于 3GB）
   - 内核启动消息: "PCI-DMA: 禁用 IOMMU"

2. `<arch/x86/kernel/amd_gart_64.c>`: 基于 AMD GART 的硬件 IOMMU
   - 内核启动消息: "PCI-DMA: 使用 GART IOMMU"

3. `<arch/x86_64/kernel/pci-swiotlb.c>`: 软件 IOMMU 实现。例如，在系统中没有硬件 IOMMU 且需要使用它时（例如：内存大于 3GB 或者内核被指示使用它 `iommu=soft`）
   - 内核启动消息: "PCI-DMA: 使用软件跳转缓冲区进行 IO (SWIOTLB)"

```
iommu=[<size>][,noagp][,off][,force][,noforce]
[,memaper[=<order>]][,merge][,fullflush][,nomerge]
[,noaperture]
```

#### 通用 IOMMU 选项：

- `off`
  - 不初始化和使用任何类型的 IOMMU

- `noforce`
  - 当不需要时，不要强制使用硬件 IOMMU。（默认）

- `force`
  - 即使实际上并不需要（例如：内存小于 3GB）也要强制使用硬件 IOMMU
使用软件缓存反弹（SWIOTLB）（对于 Intel 机器是默认选项）。这可以用来防止使用可用的硬件 IOMMU。

仅与 AMD GART 硬件 IOMMU 相关的 iommu 选项：

    <size>
      以字节为单位设置重映射区域的大小。
allowed
      覆写针对特定芯片组的 iommu 关闭规避措施。
fullflush
      在每次分配时刷新 IOMMU（默认）。
nofullflush
      不使用 IOMMU 的全刷新。
memaper[=<order>]
      在 RAM 上分配一个大小为 32MB<<(order) 的独立孔径（默认：order=1，即 64MB）。
merge
      执行分散-聚集（SG）合并。意味着启用 "force"（实验性功能）。
nomerge
      不执行分散-聚集（SG）合并。
noaperture
      请求 IOMMU 不要接触 AGP 的孔径。
noagp
      不初始化 AGP 驱动程序并使用全孔径。
### 翻译成中文：

#### 惊慌
在 IOMMU 超载时总是惊慌
IOMMU 选项仅与软件缓存缓冲（SWIOTLB）IOMMU 实现相关：

    swiotlb=<slots>[,force,noforce]
      <slots>
        预先为软件 IO 缓存缓冲预留指定数量的 2K 空槽
force
        强制所有 IO 通过软件 TLB
noforce
        不初始化软件 TLB
#### 各种杂项设置
=============

  nogbpages
    不使用 GB 页面进行内核直接映射
gbpages
    使用 GB 页面进行内核直接映射
#### AMD SEV (安全加密虚拟化)
=========================================
与 AMD SEV 相关的选项，通过以下格式指定：

::

   sev=option1[,option2]

可用的选项包括：

   debug
     启用调试消息
