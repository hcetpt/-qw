SPDX 许可证标识符: GFDL-1.1-no-invariants-or-later
.. c:namespace:: DTV.dmx

.. _dmx-mmap:

***************
Digital TV mmap()
***************

名称
====

dmx-mmap - 将设备内存映射到应用程序地址空间

.. warning:: 该API仍在实验中

概要
====

.. code-block:: c

    #include <unistd.h>
    #include <sys/mman.h>

.. c:function:: void *mmap( void *start, size_t length, int prot, int flags, int fd, off_t offset )

参数
====

``start``
    将缓冲区映射到应用程序地址空间中的这个地址。
    当指定 ``MAP_FIXED`` 标志时，``start`` 必须是页面大小的倍数，并且当指定的地址无法使用时，mmap将失败。不建议使用此选项；应用程序应仅指定一个 ``NULL`` 指针。
``length``
    要映射的内存区域长度。这必须是DVB数据包长度（大多数驱动程序上为188）的倍数。
``prot``
    ``prot`` 参数描述了所需的内存保护。
    无论设备类型和数据交换方向如何，都应将其设置为 ``PROT_READ`` | ``PROT_WRITE`` ，以允许对图像缓冲区进行读写访问。驱动程序应至少支持这种标志组合。
``flags``
    ``flags`` 参数指定了映射对象的类型、映射选项以及对映射页副本所做的修改是否仅由进程私有或与其他引用共享。
    ``MAP_FIXED`` 请求驱动程序选择除指定地址以外的其他地址。如果指定的地址无法使用，:c:func:`mmap()` 将失败。如果指定了 ``MAP_FIXED`` ，则 ``start`` 必须是页面大小的倍数。不建议使用此选项。
    必须设置 ``MAP_SHARED`` 或 ``MAP_PRIVATE`` 其中之一。
    ``MAP_SHARED`` 允许应用程序与其他（例如子）进程共享映射内存。
.. note::

       Linux数字电视应用程序不应设置 ``MAP_PRIVATE`` 、 ``MAP_DENYWRITE`` 、 ``MAP_EXECUTABLE`` 或 ``MAP_ANON`` 标志。
``fd``
    由 :c:func:`open()` 返回的文件描述符
``offset``
    在设备内存中的缓冲区偏移量，由 :ref:`DMX_QUERYBUF` ioctl 返回

描述
====

:c:func:`mmap()` 函数请求将 `fd` 指定的设备中从 `offset` 开始的 `length` 字节映射到应用程序地址空间，最好是在地址 `start`。这个地址只是一个提示，并且通常指定为 0。

合适的长度和偏移参数可以通过 :ref:`DMX_QUERYBUF` ioctl 查询。在查询缓冲区之前，必须使用 :ref:`DMX_REQBUFS` ioctl 分配缓冲区。
要取消映射缓冲区，则使用 :c:func:`munmap()` 函数。

返回值
======

如果成功，:c:func:`mmap()` 返回指向映射缓冲区的指针。如果失败，则返回 `MAP_FAILED`（-1），并且设置 `errno` 变量以指示错误原因。可能的错误代码包括：

EBADF
    `fd` 不是一个有效的文件描述符
EACCES
    `fd` 未打开用于读写
EINVAL
    `start` 或 `length` 或 `offset` 不合适（例如，它们太大或未对齐到 `PAGESIZE` 边界）。

    `flags` 或 `prot` 值不受支持
没有通过 :ref:`DMX_REQBUFS` ioctl 分配任何缓冲区
ENOMEM
没有足够的物理内存或虚拟内存来完成请求。
