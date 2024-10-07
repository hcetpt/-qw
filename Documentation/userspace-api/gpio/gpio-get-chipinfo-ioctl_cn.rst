.. SPDX 许可证标识符: GPL-2.0

.. _GPIO_GET_CHIPINFO_IOCTL:

***********************
GPIO_GET_CHIPINFO_IOCTL
***********************

名称
====

GPIO_GET_CHIPINFO_IOCTL - 获取特定芯片的公开信息

概要
========

.. c:macro:: GPIO_GET_CHIPINFO_IOCTL

``int ioctl(int chip_fd, GPIO_GET_CHIPINFO_IOCTL, struct gpiochip_info *info)``

参数
=========

``chip_fd``
    由 `open()` 返回的 GPIO 字符设备的文件描述符
``info``
    要填充的 :c:type:`chip_info<gpiochip_info>` 结构体

描述
===========

获取特定 GPIO 芯片的公开信息

返回值
============

成功时返回 0，并且 ``info`` 被填充为芯片信息；
错误时返回 -1，并且设置适当的 ``errno`` 变量。
常见的错误代码在 error-codes.rst 中描述。
