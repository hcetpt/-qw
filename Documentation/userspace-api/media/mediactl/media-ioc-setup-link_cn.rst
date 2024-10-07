SPDX 许可证标识符: GFDL-1.1-no-invariants-or-later
.. c:namespace:: MC

.. _media_ioc_setup_link:

**************************
ioctl MEDIA_IOC_SETUP_LINK
**************************

名称
====

MEDIA_IOC_SETUP_LINK - 修改链接的属性

概述
========

.. c:macro:: MEDIA_IOC_SETUP_LINK

``int ioctl(int fd, MEDIA_IOC_SETUP_LINK, struct media_link_desc *argp)``

参数
=========

``fd``
    由 :c:func:`open()` 返回的文件描述符
``argp``
    指向 :c:type:`media_link_desc` 结构体的指针
描述
===========

为了更改链接属性，应用程序需要填充一个 :c:type:`media_link_desc` 结构体，其中包含链接标识信息（源端口和接收端口）以及请求的新链接标志。然后通过指向该结构体的指针调用 MEDIA_IOC_SETUP_LINK ioctl。

唯一可配置的属性是 ``ENABLED`` 链接标志，用于启用或禁用链接。带有 ``IMMUTABLE`` 链接标志的链接不能被启用或禁用。

链接配置不会对其他链接产生副作用。如果在接收端口上已启用的链接阻止了当前链接的启用，驱动程序会返回 ``EBUSY`` 错误代码。

只有带有 ``DYNAMIC`` 链接标志的链接可以在流媒体数据期间被启用或禁用。尝试启用或禁用非动态流链接将返回 ``EBUSY`` 错误代码。

如果找不到指定的链接，驱动程序会返回 ``EINVAL`` 错误代码。

返回值
============

成功时返回 0，出错时返回 -1 并设置适当的 ``errno`` 变量。通用错误代码在“<gen-errors>”章节中有描述。

EINVAL
    结构体 :c:type:`media_link_desc` 引用了不存在的链接，或者链接是不可变的且尝试修改其配置。
