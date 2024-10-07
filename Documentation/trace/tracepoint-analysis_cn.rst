使用事件和追踪点分析行为的笔记
=========================================================

**作者：Mel Gorman（PCL信息主要基于Ingo Molnar的邮件）**

1. 引言
===============

追踪点（参见Documentation/trace/tracepoints.rst）可以在不创建自定义内核模块的情况下，利用事件跟踪基础设施注册探针函数。简单来说，追踪点代表了系统内部发生的重要事件，可以与其他追踪点结合使用来构建系统的“全貌”。收集和解释这些事件的方法有很多。由于目前缺乏最佳实践，本文档描述了一些可用的方法。

本文档假定debugfs已挂载在/sys/kernel/debug，并且内核已配置了相应的跟踪选项。假设PCL工具tools/perf已安装并位于您的路径中。

2. 列出可用事件
===========================

2.1 标准工具
----------------------

所有可能的事件都可见于/sys/kernel/tracing/events。简单地执行以下命令：

  $ find /sys/kernel/tracing/events -type d

这将大致显示可用事件的数量。

2.2 PCL（Linux性能计数器）
----------------------------------------

包括追踪点在内的所有计数器和事件的发现和枚举都可以通过perf工具实现。获取可用事件列表只需执行：

  $ perf list 2>&1 | grep Tracepoint
  ext4:ext4_free_inode                     [Tracepoint event]
  ext4:ext4_request_inode                  [Tracepoint event]
  ext4:ext4_allocate_inode                 [Tracepoint event]
  ext4:ext4_write_begin                    [Tracepoint event]
  ext4:ext4_ordered_write_end              [Tracepoint event]
  [ .... 剩余输出省略 .... ]

3. 启用事件
==================

3.1 全局启用事件
------------------------------

关于如何全局启用事件的详细说明，请参见Documentation/trace/events.rst。一个简单的示例是启用与页面分配相关的所有事件：

  $ for i in `find /sys/kernel/tracing/events -name "enable" | grep mm_`; do echo 1 > $i; done

3.2 使用SystemTap全局启用事件
---------------------------------------------

在SystemTap中，可以通过调用kernel.trace()函数访问追踪点。下面是一个每5秒报告一次哪些进程正在分配页面的例子：

```
global page_allocs

probe kernel.trace("mm_page_alloc") {
  	page_allocs[execname()]++
}

function print_count() {
  	printf ("%-25s %-s\n", "#Pages Allocated", "Process Name")
  	foreach (proc in page_allocs-)
  		printf("%-25d %s\n", page_allocs[proc], proc)
  	printf ("\n")
  	delete page_allocs
}

probe timer.s(5) {
          print_count()
}
```

3.3 使用PCL全局启用事件
---------------------------------------

通过指定-a开关并分析sleep，可以在一段时间内检查系统范围内的事件：

```
$ perf stat -a \
	-e kmem:mm_page_alloc -e kmem:mm_page_free \
	-e kmem:mm_page_free_batched \
	sleep 10
Performance counter stats for 'sleep 10':

           9630  kmem:mm_page_alloc
           2143  kmem:mm_page_free
           7424  kmem:mm_page_free_batched

   10.002577764  seconds time elapsed
```

同样，也可以执行shell并按需退出以获取该时刻的报告。

3.4 局部启用事件
------------------------

Documentation/trace/ftrace.rst描述了如何使用set_ftrace_pid按线程启用事件。

3.5 使用PCL局部启用事件
-----------------------------------

可以使用PCL在进程运行期间局部激活和跟踪事件，例如：

```
$ perf stat -e kmem:mm_page_alloc -e kmem:mm_page_free \
		 -e kmem:mm_page_free_batched ./hackbench 10
Time: 0.909

    Performance counter stats for './hackbench 10':

          17803  kmem:mm_page_alloc
          12398  kmem:mm_page_free
           4827  kmem:mm_page_free_batched

    0.973913387  seconds time elapsed
```

4. 事件过滤
==================

