### SPDX 许可证标识符：GPL-2.0

===================
IPVLAN 驱动程序 HOWTO
===================

初始发布：
Mahesh Bandewar <maheshb AT google.com>

1. 引言：
================
从概念上讲，这与macvlan驱动程序非常相似，但有一个主要的区别是使用L3进行主设备和从设备之间的复用/解复用。这一特性使得主设备可以与其从设备共享第二层（L2）。我是在网络命名空间的背景下开发这个驱动程序的，并不确定它是否有其他应用场景。
2. 构建和安装：
=============================

为了构建该驱动程序，请选择配置项 CONFIG_IPVLAN。该驱动程序可以编译进内核（CONFIG_IPVLAN=y）或作为一个模块（CONFIG_IPVLAN=m）。
3. 配置：
=================

该驱动程序没有模块参数，可以通过 IP 路由工具（ip utility）进行配置：
```
ip link add link <master> name <slave> type ipvlan [ mode MODE ] [ FLAGS ]
```
其中，
MODE: l3（默认）| l3s | l2
FLAGS: bridge（默认）| private | vepa

示例：
(a) 下面的命令将创建一个以eth0为主设备的L3桥接模式的IPvlan链接：
```
bash# ip link add link eth0 name ipvl0 type ipvlan
```
(b) 这条命令将创建一个L2桥接模式的IPvlan链接：
```
bash# ip link add link eth0 name ipvl0 type ipvlan mode l2 bridge
```
(c) 这条命令将创建一个L2私有模式的IPvlan设备：
```
bash# ip link add link eth0 name ipvlan type ipvlan mode l2 private
```
(d) 这条命令将创建一个L2 vepa模式的IPvlan设备：
```
bash# ip link add link eth0 name ipvlan type ipvlan mode l2 vepa
```

4. 工作模式：
===================

IPvlan有两种工作模式：L2 和 L3。对于给定的主设备，可以选择这两种模式之一，而该主设备上的所有从设备都将工作在所选模式下。接收模式几乎相同，但在L3模式下，从设备不会接收任何多播或广播流量。L3模式更为严格，因为路由通常受制于其他（大多数情况下为默认）命名空间。
4.1 L2 模式：
--------------

在这种模式下，发送处理发生在与从设备关联的堆栈实例中，数据包被交换并排队到主设备以进行发送。在这种模式下，从设备也将接收和发送多播和广播数据（如果适用）。
4.2 L3 模式：
--------------

在这种模式下，直到第三层（L3）的发送处理都在与从设备关联的堆栈实例中完成，然后数据包被交换到主设备的堆栈实例进行第二层（L2）处理和路由，之后数据包会被排队到出站设备。在这种模式下，从设备既不会接收也不会发送多播或广播流量。
4.3 L3S 模式：
--------------

这与L3模式非常相似，不同之处在于在这个模式下iptables（连接跟踪）可以正常工作，因此它是第三层对称的（L3-symmetric 或 L3s）。这将稍微降低一些性能，但这并不重要，因为你选择此模式而非普通的L3模式是为了让连接跟踪功能生效。
### 5. 模式标志：

#### 5.1 桥接模式：
这是默认选项。要在这种模式下配置IPvlan端口，用户可以选择在命令行中添加此选项或不指定任何内容。这是传统模式，在这里从属设备之间可以互相通信，除了通过主设备进行通信之外。

#### 5.2 私有模式：
如果在命令行中添加了此选项，则端口将设置为私有模式，即端口不允许从属设备之间的交叉通信。

#### 5.3 VEPA模式：
如果在命令行中添加了此选项，则端口将设置为VEPA模式，即端口会将交换功能卸载到外部实体，如802.1Qbg中所描述的。
**注意：** 在IPvlan中的VEPA模式存在局限性。IPvlan使用主设备的MAC地址，因此在这种模式下发出的相邻邻居的包会有相同的源和目的MAC地址。这会导致交换机/路由器发送重定向消息。

### 6. 如何选择（macvlan与ipvlan）？

这两种设备在很多方面都非常相似，具体使用场景可能会决定应该选择哪种设备。如果以下情况之一符合您的使用场景，则您可以选择使用ipvlan：

- (a) 连接到外部交换机/路由器的Linux主机上配置了只允许每个端口一个MAC地址的策略。
- (b) 在主设备上创建的虚拟设备数量超过了MAC容量，并且使NIC处于混杂模式，而性能下降是一个问题。
- (c) 如果需要将从属设备置于不信任/敌对的网络命名空间中，在这里L2层可能会被篡改或误用。

### 6. 示例配置：

```
+=============================================================+
|  主机: host1                                                |
|                                                             |
|   +----------------------+      +----------------------+    |
|   |   命名空间:ns0             |      |  命名空间:ns1              |    |
|   |                      |      |                      |    |
|   |                      |      |                      |    |
|   |        ipvl0         |      |         ipvl1        |    |
|   +----------#-----------+      +-----------#----------+    |
|              #                              #               |
|              ################################               |
|                              # eth0                         |
+==============================#==============================+
```

- (a) 创建两个网络命名空间 - ns0, ns1:

  ```
  ip netns add ns0
  ip netns add ns1
  ```

- (b) 在eth0（主设备）上创建两个ipvlan从属设备:

  ```
  ip link add link eth0 ipvl0 type ipvlan mode l2
  ip link add link eth0 ipvl1 type ipvlan mode l2
  ```

- (c) 将从属设备分配给相应的网络命名空间:

  ```
  ip link set dev ipvl0 netns ns0
  ip link set dev ipvl1 netns ns1
  ```

- (d) 现在切换到命名空间（ns0或ns1）以配置从属设备

  - 对于ns0:

    1. `ip netns exec ns0 bash`
    2. `ip link set dev ipvl0 up`
    3. `ip link set dev lo up`
    4. `ip -4 addr add 127.0.0.1 dev lo`
    5. `ip -4 addr add $IPADDR dev ipvl0`
    6. `ip -4 route add default via $ROUTER dev ipvl0`

  - 对于ns1:

    1. `ip netns exec ns1 bash`
    2. `ip link set dev ipvl1 up`
    3. `ip link set dev lo up`
    4. `ip -4 addr add 127.0.0.1 dev lo`
    5. `ip -4 addr add $IPADDR dev ipvl1`
    6. `ip -4 route add default via $ROUTER dev ipvl1`
