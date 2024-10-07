.. SPDX-License-Identifier: GPL-2.0
.. include:: <isonum.txt>

================
使用 Linux CAIF
================

:版权: |copy| ST-Ericsson AB 2010

:作者: Sjur Brendeland / sjur.brandeland@stericsson.com

开始
=====

如果您已经为模块编译了 CAIF，请执行以下命令：

    $ modprobe crc_ccitt
    $ modprobe caif
    $ modprobe caif_socket
    $ modprobe chnl_net

使用 STE 调制解调器进行设置准备
====================================

如果您正在集成 CAIF，您应该确保内核支持模块。
有些设置需要调整以正确配置与调制解调器通信的主机 TTY。
由于 CAIF 栈在内核中运行，并且我们希望使用现有的 TTY，我们将物理串行驱动程序作为 TTY 设备之上的线路纪律安装。
为了实现这一点，我们需要从用户空间安装 N_CAIF 线路纪律。
这样做的好处是我们可以连接到任何 TTY。
帧起始扩展（STX）的使用也必须设置为模块参数 "ser_use_stx"。
通常情况下，UART 上总是使用帧校验和，但这也可以通过模块参数 "ser_use_fcs" 提供。

    $ modprobe caif_serial ser_ttyname=/dev/ttyS0 ser_use_stx=yes
    $ ifconfig caif_ttyS0 up

请注意：
        Android shell 存在一个限制，
它只接受一个参数给 insmod/modprobe！

故障排除
================

提供了用于串行通信的 debugfs 参数
/sys/kernel/debug/caif_serial/<tty-name>/ 

* ser_state: 打印位掩码状态，其中

  - 0x02 表示发送中，这是一个瞬时状态
* 0x10 表示 FLOW_OFF_SENT，即前一帧尚未发送，并且阻止了进一步的发送操作。FLOW OFF 已经传播到使用此 TTY 的所有 CAIF 通道。
* tty_status: 打印位掩码形式的 tty 状态信息
  - 0x01 - tty->warned 设置
  - 0x04 - tty->packed 设置
  - 0x08 - tty->flow.tco_stopped 设置
  - 0x10 - tty->hw_stopped 设置
  - 0x20 - tty->flow.stopped 设置
* last_tx_msg: 打印最后发送的帧的二进制数据
  可以通过以下命令打印：

  ```
  $ od --format=x1 /sys/kernel/debug/caif_serial/<tty>/last_rx_msg
  ```

  最初发送的两个 TX 消息如下所示。注意：初始字节 02 是帧开始扩展（STX），用于在错误时重新同步。
  - 枚举帧:

        0000000  02 05 00 00 03 01 d2 02
                 |  |     |  |  |  |
                 STX(1)   |  |  |  |
                    长度(2)  |  |  |
                          控制信道(1)
                             命令: 枚举(1)
                                链路ID(1)
                                    校验和(2)

  - 信道设置帧:

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
针对LinkSetup的RX消息看起来几乎相同，但它们在命令位中设置了0x20位，并且Channel Setup在Checksum之前添加了一个包含Channel ID的字节。

注意：
多个CAIF消息可能会被串联。调试缓冲区的最大大小为128字节。

错误场景
=================

- last_tx_msg包含Channel Setup消息而last_rx_msg为空 -> 主机似乎能够通过UART发送数据，至少CAIF ldisc会收到发送完成的通知。
- last_tx_msg包含枚举消息而last_rx_msg为空 -> 主机无法通过UART发送消息，终端未能完成发送操作。
- 如果/sys/kernel/debug/caif_serial/<tty>/tty_status非零，则可能存在通过UART传输的问题。
例如，主机和调制解调器的连线不正确时，通常会看到tty_status = 0x10（hw_stopped）和ser_state = 0x10（FLOW_OFF_SENT）。
你可能在last_tx_message中看到枚举消息，而last_rx_message为空。
