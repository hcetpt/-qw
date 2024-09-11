AMDGPU 术语表
===============

在此处可以找到 amdgpu 驱动中使用的一些通用缩写。请注意，我们为显示核心（Display Core）提供了一个专门的术语表，请参阅 'Documentation/gpu/amdgpu/display/dc-glossary.rst'。
.. glossary::

    active_cu_number
      系统上活跃的计算单元（CUs）的数量。根据板卡配置，活跃的CU数量可能少于SE * SH * CU。

CP
      命令处理器（Command Processor）

    CPLIB
      内容保护库（Content Protection Library）

    CU
      计算单元（Compute Unit）

    DFS
      数字频率合成器（Digital Frequency Synthesizer）

    ECP
      增强内容保护（Enhanced Content Protection）

    EOP
      管道/管线结束（End Of Pipe/Pipeline）

    GART
      图形地址重映射表（Graphics Address Remapping Table）。这是我们用于GPU内核驱动程序中的GPU虚拟内存（GPUVM）页表的名字。它将系统资源（内存或MMIO空间）重映射到GPU的地址空间，以便GPU可以访问它们。GART这个名字可以追溯到AGP时代，当时平台提供了GPU可以使用的MMU，以获取分散页面的连续视图进行DMA操作。尽管MMU已经转移到了GPU上，但这个名字仍然保留了下来。
GC
      图形与计算（Graphics and Compute）

    GMC
      图形内存控制器（Graphic Memory Controller）

    GPUVM
      GPU虚拟内存（GPU Virtual Memory）。这是GPU的MMU（内存管理单元）。GPU支持多个虚拟地址空间，这些空间可以在任何给定时间同时存在。这些空间允许GPU将显存和系统资源重新映射到GPU虚拟地址空间中供GPU内核驱动程序和使用GPU的应用程序使用。这为使用GPU的不同应用程序提供了内存保护。
GTT
      图形转换表（Graphics Translation Tables）。这是一个通过TTM管理的内存池，提供了对系统资源（内存或MMIO空间）的访问，供GPU使用。这些地址可以映射到“GART”GPUVM页表中供内核驱动程序使用，或者映射到每个进程的GPUVM页表中供应用程序使用。
IH
      中断处理程序（Interrupt Handler）

    HQD
      硬件队列描述符（Hardware Queue Descriptor）

    IB
      间接缓冲区（Indirect Buffer）

    IP
      知识产权模块（Intellectual Property blocks）

    KCQ
      内核计算队列（Kernel Compute Queue）

    KGQ
      内核图形队列（Kernel Graphics Queue）

    KIQ
      内核接口队列（Kernel Interface Queue）

    MEC
      微引擎计算（MicroEngine Compute）

    MES
      微引擎调度器（MicroEngine Scheduler）

    MMHUB
      多媒体中心（Multi-Media HUB）

    MQD
      内存队列描述符（Memory Queue Descriptor）

    PPLib
      PowerPlay库（PowerPlay Library）- PowerPlay是电源管理组件

    PSP
      平台安全处理器（Platform Security Processor）

    RLC
      运行列表控制器（RunList Controller）

    SDMA
      系统直接内存访问（System DMA）

    SE
      着色引擎（Shader Engine）

    SH
      着色数组（SHader array）

    SMU
      系统管理单元（System Management Unit）

    SS
      扩展频谱（Spread Spectrum）

    VCE
      视频压缩引擎（Video Compression Engine）

    VCN
      视频编解码器下一代（Video Codec Next）
