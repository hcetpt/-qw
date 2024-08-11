SPDX 许可证标识符: GPL-2.0

====================================================
`pin_user_pages()` 及相关调用
====================================================

.. contents:: 目录

概述
========

本文档描述了以下函数::

 pin_user_pages()
 pin_user_pages_fast()
 pin_user_pages_remote()

FOLL_PIN 的基本描述
=============================

FOLL_PIN 和 FOLL_LONGTERM 是可以传递给 get_user_pages*()（简称 "gup"）系列函数的标志。FOLL_PIN 与 gup 内部相关联，意味着它不应该出现在 gup 调用现场。这样相关的包装函数（如 pin_user_pages*() 等）能够设置这些标志的正确组合，并检查可能的问题。
另一方面，允许在 gup 调用现场设置 FOLL_LONGTERM 标志。
这是为了避免创建大量的包装函数来覆盖 get*()、pin*()、FOLL_LONGTERM 以及更多情况的所有组合。此外，pin_user_pages*() 接口与 get_user_pages*() 接口明显不同，因此这是一个自然的分界线，也是进行单独包装调用的好时机。
换句话说，对于 DMA 固定的页面使用 pin_user_pages*()，对于其他情况使用 get_user_pages*()。文档稍后会详细描述五种情形，以进一步澄清这一概念。
对于特定的 gup 调用，FOLL_PIN 和 FOLL_GET 是互斥的。然而，多个线程和调用现场可以自由地通过 FOLL_PIN 和 FOLL_GET 来固定相同的 struct page。只是调用现场需要选择其中之一，而不是 struct page 本身。
FOLL_PIN 的实现几乎与 FOLL_GET 相同，只是 FOLL_PIN 使用了不同的引用计数技术。
FOLL_PIN 是 FOLL_LONGTERM 的先决条件。换言之，FOLL_LONGTERM 是 FOLL_PIN 的一种更严格的情况。
每个包装器设置哪些标志
===================================

对于这些 pin_user_pages*() 函数，FOLL_PIN 会与调用者提供的任何 gup 标志进行 OR 操作。调用者必须提供一个非空的 struct pages 数组，然后该函数通过将每个元素增加一个特殊值：GUP_PIN_COUNTING_BIAS 来固定页面。
对于大型 folio，不使用 GUP_PIN_COUNTING_BIAS 方案。相反，利用 struct folio 中可用的额外空间直接存储 pincount。
这种方法对于大型页避免了下面讨论的计数上限问题。这些限制在使用巨大页面时会严重加剧，因为每个尾页都会给头部页面增加一个引用计数。实际上，测试揭示了如果没有单独的固定计数（pincount）字段，在某些巨大的页面压力测试中会出现引用计数溢出的问题。
这也意味着巨大页面和大型页不会遭受下面提到的假阳性问题。

### 函数
----------
`pin_user_pages`          `FOLL_PIN` 总是由这个函数内部设置
`pin_user_pages_fast`     `FOLL_PIN` 总是由这个函数内部设置
`pin_user_pages_remote`   `FOLL_PIN` 总是由这个函数内部设置
对于这些 `get_user_pages*()` 函数，可能根本没有指定 `FOLL_GET`。
行为比上面的情况稍微复杂一些。如果 `FOLL_GET` 没有被指定，
但是调用者传递了一个非空的 `struct pages*` 数组，那么函数
会为你设置 `FOLL_GET`，并继续通过增加每个页面的引用计数 +1 来固定页面。

### 函数
----------
`get_user_pages`          `FOLL_GET` 有时由这个函数内部设置
`get_user_pages_fast`     `FOLL_GET` 有时由这个函数内部设置
`get_user_pages_remote`   `FOLL_GET` 有时由这个函数内部设置

### 跟踪 DMA 固定的页面
=========================

跟踪 DMA 固定的页面的一些关键设计约束及解决方案：

