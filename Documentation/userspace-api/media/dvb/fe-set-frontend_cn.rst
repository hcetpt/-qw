SPDX 许可证标识符: GFDL-1.1-no-invariants-or-later
.. c:namespace:: DTV.fe

.. _FE_SET_FRONTEND:

***************
FE_SET_FRONTEND
***************

.. 注意:: 此 ioctl 已弃用
名称
====

FE_SET_FRONTEND

概览
========

.. c:macro:: FE_SET_FRONTEND

``int ioctl(int fd, FE_SET_FRONTEND, struct dvb_frontend_parameters *p)``

参数
=========

``fd``
    由 :c:func:`open()` 返回的文件描述符
``p``
    指向调谐操作的参数
描述
===========

此 ioctl 调用使用指定的参数启动一个调谐操作。如果参数有效并且能够启动调谐，则此调用的结果将成功。然而，调谐操作的结果将以异步事件的形式到达（参见 :ref:`FE_GET_EVENT` 和 FrontendEvent 的文档）。如果在前一次 :ref:`FE_SET_FRONTEND` 操作完成之前又发起了新的操作，则前一次操作将被终止以让位于新操作。此命令需要对设备具有读写访问权限。
返回值
============

成功时返回 0
出错时返回 -1，并且设置 ``errno`` 变量为相应的错误码
.. tabularcolumns:: |p{2.5cm}|p{15.0cm}|

.. flat-table::
    :header-rows:  0
    :stub-columns: 0
    :widths: 1 16

    -  .. row 1

       -  ``EINVAL``

       -  达到支持的最大符号率
通用错误码在 :ref:`Generic Error Codes <gen-errors>` 章节中有描述
