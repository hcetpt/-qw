Coresight CPU 调试模块
==========================

   :作者:   Leo Yan <leo.yan@linaro.org>
   :日期:   2017年4月5日

介绍
------------

Coresight CPU 调试模块在 ARMv8-a 架构参考手册（ARM DDI 0487A.k）的 “第 H 部分：外部调试” 章节中有定义。CPU 可以集成调试模块，主要用于两种模式：自托管调试和外部调试。通常外部调试模式是通过 JTAG 端口连接外部调试器；另一方面，程序可以探索依赖于自托管调试模式的方法，本文档将重点介绍这部分内容。
调试模块提供了基于采样的性能分析扩展功能，可用于采样 CPU 的程序计数器、安全状态和异常级别等。通常每个 CPU 都有一个专用的调试模块与其连接。基于自托管调试机制，Linux 内核可以在内核发生崩溃时从 MMIO 区域访问这些相关寄存器。内核崩溃回调通知器会为每个 CPU 导出相关的寄存器信息；最终这有助于崩溃分析。

实现
--------------

- 在驱动注册期间，它使用 EDDEVID 和 EDDEVID1 这两个设备 ID 寄存器来决定是否实现了基于采样的性能分析功能。在某些平台上，此硬件功能可能完全或部分实现；如果此功能不被支持，则注册将会失败。
- 在撰写本文档时，调试驱动主要依赖于内核崩溃回调通知器从三个采样寄存器（EDPCSR、EDVIDSR 和 EDCIDSR）收集的信息：从 EDPCSR 我们可以获得程序计数器；EDVIDSR 包含有关安全状态、异常级别、位宽等的信息；EDCIDSR 是包含 CONTEXTIDR_EL1 采样值的上下文 ID 值。
- 该驱动支持 CPU 以 AArch64 或 AArch32 模式运行。它们之间的寄存器命名约定略有不同，AArch64 使用 ‘ED’ 作为寄存器前缀（ARM DDI 0487A.k，第 H9.1 章），而 AArch32 使用 ‘DBG’ 作为前缀（ARM DDI 0487A.k，第 G5.1 章）。驱动统一采用 AArch64 的命名约定。
- ARMv8-a（ARM DDI 0487A.k）与 ARMv7-a（ARM DDI 0406C.b）有不同的寄存器位定义。因此，驱动整合了以下两种差异：

  如果 PCSROffset=0b0000，在 ARMv8-a 中 EDPCSR 功能未实现；但 ARMv7-a 定义了“PCSR 采样取决于指令集状态”。对于 ARMv7-a，驱动进一步检查 CPU 是否运行于 ARM 或 Thumb 指令集，并校准 PCSR 值。详细的偏移描述见 ARMv7-a ARM（ARM DDI 0406C.b）第 C11.11.34 章 “DBGPCSR, 程序计数器采样寄存器”
如果 PCSROffset=0b0010，ARMv8-a 定义为 “EDPCSR 实现且采样没有偏移应用，并且在 AArch32 状态下不采样指令集状态”。因此在 ARMv8 中如果 EDDEVID1.PCSROffset 为 0b0010 且 CPU 处于 AArch32 状态，EDPCSR 不会被采样；当 CPU 处于 AArch64 状态时，EDPCSR 会被采样且不会应用任何偏移。

时钟和电源域
----------------------

在访问调试寄存器之前，应确保时钟和电源域已正确启用。在 ARMv8-a 架构参考手册（ARM DDI 0487A.k）第 “H9.1 调试寄存器” 章节中，调试寄存器分布在两个域中：调试域和 CPU 域。
::

                                +---------------+
                                |               |
                                |               |
                     +----------+--+            |
        dbg_clock -->|          |**|            |<-- cpu_clock
                     |    Debug |**|   CPU      |
 dbg_power_domain -->|          |**|            |<-- cpu_power_domain
                     +----------+--+            |
                                |               |
                                |               |
                                +---------------+

对于调试域，用户使用 DT 绑定 “clocks” 和 “power-domains” 来指定调试逻辑对应的时钟源和电源供应。
驱动根据需要调用 pm_runtime_{put|get} 操作来处理调试电源域。
对于CPU域，不同的SoC设计有不同的电源管理方案，这最终对外部调试模块产生了重大影响。因此，我们可以将其分为以下几种情况：

