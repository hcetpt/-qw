SPDX 许可证标识符: GFDL-1.1-no-invariants-or-later
c:命名空间:: V4L

.. _VIDIOC_G_CTRL:

**********************************
ioctl VIDIOC_G_CTRL, VIDIOC_S_CTRL
**********************************

名称
====

VIDIOC_G_CTRL - VIDIOC_S_CTRL - 获取或设置控制的值

概述
========

.. c:macro:: VIDIOC_G_CTRL

``int ioctl(int fd, VIDIOC_G_CTRL, struct v4l2_control *argp)``

.. c:macro:: VIDIOC_S_CTRL

``int ioctl(int fd, VIDIOC_S_CTRL, struct v4l2_control *argp)``

参数
=========

``fd``
    由 :c:func:`open()` 返回的文件描述符
``argp``
    指向结构体 :c:type:`v4l2_control` 的指针
描述
===========

为了获取某个控制项的当前值，应用程序需要初始化一个结构体 :c:type:`v4l2_control` 的 ``id`` 字段，并使用指向该结构体的指针调用 :ref:`VIDIOC_G_CTRL <VIDIOC_G_CTRL>` ioctl。为了更改某个控制项的值，应用程序需要初始化结构体 :c:type:`v4l2_control` 的 ``id`` 和 ``value`` 字段，并调用 :ref:`VIDIOC_S_CTRL <VIDIOC_G_CTRL>` ioctl。当 ``id`` 无效时，驱动程序会返回 ``EINVAL`` 错误代码。当 ``value`` 超出范围时，驱动程序可以选择取最近的有效值或返回 ``ERANGE`` 错误代码，具体取决于哪种情况更合适。然而，:ref:`VIDIOC_S_CTRL <VIDIOC_G_CTRL>` 是一个只写 ioctl，不会返回实际的新值。如果 ``value`` 对于该控制项不合适（例如，如果它引用了菜单控制中不受支持的菜单索引），则也会返回 ``EINVAL`` 错误代码。

这些 ioctl 只能与用户控制项一起工作。对于其他类型的控制类，必须使用 :ref:`VIDIOC_G_EXT_CTRLS <VIDIOC_G_EXT_CTRLS>`、:ref:`VIDIOC_S_EXT_CTRLS <VIDIOC_G_EXT_CTRLS>` 或 :ref:`VIDIOC_TRY_EXT_CTRLS <VIDIOC_G_EXT_CTRLS>`。

.. c:type:: v4l2_control

.. tabularcolumns:: |p{4.4cm}|p{4.4cm}|p{8.5cm}|

.. flat-table:: struct v4l2_control
    :header-rows:  0
    :stub-columns: 0
    :widths:       1 1 2

    * - __u32
      - ``id``
      - 标识控制项，由应用程序设置
    * - __s32
      - ``value``
      - 新值或当前值
返回值
============

成功时返回 0，失败时返回 -1 并根据情况设置 ``errno`` 变量。通用错误代码在 :ref:`Generic Error Codes <gen-errors>` 章节中有描述。

EINVAL
    结构体 :c:type:`v4l2_control` 的 ``id`` 无效或 ``value`` 对给定的控制项不合适（例如，选择了驱动程序根据 :ref:`VIDIOC_QUERYMENU <VIDIOC_QUERYCTRL>` 不支持的菜单项）
ERANGE
    结构体 :c:type:`v4l2_control` 的 ``value`` 超出了范围

EBUSY
    该控制暂时不可更改，可能是因为其他应用程序接管了此控制所属的设备功能

EACCES
    尝试设置一个只读控制或获取一个写入专用控制
或者尝试设置一个非活动控制，但驱动程序无法缓存新值直到该控制再次激活
