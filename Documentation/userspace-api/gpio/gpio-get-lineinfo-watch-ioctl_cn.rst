.. 许可证标识符: GPL-2.0

.. _GPIO_GET_LINEINFO_WATCH_IOCTL:

*******************************
GPIO_GET_LINEINFO_WATCH_IOCTL
*******************************

.. 警告::
    此 ioctl 是 chardev_v1.rst 的一部分，并已被 gpio-v2-get-lineinfo-watch-ioctl.rst 废弃。

名称
====

GPIO_GET_LINEINFO_WATCH_IOCTL - 启用对线路请求状态和配置信息更改的监控

概要
====

.. c:macro:: GPIO_GET_LINEINFO_WATCH_IOCTL

``int ioctl(int chip_fd, GPIO_GET_LINEINFO_WATCH_IOCTL, struct gpioline_info *info)``

参数
====

``chip_fd``
    由 `open()` 返回的 GPIO 字符设备文件描述符。
``info``
    要填充的 :c:type:`line_info<gpioline_info>` 结构体，其中 ``offset`` 设置为指示要监控的线路。

描述
====

启用对线路请求状态和配置信息更改的监控。线路信息的变化包括线路被请求、释放或重新配置。
.. 注意::
    监控线路信息通常不是必需的，通常仅由系统监控组件使用。
线路信息不包含线路值。
必须使用 gpio-get-linehandle-ioctl.rst 或 gpio-get-lineevent-ioctl.rst 请求线路以访问其值，并且可以使用 gpio-lineevent-data-read.rst 监控线路事件。
默认情况下，当打开 GPIO 芯片时，所有线路均未被监控。
可以通过为每个线路添加监控来同时监控多个线路。
一旦设置了监控，任何线路信息的更改都会生成事件，这些事件可以从 ``chip_fd`` 中读取，具体方法参见 gpio-lineinfo-changed-read.rst。
向已经处于监控状态的行添加监控是错误的（**EBUSY**）
监控是针对 ``chip_fd`` 的，并且与使用单独的 `open()` 调用在同一 GPIO 芯片上设置的监控独立。
首次在 5.7 版本中引入
返回值
======

成功时返回 0，并且 ``info`` 会被填充当前行的信息
出错时返回 -1，并且 ``errno`` 变量会被相应地设置
常见的错误代码在 error-codes.rst 中有描述
