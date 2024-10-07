SPDX 许可证标识符：GPL-2.0 或 GFDL-1.1-no-invariants-or-later
.. c:namespace:: RC

.. _lirc-read:

***********
LIRC read()
***********

名称
====

lirc-read - 从 LIRC 设备读取数据

概要
========

.. code-block:: c

    #include <unistd.h>

.. c:function:: ssize_t read(int fd, void *buf, size_t count)

参数
=========

``fd``
    由 ``open()`` 返回的文件描述符
``buf``
    要填充的缓冲区
``count``
    最大读取字节数

描述
===========

:c:func:`read()` 尝试从文件描述符 ``fd`` 中读取最多 ``count`` 字节的数据到以 ``buf`` 开始的缓冲区。如果 ``count`` 为零，:c:func:`read()` 返回零且无其他结果。如果 ``count`` 大于 ``SSIZE_MAX``，结果是未定义的。
数据的具体格式取决于驱动程序使用的 :ref:`lirc_modes`。使用 :ref:`lirc_get_features` 获取支持的模式，并使用 :ref:`lirc_set_rec_mode` 设置当前活动模式。
模式 :ref:`LIRC_MODE_MODE2 <lirc-mode-mode2>` 用于原始红外信号，在这种模式下，包含描述红外信号的无符号整数值的包将从字符设备中读取。
另外，:ref:`LIRC_MODE_SCANCODE <lirc-mode-scancode>` 也可以使用，在这种模式下，扫描码要么由软件解码器解码，要么由硬件解码器解码。:c:type:`rc_proto` 成员被设置为用于传输的 :ref:`IR 协议 <Remote_controllers_Protocols>`，``scancode`` 被设置为解码后的扫描码，而 ``keycode`` 被设置为键码或 ``KEY_RESERVED``。

返回值
============

成功时，返回读取的字节数。如果这个数字小于请求的字节数或一帧所需的数据量，并不视为错误。在发生错误时，返回 -1，并适当设置 ``errno`` 变量。
