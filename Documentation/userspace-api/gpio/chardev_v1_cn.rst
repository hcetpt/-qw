SPDX 许可声明标识符: GPL-2.0

========================================
GPIO 字符设备用户空间 API (v1)
========================================

.. 警告::
   此 API 已被 `chardev.rst` (v2) 取代。
   新的开发应使用 v2 API，并鼓励现有开发尽快迁移，因为此 API 将在未来移除。
   v2 API 是 v1 API 的功能超集，因此任何 v1 调用都可以直接转换为 v2 等效调用。
   在迁移期间，此接口将继续维护，但新功能将仅添加到新的 API 中。
   最初在 4.8 版本中加入。
   该 API 基于三个主要对象：:ref:`gpio-v1-chip`、:ref:`gpio-v1-line-handle` 和 :ref:`gpio-v1-line-event`。
   在本文档中，“line event” 指的是可以监控线路边缘事件的请求，而不是边缘事件本身。

.. _gpio-v1-chip:

芯片
====

芯片表示一个单独的 GPIO 芯片，并通过形式为 `/dev/gpiochipX` 的设备文件暴露给用户空间。
每个芯片支持一定数量的 GPIO 线路，即 :c:type:`chip.lines<gpiochip_info>`。
芯片上的线路由范围从 0 到 `chip.lines - 1` 的 `offset` 标识，即 `[0, chip.lines)`。
线路可以通过调用 `gpio-get-linehandle-ioctl.rst` 来从芯片请求，并且得到的线路句柄用于访问 GPIO 芯片的线路，
或者通过调用 `gpio-get-lineevent-ioctl.rst` 并使用得到的线路事件来监控 GPIO 线路的边缘事件。
在此文档中，通过调用 `open()` 返回的文件描述符称为 `chip_fd`。
操作
----------

以下操作可以在芯片上执行：

.. toctree::
   :titlesonly:

   获取线路句柄 <gpio-get-linehandle-ioctl>
   获取线路事件 <gpio-get-lineevent-ioctl>
   获取芯片信息 <gpio-get-chipinfo-ioctl>
   获取线路信息 <gpio-get-lineinfo-ioctl>
   监听线路信息 <gpio-get-lineinfo-watch-ioctl>
   取消监听线路信息 <gpio-get-lineinfo-unwatch-ioctl>
   读取线路信息变更事件 <gpio-lineinfo-changed-read>

.. _gpio-v1-line-handle:

线路句柄
=======

线路句柄由`gpio-get-linehandle-ioctl.rst`创建，并提供对一组请求线路的访问。线路句柄通过`gpio-get-linehandle-ioctl.rst`返回的匿名文件描述符`request.fd<gpiohandle_request>`暴露给用户空间。在本文档中，线路句柄文件描述符称为`handle_fd`。

操作
----------

以下操作可以在线路句柄上执行：

.. toctree::
   :titlesonly:

   获取线路值 <gpio-handle-get-line-values-ioctl>
   设置线路值 <gpio-handle-set-line-values-ioctl>
   重新配置线路 <gpio-handle-set-config-ioctl>

.. _gpio-v1-line-event:

线路事件
========

线路事件由`gpio-get-lineevent-ioctl.rst`创建，并提供对请求线路的访问。线路事件通过`gpio-get-lineevent-ioctl.rst`返回的匿名文件描述符`request.fd<gpioevent_request>`暴露给用户空间。在本文档中，线路事件文件描述符称为`event_fd`。

操作
----------

以下操作可以在线路事件上执行：

.. toctree::
   :titlesonly:

   获取线路值 <gpio-handle-get-line-values-ioctl>
   读取线路边沿事件 <gpio-lineevent-data-read>

类型
=====

本节包含ABI v1中引用的结构体。
`:c:type:` `struct gpiochip_info<gpiochip_info>` 在ABI v1和v2中是通用的。

.. kernel-doc:: include/uapi/linux/gpio.h
   :identifiers:
    gpioevent_data
    gpioevent_request
    gpiohandle_config
    gpiohandle_data
    gpiohandle_request
    gpioline_info
    gpioline_info_changed

.. toctree::
   :hidden:

   error-codes