Documentation/trace/ftrace.rst深入介绍了如何在ftrace中过滤事件。显然，使用grep和awk处理trace_pipe也是一种选择，任何读取trace_pipe的脚本也适用。
5. 使用PCL分析事件方差
=====================================

任何工作负载在运行之间都可能表现出差异，了解标准偏差是很重要的。通常，这需要性能分析师手动完成。如果离散事件的发生对性能分析师有用，则可以使用`perf`命令来实现这一目的：
  
  ```
  $ perf stat --repeat 5 -e kmem:mm_page_alloc -e kmem:mm_page_free -e kmem:mm_page_free_batched ./hackbench 10
  Time: 0.890
  Time: 0.895
  Time: 0.915
  Time: 1.001
  Time: 0.899
  
  性能计数器统计信息（5次运行）：

          16630  kmem:mm_page_alloc         ( ± 3.542% )
          11486  kmem:mm_page_free          ( ± 4.771% )
           4730  kmem:mm_page_free_batched  ( ± 2.325% )

    0.982653002  秒已用时间   ( ± 1.448% )
  ```

如果需要依赖于某些离散事件聚合的更高层次的事件，则需要开发一个脚本。使用`--repeat`选项，也可以通过`-a`和`sleep`命令查看系统级事件随时间的变化情况：
  
  ```
  $ perf stat -e kmem:mm_page_alloc -e kmem:mm_page_free -e kmem:mm_page_free_batched -a --repeat 10 sleep 1
  性能计数器统计信息（10次运行）：

           1066  kmem:mm_page_alloc         ( ± 26.148% )
            182  kmem:mm_page_free          ( ± 5.464% )
            890  kmem:mm_page_free_batched  ( ± 30.079% )

    1.002251757  秒已用时间   ( ± 0.005% )
  ```

6. 使用辅助脚本进行更高层次的分析
============================================

当启用事件时，触发的事件可以从`/sys/kernel/tracing/trace_pipe`中以人类可读的格式读取，尽管也存在二进制选项。通过对输出进行后处理，可以在适当的情况下获取更多相关信息。后处理示例包括：

  - 从`/proc`读取触发事件的PID的信息
  - 从一系列低层次事件中推导出高层次事件
  - 计算两个事件之间的延迟

`Documentation/trace/postprocess/trace-pagealloc-postprocess.pl`是一个示例脚本，可以从`STDIN`或一个追踪副本中读取`trace_pipe`。在线使用时，它可以中断一次生成报告而不退出，中断两次则退出。
简单来说，该脚本只是读取`STDIN`并计算事件数量，但它还可以做更多的事情，例如：

  - 从许多低层次事件中推导出高层次事件。如果从每个CPU列表中释放大量页面到主分配器，它会识别这是一个每个CPU的排空事件，尽管没有针对该事件的具体追踪点
  - 可以根据PID或单独的过程编号进行聚合
  - 如果内存外部碎片化，它可以报告该碎片化事件是严重的还是适度的
  - 在接收到关于PID的事件时，它可以记录其父进程是谁，以便如果大量事件来自非常短暂的进程，可以识别出创建所有辅助进程的父进程

7. 使用PCL进行低层次分析
================================

还可能需要确定程序中的哪些函数在内核中生成了事件。为此类分析开始，必须先记录数据。截至本文撰写时，这需要root权限：
  
  ```
  $ perf record -c 1 -e kmem:mm_page_alloc -e kmem:mm_page_free -e kmem:mm_page_free_batched ./hackbench 10
  Time: 0.894
  [ perf record: 捕获并写入了0.733 MB perf.data（约32010个样本）]
  ```

