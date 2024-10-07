SPDX 许可证标识符: GPL-2.0

.. _GPIO_V2_GET_LINE_IOCTL:

**************************
GPIO_V2_GET_LINE_IOCTL
**************************

名称
====

GPIO_V2_GET_LINE_IOCTL - 从内核请求一个或多个线路

概要
====

.. c:macro:: GPIO_V2_GET_LINE_IOCTL

``int ioctl(int chip_fd, GPIO_V2_GET_LINE_IOCTL, struct gpio_v2_line_request *request)``

参数
====

``chip_fd``
    由 `open()` 返回的 GPIO 字符设备文件描述符
``request``
    :c:type:`line_request<gpio_v2_line_request>`，用于指定要请求的线路及其配置

描述
====

成功时，请求进程将获得对线路值的独占访问权限、对线路配置的写入访问权限，并且当检测到线路边缘时可能会接收到事件。这些功能在 :ref:`gpio-v2-line-request` 中有更详细的描述。
可以在单个请求中请求多个线路，内核尽可能原子地对请求的线路执行操作。例如，`gpio-v2-line-get-values-ioctl.rst` 将一次性读取所有请求的线路。
线路的状态（包括输出线路的值）保证会保持到返回的文件描述符被关闭为止。一旦文件描述符被关闭，从用户空间的角度来看，线路的状态将不再受控，并可能恢复到其默认状态。
请求已被使用的线路是一个错误（**EBUSY**）。
关闭 ``chip_fd`` 对现有的线路请求没有影响。

.. _gpio-v2-get-line-config-rules:

配置规则
-------------------

对于任何给定的请求线路，以下配置规则适用：

方向标志 ``GPIO_V2_LINE_FLAG_INPUT`` 和 ``GPIO_V2_LINE_FLAG_OUTPUT`` 不能同时设置。如果两者都没有设置，则唯一可以设置的标志是 ``GPIO_V2_LINE_FLAG_ACTIVE_LOW``，这样可以请求线路“原样”，允许在不改变电气配置的情况下读取线路值。
驱动标志 ``GPIO_V2_LINE_FLAG_OPEN_xxx`` 需要设置 ``GPIO_V2_LINE_FLAG_OUTPUT``。
仅可设置一个驱动标志
如果没有设置任何标志，则默认为推挽模式
仅可设置一个偏置标志 ``GPIO_V2_LINE_FLAG_BIAS_xxx``，并且需要同时设置方向标志
如果没有设置任何偏置标志，则偏置配置保持不变
边缘标志 ``GPIO_V2_LINE_FLAG_EDGE_xxx`` 需要设置 ``GPIO_V2_LINE_FLAG_INPUT`` 并且可以组合使用以检测上升沿和下降沿。从不支持边缘检测的线路请求边缘检测是错误（**ENXIO**）
仅可设置一个事件时钟标志 ``GPIO_V2_LINE_FLAG_EVENT_CLOCK_xxx``
如果没有设置任何事件时钟标志，则事件时钟默认为 ``CLOCK_MONOTONIC``
``GPIO_V2_LINE_FLAG_EVENT_CLOCK_HTE`` 标志需要支持硬件和设置了 ``CONFIG_HTE`` 的内核。从不支持 HTE 的设备请求 HTE 是错误（**EOPNOTSUPP**）
属性 :c:type:`debounce_period_us<gpio_v2_line_attribute>` 仅适用于设置了 ``GPIO_V2_LINE_FLAG_INPUT`` 的线路。当设置后，去抖动适用于 `gpio-v2-line-get-values-ioctl.rst` 返回的值以及 `gpio-v2-line-event-read.rst` 返回的边沿。如果硬件不直接支持去抖动，内核会在软件中进行仿真。对于既不支持硬件去抖动也不支持中断（软件仿真的必要条件）的线路请求去抖动是错误（**ENXIO**）
请求无效配置是错误（**EINVAL**）
配置支持
-----------

当请求的配置不被底层硬件和驱动直接支持时，内核会采用以下方法之一：

- 拒绝请求
- 在软件中模拟该功能
- 以尽力而为的方式处理该功能

所采用的方法取决于该功能是否可以在软件中合理地进行模拟，以及如果该功能不受支持对硬件和用户空间的影响。

对于每个功能所采用的方法如下表所示：

==============   ===========
功能              方法
==============   ===========
偏置（Bias）      尽力而为
消抖（Debounce）  模拟
方向（Direction） 拒绝
驱动（Drive）     模拟
边沿检测（Edge Detection） 拒绝
==============   ==========

偏置作为尽力而为处理是为了允许用户空间在支持内部偏置的平台和需要外部偏置的平台上应用相同的配置。最坏的情况是线路上没有偏置，而是处于浮动状态。
消抖通过在电线上应用滤波器来模拟硬件中断。检测到边沿并且线路在消抖期间保持稳定后生成一个边沿事件。事件的时间戳对应消抖期结束的时间。
驱动通过在线路不应主动驱动时将其切换为输入来模拟。
边沿检测需要中断支持，如果中断支持不可用则拒绝。用户空间仍可以通过轮询来进行模拟。
在所有情况下，由`gpio-v2-get-lineinfo-ioctl.rst`报告的配置是请求的配置，而不是实际的硬件配置。
用户空间无法确定某个功能是否在硬件中支持、是否被模拟或是否为尽力而为。
返回值
============

成功时返回 0，并且 :c:type:`request.fd<gpio_v2_line_request>` 包含请求的文件描述符
出错时返回 -1，并且 ``errno`` 变量会被相应设置
常见的错误代码在 error-codes.rst 中有描述
