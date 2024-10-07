.. 许可证标识符：GFDL-1.1-no-invariants-or-later
.. c:命名空间:: DTV.fe

.. _FE_DISEQC_RESET_OVERLOAD:

*******************************
ioctl FE_DISEQC_RESET_OVERLOAD
*******************************

名称
====

FE_DISEQC_RESET_OVERLOAD - 如果由于功率过载导致天线子系统断电，则恢复其供电

概要
====

.. c:宏:: FE_DISEQC_RESET_OVERLOAD

``int ioctl(int fd, FE_DISEQC_RESET_OVERLOAD, NULL)``

参数
====

``fd``
    由 :c:func:`open()` 返回的文件描述符

描述
====

如果总线因功率过载而自动断电，此 ioctl 调用将恢复总线的供电。该调用需要对设备具有读写访问权限。如果设备是手动断电的，此调用将不起作用。并非所有数字电视适配器都支持此 ioctl。

返回值
====

成功时返回 0
出错时返回 -1，并且设置 ``errno`` 变量为适当的错误码
通用错误码在《通用错误码 <gen-errors>` 章节中描述
