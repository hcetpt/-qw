SPDX 许可声明标识符: GFDL-1.1-no-invariants-or-later
.. c:namespace:: V4L

.. _func-poll:

***********
V4L2 poll()
***********

名称
====

v4l2-poll - 在文件描述符上等待某个事件

概要
========

.. code-block:: c

    #include <sys/poll.h>

.. c:function:: int poll(struct pollfd *ufds, unsigned int nfds, int timeout)

参数
=========

描述
===========

使用 :c:func:`poll()` 函数，应用程序可以挂起执行，直到驱动程序捕获数据或准备好接收输出数据。
当协商了流式 I/O 时，此函数会等待直到捕获设备填充了一个缓冲区，并且可以通过 :ref:`VIDIOC_DQBUF <VIDIOC_QBUF>` ioctl 进行解除队列。对于输出设备，此函数会等待直到设备准备好接受一个新的缓冲区，以便通过 :ref:`VIDIOC_QBUF <VIDIOC_QBUF>` ioctl 进行排队显示。如果驱动程序（捕获）的传出队列中已经有缓冲区，或者显示的传入队列未满，则该函数立即返回。

成功时，:c:func:`poll()` 返回被选中的文件描述符的数量（即，各自 `struct pollfd` 结构体中的 `revents` 字段非零的文件描述符）。捕获设备会在 `revents` 字段中设置 `POLLIN` 和 `POLLRDNORM` 标志，输出设备会设置 `POLLOUT` 和 `POLLWRNORM` 标志。如果函数超时则返回0，失败时返回-1并设置 `errno` 变量为适当的值。如果应用程序没有调用 :ref:`VIDIOC_STREAMON <VIDIOC_STREAMON>`，:c:func:`poll()` 函数会成功但会在 `revents` 字段中设置 `POLLERR` 标志。如果应用程序对一个捕获设备调用了 :ref:`VIDIOC_STREAMON <VIDIOC_STREAMON>` 但还没有调用 :ref:`VIDIOC_QBUF <VIDIOC_QBUF>`，:c:func:`poll()` 函数会成功并在 `revents` 字段中设置 `POLLERR` 标志。对于输出设备，这种情况也会导致 :c:func:`poll()` 成功，但在 `revents` 字段中设置 `POLLOUT` 和 `POLLWRNORM` 标志。

如果发生了事件（参见 :ref:`VIDIOC_DQEVENT`），那么 `revents` 字段将设置 `POLLPRI` 标志，:c:func:`poll()` 将返回。

如果协商了 :c:func:`read()` 函数的使用并且驱动程序尚未开始捕获数据，:c:func:`poll()` 函数将启动捕获。如果这失败了，它将返回 `POLLERR`。否则，它会等待直到数据被捕获并且可以读取。如果驱动程序连续捕获数据（例如，不同于静止图像），该函数可能立即返回。

如果协商了 :c:func:`write()` 函数的使用并且驱动程序尚未开始流式传输，:c:func:`poll()` 函数将启动流式传输。如果这失败了，它将返回 `POLLERR`。否则，它会等待直到驱动程序准备好进行非阻塞的 :c:func:`write()` 调用。

如果调用者仅对事件感兴趣（即 `events` 字段中仅设置了 `POLLPRI`），那么 :c:func:`poll()` 不会启动流式传输，除非驱动程序已经开始流式传输。这使得只轮询事件而不是缓冲区成为可能。

所有实现了 :c:func:`read()` 或 :c:func:`write()` 函数或流式 I/O 的驱动程序也必须支持 :c:func:`poll()` 函数。更多详细信息，请参阅 :c:func:`poll()` 手册页。

返回值
============

成功时，:c:func:`poll()` 返回具有非零 `revents` 字段的结构体数量，或者如果调用超时则返回0。出错时返回-1，并设置 `errno` 变量为适当的值：

EBADF
    `ufds` 成员之一指定了一个无效的文件描述符
EBUSY
    驱动不支持多个读取或写入流，并且设备已经在使用中。

EFAULT
    ``ufds`` 引用了一个无法访问的内存区域。

EINTR
    调用被信号中断。

EINVAL
    ``nfds`` 的值超过了 ``RLIMIT_NOFILE`` 的值。使用 ``getrlimit()`` 获取该值。
