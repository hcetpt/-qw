SPDX 许可声明标识符: GFDL-1.1-no-invariants-or-later
.. c:namespace:: DTV.ca

.. _CA_GET_DESCR_INFO:

=================
CA_GET_DESCR_INFO
=================

名称
----

CA_GET_DESCR_INFO

概要
--------

.. c:macro:: CA_GET_DESCR_INFO

``int ioctl(fd, CA_GET_DESCR_INFO, struct ca_descr_info *desc)``

参数
---------

``fd``
  由先前调用 :c:func:`open()` 返回的文件描述符
``desc``
  指向 :c:type:`ca_descr_info` 结构体的指针
描述
-----------

返回所有解扰器插槽的信息
返回值
------------

成功时返回 0，并填充 :c:type:`ca_descr_info` 结构体
失败时返回 -1，并根据情况设置 ``errno`` 变量。通用错误代码在
:ref:`通用错误代码 <gen-errors>` 章节中描述。
