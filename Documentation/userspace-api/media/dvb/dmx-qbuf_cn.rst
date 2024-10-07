SPDX 许可声明标识符: GFDL-1.1-no-invariants-or-later
.. c:namespace:: DTV.dmx

.. _DMX_QBUF:

*************************
ioctl DMX_QBUF, DMX_DQBUF
*************************

名称
====

DMX_QBUF - DMX_DQBUF - 与驱动程序交换缓冲区

.. warning:: 此 API 仍在试验阶段

概述
========

.. c:macro:: DMX_QBUF

``int ioctl(int fd, DMX_QBUF, struct dmx_buffer *argp)``

.. c:macro:: DMX_DQBUF

``int ioctl(int fd, DMX_DQBUF, struct dmx_buffer *argp)``

参数
=========

``fd``
    由 :c:func:`open()` 返回的文件描述符
``argp``
    指向 struct :c:type:`dmx_buffer` 的指针
描述
===========

应用程序通过调用 ``DMX_QBUF`` ioctl 将一个空（用于捕获）或已填充（用于输出）的缓冲区加入到驱动程序的输入队列中。语义取决于所选的 I/O 方法。
为了将一个缓冲区加入队列，应用程序需要设置 ``index`` 字段。有效的索引号范围是从零到使用 :ref:`DMX_REQBUFS`（struct :c:type:`dmx_requestbuffers` 的 ``count`` 字段）分配的缓冲区数量减一。由 :ref:`DMX_QUERYBUF` ioctl 返回的 struct :c:type:`dmx_buffer` 的内容也同样适用。
当使用指向该结构的指针调用 ``DMX_QBUF`` 时，它会锁定缓冲区在物理内存中的页面，因此它们不能被交换到磁盘。这些缓冲区将一直保持锁定状态，直到它们被出队或设备关闭。
应用程序通过调用 ``DMX_DQBUF`` ioctl 从驱动程序的输出队列中取出一个已填充（用于捕获）的缓冲区。
它们只需设置要排队的缓冲区 ID 的 ``index`` 字段即可。
当使用指向 struct :c:type:`dmx_buffer` 的指针调用 ``DMX_DQBUF`` 时，驱动程序会填充剩余字段或返回错误代码。
默认情况下，如果没有缓冲区在输出队列中，则 ``DMX_DQBUF`` 会阻塞。如果在调用 :c:func:`open()` 函数时设置了 ``O_NONBLOCK`` 标志，并且没有可用的缓冲区时，``DMX_DQBUF`` 会立即返回一个 ``EAGAIN`` 错误代码。
结构 :c:type:`dmx_buffer` 在 :ref:`buffer` 中定义。

返回值
======

成功时返回 0，错误时返回 -1 并且设置 ``errno`` 变量。通用错误代码在 :ref:`Generic Error Codes <gen-errors>` 章节中描述。

EAGAIN
    使用 ``O_NONBLOCK`` 启用了非阻塞 I/O，并且输出队列中没有缓冲区。
EINVAL
    ``index`` 超出了范围，或者尚未分配任何缓冲区。
EIO
    由于内部错误导致 ``DMX_DQBUF`` 失败。也可能表示临时性问题，如信号丢失或 CRC 错误。
