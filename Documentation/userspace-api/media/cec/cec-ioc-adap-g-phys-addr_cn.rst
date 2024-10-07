SPDX 许可声明标识符: GFDL-1.1-no-invariants-or-later
.. c:namespace:: CEC

.. _CEC_ADAP_PHYS_ADDR:
.. _CEC_ADAP_G_PHYS_ADDR:
.. _CEC_ADAP_S_PHYS_ADDR:

***************************************************
ioctl CEC_ADAP_G_PHYS_ADDR 和 CEC_ADAP_S_PHYS_ADDR
***************************************************

名称
====

CEC_ADAP_G_PHYS_ADDR, CEC_ADAP_S_PHYS_ADDR — 获取或设置物理地址

概述
========

.. c:macro:: CEC_ADAP_G_PHYS_ADDR

``int ioctl(int fd, CEC_ADAP_G_PHYS_ADDR, __u16 *argp)``

.. c:macro:: CEC_ADAP_S_PHYS_ADDR

``int ioctl(int fd, CEC_ADAP_S_PHYS_ADDR, __u16 *argp)``

参数
=========

``fd``
    由 :c:func:`open()` 返回的文件描述符
``argp``
    指向 CEC 地址的指针

描述
===========

为了查询当前的物理地址，应用程序应调用 :ref:`ioctl CEC_ADAP_G_PHYS_ADDR <CEC_ADAP_G_PHYS_ADDR>` 并提供一个指向 __u16 的指针，驱动程序将在此存储物理地址。
为了设置新的物理地址，应用程序应在 __u16 中存储物理地址，并使用指向该整数的指针调用 :ref:`ioctl CEC_ADAP_S_PHYS_ADDR <CEC_ADAP_S_PHYS_ADDR>`。只有在设置了 ``CEC_CAP_PHYS_ADDR`` 时（否则将返回 ``ENOTTY`` 错误码），:ref:`ioctl CEC_ADAP_S_PHYS_ADDR <CEC_ADAP_S_PHYS_ADDR>` 才可用。:ref:`ioctl CEC_ADAP_S_PHYS_ADDR <CEC_ADAP_S_PHYS_ADDR>` 只能由处于发起者模式下的文件描述符调用（参见 :ref:`CEC_S_MODE`），否则将返回 ``EBUSY`` 错误码。
要清除现有的物理地址，请使用 ``CEC_PHYS_ADDR_INVALID``。适配器将进入未配置状态。
如果定义了逻辑地址类型（参见 :ref:`ioctl CEC_ADAP_S_LOG_ADDRS <CEC_ADAP_S_LOG_ADDRS>`），则此 ioctl 将会阻塞，直到所有请求的逻辑地址都被占用。如果文件描述符处于非阻塞模式，则不会等待逻辑地址被占用，而是直接返回 0。
当物理地址发生变化时，会发送 :ref:`CEC_EVENT_STATE_CHANGE <CEC-EVENT-STATE-CHANGE>` 事件。
物理地址是一个 16 位数字，每 4 位表示物理地址的一个数字 a.b.c.d，其中最高 4 位代表 'a'。CEC 根设备（通常是电视）的地址为 0.0.0.0。连接到电视输入端口的每个设备的地址为 a.0.0.0（其中 'a' ≥ 1），连接到这些设备上的其他设备地址为 a.b.0.0 等等。因此，支持最多五层深的拓扑结构。设备应当使用的物理地址存储在其 EDID 中。
例如，电视的每个 HDMI 输入的 EDID 都将有一个形式为 a.0.0.0 的不同物理地址，源设备会读取并将其作为自己的物理地址使用。
返回值
============

成功时返回 0，错误时返回 -1，并且设置 ``errno`` 变量为适当的值。通用错误代码在
:ref:`通用错误代码 <gen-errors>` 章节中描述。
:ref:`ioctl CEC_ADAP_S_PHYS_ADDR <CEC_ADAP_S_PHYS_ADDR>` 可能返回以下错误代码：

ENOTTY
    未设置 ``CEC_CAP_PHYS_ADDR`` 能力，因此此 ioctl 不受支持
EBUSY
    其他文件句柄处于独占跟随者或发起者模式，或者文件句柄处于 ``CEC_MODE_NO_INITIATOR`` 模式
EINVAL
    物理地址格式不正确
