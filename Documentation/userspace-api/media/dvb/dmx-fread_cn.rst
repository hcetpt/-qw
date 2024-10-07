SPDX 许可声明标识符: GFDL-1.1-no-invariants-or-later
.. c:namespace:: DTV.dmx

.. _dmx_fread:

=======================
数字电视解复用读取（read()）
=======================

名称
----

数字电视解复用读取()

概览
--------

.. c:function:: size_t read(int fd, void *buf, size_t count)

参数
---------

``fd``
  由前一次调用 :c:func:`open()` 返回的文件描述符
``buf``
  要填充的缓冲区

``count``
  最大读取字节数

描述
-----------

此系统调用返回过滤后的数据，这些数据可能是节(section)或分组基本流(Packetized Elementary Stream, PES)数据。过滤后的数据从驱动程序内部的环形缓冲区转移到 ``buf`` 中。最大传输数据量由 ``count`` 决定。
.. note::

   如果使用带有 :c:type:`DMX_CHECK_CRC <dmx_sct_filter_params>` 标志创建的节过滤器，
   CRC 检查失败的数据将被静默忽略
返回值
------------

成功时返回 0
出错时返回 -1，并且设置 ``errno`` 变量为适当的错误码
.. tabularcolumns:: |p{2.5cm}|p{15.0cm}|

.. flat-table::
    :header-rows:  0
    :stub-columns: 0
    :widths: 1 16

    -  -  ``EWOULDBLOCK``
       -  没有可返回的数据并且指定了 ``O_NONBLOCK``
-  -  ``EOVERFLOW``
       -  过滤后的数据没有及时从缓冲区中读取，导致未读取的数据丢失。缓冲区被清空
-  -  ``ETIMEDOUT``
       -  在指定的超时期限内没有加载该节
查看 ioctl :ref:`DMX_SET_FILTER` 来了解如何设置超时时间
-  -  ``EFAULT``
       -  由于无效的 \*buf 指针，驱动程序未能写入调用者的缓冲区
通用错误代码在《通用错误代码》(:ref:`Generic Error Codes <gen-errors>`)章节中有描述。
