======================================
页面所有者：跟踪每个页面的分配者
======================================

简介
====

页面所有者用于跟踪每个页面的分配者。它可以用来调试内存泄漏或查找占用大量内存的应用程序。在分配发生时，有关分配的信息（如调用堆栈和页面的分配顺序）将存储在每个页面对应的特定存储中。当我们需要了解所有页面的状态时，可以获取并分析这些信息。

尽管我们已经有了用于追踪页面分配/释放的追踪点（tracepoint），但使用它来分析谁分配了每个页面相对复杂。我们需要扩大追踪缓冲区以防止用户空间程序启动前的重叠。而且，启动后的程序会持续地导出追踪缓冲区以供后续分析，这可能会改变系统行为，并且与仅仅将信息保存在内存中的方式相比，这种方式不利于调试。

页面所有者还可以用于多种用途。例如，通过每个页面的gfp标志信息，可以获得精确的碎片统计信息。如果启用了页面所有者功能，这一功能已经实现并激活。欢迎其他用途的探索。

此外，页面所有者还可以显示所有堆栈及其当前分配的基本页面数量，这使我们能够快速了解内存的去向，而无需逐页筛选并匹配分配和释放操作。

默认情况下，页面所有者是禁用的。因此，如果您想使用它，需要在启动命令行中添加 "page_owner=on"。如果内核编译时包含了页面所有者功能，但在运行时由于未启用启动选项而禁用了该功能，则运行时开销很小。如果在运行时禁用，则不需要内存来存储所有者信息，因此没有运行时内存开销。并且，页面所有者仅在页面分配器的热点路径中插入两个不太可能执行的分支，如果未启用，则分配过程如同没有页面所有者的内核一样进行。这两个不太可能执行的分支不会对分配性能产生影响，特别是如果静态键跳转标签修补功能可用的话。以下是由于此功能导致的内核代码大小变化。

虽然启用页面所有者会使内核大小增加几千字节，但大部分代码位于页面分配器之外及其热点路径之外。编译包含页面所有者的内核并在需要时启用它，是调试内核内存问题的好选择。

有一个需要注意的地方，这是由实现细节引起的。页面所有者将信息存储在从 `struct page` 扩展出来的内存中。在稀疏内存系统中，这部分内存的初始化时间晚于页面分配器开始工作的时间，因此，在初始化之前，许多页面可能已经被分配，并且它们不会有所有者信息。为了修复这个问题，在初始化阶段会对这些早期分配的页面进行检查并标记为已分配。
虽然这并不意味着它们具有正确的所有者信息，但至少我们可以更准确地判断页面是否已被分配。在2GB内存的x86-64虚拟机环境中，捕获并标记了13343个早期分配的页面，尽管这些页面大多是从`struct page`扩展功能中分配的。无论如何，在此之后，没有页面处于未跟踪状态。

用法
=====

1) 构建用户空间辅助工具：

    ```
    cd tools/mm
    make page_owner_sort
    ```

2) 启用页面所有者：在启动命令行中添加`page_owner=on`
3) 执行您想要调试的任务
4) 分析页面所有者信息：

    ```
    cat /sys/kernel/debug/page_owner_stacks/show_stacks > stacks.txt
    cat stacks.txt
    post_alloc_hook+0x177/0x1a0
    get_page_from_freelist+0xd01/0xd80
    __alloc_pages+0x39e/0x7e0
    allocate_slab+0xbc/0x3f0
    ___slab_alloc+0x528/0x8a0
    kmem_cache_alloc+0x224/0x3b0
    sk_prot_alloc+0x58/0x1a0
    sk_alloc+0x32/0x4f0
    inet_create+0x427/0xb50
    __sock_create+0x2e4/0x650
    inet_ctl_sock_create+0x30/0x180
    igmp_net_init+0xc1/0x130
    ops_init+0x167/0x410
    setup_net+0x304/0xa60
    copy_net_ns+0x29b/0x4a0
    create_new_namespaces+0x4a1/0x820
    nr_base_pages: 16
    ...
    ```

将 `7000` 写入 `/sys/kernel/debug/page_owner_stacks/count_threshold`：
    
    ```
    echo 7000 > /sys/kernel/debug/page_owner_stacks/count_threshold
    cat /sys/kernel/debug/page_owner_stacks/show_stacks > stacks_7000.txt
    cat stacks_7000.txt
    post_alloc_hook+0x177/0x1a0
    get_page_from_freelist+0xd01/0xd80
    __alloc_pages+0x39e/0x7e0
    alloc_pages_mpol+0x22e/0x490
    folio_alloc+0xd5/0x110
    filemap_alloc_folio+0x78/0x230
    page_cache_ra_order+0x287/0x6f0
    filemap_get_pages+0x517/0x1160
    filemap_read+0x304/0x9f0
    xfs_file_buffered_read+0xe6/0x1d0 [xfs]
    xfs_file_read_iter+0x1f0/0x380 [xfs]
    __kernel_read+0x3b9/0x730
    kernel_read_file+0x309/0x4d0
    __do_sys_finit_module+0x381/0x730
    do_syscall_64+0x8d/0x150
    entry_SYSCALL_64_after_hwframe+0x62/0x6a
    nr_base_pages: 20824
    ...
    ```

