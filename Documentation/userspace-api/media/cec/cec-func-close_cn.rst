SPDX 许可证标识符: GFDL-1.1-no-invariants-or-later
.. c:namespace:: CEC

.. _cec-func-close:

***********
cec_close()
***********

名称
====

cec_close - 关闭一个 CEC 设备

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

关闭 CEC 设备。与文件描述符关联的资源将被释放。设备配置保持不变。
返回值
============

:c:func:`close()` 在成功时返回 0。如果出现错误，则返回 -1，并且 ``errno`` 被设置为适当的错误代码。可能的错误代码包括：

``EBADF``
    ``fd`` 不是一个有效的打开文件描述符
