SPDX 许可证标识符: GPL-2.0

========================
设备频率调节
========================

简介
------------

此框架提供了一个标准的内核接口，用于任意设备上的动态电压和频率切换。它通过类似于 cpufreq 子系统的 sysfs 文件暴露了调整频率的控制功能。对于可以测量当前使用情况的设备，可以通过控制器自动调整其频率。

API
---

设备驱动程序需要初始化一个 :c:type:`devfreq_profile` 并调用 :c:func:`devfreq_add_device` 函数来创建一个 :c:type:`devfreq` 实例。
.. kernel-doc:: include/linux/devfreq.h
.. kernel-doc:: include/linux/devfreq-event.h
.. kernel-doc:: drivers/devfreq/devfreq.c
        :export:
.. kernel-doc:: drivers/devfreq/devfreq-event.c
        :export:
