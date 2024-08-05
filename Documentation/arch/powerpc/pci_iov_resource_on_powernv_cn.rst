PCI Express I/O 虚拟化资源在 Powerenv 上的应用
===================================================

杨威 <weiyang@linux.vnet.ibm.com>

本杰明·赫伦施密特 <benh@au1.ibm.com>

比约恩·海尔加斯 <bhelgaas@google.com>

2014 年 8 月 26 日

本文档描述了 PowerKVM 中针对 PCI 内存映射 I/O (MMIO) 资源大小和分配的硬件需求，以及通用 PCI 代码如何处理这些需求。前两部分介绍了分区端点的概念及其在 P8 (IODA2) 上的实现。接下来的两部分讨论了在 IODA2 上启用 SRIOV 的考虑因素。

1. 分区端点简介
=================

分区端点 (Partitionable Endpoint, PE) 是一种将与设备或一组设备相关的各种资源进行分组的方法，以提供分区间的隔离（例如，DMA、MSI 等过滤）并提供一种机制来冻结导致错误的设备，以限制不良数据传播的可能性。
在硬件中存在一个 PE 状态表，其中为每个 PE 包含一对“冻结”状态位（一个用于 MMIO，一个用于 DMA，它们一起设置但可以独立清除）。
当一个 PE 被冻结时，所有方向上的存储操作都会被丢弃，所有加载操作返回全 1 的值。MSI 也会被阻止。还有一些其他的状态信息记录了导致冻结的错误详情等，但这些不是最关键的部分。
有趣的是 PCIe 事务（MMIO、DMA 等）是如何与相应的 PE 匹配的。
以下部分提供了我们在 P8 (IODA2) 上所具有的大致描述。请记住，这些都是针对每个 PHB (PCI 主机桥接器) 的。每个 PHB 都是一个完全独立的硬件实体，复制了整个逻辑，因此拥有自己的 PE 集合等。

2. P8 (IODA2) 上的分区端点实现
================================

P8 支持每个 PHB 最多 256 个分区端点。
* 入向

    对于 DMA、MSI 和入向 PCIe 错误消息，我们有一个表格（在内存中但由芯片在硬件层面访问），该表格直接对应 PCIe RID (总线/设备/功能) 和 PE 编号。
我们称这个表为 RTT (Routing Table)。
- 对于 DMA，我们为每个 PE 提供了一个完整的地址空间，它可以包含两个“窗口”，这取决于 PCI 地址第 59 位的值。
每个窗口都可以通过"TCE表"（IOMMU转换表）进行重映射配置，该表具有多种可配置特性，这里不作详细描述。
- 对于MSI中断，我们在地址空间中有两个窗口（一个位于32位空间的顶部，另一个则更高），通过地址和MSI值的组合，可以触发每座桥上的2048个中断之一。在中断控制器描述表中还有一个PE#（处理单元号），它与从RTT（远程触发表）获取的PE#进行比较以“授权”设备发出特定的中断。
- 错误消息仅使用RTT。
* 外发。这是最棘手的部分。
像其他PCI主机桥一样，Power8 IODA2 PHB支持从CPU地址空间到PCI地址空间的“窗口”。有一个M32窗口和十六个M64窗口。它们有不同的特性。
首先，它们有一些共同点：它们将CPU地址空间的一个可配置部分转发到PCIe总线，并且其大小必须是自然对齐的2的幂。除此之外，它们各有不同：

    - M32窗口：
      
      * 大小限制为4GB。
* 去掉地址中的高位（高于窗口大小的部分），并用一个可配置值替换。这通常用于生成32位PCIe访问。我们会在启动时从固件配置这个窗口，并且在Linux中不再对其进行修改；通常它被设置为将2GB的地址空间从CPU转发到PCIe，即0x8000_0000至0xffff_ffff。（注：实际上最上面的64KB是为MSI保留的，但这目前不是问题；我们只需要确保Linux不会在那里分配任何资源即可，M32逻辑会忽略这一点，即使我们尝试这样做，它也会在该空间内转发数据）
* 它被分为256个等大小的段。芯片中的一个表将每个段映射到一个PE#。这使得MMIO空间的部分可以按段粒度分配给PE。对于一个2GB的窗口，段粒度为2GB/256 = 8MB。
现在，这就是我们在Linux中今天使用的“主要”窗口（排除SR-IOV）。我们基本上利用了这样一个技巧，即迫使桥接器的MMIO窗口与段对齐/粒度相匹配，以便桥后方的空间可以被分配给一个PE。
理想情况下，我们希望能够让单个功能处于不同的PE中，但这意味着需要采用一种完全不同的地址分配方案，在这种方案中，单个功能的BAR（基址寄存器）可以“组合”在一起，以适应一个或多个段。
M64 窗口：

      * 必须至少为 256MB 大小
