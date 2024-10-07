=========================
硬件延迟检测器
=========================

简介
-------------

硬件延迟检测器（tracer hwlat_detector）是一种特殊用途的追踪器，用于检测由于特定底层硬件或固件行为所引起的系统大延迟，与Linux本身无关。该代码最初是为了在x86系统上检测SMI（系统管理中断）而开发的，但此补丁集并不限于x86平台。最初是为“RT”补丁编写，因为实时内核对延迟非常敏感。
SMI不由Linux内核处理，这意味着内核甚至不知道它们的发生。SMI由BIOS代码设置，并由BIOS代码处理，通常用于处理诸如温度传感器和风扇管理等“关键”事件。有时，SMI也用于其他任务，并且这些任务可能在处理程序中花费大量时间（有时以毫秒为单位）。显然，如果您试图将事件服务延迟保持在微秒范围内，这将是一个问题。
硬件延迟检测器通过占用一个CPU一段时间（中断被禁用），轮询CPU的时间戳计数器（TSC），然后查找TSC数据中的间隙来工作。任何间隙都表明轮询过程中发生了中断，而由于中断被禁用，唯一可能造成这种情况的就是SMI或其他硬件问题（或者NMI，但那些可以跟踪）。
请注意，hwlat检测器绝不能在生产环境中使用。它旨在手动运行以确定硬件平台是否存在长时间系统固件服务例程的问题。

使用方法
------

将ASCII文本“hwlat”写入追踪系统的current_tracer文件（挂载在/sys/kernel/tracing或/sys/kernel/tracing）。可以重新定义以微秒（us）为单位的阈值，超过该阈值的延迟峰值将被考虑在内。
示例：

	# echo hwlat > /sys/kernel/tracing/current_tracer
	# echo 100 > /sys/kernel/tracing/tracing_thresh

/sys/kernel/tracing/hwlat_detector接口包含以下文件：

  - width - 持有CPU进行采样的时间段（微秒）
            必须小于总的窗口大小（强制执行）
  - window - 总的采样周期，width位于其中（微秒）

默认情况下，width设置为500,000，window设置为1,000,000，这意味着每1,000,000微秒（1秒），hwlat检测器将占用500,000微秒（0.5秒）。如果在启用hwlat追踪器时tracing_thresh包含零，则会将其更改为默认值10微秒。如果观察到任何超过阈值的延迟，则数据将被写入追踪环形缓冲区。
两个周期之间的最小睡眠时间为1毫秒。即使width小于窗口之间1毫秒的间隔，也要允许系统不至于完全饥饿。
如果在启动hwlat检测器时tracing_thresh为零，则加载另一个追踪器后会将其重置为零。注意，hwlat检测器最后一次使用的tracing_thresh值将被保存，如果再次启动hwlat检测器时tracing_thresh仍为零，则将恢复该值。
以下追踪目录文件由hwlat_detector使用：

在/sys/kernel/tracing中：

 - tracing_threshold - 要考虑的最小延迟值（微秒）
 - tracing_max_latency - 实际观察到的最大硬件延迟（微秒）
 - tracing_cpumask - 用于迁移hwlat线程的CPU
 - hwlat_detector/width - 在窗口内旋转指定的时间（微秒）
 - hwlat_detector/window - 两次（width）运行之间的时间（微秒）
 - hwlat_detector/mode - 线程模式

默认情况下，一个hwlat检测器的内核线程将在每个新窗口开始时，按照循环方式迁移到cpumask中指定的每个CPU。可以通过更改线程模式来改变这种行为，可用选项如下：

 - none: 不强制迁移
 - round-robin: 迁移到cpumask中指定的每个CPU（默认）
 - per-cpu: 为tracing_cpumask中的每个CPU创建一个线程
