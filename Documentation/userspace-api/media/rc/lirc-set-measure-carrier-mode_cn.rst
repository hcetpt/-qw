SPDX 许可证标识符：GPL-2.0 或 GFDL-1.1-no-invariants-or-later
c:命名空间:: RC

.. _lirc_set_measure_carrier_mode:

***********************************
ioctl LIRC_SET_MEASURE_CARRIER_MODE
***********************************

名称
====

LIRC_SET_MEASURE_CARRIER_MODE - 启用或禁用测量模式

概要
========

.. c:macro:: LIRC_SET_MEASURE_CARRIER_MODE

``int ioctl(int fd, LIRC_SET_MEASURE_CARRIER_MODE, __u32 *enable)``

参数
=========

``fd``
    由 open() 返回的文件描述符
``enable``
    enable = 1 表示启用测量模式，enable = 0 表示禁用测量模式
描述
===========

.. _lirc-mode2-frequency:

启用或禁用测量模式。如果启用，从下一个按键开始，驱动程序将发送 ``LIRC_MODE2_FREQUENCY`` 数据包。默认情况下，此功能应处于关闭状态。
返回值
============

成功时返回 0，失败时返回 -1 并设置 ``errno`` 变量。通用错误代码在“通用错误代码”章节中描述。
