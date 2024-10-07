.. 许可证标识符: GFDL-1.1-no-invariants-or-later
.. c:命名空间:: DTV.fe

.. _frontend_f_close:

***************************
数字电视前端 close()
***************************

名称
====

fe-close - 关闭前端设备

概要
========

.. code-block:: c

    #include <unistd.h>

.. c:function:: int close(int fd)

参数
=========

``fd``
    由 :c:func:`open()` 返回的文件描述符
描述
===========

此系统调用用于关闭先前已打开的前端设备。在关闭前端设备后，其对应的硬件可能会自动断电。
返回值
============

成功时返回 0
错误时返回 -1，并且设置 ``errno`` 变量为适当的错误码
通用错误码在 :ref:`通用错误码 <gen-errors>` 章节中描述。
