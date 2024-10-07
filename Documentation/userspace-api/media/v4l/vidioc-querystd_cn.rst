SPDX 许可声明标识符: GFDL-1.1-no-invariants-or-later
.. c:namespace:: V4L

.. _VIDIOC_QUERYSTD:

*********************************************
ioctl VIDIOC_QUERYSTD, VIDIOC_SUBDEV_QUERYSTD
*********************************************

名称
====

VIDIOC_QUERYSTD - VIDIOC_SUBDEV_QUERYSTD - 检测当前输入接收到的视频标准

概要
====

.. c:macro:: VIDIOC_QUERYSTD

``int ioctl(int fd, VIDIOC_QUERYSTD, v4l2_std_id *argp)``

.. c:macro:: VIDIOC_SUBDEV_QUERYSTD

``int ioctl(int fd, VIDIOC_SUBDEV_QUERYSTD, v4l2_std_id *argp)``

参数
====

``fd``
    由 :c:func:`open()` 返回的文件描述符
``argp``
    指向 :c:type:`v4l2_std_id` 的指针

描述
====

硬件可能能够自动检测当前的视频标准。为此，应用程序通过一个指向 :ref:`v4l2_std_id <v4l2-std-id>` 类型的指针调用 :ref:`VIDIOC_QUERYSTD`。驱动程序在这里存储一组候选标准，可以是一个单一标志或一组支持的标准（例如，如果硬件只能区分50Hz和60Hz系统）。如果没有检测到信号，则驱动程序将返回 V4L2_STD_UNKNOWN。当无法检测或检测失败时，集合必须包含当前视频输入或输出支持的所有标准。
.. note::

   如果检测到新的视频标准，驱动程序不应自动切换视频标准。相反，驱动程序应该发送 ``V4L2_EVENT_SOURCE_CHANGE`` 事件（如果支持的话），并期望用户空间通过调用 :ref:`VIDIOC_QUERYSTD` 来采取行动。原因是新的视频标准也可能意味着不同的缓冲区大小，并且你不能在运行时改变缓冲区大小。一般来说，接收到源变更事件的应用程序需要调用 :ref:`VIDIOC_QUERYSTD`，并且如果检测到的视频标准有效，它们需要停止流传输、设置新标准、分配新的缓冲区并重新开始流传输。
返回值
======

成功时返回0，错误时返回-1，并且设置 ``errno`` 变量为适当的值。通用错误代码在 :ref:`Generic Error Codes <gen-errors>` 章节中描述
ENODATA
    此输入或输出不支持标准视频时序
