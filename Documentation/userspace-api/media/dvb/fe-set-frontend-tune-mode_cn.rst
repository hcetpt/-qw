.. 许可证标识符: GFDL-1.1-no-invariants-or-later
.. c:命名空间:: DTV.fe

.. _FE_SET_FRONTEND_TUNE_MODE:

*******************************
ioctl FE_SET_FRONTEND_TUNE_MODE
*******************************

名称
====

FE_SET_FRONTEND_TUNE_MODE - 允许设置调谐器模式标志到前端

概述
========

.. c:宏:: FE_SET_FRONTEND_TUNE_MODE

``int ioctl(int fd, FE_SET_FRONTEND_TUNE_MODE, unsigned int flags)``

参数
=========

``fd``
    由 :c:func:`open()` 返回的文件描述符
``flags``
    有效的标志：

    -  0 - 正常调谐模式

    -  ``FE_TUNE_MODE_ONESHOT`` - 当设置此标志时，将禁用任何锯齿状或其他“正常”调谐行为。此外，不会自动监控锁定状态，因此不会生成前端事件。如果关闭了前端设备，在以读写方式重新打开设备时，此标志会自动关闭
描述
===========

允许在前端设置调谐器模式标志，范围从 0（正常）到 ``FE_TUNE_MODE_ONESHOT`` 模式

返回值
============

成功时返回 0
出错时返回 -1，并且设置 ``errno`` 变量为适当的值
通用错误代码在《通用错误代码 <gen-errors>` 章节中描述
