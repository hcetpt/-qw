.. 许可证标识符：GPL-2.0 或 GFDL-1.1-no-invariants-or-later
.. c:命名空间:: RC

.. _lirc_set_transmitter_mask:

*******************************
ioctl LIRC_SET_TRANSMITTER_MASK
*******************************

名称
====

LIRC_SET_TRANSMITTER_MASK - 在指定的发射器上启用发送代码

概要
====

.. c:宏:: LIRC_SET_TRANSMITTER_MASK

``int ioctl(int fd, LIRC_SET_TRANSMITTER_MASK, __u32 *mask)``

参数
=====

``fd``
    由 open() 返回的文件描述符
``mask``
    要启用发送的通道掩码。通道 0 是最低有效位
描述
====

一些红外线（IR）发射设备有多个输出通道，在这种情况下，通过 :ref:`LIRC_GET_FEATURES` 返回 :ref:`LIRC_CAN_SET_TRANSMITTER_MASK <LIRC-CAN-SET-TRANSMITTER-MASK>`。
此 ioctl 设置哪些通道将发送红外代码。此 ioctl 启用给定的发射器集合。第一个发射器由最低有效位编码，依此类推。
当提供了一个无效的位掩码时，即设置了某个位，而设备并没有那么多发射器，则此 ioctl 返回可用的发射器数量，并且不执行其他操作。
返回值
======

成功时返回 0，失败时返回 -1 并设置相应的 ``errno`` 变量。通用错误代码在 :ref:`Generic Error Codes <gen-errors>` 章节中描述。
