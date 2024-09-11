.. _vga_switcheroo:

==============
VGA Switcheroo
==============

.. kernel-doc:: drivers/gpu/vga/vga_switcheroo.c
   :doc: 概览

使用模式
============

手动切换和手动电源控制
-----------------------------------------

.. kernel-doc:: drivers/gpu/vga/vga_switcheroo.c
   :doc: 手动切换和手动电源控制

驱动程序电源控制
--------------------

.. kernel-doc:: drivers/gpu/vga/vga_switcheroo.c
   :doc: 驱动程序电源控制

API
===

公共函数
----------------

.. kernel-doc:: drivers/gpu/vga/vga_switcheroo.c
   :export:

公共结构体
-----------------

.. kernel-doc:: include/linux/vga_switcheroo.h
   :functions: vga_switcheroo_handler

.. kernel-doc:: include/linux/vga_switcheroo.h
   :functions: vga_switcheroo_client_ops

公共常量
----------------

.. kernel-doc:: include/linux/vga_switcheroo.h
   :functions: vga_switcheroo_handler_flags_t

.. kernel-doc:: include/linux/vga_switcheroo.h
   :functions: vga_switcheroo_client_id

.. kernel-doc:: include/linux/vga_switcheroo.h
   :functions: vga_switcheroo_state

私有结构体
------------------

.. kernel-doc:: drivers/gpu/vga/vga_switcheroo.c
   :functions: vgasr_priv

.. kernel-doc:: drivers/gpu/vga/vga_switcheroo.c
   :functions: vga_switcheroo_client

处理器
========

apple-gmux 处理器
------------------

.. kernel-doc:: drivers/platform/x86/apple-gmux.c
   :doc: 概览

.. kernel-doc:: drivers/platform/x86/apple-gmux.c
   :doc: 中断

图形多路复用器
~~~~~~~~~~~~

.. kernel-doc:: drivers/platform/x86/apple-gmux.c
   :doc: 图形多路复用器

电源控制
~~~~~~~~~~~~~

.. kernel-doc:: drivers/platform/x86/apple-gmux.c
   :doc: 电源控制

背光控制
~~~~~~~~~~~~~~~~~

.. kernel-doc:: drivers/platform/x86/apple-gmux.c
   :doc: 背光控制

公共函数
~~~~~~~~~~~~~~~~

.. kernel-doc:: include/linux/apple-gmux.h
   :internal:
