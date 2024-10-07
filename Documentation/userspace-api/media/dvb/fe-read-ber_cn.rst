.. 许可证标识符：GFDL-1.1-no-invariants-or-later
.. c:命名空间:: DTV.fe

.. _FE_READ_BER:

***********
FE_READ_BER
***********

名称
====

FE_READ_BER

.. 注意:: 此ioctl已废弃
概述
========

.. c:宏:: FE_READ_BER

``int ioctl(int fd, FE_READ_BER, uint32_t *ber)``

参数
=========

``fd``
    由 :c:func:`open()` 返回的文件描述符
``ber``
    比特错误率将被存储到 \*ber 中
描述
===========

此ioctl调用返回当前由前端接收/解调的信号的比特错误率。对于此命令，设备的只读访问权限就足够了。
返回值
============

成功时返回0
出错时返回-1，并且设置 ``errno`` 变量为适当的值
通用错误代码在《通用错误代码 <gen-errors>` 章节中描述。
