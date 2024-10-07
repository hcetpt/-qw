SPDX 许可证标识符：GPL-2.0 或 GFDL-1.1 无不变性或更高版本
.. c:命名空间:: MC

.. _媒体请求API:

请求 API
========

请求 API 被设计用于使 V4L2 能够满足现代设备（无状态编解码器、复杂的摄像头管道等）和 API（Android 编码器 v2）的需求。其中一项需求是属于同一管道的设备能够在每帧的基础上重新配置并紧密协作。另一项需求是支持无状态编解码器，这些编解码器要求在特定帧上应用控制（即“每帧控制”），以便高效使用。虽然最初的用例是 V4L2，但它也可以扩展到其他子系统，只要它们使用媒体控制器即可。如果没有请求 API 支持这些特性通常是不可能的，即使可能也会非常低效：用户空间必须刷新媒体管道上的所有活动，为下一帧重新配置它，排队要处理的缓冲区，并等待所有缓冲区都可用以出队列后才能考虑下一帧。这违背了拥有缓冲区队列的目的，因为实际上每次只会排队一个缓冲区。

请求 API 允许将管道（媒体控制器拓扑结构+每个媒体实体的配置）的特定配置与特定缓冲区相关联。这使得用户空间可以提前安排具有不同配置的多个任务（"请求"），并且知道会在需要时应用配置以获得预期结果。请求完成时的配置值也可供读取。

一般用法
--------

请求 API 扩展了媒体控制器 API，并且与特定子系统的 API 配合以支持请求的使用。在媒体控制器级别，请求是从支持的媒体控制器设备节点分配的。然后通过请求文件描述符以不透明的方式管理其生命周期。通过为请求支持扩展的特定子系统 API（如带有显式 `request_fd` 参数的 V4L2 API）来访问存储在请求中的配置数据、缓冲区句柄和处理结果。

请求分配
--------

用户空间使用 :ref:`MEDIA_IOC_REQUEST_ALLOC` 为媒体设备节点分配请求。这返回一个代表请求的文件描述符。通常会分配几个这样的请求。

请求准备
--------

标准的 V4L2 控制命令可以接收一个请求文件描述符，以表明该控制命令是所述请求的一部分，不应立即执行。参见 :ref:`MEDIA_IOC_REQUEST_ALLOC` 以获取支持此功能的控制命令列表。使用 `request_fd` 参数设置的配置被存储而不是立即应用，而排队到请求中的缓冲区在请求本身排队之前不会进入常规缓冲区队列。

请求提交
--------

一旦指定了请求的配置和缓冲区，可以通过在请求文件描述符上调用 :ref:`MEDIA_REQUEST_IOC_QUEUE` 来将其排队。请求必须包含至少一个缓冲区，否则将返回 `ENOENT`。
排队的请求无法再进行修改。

.. 注意::
   对于内存到内存设备(:ref:`mem2mem`)，您只能为输出缓冲区使用请求，而不能用于捕获缓冲区。尝试将捕获缓冲区添加到请求中会导致 ``EBADR`` 错误。

如果请求包含多个实体的配置，各个驱动程序可能会同步操作，以确保在处理缓冲区之前应用请求的管道拓扑结构。媒体控制器驱动程序尽力实现这一目标，但由于硬件限制，可能无法实现完美的原子性。
.. 注意::

   不允许混合使用排队请求和直接排队缓冲区：无论哪种方法先被使用，都会锁定该方法直到调用 :ref:`VIDIOC_STREAMOFF <VIDIOC_STREAMON>` 或关闭设备 :ref:`closed <func-close>`。当先前通过请求排队缓冲区后再尝试直接排队缓冲区，或者反之亦然时，会导致 ``EBUSY`` 错误。
控制项可以在没有请求的情况下设置，并且会立即生效，无论是否正在使用请求。

.. 注意::

   通过请求设置相同的控制项并直接设置可能会导致未定义的行为！

用户空间可以通过 :c:func:`poll()` 调用来等待请求完成。请求被认为已完成，一旦其所有关联的缓冲区都可用于出队，并且所有相关联的控制项都已更新为完成时刻的值。
请注意，用户空间不需要等待请求完成即可出队缓冲区：在请求执行中途可用的缓冲区可以独立于请求的状态进行出队。
完成的请求包含了请求执行后设备的状态。用户空间可以通过调用 :ref:`ioctl VIDIOC_G_EXT_CTRLS <VIDIOC_G_EXT_CTRLS>` 并传入请求文件描述符来查询该状态。对于已排队但尚未完成的请求调用 :ref:`ioctl VIDIOC_G_EXT_CTRLS <VIDIOC_G_EXT_CTRLS>` 将返回 ``EBUSY``，因为驱动程序在请求执行过程中可能会随时更改控制值。

.. _media-request-life-time:

回收与销毁
------------

