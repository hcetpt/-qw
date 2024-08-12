低级串行API
=============

本文档旨在简要概述新串行驱动程序的某些方面。它并不完整，如有任何疑问，请联系<rmk@arm.linux.org.uk>。

参考实现包含在amba-pl011.c中
低级串行硬件驱动程序
----------------------------------

低级串行硬件驱动程序负责向核心串行驱动程序提供端口信息（由uart_port定义）和一组控制方法（由uart_ops定义）。低级驱动程序还负责处理端口的中断，并提供任何控制台支持。
控制台支持
--------------

串行核心提供了一些辅助函数。这包括识别正确的端口结构（通过uart_get_console()）和解析命令行参数（uart_parse_options()）。
还有一个辅助函数（uart_console_write()），它执行逐字符写入，将换行符转换为CRLF序列。
建议驱动程序编写者使用此函数而不是实现自己的版本。
锁定
-------

低级硬件驱动程序有责任使用port->lock进行必要的锁定。有一些例外（如下文struct uart_ops列表中所述）。
有两种锁：每个端口的自旋锁和总体信号量。
从核心驱动程序的角度来看，port->lock锁定了以下数据：
- port->mctrl
- port->icount
- port->state->xmit.head (circ_buf->head)
- port->state->xmit.tail (circ_buf->tail)
低级驱动程序可以自由使用此锁来提供任何额外的锁定。
端口信号量用于防止端口在不适当的时间被添加/删除或重新配置。自v2.6.27以来，该信号量一直是tty_port结构的'mutex'成员，并通常称为端口互斥锁。
uart_ops
--------

.. kernel-doc:: include/linux/serial_core.h
   :identifiers: uart_ops

其他函数
--------------

.. kernel-doc:: drivers/tty/serial/serial_core.c
   :identifiers: uart_update_timeout uart_get_baud_rate uart_get_divisor 
           uart_match_port uart_write_wakeup uart_register_driver
           uart_unregister_driver uart_suspend_port uart_resume_port
           uart_add_one_port uart_remove_one_port uart_console_write
           uart_parse_earlycon uart_parse_options uart_set_options
           uart_get_lsr_info uart_handle_dcd_change uart_handle_cts_change
           uart_try_toggle_sysrq uart_get_console

.. kernel-doc:: include/linux/serial_core.h
   :identifiers: uart_port_tx_limited uart_port_tx

其他说明
-------------

计划将来删除uart_port中的“未使用”条目，并允许低级驱动程序以其自己的个别uart_port注册到核心。这样可以让驱动程序使用uart_port作为指向包含uart_port条目及其自身扩展的结构的指针，例如：

```c
struct my_port {
    struct uart_port port;
    int my_stuff;
};
```

通过GPIO设置/获取调制解调器控制线
------------------------------

为了通过GPIO设置/获取调制解调器控制线，提供了一些帮助函数。
.. kernel-doc:: drivers/tty/serial/serial_mctrl_gpio.c
   :identifiers: mctrl_gpio_init mctrl_gpio_free mctrl_gpio_to_gpiod
           mctrl_gpio_set mctrl_gpio_get mctrl_gpio_enable_ms
           mctrl_gpio_disable_ms
