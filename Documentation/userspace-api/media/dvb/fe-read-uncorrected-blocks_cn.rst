.. 许可证标识符：GFDL-1.1-no-invariants-or-later
.. c:命名空间:: DTV.fe

.. _FE_READ_UNCORRECTED_BLOCKS:

**************************
FE_READ_UNCORRECTED_BLOCKS
**************************

名称
====

FE_READ_UNCORRECTED_BLOCKS

.. 注意:: 此ioctl已弃用
概述
========

.. c:宏:: FE_READ_UNCORRECTED_BLOCKS

``int ioctl(int fd, FE_READ_UNCORRECTED_BLOCKS, uint32_t *ublocks)``

参数
=========

``fd``
    由 :c:func:`open()` 返回的文件描述符
``ublocks``
    驱动程序迄今为止看到的未纠正块总数
描述
===========

此ioctl调用返回设备驱动程序在其生命周期中检测到的未纠正块的数量。为了获得有意义的测量结果，应在特定时间间隔内计算块计数的增量。对于此命令，只需要对设备进行只读访问。
返回值
============

成功时返回0
出错时返回-1，并设置适当的 ``errno`` 变量
通用错误代码在“通用错误代码 <gen-errors>”章节中有描述
