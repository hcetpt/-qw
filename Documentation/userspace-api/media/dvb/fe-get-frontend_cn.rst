SPDX 许可证标识符: GFDL-1.1-no-invariants-or-later
.. c:namespace:: DTV.fe

.. _FE_GET_FRONTEND:

***************
FE_GET_FRONTEND
***************

名称
====

FE_GET_FRONTEND

.. attention:: 此 ioctl 已废弃

概要
========

.. c:macro:: FE_GET_FRONTEND

``int ioctl(int fd, FE_GET_FRONTEND, struct dvb_frontend_parameters *p)``

参数
=========

``fd``
    由 :c:func:`open()` 返回的文件描述符
``p``
    指向调谐操作的参数

描述
===========

此 ioctl 调用查询当前有效的前端参数。对于此命令，仅需设备的只读访问权限。
返回值
============

成功时返回 0
出错时返回 -1，并且设置 ``errno`` 变量为适当的值
.. flat-table::
    :header-rows:  0
    :stub-columns: 0

    -  .. row 1

       -  ``EINVAL``

       -  达到最大支持的符号率
通用错误码在《通用错误码 <gen-errors>` 章节中描述。
