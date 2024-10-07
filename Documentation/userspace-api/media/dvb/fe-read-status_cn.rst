SPDX 许可声明标识符: GFDL-1.1-no-invariants-or-later
.. c:namespace:: DTV.fe

.. _FE_READ_STATUS:

********************
ioctl FE_READ_STATUS
********************

名称
====

FE_READ_STATUS - 返回关于前端的状态信息。此调用只需要对设备的只读访问权限。

概要
========

.. c:macro:: FE_READ_STATUS

``int ioctl(int fd, FE_READ_STATUS, unsigned int *status)``

参数
=========

``fd``
    由 :c:func:`open()` 返回的文件描述符。
``status``
    指向一个整数位标志的指针，该整数位标志被填充为由枚举类型 :c:type:`fe_status` 定义的值。

描述
===========

所有数字电视前端设备都支持 `FE_READ_STATUS` ioctl 调用。它用于在调谐后检查前端的锁定状态。ioctl 调用需要一个指向整数的指针，其中将写入状态信息。
.. note::

   状态的实际大小是 sizeof(enum fe_status)，这根据架构的不同而变化。这在未来需要修正。

int fe_status
=============

`fe_status` 参数用于指示前端硬件的当前状态和/或状态变化。它是使用枚举类型 :c:type:`fe_status` 的值在一个位标志中产生的。

返回值
============

成功时返回 0
错误时返回 -1，并且设置 `errno` 变量为适当的值。
通用错误代码在《通用错误代码 <gen-errors>` 章节中有描述。
