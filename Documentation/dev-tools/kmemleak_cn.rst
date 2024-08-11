### 内核内存泄漏检测器
=================================

Kmemleak 提供了一种类似“追踪垃圾收集器”<https://en.wikipedia.org/wiki/Tracing_garbage_collection> 的方式来检测可能的内核内存泄漏，不同之处在于这些孤立的对象不会被释放，而是通过 `/sys/kernel/debug/kmemleak` 报告。Valgrind 工具（`memcheck --leak-check`）使用了类似的方法来检测用户空间应用程序中的内存泄漏。

#### 使用方法

需要启用 “Kernel hacking” 中的 CONFIG_DEBUG_KMEMLEAK。默认情况下，一个内核线程每10分钟扫描一次内存，并打印找到的新孤立对象的数量。如果尚未挂载 `debugfs`，可以使用以下命令进行挂载：

```sh
# mount -t debugfs nodev /sys/kernel/debug/
```

要显示所有可能扫描到的内存泄漏的详细信息，请执行：

```sh
# cat /sys/kernel/debug/kmemleak
```

要触发中间内存扫描，请执行：

```sh
# echo scan > /sys/kernel/debug/kmemleak
```

要清除当前所有可能的内存泄漏列表，请执行：

```sh
# echo clear > /sys/kernel/debug/kmemleak
```

之后再次读取 `/sys/kernel/debug/kmemleak` 文件时，新的泄漏就会出现。

请注意，孤立对象按照它们分配的顺序列出，列表开始处的一个对象可能导致后续其他对象也被报告为孤立。

可以通过写入 `/sys/kernel/debug/kmemleak` 文件来修改内存扫描参数。支持以下参数：

- off
    禁用 kmemleak（不可逆）
- stack=on
    启用任务堆栈扫描（默认）
- stack=off
    禁用任务堆栈扫描
- scan=on
    启动自动内存扫描线程（默认）
- scan=off
    停止自动内存扫描线程
- scan=<secs>
    设置自动内存扫描周期（秒数，默认600，0表示停止自动扫描）
- scan
    触发内存扫描
- clear
    清除当前内存泄漏嫌疑列表，即标记所有已报告的未引用对象为灰色，
    或者如果 kmemleak 已被禁用，则释放所有 kmemleak 对象
- dump=<addr>
    显示在 <addr> 处找到的对象的信息

可以在启动时通过在内核命令行中传递 `kmemleak=off` 来禁用 kmemleak。

在 kmemleak 初始化之前可能会分配或释放内存，这些操作会被存储在一个早期的日志缓冲区中。该缓冲区的大小可通过 CONFIG_DEBUG_KMEMLEAK_MEM_POOL_SIZE 配置选项设置。

如果启用了 CONFIG_DEBUG_KMEMLEAK_DEFAULT_OFF，kmemleak 默认是禁用的。在内核命令行中传递 `kmemleak=on` 可以启用此功能。

如果你遇到如 “Error while writing to stdout” 或 “write_loop: Invalid argument” 这样的错误，请确保 kmemleak 已经正确启用。

#### 基本算法

通过跟踪 :c:func:`kmalloc`、:c:func:`vmalloc`、:c:func:`kmem_cache_alloc` 和其他相关函数的调用来记录内存分配，并将指针及其附加信息（如大小和堆栈跟踪）存储在红黑树中。

相应的释放函数调用会被跟踪，并从 kmemleak 数据结构中移除这些指针。

如果在扫描内存（包括保存的寄存器）时找不到指向某块已分配内存起始地址或该块内存内部任何位置的指针，则认为这块内存是孤立的。这意味着内核可能无法将分配内存的地址传给释放函数，因此这块内存被认为是内存泄漏。
扫描算法步骤：

1. 将所有对象标记为白色（稍后将把仍保持白色的对象视为孤立）
2. 从数据段和栈开始扫描内存，检查值是否与红黑树中存储的地址匹配。如果找到指向白色对象的指针，则将该对象添加到灰色列表
3. 扫描灰色对象以查找匹配的地址（某些白色对象可能会变成灰色并被添加到灰色列表的末尾），直到灰色集合处理完毕
4. 剩余的白色对象被视为孤立，并通过 /sys/kernel/debug/kmemleak 进行报告

一些已分配的内存块在内核内部数据结构中存储有指针，因此它们无法被检测为孤立。为了避免这种情况，kmemleak还可以存储需要找到的指向块地址范围内地址的值的数量，以便不将该块视为泄露。一个例子是 __vmalloc()。
测试特定部分使用kmemleak
-------------------------------

在初始启动时，您的 /sys/kernel/debug/kmemleak 输出页面可能非常长。如果您在开发过程中遇到很多错误代码，情况也可能如此。为了应对这些情况，您可以使用 'clear' 命令从 /sys/kernel/debug/kmemleak 输出中清除所有报告的未引用对象。通过在 'clear' 后执行 'scan'，您可以发现新的未引用对象；这应该有助于测试特定代码段
要使用干净的kmemleak按需测试关键部分，请执行如下操作：

```sh
# echo clear > /sys/kernel/debug/kmemleak
... 测试您的内核或模块 ..
# echo scan > /sys/kernel/debug/kmemleak
```

然后像往常一样获取报告：

```sh
# cat /sys/kernel/debug/kmemleak
```

释放kmemleak内部对象
------------------------

