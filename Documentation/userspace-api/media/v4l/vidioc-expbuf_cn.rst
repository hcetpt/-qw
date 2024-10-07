SPDX 许可证标识符: GFDL-1.1-no-invariants-or-later
.. c:namespace:: V4L

.. _VIDIOC_EXPBUF:

*******************
ioctl VIDIOC_EXPBUF
*******************

名称
====

VIDIOC_EXPBUF - 将缓冲区导出为 DMABUF 文件描述符

概要
====

.. c:macro:: VIDIOC_EXPBUF

``int ioctl(int fd, VIDIOC_EXPBUF, struct v4l2_exportbuffer *argp)``

参数
====

``fd``
    由 :c:func:`open()` 返回的文件描述符
``argp``
    指向 :c:type:`v4l2_exportbuffer` 结构体的指针

描述
====

此 ioctl 是对 :ref:`内存映射<mmap>` I/O 方法的扩展，因此仅适用于 ``V4L2_MEMORY_MMAP`` 缓冲区。在使用 :ref:`VIDIOC_REQBUFS` ioctl 分配缓冲区后，可以在任何时候将缓冲区导出为 DMABUF 文件。
为了导出一个缓冲区，应用程序需要填充 :c:type:`v4l2_exportbuffer` 结构体。“type” 字段应设置为与之前在 :c:type:`v4l2_requestbuffers` 结构体中使用的相同类型的缓冲区。
应用程序还必须设置 “index” 字段。有效的索引范围是从零到通过 :ref:`VIDIOC_REQBUFS` （:c:type:`v4l2_requestbuffers` 结构体中的 “count”）分配的缓冲区数量减一。对于多平面 API，应用程序应将 “plane” 字段设置为要导出的平面索引。有效的平面范围从零到当前活动格式的有效平面数的最大值。对于单平面 API，应用程序必须将 “plane” 设置为零。
“flags” 字段可以附加一些标志。详情请参考 `open()` 的手册页。目前只支持 O_CLOEXEC、O_RDONLY、O_WRONLY 和 O_RDWR。其他所有字段必须设置为零。在多平面 API 的情况下，每个平面都需单独使用多个 :ref:`VIDIOC_EXPBUF` 调用来导出。
调用 :ref:`VIDIOC_EXPBUF` 后，“fd” 字段将由驱动程序设置。这是一个 DMABUF 文件描述符。应用程序可以将其传递给其他支持 DMABUF 的设备。有关将 DMABUF 文件导入到 V4L2 节点的详细信息，请参阅 :ref:`DMABUF 导入<dmabuf>`。建议在不再使用 DMABUF 文件时关闭它，以便回收相关联的内存。

示例
====

.. code-block:: c

    int buffer_export(int v4lfd, enum v4l2_buf_type bt, int index, int *dmafd)
    {
        struct v4l2_exportbuffer expbuf;

        memset(&expbuf, 0, sizeof(expbuf));
        expbuf.type = bt;
        expbuf.index = index;
        if (ioctl(v4lfd, VIDIOC_EXPBUF, &expbuf) == -1) {
            perror("VIDIOC_EXPBUF");
            return -1;
        }

        *dmafd = expbuf.fd;

        return 0;
    }

.. code-block:: c

    int buffer_export_mp(int v4lfd, enum v4l2_buf_type bt, int index,
                         int dmafd[], int n_planes)
    {
        int i;

        for (i = 0; i < n_planes; ++i) {
            struct v4l2_exportbuffer expbuf;

            memset(&expbuf, 0, sizeof(expbuf));
            expbuf.type = bt;
            expbuf.index = index;
            expbuf.plane = i;
            if (ioctl(v4lfd, VIDIOC_EXPBUF, &expbuf) == -1) {
                perror("VIDIOC_EXPBUF");
                while (i)
                    close(dmafd[--i]);
                return -1;
            }
            dmafd[i] = expbuf.fd;
        }

        return 0;
    }

.. c:type:: v4l2_exportbuffer

.. tabularcolumns:: |p{4.4cm}|p{4.4cm}|p{8.5cm}|

.. flat-table:: struct v4l2_exportbuffer
    :header-rows:  0
    :stub-columns: 0
    :widths:       1 1 2

    * - __u32
      - ``type``
      - 缓冲区类型，与 :c:type:`v4l2_format` 结构体中的 ``type`` 或 :c:type:`v4l2_requestbuffers` 结构体中的 ``type`` 相同，由应用程序设置。详见 :c:type:`v4l2_buf_type`
    * - __u32
      - ``index``
      - 缓冲区编号，由应用程序设置。此字段仅用于 :ref:`内存映射<mmap>` I/O，其值可以从零到通过 :ref:`VIDIOC_REQBUFS` 和/或 :ref:`VIDIOC_CREATE_BUFS` ioctl 分配的缓冲区数量减一。
* - __u32
      - ``plane``
      - 当使用多平面 API 时，要导出的平面的索引。否则此值必须设为零。
* - __u32
      - ``flags``
      - 新创建文件的标志，目前仅支持 ``O_CLOEXEC``、``O_RDONLY``、``O_WRONLY`` 和 ``O_RDWR``，更多详细信息请参阅 `open()` 手册。
* - __s32
      - ``fd``
      - 与缓冲区关联的 DMABUF 文件描述符。由驱动程序设置。
* - __u32
      - ``reserved[11]``
      - 保留字段，供将来使用。驱动程序和应用程序必须将数组设为零。

返回值
======

成功时返回 0，失败时返回 -1 并且设置适当的 ``errno`` 变量。通用错误代码在《通用错误代码 <gen-errors>`》章节中有描述。

EINVAL
    队列不在 MMAP 模式中或不支持 DMABUF 导出，或者 ``flags``、``type``、``index`` 或 ``plane`` 字段无效。
