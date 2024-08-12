SPDX 许可证标识符: GPL-2.0

=====
TTY 缓冲区
=====

.. contents:: 目录
    :local:

在这里，我们记录了用于处理 TTY 缓冲区及其翻转的函数。
驱动程序应该使用下面列出的其中一个函数填充缓冲区，
然后翻转缓冲区，以便将数据传递给 :doc:`行律<tty_ldisc>` 进行进一步处理。

翻转缓冲区管理
======================

.. kernel-doc:: drivers/tty/tty_buffer.c
   :identifiers: tty_prepare_flip_string
           tty_flip_buffer_push tty_ldisc_receive_buf

.. kernel-doc:: include/linux/tty_flip.h
   :identifiers: tty_insert_flip_string_fixed_flag tty_insert_flip_string_flags
           tty_insert_flip_char

----

其他函数
===============

.. kernel-doc:: drivers/tty/tty_buffer.c
   :identifiers: tty_buffer_space_avail tty_buffer_set_limit

----

缓冲区锁定
==============

这些函数仅在特殊情况下使用。请尽量避免使用它们。
.. kernel-doc:: drivers/tty/tty_buffer.c
   :identifiers: tty_buffer_lock_exclusive tty_buffer_unlock_exclusive

----

内部函数
==================

.. kernel-doc:: drivers/tty/tty_buffer.c
   :internal:
