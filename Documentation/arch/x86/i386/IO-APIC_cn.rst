SPDX 许可证标识符: GPL-2.0

======
IO-APIC
======

:作者: Ingo Molnar <mingo@kernel.org>

大多数（如果不说全部的话）遵循 Intel-MP 规范的对称多处理器(SMP)主板都配备了所谓的“IO-APIC”(I/O 高级程序中断控制器)，这是一种增强型中断控制器。它使我们可以将硬件中断路由到多个 CPU 或 CPU 组。如果没有 IO-APIC，来自硬件的中断只会被传送到启动操作系统的 CPU（通常是 CPU#0）。Linux 支持所有遵循规范的 SMP 主板变体，包括具有多个 IO-APIC 的主板。在高端服务器中，多个 IO-APIC 被用来进一步分散 IRQ 负载。
某些较旧主板上存在已知的问题，这些通常会被内核通过变通方法解决。如果你遵循 Intel-MP 规范的 SMP 主板无法启动 Linux，请首先查阅 linux-smp 邮件列表归档。
如果你的机器在启用 IO-APIC IRQ 后能正常启动，那么你的 `/proc/interrupts` 文件看起来可能如下所示：

```
hell:~> cat /proc/interrupts
             CPU0
    0:    1360293    IO-APIC-edge  timer
    1:          4    IO-APIC-edge  keyboard
    2:          0          XT-PIC  cascade
   13:          1          XT-PIC  fpu
   14:       1448    IO-APIC-edge  ide0
   16:      28232   IO-APIC-level  Intel EtherExpress Pro 10/100 Ethernet
   17:      51304   IO-APIC-level  eth0
  NMI:          0
  ERR:          0
  hell:~>
```

一些中断仍然以 'XT PIC' 列出，但这不是问题；这些 IRQ 源并不影响性能。
在极不可能的情况下，如果你的主板没有创建一个有效的工作 MP 表，则可以使用 pirq= 引导参数来“手工构建”IRQ 条目。这并非易事，也无法自动化。以下是一个 `/etc/lilo.conf` 示例条目：

```
append="pirq=15,11,10"
```

实际数值取决于你的系统、你的 PCI 卡以及它们在 PCI 插槽中的位置。通常 PCI 插槽是“菊花链式连接”的，然后才连接到 PCI 芯片组的 IRQ 路由设施（即进入的 PIRQ1-4 线路）：

```
               ,-.        ,-.        ,-.        ,-.        ,-
PIRQ4 ----| |-.    ,-| |-.    ,-| |-.    ,-| |--------| |
               |S|  \  /  |S|  \  /  |S|  \  /  |S|        |S|
     PIRQ3 ----|l|-. `/---|l|-. `/---|l|-. `/---|l|--------|l|
               |o|  \/    |o|  \/    |o|  \/    |o|        |o|
     PIRQ2 ----|t|-./`----|t|-./`----|t|-./`----|t|--------|t|
               |1| /\     |2| /\     |3| /\     |4|        |5|
     PIRQ1 ----| |-  `----| |-  `----| |-  `----| |--------| |
               `-'        `-'        `-'        `-'        `-'
```

每张 PCI 卡都会发出一个 PCI IRQ，可能是 INTA、INTB、INTC 或 INTD：

```
                               ,-
INTD--| |
                               |S|
                         INTC--|l|
                               |o|
                         INTB--|t|
                               |x|
                         INTA--| |
                               `-'
```

这些 INTA-D PCI IRQ 总是“与卡本地相关”，其实际含义取决于插槽的位置。如果你查看菊花链式连接图，位于插槽 4 的卡发出 INTA IRQ，则最终会变成 PCI 芯片集上的 PIRQ4 信号。大多数卡发出 INTA，这样可以在 PIRQ 线之间实现最佳分布。（正确分配 IRQ 源并不是必需的，PCI IRQ 可以随意共享，但从性能角度来看，拥有非共享中断是有益的）。插槽 5 应用于显卡，它们通常不使用中断，因此也不会进行菊花链式连接。例如，如果你的 SCSI 卡（IRQ11）位于插槽 1，Tulip 卡（IRQ9）位于插槽 2，则需要指定以下 pirq= 行：

```
append="pirq=11,9"
```

下面的脚本尝试从你的 PCI 配置中推断出这样的默认 pirq= 行：

```
echo -n pirq=; echo `scanpci | grep T_L | cut -c56-` | sed 's/ /,/g'
```

需要注意的是，如果跳过了几个插槽或你的主板不执行默认菊花链式连接（或者 IO-APIC 以某种奇怪的方式连接了 PIRQ 引脚），这个脚本可能不会工作。例如，在上述情况下，如果你的 SCSI 卡（IRQ11）位于插槽 3，并且插槽 1 空着：

```
append="pirq=0,9,11"
```

值 '0' 是一个通用的“占位符”，为未使用（或不产生 IRQ）的插槽预留。

一般来说，总是有可能找出正确的 pirq= 设置，只需要适当地排列所有的 IRQ 编号……但这需要一些时间。错误的 pirq 行会导致引导过程挂起，或设备无法正常工作（例如，如果作为模块插入）。
如果你有两个 PCI 总线，那么你可以使用多达 8 个 pirq 值，尽管这种主板往往有一个良好的配置。
请准备好可能会出现需要使用奇怪的 pirq 行的情况：

```
append="pirq=0,0,0,0,0,0,9,11"
```

使用智能试错技术找出正确的 pirq 行。
祝你好运，如果遇到本文件未涵盖的问题，请发送邮件至 linux-smp@vger.kernel.org 或 linux-kernel@vger.kernel.org。
