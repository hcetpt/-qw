SPDX 许可声明标识符：GPL-2.0 或 GFDL-1.1-no-invariants-or-later
C 命名空间：RC

.. _lirc_get_send_mode:
.. _lirc_set_send_mode:

************************************************
ioctl 命令 LIRC_GET_SEND_MODE 和 LIRC_SET_SEND_MODE
************************************************

名称
====

LIRC_GET_SEND_MODE/LIRC_SET_SEND_MODE - 获取/设置当前的传输模式

概述
====

.. c:macro:: LIRC_GET_SEND_MODE

``int ioctl(int fd, LIRC_GET_SEND_MODE, __u32 *mode)``

.. c:macro:: LIRC_SET_SEND_MODE

``int ioctl(int fd, LIRC_SET_SEND_MODE, __u32 *mode)``

参数
====

``fd``
    由 open() 返回的文件描述符
``mode``
    用于传输的模式

描述
====

获取/设置当前的传输模式。
对于红外发送，仅支持 :ref:`LIRC_MODE_PULSE <lirc-mode-pulse>` 和 :ref:`LIRC_MODE_SCANCODE <lirc-mode-scancode>`，具体取决于驱动程序。使用 :ref:`lirc_get_features` 来了解驱动程序支持哪些模式。

返回值
======

.. tabularcolumns:: |p{2.5cm}|p{15.0cm}|

.. flat-table::
    :header-rows:  0
    :stub-columns: 0

    -  .. row 1

       -  ``ENODEV``

       -  设备不可用
    -  .. row 2

       -  ``ENOTTY``

       -  设备不支持传输
    -  .. row 3

       -  ``EINVAL``

       -  无效的模式或此设备不支持的模式
