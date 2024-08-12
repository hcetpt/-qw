SPDX 许可证标识符: GPL-2.0

===================
TTY 行纪律
===================

.. contents:: :local:

TTY 行纪律处理来自/到 TTY 设备的所有输入和输出字符。默认的行纪律是 :doc:`N_TTY <n_tty>`。当为 TTY 建立任何其他纪律失败时，它也会作为后备选项。如果连 N_TTY 都失败了，那么 N_NULL 将接管。这永远不会失败，但也不会处理任何字符——它会丢弃它们。
注册
============

行纪律通过 tty_register_ldisc() 函数注册，并传递 ldisc 结构体。在注册点，该纪律必须准备好使用，并且有可能在调用返回成功之前就会被使用。如果调用返回错误，则不会被调用。不要重复使用 ldisc 编号，因为它们是用户空间 ABI 的一部分，并且覆盖现有 ldisc 将导致恶魔吃掉你的计算机。你甚至不能用相同的数据重新注册行纪律，否则你的计算机同样会被恶魔吞噬。为了移除一个行纪律，请调用 tty_unregister_ldisc()。

请注意这一警告：ldisc 表中已注册的 tty_ldisc 结构副本的引用计数字段记录了使用此纪律的行数量。tty 中的 tty_ldisc 结构的引用计数记录了此时使用 ldisc 的活动用户数量。实际上，它记录了在 ldisc 方法中执行线程的数量（加上那些即将进入和退出的线程，尽管这个细节无关紧要）。
.. kernel-doc:: drivers/tty/tty_ldisc.c
   :identifiers: tty_register_ldisc tty_unregister_ldisc

其他函数
===============

.. kernel-doc:: drivers/tty/tty_ldisc.c
   :identifiers: tty_set_ldisc tty_ldisc_flush

行纪律操作参考
====================================

.. kernel-doc:: include/linux/tty_ldisc.h
   :identifiers: tty_ldisc_ops

驱动访问
=============

行纪律方法可以调用底层硬件驱动的方法
这些方法作为 struct tty_operations 的一部分进行文档说明
TTY 标志
=========

行纪律方法可以访问 :c:member:`tty_struct.flags` 字段。参见
:doc:`tty_struct`
锁定
=======

从 TTY 层调用行纪律函数的调用者需要获取行纪律锁。对于来自驱动程序侧的调用也同样是真实的，但是目前还未强制执行。
.. kernel-doc:: drivers/tty/tty_ldisc.c
   :identifiers: tty_ldisc_ref_wait tty_ldisc_ref tty_ldisc_deref

虽然这些函数比旧代码略慢一些，但它们应该影响很小，因为大多数接收逻辑使用翻转缓冲区，并且仅在向上推送数据时才需要获取引用。
一个警告：:c:member:`tty_ldisc_ops.open()`, :c:member:`tty_ldisc_ops.close()` 和 :c:member:`tty_driver.set_ldisc()` 函数是在 ldisc 不可用的情况下被调用的。因此，如果在这三个函数内部使用 tty_ldisc_ref()，则会失败。ldisc 和驱动程序代码在调用自己的函数时必须小心处理这种情况。
内部函数
==================

.. kernel-doc:: drivers/tty/tty_ldisc.c
   :internal:
