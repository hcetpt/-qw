SPDX 许可证标识符: GFDL-1.1-no-invariants-or-later
.. c:namespace:: DTV.ca

.. _CA_GET_CAP:

==========
CA_GET_CAP
==========

名称
----

CA_GET_CAP

概要
--------

.. c:macro:: CA_GET_CAP

``int ioctl(fd, CA_GET_CAP, struct ca_caps *caps)``

参数
---------

``fd``
  由先前调用 :c:func:`open()` 返回的文件描述符
``caps``
  指向结构体 :c:type:`ca_caps` 的指针

描述
-----------

向内核查询有关可用的条件接收（CA）插槽和解扰器插槽及其类型的信息
返回值
------------

成功时返回 0，并填充 :c:type:`ca_caps`
出错时，返回 -1，并适当设置 ``errno`` 变量
通用错误代码在章节 :ref:`Generic Error Codes <gen-errors>` 中有描述
