.. SPDX 许可证标识符: GFDL-1.1-no-invariants-or-later
.. c:namespace:: DTV.dmx

.. _DMX_QUERYBUF:

**************
ioctl DMX_QUERYBUF
**************

名称
====

DMX_QUERYBUF - 查询缓冲区的状态

.. warning:: 此 API 仍在试验阶段

简介
========

.. c:macro:: DMX_QUERYBUF

``int ioctl(int fd, DMX_QUERYBUF, struct dvb_buffer *argp)``

参数
=========

``fd``
    由 :c:func:`open()` 返回的文件描述符
``argp``
    指向 :c:type:`dvb_buffer` 结构体的指针
描述
===========

此 ioctl 是 mmap 流式 I/O 方法的一部分。可以在使用 :ref:`DMX_REQBUFS` ioctl 分配缓冲区后随时查询缓冲区的状态。
应用程序设置 ``index`` 字段。有效的索引号范围是从零到使用 :ref:`DMX_REQBUFS` ioctl（struct :c:type:`dvb_requestbuffers` 的 ``count`` 字段）分配的缓冲区数量减一。
在使用指向该结构的指针调用 :ref:`DMX_QUERYBUF` 后，驱动程序将返回一个错误代码或填充结构的其余部分。
成功时，``offset`` 将包含从设备内存起始位置到缓冲区的偏移量，``length`` 字段包含其大小，而 ``bytesused`` 包含缓冲区中数据所占用的字节数（有效载荷）。
返回值
============

成功时返回 0，``offset`` 将包含从设备内存起始位置到缓冲区的偏移量，``length`` 字段包含其大小，而 ``bytesused`` 包含缓冲区中数据所占用的字节数（有效载荷）。
出错时返回 -1，并且设置适当的 ``errno`` 变量。通用错误代码在 :ref:`通用错误代码 <gen-errors>` 章节中描述。
EINVAL
    ``index`` 超出了范围
