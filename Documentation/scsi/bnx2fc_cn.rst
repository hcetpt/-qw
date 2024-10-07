SPDX 许可证标识符: GPL-2.0

===========================
使用 bnx2fc 运行 FCoE
===========================
通过 bnx2fc 实现的 Broadcom FCoE 卸载是完全的状态化硬件卸载，并且与 Linux 生态系统提供的所有 FC/FCoE 和 SCSI 控制器接口协同工作。因此，一旦启用 FCoE 功能，它基本上是透明的。在 SAN 上发现的设备将自动在上层存储中注册和注销。

尽管 Broadcom 的 FCoE 卸载是完全卸载的，但它依赖于网络接口的状态来运行。因此，与 FCoE 卸载启动程序关联的网络接口（例如 eth0）必须处于“开启”状态。建议将网络接口配置为在启动时自动启动。

此外，Broadcom FCoE 卸载解决方案会创建 VLAN 接口以支持已发现用于 FCoE 操作的 VLAN（例如 eth0.1001-fcoe）。请勿删除或禁用这些接口，否则会导致 FCoE 操作中断。

驱动程序使用模型：
===================

1. 确保安装了 fcoe-utils 软件包。
2. 配置 bnx2fc 驱动程序需要操作的接口。以下是配置步骤：

	a. cd /etc/fcoe
	b. 如果要在 eth5 上启用 FCoE，则将 cfg-ethx 复制为 cfg-eth5
	c. 对所有需要启用 FCoE 的接口重复此步骤
	d. 编辑所有 cfg-eth 文件，将 "DCB_REQUIRED" 字段设置为 "no"，并将 "AUTO_VLAN" 设置为 "yes"
e. 其他配置参数应保持默认设置

3. 确保“bnx2fc”包含在/etc/fcoe/config中的SUPPORTED_DRIVERS列表中
4. 启动fcoe服务。（service fcoe start）。如果系统中存在Broadcom设备，bnx2fc驱动会自动声明接口，开始VLAN发现并登录目标
5. 在"fcoeadm -i"输出中的“Symbolic Name”将显示bnx2fc是否已声明接口
例如：

 [root@bh2 ~]# fcoeadm -i
    描述:      NetXtreme II BCM57712 10千兆以太网
    版本:         01
    制造商:     Broadcom Corporation
    序列号:    0010186FD558
    驱动:           bnx2x 1.70.00-0
    端口数量:  2

        符号名称:     bnx2fc v1.0.5 over eth5.4
        操作系统设备名称:    host11
        节点名称:         0x10000010186FD559
        端口名称:         0x20000010186FD559
        Fabric名称:        0x2001000DECB3B681
        速度:             10 Gbit
        支持的速率:   10 Gbit
        最大帧大小:      2048
        FC-ID（端口ID）:   0x0F0377
        状态:             在线

6. 通过运行ifconfig验证VLAN发现是否已执行，并注意到<INTERFACE>.<VLAN>-fcoe接口已自动创建
有关fcoeadm操作的更多信息，包括创建/销毁接口或显示LUN/目标信息，请参阅fcoeadm手册页
注意
====
** Broadcom FCoE功能设备在芯片上实现了一个DCBX/LLDP客户端。每个接口只允许一个LLDP客户端。为了正常运行，所有基于主机软件的DCBX/LLDP客户端（例如lldpad）必须禁用。要禁用某个接口上的lldpad，请运行以下命令：

	lldptool set-lldp -i <interface_name> adminStatus=disabled
