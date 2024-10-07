SPDX 许可声明标识符: GFDL-1.1-no-invariants-or-later
C 命名空间: MC

.. _media_ioc_device_info:

***************************
ioctl MEDIA_IOC_DEVICE_INFO
***************************

名称
====

MEDIA_IOC_DEVICE_INFO — 查询设备信息

概要
========

.. c:macro:: MEDIA_IOC_DEVICE_INFO

``int ioctl(int fd, MEDIA_IOC_DEVICE_INFO, struct media_device_info *argp)``

参数
=========

``fd``
    由 :c:func:`open()` 返回的文件描述符
``argp``
    指向结构体 :c:type:`media_device_info` 的指针

描述
===========

所有媒体设备都必须支持 ``MEDIA_IOC_DEVICE_INFO`` ioctl。为了查询设备信息，应用程序需要通过指向结构体 :c:type:`media_device_info` 的指针调用 ioctl。驱动程序会填充该结构体并将信息返回给应用程序。ioctl 不应失败。

.. c:type:: media_device_info

.. tabularcolumns:: |p{4.4cm}|p{4.4cm}|p{8.5cm}|

.. flat-table:: 结构体 media_device_info
    :header-rows:  0
    :stub-columns: 0
    :widths:       1 1 2

    *  -  char
       -  ``driver``\ [16]
       -  实现媒体 API 的驱动名称，作为以 NUL 结尾的 ASCII 字符串。驱动版本存储在 ``driver_version`` 字段中
驱动特定的应用程序可以使用此信息来验证驱动的身份。这也有助于解决已知问题，或在错误报告中识别驱动程序。
*  -  char
       -  ``model``\ [32]
       -  设备型号名称，作为以 NUL 结尾的 UTF-8 字符串。设备版本存储在 ``device_version`` 字段中，并且不会附加到型号名称后面。
*  -  char
       -  ``serial``\ [40]
       -  序列号，作为以 NUL 结尾的 ASCII 字符串
*  -  char
       -  ``bus_info``\ [32]
       -  设备在系统中的位置，作为以 NUL 结尾的 ASCII 字符串。这包括总线类型名称（PCI、USB 等）和特定于总线的标识符
*  -  __u32
       -  ``media_version``
       -  媒体 API 版本，使用 ``KERNEL_VERSION()`` 宏格式化
*  -  __u32
       -  ``hw_revision``
       -  硬件设备修订版，使用驱动特定的格式
*  -  `__u32`
       -  `driver_version`
       -  媒体设备驱动程序版本，使用 `KERNEL_VERSION()` 宏格式化。与 `driver` 字段一起，这可以标识一个特定的驱动程序。
*  -  `__u32`
       -  `reserved`[31]
       -  为将来扩展保留。驱动程序和应用程序必须将此数组设置为零。

`serial` 和 `bus_info` 字段可用于区分其他方面相同的硬件的不同实例。当提供序列号时，它具有优先级，并且可以假定是唯一的。

如果序列号是一个空字符串，则可以使用 `bus_info` 字段代替。`bus_info` 字段保证是唯一的，但在重启或设备拔插后可能会发生变化。

返回值
======

成功时返回 0，失败时返回 -1 并且设置 `errno` 变量以表示适当的错误码。通用错误码在“<gen-errors> 通用错误码”章节中描述。
