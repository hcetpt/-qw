.. SPDX-License-Identifier: GPL-2.0

.. _GPIO_V2_LINEINFO_CHANGED_READ:

*******************************
GPIO_V2_LINEINFO_CHANGED_READ
*******************************

名称
====

GPIO_V2_LINEINFO_CHANGED_READ - 从芯片读取被监视线路的信息变更事件

概要
========

``int read(int chip_fd, void *buf, size_t count)``

参数
=========

``chip_fd``
    由 `open()` 返回的 GPIO 字符设备文件描述符
``buf``
    存放 :c:type:`events<gpio_v2_line_info_changed>` 的缓冲区
``count``
    ``buf`` 中可用的字节数，必须至少为一个 :c:type:`gpio_v2_line_info_changed` 事件的大小
描述
===========

从芯片读取被监视线路的信息变更事件

.. note::
    通常不需要监控线路信息变更，一般仅由系统监控组件执行
这些事件与线路请求状态或配置的变化有关，而不是其值。使用 gpio-v2-line-event-read.rst 来接收线路值变化的事件
必须使用 gpio-v2-get-lineinfo-watch-ioctl.rst 监视一条线路以生成信息变更事件。随后，对该线路的请求、释放或重新配置将生成信息变更事件
内核在事件发生时为其打上时间戳，并将其存储在一个缓冲区中，用户空间可以使用 `read()` 按需读取这些事件
内核事件缓冲区的大小固定为每个 ``chip_fd`` 32 个事件
### 翻译成中文：

如果事件爆发的速度快于用户空间读取的速度，缓冲区可能会溢出。如果发生溢出，则会丢弃最近的事件。
溢出无法从用户空间检测到。
从缓冲区读取的事件始终按照内核检测到的顺序排列，即使有多个行由同一个“chip_fd”监控也是如此。
为了尽量减少将事件从内核复制到用户空间所需的调用次数，`read()` 支持一次复制多个事件。复制的事件数量是内核缓冲区中可用事件数量和用户空间缓冲区（`buf`）能容纳的事件数量中的较小值。
如果没有任何事件可用且 `chip_fd` 未设置 `O_NONBLOCK`，则 `read()` 将阻塞。
可以通过检查 `chip_fd` 是否可读来测试是否有事件存在，这可以通过使用 `poll()` 或等效函数实现。

### 返回值
成功时返回读取的字节数，该数值将是 `gpio_v2_line_info_changed` 事件大小的倍数。
失败时返回 -1，并且设置适当的 `errno` 变量。
常见的错误代码在 `error-codes.rst` 中描述。
