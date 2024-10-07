==========================
SLUB 简短用户指南
==========================

SLUB 的基本理念与 SLAB 非常不同。SLAB 要求重新编译内核以激活所有 slab 缓存的调试选项。而 SLUB 始终包含完整的调试功能，但默认是关闭的。SLUB 可以为选定的 slab 启用调试，以避免对整体系统性能产生影响，这可能会使错误更难发现。
为了开启调试，可以在内核命令行中添加一个选项 `slab_debug`。这将为所有 slab 启用完整调试。
通常会使用 `slabinfo` 命令来获取统计数据并对 slab 进行操作。默认情况下，`slabinfo` 只列出有数据的 slab。运行命令时，可以通过 `slabinfo -h` 查看更多选项。`slabinfo` 可以通过以下命令编译：
```bash
gcc -o slabinfo tools/mm/slabinfo.c
```

`slabinfo` 的一些操作模式要求在命令行中启用 slub 调试。例如，如果没有启用调试，则无法获得跟踪信息，并且验证只能部分完成。
一些更高级的 slab_debug 使用方法：
-------------------------------------------

可以给 `slab_debug` 指定参数。如果不指定任何参数，则启用完整调试。格式如下：

slab_debug=<Debug-Options>
    为所有 slab 启用选项

slab_debug=<Debug-Options>,<slab name1>,<slab name2>,...
    仅为选定的 slab 启用选项（逗号后不能有空格）

可以为所有 slab 或选定的 slab 给出多个选项块，选项块之间用分号分隔。最后一个“所有 slab”块适用于除匹配“选定 slab”块之外的所有 slab。第一个匹配 slab 名称的“选定 slab”块中的选项将被应用。
可能的调试选项包括：

F     完整性检查（启用 SLAB_DEBUG_CONSISTENCY_CHECKS）
        对不起，这是 SLAB 遗留问题
Z     红区（Red zoning）
P     毒化（对象和填充）
U     用户跟踪（分配和释放）
T     跟踪（请仅在单个 slab 上使用）
A     为缓存启用 failslab 过滤标记
O     关闭可能导致更高最小 slab 订单的缓存的调试
-     关闭所有调试（如果内核配置了 CONFIG_SLUB_DEBUG_ON 则有用）

例如，为了仅启用完整性检查和红区，可以指定：

slab_debug=FZ

尝试查找 dentry 缓存中的问题？试试：

slab_debug=,dentry

仅对 dentry 缓存启用调试。可以在 slab 名称末尾使用星号，以覆盖具有相同前缀的所有 slab。例如，以下命令可以毒化 dentry 缓存以及所有 kmalloc slab：

slab_debug=P,kmalloc-*,dentry

红区和跟踪可能会重新对齐 slab。我们仅对 dentry 缓存应用完整性检查：

slab_debug=F,dentry

调试选项可能需要存储元数据导致最小可能 slab 订单增加（例如，具有 PAGE_SIZE 对象大小的缓存）。这在内存较低或内存高度碎片化的情况下更有可能导致 slab 分配错误。要默认关闭此类缓存的调试，请使用：

slab_debug=O

您可以使用选项块为不同的 slab 名称列表应用不同的选项。这将为 dentry 启用红区，并为 kmalloc 启用用户跟踪。其他所有 slab 将不会启用任何调试：

slab_debug=Z,dentry;U,kmalloc-*

您还可以通过指定全局调试选项并列出不需要调试的 slab 名称（选项为 `-`）来为所有缓存启用选项（例如，完整性检查和毒化），除了那些被认为性能关键的缓存：

slab_debug=FZ;-,zs_handle,zspage

每个 slab 的调试选项状态可以在以下文件中找到：

/sys/kernel/slab/<slab name>/

如果文件内容为 1，则选项已启用；0 表示禁用。`slab_debug` 参数中的调试选项对应于以下文件：

F   sanity_checks
Z   red_zone
P   poison
U   store_user
T   trace
A   failslab

failslab 文件可写，因此写入 1 或 0 可以在运行时启用或禁用该选项。如果缓存是别名，则写入返回 -EINVAL。
注意跟踪：如果在不合适的 slab 上使用，可能会输出大量信息并且不会停止。
slab 合并
============

如果没有指定调试选项，SLUB 可能会合并类似的 slab 以减少开销并提高对象缓存的热度。
`slabinfo -a` 显示了哪些 slab 被合并在一起。
块验证
===============

如果内核在启动时启用了slab_debug，SLUB可以验证所有对象。为了做到这一点，你必须有`slabinfo`工具。然后你可以执行以下命令：
::
	slabinfo -v

