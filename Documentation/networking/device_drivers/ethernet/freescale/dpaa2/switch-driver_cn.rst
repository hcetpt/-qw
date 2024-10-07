.. SPDX 许可证标识符: GPL-2.0
.. include:: <isonum.txt>

===================
DPAA2 交换机驱动程序
===================

:版权: |copy| 2021 NXP

DPAA2 交换机驱动程序会在数据路径交换（DPSW）对象上进行探测，该对象可以在以下 DPAA2 系统芯片及其变体上实例化：LS2088A 和 LX2160A。该驱动程序使用交换设备驱动模型，并将每个交换端口暴露为一个网络接口，该接口可以包含在网桥中或作为独立接口使用。端口之间的流量切换被卸载到硬件中。
DPSW 可以有连接到 DPNIs 或 DPMACs 的端口用于外部访问。

::

         [ethA]     [ethB]      [ethC]     [ethD]     [ethE]     [ethF]
            :          :          :          :          :          :
            :          :          :          :          :          :
       [dpaa2-eth]  [dpaa2-eth]  [              dpaa2-switch              ]
            :          :          :          :          :          :        内核
       =============================================================================
            :          :          :          :          :          :        硬件
         [DPNI]      [DPNI]     [============= DPSW =================]
            |          |          |          |          |          |
            |           ----------           |       [DPMAC]    [DPMAC]
             -------------------------------            |          |
                                                        |          |
                                                      [PHY]      [PHY]

创建以太网交换机
===========================

dpaa2-switch 驱动程序会在 fsl-mc 总线上找到的 DPSW 设备上进行探测。这些设备可以通过启动时配置文件——DataPath Layout (DPL)——静态创建，或者使用 DPAA2 对象 API 在运行时创建（已经集成到 restool 用户空间工具中）。目前，dpaa2-switch 驱动程序对它将要探测的 DPSW 对象施加了以下限制：

* 最少的 FDB 数量应该至少等于交换接口的数量。这是必要的，以便分离交换端口，即当不在网桥下时，每个交换端口将有自己的 FDB。
::

        fsl_dpaa2_switch dpsw.0: FDB 数量低于端口数量，无法探测

* 广播和洪泛配置应该是按 FDB 进行的。这使得驱动程序能够根据共享 FDB 的交换端口（即在同一网桥下）来限制每个 FDB 的广播和洪泛域。
::

        fsl_dpaa2_switch dpsw.0: 洪泛域不是按 FDB 的，无法探测
        fsl_dpaa2_switch dpsw.0: 广播域不是按 FDB 的，无法探测

* 交换机的控制接口不应被禁用（DPSW_OPT_CTRL_IF_DIS 不应作为创建时的选项传递）。没有控制接口，驱动程序无法在交换端口的 netdevice 上提供适当的 Rx/Tx 流量支持。
::

        fsl_dpaa2_switch dpsw.0: 控制接口已禁用，无法探测

除了实际的 DPSW 对象配置之外，dpaa2-switch 驱动程序还需要以下 DPAA2 对象：

* 1个 DPMCP —— 需要一个管理命令门户对象来进行与 MC 固件的任何交互。
* 1个 DPBP —— 缓冲池用于为控制接口上的接收路径提供缓冲。
* 至少需要访问一个 DPIO 对象（软件门户），以便在控制接口队列上执行任何入队/出队操作。
DPIO 对象将被共享，无需私有对象。

切换功能
=================

驱动程序支持在硬件中配置 L2 转发规则以进行端口桥接以及独立使用独立交换接口。硬件不支持 VLAN 意识，因此任何 DPAA2 交换端口仅应在具有 VLAN 意识的桥接场景中使用：
```
$ ip link add dev br0 type bridge vlan_filtering 1

$ ip link add dev br1 type bridge
$ ip link set dev ethX master br1
错误：fsl_dpaa2_switch: 无法加入无 VLAN 意识的桥接
```

通过 STP 支持拓扑和环路检测，在创建桥接时使用 `stp_state 1` 参数：
```
$ ip link add dev br0 type bridge vlan_filtering 1 stp_state 1
```

支持 L2 FDB 操作（添加/删除/转储）。可以通过桥接命令独立配置每个交换端口上的硬件 FDB 学习。当禁用硬件学习时，将运行快速老化过程，并移除所有先前学到的地址：
```
$ bridge link set dev ethX learning off
$ bridge link set dev ethX learning on
```

支持限制未知单播和组播泛洪域，但不能独立于彼此：
```
$ ip link set dev ethX type bridge_slave flood off mcast_flood off
$ ip link set dev ethX type bridge_slave flood off mcast_flood on
错误：fsl_dpaa2_switch: 无法独立配置组播泛洪
```

