SPDX 许可证标识符：GPL-2.0 或 GFDL-1.1-no-invariants-or-later
c:命名空间:: RC

.. _lirc_set_rec_carrier:

**************************
ioctl LIRC_SET_REC_CARRIER
**************************

名称
====

LIRC_SET_REC_CARRIER - 设置用于调制红外接收的载波频率

概要
====

.. c:宏:: LIRC_SET_REC_CARRIER

``int ioctl(int fd, LIRC_SET_REC_CARRIER, __u32 *frequency)``

参数
====

``fd``
    由 open() 返回的文件描述符
``frequency``
    调制 PWM 数据的载波频率，单位为 Hz
描述
====

设置用于调制红外 PWM 脉冲和空闲时间的接收载波频率
.. 注意::

   如果与 :ref:`LIRC_SET_REC_CARRIER_RANGE` 一起调用，此 ioctl 将设置设备识别的上限频率
返回值
====

成功时返回 0，失败时返回 -1，并且设置 `errno` 变量。通用错误代码在
:ref:`通用错误代码 <gen-errors>` 章节中进行了描述