这将测试所有对象，并将输出生成到系统日志中。如果是在没有启用slab_debug的情况下启动的，则`slabinfo -v`仅会测试所有可到达的对象。通常这些对象位于CPU块和部分块中。在非调试情况下，完整块不会被SLUB跟踪。

提高性能
========================

在某种程度上，SLUB的性能受限于偶尔需要获取list_lock来处理部分块。这种开销受每个块分配顺序的影响。分配可以通过内核参数进行影响：

.. slab_min_objects=x		（默认：根据CPU数量自动调整）
.. slab_min_order=x		（默认为0）
.. slab_max_order=x		（默认为3 (PAGE_ALLOC_COSTLY_ORDER)）

`slab_min_objects`
	允许指定至少有多少个对象必须放入一个块中才能使分配顺序可接受。一般来说，slub可以在不咨询集中资源（list_lock）的情况下，在一个块上完成这个数量的分配，从而减少争用。
`slab_min_order`
	指定块的最小分配顺序。效果类似于`slab_min_objects`。
`slab_max_order`
	指定不再检查`slab_min_objects`的分配顺序。这对于避免SLUB尝试生成超大页以适应具有较大对象大小的slab缓存是有用的。设置命令行参数`debug_guardpage_minorder=N`（N > 0），会强制将`slab_max_order`设为0，从而导致最小可能的块分配顺序。

SLUB调试输出
=================

以下是slub调试输出的一个示例：
:: 

=============================================================================
BUG kmalloc-8: Right Redzone 被覆盖
--------------------------------------------------------------------

INFO: 0xc90f6d28-0xc90f6d2b. 第一个字节为0x00而不是0xcc
INFO: Slab 0xc528c530 标志=0x400000c3 使用中=61 fp=0xc90f6d58
INFO: 对象 0xc90f6d20 @偏移量=3360 fp=0xc90f6d58
INFO: 在get_modalias+0x61/0xf5处分配 年龄=53 cpu=1 pid=554

Bytes b4 (0xc90f6d10): 00 00 00 00 00 00 00 00 5a 5a 5a 5a 5a 5a 5a 5a ........ZZZZZZZZ
对象   (0xc90f6d20): 31 30 31 39 2e 30 30 35                         1019.005
Redzone  (0xc90f6d28): 00 cc cc cc
填充  (0xc90f6d50): 5a 5a 5a 5a 5a 5a 5a 5a                         ZZZZZZZZ

   [<c010523d>] dump_trace+0x63/0x1eb
   [<c01053df>] show_trace_log_lvl+0x1a/0x2f
   [<c010601d>] show_trace+0x12/0x14
   [<c0106035>] dump_stack+0x16/0x18
   [<c017e0fa>] object_err+0x143/0x14b
   [<c017e2cc>] check_object+0x66/0x234
   [<c017eb43>] __slab_free+0x239/0x384
   [<c017f446>] kfree+0xa6/0xc6
   [<c02e2335>] get_modalias+0xb9/0xf5
   [<c02e23b7>] dmi_dev_uevent+0x27/0x3c
   [<c027866a>] dev_uevent+0x1ad/0x1da
   [<c0205024>] kobject_uevent_env+0x20a/0x45b
   [<c020527f>] kobject_uevent+0xa/0xf
   [<c02779f1>] store_uevent+0x4f/0x58
   [<c027758e>] dev_attr_store+0x29/0x2f
   [<c01bec4f>] sysfs_write_file+0x16e/0x19c
   [<c0183ba7>] vfs_write+0xd1/0x15a
   [<c01841d7>] sys_write+0x3d/0x72
   [<c0104112>] sysenter_past_esp+0x5f/0x99
   [<b7f7b410>] 0xb7f7b410
   =======================

 FIX kmalloc-8: 恢复Redzone 0xc90f6d28-0xc90f6d2b=0xcc

如果SLUB遇到损坏的对象（完全检测需要内核在启动时启用slab_debug），则会将以下输出转储到系统日志中：

1. 遇到的问题描述

    这将是一个系统日志中的消息，以如下内容开始：
    ::

      ===============================================================
      BUG <受影响的slab缓存>: <出了什么问题>
      ---------------------------------------------------------------

      INFO: <损坏起始>-<损坏结束> 更多信息
      INFO: Slab <地址> <slab信息>
      INFO: 对象 <地址> <对象信息>
      INFO: 在<内核函数>处分配 年龄=<自分配以来的滴答数> cpu=<分配的cpu> pid=<进程的pid>
      INFO: 在<内核函数>处释放 年龄=<自释放以来的滴答数> cpu=<释放的cpu> pid=<进程的pid>

    （对象分配/释放信息只有在slab设置了SLAB_STORE_USER时才可用。slab_debug会设置此选项）

