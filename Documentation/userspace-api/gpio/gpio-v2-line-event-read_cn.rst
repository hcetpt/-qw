.. SPDX-License-Identifier: GPL-2.0

.. _GPIO_V2_LINE_EVENT_READ:

**************************
GPIO_V2_LINE_EVENT_READ
**************************

名称
====

GPIO_V2_LINE_EVENT_READ - 从请求中读取线路的边沿检测事件

简介
========

``int read(int req_fd, void *buf, size_t count)``

参数
=========

``req_fd``
    GPIO 字符设备的文件描述符，由 gpio-v2-get-line-ioctl.rst 返回的 :c:type:`request.fd<gpio_v2_line_request>`
``buf``
    用于存储 :c:type:`events<gpio_v2_line_event>` 的缓冲区
``count``
    ``buf`` 中可用的字节数，必须至少为一个 :c:type:`gpio_v2_line_event` 的大小
描述
===========

从请求中读取线路的边沿检测事件。
必须使用 ``GPIO_V2_LINE_FLAG_EDGE_RISING`` 或 ``GPIO_V2_LINE_FLAG_EDGE_FALLING``（或两者）为输入线路启用边沿检测。当在输入线路上检测到边沿中断时，将生成边沿事件。
边沿定义为逻辑线路值的变化，因此从非活动状态到活动状态的转换是一个上升沿。如果设置了 ``GPIO_V2_LINE_FLAG_ACTIVE_LOW``，则逻辑极性与物理极性相反，此时 ``GPIO_V2_LINE_FLAG_EDGE_RISING`` 对应于物理下降沿。
内核尽可能接近事件发生的时间捕获并打上时间戳，并将其存储在一个缓冲区中，用户空间可以方便地使用 `read()` 函数读取这些事件。
从缓冲区读取的事件始终按照它们被内核检测到的顺序排列，即使同时监控多个线路也是如此。
内核事件缓冲区的大小在创建线路请求时是固定的，可以通过 :c:type:`request.event_buffer_size<gpio_v2_line_request>` 来影响其大小。
默认大小是请求的行数的16倍。
如果事件突发的速度快于用户空间读取的速度，缓冲区可能会溢出。如果发生溢出，则会丢弃最旧的缓冲事件。用户空间可以通过监控事件序列号来检测溢出。
为了尽量减少将事件从内核复制到用户空间所需的调用次数，`read()` 支持复制多个事件。复制的事件数量为内核缓冲区中可用事件数量和用户空间缓冲区（`buf`）中能容纳事件数量中的较小值。
使用 gpio-v2-line-set-config-ioctl.rst 更改边沿检测标志不会移除或修改内核事件缓冲区中已有的事件。
如果没有可用事件且 `req_fd` 未设置 **O_NONBLOCK**，`read()` 将会阻塞。
可以通过检查 `req_fd` 是否可读（使用 `poll()` 或等效方法）来测试是否有事件存在。

返回值
======

成功时返回读取的字节数，该数值将是 `gpio_v2_line_event` 类型大小的倍数。
错误时返回 -1，并且设置 `errno` 变量以表示适当的错误代码。常见的错误代码在 error-codes.rst 中描述。
