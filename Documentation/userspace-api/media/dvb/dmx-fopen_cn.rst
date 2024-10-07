.. SPDX 许可证标识符: GFDL-1.1-no-invariants-or-later
.. c:命名空间:: DTV.dmx

.. _dmx_fopen:

=======================
数字电视解复用器 open()
=======================

名称
----

数字电视解复用器 open()

概览
--------

.. c:函数:: int open(const char *deviceName, int flags)

参数
---------

``name``
  特定数字电视解复用器设备的名称
``flags``
  以下标志位的按位或操作：

.. tabularcolumns:: |p{2.5cm}|p{15.0cm}|

.. flat-table::
    :header-rows:  0
    :stub-columns: 0
    :widths: 1 16

    -
       - ``O_RDONLY``
       - 只读访问

    -
       - ``O_RDWR``
       - 读写访问

    -
       - ``O_NONBLOCK``
       - 非阻塞模式打开
         （默认为阻塞模式）

描述
-----------

此系统调用与设备名 ``/dev/dvb/adapter?/demux?`` 一起使用时，会分配一个新的过滤器，并返回一个句柄，该句柄可用于后续对该过滤器的控制。对于每个要使用的过滤器都需要进行此调用，即每个返回的文件描述符都指向单个过滤器。``/dev/dvb/adapter?/dvr?`` 是用于获取数字视频录制的传输流的逻辑设备。从这个设备读取时，会包含对应解复用器设备（``/dev/dvb/adapter?/demux?``）中设置的所有PES过滤器的数据包，并且输出设置为 ``DMX_OUT_TS_TAP``。通过向该设备写入数据来重放已记录的传输流。
阻塞模式或非阻塞模式的意义在相关文档中有说明，在这些文档中有所区别。它不会影响 ``open()`` 调用本身的语义。通过使用fcntl系统调用中的 ``F_SETFL`` 命令，可以在以后将阻塞模式下的设备切换到非阻塞模式（反之亦然）。

返回值
------------

成功时返回 0
错误时返回 -1，并且设置 ``errno`` 变量为适当的值
.. tabularcolumns:: |p{2.5cm}|p{15.0cm}|

.. flat-table::
    :header-rows:  0
    :stub-columns: 0
    :widths: 1 16

    -  -  ``EMFILE``
       -  “打开的文件太多”，即没有更多的过滤器可用
通用错误代码在 :ref:`通用错误代码 <gen-errors>` 章节中描述。