* 不进行地址转换（PCIe 上的地址与 PowerBus 上的地址相同）。有一种方法可以设置未通过 PowerBus 传输的最高 14 位，但我们并未使用这种方法。
* 可以配置为分段。当不分段时，我们可以为整个窗口指定 PE 编号。当分段时，一个窗口有 256 个分段；但是，并没有将分段映射到 PE 编号的表。分段编号 *就是* PE 编号。
* 支持重叠。如果一个地址被多个窗口覆盖，则定义了确定适用哪个窗口的顺序。

我们有代码（相比 M32 的内容来说相对较新），用于利用这些特性处理 64 位空间中的大 BAR：

    我们配置了一个 M64 窗口，以覆盖由固件分配给 PHB 地址空间的整个区域（大约 64GB，忽略 M32 的空间，它来自不同的“预留”）。我们将其配置为分段。
然后我们像处理 M32 一样使用桥接对齐技巧来匹配那些巨大的分段。
由于我们无法重新映射，我们有两个额外的限制：

    - 我们在分配完 64 位空间后才进行 PE 编号分配，因为我们使用的地址直接决定了 PE 编号。之后，我们更新使用 32 位和 64 位空间的设备的 M32 PE 编号，或者为仅使用 32 位空间的设备分配剩余的 PE 编号。
- 我们不能在硬件中“组合”分段，因此如果一个设备使用了不止一个分段，我们最终会有不止一个 PE 编号。有一个硬件机制可以使冻结状态级联到“伙伴”PE，但这仅适用于 PCIe 错误消息（通常用于冻结交换机时也冻结其所有子节点）。所以我们用软件实现这一点。在这种情况下，EEH 的效果会有所损失，但这是我们找到的最佳方案。所以当任何 PE 冻结时，我们也冻结该“域”的其他 PE。这样就引入了“主 PE”的概念，即用于 DMA、MSI 等操作的 PE，以及“次级 PE”，用于其余 M64 分段的 PE。
我们希望研究使用额外的 M64 窗口以“单一 PE”模式叠加在特定 BAR 上的方法来解决上述问题，例如对于具有非常大的 BAR 的设备，如 GPU。这似乎合理，但我们尚未实施。
3. PowerKVM 中 SR-IOV 的考虑因素
========================================

  * SR-IOV 背景

    PCIe 的 SR-IOV 特性允许单个物理功能（PF）支持多个虚拟功能（VF）。PF 的 SR-IOV 功能寄存器控制 VF 的数量及其是否启用。
When VFs are enabled, they appear in Configuration Space similar to regular PCI devices, but the BARs within the VF configuration space headers are unique. For a non-VF device, software uses the BARs in the configuration space header to determine the BAR sizes and assign addresses to them. For VF devices, software uses VF BAR registers within the *PF* SR-IOV Capability to discover sizes and assign addresses. The BARs in the VF's configuration space header are read-only and set to zero.

When a VF BAR in the PF SR-IOV Capability is configured, it sets the base address for all corresponding VF(n) BARs. For example, if the PF SR-IOV Capability is configured to support eight VFs and includes a 1MB VF BAR0, the address in that VF BAR determines the base of an 8MB region. This region is divided into eight contiguous 1MB segments, each serving as a BAR0 for one of the VFs. It's important to note that although the VF BAR describes an 8MB region, the alignment requirement applies to a single VF—in this case, 1MB.

There are several strategies for isolating VFs in Processing Elements (PEs):

  - **M32 Window**: There's one M32 window, divided into 256 equally-sized segments. The finest granularity possible is a 256MB window with 1MB segments. VF BARs that are 1MB or larger can be mapped to separate PEs within this window. Each segment can be individually mapped to a PE through a lookup table, providing flexibility, but it works best when all VF BARs are the same size. If they vary in size, the entire window must be small enough that the segment size matches the smallest VF BAR, meaning larger VF BARs may span several segments.
- **Non-Segmented M64 Window**: A non-segmented M64 window is mapped entirely to a single PE, making it suitable for isolating a single VF.
- **Single Segmented M64 Windows**: A segmented M64 window can be used similarly to the M32 window, but segments cannot be individually mapped to PEs (the segment number corresponds to the PE number), reducing flexibility. A VF with multiple BARs would require a "domain" spanning multiple PEs, which is less isolated than a single PE.
- **Multiple Segmented M64 Windows**: Each window is divided into 256 equally-sized segments, with the segment number corresponding to the PE number. Using several M64 windows allows setting different base addresses and segment sizes. For instance, if VFs each have a 1MB BAR and a 32MB BAR, one M64 window can be used to assign 1MB segments, and another M64 window can assign 32MB segments.

