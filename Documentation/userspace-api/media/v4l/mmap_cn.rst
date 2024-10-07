SPDX 许可证标识符: GFDL-1.1-no-invariants-or-later
.. c:namespace:: V4L

.. _mmap:

*******************************
流式 I/O（内存映射）
*******************************

当设备的 `capabilities` 字段中的 `V4L2_CAP_STREAMING` 标志被设置时，输入和输出设备支持这种 I/O 方法。此标志在由 `VIDIOC_QUERYCAP` ioctl 返回的结构体 `:c:type:'v4l2_capability'` 中定义。有两种流式方法，要确定是否支持内存映射方式，应用程序必须调用 `VIDIOC_REQBUFS` ioctl 并将内存类型设置为 `V4L2_MEMORY_MMAP`。

流式是一种 I/O 方法，在应用程序和驱动程序之间仅交换缓冲区指针而不复制数据本身。内存映射主要用于将设备内存中的缓冲区映射到应用程序的地址空间。设备内存可以是例如带有视频捕获附加组件的显卡上的视频内存。然而，由于长期以来这是最高效的 I/O 方法，许多其他驱动程序也支持流式传输，并在可直接访问的主内存中分配缓冲区。

一个驱动程序可以支持多组缓冲区。每组由一个唯一的缓冲区类型值来标识。这些组是独立的，每个组可以保存不同类型的数据。为了同时访问不同的组，需要使用不同的文件描述符。[#f1]_

为了分配设备缓冲区，应用程序需要调用 `VIDIOC_REQBUFS` ioctl 并指定所需的缓冲区数量和缓冲区类型，例如 `V4L2_BUF_TYPE_VIDEO_CAPTURE`。此 ioctl 还可用于更改缓冲区数量或释放已分配的内存，前提是没有任何缓冲区仍然处于映射状态。

在应用程序能够访问缓冲区之前，它们必须使用 `:c:func:'mmap()'` 函数将其映射到自己的地址空间。可以通过 `VIDIOC_QUERYBUF` ioctl 确定缓冲区在设备内存中的位置。在单平面 API 情况下，从结构体 `:c:type:'v4l2_buffer'` 返回的 `m.offset` 和 `length` 分别作为 `:c:func:'mmap()'` 函数的第六个和第二个参数传递。当使用多平面 API 时，结构体 `:c:type:'v4l2_buffer'` 包含一个 `:c:type:'v4l2_plane'` 结构体数组，每个结构体包含其自己的 `m.offset` 和 `length`。当使用多平面 API 时，每个缓冲区的每个平面都必须单独映射，因此调用 `:c:func:'mmap()'` 的次数应该等于缓冲区数量乘以每个缓冲区中的平面数量。偏移量和长度值不得修改。请记住，缓冲区是在物理内存而不是虚拟内存中分配的，后者可以被交换到磁盘。应用程序应尽快使用 `:c:func:'munmap()'` 函数释放缓冲区。

示例：在单平面 API 中映射缓冲区
==================================

.. code-block:: c

    struct v4l2_requestbuffers reqbuf;
    struct {
        void *start;
        size_t length;
    } *buffers;
    unsigned int i;

    memset(&reqbuf, 0, sizeof(reqbuf));
    reqbuf.type = V4L2_BUF_TYPE_VIDEO_CAPTURE;
    reqbuf.memory = V4L2_MEMORY_MMAP;
    reqbuf.count = 20;

    if (-1 == ioctl(fd, VIDIOC_REQBUFS, &reqbuf)) {
        if (errno == EINVAL)
            printf("不支持视频捕捉或 mmap 流式传输\n");
        else
            perror("VIDIOC_REQBUFS");

        exit(EXIT_FAILURE);
    }

    /* 我们至少需要五个缓冲区。 */

    if (reqbuf.count < 5) {
        /* 您可能需要在此处释放缓冲区。 */
        printf("缓冲区内存不足\n");
        exit(EXIT_FAILURE);
    }

    buffers = calloc(reqbuf.count, sizeof(*buffers));
    assert(buffers != NULL);

    for (i = 0; i < reqbuf.count; i++) {
        struct v4l2_buffer buffer;

        memset(&buffer, 0, sizeof(buffer));
        buffer.type = reqbuf.type;
        buffer.memory = V4L2_MEMORY_MMAP;
        buffer.index = i;

        if (-1 == ioctl(fd, VIDIOC_QUERYBUF, &buffer)) {
            perror("VIDIOC_QUERYBUF");
            exit(EXIT_FAILURE);
        }

        buffers[i].length = buffer.length; /* 记住用于 munmap() */

        buffers[i].start = mmap(NULL, buffer.length,
                PROT_READ | PROT_WRITE, /* 推荐 */
                MAP_SHARED,             /* 推荐 */
                fd, buffer.m.offset);

        if (MAP_FAILED == buffers[i].start) {
            /* 如果您不在此处退出，则应使用 unmap() 和 free() 解映射和释放已映射的缓冲区。 */
            perror("mmap");
            exit(EXIT_FAILURE);
        }
    }

    /* 清理。 */

    for (i = 0; i < reqbuf.count; i++)
        munmap(buffers[i].start, buffers[i].length);

示例：在多平面 API 中映射缓冲区
==================================

.. code-block:: c

    struct v4l2_requestbuffers reqbuf;
    /* 当前格式使用每个缓冲区 3 个平面 */
    #define FMT_NUM_PLANES = 3

    struct {
        void *start[FMT_NUM_PLANES];
        size_t length[FMT_NUM_PLANES];
    } *buffers;
    unsigned int i, j;

    memset(&reqbuf, 0, sizeof(reqbuf));
    reqbuf.type = V4L2_BUF_TYPE_VIDEO_CAPTURE_MPLANE;
    reqbuf.memory = V4L2_MEMORY_MMAP;
    reqbuf.count = 20;

    if (ioctl(fd, VIDIOC_REQBUFS, &reqbuf) < 0) {
        if (errno == EINVAL)
            printf("不支持视频捕捉或 mmap 流式传输\n");
        else
            perror("VIDIOC_REQBUFS");

        exit(EXIT_FAILURE);
    }

    /* 我们至少需要五个缓冲区。 */

    if (reqbuf.count < 5) {
        /* 您可能需要在此处释放缓冲区。 */
        printf("缓冲区内存不足\n");
        exit(EXIT_FAILURE);
    }

    buffers = calloc(reqbuf.count, sizeof(*buffers));
    assert(buffers != NULL);

    for (i = 0; i < reqbuf.count; i++) {
        struct v4l2_buffer buffer;
        struct v4l2_plane planes[FMT_NUM_PLANES];

        memset(&buffer, 0, sizeof(buffer));
        buffer.type = reqbuf.type;
        buffer.memory = V4L2_MEMORY_MMAP;
        buffer.index = i;
        /* 在多平面 API 中，结构体 v4l2_buffer 中的 length 存储 planes 数组的大小。 */
        buffer.length = FMT_NUM_PLANES;
        buffer.m.planes = planes;

        if (ioctl(fd, VIDIOC_QUERYBUF, &buffer) < 0) {
            perror("VIDIOC_QUERYBUF");
            exit(EXIT_FAILURE);
        }

        /* 每个平面都需要单独映射 */
        for (j = 0; j < FMT_NUM_PLANES; j++) {
            buffers[i].length[j] = buffer.m.planes[j].length; /* 记住用于 munmap() */

            buffers[i].start[j] = mmap(NULL, buffer.m.planes[j].length,
                    PROT_READ | PROT_WRITE, /* 推荐 */
                    MAP_SHARED,             /* 推荐 */
                    fd, buffer.m.planes[j].m.mem_offset);

            if (MAP_FAILED == buffers[i].start[j]) {
                /* 如果您不在此处退出，则应使用 unmap() 和 free() 解映射和释放已映射的缓冲区和平面。 */
                perror("mmap");
                exit(EXIT_FAILURE);
            }
        }
    }

    /* 清理。 */

    for (i = 0; i < reqbuf.count; i++)
        for (j = 0; j < FMT_NUM_PLANES; j++)
            munmap(buffers[i].start[j], buffers[i].length[j]);

概念上，流式驱动程序维护两个缓冲区队列，一个输入队列和一个输出队列。它们将锁定到视频时钟的同步捕获或输出操作与应用程序分开，后者受随机磁盘或网络延迟以及其他进程抢占的影响，从而减少了数据丢失的可能性。队列组织为先进先出（FIFO），缓冲区将按输入 FIFO 中入队的顺序输出，并按从输出 FIFO 中出队的顺序捕获。
驱动程序可能要求始终有最少数量的缓冲区入队才能正常工作，除此之外没有限制应用程序可以提前入队或出队并处理的缓冲区数量。他们也可以按照不同于出队顺序的方式入队缓冲区，并且驱动程序可以在任意顺序下填充入队的“空”缓冲区。[#f2]_ 缓冲区的索引号（结构体 `:c:type:'v4l2_buffer'` 的 `index`）在这里不起作用，它只标识缓冲区。
最初所有映射的缓冲区都处于未出队状态，无法被驱动程序访问。对于捕获应用程序，通常首先将所有映射的缓冲区入队，然后开始捕获并进入读取循环。在这里，应用程序等待直到可以出队一个已填充的缓冲区，并在不再需要数据时重新入队该缓冲区。输出应用程序填充并入队缓冲区，当有足够的缓冲区堆积起来时，可以使用 `VIDIOC_STREAMON <VIDIOC_STREAMON>` 启动输出。
在写入循环中，当应用程序用完所有空闲缓冲区时，必须等待直到可以出队一个空缓冲区并重用它。
为了入队和出队一个缓冲区，应用程序使用 `VIDIOC_QBUF <VIDIOC_QBUF>` 和 `VIDIOC_DQBUF <VIDIOC_QBUF>` ioctl。可以随时使用 `VIDIOC_QUERYBUF` ioctl 确定缓冲区的状态（已映射、已入队、已填满或为空）。存在两种方法暂停应用程序执行直到可以出队一个或多个缓冲区。默认情况下，当输出队列中没有缓冲区时，`VIDIOC_DQBUF <VIDIOC_QBUF>` 会阻塞。如果在调用 `:c:func:'open()'` 函数时指定了 `O_NONBLOCK` 标志，当没有缓冲区可用时，`VIDIOC_DQBUF <VIDIOC_QBUF>` 会立即返回一个 `EAGAIN` 错误代码。`:c:func:'select()'` 或 `:c:func:'poll()'` 函数总是可用的。
启动和停止捕获或输出应用程序需要调用 `VIDIOC_STREAMON <VIDIOC_STREAMON>` 和 `VIDIOC_STREAMOFF <VIDIOC_STREAMON>` ioctl。

.. note::
   `VIDIOC_STREAMOFF <VIDIOC_STREAMON>` 作为副作用会从两个队列中移除所有缓冲区。由于多任务系统中没有“立即”执行的概念，如果一个应用程序需要与另一个事件同步，应该检查结构体 `v4l2_buffer` 的 `timestamp` 字段，以获取已捕获或输出的缓冲区的时间戳。

实现内存映射I/O的驱动程序必须支持 `VIDIOC_REQBUFS <VIDIOC_REQBUFS>`、`VIDIOC_QUERYBUF <VIDIOC_QUERYBUF>`、`VIDIOC_QBUF <VIDIOC_QBUF>`、`VIDIOC_DQBUF <VIDIOC_QBUF>`、`VIDIOC_STREAMON <VIDIOC_STREAMON>` 和 `VIDIOC_STREAMOFF <VIDIOC_STREAMON>` ioctl，以及 `mmap() <func-mmap>`、`munmap()`、`select() <func-select>` 和 `poll()` 函数。 [#f3]_

[捕获示例]

.. [#f1]
   可以使用一个文件描述符并在调用 `VIDIOC_QBUF` 等函数时根据需要设置缓冲区类型字段，但这会使 `select()` 函数变得不明确。我们更喜欢为每个逻辑流分配一个文件描述符的清晰方法。
视频覆盖也是一个逻辑流，尽管在连续操作过程中不需要CPU参与。

.. [#f2]
   随机入队顺序允许处理乱序图像（如视频编解码器）的应用程序提前返回缓冲区，从而减少数据丢失的可能性。随机填充顺序允许驱动程序基于后进先出（LIFO）原则重用缓冲区，利用持有分散-聚集列表等的缓存。

.. [#f3]
   在驱动程序级别，`select()` 和 `poll()` 是相同的，并且 `select()` 太重要了，不能是可选的。

其余部分应该是显而易见的。
