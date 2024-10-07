SPDX 许可声明标识符: GFDL-1.1-no-invariants-or-later
.. c:命名空间:: DTV.dmx

.. _DMX_REMOVE_PID:

==============
DMX_REMOVE_PID
==============

名称
----

DMX_REMOVE_PID

简介
--------

.. c:宏:: DMX_REMOVE_PID

``int ioctl(fd, DMX_REMOVE_PID, __u16 *pid)``

参数
---------

``fd``
    由 :c:func:`open()` 返回的文件描述符
``pid``
    要移除的 PES 过滤器的 PID
描述
-----------

此 ioctl 调用允许在传输流过滤器设置了多个 PID 的情况下移除一个 PID，例如，通过输出等于 :c:type:`DMX_OUT_TSDEMUX_TAP <dmx_output>` 的过滤器设置，该过滤器是通过 :ref:`DMX_SET_PES_FILTER` 或 :ref:`DMX_ADD_PID` 创建的。
返回值
------------

成功时返回 0
出错时返回 -1，并且设置 `errno` 变量为适当的值
通用错误代码在《通用错误代码 <gen-errors>` 章节中描述。
