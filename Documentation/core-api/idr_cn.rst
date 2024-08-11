SPDX 许可证标识符: GPL-2.0+

=============
ID 分配
=============

:作者: Matthew Wilcox

概述
========

一个常见的问题是如何分配标识符（ID）；通常是用于标识某个事物的小数字。例子包括文件描述符、进程ID、网络协议中的包标识符、SCSI标签和设备实例号。IDR 和 IDA 提供了一个合理的解决方案来避免每个人都发明自己的方法。IDR 提供了将ID映射到指针的能力，而 IDA 只提供 ID 分配，因此它在内存使用上更为高效。IDR 接口已被废弃；请改用 :doc:`XArray <xarray>`。
IDR 的使用
=========

首先初始化一个 IDR，可以使用 DEFINE_IDR() 对于静态分配的 IDR 或者使用 idr_init() 对于动态分配的 IDR。

你可以通过调用 idr_alloc() 来分配一个未使用的 ID。通过 idr_find() 查找与该 ID 关联的指针，并通过调用 idr_remove() 释放该 ID。

如果你需要改变与 ID 关联的指针，可以调用 idr_replace()。一个常见的做法是通过向分配函数传递 `NULL` 指针来预留一个 ID；初始化具有预留 ID 的对象，最后将初始化的对象插入到 IDR 中。

有些用户需要分配大于 `INT_MAX` 的 ID。迄今为止，所有这些用户都对 `UINT_MAX` 的限制感到满意，并且他们使用 idr_alloc_u32()。如果你需要不能放入 u32 的 ID，请联系我们，我们将与你合作解决你的需求。

如果你需要顺序地分配 ID，可以使用 idr_alloc_cyclic()。当处理较大的 ID 时，IDR 的效率会降低，因此使用这个函数会带来一些开销。

为了对 IDR 使用的所有指针执行操作，你可以使用基于回调的 idr_for_each() 或迭代风格的 idr_for_each_entry()。你可能需要用 idr_for_each_entry_continue() 继续一次迭代。如果迭代器不符合你的需求，你还可以使用 idr_get_next()。

当你完成对 IDR 的使用后，可以调用 idr_destroy() 来释放 IDR 使用的内存。这不会释放 IDR 所指向的对象；如果你想这样做，可以使用其中一个迭代器来实现。

你可以使用 idr_is_empty() 来判断当前是否已分配任何 ID。
如果你在从IDR分配新ID时需要获取一个锁，则可能需要传递一组限制性的GFP标志，这可能会导致IDR无法分配内存。为了绕过这个问题，你可以在获取锁之前调用`idr_preload()`，然后在分配之后调用`idr_preload_end()`。

.. kernel-doc:: include/linux/idr.h
   :doc: IDR 同步

IDA 使用
=========

.. kernel-doc:: lib/idr.c
   :doc: IDA 描述

函数和结构体
=============

.. kernel-doc:: include/linux/idr.h
   :functions:

.. kernel-doc:: lib/idr.c
   :functions:
