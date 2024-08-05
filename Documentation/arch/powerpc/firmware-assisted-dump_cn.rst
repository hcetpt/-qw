======================
固件辅助内存转储
======================

2011年7月

固件辅助内存转储的目标是在系统崩溃后实现系统转储，并且能在系统完全重置的情况下完成这一操作，同时尽量减少系统恢复生产使用所需的总时间。
- 固件辅助内存转储（FADump）基础设施旨在替代现有的phyp辅助内存转储。
- FADump 使用与phyp辅助内存转储相同的固件接口和内存预留模型。
- 与phyp转储不同的是，FADump通过`/proc/vmcore`以ELF格式导出内存转储，与kdump的方式相同。这有助于我们复用kdump的基础设施来捕获和过滤转储。
- 与phyp转储不同的是，在读取`/proc/vmcore`时，用户空间工具无需引用任何sysfs接口。
- 与phyp转储不同的是，FADump允许用户通过一个简单的操作（即向`/sys/kernel/fadump_release_mem`写入1）释放所有为转储保留的内存。
- 一旦通过内核启动参数启用，FADump可以通过`/sys/kernel/fadump_registered`接口启动或停止（见下文中的sysfs文件部分），并且可以轻松地与kdump服务启动/停止初始化脚本集成。
与kdump或其他策略相比，固件辅助转储提供了几个显著的实际优势：

- 与kdump不同的是，系统已经重置，并加载了新的内核副本。特别是PCI和I/O设备已经重新初始化，处于干净、一致的状态。
- 在转储被复制出来后，持有转储的内存立即可供运行中的内核使用。因此，与kdump不同，FADump不需要第二次重启就能使系统回到生产配置状态。
上述过程只能通过与Power固件协调并得到其协助来实现。具体步骤如下：

- 首个内核在操作系统初始化期间向Power固件注册需要在转储中保留的内存区域。
这些注册的内存区域由第一个内核在启动早期预留。

- 当系统崩溃时，Power固件会将注册的低地址内存区域（启动内存）从源复制到目标区域。
它还会保存硬件页表项（PTE）。

**注：**
“启动内存”一词指的是内核在有限制内存的情况下成功启动所需的低地址内存块大小。默认情况下，启动内存大小是系统RAM的5%或256MB中的较大值。
用户也可以通过启动参数`crashkernel=`来指定启动内存大小，这将覆盖默认计算的大小。如果默认的启动内存大小不足以使第二个内核成功启动，请使用此选项。关于`crashkernel=`参数的语法，请参阅`Documentation/admin-guide/kdump/kdump.rst`。如果在`crashkernel=`参数中提供了任何偏移量，它将被忽略，因为FADump使用预定义的偏移量来为启动内存转储保护预留内存，以防系统崩溃。

- 在保存了低地址内存（启动内存）区域后，固件将重置PCI和其他硬件状态。它**不会**清除RAM。然后，它将以常规方式启动引导加载程序。
- 新启动的内核会注意到设备树中有一个新节点（在pSeries上为`rtas/ibm,kernel-dump`，在OPAL平台上为`ibm,opal/dump/mpipl-boot`），表明有来自前一次启动的崩溃数据可用。在早期启动阶段，操作系统会保留启动内存大小以上的剩余内存，有效地以有限制的内存大小启动。这将确保这个内核（也称为第二个内核或捕获内核）不会触碰任何转储内存区域。
- 用户空间工具将读取`/proc/vmcore`来获取内存内容，其中包含以前崩溃内核的ELF格式转储。用户空间工具可以将这些信息复制到磁盘、网络、NAS、SAN、iSCSI等，按需处理。
- 一旦用户空间工具完成了转储保存，它将向`/sys/kernel/fadump_release_mem`写入`1`来释放保留的内存供一般使用，但不包括下次固件辅助转储注册所需的内存。

请注意，固件辅助转储功能仅在pSeries（PowerVM）平台上的POWER6及以上系统以及PowerNV（OPAL）平台上的POWER9及以上系统且具有OP940或更高版本固件时可用。

示例命令如下：

```
# echo 1 > /sys/kernel/fadump_release_mem
```
请注意，当 PowerNV 平台上支持 FADump 时，OPAL 固件会导出 `ibm,opal/dump` 节点。
在基于 OPAL 的机器上，系统首先启动到一个临时内核（称为 petitboot 内核），然后才启动到捕获内核。此内核具有最小的内核和/或用户空间支持来处理崩溃数据。此类内核需要保留先前崩溃内核的内存以供后续的捕获内核启动时处理这些崩溃数据。必须在这样的内核中启用内核配置选项 `CONFIG_PRESERVE_FA_DUMP` 以确保崩溃数据得以保留以便稍后处理。
-- 在基于 OPAL 的机器（PowerNV）上，如果内核构建时启用了 `CONFIG_OPAL_CORE=y`，则在崩溃时刻的 OPAL 内存也会被导出为 `/sys/firmware/opal/mpipl/core` 文件。此 procfs 文件有助于使用 GDB 调试 OPAL 崩溃。可以通过向 `/sys/firmware/opal/mpipl/release_core` 节点写入 '1' 来释放用于导出此 procfs 文件的内核内存：
例如
```
# echo 1 > /sys/firmware/opal/mpipl/release_core
```