2. 如果涉及对象，则显示对象的内容
在BUG SLUB行之后可以跟随各种类型的行：

   Bytes b4 <地址> : <字节>
    显示在检测到问题的对象之前的几个字节
    如果损坏没有从对象的开始停止，这可能是有用的。
### 对象 <地址> : <字节>
对象的字节。如果对象处于非活动状态，则这些字节通常包含毒值。任何非毒值表示在释放后有写入操作导致的数据损坏。

### 红区 <地址> : <字节>
对象后面的红区。红区用于检测对象释放后的写入操作。所有字节应始终具有相同的值。如果有任何偏差，则表明有越界写入。
（只有在设置了 SLAB_RED_ZONE 选项时，红区信息才可用。slab_debug 设置了该选项）

### 填充 <地址> : <字节>
用于填充空间以使下一个对象正确对齐的未使用数据。在调试模式下，我们确保至少有 4 字节的填充。这可以检测到对象前的写入操作。

### 栈转储

栈转储描述了检测到错误的位置。通过查看分配或释放对象的函数，可以更有可能找到导致损坏的原因。

### 处理问题报告以确保系统继续运行

这些是系统日志中的消息，以以下内容开头：

```
FIX <受影响的 slab 缓存>: <采取的纠正措施>
```

在上面的示例中，SLUB 发现一个活动对象的红区被覆盖。这里将一个长度为 8 个字符的字符串写入了一个同样长度为 8 个字符的 slab 中。然而，一个 8 个字符的字符串需要一个终止符 0。这个零覆盖了红区字段的第一个字节。

在报告了遇到的问题详情后，FIX SLUB 消息告诉我们 SLUB 已经将红区恢复为其正确的值，并且系统操作继续进行。

### 紧急操作

通过以下启动参数可以启用最小调试（仅进行合理性检查）：

```
slab_debug=F
```

这通常足以启用 SLUB 的容错特性，即使有不良内核组件不断损坏对象，也能保持系统运行。这对于生产系统可能很重要。
性能会受到合理性检查的影响，并且系统日志中会持续出现错误消息，但不会使用额外的内存（与全调试模式不同）。
无任何保证。内核组件仍需修复。通过定位发生损坏的内存块并仅为此缓存启用调试，性能可能会进一步优化。

例如：

	slab_debug=F,dentry

如果损坏是由于超出对象末尾写入造成的，则建议启用红区（Redzone）以避免破坏其他对象的开头：

	slab_debug=FZ,dentry

扩展的 slabinfo 模式与绘图
===============================

`slabinfo` 工具具有一个特殊的“扩展”（'-X'）模式，该模式包括：
- 内存池总览
- 按大小排序的内存块（最多 -N <num> 个内存块，默认为 1）
- 按损失排序的内存块（最多 -N <num> 个内存块，默认为 1）

此外，在此模式下，`slabinfo` 不会动态调整大小单位（G/M/K），而是报告所有数据的字节数（此功能也可通过 '-B' 选项应用于其他 slabinfo 模式），这使得报告更加精确和准确。此外，某种意义上，`-X` 模式还简化了对内存块行为的分析，因为其输出可以使用 `slabinfo-gnuplot.sh` 脚本进行绘图。因此，它将分析从查看数字转变为更简单的视觉分析。

要生成绘图：

a) 收集扩展的 slabinfo 记录，例如：

	while [ 1 ]; do slabinfo -X >> FOO_STATS; sleep 1; done

b) 将统计文件传递给 `slabinfo-gnuplot.sh` 脚本：

	slabinfo-gnuplot.sh FOO_STATS [FOO_STATS2 .. FOO_STATSN]

`slabinfo-gnuplot.sh` 脚本将预处理收集到的记录，并为每个 STATS 文件生成 3 个 PNG 文件（和 3 个预处理缓存文件）：
- 内存池总览：FOO_STATS-totals.png
- 按大小排序的内存块：FOO_STATS-slabs-by-size.png
- 按损失排序的内存块：FOO_STATS-slabs-by-loss.png

另一个使用场景是当您需要比较代码修改前后的内存块行为时，`slabinfo-gnuplot.sh` 脚本可以合并不同测量中的“内存池总览”部分。为了帮助您进行可视化比较：

