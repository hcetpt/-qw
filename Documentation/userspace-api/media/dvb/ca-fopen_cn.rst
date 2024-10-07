.. SPDX 许可证标识符: GFDL-1.1-no-invariants-or-later
.. c:namespace:: DTV.ca

.. _ca_fopen:

====================
Digital TV CA open()
====================

名称
----

Digital TV CA open()

概览
----

.. c:function:: int open(const char *name, int flags)

参数
---------

``name``
  特定的数字电视 CA 设备名称
``flags``
  以下标志的按位或：

.. tabularcolumns:: |p{2.5cm}|p{15.0cm}|

.. flat-table::
    :header-rows:  0
    :stub-columns: 0
    :widths: 1 16

    -  - ``O_RDONLY``
       - 只读访问

    -  - ``O_RDWR``
       - 读写访问

    -  - ``O_NONBLOCK``
       - 非阻塞模式打开
         （默认为阻塞模式）

描述
----

此系统调用为后续使用打开一个命名的 CA 设备（例如 ``/dev/dvb/adapter?/ca?``）
当 `open()` 调用成功后，设备将准备好使用。阻塞模式和非阻塞模式的意义在有差异的功能文档中有描述。它不会影响 `open()` 调用本身的语义。使用 `fcntl` 系统调用中的 `F_SETFL` 命令可以将阻塞模式打开的设备设置为非阻塞模式（反之亦然）。这是一个标准系统调用，在 Linux 手册页中有关于 `fcntl` 的文档。只有单个用户可以以 `O_RDWR` 模式打开 CA 设备。所有其他尝试以该模式打开设备的操作都会失败，并返回错误代码。

返回值
------------

成功时返回 0
出错时返回 -1，并且设置 `errno` 变量
通用错误代码在 :ref:`通用错误代码 <gen-errors>` 章节中有描述。
