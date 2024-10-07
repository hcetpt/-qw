SPDX 许可证标识符：GPL-2.0 或 GFDL-1.1-no-invariants-or-later
c:命名空间:: RC

.. _lirc_set_wideband_receiver:

********************************
ioctl LIRC_SET_WIDEBAND_RECEIVER
********************************

名称
====

LIRC_SET_WIDEBAND_RECEIVER - 启用宽带接收器

概要
========

.. c:宏:: LIRC_SET_WIDEBAND_RECEIVER

``int ioctl(int fd, LIRC_SET_WIDEBAND_RECEIVER, __u32 *enable)``

参数
=========

``fd``
    由 open() 返回的文件描述符
``enable``
    enable = 1 表示启用宽带接收器，enable = 0 表示禁用宽带接收器
描述
===========

某些接收器配备了特殊的宽带接收器，旨在用于学习现有遥控器的输出。此 ioctl 允许启用或禁用该功能。
对于那些本身具有窄带接收器从而无法与某些遥控器一起使用的接收器，这可能会有所帮助。宽带接收器可能也会更精确。然而，它的缺点通常是接收范围减少。
.. 注意::

    如果启用了载波报告，则宽带接收器可能会被隐式启用。在这种情况下，一旦您禁用载波报告，它就会被禁用。在载波报告处于活动状态时尝试禁用宽带接收器将不起作用
返回值
============

成功时返回 0，失败时返回 -1 并设置适当的 ``errno`` 变量。通用错误代码在“通用错误代码”章节中描述。
