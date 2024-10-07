SPDX 许可证标识符: GPL-2.0

===================================
GPIO 字符设备用户空间 API
===================================

这是字符设备 API 的最新版本（v2），如 ``include/uapi/linux/gpio.h`` 中定义。

首次添加于 5.10 版本
.. note::
   请勿滥用用户空间 API 来控制已经有合适内核驱动程序的硬件。您的用例可能已经有现成的驱动程序，而现有的内核驱动程序肯定能提供比从用户空间进行位操作更好的解决方案。
   阅读 `Documentation/driver-api/gpio/drivers-on-gpio.rst` 以避免在用户空间重新发明内核轮子。
   同样地，对于多功能线路，可能有其他子系统（例如 `Documentation/spi/index.rst`, `Documentation/i2c/index.rst`, `Documentation/driver-api/pwm.rst`, `Documentation/w1/index.rst` 等）提供了适合您硬件的驱动程序和 API。
使用字符设备 API 的基本示例可以在 ``tools/gpio/*`` 中找到。
该 API 主要围绕两个主要对象：:ref:`gpio-v2-chip` 和 :ref:`gpio-v2-line-request`。
.. _gpio-v2-chip:

芯片
====

芯片表示一个单一的 GPIO 芯片，并通过形式为 `/dev/gpiochipX` 的设备文件暴露给用户空间。
每个芯片支持一定数量的 GPIO 线路，这些线路由 :c:type:`chip.lines<gpiochip_info>` 表示。
芯片上的线路通过范围从 0 到 `chip.lines - 1` 的 `偏移量` 进行标识，即 `[0, chip.lines)`。
线路请求通过 `gpio-v2-get-line-ioctl.rst` 从芯片中获取，得到的线路请求用于访问 GPIO 芯片的线路或监控线路的边缘事件。
在此文档中，调用 `open()` 打开 GPIO 设备文件后返回的文件描述符被称为 `chip_fd`。
操作
----------

以下操作可以在芯片上执行：

.. toctree::
   :titlesonly:

   获取引脚线路 <gpio-v2-get-line-ioctl>
   获取芯片信息 <gpio-get-chipinfo-ioctl>
   获取引脚线路信息 <gpio-v2-get-lineinfo-ioctl>
   监听引脚线路信息 <gpio-v2-get-lineinfo-watch-ioctl>
   停止监听引脚线路信息 <gpio-get-lineinfo-unwatch-ioctl>
   读取引脚线路变更事件 <gpio-v2-lineinfo-changed-read>

.. _gpio-v2-line-request:

引脚线路请求
============

引脚线路请求由 gpio-v2-get-line-ioctl.rst 创建，并提供对一组请求的引脚线路的访问。引脚线路请求通过 gpio-v2-get-line-ioctl.rst 返回的匿名文件描述符 :c:type:`request.fd<gpio_v2_line_request>` 暴露给用户空间。在此文档中，引脚线路请求文件描述符称为 `req_fd`。

操作
----------

以下操作可以在引脚线路请求上执行：

.. toctree::
   :titlesonly:

   获取引脚值 <gpio-v2-line-get-values-ioctl>
   设置引脚值 <gpio-v2-line-set-values-ioctl>
   读取引脚边沿事件 <gpio-v2-line-event-read>
   重新配置引脚 <gpio-v2-line-set-config-ioctl>

类型
=====

本节包含 API v2 中引用的结构体和枚举，定义在 `include/uapi/linux/gpio.h` 中。
.. kernel-doc:: include/uapi/linux/gpio.h
   :identifiers:
    gpio_v2_line_attr_id
    gpio_v2_line_attribute
    gpio_v2_line_changed_type
    gpio_v2_line_config
    gpio_v2_line_config_attribute
    gpio_v2_line_event
    gpio_v2_line_event_id
    gpio_v2_line_flag
    gpio_v2_line_info
    gpio_v2_line_info_changed
    gpio_v2_line_request
    gpio_v2_line_values
    gpiochip_info

.. toctree::
   :hidden:

   错误代码