* 需要实际的每个 `struct page` 的引用计数。这是因为多个进程可能会固定和释放同一个页面。
* 假阳性（报告页面已被 DMA 固定，而实际上并没有）是可以接受的，但假阴性是不可接受的。
* 结构体 `page` 的大小不能为此而增加，并且所有字段都已经在使用中。
* 鉴于上述情况，我们可以重用 `page->_refcount` 字段的一部分高位来作为 DMA 锁定计数。所谓的“一部分”，意味着我们不是将 `page->_refcount` 分割成位字段，而是简单地向其添加一个中等偏大的值（最初选择为 1024：10 位）作为 DMA 锁定计数的偏移量。这样会产生一种模糊的行为：如果一个页面被 `get_page()` 调用了 1024 次，则它会显示为有一个 DMA 锁定计数。
  再次强调，这种做法是可以接受的。
  这也带来了一些限制：可用的计数器位数只有 31 - 10 = 21 位，而这些位每次增加 10 位。
* 由于这一限制，当使用 `FOLL_PIN` 时对零页进行了特殊处理。我们只是假装锁定了零页——我们不会改变它的引用计数或锁定计数（因为它总是存在的，所以没有必要）。解锁定函数对零页也不做任何操作。这对调用者来说是透明的。
* 调用者必须明确请求“DMA 页面锁定跟踪”。换句话说，仅仅调用 `get_user_pages()` 是不够的；必须使用一组新的函数，如 `pin_user_page()` 及其相关函数。
* 关于何时使用哪些标志 (`FOLL_PIN`, `FOLL_GET`, `FOLL_LONGTERM`)：

感谢 Jan Kara、Vlastimil Babka 和其他几位 `-mm` 社区成员描述了以下分类：

**案例 1：直接 I/O (DIO)**
---
存在一些指向用作 DIO 缓冲区的页面的 GUP 引用。这些缓冲区需要的时间相对较短（因此它们不属于“长期”）。没有提供与 `page_mkclean()` 或 `munmap()` 特别的同步。因此，在调用现场应设置的标志是：

    FOLL_PIN

...但是，调用现场不应该直接设置 `FOLL_PIN`，而应该使用其中一个 `pin_user_pages*()` 函数来设置 `FOLL_PIN`。

**案例 2：RDMA**
---
存在一些指向用作 DMA 缓冲区的页面的 GUP 引用。这些缓冲区需要很长时间（即“长期”）。没有提供与 `page_mkclean()` 或 `munmap()` 特别的同步。因此，在调用现场应设置的标志是：

    FOLL_PIN | FOLL_LONGTERM

注意：有些页面，例如 DAX 页面，不能使用长期锁定。这是因为 DAX 页面没有单独的页面缓存，因此“锁定”意味着锁定文件系统块，而这目前尚未得到支持。

**案例 3：MMU 通知注册，无论是否有可重放的页面错误硬件**
---
设备驱动程序可以通过 `get_user_pages*()` 来锁定页面，并为该内存范围注册 MMU 通知回调。然后，在接收到通知中的“使范围无效”回调时，停止设备使用该范围，并解锁页面。还可能有其他的方案，比如显式地同步待处理的 I/O，以达到类似的效果。
或者，如果硬件支持可重放的页面错误，那么设备驱动程序可以完全避免锁定（这是最理想的），具体做法如下：像上面那样注册 MMU 通知回调，但在回调中不是停止设备并解锁，而是简单地从设备的页表中删除该范围。
无论如何，只要驱动程序在MMU通知回调时解除固定页面，
那么与文件系统和内存管理（如page_mkclean()、munmap()等）之间就有适当的同步。因此，无需设置任何标志。
情况4：仅针对struct page操作的固定
-------------------------------------
如果只影响struct page数据（而非页面所跟踪的实际内存内容），则普通的GUP调用就足够了，无需设置任何标志。
情况5：为了写入页面内的数据而固定
---------------------------------------
尽管没有涉及DMA或直接I/O，仅仅是“固定、写入页面数据、解除固定”的简单案例也会造成问题。情况5可以被视为情况1、情况2以及任何触发该模式的超集。换句话说，即使代码不属于情况1或情况2，也可能需要FOLL_PIN，例如：

