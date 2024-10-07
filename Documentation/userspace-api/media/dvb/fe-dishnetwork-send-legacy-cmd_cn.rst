.. 许可证标识符：GFDL-1.1-no-invariants-or-later
.. c:命名空间:: DTV.fe

.. _FE_DISHNETWORK_SEND_LEGACY_CMD:

*******************************
FE_DISHNETWORK_SEND_LEGACY_CMD
*******************************

名称
====

FE_DISHNETWORK_SEND_LEGACY_CMD

概要
====

.. c:宏:: FE_DISHNETWORK_SEND_LEGACY_CMD

``int ioctl(int fd, FE_DISHNETWORK_SEND_LEGACY_CMD, unsigned long cmd)``

参数
====

``fd``
    由 :c:func:`open()` 返回的文件描述符。
``cmd``
    通过 DISEqC 将指定的原始命令发送到天线。

描述
====

.. 警告::
   这是一个非常罕见的遗留命令，仅在 stv0299 驱动程序中使用。不应用于较新的驱动程序。
该命令提供了一种非标准的方法来选择前端上的 DISEqC 电压，适用于 Dish Network 的遗留切换器。
由于对这个 ioctl 的支持是在 2004 年添加的，这意味着这些天线在 2004 年就已经是遗留设备了。

返回值
====

成功时返回 0。
失败时返回 -1，并且设置适当的 ``errno`` 变量。
通用错误代码在 :ref:`通用错误代码 <gen-errors>` 章节中有描述。