注意使用`-c 1`设置事件采样周期。默认采样周期非常高，以尽量减少开销，但收集的信息可能会非常粗略。
此记录输出了一个名为`perf.data`的文件，可以使用`perf report`进行分析：
  
  ```
  $ perf report
  # 样本数: 30922
  #
  # 开销    命令                      共享对象
  # ........  .........  ...............................
  #
      87.27%  hackbench  [vdso]
       6.85%  hackbench  /lib/i686/cmov/libc-2.9.so
       2.62%  hackbench  /lib/ld-2.9.so
       1.52%       perf  [vdso]
       1.22%  hackbench  ./hackbench
       0.48%  hackbench  [kernel]
       0.02%       perf  /lib/i686/cmov/libc-2.9.so
       0.01%       perf  /usr/bin/perf
       0.01%       perf  /lib/ld-2.9.so
       0.00%  hackbench  /lib/i686/cmov/libpthread-2.9.so
  #
  # （更多信息，请尝试：perf report --sort comm,dso,symbol）
  #
  ```

根据上述结果，绝大多数事件是在VDSO中触发的。对于简单的二进制文件，这种情况很常见，让我们看一个稍微不同的例子。在撰写本文的过程中，注意到X生成了大量的页面分配，让我们来看一下：
  
  ```
  $ perf record -c 1 -f -e kmem:mm_page_alloc -e kmem:mm_page_free -e kmem:mm_page_free_batched -p $(pidof X)

  这一操作在几秒钟后被中断，并执行：
  $ perf report
  # 样本数: 27666
  #
  # 开销  命令                            共享对象
  # ........  .......  ......................................
  ```
所以，几乎一半的事件发生在某个库中。要了解具体是哪个符号：
::

  $ perf report --sort comm,dso,symbol
  # 样本：27666
  #
  # 开销    命令                            共享对象  符号
  # ........  .......  .......................................  .....
#
      51.95%     Xorg  [vdso]                                   [.] 0x000000ffffe424
      47.93%     Xorg  /opt/gfx-test/lib/libpixman-1.so.0.13.1  [.] pixmanFillsse2
       0.09%     Xorg  /lib/i686/cmov/libc-2.9.so               [.] _int_malloc
       0.01%     Xorg  /opt/gfx-test/lib/libpixman-1.so.0.13.1  [.] pixman_region32_copy_f
       0.01%     Xorg  [kernel]                                 [k] read_hpet
       0.01%     Xorg  /opt/gfx-test/lib/libpixman-1.so.0.13.1  [.] get_fast_path
       0.00%     Xorg  [kernel]                                 [k] ftrace_trace_userstack

要查看函数 `pixmanFillsse2` 内部出现问题的地方：
::

  $ perf annotate pixmanFillsse2
  [ ... ]
    0.00 :         34eeb:       0f 18 08                prefetcht0 (%eax)
         :      }
         :
         :      extern __inline void __attribute__((__gnu_inline__, __always_inline__, _
         :      _mm_store_si128 (__m128i *__P, __m128i __B) :      {
         :        *__P = __B;
   12.40 :         34eee:       66 0f 7f 80 40 ff ff    movdqa %xmm0,-0xc0(%eax)
    0.00 :         34ef5:       ff
   12.40 :         34ef6:       66 0f 7f 80 50 ff ff    movdqa %xmm0,-0xb0(%eax)
    0.00 :         34efd:       ff
   12.39 :         34efe:       66 0f 7f 80 60 ff ff    movdqa %xmm0,-0xa0(%eax)
    0.00 :         34f05:       ff
   12.67 :         34f06:       66 0f 7f 80 70 ff ff    movdqa %xmm0,-0x90(%eax)
    0.00 :         34f0d:       ff
   12.58 :         34f0e:       66 0f 7f 40 80          movdqa %xmm0,-0x80(%eax)
   12.31 :         34f13:       66 0f 7f 40 90          movdqa %xmm0,-0x70(%eax)
   12.40 :         34f18:       66 0f 7f 40 a0          movdqa %xmm0,-0x60(%eax)
   12.31 :         34f1d:       66 0f 7f 40 b0          movdqa %xmm0,-0x50(%eax)

乍一看，时间花在了将位图复制到显卡上。要进一步确定为什么位图会被大量复制，可以作为一个起点，移除库路径中的一个古老的 `libpixmap` 版本，这个版本已经被遗忘了好几个月！
