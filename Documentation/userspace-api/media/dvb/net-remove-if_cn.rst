SPDX 许可声明标识符: GFDL-1.1-no-invariants-or-later
.. c:namespace:: DTV.net

.. _NET_REMOVE_IF:

*******************
ioctl NET_REMOVE_IF
*******************

名称
====

NET_REMOVE_IF - 删除网络接口

概要
====

.. c:macro:: NET_REMOVE_IF

``int ioctl(int fd, NET_REMOVE_IF, int ifnum)``

参数
====

``fd``
    由 :c:func:`open()` 返回的文件描述符
``ifnum``
    要删除的接口编号

描述
====

NET_REMOVE_IF ioctl 命令会删除之前通过 :ref:`NET_ADD_IF <net>` 创建的接口。

返回值
======

成功时返回 0，并且 :c:type:`ca_slot_info` 被填充；
失败时返回 -1，并且 ``errno`` 变量被设置为适当的错误码。
通用错误码在 :ref:`Generic Error Codes <gen-errors>` 章节中描述。