为了允许用户禁用kmemleak或因致命错误后仍然可以访问先前发现的内存泄露，当kmemleak被禁用时，不会释放内部kmemleak对象，而这些对象可能会占用大量物理内存
在这种情况下，您可以通过以下命令回收内存：

```sh
# echo clear > /sys/kernel/debug/kmemleak
```

kmemleak API
--------------

请参阅include/linux/kmemleak.h头文件以获取函数原型：
- `kmemleak_init`		 - 初始化kmemleak
- `kmemleak_alloc`		 - 通知内存块分配
- `kmemleak_alloc_percpu`	 - 通知每个CPU的内存块分配
- `kmemleak_vmalloc`		 - 通知vmalloc()内存分配
- `kmemleak_free`		 - 通知内存块释放
- `kmemleak_free_part`	 - 通知部分内存块释放
- `kmemleak_free_percpu`	 - 通知每个CPU的内存块释放
- `kmemleak_update_trace`	 - 更新对象分配堆栈跟踪
- `kmemleak_not_leak`	 - 标记一个对象不是泄露
- `kmemleak_ignore`		 - 不扫描也不报告对象为泄露
- `kmemleak_scan_area`	 - 在内存块中添加扫描区域
- `kmemleak_no_scan`	 - 不扫描内存块
- `kmemleak_erase`		 - 清除指针变量中的旧值
- `kmemleak_alloc_recursive` - 类似于kmemleak_alloc但检查递归性
- `kmemleak_free_recursive`	 - 类似于kmemleak_free但检查递归性

以下函数接收物理地址作为对象指针，并且仅在地址具有低内存映射的情况下执行相应的操作：

- `kmemleak_alloc_phys`
- `kmemleak_free_part_phys`
- `kmemleak_ignore_phys`

处理误报/漏报
------------------------------

误报是指实际存在的内存泄露（孤立对象）但由于在内存扫描期间找到的值指向这些对象而没有被kmemleak报告。为了减少误报数量，kmemleak提供了kmemleak_ignore、kmemleak_scan_area、kmemleak_no_scan 和 kmemleak_erase 函数（见上文）。任务栈也会增加误报的数量，默认情况下不会启用其扫描
误报是指错误地报告为内存泄露（孤立）的对象。对于已知不是泄露的对象，kmemleak提供了kmemleak_not_leak函数。如果已知内存块不包含其他指针，也可以使用kmemleak_ignore，它将不再被扫描
有些报告的泄露只是暂时的，特别是在SMP系统上，因为指针可能暂时存储在CPU寄存器或栈中。kmemleak定义了MSECS_MIN_AGE（默认为1000），代表对象被报告为内存泄露所需的最小年龄
限制和缺点
------------------

主要缺点是内存分配和释放性能下降。为了避免其他损失，只有在读取/sys/kernel/debug/kmemleak文件时才进行内存扫描。无论如何，此工具旨在用于调试目的，在这种情况下，性能可能不是最重要的要求
为了保持算法简单，kmemleak会扫描指向块地址范围内的任何地址的值。这可能导致误报数量增加。然而，真实的内存泄露最终很可能会显现出来。
另一个导致假阴性的来源是非指针值中存储的数据。在未来的版本中，kmemleak可以只扫描已分配结构中的指针成员。此功能将解决上述许多假阴性的情况。

该工具可能会报告假阳性。这些情况包括：分配的内存块不需要被释放（如某些init_call函数中的情况），指针通过非标准container_of宏的方式计算得出，或者指针存储在kmemleak未扫描的位置。页面分配和ioremap操作不会被追踪。

使用kmemleak-test进行测试
------------------------------

要检查是否已经设置好使用kmemleak的环境，可以使用kmemleak-test模块，这是一个故意泄露内存的模块。将CONFIG_SAMPLE_KMEMLEAK设置为模块（不能作为内置使用），并启用kmemleak启动内核。加载该模块，并执行一次扫描：

        # modprobe kmemleak-test
        # echo scan > /sys/kernel/debug/kmemleak

请注意，你可能不会立即或在第一次扫描时就得到结果。当kmemleak获得结果后，它会记录“kmemleak: 新发现疑似内存泄漏的数量”。然后你可以阅读文件查看详情：

        # cat /sys/kernel/debug/kmemleak
        未引用的对象 0xffff89862ca702e8 (大小 32 字节)：
          进程名 "modprobe"，进程ID 2088，时间戳 4294680594（持续时间 375.486秒）
          十六进制转储（前32字节）：
            6b 6b 6b 6b 6b 6b 6b 6b 6b 6b 6b 6b 6b 6b 6b 6b  kkkkkkkkkkkkkkkk
            6b 6b 6b 6b 6b 6b 6b 6b 6b 6b 6b 6b 6b 6b 6b a5  kkkkkkkkkkkkkkk
回溯：
            [<00000000e0a73ec7>] 0xffffffffc01d2036
            [<000000000c5d2a46>] do_one_initcall+0x41/0x1df
            [<0000000046db7e0a>] do_init_module+0x55/0x200
            [<00000000542b9814>] load_module+0x203c/0x2480
            [<00000000c2850256>] __do_sys_finit_module+0xba/0xe0
            [<000000006564e7ef>] do_syscall_64+0x43/0x110
            [<000000007c873fa6>] entry_SYSCALL_64_after_hwframe+0x44/0xa9
        ..
卸载模块（使用`rmmod kmemleak_test`）也应该触发一些kmemleak的结果。
