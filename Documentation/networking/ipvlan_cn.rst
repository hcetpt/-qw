SPDX许可证标识符: GPL-2.0

===================
IPVLAN驱动程序HOWTO
===================

初始发布：
Mahesh Bandewar <maheshb AT google.com>

1. 介绍：
================
概念上，这与macvlan驱动程序非常相似，唯一的重大区别在于使用L3进行从属设备之间的复用/解复用。这一特性使得主设备与其从属设备共享二层（L2）。我是在网络命名空间的基础上开发此驱动程序的，并不确定其是否有其他应用场景。

2. 构建和安装：
=============================
为了构建该驱动程序，请选择配置项CONFIG_IPVLAN。
该驱动程序可以构建到内核中（CONFIG_IPVLAN=y），也可以作为一个模块构建（CONFIG_IPVLAN=m）。

3. 配置：
=================
该驱动程序没有模块参数，可以使用IProute2/ip工具进行配置。
::

    ip link add link <master> name <slave> type ipvlan [ mode MODE ] [ FLAGS ]
       其中
	 MODE: l3（默认）| l3s | l2
	 FLAGS: bridge（默认）| private | vepa

例如：
(a) 下面的命令将创建一个以eth0为主设备的L3桥接模式下的IPvlan链路::

	  bash# ip link add link eth0 name ipvl0 type ipvlan

(b) 此命令将创建一个L2桥接模式下的IPvlan链路::

	  bash# ip link add link eth0 name ipvl0 type ipvlan mode l2 bridge

(c) 此命令将创建一个L2私有模式下的IPvlan设备::

	  bash# ip link add link eth0 name ipvlan type ipvlan mode l2 private

(d) 此命令将创建一个L2 vepa模式下的IPvlan设备::

	  bash# ip link add link eth0 name ipvlan type ipvlan mode l2 vepa

4. 工作模式：
==================

IPvlan有两种工作模式：L2和L3。对于给定的主设备，您可以选择这两种模式之一，且该主设备上的所有从属设备都将运行在所选模式下。L3模式下接收模式几乎相同，只是从属设备不会接收任何组播或广播流量。L3模式更为严格，因为路由通常由另一个（通常是默认的）命名空间控制。

4.1 L2模式：
------------

在此模式下，发送处理发生在与从属设备关联的堆栈实例上，并且数据包被切换并排队到主设备以发送出去。在此模式下，从属设备将接收和发送组播和广播（如果适用）。

4.2 L3模式：
------------

在此模式下，发送处理直到第三层都在与从属设备关联的堆栈实例上完成，然后数据包被切换到主设备的堆栈实例进行第二层处理和路由，之后再将数据包排队到出站设备。在此模式下，从属设备不会接收也不会发送组播或广播流量。

4.3 L3S模式：
-------------

这与L3模式非常相似，不同之处在于在此模式下iptables（连接跟踪）有效，因此它是L3对称的（L3s）。这会稍微降低一些性能，但不应影响您选择此模式而不是纯L3模式来使连接跟踪生效。
5. 模式标志：
==============

目前可用的模式标志如下：

5.1 桥接模式：
-----------
这是默认选项。要在此模式下配置IPvlan端口，用户可以选择在命令行中添加此选项或不指定任何内容。这是传统模式，在此模式下，从设备之间可以互相通信，除了通过主设备进行通信。

5.2 私有模式：
------------
如果在命令行中添加了此选项，则端口将设置为私有模式，即端口不允许从设备之间的交叉通信。

5.3 VEPA模式：
---------
如果在命令行中添加了此选项，则端口将设置为VEPA模式，即端口将802.1Qbg中描述的功能卸载到外部实体。
注意：IPvlan中的VEPA模式存在局限性。IPvlan使用主设备的MAC地址，因此在此模式下发出的相邻邻居数据包的源和目的MAC地址相同。这将导致交换机/路由器发送重定向消息。

6. 如何选择（macvlan与ipvlan）？
=======================================

这两种设备在很多方面非常相似，具体的使用场景可能会决定选择哪种设备。如果以下情况之一符合您的使用场景，则可以选择使用ipvlan：

(a) 连接到外部交换机/路由器的Linux主机配置了策略，每个端口只允许一个MAC地址。
(b) 在主设备上创建的虚拟设备数量超过了MAC容量，并且将NIC置于混杂模式，性能下降是一个问题。
(c) 如果需要将从设备置于敌对/不可信的网络命名空间中，其中L2可能会被更改/滥用。

6. 示例配置：
=========================

::

  +=============================================================+
  |  主机: host1                                                |
  |                                                             |
  |   +----------------------+      +----------------------+    |
  |   |   命名空间:ns0            |      |  命名空间:ns1           |    |
  |   |                        |      |                        |    |
  |   |                        |      |                        |    |
  |   |         ipvl0          |      |         ipvl1           |    |
  |   +----------#-------------+      +-----------#------------+    |
  |              #                                #                |
  |              ################################                |
  |                              # eth0                           |
  +==============================#===============================+

(a) 创建两个网络命名空间 - ns0, ns1::
	
	ip netns add ns0
	ip netns add ns1

(b) 在eth0（主设备）上创建两个ipvlan从设备::

	ip link add link eth0 ipvl0 type ipvlan mode l2
	ip link add link eth0 ipvl1 type ipvlan mode l2

(c) 将从设备分配给相应的网络命名空间::

	ip link set dev ipvl0 netns ns0
	ip link set dev ipvl1 netns ns1

(d) 现在切换到命名空间（ns0或ns1）以配置从设备

	- 对于ns0::

		(1) ip netns exec ns0 bash
		(2) ip link set dev ipvl0 up
		(3) ip link set dev lo up
		(4) ip -4 addr add 127.0.0.1 dev lo
		(5) ip -4 addr add $IPADDR dev ipvl0
		(6) ip -4 route add default via $ROUTER dev ipvl0

	- 对于ns1::

		(1) ip netns exec ns1 bash
		(2) ip link set dev ipvl1 up
		(3) ip link set dev lo up
		(4) ip -4 addr add 127.0.0.1 dev lo
		(5) ip -4 addr add $IPADDR dev ipvl1
		(6) ip -4 route add default via $ROUTER dev ipvl1
