SPDX 许可证标识符: GPL-2.0

============
Rmnet 驱动程序
============

1. 引言
===============

Rmnet 驱动程序用于支持复用与聚合协议 (MAP)。该协议被所有近期使用高通技术公司调制解调器的芯片组所采用。
此驱动程序可以用于在任何物理网络设备上以 IP 模式进行注册。物理传输方式包括 USB、HSIC、PCIe 和 IP 加速器。
复用允许创建逻辑网卡（rmnet 设备）来处理多个私有数据网络 (PDN)，如默认互联网、共享热点、多媒体信息服务 (MMS) 或 IP 多媒体子系统 (IMS)。硬件发送带有 MAP 标头的数据包到 rmnet，根据复用器ID，rmnet 在移除 MAP 标头后将数据路由到相应的 PDN。
为了实现高速数据传输，需要聚合。这涉及到硬件发送一组聚合的 MAP 帧。Rmnet 驱动程序会分解这些 MAP 帧，并将其发送到相应的 PDN。

2. 数据包格式
================

a. MAP 数据包版本 1（数据/控制）

MAP 标头字段采用大端字节序。
数据包格式如下所示：

  位             0             1           2-7      8-15           16-31
  功能   命令 / 数据   保留     填充   复用器 ID    载荷长度

  位            32-x
  功能      原始字节

命令 (1)/ 数据 (0) 位值用于指示数据包是 MAP 命令还是数据包。命令数据包用于传输级别的流量控制。数据包是标准的 IP 数据包。
保留位在发送时必须为零，在接收时会被忽略。
填充是指附加到载荷末尾的字节数，以确保 4 字节对齐。
复用器 ID 用于指示数据要发送的 PDN。
载荷长度包含填充长度，但不包括 MAP 标头长度。
b. MAP 数据包 v4（数据/控制）

MAP 标头字段采用大端格式。
数据包格式如下：

  位             0             1           2-7      8-15           16-31
  功能   命令/数据   保留       填充   复用器ID    负载长度

  位            32-(x-33)      (x-32)-x
  功能      原始字节      校验和卸载标头

命令(1)/ 数据(0) 位的值用于指示该数据包是 MAP 命令还是数据包。命令数据包用于传输层的流量控制。数据包为标准的 IP 数据包。
保留位在发送时必须为零，在接收时会被忽略。
填充是指附加到负载的字节数量，以确保对齐为 4 字节。
复用器ID用于指示要发送数据的 PDN（分组数据网络）。
负载长度包括了填充长度，但不包括 MAP 标头的长度。
校验和卸载标头包含了硬件执行的校验和处理的信息。校验和卸载标头字段采用大端格式。
数据包格式如下：

  位             0-14        15              16-31
  功能      保留   有效     校验和起始偏移

  位                31-47                    48-64
  功能      校验和长度           校验和值

保留位在发送时必须为零，在接收时会被忽略。
有效位表示部分校验和是否已被计算并且有效。
如果有效，则设置为 1。否则，设置为 0。
填充是指附加到有效载荷末尾的字节数，以确保4字节对齐。
校验和起始偏移量表示从IP头开始处计算调制解调器校验和的偏移量（以字节为单位）。
校验和长度是从CKSUM_START_OFFSET开始的字节数，用于计算校验和的范围。
校验和值表示计算出的校验和值。
c. MAP数据包v5（数据/控制）

MAP头部字段采用大端格式。
数据包格式如下：

  位             0             1         2-7      8-15           16-31
  功能   命令/数据  下一个头部  填充   复用器ID   有效载荷长度

  位            32-x
  功能      原始字节

命令（1）/ 数据（0）位值用于指示数据包是MAP命令还是数据包。命令包用于传输层流量控制。数据包是标准的IP数据包。
下一个头部用于指示另一个头部的存在，目前仅限于校验和头部。
填充是指附加到有效载荷末尾的字节数，以确保4字节对齐。
复用器ID用于指示要发送数据的PDN。
有效载荷长度包括填充长度，但不包括MAP头部长度。
d. 校验和卸载头版本5

校验和卸载头字段采用大端格式。
比特            0 - 6          7               8-15              16-31
  功能     头类型    下一头部     校验和有效    保留

头类型用于指示头的类型，这通常被设置为CHECKSUM。

头类型
= ==========================================
0 保留
1 保留
2 校验和头

校验和有效用于指示头部校验和是否有效。值为1表示该包上的校验和已计算且有效，值为0表示计算出的包校验和无效。
保留位在发送时必须置零，在接收时忽略。
e. MAP数据包v1/v5（特定于命令）::

    比特             0             1         2-7      8 - 15           16 - 31
    功能   命令         保留     填充   复用器ID    载荷长度
    比特          32 - 39        40 - 45    46 - 47       48 - 63
    功能   命令名称    保留   命令类型   保留
    比特          64 - 95
    功能   交易ID
    比特          96 - 127
    功能   命令数据

命令1表示禁用流而2表示启用流

命令类型

= ==========================================
0 用于MAP命令请求
1 用于确认收到命令
2 用于不支持的命令
3 用于处理命令期间出现的错误
= ==========================================

f. 聚合

聚合是指多个MAP数据包（可以是数据或命令）以单个线性skb的形式传递给rmnet。rmnet将处理各个数据包，并根据需要要么确认MAP命令，要么将IP数据包交付给网络栈。

MAP头|IP数据包|可选填充|MAP头|IP数据包|可选填充...
MAP头|IP数据包|可选填充|MAP头|命令数据包|可选填充..
3. 用户空间配置
==========================

rmnet用户空间配置通过iproute2使用netlink实现
https://git.kernel.org/pub/scm/network/iproute2/iproute2.git/

驱动程序使用rtnl_link_ops进行通信
