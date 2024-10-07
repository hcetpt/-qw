SPDX 许可证标识符: GFDL-1.1-no-invariants-or-later
.. c:namespace:: V4L

.. _func-close:

************
V4L2 close()
************

名称
====

v4l2-close — 关闭一个 V4L2 设备

简介
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

关闭设备。任何正在进行的 I/O 操作将被终止，并且与该文件描述符关联的资源将被释放。但是，数据格式参数、当前输入或输出、控制值或其他属性保持不变。
返回值
============

函数在成功时返回 0，在失败时返回 -1，并且根据情况设置 ``errno``。可能的错误代码：

EBADF
    ``fd`` 不是一个有效的打开文件描述符