a) 收集尽可能多的 STATS1, STATS2, .. STATSN 文件：

	while [ 1 ]; do slabinfo -X >> STATS<X>; sleep 1; done

b) 预处理这些 STATS 文件：

	slabinfo-gnuplot.sh STATS1 STATS2 .. STATSN

c) 在 '-t' 模式下执行 `slabinfo-gnuplot.sh`，并传递所有生成的预处理的 *-totals：

	slabinfo-gnuplot.sh -t STATS1-totals STATS2-totals .. STATSN-totals

这将生成单个绘图（PNG 文件）。

由于绘图可能较大，某些波动或小峰值可能被忽略。为此，`slabinfo-gnuplot.sh` 提供了两种选项来“放大”或“缩小”：

a) `-s %d,%d` -- 重写默认图像宽度和高度
b) `-r %d,%d` -- 指定要使用的样本范围（例如，在 `slabinfo -X >> FOO_STATS; sleep 1;` 情况下，使用 `-r 40,60` 范围将仅绘制第 40 秒至第 60 秒之间收集的样本）

SLUB 的 DebugFS 文件
=====================

为了获取更多关于当前状态下的 SLUB 缓存信息（启用用户跟踪调试选项），可以访问 DebugFS 文件，通常位于 `/sys/kernel/debug/slab/<cache>/`（仅在启用了用户跟踪的缓存中创建）。这些文件包含以下两种类型的调试信息：

1. alloc_traces：

    显示当前已分配对象的独特分配追踪信息。输出按每个追踪的频率排序。
    
    输出中的信息包括：
    对象数量、分配函数、kmalloc 对象可能的内存浪费（总量/每个对象）、自分配以来的最小/平均/最大 jiffies 数、分配进程的 PID 范围、分配 CPU 的 CPU 掩码、内存来源的 NUMA 节点掩码以及堆栈追踪。
    
    示例：
    
    338 pci_alloc_dev+0x2c/0xa0 waste=521872/1544 age=290837/291891/293509 pid=1 cpus=106 nodes=0-1
        __kmem_cache_alloc_node+0x11f/0x4e0
        kmalloc_trace+0x26/0xa0
        pci_alloc_dev+0x2c/0xa0
        pci_scan_single_device+0xd2/0x150
        pci_scan_slot+0xf7/0x2d0
        pci_scan_child_bus_extend+0x4e/0x360
        acpi_pci_root_create+0x32e/0x3b0
        pci_acpi_scan_root+0x2b9/0x2d0
        acpi_pci_root_add.cold.11+0x110/0xb0a
        acpi_bus_attach+0x262/0x3f0
        device_for_each_child+0xb7/0x110
        acpi_dev_for_each_child+0x77/0xa0
        acpi_bus_attach+0x108/0x3f0
        device_for_each_child+0xb7/0x110
        acpi_dev_for_each_child+0x77/0xa0
        acpi_bus_attach+0x108/0x3f0

2. free_traces：

    显示当前已分配对象的独特释放追踪信息。释放追踪来自对象的上一个生命周期，并且对于首次分配的对象报告为不可用。输出按每个追踪的频率排序。
    
    输出中的信息包括：
    对象数量、释放函数、自释放以来的最小/平均/最大 jiffies 数、释放进程的 PID 范围、释放 CPU 的 CPU 掩码以及堆栈追踪。
    
    示例：
    
    1980 <not-available> age=4294912290 pid=0 cpus=0
    51 acpi_ut_update_ref_count+0x6a6/0x782 age=236886/237027/237772 pid=1 cpus=1
	kfree+0x2db/0x420
	acpi_ut_update_ref_count+0x6a6/0x782
	acpi_ut_update_object_reference+0x1ad/0x234
	acpi_ut_remove_reference+0x7d/0x84
	acpi_rs_get_prt_method_data+0x97/0xd6
	acpi_get_irq_routing_table+0x82/0xc4
	acpi_pci_irq_find_prt_entry+0x8e/0x2e0
	acpi_pci_irq_lookup+0x3a/0x1e0
	acpi_pci_irq_enable+0x77/0x240
	pcibios_enable_device+0x39/0x40
	do_pci_enable_device.part.0+0x5d/0xe0
	pci_enable_device_flags+0xfc/0x120
	pci_enable_device+0x13/0x20
	virtio_pci_probe+0x9e/0x170
	local_pci_probe+0x48/0x80
	pci_device_probe+0x105/0x1c0

Christoph Lameter，2007年5月30日  
Sergey Senozhatsky，2015年10月23日
