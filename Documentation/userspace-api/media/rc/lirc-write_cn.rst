SPDX 许可证标识符：GPL-2.0 或 GFDL-1.1-no-invariants-or-later
c:命名空间:: RC

.. _lirc-write:

************
LIRC write()
************

名称
====

lirc-write - 向 LIRC 设备写入数据

概要
========

.. code-block:: c

    #include <unistd.h>

.. c:function:: ssize_t write(int fd, void *buf, size_t count)

参数
=========

``fd``
    由 ``open()`` 返回的文件描述符
``buf``
    包含待写入数据的缓冲区

``count``
    缓冲区中的字节数

描述
===========

:c:func:`write()` 从 ``buf`` 开始的位置向由文件描述符 ``fd`` 引用的设备写入最多 ``count`` 字节的数据。
数据的具体格式取决于驱动程序所处的模式，使用 :ref:`lirc_get_features` 获取支持的模式，并使用 :ref:`lirc_set_send_mode` 设置模式。
当处于 :ref:`LIRC_MODE_PULSE <lirc-mode-PULSE>` 模式时，写入字符设备的数据是一个整数值的脉冲/空闲序列。脉冲和空闲仅通过它们的位置隐式标记。数据必须以脉冲开始并以脉冲结束，因此数据总是包含奇数个采样。写入函数会阻塞直到硬件发送了数据。如果提供的数据多于硬件能够发送的数据量，驱动程序将返回 ``EINVAL``。
当处于 :ref:`LIRC_MODE_SCANCODE <lirc-mode-scancode>` 模式时，一次必须向字符设备写入一个 ``struct lirc_scancode``，否则返回 ``EINVAL``。设置 ``scancode`` 成员中的期望扫描码，并在 :c:type:`rc_proto` 成员中设置 :ref:`IR 协议 <Remote_controllers_Protocols>`。所有其他成员必须设置为 0，否则返回 ``EINVAL``。如果没有该协议的编码器或扫描码对于指定的协议无效，则返回 ``EINVAL``。写入函数会阻塞直到硬件发送了扫描码。

返回值
============

成功时，返回写入的字节数。如果这个数字小于请求的字节数或一帧所需的数据量，并不表示错误。出错时返回 -1，并且 ``errno`` 变量会被适当地设置。通用错误代码在 :ref:`通用错误代码 <gen-errors>` 章节中描述。
