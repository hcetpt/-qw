.. SPDX 许可证标识符: GPL-2.0 或 GFDL-1.1-no-invariants-or-later
.. c:命名空间:: RC

.. _lirc_set_rec_carrier_range:

********************************
ioctl LIRC_SET_REC_CARRIER_RANGE
********************************

名称
====

LIRC_SET_REC_CARRIER_RANGE - 设置用于调制红外接收的载波下限

概要
====

.. c:宏:: LIRC_SET_REC_CARRIER_RANGE

``int ioctl(int fd, LIRC_SET_REC_CARRIER_RANGE, __u32 *frequency)``

参数
====

``fd``
    由 open() 返回的文件描述符
``frequency``
    调制 PWM 数据的载波频率，单位为 Hz

描述
====

此 ioctl 设置红外接收器将识别的载波频率上限。
.. 注意::

   要设置一个范围，请首先使用 :ref:`LIRC_SET_REC_CARRIER_RANGE <LIRC_SET_REC_CARRIER_RANGE>` 设置下限，然后稍后使用 :ref:`LIRC_SET_REC_CARRIER <LIRC_SET_REC_CARRIER>` 设置上限。

返回值
======

成功时返回 0，失败时返回 -1，并且会根据情况设置 ``errno`` 变量。通用错误代码在 :ref:`通用错误代码 <gen-errors>` 章节中描述。
