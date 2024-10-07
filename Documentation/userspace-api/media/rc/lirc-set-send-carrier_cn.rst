SPDX 许可证标识符：GPL-2.0 或 GFDL-1.1-no-invariants-or-later
c:命名空间:: RC

.. _lirc_set_send_carrier:

***************************
ioctl LIRC_SET_SEND_CARRIER
***************************

名称
====

LIRC_SET_SEND_CARRIER - 设置用于调制红外发射的载波频率

概要
====

.. c:宏:: LIRC_SET_SEND_CARRIER

``int ioctl(int fd, LIRC_SET_SEND_CARRIER, __u32 *frequency)``

参数
====

``fd``
    由 open() 返回的文件描述符
``frequency``
    载波的调制频率，单位为 Hz
描述
====

设置用于调制红外 PWM 脉冲和空闲时间的载波频率
返回值
====

成功时返回 0，失败时返回 -1 并且设置相应的 ``errno`` 变量。通用错误代码在“通用错误代码”章节中进行了描述。
