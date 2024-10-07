SPDX 许可证标识符：GPL-2.0 或 GFDL-1.1-no-invariants-or-later
C 命名空间：RC

.. _lirc_get_rec_mode:
.. _lirc_set_rec_mode:

**********************************************
ioctl 命令 LIRC_GET_REC_MODE 和 LIRC_SET_REC_MODE
**********************************************

名称
====

LIRC_GET_REC_MODE/LIRC_SET_REC_MODE — 获取/设置当前接收模式

概述
====

.. c:macro:: LIRC_GET_REC_MODE

``int ioctl(int fd, LIRC_GET_REC_MODE, __u32 *mode)``

.. c:macro:: LIRC_SET_REC_MODE

``int ioctl(int fd, LIRC_SET_REC_MODE, __u32 *mode)``

参数
====

``fd``
    由 open() 返回的文件描述符
``mode``
    用于接收的模式

描述
====

获取和设置当前的接收模式。仅支持 :ref:`LIRC_MODE_MODE2 <lirc-mode-mode2>` 和 :ref:`LIRC_MODE_SCANCODE <lirc-mode-scancode>`。
使用 :ref:`lirc_get_features` 来查询驱动程序支持哪些模式。

返回值
====

.. tabularcolumns:: |p{2.5cm}|p{15.0cm}|

.. flat-table::
    :header-rows:  0
    :stub-columns: 0

    -  .. row 1

       -  ``ENODEV``

       -  设备不可用
-  .. row 2

       -  ``ENOTTY``

       -  设备不支持接收
-  .. row 3

       -  ``EINVAL``

       -  模式无效或对于此设备无效
