.. SPDX 许可证标识符: GFDL-1.1-no-invariants-or-later
.. c:namespace:: DTV.net

.. _NET_ADD_IF:

****************
ioctl NET_ADD_IF
****************

名称
====

NET_ADD_IF - 为给定的包 ID 创建一个新的网络接口

概要
====

.. c:macro:: NET_ADD_IF

``int ioctl(int fd, NET_ADD_IF, struct dvb_net_if *net_if)``

参数
====

``fd``
    由 :c:func:`open()` 返回的文件描述符
``net_if``
    指向结构体 :c:type:`dvb_net_if` 的指针

描述
====

NET_ADD_IF ioctl 系统调用选择包含 TCP/IP 流量的包 ID（PID），选择要使用的封装类型（MPE 或 ULE）以及新创建接口的接口编号。当系统调用成功返回时，会创建一个新的虚拟网络接口。
结构体 :c:type:`dvb_net_if` 中的 `ifnum` 字段将被填充为创建的接口编号。

返回值
============

成功时返回 0，并且 :c:type:`ca_slot_info` 被填充；
出错时返回 -1，并且设置适当的 `errno` 变量。
通用错误代码在章节 :ref:`Generic Error Codes <gen-errors>` 中描述。
