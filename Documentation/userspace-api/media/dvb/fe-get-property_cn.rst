SPDX 许可声明标识符: GFDL-1.1-no-invariants-or-later
.. c:namespace:: DTV.fe

.. _FE_GET_PROPERTY:

**************************************
ioctl FE_SET_PROPERTY, FE_GET_PROPERTY
**************************************

名称
====

FE_SET_PROPERTY - FE_GET_PROPERTY - FE_SET_PROPERTY 设置一个或多个前端属性。- FE_GET_PROPERTY 返回一个或多个前端属性。

概述
========

.. c:macro:: FE_GET_PROPERTY

``int ioctl(int fd, FE_GET_PROPERTY, struct dtv_properties *argp)``

.. c:macro:: FE_SET_PROPERTY

``int ioctl(int fd, FE_SET_PROPERTY, struct dtv_properties *argp)``

参数
=========

``fd``
    由 :c:func:`open()` 返回的文件描述符。
``argp``
    指向结构体 :c:type:`dtv_properties` 的指针。

描述
===========

所有数字电视前端设备都支持 ``FE_SET_PROPERTY`` 和 ``FE_GET_PROPERTY`` ioctl 命令。支持的属性和统计信息取决于传输系统和设备：

-  ``FE_SET_PROPERTY:``

   -  此 ioctl 用于设置一个或多个前端属性。
-  这是请求前端调谐到某个频率并开始解码数字电视信号的基本命令。
-  此调用需要对设备具有读写访问权限。
.. note::

   返回时，值不会更新以反映实际使用的参数。如果需要实际使用的参数，则需要显式调用 ``FE_GET_PROPERTY``。
-  ``FE_GET_PROPERTY:``

   -  此 ioctl 用于从前端获取属性和统计信息。
-  不会更改任何属性，并且统计信息也不会重置。
-  此调用只需要对设备具有只读访问权限。
返回值
============

成功时返回 0
出错时返回 -1，并且设置 ``errno`` 变量为适当的值
通用错误代码在《通用错误代码 <gen-errors>`》章节中描述
