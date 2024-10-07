SPDX 许可证标识符: GFDL-1.1-no-invariants-or-later
.. c:namespace:: V4L

.. _VIDIOC_G_AUDIO:

************************************
ioctl VIDIOC_G_AUDIO, VIDIOC_S_AUDIO
************************************

名称
====

VIDIOC_G_AUDIO - VIDIOC_S_AUDIO - 查询或选择当前音频输入及其属性

概述
========

.. c:macro:: VIDIOC_G_AUDIO

``int ioctl(int fd, VIDIOC_G_AUDIO, struct v4l2_audio *argp)``

.. c:macro:: VIDIOC_S_AUDIO

``int ioctl(int fd, VIDIOC_S_AUDIO, const struct v4l2_audio *argp)``

参数
=========

``fd``
    由 :c:func:`open()` 返回的文件描述符
``argp``
    指向结构体 :c:type:`v4l2_audio` 的指针
描述
===========

为了查询当前音频输入，应用程序需要将结构体 :c:type:`v4l2_audio` 中的 ``reserved`` 数组清零，并使用指向该结构体的指针调用 :ref:`VIDIOC_G_AUDIO <VIDIOC_G_AUDIO>` ioctl。如果设备没有音频输入或者没有与当前视频输入组合的音频输入时，驱动程序会填充其余部分或返回一个 ``EINVAL`` 错误代码。

要选择当前音频输入并更改音频模式，应用程序需要初始化结构体 :c:type:`v4l2_audio` 中的 ``index`` 和 ``mode`` 字段以及 ``reserved`` 数组，并调用 :ref:`VIDIOC_S_AUDIO <VIDIOC_G_AUDIO>` ioctl。如果请求无法满足，驱动程序可能会切换到不同的音频模式。但是，这是一个只写 ioctl，不会返回实际的新音频模式。
.. tabularcolumns:: |p{4.4cm}|p{4.4cm}|p{8.5cm}|

.. c:type:: v4l2_audio

.. flat-table:: 结构体 v4l2_audio
    :header-rows:  0
    :stub-columns: 0
    :widths:       1 1 2

    * - __u32
      - ``index``
      - 标识音频输入，由驱动程序或应用程序设置
* - __u8
      - ``name``\ [32]
      - 音频输入的名称，为 NUL 终止的 ASCII 字符串，例如："Line In"。此信息旨在供用户查看，最好是设备上的连接器标签
* - __u32
      - ``capability``
      - 音频功能标志，参见 :ref:`audio-capability`
* - __u32
      - ``mode``
      - 由驱动程序和应用程序（在 :ref:`VIDIOC_S_AUDIO <VIDIOC_G_AUDIO>` ioctl 上）设置的音频模式标志，参见 :ref:`audio-mode`
* - __u32
      - ``reserved``\ [2]
      - 保留用于未来扩展。驱动程序和应用程序必须将数组清零
.. tabularcolumns:: |p{6.6cm}|p{2.2cm}|p{8.5cm}|

.. _audio-capability:

.. flat-table:: 音频功能标志
    :header-rows:  0
    :stub-columns: 0
    :widths:       3 1 4

    * - ``V4L2_AUDCAP_STEREO``
      - 0x00001
      - 这是一个立体声输入。该标志旨在自动禁用立体声录制等操作，当信号始终是单声道时
API不提供检测是否接收立体声的方法，除非音频输入属于调谐器。

* - ``V4L2_AUDCAP_AVL``
  - 0x00002
  - 支持自动音量电平模式

.. tabularcolumns:: |p{6.6cm}|p{2.2cm}|p{8.5cm}|

.. _audio-mode:

.. flat-table:: 音频模式标志
    :header-rows:  0
    :stub-columns: 0
    :widths:       3 1 4

    * - ``V4L2_AUDMODE_AVL``
      - 0x00001
      - AVL 模式开启

返回值
======

成功时返回0，错误时返回-1，并且设置 ``errno`` 变量。通用错误代码在
:ref:`通用错误代码 <gen-errors>` 章节中描述。

EINVAL
    没有音频输入与当前视频输入组合，或者选定的音频输入编号超出范围或无法组合。
