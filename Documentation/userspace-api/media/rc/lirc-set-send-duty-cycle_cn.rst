.. 许可证标识符：GPL-2.0 或 GFDL-1.1-no-invariants-or-later
.. c:命名空间:: RC

.. _lirc_set_send_duty_cycle:

*******************************
ioctl LIRC_SET_SEND_DUTY_CYCLE
*******************************

名称
====

LIRC_SET_SEND_DUTY_CYCLE - 设置用于红外发射的载波信号占空比

概要
====

.. c:宏:: LIRC_SET_SEND_DUTY_CYCLE

``int ioctl(int fd, LIRC_SET_SEND_DUTY_CYCLE, __u32 *duty_cycle)``

参数
====

``fd``
    由open()返回的文件描述符
``duty_cycle``
    占空比，描述脉冲宽度占总周期的百分比（从1到99）。值0和100被保留

描述
====

获取/设置用于红外发射的载波信号的占空比
目前，对于0或100没有定义特殊含义，但这些值可能会在未来用于关闭载波生成，因此应保留这些值

返回值
====

成功时返回0，失败时返回-1，并且设置适当的``errno``变量。通用错误代码在“通用错误代码”章节中描述。
