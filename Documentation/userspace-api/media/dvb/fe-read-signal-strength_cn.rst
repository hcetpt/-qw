.. 许可证标识符：GFDL-1.1-no-invariants-or-later
.. C 命名空间:: DTV.fe

.. _FE_READ_SIGNAL_STRENGTH:

**************************
FE_READ_SIGNAL_STRENGTH
**************************

名称
====

FE_READ_SIGNAL_STRENGTH

.. 注意:: 此 ioctl 已弃用
概述
========

.. C 宏:: FE_READ_SIGNAL_STRENGTH

``int ioctl(int fd, FE_READ_SIGNAL_STRENGTH, uint16_t *strength)``

参数
=========

``fd``
    由 :c:func:`open()` 返回的文件描述符
``strength``
    信号强度值存储到 \*strength 中
描述
===========

此 ioctl 调用返回前端当前接收到的信号的信号强度值。对于此命令，仅需要对设备的只读访问权限。
返回值
============

成功时返回 0
出错时返回 -1，并设置 ``errno`` 变量为适当的错误码
通用错误码在《通用错误码 <gen-errors>` 章节中有描述
