SPDX 许可证标识符: GFDL-1.1-no-invariants-or-later

.. c:namespace:: V4L

.. _io:

############
输入/输出
############
V4L2 API 定义了多种不同的方法来从设备读取数据或向设备写入数据。所有与应用程序交换数据的驱动程序必须支持其中至少一种方法。
使用经典的 I/O 方法，通过 :c:func:`read()` 和 :c:func:`write()` 函数在打开 V4L2 设备后会自动选择这种方法。如果驱动程序不支持这种方法，则任何尝试读取或写入的操作都会失败。
其他方法需要协商。要选择带有内存映射或用户缓冲区的流式 I/O 方法，应用程序应调用 :ref:`VIDIOC_REQBUFS` ioctl。
视频覆盖可以被视为另一种 I/O 方法，尽管应用程序不会直接接收图像数据。通过使用 :ref:`VIDIOC_S_FMT <VIDIOC_G_FMT>` ioctl 初始化视频覆盖来选择此方法。更多信息请参见 :ref:`overlay`。
通常每个文件描述符关联一个确切的 I/O 方法（包括覆盖）。唯一的例外是不与驱动程序交换数据的应用程序（“面板应用程序”，详见 :ref:`open`）以及允许使用同一文件描述符同时进行视频捕获和覆盖的驱动程序，以兼容 V4L 和早期版本的 V4L2。
:ref:`VIDIOC_S_FMT <VIDIOC_G_FMT>` 和 :ref:`VIDIOC_REQBUFS` 在某种程度上允许这样做，但为了简化，驱动程序无需支持除关闭和重新打开设备之外的 I/O 方法切换（首次从读写切换后）。
以下各节将更详细地描述各种 I/O 方法。

.. toctree::
    :maxdepth: 1

    rw
    mmap
    userp
    dmabuf
    buffer
    field-order
