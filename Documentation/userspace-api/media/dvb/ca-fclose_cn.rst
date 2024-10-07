SPDX 许可证标识符: GFDL-1.1-no-invariants-or-later
.. c:namespace:: DTV.ca

.. _ca_fclose:

=====================
数字电视 CA close()
=====================

名称
----

数字电视 CA close()

概要
--------

.. c:function:: int close(int fd)

参数
---------

``fd``
  由前一个调用 :c:func:`open()` 返回的文件描述符
描述
-----------

此系统调用关闭之前已打开的 CA 设备
返回值
------------

成功时返回 0
出错时返回 -1，并且设置 ``errno`` 变量为适当的值
通用错误代码在章节 :ref:`通用错误代码 <gen-errors>` 中有描述
