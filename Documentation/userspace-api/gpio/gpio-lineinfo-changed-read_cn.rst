.. SPDX-License-Identifier: GPL-2.0

.. _GPIO_LINEINFO_CHANGED_READ:

**************************
GPIO_LINEINFO_CHANGED_READ
**************************

.. warning::
    此ioctl是chardev_v1.rst的一部分，并已被gpio-v2-lineinfo-changed-read.rst取代

名称
====

GPIO_LINEINFO_CHANGED_READ - 从芯片读取被监控线路的信息变更事件

概述
========

``int read(int chip_fd, void *buf, size_t count)``

参数
=========

``chip_fd``
    由`open()`返回的GPIO字符设备文件描述符
``buf``
    包含:c:type:`events<gpioline_info_changed>` 的缓冲区
``count``
    ``buf``中的字节数，必须至少为一个:c:type:`gpioline_info_changed` 事件的大小
描述
===========

从芯片读取被监控线路的信息变更事件

.. note::
    通常不需要监控线路信息变更，通常只有系统监控组件才会执行此操作

这些事件与线路请求状态或配置的更改有关，而不是其值。使用gpio-lineevent-data-read.rst来接收线路值发生变化时的事件。

必须使用gpio-get-lineinfo-watch-ioctl.rst监控线路以生成信息变更事件。随后对该线路的请求、释放或重新配置将生成一个信息变更事件。

内核在事件发生时对其进行时间戳记，并将其存储在一个缓冲区中，用户空间可以方便地使用`read()`进行读取。
内核事件缓冲区的大小固定为每个 `chip_fd` 32 个事件。
如果事件爆发的速度快于用户空间读取的速度，缓冲区可能会溢出。
如果发生溢出，则丢弃最近的一个事件。
从用户空间无法检测到溢出。
从缓冲区读取的事件始终按照内核检测到的顺序排列，即使有多个线路由同一个 `chip_fd` 监控也是如此。
为了尽量减少将事件从内核复制到用户空间所需的调用次数，`read()` 支持一次复制多个事件。复制的事件数量是内核缓冲区中可用事件数和用户空间缓冲区（`buf`）能容纳的事件数中的较小值。
如果没有任何事件可用且 `chip_fd` 没有设置 **O_NONBLOCK**，`read()` 将会阻塞。
可以通过检查 `chip_fd` 是否可读（使用 `poll()` 或等效方法）来测试是否有事件存在。
首次添加于 5.7 版本。

返回值
======

成功时返回读取的字节数，该数值将是 `gpioline_info_changed` 事件大小的倍数。
错误时返回 -1，并且 `errno` 变量将被适当设置。
常见的错误代码在 error-codes.rst 中有描述。
