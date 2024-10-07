SPDX 许可证标识符: GFDL-1.1-no-invariants-or-later
.. c:namespace:: V4L

.. _func-select:

*************
V4L2 select()
*************

名称
====

v4l2-select — 同步I/O多路复用

简介
========

.. code-block:: c

    #include <sys/time.h>
    #include <sys/types.h>
    #include <unistd.h>

.. c:function:: int select(int nfds, fd_set *readfds, fd_set *writefds, fd_set *exceptfds, struct timeval *timeout)

参数
=========

``nfds``
  三个集合中编号最高的文件描述符加1。
``readfds``
  监控的文件描述符，如果调用 read() 不会阻塞。
``writefds``
  监控的文件描述符，如果调用 write() 不会阻塞。
``exceptfds``
  监控的文件描述符，用于 V4L2 事件。
``timeout``
  最大等待时间。

描述
===========

使用 :c:func:`select()` 函数，应用程序可以挂起执行，直到驱动程序捕获数据或准备好接收输出数据。当协商了流式 I/O 时，此函数将等待缓冲区被填充或显示，并且可以使用 :ref:`VIDIOC_DQBUF <VIDIOC_QBUF>` ioctl 命令取消排队。当驱动程序的输出队列中已经有缓冲区时，该函数立即返回。成功时，:c:func:`select()` 返回 ``fd_set`` 中设置的位总数。当超时时，返回值为零。失败时返回 -1，并且 ``errno`` 变量将相应地设置。如果应用程序尚未调用 :ref:`VIDIOC_QBUF` 或 :ref:`VIDIOC_STREAMON`，:c:func:`select()` 函数成功，并在 ``readfds`` 或 ``writefds`` 中设置文件描述符的位，但随后的 :ref:`VIDIOC_DQBUF <VIDIOC_QBUF>` 调用将失败。[#f1]_

当协商使用 :c:func:`read()` 函数且驱动程序尚未开始捕获时，:c:func:`select()` 函数启动捕获。如果捕获失败，:c:func:`select()` 成功返回，随后的 :c:func:`read()` 调用（也尝试启动捕获）将返回适当的错误代码。当驱动程序连续捕获数据（与例如静止图像相反），并且数据已经可用时，:c:func:`select()` 函数立即返回。当协商使用 :c:func:`write()` 函数时，:c:func:`select()` 函数仅等待驱动程序准备好进行非阻塞的 :c:func:`write()` 调用。

所有实现了 :c:func:`read()` 或 :c:func:`write()` 函数或流式 I/O 的驱动程序还必须支持 :c:func:`select()` 函数。
更多信息请参见 :c:func:`select()` 手册页。

返回值
======

在成功的情况下，:c:func:`select()` 返回三个返回的描述符集中包含的描述符数量，如果超时到期，则该数量为零。在发生错误时返回 -1，并且设置 ``errno`` 变量；描述符集和 ``timeout`` 会处于未定义状态。可能的错误代码包括：

EBADF
    指定的一个或多个文件描述符集包含一个未打开的文件描述符。
EBUSY
    驱动程序不支持多个读取或写入流，并且设备已经在使用中。
EFAULT
    ``readfds``、``writefds``、``exceptfds`` 或 ``timeout`` 指针引用了不可访问的内存区域。
EINTR
    调用被信号中断。
EINVAL
    ``nfds`` 参数小于零或大于 ``FD_SETSIZE``。

.. [#f1]
   Linux 内核实现 :c:func:`select()` 类似于 :c:func:`poll()` 函数，但 :c:func:`select()` 不能返回 ``POLLERR``。
