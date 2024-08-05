... SPDX 许可证标识符: GPL-2.0

======
TLB（转换后备缓冲区）
======

当内核取消映射或修改某段内存的属性时，它有两种选择：

 1. 使用两条指令序列刷新整个 TLB。这是一个快速操作，但会导致附带损害：除了我们试图刷新的部分之外，其他区域的 TLB 条目也会被销毁，并且必须在稍后以一定代价重新填充。
2. 使用 `invlpg` 指令逐页无效化。这可能需要更多的指令，但它是一个更精确的操作，对其他 TLB 条目不会造成任何附带损害。
选择哪种方法取决于以下几个因素：

 1. 执行刷新的大小。显然，对于整个地址空间的刷新来说，刷新整个 TLB 要比执行 2^48/PAGE_SIZE 次单页刷新更好。
2. TLB 的内容。如果 TLB 是空的，那么全局刷新不会造成任何附带损害，而所有单独的刷新将变成无用功。
3. TLB 的大小。TLB 越大，全局刷新造成的附带损害就越大。因此，TLB 越大，单页刷新看起来就越有吸引力。数据和指令有不同的 TLB，不同页面大小也有各自的 TLB。
4. 微架构。现代 CPU 上的 TLB 已经变成了多级缓存，全局刷新相对于单页刷新变得更加昂贵。
很明显，内核无法知道所有这些信息，特别是在给定刷新时 TLB 的内容。刷新的大小也会根据工作负载而有很大变化。实际上没有一个“正确”的点来做出选择。

如果你发现 `invlpg` 指令（或靠近它的指令）在性能分析中排名很高，你可能正在进行太多的单页无效化。如果你认为单页无效化被调用得太频繁，你可以降低可调节参数：

	/sys/kernel/debug/x86/tlb_single_page_flush_ceiling

这将导致我们在更多情况下进行全局刷新。
将其降低到 0 将禁用单页刷新的使用。
将其设置为 1 是一个非常保守的设置，在正常情况下不应该需要将其设置为 0。
尽管在 x86 上单个无效化操作（flush）保证可以无效化完整的 2MB [1]_，hugetlbfs 始终使用全范围的无效化操作。THP 被完全视同普通内存处理。你可能会在性能剖析中看到 `flush_tlb_mm_range()` 内的 `invlpg` 调用，或者你可以使用 `trace_tlb_flush()` 的跟踪点来确定无效化操作所花费的时间。
基本上，你需要权衡执行 `invlpg` 所消耗的周期与之后重新填充 TLB 所需的周期。
你可以通过使用性能计数器和 'perf stat' 来衡量 TLB 重填的开销，例如：

```bash
perf stat -e \
    cpu/event=0x8,umask=0x84,name=dtlb_load_misses_walk_duration/,\
    cpu/event=0x8,umask=0x82,name=dtlb_load_misses_walk_completed/,\
    cpu/event=0x49,umask=0x4,name=dtlb_store_misses_walk_duration/,\
    cpu/event=0x49,umask=0x2,name=dtlb_store_misses_walk_completed/,\
    cpu/event=0x85,umask=0x4,name=itlb_misses_walk_duration/,\
    cpu/event=0x85,umask=0x2,name=itlb_misses_walk_completed/
```

这适用于 IvyBridge 时代的 CPU（如 i5-3320M）。不同的 CPU 可能会有不同名称的计数器，但至少它们应该以某种形式存在。你可以使用 pmu-tools 的 `ocperf list`（https://github.com/andikleen/pmu-tools）来找到特定 CPU 的正确计数器。
.. [1] 在英特尔的 SDM “4.10.4.2 推荐的无效化” 脚注中提到：“即使对于大于 4 KB 的页面，一次执行 INVLPG 也已足够。”
