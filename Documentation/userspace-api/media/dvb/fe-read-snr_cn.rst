.. 许可证标识符：GFDL-1.1-no-invariants-or-later
.. c:命名空间:: DTV.fe

.. _FE_READ_SNR:

***********
FE_READ_SNR
***********

名称
====

FE_READ_SNR

.. 注意:: 此ioctl已废弃
概述
========

.. c:宏:: FE_READ_SNR

``int ioctl(int fd, FE_READ_SNR, int16_t *snr)``

参数
=========

``fd``
    由 :c:func:`open()` 返回的文件描述符
``snr``
    信噪比存储到 \*snr 中
描述
===========

此ioctl调用返回前端当前接收到的信号的信噪比。对于此命令，只读访问设备就足够了。
返回值
============

成功时返回0
错误时返回-1，并且设置相应的 ``errno`` 变量
通用错误代码在“通用错误代码”章节中描述 (:ref:`Generic Error Codes <gen-errors>`)
