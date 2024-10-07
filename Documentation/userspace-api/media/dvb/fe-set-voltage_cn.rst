.. 许可证标识符: GFDL-1.1-no-invariants-or-later
.. c:命名空间:: DTV.fe

.. _FE_SET_VOLTAGE:

********************
ioctl FE_SET_VOLTAGE
********************

名称
====

FE_SET_VOLTAGE - 允许设置发送到天线子系统的直流电平

概要
========

.. c:宏:: FE_SET_VOLTAGE

``int ioctl(int fd, FE_SET_VOLTAGE, enum fe_sec_voltage voltage)``

参数
=========

``fd``
    由 :c:func:`open()` 返回的文件描述符
``voltage``
    一个整型枚举值，具体描述见 :c:type:`fe_sec_voltage`

描述
===========

此 ioctl 操作允许设置通过天线电缆发送至 13V、18V 或关闭的直流电压。
通常，卫星天线子系统需要数字电视设备发送直流电压以给低噪声块下变频器（LNBf）供电。根据 LNBf 的类型，可以通过电压水平来控制极化或 LNBf 的中频（IF）。其他设备（例如，实现 DISEqC 和多点 LNBf 的设备）则不需要控制电压水平，只要提供 13V 或 18V 以启动 LNBf 即可。
.. 注意:: 如果有多个设备连接到同一根天线上，设置电压可能会干扰其他设备，因为它们可能会失去设置极化或中频的能力。因此，在设备不使用时，建议将电压设置为 SEC_VOLTAGE_OFF。

返回值
============

成功时返回 0
出错时返回 -1，并且设置 ``errno`` 变量为适当的错误代码
通用错误代码在 :ref:`通用错误代码 <gen-errors>` 章节中有描述。
