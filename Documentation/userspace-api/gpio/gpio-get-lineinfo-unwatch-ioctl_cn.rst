SPDX 许可证标识符: GPL-2.0

.. _GPIO_GET_LINEINFO_UNWATCH_IOCTL:

*******************************
GPIO_GET_LINEINFO_UNWATCH_IOCTL
*******************************

名称
====

GPIO_GET_LINEINFO_UNWATCH_IOCTL - 禁用对某条线路状态和配置信息更改的监控

概述
========

.. c:macro:: GPIO_GET_LINEINFO_UNWATCH_IOCTL

``int ioctl(int chip_fd, GPIO_GET_LINEINFO_UNWATCH_IOCTL, u32 *offset)``

参数
=========

``chip_fd``
    由 `open()` 返回的 GPIO 字符设备文件描述符
``offset``
    不再监控的线路偏移量

描述
===========

从当前 `chip_fd` 上正在监控的线路列表中移除该线路。
这是 gpio-v2-get-lineinfo-watch-ioctl.rst（v2）和 gpio-get-lineinfo-watch-ioctl.rst（v1）的反向操作。
如果尝试取消监控一个未被监控的线路，将返回错误（**EBUSY**）。
此功能首次在 5.7 版本中添加。

返回值
============

成功时返回 0
出错时返回 -1，并且 `errno` 变量会被设置为适当的错误代码
常见错误代码请参见 error-codes.rst
当然，请提供您需要翻译的文本。
