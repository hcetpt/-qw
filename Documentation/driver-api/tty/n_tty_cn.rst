SPDX许可标识符: GPL-2.0

=====
N_TTY
=====

.. contents:: 目录

默认（及回退）:doc:`TTY 行律 `<tty_ldisc>。它试图按照 POSIX 标准来处理字符。

外部函数
==================

.. kernel-doc:: drivers/tty/n_tty.c
   :export:

内部函数
==================

.. kernel-doc:: drivers/tty/n_tty.c
   :internal: 
请注意，`:kernel-doc:` 似乎是一个类似于指令或标签的元素，并不是直接可翻译的文本内容，它可能需要根据具体的文档生成工具来解释和渲染。