实现细节：
--------------

在启动过程中，会检查固件是否支持特定机器上的此功能。如果支持，则会检查是否有活动的崩溃转储等待我们。如果有，则除了 RAM 的引导内存大小之外，在早期启动期间会保留所有内容（参见图 2）。在我们从用户空间脚本（例如 kdump 脚本）收集完崩溃转储之后，这个区域会被释放。如果有崩溃转储数据，则会创建 `/sys/kernel/fadump_release_mem` 文件，并且保留的内存将被持有。
如果没有等待中的崩溃转储数据，则通常仅保留用于保存 CPU 状态、HPTE 区域、引导内存转储以及 FADump 标头的内存，并且该内存位于大于引导内存大小的位置（参见图 1）。
该区域不会被释放：该区域将永久保留，以便在发生崩溃的情况下充当引导内存内容副本的接收器，同时包含 CPU 状态和 HPTE 区域。
由于此保留内存区域仅在系统崩溃后使用，因此没有必要阻止生产内核使用这一大块内存。因此，如果配置了 CMA（连续内存分配器），实现使用 Linux 内核的 CMA 进行内存预留。通过 CMA 预留，此内存将可供应用程序使用，而内核被阻止使用它。这样，即使在用户页面存在于 CMA 区域的情况下，FADump 仍然能够捕获所有内核内存和大部分用户空间内存。

**图 1：第一个内核期间的内存预留**

低内存                                                内存顶部
0    引导内存大小   |<------ 保留的转储区域 ----->|     |
|           |           |      永久预留      |     |
V           V           |                                 |     V
+-----------+-----/ /---+---+----+-----------+-------+----+-----+
|           |           |///|////|    DUMP   |  HDR  |////|     |
+-----------+-----/ /---+---+----+-----------+-------+----+-----+
        |                   ^    ^       ^         ^      ^
        |                   |    |       |         |      |
        \                  CPU  HPTE     /         |      |
         --------------------------------          |      |
      引导内存内容由固件在崩溃时转移到保留区域。          |      |
      |                                            FADump 标头  |
                                             （元数据区域）   |

元数据：此区域存储一个元数据结构，其地址已注册给固件，并在支持标签（OPAL）的平台上崩溃后的第二个内核中检索。具有所需信息以处理崩溃转储的这种结构简化了转储捕获过程。

**图 2：崩溃后第二个内核期间的内存预留**

低内存                                              内存顶部
0      引导内存大小                                        |
|           |<------------ 保留的崩溃区域 ------------>|       |
V           V           |<--- 保留的转储区域 --->|       |
+----+---+--+-----/ /---+---+----+-------+-----+-----+-------+
|    |ELF|  |           |///|////|  DUMP | HDR |/////|       |
+----+---+--+-----/ /---+---+----+-------+-----+-----+-------+
       |   |  |                            |     |             |
       -----  ------------------------------     ---------------
         \              |                               |
           \            |                               |
             \          |                               |
               \        |    ----------------------------
                 \      |   /
                   \    |  /
                     \  | /
                  /proc/vmcore

+---+
|///| -> 上图中标记为此类区域（CPU、HPTE 和元数据）并不总是存在。例如，OPAL 平台没有 CPU 和 HPTE 区域，而元数据区域目前不支持 pSeries
+---+

+---+
|ELF| -> elfcorehdr，在崩溃后的第二个内核中创建
---

**注释：** 从 0 到启动内存大小的内存被第二个内核使用。

**图 2**

目前，当用户介入时，/proc/vmcore 中的转储将被复制到一个新文件中。通过 /proc/vmcore 可获得的转储数据将以 ELF 格式存在。因此，现有的 kdump 基础架构（kdump 脚本）只需稍作修改即可正常保存转储。在主要发行版中，kdump 脚本已经进行了修改，当使用 FADump 而不是 kdump 作为转储机制时，可以无缝运行（无需用户介入来保存转储）。用于检查转储的工具与用于 kdump 的相同。

如何启用固件辅助转储 (FADump)：
--------------------------------------

1. 设置配置选项 CONFIG_FA_DUMP=y 并构建内核。
2. 使用 'fadump=on' 内核命令行选项启动 Linux 内核。
   默认情况下，FADump 预留的内存将被初始化为 CMA 区域。
   另外，用户可以通过 'fadump=nocma' 启动 Linux 内核以防止 FADump 使用 CMA。
3. 可选地，用户还可以设置 'crashkernel=' 内核命令行选项
   来指定要为启动内存转储保留的内存大小。

**注释：**
1. 'fadump_reserve_mem=' 参数已被弃用。相反，请使用 'crashkernel=' 来指定要为启动内存转储保留的内存大小。
2. 如果固件辅助转储无法预留内存，则如果设置了 'crashkernel=' 命令行选项，它会回退到现有的 kdump 机制。
3. 如果用户希望捕获所有用户空间内存，并且可以接受预留内存不可用于生产系统，则可以使用 'fadump=nocma' 内核参数回退到旧的行为。
Sysfs/debugfs 文件：
--------------------

