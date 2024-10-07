.. SPDX 许可证标识符: GFDL-1.1-no-invariants-or-later
.. c:namespace:: V4L

.. _VIDIOC_QUERY_DV_TIMINGS:

*******************************
ioctl VIDIOC_QUERY_DV_TIMINGS
*******************************

名称
====

VIDIOC_QUERY_DV_TIMINGS - VIDIOC_SUBDEV_QUERY_DV_TIMINGS - 检测当前输入接收到的 DV 预设

概要
====

.. c:macro:: VIDIOC_QUERY_DV_TIMINGS

``int ioctl(int fd, VIDIOC_QUERY_DV_TIMINGS, struct v4l2_dv_timings *argp)``

.. c:macro:: VIDIOC_SUBDEV_QUERY_DV_TIMINGS

``int ioctl(int fd, VIDIOC_SUBDEV_QUERY_DV_TIMINGS, struct v4l2_dv_timings *argp)``

参数
====

``fd``
    由 :c:func:`open()` 返回的文件描述符
``argp``
    指向结构体 :c:type:`v4l2_dv_timings` 的指针

描述
====

硬件可能能够自动检测当前的 DV 定时，类似于检测视频标准。为此，应用程序需要调用 :ref:`VIDIOC_QUERY_DV_TIMINGS` 并传入指向结构体 :c:type:`v4l2_dv_timings` 的指针。一旦硬件检测到定时信息，它将填充该定时结构体。
.. note::

   如果检测到新的定时信息，驱动程序不应自动切换定时信息。相反，驱动程序应该发送 ``V4L2_EVENT_SOURCE_CHANGE`` 事件（如果支持此功能），并期望用户空间通过调用 :ref:`VIDIOC_QUERY_DV_TIMINGS` 来采取行动。
原因是新的定时通常意味着不同的缓冲区大小，而你不能在运行时动态更改缓冲区大小。一般来说，接收源变更事件的应用程序必须调用 :ref:`VIDIOC_QUERY_DV_TIMINGS`，如果检测到的定时信息有效，则必须停止流传输、设置新的定时信息、分配新的缓冲区并重新开始流传输。
如果没有信号，则由于无法检测到定时信息而返回 ENOLINK。如果检测到了信号，但信号不稳定且接收器无法锁定信号，则返回 ``ENOLCK``。如果接收器能够锁定信号，但格式不受支持（例如，因为像素时钟超出了硬件能力范围），则驱动程序将填充尽可能找到的定时信息并返回 ``ERANGE``。在这种情况下，应用程序可以调用 :ref:`VIDIOC_DV_TIMINGS_CAP` 来比较发现的定时信息与硬件的能力，以便给用户提供更精确的反馈。

返回值
======

成功时返回 0，失败时返回 -1 并设置 ``errno`` 变量为适当的错误代码。通用错误代码在 :ref:`Generic Error Codes <gen-errors>` 章节中描述。
ENODATA
    数字视频定时不支持此输入或输出
ENOLINK
    由于未检测到信号，无法检测到定时信息
ENOLCK
    信号不稳定，硬件无法锁定信号
ERANGE
    找到了时序，但它们超出了硬件能力的范围
