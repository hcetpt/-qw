SPDX 许可证标识符: GFDL-1.1-no-invariants-or-later
c:命名空间:: V4L

.. _VIDIOC_G_PRIORITY:

******************************************
ioctl VIDIOC_G_PRIORITY, VIDIOC_S_PRIORITY
******************************************

名称
====

VIDIOC_G_PRIORITY - VIDIOC_S_PRIORITY - 查询或请求与文件描述符相关的访问优先级

概要
========

.. c:宏:: VIDIOC_G_PRIORITY

``int ioctl(int fd, VIDIOC_G_PRIORITY, enum v4l2_priority *argp)``

.. c:宏:: VIDIOC_S_PRIORITY

``int ioctl(int fd, VIDIOC_S_PRIORITY, const enum v4l2_priority *argp)``

参数
=========

``fd``
    由 :c:func:`open()` 返回的文件描述符
``argp``
    指向一个枚举类型 :c:type:`v4l2_priority` 的指针
描述
===========

为了查询当前的访问优先级，应用程序应调用 :ref:`VIDIOC_G_PRIORITY <VIDIOC_G_PRIORITY>` ioctl，并提供一个指向枚举类型 v4l2_priority 变量的指针，驱动程序将在此变量中存储当前优先级。
为了请求一个访问优先级，应用程序应在枚举类型 v4l2_priority 变量中存储所需的优先级，并通过提供该变量的指针来调用 :ref:`VIDIOC_S_PRIORITY <VIDIOC_G_PRIORITY>` ioctl。

.. c:type:: v4l2_priority

.. tabularcolumns:: |p{6.6cm}|p{2.2cm}|p{8.5cm}|

.. flat-table:: 枚举 v4l2_priority
    :header-rows:  0
    :stub-columns: 0
    :widths:       3 1 4

    * - ``V4L2_PRIORITY_UNSET``
      - 0
      -
    * - ``V4L2_PRIORITY_BACKGROUND``
      - 1
      - 最低优先级，通常是后台运行的应用程序，例如监控 VBI 传输。如果多个应用程序希望以这个优先级读取设备，则需要在用户空间中运行代理应用程序
    * - ``V4L2_PRIORITY_INTERACTIVE``
      - 2
      -
    * - ``V4L2_PRIORITY_DEFAULT``
      - 2
      - 中等优先级，通常是由用户启动并交互控制的应用程序。例如电视观众、Teletext 浏览器，或者仅仅是用于更改频道或视频控制的“面板”应用程序。除非应用程序请求其他优先级，否则这是默认优先级
    * - ``V4L2_PRIORITY_RECORD``
      - 3
      - 最高优先级。只有一个文件描述符可以具有此优先级，它阻止任何其他文件描述符更改设备属性。通常用于不能中断的应用程序，如视频录制

返回值
============

成功时返回 0，失败时返回 -1 并设置 ``errno`` 变量为适当的错误码。通用错误代码在 :ref:`通用错误代码 <gen-errors>` 章节中有描述

EINVAL
    请求的优先级值无效
EBUSY
    其他应用程序已经请求了更高的优先级
当然，请提供你需要翻译的文本。