固件辅助转储（FADump）功能使用 Sysfs 文件系统来保存控制文件，并使用 Debugfs 文件来显示预留的内存区域。以下是内核 Sysfs 下的文件列表：

/sys/kernel/fadump_enabled
    此文件用于显示 FADump 状态：
- 0 = FADump 已禁用
- 1 = FADump 已启用

    此接口可以被 kdump 初始化脚本用来识别内核中是否启用了 FADump，然后根据情况采取行动。
/sys/kernel/fadump_registered
    此文件用于显示 FADump 的注册状态以及控制（启动/停止）FADump 注册：
- 0 = FADump 未注册
- 1 = FADump 已注册并准备好处理系统崩溃

    要注册 FADump，请执行 `echo 1 > /sys/kernel/fadump_registered`；要取消注册并停止 FADump，请执行 `echo 0 > /sys/kernel/fadump_registered`。

    取消注册 FADump 后，系统崩溃将不再被处理，也不会捕获 vmcore。此接口可以轻松集成到 kdump 服务的启动/停止流程中。
/sys/kernel/fadump/mem_reserved
    此文件用于显示 FADump 预留用于保存崩溃转储的内存。
/sys/kernel/fadump_release_mem
    当 FADump 在第二个内核中处于活动状态时，此文件才可用。它用于释放为保存崩溃转储而保留的内存区域。要释放预留的内存，请执行以下操作：

```
echo 1 > /sys/kernel/fadump_release_mem
```

    执行 `echo 1` 后，`/sys/kernel/debug/powerpc/fadump_region` 文件的内容会改变以反映新的内存预留情况。
现有的用户空间工具（如 kdump 基础设施）可以很容易地增强功能，使用此接口来释放为转储预留的内存，并在无需第二次重启的情况下继续运行。
注释：`/sys/kernel/fadump_release_opalcore` sysfs 已移动到
      `/sys/firmware/opal/mpipl/release_core`

`/sys/firmware/opal/mpipl/release_core`

此文件仅在 FADump 在捕获内核时处于活动状态的基于 OPAL 的机器上可用。
该文件用于释放内核用来导出 `/sys/firmware/opal/mpipl/core` 文件所使用的内存。要释放此内存，请向其写入 '1'：

    echo 1 > /sys/firmware/opal/mpipl/release_core

注释：以下 FADump sysfs 文件已废弃
+----------------------------------+--------------------------------+
| 已废弃                           | 替代方案                      |
+----------------------------------+--------------------------------+
| `/sys/kernel/fadump_enabled`     | `/sys/kernel/fadump/enabled`   |
+----------------------------------+--------------------------------+
| `/sys/kernel/fadump_registered`  | `/sys/kernel/fadump/registered`|
+----------------------------------+--------------------------------+
| `/sys/kernel/fadump_release_mem` | `/sys/kernel/fadump/release_mem`|
+----------------------------------+--------------------------------+

以下是 powerpc debugfs 下的文件列表：
（假设 debugfs 已挂载在 `/sys/kernel/debug` 目录下。）

`/sys/kernel/debug/powerpc/fadump_region`
如果启用了 FADump，此文件会显示预留的内存区域；否则，此文件为空。输出格式如下：

      `<region>`: `[<start>-<end>]` `<reserved-size>` 字节, 已转储: `<dump-size>`

对于内核转储区域，格式为：

    `DUMP`: Src: `<src-addr>`, Dest: `<dest-addr>`, Size: `<size>`, Dumped: # 字节

例如，在首次内核启动期间注册 FADump 时的内容如下：

      # cat /sys/kernel/debug/powerpc/fadump_region
      CPU : [0x0000006ffb0000-0x0000006fff001f] 0x40020 字节, Dumped: 0x0
      HPTE: [0x0000006fff0020-0x0000006fff101f] 0x1000 字节, Dumped: 0x0
      DUMP: [0x0000006fff1020-0x0000007fff101f] 0x10000000 字节, Dumped: 0x0

在第二次内核启动期间 FADump 处于活动状态时的内容如下：

      # cat /sys/kernel/debug/powerpc/fadump_region
      CPU : [0x0000006ffb0000-0x0000006fff001f] 0x40020 字节, Dumped: 0x40020
      HPTE: [0x0000006fff0020-0x0000006fff101f] 0x1000 字节, Dumped: 0x1000
      DUMP: [0x0000006fff1020-0x0000007fff101f] 0x10000000 字节, Dumped: 0x10000000
          : [0x00000010000000-0x0000006ffaffff] 0x5ffb0000 字节, Dumped: 0x5ffb0000

注意：
      有关如何挂载 debugfs 文件系统的详细信息，请参阅 `Documentation/filesystems/debugfs.rst`
待办事项：
-----
 - 需要找到更好的方法来确定更精确的引导内存大小，以便内核在有限制的内存下成功启动
作者：Mahesh Salgaonkar <mahesh@linux.vnet.ibm.com>

此文档基于 Linas Vepstas 和 Manish Ahuja 编写的原始文档。
