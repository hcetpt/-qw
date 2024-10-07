SPDX 许可证标识符: GFDL-1.1-no-invariants-or-later
.. c:namespace:: CEC

.. _cec-func-poll:

**********
cec poll()
**********

名称
====

cec-poll — 等待文件描述符上的某个事件

概要
========

.. code-block:: c

    #include <sys/poll.h>

.. c:function:: int poll(struct pollfd *ufds, unsigned int nfds, int timeout)

参数
=========

``ufds``
   要监视的 FD 事件列表

``nfds``
   \*ufds 数组中的 FD 事件数量

``timeout``
   等待事件的超时时间

描述
===========

使用 :c:func:`poll()` 函数，应用程序可以等待 CEC 事件。在成功的情况下，:c:func:`poll()` 返回被选中的文件描述符的数量（即相应结构 :c:type:`pollfd` 的 ``revents`` 字段非零的文件描述符）。CEC 设备会在接收队列中有消息时设置 ``POLLIN`` 和 ``POLLRDNORM`` 标志。如果发送队列有空间容纳新消息，则会设置 ``POLLOUT`` 和 ``POLLWRNORM`` 标志。如果有事件在事件队列中，则设置 ``POLLPRI`` 标志。当函数超时时，返回值为零；失败时返回 -1，并设置相应的 ``errno`` 变量。更多详细信息请参阅 :c:func:`poll()` 手册页。

返回值
============

在成功的情况下，:c:func:`poll()` 返回具有非零 ``revents`` 字段的结构数量，或者如果调用超时则返回零。错误时返回 -1，并根据以下情况设置 ``errno`` 变量：

``EBADF``
    ``ufds`` 成员中指定的一个或多个文件描述符无效

``EFAULT``
    ``ufds`` 引用了一个无法访问的内存区域

``EINTR``
    调用被信号中断

``EINVAL``
    ``nfds`` 值超过了 ``RLIMIT_NOFILE`` 值。使用 ``getrlimit()`` 获取该值
