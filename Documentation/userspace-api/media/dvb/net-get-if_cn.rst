.. SPDX 许可证标识符: GFDL-1.1-no-invariants-or-later
.. c:命名空间:: DTV.net

.. _NET_GET_IF:

***************
ioctl NET_GET_IF
***************

名称
====

NET_GET_IF - 读取通过 :ref:`NET_ADD_IF <net>` 创建的接口的配置数据

概要
====

.. c:宏:: NET_GET_IF

``int ioctl(int fd, NET_GET_IF, struct dvb_net_if *net_if)``

参数
====

``fd``
    由 :c:func:`open()` 返回的文件描述符
``net_if``
    指向结构体 :c:type:`dvb_net_if` 的指针

描述
====

NET_GET_IF ioctl 使用由结构体 :c:type:`dvb_net_if`::ifnum 字段给出的接口编号，并用该接口上使用的包 ID 和封装类型填充结构体 :c:type:`dvb_net_if` 的内容。如果该接口尚未使用 :ref:`NET_ADD_IF <net>` 创建，则返回 -1 并将 ``errno`` 填充为 ``EINVAL`` 错误代码。

返回值
======

成功时返回 0，并填充 :c:type:`ca_slot_info`
发生错误时返回 -1，并适当设置 ``errno`` 变量
通用错误代码在 :ref:`通用错误代码 <gen-errors>` 章节中描述。
