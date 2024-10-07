SPDX 许可证标识符: GFDL-1.1-no-invariants-or-later
.. c:namespace:: DTV.dmx

.. _DMX_SET_PES_FILTER:

==================
DMX_SET_PES_FILTER
==================

名称
----

DMX_SET_PES_FILTER

概要
--------

.. c:macro:: DMX_SET_PES_FILTER

``int ioctl(int fd, DMX_SET_PES_FILTER, struct dmx_pes_filter_params *params)``

参数
---------

``fd``
    由 :c:func:`open()` 返回的文件描述符
``params``
    指向包含过滤器参数的结构体的指针

描述
-----------

此 ioctl 调用根据提供的参数设置一个 PES 过滤器。这里的 PES 过滤器是指仅基于包标识符（PID）的过滤器，即不支持 PES 头或有效负载的过滤功能。
返回值
------------

成功时返回 0
错误时返回 -1，并且设置相应的 ``errno`` 变量
.. tabularcolumns:: |p{2.5cm}|p{15.0cm}|

.. flat-table::
    :header-rows:  0
    :stub-columns: 0
    :widths: 1 16

    -  .. row 1

       -  ``EBUSY``

       -  此错误代码表示有冲突的请求。存在活动过滤器正在从其他输入源过滤数据。确保在启动此过滤器之前停止这些过滤器。
通用错误代码在“通用错误代码”章节中描述。
