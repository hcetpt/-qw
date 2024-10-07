SPDX 许可证标识符：GPL-2.0 或 GFDL-1.1-no-invariants-or-later
c:命名空间:: RC

.. _lirc_set_rec_timeout:
.. _lirc_get_rec_timeout:

***************************************************
ioctl LIRC_GET_REC_TIMEOUT 和 LIRC_SET_REC_TIMEOUT
***************************************************

名称
====

LIRC_GET_REC_TIMEOUT/LIRC_SET_REC_TIMEOUT — 获取/设置 IR 休眠超时的整数值

概要
====

.. c:macro:: LIRC_GET_REC_TIMEOUT

``int ioctl(int fd, LIRC_GET_REC_TIMEOUT, __u32 *timeout)``

.. c:macro:: LIRC_SET_REC_TIMEOUT

``int ioctl(int fd, LIRC_SET_REC_TIMEOUT, __u32 *timeout)``

参数
====

``fd``
    由 open() 返回的文件描述符
``timeout``
    超时时间，以微秒为单位

描述
====

获取和设置 IR 休眠超时的整数值。
如果硬件支持，将其设置为 0 将禁用所有硬件超时，并且数据应尽快报告。如果无法设置确切值，则应设置下一个可能的比给定值更大的值。
.. note::

   支持的超时范围由 :ref:`LIRC_GET_MIN_TIMEOUT` 给出。

返回值
====

成功时返回 0，失败时返回 -1 并将 ``errno`` 变量设置为适当的错误码。通用错误码在 :ref:`Generic Error Codes <gen-errors>` 章节中描述。
