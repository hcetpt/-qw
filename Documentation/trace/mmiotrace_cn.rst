===================================
内核内存映射I/O追踪
===================================

主页和可选用户空间工具的链接：

	https://nouveau.freedesktop.org/wiki/MmioTrace

MMIO追踪最初由Intel在2003年左右为其故障注入测试框架开发。2006年12月至2007年1月，Jeff Muizelaar使用Intel的代码为Nouveau项目创建了一个追踪MMIO访问的工具。自那时以来，许多人对Mmiotrace做出了贡献。Mmiotrace最初是为了反向工程任何内存映射I/O设备而构建的，Nouveau项目是其第一个真正的用户。目前仅支持x86和x86_64架构。
树外的mmiotrace最初由Pekka Paalanen <pq@iki.fi> 修改以纳入主线内核并集成到ftrace框架中。

准备
------

Mmiotrace功能通过CONFIG_MMIOTRACE选项编译进内核。默认情况下追踪是禁用的，因此将其设置为“是”是安全的。SMP系统被支持，但在多于一个CPU在线的情况下，追踪可能不可靠且会错过事件，因此mmiotrace在运行时激活时将所有但一个CPU离线。你可以手动重新启用CPU，但请注意警告：无法自动检测由于CPU竞争而导致的事件丢失。

快速使用参考
---------------------
::

	$ mount -t debugfs debugfs /sys/kernel/debug
	$ echo mmiotrace > /sys/kernel/tracing/current_tracer
	$ cat /sys/kernel/tracing/trace_pipe > mydump.txt &
	启动X或其他应用程序
	$ echo "X is up" > /sys/kernel/tracing/trace_marker
	$ echo nop > /sys/kernel/tracing/current_tracer
	检查丢失的事件

使用方法
-----

确保debugfs已挂载到/sys/kernel/debug
如果没有（需要root权限）:: 

	$ mount -t debugfs debugfs /sys/kernel/debug

确认你要追踪的驱动程序尚未加载
激活mmiotrace（需要root权限）:: 

	$ echo mmiotrace > /sys/kernel/tracing/current_tracer

开始存储追踪信息:: 

	$ cat /sys/kernel/tracing/trace_pipe > mydump.txt &

“cat”进程应该在后台持续运行（休眠）
加载你想要追踪的驱动程序并使用它。Mmiotrace只会捕捉在mmiotrace激活期间ioremapped区域的MMIO访问。
在跟踪过程中，您可以通过以下命令在跟踪记录中添加注释（标记）：
```
$ echo "X is up" > /sys/kernel/tracing/trace_marker
```
这有助于更清晰地了解哪部分（巨大的）跟踪记录对应于哪个操作。建议放置描述性的标记来说明您的操作。
关闭 mmiotrace（需要root权限）：

```
$ echo nop > /sys/kernel/tracing/current_tracer
```

`cat` 进程会退出。如果它没有退出，请使用 `fg` 命令并按 Ctrl+C 来终止它。
检查 mmiotrace 是否因为缓冲区已满而丢失了事件。您可以执行以下操作：

```
$ grep -i lost mydump.txt
```

这会告诉您确切丢失了多少个事件。或者，使用以下命令查看内核日志，并查找“mmiotrace has lost events”警告：

```
$ dmesg
```

如果事件丢失，则跟踪记录不完整。您应该增加缓冲区大小并重新尝试。首先查看当前缓冲区的大小：

```
$ cat /sys/kernel/tracing/buffer_size_kb
```

这会给出一个数字。大约将这个数字翻倍并写回，例如：

```
$ echo 128000 > /sys/kernel/tracing/buffer_size_kb
```

然后从头开始。
如果您正在为某个驱动项目（如 Nouveau）进行跟踪，在发送结果之前，还应执行以下操作：

```
$ lspci -vvv > lspci.txt
$ dmesg > dmesg.txt
$ tar zcf pciid-nick-mmiotrace.tar.gz mydump.txt lspci.txt dmesg.txt
```

然后发送该 `.tar.gz` 文件。跟踪记录会大幅压缩。请将 “pciid” 和 “nick” 替换为您正在调查的硬件的 PCI ID 或型号名称以及您的昵称。

MMIOTrace 工作原理
-------------------

通过调用其中一个 `ioremap_*()` 函数，映射 PCI 总线上的地址以获得对硬件 I/O 内存的访问权限。MMIOTrace 被挂接到 `__ioremap()` 函数上，每当创建映射时都会被调用。映射是一个被记录到跟踪日志中的事件。请注意，ISA 范围的映射不会被捕获，因为这些映射始终存在并且直接返回。
MMIO 访问是通过页面错误记录的。在 `__ioremap()` 返回之前，映射的页面会被标记为不存在。任何对该页面的访问都会导致错误。页面错误处理器调用 MMIOTrace 来处理错误。MMIOTrace 将页面标记为存在，设置 TF 标志以实现单步执行，并退出错误处理器。引发错误的指令被执行，并进入调试陷阱。在这里，MMIOTrace 再次将页面标记为不存在。指令被解码以获取操作类型（读/写）、数据宽度和读取或写入的值。这些信息被存储到跟踪日志中。
在页面错误处理器中设置页面存在会导致 SMP 机器上的竞争条件。在单步执行期间，其他 CPU 可能自由运行在同一页面上，并且可能会在没有提示的情况下错过事件。在跟踪过程中重新启用其他 CPU 不被鼓励。

跟踪日志格式
-------------

原始日志是文本形式，可以轻松地通过 `grep` 和 `awk` 等工具进行过滤。一条记录就是日志中的一行。记录以一个关键词开始，后跟与关键词相关的参数。参数之间用空格分隔，或者一直延续到行尾。版本 20070824 的格式如下：

| 解释 | 关键词 | 空格分隔的参数 |
| --- | --- | --- |
| 读取事件 | R | 宽度、时间戳、映射ID、物理地址、值、PC、PID |
| 写入事件 | W | 宽度、时间戳、映射ID、物理地址、值、PC、PID |
| 映射事件 | MAP | 时间戳、映射ID、物理地址、虚拟地址、长度、PC、PID |
| 取消映射事件 | UNMAP | 时间戳、映射ID、PC、PID |
| 标记 | MARK | 时间戳、文本 |
| 版本 | VERSION | 字符串 "20070824" |
| 供读者的信息 | LSPCI | 一行来自 `lspci -v` 的输出 |
| PCI 地址映射 | PCIDEV | 从 `/proc/bus/pci/devices` 数据中空格分隔的内容 |
| 未知的操作码 | UNKNOWN | 时间戳、映射ID、物理地址、数据、PC、PID |

时间戳是以秒为单位的小数。物理地址是一个 PCI 总线地址，虚拟地址是一个内核虚拟地址。宽度是数据宽度（以字节为单位），值是数据值。映射ID是一个任意编号，用于标识在操作中使用的映射。PC 是程序计数器，PID 是进程ID。如果未记录PC，则其值为零。PID 始终为零，因为尚未支持跟踪用户空间内存中发起的 MMIO 访问。
例如，以下 `awk` 过滤器会传递所有针对物理地址范围 [0xfb73ce40, 0xfb800000] 的 32 位写入：

```
$ awk '/W 4 / { adr=strtonum($5); if (adr >= 0xfb73ce40 && adr < 0xfb800000) print; }'
```

开发人员工具
-------------

用户空间工具包括以下功能：
- 将数值地址和值替换为硬件寄存器名称
- 重放 MMIO 日志，即重新执行记录的写入操作
