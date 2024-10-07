.. SPDX-License-Identifier: GPL-2.0

.. _GPIO_V2_LINE_GET_VALUES_IOCTL:

*******************************
`GPIO_V2_LINE_GET_VALUES_IOCTL`
*******************************

名称
====

`GPIO_V2_LINE_GET_VALUES_IOCTL` - 获取请求线路的值

概览
========

.. c:macro:: GPIO_V2_LINE_GET_VALUES_IOCTL

``int ioctl(int req_fd, GPIO_V2_LINE_GET_VALUES_IOCTL, struct gpio_v2_line_values *values)``

参数
=========

``req_fd``
    GPIO 字符设备的文件描述符，由 `gpio-v2-get-line-ioctl.rst` 返回的 :c:type:`request.fd<gpio_v2_line_request>` 中得到。
``values``
    要获取的 :c:type:`line_values<gpio_v2_line_values>`，其中 ``mask`` 设置为指示要获取的请求线路的子集。

描述
===========

获取请求线路的值
返回的值是逻辑值，表示线路是否处于活动或非活动状态。
`GPIO_V2_LINE_FLAG_ACTIVE_LOW` 标志控制物理值（高/低）和逻辑值（活动/非活动）之间的映射。
如果未设置 `GPIO_V2_LINE_FLAG_ACTIVE_LOW`，则高电平为活动，低电平为非活动。如果设置了 `GPIO_V2_LINE_FLAG_ACTIVE_LOW`，则低电平为活动，高电平为非活动。
输入和输出线路的值都可以读取。
对于输出线路，返回的值取决于驱动程序和配置，并且可能是输出缓冲区（最后请求设置的值）或输入缓冲区（线路的实际电平），具体取决于硬件和配置，这些值可能会有所不同。

返回值
============

成功时返回 0，相应的 :c:type:`values.bits<gpio_v2_line_values>` 包含读取的值。
在出现错误 -1 时，`errno` 变量会被相应地设置
常见的错误代码在 error-codes.rst 中有描述
