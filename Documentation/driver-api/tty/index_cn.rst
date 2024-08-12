### SPDX 许可证标识符：GPL-2.0

===
TTY
===

电传打字机（TTY）层负责处理所有的串行设备，包括像伪终端（PTY）这样的虚拟设备。
TTY 结构
==============

有几个主要的 TTY 结构。系统中的每个 TTY 设备都有一个对应的 `struct tty_port`。这些设备由一个 TTY 驱动程序维护，该驱动程序是 `struct tty_driver`。这个结构描述了驱动程序，同时也包含了可以对 TTY 执行的操作的引用，它是 `struct tty_operations`。在打开时，会分配一个 `struct tty_struct` 并一直存在到最终关闭。在这段时间里，`struct tty_operations` 中的几个回调会被 TTY 层调用。
内核接收到的每一个字符（无论是来自设备还是用户）都会通过预选的 [TTY 线律](doc:tty_ldisc)（简称 ldisc；在 C 语言中为 `struct tty_ldisc_ops`）。它的任务是根据特定的 ldisc 或用户的定义转换字符。默认的是 n_tty，实现了回显、信号处理、作业控制、特殊字符处理等。转换后的字符会进一步传递给用户/设备，这取决于来源。

关于上述提到的 TTY 结构的详细描述可以在以下单独文档中找到：

.. toctree::
   :maxdepth: 2

   tty_driver
   tty_port
   tty_struct
   tty_ldisc
   tty_buffer
   tty_ioctl
   tty_internals
   console

编写 TTY 驱动程序
==================

在开始编写 TTY 驱动程序之前，应该首先考虑 [串行](../serial/driver) 和 [USB 串行](../../usb/usb-serial) 层。对于串行设备的驱动程序，通常可以使用这些特定的层来实现串行驱动程序。只有特殊的设备才应该直接由 TTY 层处理。如果你打算编写这样的驱动程序，请继续阅读。
一个 *典型的* TTY 驱动程序执行的序列如下：

1. 分配并注册 TTY 驱动程序（模块初始化）
2. 在设备被探测到时创建并注册 TTY 设备（探测函数）
3. 处理 TTY 操作和事件，如中断（TTY 核心调用前者，设备触发后者）
4. 在设备消失时移除设备（移除函数）
5. 注销并释放 TTY 驱动程序（模块退出）

关于驱动程序本身，即第 1、3 和 5 步，在 [tty_driver](doc:tty_driver) 中有详细的描述。对于其他两步（设备处理），请参阅 [tty_port](doc:tty_port)。

其他文档
===================

其他杂项文档可以在以下文档中找到：

.. toctree::
   :maxdepth: 2

   moxa-smartio
   n_gsm
   n_tty
