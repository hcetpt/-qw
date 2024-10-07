SPDX 许可证标识符: GFDL-1.1-no-invariants-or-later
.. c:namespace:: DTV.ca

.. _CA_GET_SLOT_INFO:

================
CA_GET_SLOT_INFO
================

名称
----

CA_GET_SLOT_INFO

概要
--------

.. c:macro:: CA_GET_SLOT_INFO

``int ioctl(fd, CA_GET_SLOT_INFO, struct ca_slot_info *info)``

参数
---------

``fd``
  由先前调用 :c:func:`open()` 返回的文件描述符
``info``
  指向结构体 :c:type:`ca_slot_info` 的指针
描述
-----------

返回指定 :c:type:`ca_slot_info`.slot_num 的 CA 插槽信息
返回值
------------

成功时返回 0，并填充 :c:type:`ca_slot_info`
失败时返回 -1，并设置相应的 ``errno`` 变量
.. tabularcolumns:: |p{2.5cm}|p{15.0cm}|

.. flat-table::
    :header-rows:  0
    :stub-columns: 0
    :widths: 1 16

    -  -  ``ENODEV``
       -  该插槽不可用
通用错误代码在
:ref:`通用错误代码 <gen-errors>` 章节中描述。
