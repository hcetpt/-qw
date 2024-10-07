SPDX 许可声明标识符: GFDL-1.1-no-invariants-or-later
.. c:namespace:: DTV.dmx

.. _dmx_fwrite:

========================
数字电视解复用写入（write()）
========================

名称
----

数字电视解复用写入()

概览
--------

.. c:function:: ssize_t write(int fd, const void *buf, size_t count)

参数
---------

``fd``
  由前一次调用 :c:func:`open()` 返回的文件描述符
``buf``
  包含要写入的数据的缓冲区

``count``
  缓冲区中的字节数

描述
-----------

此系统调用仅由逻辑设备 ``/dev/dvb/adapter?/dvr?`` 提供，该设备与提供实际DVR功能的物理解复用设备相关联。它用于回放数字录制的传输流。相应的物理解复用设备 ``/dev/dvb/adapter?/demux?`` 中必须定义匹配过滤器。要传输的数据量由 `count` 指定。

返回值
------------

成功时返回0
错误时返回-1，并设置相应的 ``errno`` 变量
.. tabularcolumns:: |p{2.5cm}|p{15.0cm}|

.. flat-table::
    :header-rows:  0
    :stub-columns: 0
    :widths: 1 16

    -  -  ``EWOULDBLOCK``
       -  没有数据被写入。这可能发生在指定了 ``O_NONBLOCK`` 并且没有更多缓冲空间可用的情况下（如果没有指定 ``O_NONBLOCK``，函数将阻塞直到缓冲空间可用）

    -  -  ``EBUSY``
       -  此错误代码表示存在冲突请求。对应的解复用设备已设置为从前端接收数据。请确保这些过滤器已停止，并且已启动输入设置为 ``DMX_IN_DVR`` 的过滤器

通用错误码在 :ref:`通用错误码 <gen-errors>` 章节中描述。
