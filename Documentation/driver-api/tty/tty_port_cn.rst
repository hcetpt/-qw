SPDX 许可证标识符: GPL-2.0

=====
TTY 端口
=====

.. contents:: :local:

建议TTY驱动程序尽可能使用struct tty_port辅助函数。
如果驱动程序实现了:c:member:`tty_port.ops.activate()` 和 :c:member:`tty_port.ops.shutdown()`，那么它们可以在相应的 :c:member:`tty_struct.ops` 钩子中使用 tty_port_open()、tty_port_close() 和 tty_port_hangup()。
更多的参考和细节包含在底部的 `TTY 端口参考`_ 和 `TTY 端口操作参考`_ 部分。

TTY端口函数
==================

初始化与销毁
--------------

.. kernel-doc::  drivers/tty/tty_port.c
   :identifiers: tty_port_init tty_port_destroy
        tty_port_get tty_port_put

打开/关闭/挂起助手
-------------------------

.. kernel-doc::  drivers/tty/tty_port.c
   :identifiers: tty_port_install tty_port_open tty_port_block_til_ready
        tty_port_close tty_port_close_start tty_port_close_end tty_port_hangup
        tty_port_shutdown

TTY 引用计数
---------------

.. kernel-doc::  drivers/tty/tty_port.c
   :identifiers: tty_port_tty_get tty_port_tty_set

TTY 辅助函数
-----------

.. kernel-doc::  drivers/tty/tty_port.c
   :identifiers: tty_port_tty_hangup tty_port_tty_wakeup


调制解调器信号
-------------

.. kernel-doc::  drivers/tty/tty_port.c
   :identifiers: tty_port_carrier_raised tty_port_raise_dtr_rts
        tty_port_lower_dtr_rts

----

TTY 端口参考
==================

.. kernel-doc:: include/linux/tty_port.h
   :identifiers: tty_port

----

TTY 端口操作参考
=============================

.. kernel-doc:: include/linux/tty_port.h
   :identifiers: tty_port_operations
