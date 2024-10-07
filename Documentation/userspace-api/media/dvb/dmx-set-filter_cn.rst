SPDX 许可证标识符: GFDL-1.1-no-invariants-or-later
.. c:namespace:: DTV.dmx

.. _DMX_SET_FILTER:

==============
DMX_SET_FILTER
==============

名称
----

DMX_SET_FILTER

简介
--------

.. c:macro:: DMX_SET_FILTER

``int ioctl(int fd, DMX_SET_FILTER, struct dmx_sct_filter_params *params)``

参数
---------

``fd``
    由 :c:func:`open()` 返回的文件描述符
``params``

    指向包含过滤器参数结构的指针
描述
-----------

此 ioctl 调用根据提供的过滤器和掩码参数设置一个过滤器。可以定义一个超时时间，表示等待某个部分加载的秒数。值为 0 表示不应应用超时。最后还有一个标志字段，用于指定是否应对某部分进行 CRC 校验，过滤器是否应为“一次性”过滤器（即在接收到第一个部分后停止过滤操作），以及是否应立即开始过滤操作（无需等待 :ref:`DMX_START` ioctl 调用）。如果之前已设置了一个过滤器，则该过滤器将被取消，并且接收缓冲区将被清空。
返回值
------------

成功时返回 0
出错时返回 -1，并且设置 ``errno`` 变量
通用错误代码在 :ref:`通用错误代码 <gen-errors>` 章节中描述