正确做法（使用FOLL_PIN调用）：
    pin_user_pages()
    写入页面内的数据
    unpin_user_pages()

错误做法（使用FOLL_GET调用）：
    get_user_pages()
    写入页面内的数据
    put_page()

page_maybe_dma_pinned()：固定页面的根本目的
==========================================
标记页面为“DMA固定”或“GUP固定”的根本目的是能够查询，“这个页面是否是DMA固定的？”这使得像page_mkclean()这样的代码（以及一般的文件系统回写代码）能够在页面由于此类固定无法被解除映射时做出明智的决策。
在这种情况下应该做什么是多年来一系列讨论和辩论的主题（参见本文档末尾的参考）。这是一个待办事项：一旦确定解决方案后填写详细信息。同时，可以说提供以下功能是一个解决长期存在的GUP+DMA问题的前提条件： ::

        static inline bool page_maybe_dma_pinned(struct page *page)

另一种理解FOLL_GET、FOLL_PIN和FOLL_LONGTERM的方式
====================================================
另一种理解这些标志的方法是将它们视为一种限制级别的进展：
FOLL_GET适用于对struct page进行操作，而不影响struct page所引用的数据。FOLL_PIN是FOLL_GET的替代品，适用于短期内固定那些其数据将被访问的页面。因此，FOLL_PIN是一种更严格的固定形式。最后，FOLL_LONGTERM是一种更加严格的案例，它以FOLL_PIN为前提：这是指那些将被长期固定的页面，并且其数据会被访问的情况。
单元测试
=========
此文件:: 

 tools/testing/selftests/mm/gup_test.c

具有以下新的调用来测试新的pin*()包装函数：

* PIN_FAST_BENCHMARK (./gup_test -a)
* PIN_BASIC_TEST (./gup_test -b)

你可以通过两个新的/proc/vmstat条目来监控自系统启动以来已经获取和释放了多少个DMA固定的页面： ::

    /proc/vmstat/nr_foll_pin_acquired
    /proc/vmstat/nr_foll_pin_released

正常情况下，这两个值相等，除非存在任何长期的[R]DMA固定，或者在固定/解除固定过渡期间。
* nr_foll_pin_acquired：这是自系统启动以来已获取的逻辑固定数量。对于大页面，头部页面会根据大页面中的每个页面（头部页面和每个尾部页面）固定一次
这遵循get_user_pages()处理大页面时的行为：当get_user_pages()应用于大页面时，头部页面的引用计数会根据大页面中的每个尾部或头部页面增加一次
* nr_foll_pin_released：自系统启动以来已释放的逻辑固定数量。请注意，页面是以PAGE_SIZE粒度解除固定的，即使原始固定应用于大页面
由于上面“nr_foll_pin_acquired”中描述的固定计数行为，会计平衡最终会使得在执行以下操作之后::

    pin_user_pages(大页面);
    对于大页面中的每个页面
        unpin_user_page(页面);

预期结果如下::

    nr_foll_pin_released == nr_foll_pin_acquired

(...除非由于存在长期RDMA固定而导致已经不平衡。)

其他诊断工具
==============
dump_page()已被稍作增强以处理这些新的计数字段，并更好地报告一般的大folio。具体来说，对于大folio，会报告确切的固定计数。
参考资料
==========

* `get_user_pages() 的一些缓慢进展 (2019年4月2日) <https://lwn.net/Articles/784574/>`_
* `DMA 和 get_user_pages() (LPC: 2018年12月12日) <https://lwn.net/Articles/774411/>`_
* `get_user_pages() 的问题 (2018年4月30日) <https://lwn.net/Articles/753027/>`_
* `LWN 内核索引: get_user_pages() <https://lwn.net/Kernel/Index/#Memory_management-get_user_pages>`_

John Hubbard, 2019年10月
