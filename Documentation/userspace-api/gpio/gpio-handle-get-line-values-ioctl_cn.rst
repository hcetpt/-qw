.. SPDX-License-Identifier: GPL-2.0

.. _GPIOHANDLE_GET_LINE_VALUES_IOCTL:

********************************
GPIOHANDLE_GET_LINE_VALUES_IOCTL
********************************
.. warning::
    此ioctl是chardev_v1.rst的一部分，并已被gpio-v2-line-get-values-ioctl.rst废弃。
名称
====

GPIOHANDLE_GET_LINE_VALUES_IOCTL - 获取所有请求行的值
概要
========

.. c:macro:: GPIOHANDLE_GET_LINE_VALUES_IOCTL

``int ioctl(int handle_fd, GPIOHANDLE_GET_LINE_VALUES_IOCTL, struct gpiohandle_data *values)``

参数
=========

``handle_fd``
    GPIO字符设备的文件描述符，由gpio-get-linehandle-ioctl.rst中的:c:type:`request.fd<gpiohandle_request>`返回。
``values``
    要填充的:c:type:`line_values<gpiohandle_data>`。
描述
===========

获取所有请求行的值
返回的值是逻辑值，表示线路是否处于活动状态或非活动状态
``GPIOHANDLE_REQUEST_ACTIVE_LOW`` 标志控制物理值（高/低）与逻辑值（活动/非活动）之间的映射
如果没有设置 ``GPIOHANDLE_REQUEST_ACTIVE_LOW``，则高为活动，低为非活动。如果设置了 ``GPIOHANDLE_REQUEST_ACTIVE_LOW``，则低为活动，高为非活动
输入和输出行的值都可以读取
对于输出行，返回的值取决于驱动程序和配置，可能是输出缓冲区（最后请求设置的值）或输入缓冲区（线路的实际电平），并且根据硬件和配置，这些可能有所不同。
此ioctl也可以用于读取线路事件的线路值，此时用“event_fd”代替“handle_fd”。由于在这种情况下只请求了一条线路，因此只有一个值返回到“values”中。

返回值
======

成功时返回0，并且“values”被读取的值填充；
出错时返回-1，并且根据情况设置“errno”变量。
常见的错误代码在error-codes.rst中有描述。
