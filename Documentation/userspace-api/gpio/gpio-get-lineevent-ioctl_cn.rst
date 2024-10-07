.. SPDX-License-Identifier: GPL-2.0

.. _GPIO_GET_LINEEVENT_IOCTL:

************************
GPIO_GET_LINEEVENT_IOCTL
************************

.. warning::
    此ioctl是chardev_v1.rst的一部分，并已被gpio-v2-get-line-ioctl.rst废弃

名称
====

GPIO_GET_LINEEVENT_IOCTL - 从内核请求带有边沿检测的线路

概要
====

.. c:macro:: GPIO_GET_LINEEVENT_IOCTL

``int ioctl(int chip_fd, GPIO_GET_LINEEVENT_IOCTL, struct gpioevent_request *request)``

参数
====

``chip_fd``
    由`open()`返回的GPIO字符设备文件描述符
``request``
    类型为:c:type:`event_request<gpioevent_request>`，用于指定要请求的线路及其配置

描述
====

从内核请求带有边沿检测的线路。
成功时，请求进程将获得对该线路值的独占访问权限，并且当在该线路上检测到边沿时可能会接收到事件，具体描述见gpio-lineevent-data-read.rst。
线路的状态保证保持所请求的状态，直到返回的文件描述符被关闭。一旦文件描述符被关闭，从用户空间的角度来看，线路的状态将变得不受控制，并可能恢复为其默认状态。
请求一个已经被使用的线路是一个错误（**EBUSY**）。
请求一个不支持中断的线路上的边沿检测是一个错误（**ENXIO**）。
与:ref:`线路句柄<gpio-get-linehandle-config-support>`一样，偏置配置尽力而为。
关闭 `chip_fd` 对现有的行事件没有影响。

配置规则
-------------------

以下配置规则适用：

- 行事件作为输入被请求，因此不能设置与输出行相关的标志，如 `GPIOHANDLE_REQUEST_OUTPUT`、`GPIOHANDLE_REQUEST_OPEN_DRAIN` 或 `GPIOHANDLE_REQUEST_OPEN_SOURCE`。
- 只能设置一个偏置标志 `GPIOHANDLE_REQUEST_BIAS_xxx`。
- 如果没有设置任何偏置标志，则偏置配置不会改变。
- 边沿标志 `GPIOEVENT_REQUEST_RISING_EDGE` 和 `GPIOEVENT_REQUEST_FALLING_EDGE` 可以组合使用来检测上升沿和下降沿。
- 请求无效的配置是一个错误（**EINVAL**）。

返回值
=================

成功时返回 0，并且 :c:type:`request.fd<gpioevent_request>` 包含请求的文件描述符。
出错时返回 -1，并且 `errno` 变量被适当设置。
常见的错误代码在 error-codes.rst 中描述。
