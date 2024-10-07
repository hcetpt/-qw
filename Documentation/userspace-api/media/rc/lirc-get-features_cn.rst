SPDX 许可证标识符：GPL-2.0 或 GFDL-1.1-no-invariants-or-later  
c:命名空间:: RC

.. _lirc_get_features:

**************************
ioctl LIRC_GET_FEATURES
**************************

名称
====

LIRC_GET_FEATURES — 获取底层硬件设备的功能

概览
========

.. c:宏:: LIRC_GET_FEATURES

``int ioctl(int fd, LIRC_GET_FEATURES, __u32 *features)``

参数
=========

``fd``
    由 open() 返回的文件描述符
``features``
    包含 LIRC 功能的位掩码

描述
===========

获取底层硬件设备的功能。如果驱动程序没有宣布支持某些功能，则调用相应的 ioctl 是未定义的行为。

LIRC 功能
=============

.. _LIRC-CAN-REC-RAW:

``LIRC_CAN_REC_RAW``

    未使用。保留以避免破坏用户 API。

.. _LIRC-CAN-REC-PULSE:

``LIRC_CAN_REC_PULSE``

    未使用。保留以避免破坏用户 API。
:ref:`LIRC_MODE_PULSE <lirc-mode-pulse>` 仅可用于传输。

.. _LIRC-CAN-REC-MODE2:

``LIRC_CAN_REC_MODE2``

    这是一个用于接收的原始红外驱动程序。这意味着使用了 :ref:`LIRC_MODE_MODE2 <lirc-mode-MODE2>`。这也意味着只要内核足够新，:ref:`LIRC_MODE_SCANCODE <lirc-mode-SCANCODE>` 同样被支持。使用 :ref:`lirc_set_rec_mode` 切换模式。

.. _LIRC-CAN-REC-LIRCCODE:

``LIRC_CAN_REC_LIRCCODE``

    未使用。保留以避免破坏用户 API。

.. _LIRC-CAN-REC-SCANCODE:

``LIRC_CAN_REC_SCANCODE``

    这是一个用于接收的扫描码驱动程序。这意味着使用了 :ref:`LIRC_MODE_SCANCODE <lirc-mode-SCANCODE>`。

.. _LIRC-CAN-SET-SEND-CARRIER:

``LIRC_CAN_SET_SEND_CARRIER``

    驱动程序支持通过 :ref:`ioctl LIRC_SET_SEND_CARRIER <LIRC_SET_SEND_CARRIER>` 更改调制频率。
.. _LIRC-CAN-SET-SEND-DUTY-CYCLE:

``LIRC_CAN_SET_SEND_DUTY_CYCLE``

    该驱动程序支持使用 :ref:`ioctl LIRC_SET_SEND_DUTY_CYCLE <LIRC_SET_SEND_DUTY_CYCLE>` 更改占空比。
.. _LIRC-CAN-SET-TRANSMITTER-MASK:

``LIRC_CAN_SET_TRANSMITTER_MASK``

    该驱动程序支持使用 :ref:`ioctl LIRC_SET_TRANSMITTER_MASK <LIRC_SET_TRANSMITTER_MASK>` 更改活动的发射器。
.. _LIRC-CAN-SET-REC-CARRIER:

``LIRC_CAN_SET_REC_CARRIER``

    该驱动程序支持使用 :ref:`ioctl LIRC_SET_REC_CARRIER <LIRC_SET_REC_CARRIER>` 设置接收载波频率。
.. _LIRC-CAN-SET-REC-CARRIER-RANGE:

``LIRC_CAN_SET_REC_CARRIER_RANGE``

    该驱动程序支持 :ref:`ioctl LIRC_SET_REC_CARRIER_RANGE <LIRC_SET_REC_CARRIER_RANGE>`。
.. _LIRC-CAN-GET-REC-RESOLUTION:

``LIRC_CAN_GET_REC_RESOLUTION``

    该驱动程序支持 :ref:`ioctl LIRC_GET_REC_RESOLUTION <LIRC_GET_REC_RESOLUTION>`。
.. _LIRC-CAN-SET-REC-TIMEOUT:

``LIRC_CAN_SET_REC_TIMEOUT``

    该驱动程序支持 :ref:`ioctl LIRC_SET_REC_TIMEOUT <LIRC_SET_REC_TIMEOUT>`。
.. _LIRC-CAN-MEASURE-CARRIER:

``LIRC_CAN_MEASURE_CARRIER``

    该驱动程序支持使用 :ref:`ioctl LIRC_SET_MEASURE_CARRIER_MODE <LIRC_SET_MEASURE_CARRIER_MODE>` 测量调制频率。
.. _LIRC-CAN-USE-WIDEBAND-RECEIVER:

``LIRC_CAN_USE_WIDEBAND_RECEIVER``

    该驱动程序支持使用 :ref:`ioctl LIRC_SET_WIDEBAND_RECEIVER <LIRC_SET_WIDEBAND_RECEIVER>` 的学习模式。
.. _LIRC-CAN-SEND-RAW:

``LIRC_CAN_SEND_RAW``

    未使用。保留只是为了避免破坏用户API。
.. _LIRC-CAN-SEND-PULSE:

``LIRC_CAN_SEND_PULSE``

    该驱动程序支持使用 :ref:`LIRC_MODE_PULSE <lirc-mode-pulse>` 发送（也称为红外爆破或红外发送）。这意味着只要内核足够新， :ref:`LIRC_MODE_SCANCODE <lirc-mode-SCANCODE>` 也支持发送。使用 :ref:`lirc_set_send_mode` 切换模式。
``LIRC_CAN_SEND_MODE2``

    未使用。仅为了不破坏用户API而保留。
:ref:`LIRC_MODE_MODE2 <lirc-mode-mode2>` 仅可用于接收。

.. _LIRC-CAN-SEND-LIRCCODE:

``LIRC_CAN_SEND_LIRCCODE``

    未使用。仅为了不破坏用户API而保留。

返回值
======

成功时返回0，失败时返回-1，并且设置 ``errno`` 变量为适当的错误码。通用错误码在
:ref:`通用错误码 <gen-errors>` 章节中有描述。
