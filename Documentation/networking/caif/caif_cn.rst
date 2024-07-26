SPDX 许可证标识符: GPL-2.0
.. include:: <isonum.txt>

================
使用 Linux CAIF
================

:版权所有: |copy| ST-Ericsson AB 2010

:作者: Sjur Brendeland/ sjur.brandeland@stericsson.com

开始
=====

如果您已经为模块编译了 CAIF，请执行以下命令：

    $ modprobe crc_ccitt
    $ modprobe caif
    $ modprobe caif_socket
    $ modprobe chnl_net

与 STE 调制解调器一起准备设置
====================================

如果您正在对 CAIF 进行集成工作，您应该确保内核是带有模块支持构建的。
有一些事情需要调整才能正确设置主机 TTY 来与调制解调器通信。
由于 CAIF 栈在内核中运行，并且我们想要使用现有的 TTY，我们将物理串行驱动程序作为 TTY 设备之上的行纪律来安装。
为了实现这一点，我们需要从用户空间安装 N_CAIF 行纪律。
好处是我们可以连接到任何 TTY。
帧起始扩展 (STX) 的使用也应作为模块参数 "ser_use_stx" 设置。
通常情况下，UART 上总是使用帧校验和，但这也作为一个模块参数 "ser_use_fcs" 提供。
执行以下命令：

    $ modprobe caif_serial ser_ttyname=/dev/ttyS0 ser_use_stx=yes
    $ ifconfig caif_ttyS0 up

请注意：
		Android 命令行有一个限制，
它只接受一个参数给 insmod/modprobe！

故障排除
================

对于串行通信提供了一些 debugfs 参数
/sys/kernel/debug/caif_serial/<tty-name>/ 

* ser_state: 打印位掩码状态，其中

  - 0x02 意味着 SENDING，这是一个过渡状态
- 0x10 表示 FLOW_OFF_SENT，即前一帧尚未发送
    并且阻碍了进一步的发送操作。流量关闭已传播
    到使用此 TTY 的所有 CAIF 通道。
* tty_status: 打印位掩码形式的 tty 状态信息

  - 0x01 - tty->warned 已启用
- 0x04 - tty->packed 已启用
- 0x08 - tty->flow.tco_stopped 已启用
- 0x10 - tty->hw_stopped 已启用
- 0x20 - tty->flow.stopped 已启用
* last_tx_msg: 二进制数据块，打印最后发送的帧
这可以通过以下命令打印出来：

	$ od --format=x1 /sys/kernel/debug/caif_serial/<tty>/last_rx_msg
最初发送的两个消息如下所示。注意：初始
  字节 02 是帧起始扩展 (STX)，用于错误时的重新同步
- 枚举消息示例:

        0000000  02 05 00 00 03 01 d2 02
                 |  |     |  |  |  |
                 STX(1)   |  |  |  |
                    长度(2)  |  |  |
                          控制信道(1)
                             命令: 枚举(1)
                                链路ID(1)
                                    校验和(2)

  - 信道设置消息示例:

        0000000  02 07 00 00 00 21 a1 00 48 df
                 |  |     |  |  |  |  |  |
                 STX(1)   |  |  |  |  |  |
                    长度(2)  |  |  |  |  |
                          控制信道(1)
                             命令: 信道设置(1)
                                信道类型(1)
                                    优先级和链路ID(1)
                                      终端(1)
                                          校验和(2)
* last_rx_msg: 打印最后接收的帧
LinkSetup的接收（RX）消息看起来几乎相同，但它们在命令位中设置了0x20位，而Channel Setup在Checksum之前添加了一个包含Channel ID的字节。

注释：
多个CAIF消息可能会被串联起来。调试缓冲区的最大大小为128字节。

错误场景
=========

- `last_tx_msg` 包含 Channel Setup 消息，而 `last_rx_msg` 是空的 -> 主机似乎能够通过UART发送消息，至少CAIF层协议会收到发送完成的通知。
- `last_tx_msg` 包含枚举消息，而 `last_rx_msg` 是空的 -> 主机无法通过UART发送该消息，即串行终端未能完成发送操作。
- 如果 `/sys/kernel/debug/caif_serial/<tty>/tty_status` 的值非零，则可能存在通过UART传输的问题。
例如：主机和调制解调器之间的连线不正确时，你通常会看到 `tty_status = 0x10`（硬件停止） 和 `ser_state = 0x10`（FLOW_OFF_SENT）。
此时，你可能在 `last_tx_message` 中看到枚举消息，而 `last_rx_message` 为空。
