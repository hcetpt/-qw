.. 许可证标识符: GPL-2.0 或 GFDL-1.1-no-invariants-or-later
.. c:命名空间:: RC

.. _lirc_get_min_timeout:
.. _lirc_get_max_timeout:

**************************************************
ioctl 命令 LIRC_GET_MIN_TIMEOUT 和 LIRC_GET_MAX_TIMEOUT
**************************************************

名称
====

LIRC_GET_MIN_TIMEOUT / LIRC_GET_MAX_TIMEOUT - 获取 IR 接收的可能超时范围

概要
====

.. c:宏:: LIRC_GET_MIN_TIMEOUT

``int ioctl(int fd, LIRC_GET_MIN_TIMEOUT, __u32 *timeout)``

.. c:宏:: LIRC_GET_MAX_TIMEOUT

``int ioctl(int fd, LIRC_GET_MAX_TIMEOUT, __u32 *timeout)``

参数
====

``fd``
    由 open() 返回的文件描述符
``timeout``
    超时时间，以微秒为单位

描述
====

某些设备具有内部计时器，可以用来检测长时间内没有 IR 活动的情况。这可以帮助 lircd 检测到 IR 信号已经结束，并加快解码过程。返回一个整数值，表示可以设置的最小/最大超时时间。
.. 注意::

   有些设备具有固定的超时时间，在这种情况下，
   即使超时时间不能通过 :ref:`LIRC_SET_REC_TIMEOUT` 更改，两个 ioctl 命令也会返回相同的值。

返回值
======

成功时返回 0，失败时返回 -1 并且设置适当的 ``errno`` 变量。通用错误代码在 :ref:`通用错误代码 <gen-errors>` 章节中进行了描述。
