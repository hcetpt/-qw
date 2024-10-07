SPDX 许可证标识符：GPL-2.0 或 GFDL-1.1-no-invariants-or-later
C 命名空间：MC

.. _media_request_ioc_reinit:

*******************************
ioctl MEDIA_REQUEST_IOC_REINIT
*******************************

名称
====

MEDIA_REQUEST_IOC_REINIT - 重新初始化一个请求

简介
========

.. c:macro:: MEDIA_REQUEST_IOC_REINIT

``int ioctl(int request_fd, MEDIA_REQUEST_IOC_REINIT)``

参数
=========

``request_fd``
    由 :ref:`MEDIA_IOC_REQUEST_ALLOC` 返回的文件描述符

描述
===========

如果媒体设备支持 :ref:`请求 <media-request-api>`，则可以使用此 ioctl 请求来重新初始化先前分配的请求。
重新初始化请求将清除请求中的任何现有数据。这样避免了必须对已完成的请求调用 :c:func:`close()` 并分配新的请求。相反，可以直接重新初始化完成的请求，使其准备好再次使用。
只有在请求尚未排队或已排队并已完成的情况下，才能重新初始化该请求。否则会将 ``errno`` 设置为 ``EBUSY``。不会返回其他错误代码。

返回值
============

成功时返回 0，出错时返回 -1，并且根据情况设置 ``errno`` 变量
EBUSY
    请求已排队但尚未完成
