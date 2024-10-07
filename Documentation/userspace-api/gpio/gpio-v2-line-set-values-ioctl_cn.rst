.. SPDX-许可证标识符: GPL-2.0

.. _GPIO_V2_LINE_SET_VALUES_IOCTL:

*******************************
GPIO_V2_LINE_SET_VALUES_IOCTL
*******************************

名称
====

GPIO_V2_LINE_SET_VALUES_IOCTL - 设置请求的输出线的值

概要
====

.. c:macro:: GPIO_V2_LINE_SET_VALUES_IOCTL

``int ioctl(int req_fd, GPIO_V2_LINE_SET_VALUES_IOCTL, struct gpio_v2_line_values *values)``

参数
====

``req_fd``
    GPIO 字符设备的文件描述符，由 gpio-v2-get-line-ioctl.rst 中的 :c:type:`request.fd<gpio_v2_line_request>` 返回。
``values``
    要设置的 :c:type:`line_values<gpio_v2_line_values>`，其中 ``mask`` 用于指示要设置的请求线的子集，而 ``bits`` 用于指示新的值。

描述
====

设置请求的输出线的值。
所设置的值是逻辑值，表示线路是否处于活动或非活动状态。
``GPIO_V2_LINE_FLAG_ACTIVE_LOW`` 标志控制逻辑值（活动/非活动）与物理值（高/低）之间的映射。
如果未设置 ``GPIO_V2_LINE_FLAG_ACTIVE_LOW``，则活动为高电平，非活动为低电平。如果设置了 ``GPIO_V2_LINE_FLAG_ACTIVE_LOW``，则活动为低电平，非活动为高电平。
仅能设置输出线的值。
尝试设置输入线的值将导致错误（**EPERM**）。

返回值
======

成功时返回 0。
在出现错误 -1 时，`errno` 变量会被相应地设置
常见的错误代码在 error-codes.rst 中有描述
