SPDX 许可声明标识符: GFDL-1.1-no-invariants-or-later
.. c:namespace:: DTV.ca

.. _CA_SEND_MSG:

===========
CA_SEND_MSG
===========

名称
----

CA_SEND_MSG

概要
--------

.. c:macro:: CA_SEND_MSG

``int ioctl(fd, CA_SEND_MSG, struct ca_msg *msg)``

参数
---------

``fd``
  由先前调用 :c:func:`open()` 返回的文件描述符
``msg``
  指向 :c:type:`ca_msg` 结构体的指针
描述
-----------

通过 CI CA 模块发送一条消息
.. note::

   请注意，在大多数驱动程序中，这是通过写入 /dev/adapter?/ca? 设备节点来完成的
返回值
------------

成功时返回 0
出错时返回 -1，并且设置 ``errno`` 变量为适当的值
通用错误代码在 :ref:`通用错误代码 <gen-errors>` 章节中有描述