将 `/sys/kernel/debug/page_owner` 的内容保存到文件中：
    
    ```
    cat /sys/kernel/debug/page_owner > page_owner_full.txt
    ./page_owner_sort page_owner_full.txt sorted_page_owner.txt
    ```

`page_owner_full.txt` 的一般输出如下所示：

```
Page allocated via order XXX, ..
PFN XXX ..
// Detailed stack

Page allocated via order XXX, ..
PFN XXX ..
```
// 详细堆栈
    默认情况下，它将执行完整的PFN转储，从给定的PFN开始，
    page_owner支持fseek
FILE *fp = fopen("/sys/kernel/debug/page_owner", "r");
    fseek(fp, pfn_start, SEEK_SET);

   ``page_owner_sort``工具忽略``PFN``行，将剩余的行放入buf中，
   使用正则表达式提取页序值，统计buf中的次数和页数，并最终根据参数进行排序。
查看``sorted_page_owner.txt``中每个页面的分配情况。一般输出格式如下::

	XXX次，XXX页：
	通过顺序XXX分配的页面，..

// 详细堆栈

   默认情况下，``page_owner_sort``根据buf中的次数进行排序。
如果想根据buf中的页数进行排序，请使用``-m``参数。
详细的参数如下：

   基本功能::

   排序：
		-a		按内存分配时间排序
		-m		按总内存排序
		-p		按进程ID（pid）排序
		-P		按线程组ID（tgid）排序
		-n		按任务命令名称排序
### 翻译成中文：

- `r`    按内存释放时间排序
- `s`    按堆栈跟踪排序
- `t`    按次数排序（默认）
- `--sort <order>`   指定排序顺序。排序语法是 `[+|-]key[,[+|-]key[,...]]`
  从 **标准格式说明符** 部分选择一个键。“+” 是可选的，因为默认方向是数值或字典序递增。
  允许混合使用缩写和完整形式的键。

示例：
  - `./page_owner_sort <input> <output> --sort=n,+pid,-tgid`
  - `./page_owner_sort <input> <output> --sort=at`

### 额外功能：

#### 剔除：
- `--cull <rules>`   指定剔除规则。剔除语法是 `key[,key[,...]]`。从 **标准格式说明符** 部分选择一个多字母键。
  `<rules>` 是一个以逗号分隔的形式表示的单一参数，提供了一种指定个体剔除规则的方法。认可的关键词在下面的 **标准格式说明符** 部分描述。
  `<rules>` 可以按照下面 **标准排序键** 部分描述的键序列 `k1,k2, ...` 来指定。允许混合使用缩写和完整形式的键。

示例：
  - `./page_owner_sort <input> <output> --cull=stacktrace`
  - `./page_owner_sort <input> <output> --cull=st,pid,name`
  - `./page_owner_sort <input> <output> --cull=n,f`

#### 过滤：
- `-f`   过滤掉已释放内存块的信息

#### 选择：
- `--pid <pidlist>`   按进程ID选择。这会选取出现在 `<pidlist>` 中的进程ID号码的块
--tgid <tgidlist>  根据 tgid 进行选择。这会选择那些线程组 ID 在 <tgidlist> 中出现的块。
--name <cmdlist>  根据任务命令名称进行选择。这会选择那些任务命令名称在 <cmdlist> 中出现的块。

<pidlist>, <tgidlist>, <cmdlist> 是以逗号分隔的形式呈现的单个参数，提供了一种指定单独选择规则的方法。

示例：
```
./page_owner_sort <input> <output> --pid=1
./page_owner_sort <input> <output> --tgid=1,2,3
./page_owner_sort <input> <output> --name name1,name2
```

标准格式说明
=============
::

  对于 --sort 选项：

  | 缩写 | 长格式       | 描述                                 |
  |------|--------------|--------------------------------------|
  | p    | pid          | 进程 ID                              |
  | tg   | tgid         | 线程组 ID                            |
  | n    | name         | 任务命令名称                         |
  | st   | stacktrace   | 页面分配的堆栈跟踪                   |
  | T    | txt          | 块的完整文本                         |
  | ft   | free_ts      | 页面释放时的时间戳                   |
  | at   | alloc_ts     | 页面分配时的时间戳                   |
  | ator | allocator    | 页面的内存分配器                     |

  对于 --cull 选项：

  | 缩写 | 长格式       | 描述                                 |
  |------|--------------|--------------------------------------|
  | p    | pid          | 进程 ID                              |
  | tg   | tgid         | 线程组 ID                            |
  | n    | name         | 任务命令名称                         |
  | f    | free         | 页面是否已经被释放                    |
  | st   | stacktrace   | 页面分配的堆栈跟踪                   |
  | ator | allocator    | 页面的内存分配器                     |
