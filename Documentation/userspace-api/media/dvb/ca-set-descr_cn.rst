SPDX 许可证标识符: GFDL-1.1-no-invariants-or-later
.. c:namespace:: DTV.ca

.. _CA_SET_DESCR:

============
CA_SET_DESCR
============

名称
----

CA_SET_DESCR

概要
--------

.. c:macro:: CA_SET_DESCR

``int ioctl(fd, CA_SET_DESCR, struct ca_descr *desc)``

参数
---------

``fd``
  由先前调用 :c:func:`open()` 返回的文件描述符
``desc``
  指向 :c:type:`ca_descr` 结构体的指针
描述
-----------

CA_SET_DESCR 用于向解扰器 CA 插槽提供解扰密钥（称为控制字）
返回值
------------

成功时返回 0
出错时返回 -1，并且设置 ``errno`` 变量为适当的错误码
通用错误码在“通用错误码”章节中描述 (:ref:`Generic Error Codes <gen-errors>`)
