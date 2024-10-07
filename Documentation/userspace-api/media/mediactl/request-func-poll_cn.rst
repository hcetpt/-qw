SPDX 许可证标识符：GPL-2.0 或 GFDL-1.1-no-invariants-or-later
C 命名空间：MC

.. _request-func-poll:

**************
request poll()
**************

名称
====

request-poll - 等待文件描述符上的某个事件

概览
====

.. code-block:: c

    #include <sys/poll.h>

.. c:function:: int poll(struct pollfd *ufds, unsigned int nfds, int timeout)

参数
=========

``ufds``
   要监视的文件描述符事件列表

``nfds``
   \*ufds 数组中的文件描述符事件数量

``timeout``
   等待事件的超时时间

描述
===========

通过 :c:func:`poll()` 函数，应用程序可以等待请求完成。在成功的情况下，:c:func:`poll()` 返回已选择的文件描述符的数量（即，相应结构 :c:type:`pollfd` 的 ``revents`` 字段非零的文件描述符）。当请求完成时，请求文件描述符会在 ``revents`` 中设置 ``POLLPRI`` 标志。当函数超时时，返回值为零；如果失败，则返回 -1，并且设置适当的 ``errno`` 变量。尝试轮询尚未排队的请求将在 ``revents`` 中设置 ``POLLERR`` 标志。

返回值
============

在成功的情况下，:c:func:`poll()` 返回具有非零 ``revents`` 字段的结构数量，如果调用超时则返回零。在错误情况下返回 -1，并且设置适当的 ``errno`` 变量：

``EBADF``
    ``ufds`` 成员中有一个或多个无效的文件描述符

``EFAULT``
    ``ufds`` 引用了一个不可访问的内存区域

``EINTR``
    调用被信号中断

``EINVAL``
    ``nfds`` 的值超过了 ``RLIMIT_NOFILE`` 的值。使用 ``getrlimit()`` 获取此值
