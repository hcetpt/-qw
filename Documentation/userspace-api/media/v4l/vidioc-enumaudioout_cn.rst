SPDX 许可证标识符: GFDL-1.1-no-invariants-or-later
.. c:namespace:: V4L

.. _VIDIOC_ENUMAUDOUT:

**************************
ioctl VIDIOC_ENUMAUDOUT
**************************

名称
====

VIDIOC_ENUMAUDOUT —— 列出音频输出

概要
========

.. c:macro:: VIDIOC_ENUMAUDOUT

``int ioctl(int fd, VIDIOC_ENUMAUDOUT, struct v4l2_audioout *argp)``

参数
=========

``fd``
    由 :c:func:`open()` 返回的文件描述符
``argp``
    指向结构体 :c:type:`v4l2_audioout` 的指针
描述
===========

为了查询音频输出的属性，应用程序需要初始化结构体 :c:type:`v4l2_audioout` 的 ``index`` 字段，并清零 ``reserved`` 数组，然后使用指向该结构体的指针调用 ``VIDIOC_G_AUDOUT`` ioctl。驱动程序会填充结构体的其余部分，或者在索引超出范围时返回一个 ``EINVAL`` 错误码。为了枚举所有的音频输出，应用程序应从索引为零开始，逐个递增，直到驱动程序返回 ``EINVAL``。
.. note::

    电视卡上的用于将接收到的音频信号回环到声卡的连接器在这种意义上不是音频输出。
参见 :ref:`VIDIOC_G_AUDIOout <VIDIOC_G_AUDOUT>` 了解结构体 :c:type:`v4l2_audioout` 的描述。
返回值
============

成功时返回 0，失败时返回 -1 并且设置适当的 ``errno`` 变量。通用错误代码在 :ref:`Generic Error Codes <gen-errors>` 章节中描述。
EINVAL
    音频输出的编号超出范围
