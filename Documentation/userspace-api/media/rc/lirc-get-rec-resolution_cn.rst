SPDX 许可证标识符：GPL-2.0 或 GFDL-1.1-no-invariants-or-later
c:命名空间:: RC

.. _lirc_get_rec_resolution:

*******************************
ioctl LIRC_GET_REC_RESOLUTION
*******************************

名称
====

LIRC_GET_REC_RESOLUTION - 获取接收分辨率的值（以微秒为单位）

概要
====

.. c:宏:: LIRC_GET_REC_RESOLUTION

``int ioctl(int fd, LIRC_GET_REC_RESOLUTION, __u32 *microseconds)``

参数
====

``fd``
    由 open() 返回的文件描述符
``microseconds``
    分辨率，以微秒为单位

描述
====

某些接收器的最大分辨率由内部采样率或数据格式限制定义。例如，信号通常只能以50微秒为步长进行报告。
此 ioctl 返回表示此类分辨率的整数值，可以被用户空间应用程序（如 lircd）用于自动调整容差值。

返回值
======

成功时返回 0，失败时返回 -1，并且设置适当的 ``errno`` 变量。通用错误代码在“通用错误代码”章节中描述。