Finally, the plan is to use M64 windows for SR-IOV, which will be detailed further in the next two sections. For a given VF BAR, we need to effectively reserve the entire 256 segments (256 times the VF BAR size) and position the VF BAR to start at the beginning of a free range of segments/PEs within that M64 window.

The goal is to allocate a separate PE for each VF. The IODA2 platform has 16 M64 windows, which are used to map Memory-Mapped I/O (MMIO) ranges to PE numbers. Each M64 window defines one MMIO range, and this range is divided into 256 segments, with each segment corresponding to one PE.
我们决定利用这个M64窗口来将VF映射到各个PE上，因为SR-IOV的VF BAR都是相同大小的。
但这样做引入了另一个问题：total_VFs通常小于M64窗口段的数量，因此如果我们将一个VF BAR直接映射到一个M64窗口上，M64窗口的一部分可能会映射到其他设备的MMIO范围上。
IODA支持256个PE，因此分段窗口包含256个段，如果total_VFs小于256，则会出现图1.0所示的情况，其中M64窗口的[total_VFs, 255]段可能会映射到其他设备上的某个MMIO范围：

     0      1                     total_VFs - 1
     +------+------+-     -+------+------+
     |      |      |  ...  |      |      |
     +------+------+-     -+------+------+

                           VF(n) BAR空间

     0      1                     total_VFs - 1                255
     +------+------+-     -+------+------+-      -+------+------+
     |      |      |  ...  |      |      |   ...  |      |      |
     +------+------+-     -+------+------+-      -+------+------+

                           M64窗口

		图1.0 直接映射VF(n) BAR空间

我们的当前解决方案是即使VF(n) BAR空间不需要这么多段也分配256个段，如图1.1所示：

     0      1                     total_VFs - 1                255
     +------+------+-     -+------+------+-      -+------+------+
     |      |      |  ...  |      |      |   ...  |      |      |
     +------+------+-     -+------+------+-      -+------+------+

                           VF(n) BAR空间 + 额外空间

     0      1                     total_VFs - 1                255
     +------+------+-     -+------+------+-      -+------+------+
     |      |      |  ...  |      |      |   ...  |      |      |
     +------+------+-     -+------+------+-      -+------+------+

			   M64窗口

		图1.1 映射VF(n) BAR空间 + 额外空间

分配额外的空间确保整个M64窗口将被分配给这一个SR-IOV设备，并且这部分空间不会对其他设备可用。需要注意的是，这仅扩展了软件中保留的空间；仍然只有total_VFs个VF，并且它们只响应[0, total_VFs - 1]段。硬件中没有响应[total_VFs, 255]段的部分。
4. 对通用PCI代码的影响
=============================

PCIe SR-IOV规范要求VF(n) BAR空间的基址要与单个VF BAR的大小对齐。
在IODA2中，MMIO地址决定了PE#。如果地址位于M32窗口内，我们可以通过更新将段转换为PE#的表来设置PE#。同样地，如果地址位于未分段的M64窗口内，我们可以设置该窗口的PE#。但如果是在分段的M64窗口内，段号就是PE#。
因此，控制VF的PE#的唯一方法是更改VF BAR中的VF(n) BAR空间的基址。如果PCI核心分配了VF(n) BAR空间所需的确切空间量，则VF BAR值是固定的，无法改变。
另一方面，如果PCI核心分配了额外的空间，则只要整个VF(n) BAR空间保持在核心分配的空间内，VF BAR值就可以改变。
理想情况下，段大小应与单个VF BAR的大小相同。
这样每个VF都将在其自己的PE中。VF BAR（以及因此的PE#）是连续的。如果VF0位于PE(x)中，那么VF(n)将位于PE(x+n)中。如果我们分配256个段，那么VF0的PE#有(256 - numVFs)种选择。
如果段大小小于VF BAR的大小，那么覆盖一个VF BAR需要多个段，这意味着一个VF将在几个PE中。这是可能的，但是隔离性较差，并且减少了PE#的选择数量，因为VF(n) BAR空间不是消耗numVFs个段，而是消耗(numVFs * n)个段。这意味着用于调整VF(n) BAR空间基址的可用段较少。
您没有提供需要翻译的文本。请提供需要翻译成中文的英文或其他语言的文本。
