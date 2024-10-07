SPDX 许可声明标识符: GFDL-1.1-no-invariants-or-later
.. c:namespace:: V4L

.. _func-write:

************
V4L2 write()
************

名称
====

v4l2-write - 向 V4L2 设备写入数据

概要
========

.. code-block:: c

    #include <unistd.h>

.. c:function:: ssize_t write(int fd, void *buf, size_t count)

参数
=========

``fd``
    由 :c:func:`open()` 返回的文件描述符
``buf``
    包含待写入数据的缓冲区
``count``
    缓冲区中的字节数

描述
===========

:c:func:`write()` 从 ``buf`` 开始的位置向由文件描述符 ``fd`` 引用的设备写入最多 ``count`` 字节的数据。当硬件输出尚未激活时，此函数会启用它们。如果 ``count`` 为零，则 :c:func:`write()` 不产生任何其他效果直接返回 0。如果应用程序未能及时提供更多的数据，则将重新显示前一视频帧、原始 VBI 图像、分片 VPS 或 WSS 数据。分片 Teletext 或 Closed Caption 数据不会重复，驱动程序会插入一个空白行。
返回值
============

成功时，返回已写入的字节数。返回零表示没有写入任何内容。发生错误时，返回 -1，并且设置适当的 ``errno`` 变量。此时下一次写入将从新帧的开始处进行。可能的错误代码包括：

EAGAIN
    使用 :ref:`O_NONBLOCK <func-open>` 标志选择了非阻塞 I/O，并且没有可用的缓冲空间立即写入数据
EBADF
    ``fd`` 不是有效的文件描述符或未打开以供写入
EBUSY
    驱动程序不支持多个写入流并且设备已经在使用中
EFAULT
    ``buf`` 引用了不可访问的内存区域
EINTR
    在写入任何数据之前调用被信号中断
EIO
    I/O 错误。这表明存在某些硬件问题
EINVAL
此驱动不支持`:c:func:`write()`函数，或者在此设备上不支持，或者通常在这种类型的设备上不支持。
