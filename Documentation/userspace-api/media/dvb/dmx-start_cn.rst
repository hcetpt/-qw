SPDX 许可证标识符: GFDL-1.1-no-invariants-or-later
.. c:namespace:: DTV.dmx

.. _DMX_START:

=========
DMX_START
=========

名称
----

DMX_START

概要
--------

.. c:macro:: DMX_START

``int ioctl(int fd, DMX_START)``

参数
---------

``fd``
    由 :c:func:`open()` 返回的文件描述符
描述
-----------

此 ioctl 调用用于启动通过 ioctl 调用 :ref:`DMX_SET_FILTER` 或 :ref:`DMX_SET_PES_FILTER` 定义的实际过滤操作。
返回值
------------

成功时返回 0
错误时返回 -1，并且设置相应的 ``errno`` 变量
.. tabularcolumns:: |p{2.5cm}|p{15.0cm}|

.. flat-table::
    :header-rows:  0
    :stub-columns: 0

    -  .. row 1

       -  ``EINVAL``

       -  无效参数，即没有通过 :ref:`DMX_SET_FILTER` 或 :ref:`DMX_SET_PES_FILTER` ioctl 提供过滤参数
-  .. row 2

       -  ``EBUSY``

       -  此错误代码表示存在冲突请求。有活动过滤器正在从另一个输入源过滤数据。确保在启动此过滤器之前停止这些过滤器。
通用错误代码在 :ref:`Generic Error Codes <gen-errors>` 章节中进行了描述。
