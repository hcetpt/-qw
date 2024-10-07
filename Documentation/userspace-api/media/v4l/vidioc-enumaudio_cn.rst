SPDX 许可声明标识符: GFDL-1.1-no-invariants-or-later
.. c:namespace:: V4L

.. _VIDIOC_ENUMAUDIO:

**********************
ioctl VIDIOC_ENUMAUDIO
**********************

名称
====

VIDIOC_ENUMAUDIO - 列举音频输入

概要
====

.. c:macro:: VIDIOC_ENUMAUDIO

``int ioctl(int fd, VIDIOC_ENUMAUDIO, struct v4l2_audio *argp)``

参数
====

``fd``
    由 :c:func:`open()` 返回的文件描述符
``argp``
    指向结构体 :c:type:`v4l2_audio` 的指针
描述
====

为了查询音频输入的属性，应用程序需要初始化结构体 :c:type:`v4l2_audio` 的 `index` 字段，并清零 `reserved` 数组，然后使用指向该结构体的指针调用 :ref:`VIDIOC_ENUMAUDIO` ioctl。驱动程序会填充结构体的其余部分，或者在索引超出范围时返回一个 `EINVAL` 错误码。为了枚举所有音频输入，应用程序应从索引为零开始，每次递增一，直到驱动程序返回 `EINVAL`。关于结构体 :c:type:`v4l2_audio` 的描述，请参阅 :ref:`VIDIOC_G_AUDIO <VIDIOC_G_AUDIO>`。
返回值
====

成功时返回 0，出错时返回 -1 并设置 `errno` 变量。通用错误码在 :ref:`Generic Error Codes <gen-errors>` 章节中描述。
EINVAL
    音频输入的编号超出范围
