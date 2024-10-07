.. SPDX-License-Identifier: GPL-2.0

.. _GPIO_LINEEVENT_DATA_READ:

************************
GPIO_LINEEVENT_DATA_READ
************************

.. warning::
    此ioctl是chardev_v1.rst的一部分，并已被gpio-v2-line-event-read.rst弃用。

名称
====

GPIO_LINEEVENT_DATA_READ - 从行事件中读取边沿检测事件

概要
====

``int read(int event_fd, void *buf, size_t count)``

参数
====

``event_fd``
    GPIO字符设备的文件描述符，由gpio-get-lineevent-ioctl.rst通过:c:type:`request.fd<gpioevent_request>`返回。
``buf``
    包含:c:type:`events<gpioevent_data>`的缓冲区。
``count``
    ``buf``中的字节数，必须至少为一个:c:type:`gpioevent_data`的大小。
描述
====

从行事件中读取边沿检测事件。
必须使用``GPIOEVENT_REQUEST_RISING_EDGE``或``GPIOEVENT_REQUEST_FALLING_EDGE``或两者之一为输入线启用边沿检测。当在输入线上检测到边沿中断时，将生成边沿事件。
边沿定义为逻辑线路值的变化，因此从非激活状态到激活状态的过渡是一个上升沿。如果设置了``GPIOHANDLE_REQUEST_ACTIVE_LOW``，则逻辑极性与物理极性相反，此时``GPIOEVENT_REQUEST_RISING_EDGE``对应于一个下降沿。
内核尽可能接近事件发生的时间捕获并记录边沿事件的时间戳，并将其存储在一个缓冲区中，用户空间可以使用`read()`按需读取这些事件。
:c:type:`event.timestamp<gpioevent_data>`的时间源为``CLOCK_MONOTONIC``，但对于早于Linux 5.7的内核，该时间源为``CLOCK_REALTIME``。在:c:type:`gpioevent_data`中没有指示使用了哪个时间源，必须通过内核版本或对时间戳本身的合理性检查来确定。
事件从缓冲区读取时，始终按照内核检测到的顺序进行。
内核事件缓冲区的大小固定为16个事件。
如果事件爆发的速度快于用户空间读取的速度，缓冲区可能会溢出。如果发生溢出，则丢弃最近的一个事件。
用户空间无法检测到溢出。
为了尽量减少将事件从内核复制到用户空间所需的调用次数，`read()` 支持复制多个事件。复制的事件数量是内核缓冲区中可用事件数量和用户空间缓冲区（`buf`）能容纳的数量中的较小值。
如果没有可用事件，并且 `event_fd` 没有设置 **O_NONBLOCK**，`read()` 将会阻塞。
可以通过检查 `event_fd` 是否可读（使用 `poll()` 或等效方法）来测试是否有事件存在。
返回值
======

成功时返回读取的字节数，该数字将是 `gpio_lineevent_data` 事件大小的倍数。
失败时返回-1，并且设置 `errno` 变量以表示适当的错误码。
常见的错误码在 error-codes.rst 中描述。
当然，请提供您需要翻译的文本。
