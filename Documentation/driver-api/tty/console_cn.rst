SPDX 许可证标识符: GPL-2.0

=====
控制台
=====

.. contents:: 目录

结构体 Console
==============

.. kernel-doc:: include/linux/console.h
   :identifiers: console cons_flags

内部实现
---------

.. kernel-doc:: include/linux/console.h
   :identifiers: nbcon_state nbcon_prio nbcon_context nbcon_write_context

结构体 Consw
============

.. kernel-doc:: include/linux/console.h
   :identifiers: consw

控制台函数
=================

.. kernel-doc:: include/linux/console.h
   :identifiers: console_srcu_read_flags console_srcu_write_flags
        console_is_registered for_each_console_srcu for_each_console

.. kernel-doc:: drivers/tty/vt/selection.c
   :export:
.. kernel-doc:: drivers/tty/vt/vt.c
   :export:

内部实现
---------

.. kernel-doc:: drivers/tty/vt/selection.c
   :internal:
.. kernel-doc:: drivers/tty/vt/vt.c
   :internal:
