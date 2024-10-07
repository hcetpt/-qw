SPDX 许可证标识符: GFDL-1.1-no-invariants-or-later
.. c:namespace:: DTV.dmx

.. _DMX_STOP:

========
DMX_STOP
========

名称
----

DMX_STOP

概览
--------

.. c:macro:: DMX_STOP

``int ioctl(int fd, DMX_STOP)``

参数
---------

``fd``
    由 :c:func:`open()` 返回的文件描述符
描述
-----------

此 ioctl 调用用于停止通过 ioctl 调用 :ref:`DMX_SET_FILTER` 或 :ref:`DMX_SET_PES_FILTER` 定义并通过 :ref:`DMX_START` 命令启动的实际过滤操作。
返回值
------------

成功时返回 0
出错时返回 -1，并且设置 ``errno`` 变量为适当的错误码
通用错误码在 :ref:`通用错误码 <gen-errors>` 章节中描述。
