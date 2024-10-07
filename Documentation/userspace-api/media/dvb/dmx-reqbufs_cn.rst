SPDX 许可证标识符: GFDL-1.1-no-invariants-or-later
.. c:namespace:: DTV.dmx

.. _DMX_REQBUFS:

***************
ioctl DMX_REQBUFS
***************

名称
====

DMX_REQBUFS - 初始化内存映射和/或DMA缓冲区I/O

.. warning:: 此API仍在试验阶段

概要
========

.. c:macro:: DMX_REQBUFS

``int ioctl(int fd, DMX_REQBUFS, struct dmx_requestbuffers *argp)``

参数
=========

``fd``
    由 :c:func:`open()` 返回的文件描述符
``argp``
    指向 :c:type:`dmx_requestbuffers` 结构体的指针
描述
===========

此ioctl用于初始化内存映射或基于DMABUF的解复用I/O。
内存映射缓冲区位于设备内存中，必须通过此ioctl进行分配，才能将其映射到应用程序的地址空间。用户缓冲区由应用程序自己分配，此ioctl仅用于将驱动程序切换到用户指针I/O模式并设置一些内部结构。同样地，DMABUF缓冲区通过设备驱动程序由应用程序分配，此ioctl仅配置驱动程序进入DMABUF I/O模式而不执行任何直接分配。

为了分配设备缓冲区，应用程序需要初始化 :c:type:`dmx_requestbuffers` 结构体的所有字段。他们将 ``count`` 字段设置为所需缓冲区的数量，并将 ``size`` 设置为每个缓冲区的大小。

当使用指向该结构的指针调用ioctl时，驱动程序将尝试分配请求的缓冲区数量，并将实际分配的数量存储在 ``count`` 字段中。 ``count`` 可能小于请求的数量，甚至为零，当驱动程序内存不足时。如果驱动程序需要更多缓冲区以正确运行，也可能返回更大的数量。实际分配的缓冲区大小会返回在 ``size`` 中，可能小于请求的大小。

如果此I/O方法不受支持，ioctl将返回 ``EOPNOTSUPP`` 错误代码。
应用程序可以再次调用 :ref:`DMX_REQBUFS` 来更改缓冲区数量，但如果有任何缓冲区仍然映射，则此操作不会成功。
一个为零的 ``count`` 值会在中断或完成任何正在进行的DMA后释放所有缓冲区。
返回值
============

成功时返回0，出错时返回-1，并且设置 ``errno`` 变量为适当的错误码。通用错误码在 :ref:`Generic Error Codes <gen-errors>` 章节中描述。
EOPNOTSUPP
请求的 I/O 方法不被支持
