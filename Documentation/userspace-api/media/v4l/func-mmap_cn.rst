SPDX 许可声明标识符：GFDL-1.1-no-invariants-or-later

C 命名空间：V4L

.. _func-mmap:

***********
V4L2 mmap()
***********

名称
====

v4l2-mmap - 将设备内存映射到应用程序地址空间

概要
========

.. code-block:: c

    #include <unistd.h>
    #include <sys/mman.h>

.. c:function:: void *mmap( void *start, size_t length, int prot, int flags, int fd, off_t offset )

参数
=========

``start``
    将缓冲区映射到应用程序地址空间中的这个地址。
    当指定 ``MAP_FIXED`` 标志时，``start`` 必须是页面大小的倍数，并且如果指定的地址不能使用，则 ``mmap()`` 会失败。不建议使用此选项；应用程序应在此处指定一个 ``NULL`` 指针。

``length``
    要映射的内存区域长度。对于单平面 API，这必须是驱动程序在结构体 :c:type:`v4l2_buffer` 的 ``length`` 字段中返回的值；对于多平面 API，这必须是驱动程序在结构体 :c:type:`v4l2_plane` 的 ``length`` 字段中返回的值。

``prot``
    ``prot`` 参数描述了所需的内存保护。无论设备类型和数据交换方向如何，都应将其设置为 ``PROT_READ`` | ``PROT_WRITE``，允许对图像缓冲区进行读写访问。驱动程序应至少支持这种标志组合。
    
    .. note::
    
       #. Linux 的 ``videobuf`` 内核模块（某些驱动程序使用）仅支持 ``PROT_READ`` | ``PROT_WRITE``。如果驱动程序不支持所需的保护，则 ``mmap()`` 函数将失败。
       #. 设备内存访问（例如带有视频捕获硬件的显卡上的内存）可能比主内存访问带来性能损失，或者读取速度可能明显慢于写入速度或反之亦然。在这种情况下，其他 I/O 方法可能更高效。

``flags``
    ``flags`` 参数指定了映射对象的类型、映射选项以及对映射副本所做的修改是否仅对该进程私有还是与其他引用共享。
    
    ``MAP_FIXED`` 请求驱动程序选择指定的地址而不是其他地址。如果指定的地址不能使用，则 ``mmap()`` 将失败。如果指定了 ``MAP_FIXED``，则 ``start`` 必须是页面大小的倍数。不建议使用此选项。
    
    必须设置 ``MAP_SHARED`` 或 ``MAP_PRIVATE`` 标志之一。
``MAP_SHARED`` 允许应用程序与其他进程（例如子进程）共享映射的内存。
.. note::

       Linux 的 ``videobuf`` 模块被一些驱动程序使用，仅支持 ``MAP_SHARED``。``MAP_PRIVATE`` 请求写时复制语义。V4L2 应用程序不应设置 ``MAP_PRIVATE``、``MAP_DENYWRITE``、``MAP_EXECUTABLE`` 或 ``MAP_ANON`` 标志。

``fd``
    由 :c:func:`open()` 返回的文件描述符。
``offset``
    缓冲区在设备内存中的偏移量。对于单平面 API，这必须是驱动程序返回的结构体 :c:type:`v4l2_buffer` 中 ``m`` 联合的 ``offset`` 字段值；对于多平面 API，这必须是驱动程序返回的结构体 :c:type:`v4l2_plane` 中 ``m`` 联合的 ``mem_offset`` 字段值。

描述
====

:c:func:`mmap()` 函数请求将由 ``fd`` 指定的设备内存中从 ``offset`` 开始的 ``length`` 字节映射到应用程序地址空间，最好映射到地址 ``start``。此地址只是一个提示，通常指定为 0。

合适的长度和偏移参数可以通过 :ref:`VIDIOC_QUERYBUF` ioctl 查询。在查询缓冲区之前，必须使用 :ref:`VIDIOC_REQBUFS` ioctl 分配缓冲区。

要取消映射缓冲区，请使用 :c:func:`munmap()` 函数。

返回值
======

成功时，:c:func:`mmap()` 返回一个指向映射缓冲区的指针。失败时，返回 ``MAP_FAILED``（-1），并根据具体情况设置 ``errno`` 变量。可能的错误代码包括：

EBADF
    ``fd`` 不是一个有效的文件描述符。
EACCES
    ``fd`` 未打开用于读写。
EINVAL
    ``start`` 或 ``length`` 或 ``offset`` 不合适。（例如
它们太大，或者没有对齐到“PAGESIZE”边界。

`flags` 或 `prot` 值不被支持。
没有使用 :ref:`VIDIOC_REQBUFS` ioctl 分配缓冲区。
ENOMEM
没有足够的物理或虚拟内存来完成请求。
