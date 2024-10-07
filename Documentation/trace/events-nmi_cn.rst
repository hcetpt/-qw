NMI 追踪事件
============

这些事件通常会出现在这里：

	/sys/kernel/tracing/events/nmi

nmi_handler
-----------

如果你怀疑你的 NMI 处理程序占用了大量的 CPU 时间，你可能想使用这个追踪点。内核会在发现长时间运行的处理程序时发出警告：

	INFO: NMI handler took too long to run: 9.207 msecs

此追踪点允许你深入调查并获取更多细节。
假设你怀疑 `perf_event_nmi_handler()` 导致了一些问题，并且只想追踪该特定处理程序。你需要找到它的地址：

	$ grep perf_event_nmi_handler /proc/kallsyms
	ffffffff81625600 t perf_event_nmi_handler

再假设你只对那个函数真正占用大量 CPU 时间的情况感兴趣，比如每次占用一毫秒的时间。
请注意，内核的输出是以毫秒为单位的，但过滤器输入需要的是纳秒！你可以根据 'delta_ns' 进行过滤：

	cd /sys/kernel/tracing/events/nmi/nmi_handler
	echo 'handler==0xffffffff81625600 && delta_ns>1000000' > filter
	echo 1 > enable

这样，你的输出将会如下所示：

	$ cat /sys/kernel/tracing/trace_pipe
	<idle>-0     [000] d.h3   505.397558: nmi_handler: perf_event_nmi_handler() delta_ns: 3236765 handled: 1
	<idle>-0     [000] d.h3   505.805893: nmi_handler: perf_event_nmi_handler() delta_ns: 3174234 handled: 1
	<idle>-0     [000] d.h3   506.158206: nmi_handler: perf_event_nmi_handler() delta_ns: 3084642 handled: 1
	<idle>-0     [000] d.h3   506.334346: nmi_handler: perf_event_nmi_handler() delta_ns: 3080351 handled: 1
