### 数据流控制寄存器 (DSCR)

DSCR 寄存器在 PowerPC 架构中允许用户对处理器中的数据流预取进行一定程度的控制。有关如何使用此 DSCR 来实现预取控制的详细信息，请参考 ISA 文档或相关手册。本文件提供内核对 DSCR 的支持概述，包括相关的内核对象、功能及其导出的用户接口。

(A) **数据结构**：

    1. `thread_struct`:
    
        - `dscr`：线程的 DSCR 值。
        - `dscr_inherit`：线程已更改默认 DSCR。
    
    2. `PACA`（Per-CPU Area）:
    
        - `dscr_default`：每个 CPU 的默认 DSCR 值。
    
    3. `sysfs.c`:
    
        - `dscr_default`：系统的默认 DSCR 值。

(B) **调度程序更改**：

    如果线程的 `dscr_inherit` 标志被清除，表示它尚未更改默认 DSCR，则调度程序会将存储在 CPU PACA 结构中的每 CPU 默认 DSCR 写入寄存器。如果 `dscr_inherit` 被设置，意味着线程已更改了默认 DSCR 值，则调度程序会将线程结构中的更改后的值写入寄存器，而不是使用基于每 CPU 默认 PACA 的 DSCR 值。

    **注意**：请注意，全局系统范围内的默认 DSCR 值从未直接用于调度程序上下文切换过程中。

(C) **SYSFS 接口**：

    - 全局 DSCR 默认值：`/sys/devices/system/cpu/dscr_default`
    - 每个 CPU 的 DSCR 默认值：`/sys/devices/system/cpu/cpuN/dscr`

    更改 sysfs 中的全局 DSCR 默认值会立即更改所有 CPU 的 PACA 结构中的特定于 CPU 的 DSCR 默认值。如果当前进程的 `dscr_inherit` 未被设置，则也会立即将新值写入每个 CPU 的 DSCR 寄存器，并更新当前线程的 DSCR 值。

    更改 sysfs 中的特定于 CPU 的 DSCR 默认值会产生相同的效果，但与全局值不同的是，它仅针对特定 CPU 进行更改，而非系统上的所有 CPU。

(D) **用户空间指令**：

    可以使用以下两个 SPR 编号之一从用户空间访问 DSCR 寄存器：
    
    1. 问题状态 SPR：`0x03`（非特权，仅限 POWER8）
    2. 特权状态 SPR：`0x11`（特权）

    从用户空间通过特权 SPR 编号 (0x11) 访问 DSCR 是可行的，因为它会在内核中模拟非法指令异常。mfspr 和 mtspr 指令都会被模拟。
    
    从用户空间通过用户级 SPR (0x03) 访问 DSCR 首先会创建一个设施不可用异常。在此异常处理程序中，所有基于 mfspr 指令的读取尝试都将被模拟并返回；而基于 mtspr 指令的首次写入尝试将通过设置 FSCR 寄存器中的 DSCR 设施来为下一次读写启用 DSCR 设施。

(E) **关于 `dscr_inherit` 的具体说明**：

    `thread_struct` 元素 `dscr_inherit` 表示线程是否尝试并更改了 DSCR 本身。此元素表明线程是希望使用 CPU 默认的 DSCR 值还是其自身更改过的 DSCR 值。
(1) mtspr指令 (SPR编号 0x03)
(2) mtspr指令 (SPR编号 0x11)
(3) ptrace接口 (明确设置用户DSCR值)

在此事件后进程创建的任何子进程也会继承相同的行为。
