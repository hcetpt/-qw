.. SPDX 许可证标识符: GPL-2.0

.. _GPIO_V2_GET_LINEINFO_IOCTL:

**************************
GPIO_V2_GET_LINEINFO_IOCTL
**************************

名称
====

GPIO_V2_GET_LINEINFO_IOCTL - 获取一条线路的公开信息

概要
========

.. c:macro:: GPIO_V2_GET_LINEINFO_IOCTL

``int ioctl(int chip_fd, GPIO_V2_GET_LINEINFO_IOCTL, struct gpio_v2_line_info *info)``

参数
=========

``chip_fd``
    由 `open()` 返回的 GPIO 字符设备文件描述符
``info``
    要填充的 :c:type:`line_info<gpio_v2_line_info>`，其中 `offset` 字段设置为指示要收集的线路

描述
===========

获取一条线路的公开信息
这些信息无论线路是否在使用中都是可用的
.. note::
    线路信息不包括线路值
要访问线路值，必须使用 gpio-v2-get-line-ioctl.rst 请求线路
返回值
============

成功时返回 0，并且 `info` 被填充了芯片信息
失败时返回 -1，并且 `errno` 变量被适当地设置
常见的错误代码在 error-codes.rst 中描述
当然，请提供你需要翻译的文本。