- 在具有合理电源控制器的系统上，该控制器能够正确处理CPU电源域，可以通过驱动程序中的寄存器EDPRCR来控制CPU电源域。驱动程序首先将位EDPRCR.COREPURQ写入以启动CPU，然后写入位EDPRCR.CORENPDRQ以模拟CPU断电。因此，这可以确保在访问调试相关寄存器期间，CPU电源域正常供电；

- 某些设计会在集群上的所有CPU都断电时关闭整个集群——包括那些应该在调试电源域中保持供电的调试寄存器部分。在这种情况下，EDPRCR中的位不受尊重，因此这些设计不支持CoreSight/Debug设计者预期的那种断电调试。这意味着即使检查EDPRSR也可能导致总线挂起，如果目标寄存器未供电的话。在这种情况下，在调试寄存器未供电时访问它们可能会导致灾难；因此我们需要在启动时或用户在运行时启用模块时防止CPU进入低功耗状态。请参阅“如何使用模块”一章获取详细用法信息。

设备树绑定
--------------

详情请参见Documentation/devicetree/bindings/arm/arm,coresight-cpu-debug.yaml

如何使用模块
--------------

如果您希望在启动时启用调试功能，可以在内核命令行参数中添加"coresight_cpu_debug.enable=1"

驱动程序也可以作为一个模块工作，因此可以在加载模块时启用调试功能：

```
# insmod coresight_cpu_debug.ko debug=1
```

如果在启动或加载模块时未启用调试功能，驱动程序会使用debugfs文件系统提供一个开关来动态启用或禁用调试功能：

要启用它，请将'1'写入/sys/kernel/debug/coresight_cpu_debug/enable：
```
# echo 1 > /sys/kernel/debug/coresight_cpu_debug/enable
```

要禁用它，请将'0'写入/sys/kernel/debug/coresight_cpu_debug/enable：
```
# echo 0 > /sys/kernel/debug/coresight_cpu_debug/enable
```

如“时钟和电源域”章节所述，如果您正在使用一个具有空闲状态以关闭调试逻辑的平台，并且电源控制器无法很好地响应来自EDPRCR的请求，则应在启用CPU调试功能之前先限制CPU空闲状态；这样可以确保对调试逻辑的访问。

如果您希望在启动时限制空闲状态，可以在内核命令行中使用"nohlt"或"cpuidle.off=1"

在运行时，您可以使用以下方法禁用空闲状态：

可以通过PM QoS子系统禁用CPU空闲状态，更具体地说是通过使用"/dev/cpu_dma_latency"接口（详见Documentation/power/pm_qos_interface.rst）。根据PM QoS文档，所请求的参数将一直有效直到文件描述符被释放。例如：
```
# exec 3<> /dev/cpu_dma_latency; echo 0 >&3
..
做一些工作..
```
```
# exec 3<>-

同样的操作也可以从应用程序中完成
从 cpuidle sysfs 禁用特定 CPU 的特定空闲状态（参见
Documentation/admin-guide/pm/cpuidle.rst）::

  # echo 1 > /sys/devices/system/cpu/cpu$cpu/cpuidle/state$state/disable

输出格式
--------

以下是调试输出格式的一个示例::

  ARM 外部调试模块:
  coresight-cpu-debug 850000.debug: CPU[0]:
  coresight-cpu-debug 850000.debug:  EDPRSR:  00000001 (电源：开启 DLK：解锁)
  coresight-cpu-debug 850000.debug:  EDPCSR:  handle_IPI+0x174/0x1d8
  coresight-cpu-debug 850000.debug:  EDCIDSR: 00000000
  coresight-cpu-debug 850000.debug:  EDVIDSR: 90000000 (状态：非安全模式 模式：EL1/0 宽度：64位 VMID：0)
  coresight-cpu-debug 852000.debug: CPU[1]:
  coresight-cpu-debug 852000.debug:  EDPRSR:  00000001 (电源：开启 DLK：解锁)
  coresight-cpu-debug 852000.debug:  EDPCSR:  debug_notifier_call+0x23c/0x358
  coresight-cpu-debug 852000.debug:  EDCIDSR: 00000000
  coresight-cpu-debug 852000.debug:  EDVIDSR: 90000000 (状态：非安全模式 模式：EL1/0 宽度：64位 VMID：0)
```
