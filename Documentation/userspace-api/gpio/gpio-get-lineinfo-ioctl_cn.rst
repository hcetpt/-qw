.. SPDX-License-Identifier: GPL-2.0

.. _GPIO_GET_LINEINFO_IOCTL:

***********************
GPIO_GET_LINEINFO_IOCTL
***********************

.. warning::
    此 ioctl 是 chardev_v1.rst 的一部分，并已被 gpio-v2-get-lineinfo-ioctl.rst 废弃。

名称
====
GPIO_GET_LINEINFO_IOCTL - 获取某条线的公开信息

概要
====

.. c:macro:: GPIO_GET_LINEINFO_IOCTL

``int ioctl(int chip_fd, GPIO_GET_LINEINFO_IOCTL, struct gpioline_info *info)``

参数
=========

``chip_fd``
    由 `open()` 返回的 GPIO 字符设备的文件描述符。
``info``
    要填充的 :c:type:`line_info<gpioline_info>`，其中 ``offset`` 字段设置为指示要收集的线。

描述
===========

获取某条线的公开信息。
此信息与该线是否正在使用无关。
.. note::
    线信息不包括线值。
必须使用 gpio-get-linehandle-ioctl.rst 或 gpio-get-lineevent-ioctl.rst 请求该线才能访问其值。

返回值
============

成功时返回 0 并且 ``info`` 被芯片信息填充；
失败时返回 -1 并且适当设置 ``errno`` 变量。
常见的错误代码在 error-codes.rst 中有描述。
