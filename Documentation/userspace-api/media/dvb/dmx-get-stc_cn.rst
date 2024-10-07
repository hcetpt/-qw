SPDX 许可证标识符: GFDL-1.1-no-invariants-or-later
.. c:命名空间:: DTV.dmx

.. _DMX_GET_STC:

===========
DMX_GET_STC
===========

名称
----

DMX_GET_STC

概览
--------

.. c:宏:: DMX_GET_STC

``int ioctl(int fd, DMX_GET_STC, struct dmx_stc *stc)``

参数
---------

``fd``
    由 :c:func:`open()` 返回的文件描述符
``stc``
    指向 :c:type:`dmx_stc` 的指针，系统时间计数器（STC）数据将存储在此结构中
描述
-----------

此 ioctl 调用返回当前的系统时间计数器值（该计数器由类型为 :c:type:`DMX_PES_PCR <dmx_ts_pes>` 的 PES 过滤器驱动）
某些硬件支持多个 STC，因此您必须通过设置 stc 结构中的 :c:type:`num <dmx_stc>` 字段来指定使用哪一个（范围 0...n）
结果将以一个比率的形式返回，具有一个 64 位的分子和一个 32 位的分母，因此实际的 90kHz STC 值为
``stc->stc / stc->base``
返回值
------------

成功时返回 0
出错时返回 -1，并且设置 `errno` 变量
.. tabularcolumns:: |p{2.5cm}|p{15.0cm}|

.. flat-table::
    :header-rows:  0
    :stub-columns: 0
    :widths: 1 16

    -  .. 行 1

       -  ``EINVAL``

       -  无效的 stc 编号
通用错误代码在
:ref:`通用错误代码 <gen-errors>` 章节中有描述
