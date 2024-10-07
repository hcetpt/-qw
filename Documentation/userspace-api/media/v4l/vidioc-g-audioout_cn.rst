SPDX 许可声明标识符: GFDL-1.1-no-invariants-or-later
C 命名空间:: V4L

.. _VIDIOC_G_AUDOUT:

**************************************
ioctl VIDIOC_G_AUDOUT, VIDIOC_S_AUDOUT
**************************************

名称
====

VIDIOC_G_AUDOUT - VIDIOC_S_AUDOUT - 查询或选择当前音频输出

概览
====

.. c:macro:: VIDIOC_G_AUDOUT

``int ioctl(int fd, VIDIOC_G_AUDOUT, struct v4l2_audioout *argp)``

.. c:macro:: VIDIOC_S_AUDOUT

``int ioctl(int fd, VIDIOC_S_AUDOUT, const struct v4l2_audioout *argp)``

参数
====

``fd``
    由 :c:func:`open()` 返回的文件描述符
``argp``
    指向结构体 :c:type:`v4l2_audioout` 的指针
描述
====

为了查询当前音频输出，应用程序需要将一个 :c:type:`v4l2_audioout` 结构体中的 ``reserved`` 数组清零，并使用指向该结构体的指针调用 ``VIDIOC_G_AUDOUT`` ioctl。驱动程序会填充结构体的其余部分，或者在设备没有音频输入，或者没有与当前视频输出匹配的音频输入时返回 ``EINVAL`` 错误代码。
音频输出没有可写属性。尽管如此，为了选择当前音频输出，应用程序可以初始化一个 :c:type:`v4l2_audioout` 结构体的 ``index`` 字段和 ``reserved`` 数组（未来可能包含可写属性），并调用 ``VIDIOC_S_AUDOUT`` ioctl。驱动程序会切换到请求的输出，或者在索引超出范围时返回 ``EINVAL`` 错误代码。这是一个只写 ioctl，不会像 ``VIDIOC_G_AUDOUT`` 那样返回当前音频输出属性。
.. note::

   TV 卡上的连接器用于将接收到的音频信号回环到声卡，在这种情况下它们不是音频输出
.. c:type:: v4l2_audioout

.. tabularcolumns:: |p{4.4cm}|p{4.4cm}|p{8.5cm}|

.. flat-table:: struct v4l2_audioout
    :header-rows:  0
    :stub-columns: 0
    :widths:       1 1 2

    * - __u32
      - ``index``
      - 标识音频输出，由驱动程序或应用程序设置
    * - __u8
      - ``name``\ [32]
      - 音频输出的名称，一个以 NUL 终止的 ASCII 字符串，例如："Line Out"。此信息旨在供用户查看，最好是设备上的连接器标签
    * - __u32
      - ``capability``
      - 音频功能标志，目前尚未定义。驱动程序必须将此字段设为零
    * - __u32
      - ``mode``
      - 音频模式，目前尚未定义。驱动程序和应用程序（在 ``VIDIOC_S_AUDOUT`` 上）必须将此字段设为零
    * - __u32
      - ``reserved``\ [2]
      - 保留以备将来扩展。驱动程序和应用程序必须将数组设为零
返回值
============

成功时返回 0，错误时返回 -1，并且设置 ``errno`` 变量为适当的值。通用错误代码在
:ref:`通用错误代码 <gen-errors>` 章节中描述。

EINVAL
    没有音频输出与当前的视频输出匹配，或者所选音频输出的编号超出范围或不匹配。
