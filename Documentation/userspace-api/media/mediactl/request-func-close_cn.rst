.. SPDX 许可证标识符: GPL-2.0 或 GFDL-1.1-no-invariants-or-later
.. c:命名空间:: MC.request

.. _request-func-close:

***************
request close()
***************

名称
====

request-close - 关闭请求文件描述符

概要
========

.. code-block:: c

    #include <unistd.h>

.. c:function:: int close(int fd)

参数
=========

``fd``
    由 :ref:`MEDIA_IOC_REQUEST_ALLOC` 返回的文件描述符
描述
===========

关闭请求文件描述符。一旦与该请求相关的所有文件描述符被关闭，并且驱动程序完成了该请求，与此请求关联的资源将被释放。
更多详细信息请参见 :ref:`这里 <media-request-life-time>`
返回值
============

:c:func:`close()` 在成功时返回 0。如果出现错误，则返回 -1，并且适当设置 ``errno``。可能的错误代码包括：

EBADF
    ``fd`` 不是一个有效的打开文件描述符