可以通过 `/sys/bus/fsl-mc/devices/dpsw.Y/net/ethX/brport/broadcast_flood` 系统文件启用或禁用交换端口上的广播泛洪：
```
$ echo 0 > /sys/bus/fsl-mc/devices/dpsw.Y/net/ethX/brport/broadcast_flood
```

卸载
========

路由操作（重定向、捕获、丢弃）
--------------------------------------

DPAA2 交换机能够卸载基于流的报文重定向，利用 ACL 表实现。多个端口可以共享一个 ACL 表来支持共享过滤块。支持以下流键：

* Ethernet: 目的 MAC/源 MAC
* IPv4: 目的 IP/源 IP/IP 协议/TOS
* VLAN: VLAN ID/VLAN 优先级/VLAN 类型标识符/VLAN DEI
* L4: 目的端口/源端口

此外，还可以使用匹配所有过滤器来重定向端口上接收的所有流量。关于流操作，支持以下几种：

* 丢弃
* 镜像出口重定向
* 捕获

每个 ACL 条目（过滤器）只能设置列表中的一个动作。示例 1：将 eth4 接收到的源地址为 00:01:02:03:04:05 的帧发送到 CPU：
```
$ tc qdisc add dev eth4 clsact
$ tc filter add dev eth4 ingress flower src_mac 00:01:02:03:04:05 skip_sw action trap
```

示例 2：丢弃 eth4 接收到的 VID 为 100 且 PCP 为 3 的帧：
```
$ tc filter add dev eth4 ingress protocol 802.1q flower skip_sw vlan_id 100 vlan_prio 3 action drop
```

示例 3：将 eth4 接收到的所有帧重定向到 eth1：
```
$ tc filter add dev eth4 ingress matchall action mirred egress redirect dev eth1
```

示例 4：在 eth5 和 eth6 上使用同一个共享过滤块：
```
$ tc qdisc add dev eth5 ingress_block 1 clsact
$ tc qdisc add dev eth6 ingress_block 1 clsact
$ tc filter add block 1 ingress flower dst_mac 00:01:02:03:04:04 skip_sw action trap
$ tc filter add block 1 ingress protocol ipv4 flower src_ip 192.168.1.1 skip_sw action mirred egress redirect dev eth3
```

镜像
~~~~~~~~~

DPAA2 交换机仅支持按端口镜像和按 VLAN 镜像。在共享块中添加镜像过滤器也是支持的。
当使用 `tc-flower` 分类器与 802.1q 协议时，仅接受 `vlan_id` 键。基于 802.1q 协议的其他字段的镜像将会被拒绝：

    $ tc qdisc add dev eth8 ingress_block 1 clsact
    $ tc filter add block 1 ingress protocol 802.1q flower skip_sw vlan_prio 3 action mirred egress mirror dev eth6
    错误：fsl_dpaa2_switch: 只支持匹配 VLAN ID
    我们在与内核通信时遇到了错误

如果在一个端口上请求了基于VLAN的镜像过滤器，则必须在相应的交换机端口上安装该VLAN，要么通过 `bridge` 命令，要么如果该交换机端口作为独立接口使用，则创建一个VLAN上层设备：

    $ tc qdisc add dev eth8 ingress_block 1 clsact
    $ tc filter add block 1 ingress protocol 802.1q flower skip_sw vlan_id 200 action mirred egress mirror dev eth6
    错误：必须在交换机端口上安装VLAN
    我们在与内核通信时遇到了错误

    $ bridge vlan add vid 200 dev eth8
    $ tc filter add block 1 ingress protocol 802.1q flower skip_sw vlan_id 200 action mirred egress mirror dev eth6

    $ ip link add link eth8 name eth8.200 type vlan id 200
    $ tc filter add block 1 ingress protocol 802.1q flower skip_sw vlan_id 200 action mirred egress mirror dev eth6

此外，需要注意的是，被镜像的流量将受到与其他任何流量相同的出口限制。这意味着当一个被镜像的数据包到达镜像端口时，如果数据包中的VLAN没有安装在该端口上，它将被丢弃。
DPAA2 交换机只支持单一的镜像目标，因此可以安装多个镜像规则，但它们的目标端口必须相同：

    $ tc filter add block 1 ingress protocol 802.1q flower skip_sw vlan_id 200 action mirred egress mirror dev eth6
    $ tc filter add block 1 ingress protocol 802.1q flower skip_sw vlan_id 100 action mirred egress mirror dev eth7
    错误：fsl_dpaa2_switch: 不支持多个镜像端口
    我们在与内核通信时遇到了错误
