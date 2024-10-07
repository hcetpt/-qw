.. SPDX 许可证标识符: GFDL-1.1-no-invariants-or-later
.. c:namespace:: DTV.fe

.. _FE_GET_EVENT:

************
FE_GET_EVENT
************

名称
====

FE_GET_EVENT

.. attention:: 此 ioctl 已弃用
概要
========

.. c:macro:: FE_GET_EVENT

``int ioctl(int fd, FE_GET_EVENT, struct dvb_frontend_event *ev)``

参数
=========

``fd``
    由 :c:func:`open()` 返回的文件描述符
``ev``
    指向事件（如果有）将被存储的位置
描述
===========

此 ioctl 调用在有可用的前端事件时返回该事件。如果没有事件可用，其行为取决于设备是处于阻塞模式还是非阻塞模式。在非阻塞模式下，调用会立即失败，并将 ``errno`` 设置为 ``EWOULDBLOCK``。在阻塞模式下，调用会一直阻塞直到事件变得可用。
返回值
============

成功时返回 0
错误时返回 -1，并设置相应的 ``errno`` 变量
.. flat-table::
    :header-rows:  0
    :stub-columns: 0

    -  .. row 1

       -  ``EWOULDBLOCK``

       -  没有待处理的事件，且设备处于非阻塞模式
-  .. row 2

       -  ``EOVERFLOW``

       -  事件队列溢出 - 一个或多个事件丢失
通用错误代码在 :ref:`通用错误代码 <gen-errors>` 章节中描述。
