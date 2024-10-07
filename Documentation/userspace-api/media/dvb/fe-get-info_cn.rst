SPDX 许可证标识符: GFDL-1.1-no-invariants-or-later
.. c:namespace:: DTV.fe

.. _FE_GET_INFO:

***************
ioctl FE_GET_INFO
***************

名称
====

FE_GET_INFO - 查询数字电视前端功能并返回关于前端的信息。此调用只需要对设备的只读访问权限。

概要
====

.. c:macro:: FE_GET_INFO

``int ioctl(int fd, FE_GET_INFO, struct dvb_frontend_info *argp)``

参数
====

``fd``
    由 :c:func:`open()` 返回的文件描述符。
``argp``
    指向 :c:type:`dvb_frontend_info` 结构体的指针。

描述
====

所有数字电视前端设备都支持 :ref:`FE_GET_INFO` ioctl 调用。它用于识别符合此规范的内核设备，并获取有关驱动程序和硬件功能的信息。ioctl 调用需要一个指向 `dvb_frontend_info` 的指针，该指针由驱动程序填充。如果驱动程序不兼容此规范，则 ioctl 返回错误。

前端功能
========

功能描述了前端可以执行的操作。某些功能仅在特定类型的前端上支持。前端功能在 :c:type:`fe_caps` 中描述。

返回值
======

成功时返回 0。
出错时返回 -1，并且设置相应的 ``errno`` 变量。通用错误代码在 :ref:`Generic Error Codes <gen-errors>` 章节中描述。
