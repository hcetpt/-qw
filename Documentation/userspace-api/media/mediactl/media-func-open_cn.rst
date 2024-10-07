SPDX 许可证标识符: GFDL-1.1-no-invariants-or-later
.. c:namespace:: MC

.. _media-func-open:

************
media open()
************

名称
====

media-open - 打开一个媒体设备

概要
========

.. code-block:: c

    #include <fcntl.h>

.. c:function:: int open(const char *device_name, int flags)

参数
=========

``device_name``
    要打开的设备
``flags``
    打开标志。访问模式必须是 ``O_RDONLY`` 或 ``O_RDWR``，其他标志无效。
描述
===========

为了打开一个媒体设备，应用程序需要调用 :c:func:`open()` 并传入所需的设备名。此函数没有副作用；设备配置保持不变。
当设备以只读模式打开时，尝试修改其配置将导致错误，并且 ``errno`` 将被设置为 EBADF。
返回值
============

:c:func:`open()` 在成功时返回新的文件描述符。在出现错误时，返回 -1，并且根据情况设置 ``errno``。可能的错误代码包括：

EACCES
    请求的文件访问权限不被允许
EMFILE
    进程已经打开了最大数量的文件
ENFILE
    系统上总的打开文件数达到了限制
ENOMEM
    内核可用内存不足
ENXIO
    不存在与此设备特殊文件对应的设备
当然，请提供您需要翻译的文本。
