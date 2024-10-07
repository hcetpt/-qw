.. SPDX 许可证标识符: GFDL-1.1-no-invariants-or-later
.. c:namespace:: DTV.dmx

.. _DMX_EXPBUF:

***************
ioctl DMX_EXPBUF
***************

名称
====

DMX_EXPBUF - 将缓冲区导出为 DMABUF 文件描述符
.. 警告:: 此 API 仍在试验阶段

概要
====

.. c:macro:: DMX_EXPBUF

``int ioctl(int fd, DMX_EXPBUF, struct dmx_exportbuffer *argp)``

参数
====

``fd``
    由 :c:func:`open()` 返回的文件描述符
``argp``
    指向 :c:type:`dmx_exportbuffer` 结构体的指针
描述
====

此 ioctl 是对内存映射 I/O 方法的扩展。
它可以在分配了缓冲区之后的任何时间将缓冲区导出为 DMABUF 文件描述符。
要导出一个缓冲区，应用程序需要填充 :c:type:`dmx_exportbuffer` 结构体。
应用程序必须设置 ``index`` 字段。有效的索引号范围是从零到通过 :ref:`DMX_REQBUFS` ioctl 分配的缓冲区数量减一（:c:type:`dmx_requestbuffers` 结构体中的 ``count`` 字段）。
可以在 ``flags`` 字段中设置额外的标志位。具体细节请参阅 `open()` 的手册。目前仅支持 O_CLOEXEC、O_RDONLY、O_WRONLY 和 O_RDWR。
所有其他字段必须设为零。在多平面 API 中，每个平面都需要分别使用多个 :ref:`DMX_EXPBUF` 调用来导出。
调用 :ref:`DMX_EXPBUF` 成功后，``fd`` 字段将由驱动程序设置。这是一个 DMABUF 文件描述符。应用程序可以将其传递给其他支持 DMABUF 的设备。建议不再使用 DMABUF 文件时关闭它，以便释放关联的内存。
示例
========

.. code-block:: c

    int buffer_export(int v4lfd, enum dmx_buf_type bt, int index, int *dmafd)
    {
        struct dmx_exportbuffer expbuf;

        memset(&expbuf, 0, sizeof(expbuf));
        expbuf.type = bt;
        expbuf.index = index;
        if (ioctl(v4lfd, DMX_EXPBUF, &expbuf) == -1) {
            perror("DMX_EXPBUF");
            return -1;
        }

        *dmafd = expbuf.fd;

        return 0;
    }

返回值
============

成功时返回 0，出错时返回 -1，并且设置 `errno` 变量为适当的错误码。通用错误码的描述请参见
:ref:`通用错误码 <gen-errors>` 章节。

EINVAL
    队列不在 MMAP 模式下或不支持 DMABUF 导出，或者 `flags` 或 `index` 字段无效。
