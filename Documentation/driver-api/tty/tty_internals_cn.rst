SPDX 许可声明标识符: GPL-2.0

=============
TTY 内部机制
=============

.. 本地内容目录::

科彭 (Kopen)
=====

这些函数用于从内核空间打开 TTY：

.. 内核文档:: drivers/tty/tty_io.c
      :标识符: tty_kopen_exclusive tty_kopen_shared tty_kclose

----

导出的内部函数
===========================

.. 内核文档:: drivers/tty/tty_io.c
   :标识符: tty_release_struct tty_dev_name_to_number tty_get_icount

----

内部函数
==================

.. 内核文档:: drivers/tty/tty_io.c
   :内部: 

注意：文档中的"科彭 (Kopen)"部分，“科彭”可能是“打开（Open）”的误译，而“:内部:”可能需要更明确的描述。在实际的文档中，你可能需要更正这些地方以提高清晰度。