最后，完成的请求可以被丢弃或重复使用。对请求文件描述符调用 :c:func:`close()` 将使该文件描述符不可用，并且一旦内核不再使用该请求，请求将被释放。也就是说，如果请求已排队然后关闭了文件描述符，则不会立即释放，直到驱动程序完成了请求。

:ref:`MEDIA_REQUEST_IOC_REINIT` 将清除请求的状态并使其再次可用。此操作不保留任何状态：请求就像刚刚分配的一样。
### 编解码器设备示例
--------------------------

对于如 :ref:`codecs <mem2mem>` 这样的用例，可以使用请求 API 将特定的控制项与输出缓冲区关联起来，允许用户空间提前排队多个这样的缓冲区。它还可以利用请求的能力，在请求完成时捕获控制项的状态，从而读取可能发生变化的信息。

在代码中，用户空间在获取一个请求后，可以为该请求分配控制项和一个输出缓冲区：

```c
struct v4l2_buffer buf;
struct v4l2_ext_controls ctrls;
int req_fd;
..
if (ioctl(media_fd, MEDIA_IOC_REQUEST_ALLOC, &req_fd))
    return errno;
..
ctrls.which = V4L2_CTRL_WHICH_REQUEST_VAL;
ctrls.request_fd = req_fd;
if (ioctl(codec_fd, VIDIOC_S_EXT_CTRLS, &ctrls))
    return errno;
..
buf.type = V4L2_BUF_TYPE_VIDEO_OUTPUT;
buf.flags |= V4L2_BUF_FLAG_REQUEST_FD;
buf.request_fd = req_fd;
if (ioctl(codec_fd, VIDIOC_QBUF, &buf))
    return errno;
```

请注意，不允许将请求 API 用于捕获缓冲区，因为那里没有每帧设置需要报告。

一旦请求完全准备就绪，可以将其排队到驱动程序：

```c
if (ioctl(req_fd, MEDIA_REQUEST_IOC_QUEUE))
    return errno;
```

然后，用户空间可以通过在其文件描述符上调用 `poll()` 来等待请求完成，或者开始取消排队捕获缓冲区。通常，用户空间会希望尽快获取捕获缓冲区，这可以通过常规的 :ref:`VIDIOC_DQBUF <VIDIOC_QBUF>` 来实现：

```c
struct v4l2_buffer buf;

memset(&buf, 0, sizeof(buf));
buf.type = V4L2_BUF_TYPE_VIDEO_CAPTURE;
if (ioctl(codec_fd, VIDIOC_DQBUF, &buf))
    return errno;
```

请注意，这个示例为了简单起见假设每个输出缓冲区都会有一个捕获缓冲区，但情况不一定如此。

然后，确保通过轮询请求文件描述符来确认请求已完成，并通过调用 :ref:`VIDIOC_G_EXT_CTRLS <VIDIOC_G_EXT_CTRLS>` 查询其完成时的控制值。这对于那些我们希望在捕获缓冲区生成后立即查询值的易变控制项特别有用：

```c
struct pollfd pfd = { .events = POLLPRI, .fd = req_fd };
poll(&pfd, 1, -1);
..
ctrls.which = V4L2_CTRL_WHICH_REQUEST_VAL;
ctrls.request_fd = req_fd;
if (ioctl(codec_fd, VIDIOC_G_EXT_CTRLS, &ctrls))
    return errno;
```

当我们不再需要这个请求时，可以使用 :ref:`MEDIA_REQUEST_IOC_REINIT` 回收以供重用。
```c
if (ioctl(req_fd, MEDIA_REQUEST_IOC_REINIT))
    return errno;

... 或关闭其文件描述符以完全释放它
``` 

```c
close(req_fd);
```

简单的捕获设备示例
--------------------

在简单的捕获设备中，请求可用于指定应用于特定CAPTURE缓冲区的控制。

```c
struct v4l2_buffer buf;
struct v4l2_ext_controls ctrls;
int req_fd;
..
if (ioctl(media_fd, MEDIA_IOC_REQUEST_ALLOC, &req_fd))
    return errno;
..
ctrls.which = V4L2_CTRL_WHICH_REQUEST_VAL;
ctrls.request_fd = req_fd;
if (ioctl(camera_fd, VIDIOC_S_EXT_CTRLS, &ctrls))
    return errno;
..
buf.type = V4L2_BUF_TYPE_VIDEO_CAPTURE;
buf.flags |= V4L2_BUF_FLAG_REQUEST_FD;
buf.request_fd = req_fd;
if (ioctl(camera_fd, VIDIOC_QBUF, &buf))
    return errno;
```

一旦请求完全准备就绪，就可以将其排队到驱动程序：

```c
if (ioctl(req_fd, MEDIA_REQUEST_IOC_QUEUE))
    return errno;
```

然后用户空间可以出队缓冲区，等待请求完成，查询控制，并像上面的M2M示例那样回收请求。
