.. SPDX-License-Identifier: GPL-2.0

.. _GPIO_HANDLE_SET_LINE_VALUES_IOCTL:

*********************************
GPIO_HANDLE_SET_LINE_VALUES_IOCTL
*********************************

.. warning::
    此 ioctl 是 chardev_v1.rst 的一部分，并已被 gpio-v2-line-set-values-ioctl.rst 废弃。

名称
====

GPIO_HANDLE_SET_LINE_VALUES_IOCTL - 设置所有请求的输出线的值

概要
====

.. c:macro:: GPIO_HANDLE_SET_LINE_VALUES_IOCTL

``int ioctl(int handle_fd, GPIO_HANDLE_SET_LINE_VALUES_IOCTL, struct gpiohandle_data *values)``

参数
====

``handle_fd``
    GPIO 字符设备的文件描述符，由 gpio-get-linehandle-ioctl.rst 返回的 :c:type:`request.fd<gpiohandle_request>` 中获得。
``values``
    要设置的 :c:type:`line_values<gpiohandle_data>`。

描述
====

设置所有请求的输出线的值。
设置的值是逻辑值，表示线路是否处于活动状态或非活动状态。
``GPIOHANDLE_REQUEST_ACTIVE_LOW`` 标志控制逻辑值（活动/非活动）与物理值（高/低）之间的映射。
如果未设置 ``GPIOHANDLE_REQUEST_ACTIVE_LOW``，则活动为高电平，非活动为低电平。如果设置了 ``GPIOHANDLE_REQUEST_ACTIVE_LOW``，则活动为低电平，非活动为高电平。
仅能设置输出线的值。
尝试设置输入线的值将导致错误（**EPERM**）。
返回值
============

成功时返回 0
出错时返回 -1，并且设置 ``errno`` 变量为适当的值
常见的错误代码在 error-codes.rst 中有描述
