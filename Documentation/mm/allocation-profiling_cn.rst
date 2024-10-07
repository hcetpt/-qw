SPDX 许可证标识符: GPL-2.0

===========================
内存分配剖析
===========================

所有内存分配的低开销（适合生产环境）会计，通过文件和行号进行跟踪。

使用方法：
kconfig 选项：
- CONFIG_MEM_ALLOC_PROFILING

- CONFIG_MEM_ALLOC_PROFILING_ENABLED_BY_DEFAULT

- CONFIG_MEM_ALLOC_PROFILING_DEBUG
  对于由于缺少注释而未被记录的分配增加警告信息

启动参数：
  sysctl.vm.mem_profiling=0|1|never

  当设置为 "never" 时，内存分配剖析的开销被最小化，并且无法在运行时启用（sysctl 变为只读）
当 CONFIG_MEM_ALLOC_PROFILING_ENABLED_BY_DEFAULT=y 时，默认值为 "1"
当 CONFIG_MEM_ALLOC_PROFILING_ENABLED_BY_DEFAULT=n 时，默认值为 "never"
sysctl：
  /proc/sys/vm/mem_profiling

运行时信息：
  /proc/allocinfo

示例输出：

```
root@moria-kvm:~# sort -g /proc/allocinfo | tail | numfmt --to=iec
        2.8M    22648 fs/kernfs/dir.c:615 func:__kernfs_new_node
        3.8M      953 mm/memory.c:4214 func:alloc_anon_folio
        4.0M     1010 drivers/staging/ctagmod/ctagmod.c:20 [ctagmod] func:ctagmod_start
        4.1M        4 net/netfilter/nf_conntrack_core.c:2567 func:nf_ct_alloc_hashtable
        6.0M     1532 mm/filemap.c:1919 func:__filemap_get_folio
        8.8M     2785 kernel/fork.c:307 func:alloc_thread_stack_node
         13M      234 block/blk-mq.c:3421 func:blk_mq_alloc_rqs
         14M     3520 mm/mm_init.c:2530 func:alloc_large_system_hash
         15M     3656 mm/readahead.c:247 func:page_cache_ra_unbounded
         55M     4887 mm/slub.c:2259 func:alloc_slab_page
        122M    31168 mm/page_ext.c:270 func:alloc_page_ext
```

工作原理
===================

内存分配剖析基于代码标记，这是一种声明静态结构体（通常以某种方式描述文件和行号，因此称为代码标记）的库，然后在运行时找到并操作这些结构体。
- 例如，在 debugfs/procfs 中迭代打印它们
为了添加对分配调用的记录，我们将其替换为一个宏调用 alloc_hooks()，该宏调用会执行以下操作：
- 声明一个代码标签
- 将其指针存放在 task_struct 中
- 调用实际的分配函数
- 最后，恢复 task_struct 的分配标签指针到之前的值
这使得 alloc_hooks() 调用可以嵌套，最近的一个生效。这对于 mm/ 代码内部的分配很重要，这些分配不应属于外部分配上下文，而应单独计数：例如，slab 对象扩展向量，或者当 slab 从页面分配器中分配页面时。
因此，正确使用要求确定在分配调用栈中哪个函数应该被打上标签。有许多辅助函数基本上包装了如 kmalloc() 并做了更多的工作，然后在多个地方被调用；我们通常希望在调用这些辅助函数的地方进行记录，而不是在辅助函数本身。
要修复某个给定的辅助函数，例如 foo()，请执行以下操作：
- 将其分配调用切换为 _noprof() 版本，例如 kmalloc_noprof()

- 将其重命名为 foo_noprof()

- 定义 foo() 的宏版本如下：

  #define foo(...) alloc_hooks(foo_noprof(__VA_ARGS__))

也可以在自己的数据结构中存储一个分配标签的指针。当实现一个通用的数据结构，代表其他代码进行分配时，这样做是有意义的——例如，rhashtable 代码。这样，我们可以按 rhashtable 类型拆分 /proc/allocinfo 中的 rhashtable.c 大条目。
要这样做：
- 钩住（拦截）你的数据结构的初始化函数，就像钩住任何其他分配函数一样
- 在你的初始化函数中，使用便捷宏 `alloc_tag_record()` 来记录你数据结构中的分配标签
- 然后，以以下形式进行分配：
  `alloc_hooks_tag(ht->your_saved_tag, kmalloc_noprof(...))`
