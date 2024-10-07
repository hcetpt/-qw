.. SPDX 许可证标识符: GFDL-1.1-no-invariants-or-later
.. c:namespace:: DTV.fe

.. _FE_SET_TONE:

*****************
ioctl FE_SET_TONE
*****************

名称
====

FE_SET_TONE - 设置或重置连续 22kHz 音调的生成

概述
========

.. c:macro:: FE_SET_TONE

``int ioctl(int fd, FE_SET_TONE, enum fe_sec_tone_mode tone)``

参数
=========

``fd``
    由 :c:func:`open()` 返回的文件描述符
``tone``
    在 :c:type:`fe_sec_tone_mode` 中描述的一个整数枚举值

描述
===========

此 ioctl 用于设置连续 22kHz 音调的生成。
此调用需要读写权限。
通常，卫星天线子系统要求数字电视设备发送一个 22kHz 的音调，以便在某些双频 LNB 上选择高低频段。它还用于向 DiSEqC 设备发送信号，但这是通过使用 DiSEqC 的 ioctl 来完成的。
.. 注意:: 如果有多个设备连接到同一根天线上，设置音调可能会干扰其他设备，因为它们可能会失去选择频段的能力。因此，建议应用程序在设备不使用时切换到 SEC_TONE_OFF。
返回值
============

成功时返回 0
出错时返回 -1，并且设置适当的 ``errno`` 变量
通用错误代码在“通用错误代码”章节中描述 (:ref:`Generic Error Codes <gen-errors>`)
