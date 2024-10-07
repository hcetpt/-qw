SPDX 许可声明标识符: GFDL-1.1-no-invariants-or-later
.. c:namespace:: DTV.dmx

.. _DMX_SET_BUFFER_SIZE:

===================
DMX_SET_BUFFER_SIZE
===================

名称
----

DMX_SET_BUFFER_SIZE

概要
--------

.. c:macro:: DMX_SET_BUFFER_SIZE

``int ioctl(int fd, DMX_SET_BUFFER_SIZE, unsigned long size)``

参数
---------

``fd``
    由 :c:func:`open()` 返回的文件描述符
``size``
    无符号长整型大小

描述
-----------

此 ioctl 调用用于设置用于过滤数据的循环缓冲区的大小。默认大小是两个最大尺寸的部分，即如果未调用此函数，则使用 ``2 * 4096`` 字节的缓冲区大小。
返回值
------------

成功时返回 0
出错时返回 -1，并且将 ``errno`` 变量设置为适当的值
通用错误代码在章节 :ref:`Generic Error Codes <gen-errors>` 中描述
