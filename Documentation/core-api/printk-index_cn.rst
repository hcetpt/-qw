SPDX 许可证标识符: GPL-2.0

============
打印索引 (Printk Index)
============

有许多方法可以监控系统的状态。一个重要的信息来源是系统日志。它提供了大量信息，包括不同程度的重要警告和错误消息。有监控工具可以根据记录的日志消息进行过滤并采取行动。
内核消息会随着代码的演变而变化。因此，特定的内核消息并不是 KABI（Kernel ABI，内核应用程序二进制接口）的一部分，并且永远不会成为 KABI 的一部分！

对于维护系统日志监控来说是一个巨大的挑战。这需要知道在某个特定内核版本中哪些消息被更新以及为何更新。要找到这些变化，需要非平凡的解析器来处理源代码。同时还需要将源代码与二进制内核进行匹配，而这并不总是容易做到的。各种变更可能被回退到旧版本，不同的监控系统可能会使用不同版本的内核。在这种情况下，打印索引功能可能会变得非常有用。它提供了一个运行时内核及其模块所使用的打印格式的汇总信息，可以通过 debugfs 接口访问。
打印索引有助于发现消息格式的变化，也有助于追踪字符串回到内核源码及相关提交。

用户界面
==============

打印格式的索引被拆分成单独的文件。文件名根据包含打印格式的二进制文件命名。通常会有 "vmlinux" 文件，另外还可能有模块文件，例如：

   /sys/kernel/debug/printk/index/vmlinux
   /sys/kernel/debug/printk/index/ext4
   /sys/kernel/debug/printk/index/scsi_mod

请注意，只有已加载的模块才会显示出来。此外，如果模块是内置的，其打印格式也可能出现在 "vmlinux" 中。
内容受到了动态调试接口的启发，看起来像这样：

   $> head -1 /sys/kernel/debug/printk/index/vmlinux; shuf -n 5 vmlinux
   # <级别[,标志]> 文件名:行号 函数 "格式"
   <5> block/blk-settings.c:661 disk_stack_limits "%s: 警告: 设备 %s 不对齐\n"
   <4> kernel/trace/trace.c:8296 trace_create_file "无法创建 tracefs '%s' 条目\n"
   <6> arch/x86/kernel/hpet.c:144 _hpet_print_config "hpet: %s(%d):\n"
   <6> init/do_mounts.c:605 prepare_namespace "等待根设备 %s...\n"
   <6> drivers/acpi/osl.c:1410 acpi_no_auto_serialize_setup "ACPI: 禁用自动序列化\n"

其中含义如下：

   - **级别**：日志级别值：0-7 表示不同严重程度，-1 表示默认值，'c' 表示连续行且没有显式日志级别。
   - **标志**：可选标志：目前仅支持 'c' 表示 KERN_CONT。
   - **文件名:行号**：与 printk() 调用相关的源文件名和行号。需要注意的是，有许多封装函数，例如 pr_warn()、pr_warn_once()、dev_warn()。
   - **函数**：使用 printk() 调用的函数名称。
额外的信息使得比较不同内核之间的差异变得稍微困难。特别是行号可能会经常发生变化。另一方面，它对于确认这是相同的字符串或找到导致任何变化的提交非常有帮助。

`printk()` 并非稳定的 KABI（Kernel Application Binary Interface，内核应用二进制接口）
======================================================
一些开发者担心将所有这些实现细节导出到用户空间会将特定的 `printk()` 调用变成 KABI 的一部分。但事实恰恰相反。`printk()` 调用不应是 KABI 的一部分，并且 `printk` 索引有助于用户空间工具处理这种情况。

子系统特定的 `printk` 包装器
=================================
`printk` 索引是使用存储在专用 `.elf` 部分（即 ".printk_index"）中的附加元数据生成的。这通过宏包装器与实际的 `printk()` 调用一起调用 `__printk_index_emit()` 来实现。同样的技术也用于动态调试功能所需的元数据。
只有当消息使用这些特殊的包装器打印时，才会为该消息存储元数据。这种方法已经实现了对常用的 `printk()` 调用的支持，例如 `pr_warn()` 或 `pr_once()`。
对于通过通用辅助函数调用原始 `printk()` 的各种子系统特定包装器，需要进行额外的更改以添加 `__printk_index_emit()`。到目前为止，只有少数子系统的包装器进行了更新，例如 `dev_printk()`。因此，某些子系统的 `printk` 格式可能在 `printk` 索引中缺失。

子系统特定的前缀
==================
`pr_fmt()` 宏允许定义一个前缀，这个前缀会在由相关 `printk()` 调用生成的字符串之前打印出来。子系统特定的包装器通常会添加更复杂的前缀。
这些前缀可以通过 `__printk_index_emit()` 的一个可选参数存储到 `printk` 索引元数据中。然后，debugfs 接口可能会显示包含这些前缀的 `printk` 格式。例如，`drivers/acpi/osl.c` 包含：

```c
#define pr_fmt(fmt) "ACPI: OSL: " fmt

static int __init acpi_no_auto_serialize_setup(char *str)
{
	acpi_gbl_auto_serialize_methods = FALSE;
	pr_info("Auto-serialization disabled\n");

	return 1;
}
```

这将产生以下 `printk` 索引条目：

```
<6> drivers/acpi/osl.c:1410 acpi_no_auto_serialize_setup "ACPI: auto-serialization disabled\n"
```

这有助于将实际日志中的消息与 `printk` 索引匹配。然后可以使用源文件名、行号和函数名称来将字符串与源代码进行匹配。
