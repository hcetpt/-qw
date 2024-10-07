SPDX 许可声明标识符: GFDL-1.1-no-invariants-or-later
.. c:命名空间:: DTV.dmx

.. _DMX_ADD_PID:

===========
DMX_ADD_PID
===========

名称
----

DMX_ADD_PID

概要
--------

.. c:宏:: DMX_ADD_PID

``int ioctl(fd, DMX_ADD_PID, __u16 *pid)``

参数
---------

``fd``
    由 :c:func:`open()` 返回的文件描述符
``pid``
    需要过滤的 PID 编号
描述
-----------

此 ioctl 调用允许向先前使用 :ref:`DMX_SET_PES_FILTER` 设置的传输流过滤器添加多个 PID，并且输出等于 :c:type:`DMX_OUT_TSDEMUX_TAP <dmx_output>`
返回值
------------

成功时返回 0
错误时返回 -1，并且设置 ``errno`` 变量为适当的值
通用错误代码在“通用错误代码”章节中有所描述 :ref:`Generic Error Codes <gen-errors>`
