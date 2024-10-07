SPDX 许可声明标识符: GFDL-1.1-no-invariants-or-later
.. c:namespace:: V4L

.. _userp:

******************************
流输入/输出（用户指针）
******************************

当 `V4L2_CAP_STREAMING` 标志在由 `VIDIOC_QUERYCAP` ioctl 返回的结构体 :c:type:`v4l2_capability` 的 `capabilities` 字段中被设置时，输入和输出设备支持此I/O方法。如果特定的用户指针方法（不仅仅是内存映射）是否支持，则需要通过调用 `VIDIOC_REQBUFS` ioctl 并将内存类型设置为 `V4L2_MEMORY_USERPTR` 来确定。这种I/O方法结合了读写和内存映射方法的优点。缓冲区（平面）由应用程序本身分配，并且可以位于例如虚拟或共享内存中。仅交换数据指针，这些指针和元信息通过结构体 :c:type:`v4l2_buffer` （或多平面API情况下的结构体 :c:type:`v4l2_plane` ）传递。必须通过调用 `VIDIOC_REQBUFS` 并指定所需的缓冲区类型来切换驱动程序到用户指针I/O模式。没有任何预先分配的缓冲区（平面），因此它们没有索引，也无法像使用 `VIDIOC_QUERYBUF <VIDIOC_QUERYBUF>` ioctl 查询映射的缓冲区那样进行查询。

示例：使用用户指针启动流I/O
=================================

.. code-block:: c

    struct v4l2_requestbuffers reqbuf;

    memset (&reqbuf, 0, sizeof (reqbuf));
    reqbuf.type = V4L2_BUF_TYPE_VIDEO_CAPTURE;
    reqbuf.memory = V4L2_MEMORY_USERPTR;

    if (ioctl (fd, VIDIOC_REQBUFS, &reqbuf) == -1) {
	if (errno == EINVAL)
	    printf ("视频捕获或用户指针流不被支持\n");
	else
	    perror ("VIDIOC_REQBUFS");

	exit (EXIT_FAILURE);
    }

缓冲区（平面）地址和大小通过 `VIDIOC_QBUF <VIDIOC_QBUF>` ioctl 在运行时传递。尽管缓冲区通常会循环使用，但应用程序可以在每次 `VIDIOC_QBUF <VIDIOC_QBUF>` 调用时传递不同的地址和大小。如果硬件需要，驱动程序会在物理内存中交换内存页以创建连续的内存区域。这在内核的虚拟内存子系统中对应用程序透明地发生。当缓冲区页面被交换到磁盘后，它们会被带回并最终锁定在物理内存中以供DMA使用。[#f1]_

已填充或显示的缓冲区通过 `VIDIOC_DQBUF <VIDIOC_QBUF>` ioctl 取出队列。驱动程序可以在DMA完成与该ioctl之间的任何时候解锁内存页。当调用 `VIDIOC_STREAMOFF <VIDIOC_STREAMON>`、`VIDIOC_REQBUFS` 或关闭设备时，内存也会被解锁。应用程序必须注意不要在未取出队列的情况下释放缓冲区。首先，缓冲区会保持锁定状态更长时间，浪费物理内存。其次，驱动程序不会在内存返回到应用程序的空闲列表并随后用于其他用途时得到通知，可能会完成请求的DMA并覆盖宝贵的数据。对于捕获应用程序，通常会将一些空缓冲区入队列，开始捕获并进入读取循环。在此过程中，应用程序等待直到可以取出队列一个已填充的缓冲区，并在不再需要数据时重新入队列该缓冲区。输出应用程序则填充并入队列缓冲区，当有足够的缓冲区堆积起来时开始输出。在写入循环中，当应用程序缺少可用的空缓冲区时，必须等待直到可以取出队列一个空缓冲区并重新使用它。

有两种方法可以让应用程序暂停执行直到一个或多个缓冲区可以取出队列。默认情况下，当队列中没有缓冲区时 `VIDIOC_DQBUF <VIDIOC_QBUF>` 会阻塞。如果在调用 :c:func:`open()` 函数时指定了 `O_NONBLOCK` 标志，则当没有缓冲区可用时 `VIDIOC_DQBUF <VIDIOC_QBUF>` 会立即返回一个 `EAGAIN` 错误代码。无论何时 :ref:`select() <func-select>` 或 :c:func:`poll()` 函数总是可用的。

要开始和停止捕获或输出应用程序，请调用 `VIDIOC_STREAMON <VIDIOC_STREAMON>` 和 `VIDIOC_STREAMOFF <VIDIOC_STREAMON>` ioctl。
.. 注意::

   :ref:`VIDIOC_STREAMOFF <VIDIOC_STREAMON>` 会从两个队列中移除所有缓冲区，并作为副作用解锁所有缓冲区。由于在多任务系统中没有“现在”执行的概念，如果应用程序需要与另一个事件同步，则应检查结构体 :c:type:`v4l2_buffer` 的 ``timestamp`` 字段，以获取捕获或输出的缓冲区。

实现用户指针 I/O 的驱动程序必须支持以下 ioctl：:ref:`VIDIOC_REQBUFS <VIDIOC_REQBUFS>`、:ref:`VIDIOC_QBUF <VIDIOC_QBUF>`、:ref:`VIDIOC_DQBUF <VIDIOC_QBUF>`、:ref:`VIDIOC_STREAMON <VIDIOC_STREAMON>` 和 :ref:`VIDIOC_STREAMOFF <VIDIOC_STREAMON>`，以及 :c:func:`select()` 和 :c:func:`poll()` 函数。[#f2]_

.. [#f1]
   我们期望频繁使用的缓冲区通常不会被交换出去。
   无论如何，交换、锁定或生成分散-聚集列表的过程可能会耗时。这种延迟可以通过增加输入缓冲区队列的深度来掩盖，并且可能通过维护缓存来假设缓冲区很快会被再次入队。另一方面，为了优化内存使用，驱动程序可以限制提前锁定的缓冲区数量，并优先回收最近使用的缓冲区。当然，输入队列中的空缓冲区页面不需要保存到磁盘上。输出缓冲区必须保存在输入和输出队列上，因为应用程序可能与其他进程共享它们。

.. [#f2]
   在驱动程序级别，:c:func:`select()` 和 :c:func:`poll()` 是相同的，并且 :c:func:`select()` 太重要了，不能是可选的。
   其余部分应该是显而易见的。
