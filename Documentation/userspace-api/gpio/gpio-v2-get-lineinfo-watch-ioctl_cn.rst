.. SPDX-文件授权协议: GPL-2.0

.. _GPIO_V2_GET_LINEINFO_WATCH_IOCTL:

********************************
GPIO_V2_GET_LINEINFO_WATCH_IOCTL
********************************

名称
====

GPIO_V2_GET_LINEINFO_WATCH_IOCTL - 启用对某条线路请求状态和配置信息更改的监视

概要
========

.. c:macro:: GPIO_V2_GET_LINEINFO_WATCH_IOCTL

``int ioctl(int chip_fd, GPIO_V2_GET_LINEINFO_WATCH_IOCTL, struct gpio_v2_line_info *info)``

参数
=========

``chip_fd``
    由 `open()` 返回的 GPIO 字符设备文件描述符。
``info``
    要填充的 :c:type:`line_info<gpio_v2_line_info>` 结构体，其中 `offset` 设置为指示要监视的线路。

描述
===========

启用对某条线路请求状态和配置信息更改的监视。线路信息的更改包括线路被请求、释放或重新配置。
.. note::
    通常不需要监视线路信息，这通常仅由系统监控组件使用。
线路信息不包括线路值。
必须使用 gpio-v2-get-line-ioctl.rst 请求线路以访问其值，并且线路请求可以使用 gpio-v2-line-event-read.rst 监视线路事件。
默认情况下，当打开 GPIO 芯片时，所有线路都是未监视的。
可以通过为每条线路添加监视来同时监视多条线路。
一旦设置了监视，任何对线路信息的更改都会生成事件，这些事件可以从 ``chip_fd`` 中读取，具体如 gpio-v2-lineinfo-changed-read.rst 所述。
对已经处于监视状态的线路添加监视是错误的（**EBUSY**）。
手表（监控）是针对 ``chip_fd`` 的，并且独立于通过单独的 `open()` 调用在同一 GPIO 芯片上设置的手表（监控）。

返回值
======

成功时，返回 0 并且 ``info`` 会被当前的行信息填充。
出错时，返回 -1 并且 ``errno`` 变量会被适当设置。
常见的错误代码在 error-codes.rst 中有描述。
