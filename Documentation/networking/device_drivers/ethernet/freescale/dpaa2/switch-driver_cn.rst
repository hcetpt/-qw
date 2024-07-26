### SPDX 许可证标识符：GPL-2.0
### 包含：<isonum.txt>

===================
DPAA2 交换机驱动程序
===================

:版权所有: |copy| 2021 NXP

DPAA2 交换机驱动程序在数据路径交换(DPSW)对象上进行探测，该对象可以在以下 DPAA2 系统级芯片及其变体上实例化：LS2088A 和 LX2160A。
驱动程序使用交换设备驱动模型，并将每个交换端口暴露为网络接口，这些接口可以被包含在一个网桥中或作为独立的接口使用。端口之间的流量切换被卸载到硬件中。
DPSW 可以有连接到数据包网络接口(DPNIs)或数据包媒体接入控制(DPMACs)的端口，用于外部访问。

```
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
```

创建以太网交换机
==================

dpaa2-switch 驱动程序在 fsl-mc 总线上找到的 DPSW 设备上进行探测。这些设备可以通过启动时配置文件——数据路径布局(DPL)静态创建，或者使用 DPAA2 对象 API（已经集成到 restool 用户空间工具中）在运行时创建。
目前，dpaa2-switch 驱动程序对它将要探测的 DPSW 对象施加了以下限制：

 * 最少的 FDB 数量应该至少等于交换接口的数量。这是必要的，以便能够分离交换端口，即当不在网桥下时，每个交换端口将拥有自己的 FDB。
```
        fsl_dpaa2_switch dpsw.0: FDB 的数量低于端口数量，无法进行探测
```

 * 广播和泛洪配置都应该是按 FDB 进行的。这使得驱动程序能够根据共享同一 FDB 的交换端口（即处于同一网桥下）来限制每个 FDB 的广播和泛洪域。
```
        fsl_dpaa2_switch dpsw.0: 泛洪域不是按 FDB 的，无法进行探测
        fsl_dpaa2_switch dpsw.0: 广播域不是按 FDB 的，无法进行探测
```

 * 交换机的控制接口不应该被禁用（没有传递 DPSW_OPT_CTRL_IF_DIS 作为创建时的选项）。没有控制接口，驱动程序无法在交换端口网络设备上提供正确的接收/发送流量支持。
```
        fsl_dpaa2_switch dpsw.0: 控制接口被禁用，无法进行探测
```

除了实际 DPSW 对象的配置之外，dpaa2-switch 驱动程序还需要以下 DPAA2 对象：

 * 1 个 DPMCP —— 一个管理命令门户对象对于与 MC 固件的任何交互都是必需的。
 * 1 个 DPBP —— 一个缓冲池用于在控制接口上的接收路径上播种缓冲区。
 * 至少需要访问一个 DPIO 对象（软件门户），以便在控制接口队列上执行任何入队/出队操作。
DPIO 对象将被共享，无需使用私有对象。

特性切换
========

该驱动支持在硬件中配置 L2 转发规则以实现端口桥接以及独立使用独立的交换接口。硬件不支持针对 VLAN 意识的配置，因此任何 DPAA2 交换端口仅应在具有 VLAN 意识的桥接场景中使用：

        $ ip link add dev br0 type bridge vlan_filtering 1

        $ ip link add dev br1 type bridge
        $ ip link set dev ethX master br1
        错误: fsl_dpaa2_switch: 无法加入一个不支持VLAN的桥接

通过 STP 进行拓扑和环路检测在创建桥接时使用 `stp_state 1` 是支持的：

        $ ip link add dev br0 type bridge vlan_filtering 1 stp_state 1

支持 L2 FDB 的操作（添加/删除/导出）。
可以通过桥接命令为每个交换端口独立地配置硬件 FDB 学习功能。当禁用硬件学习时，将运行快速老化过程，并移除所有之前学习到的地址：

        $ bridge link set dev ethX learning off
        $ bridge link set dev ethX learning on

支持限制未知单播和组播泛洪域，但不能独立配置：

        $ ip link set dev ethX type bridge_slave flood off mcast_flood off
        $ ip link set dev ethX type bridge_slave flood off mcast_flood on
        错误: fsl_dpaa2_switch: 无法独立于单播配置组播泛洪

可以在 brport sysfs 中启用/禁用交换端口上的广播泛洪：

        $ echo 0 > /sys/bus/fsl-mc/devices/dpsw.Y/net/ethX/brport/broadcast_flood

卸载任务
========

路由行为（重定向、捕获、丢弃）
--------------------------------------

DPAA2 交换机能够卸载基于流的包重定向任务，利用 ACL 表。支持通过多个端口共享单一 ACL 表来实现共享过滤块。
以下流键是支持的：

 * 以太网：dst_mac/src_mac
 * IPv4：dst_ip/src_ip/ip_proto/tos
 * VLAN：vlan_id/vlan_prio/vlan_tpid/vlan_dei
 * L4：dst_port/src_port

此外，可以使用匹配所有（matchall）过滤器将端口收到的所有流量重定向。
关于流行为，支持以下选项：

 * 丢弃
 * 镜像 egress 重定向
 * 捕获

每个 ACL 条目（过滤器）只能设置上述动作之一。
示例 1：将 eth4 接收的源 MAC 地址为 00:01:02:03:04:05 的帧发送到 CPU：

        $ tc qdisc add dev eth4 clsact
        $ tc filter add dev eth4 ingress flower src_mac 00:01:02:03:04:05 skip_sw action trap

示例 2：丢弃 eth4 接收的 VID 为 100 且 PCP 为 3 的帧：

        $ tc filter add dev eth4 ingress protocol 802.1q flower skip_sw vlan_id 100 vlan_prio 3 action drop

示例 3：将 eth4 接收的所有帧重定向到 eth1：

        $ tc filter add dev eth4 ingress matchall action mirred egress redirect dev eth1

示例 4：在 eth5 和 eth6 上使用相同的共享过滤块：

        $ tc qdisc add dev eth5 ingress_block 1 clsact
        $ tc qdisc add dev eth6 ingress_block 1 clsact
        $ tc filter add block 1 ingress flower dst_mac 00:01:02:03:04:04 skip_sw \
                action trap
        $ tc filter add block 1 ingress protocol ipv4 flower src_ip 192.168.1.1 skip_sw \
                action mirred egress redirect dev eth3

镜像
~~~~~~~~~

DPAA2 交换机仅支持端口级镜像和每 VLAN 级镜像。
同样支持在共享块中添加镜像过滤器。
使用 tc-flower 分类器与 802.1q 协议时，仅接受 'vlan_id' 键。基于 802.1q 协议中的其他字段的镜像将会被拒绝：

        $ tc qdisc add dev eth8 ingress_block 1 clsact
        $ tc filter add block 1 ingress protocol 802.1q flower skip_sw vlan_prio 3 action mirred egress mirror dev eth6
        错误：fsl_dpaa2_switch: 只支持匹配 VLAN ID
我们与内核通信时出现了错误。

如果在端口上请求了镜像 VLAN 过滤器，则必须通过使用 'bridge' 或创建一个 VLAN 上层设备（如果该交换机端口用作独立接口）来在相关交换机端口上安装该 VLAN ：

        $ tc qdisc add dev eth8 ingress_block 1 clsact
        $ tc filter add block 1 ingress protocol 802.1q flower skip_sw vlan_id 200 action mirred egress mirror dev eth6
        错误：VLAN 必须安装在交换机端口上
我们与内核通信时出现了错误。

        $ bridge vlan add vid 200 dev eth8
        $ tc filter add block 1 ingress protocol 802.1q flower skip_sw vlan_id 200 action mirred egress mirror dev eth6

        $ ip link add link eth8 name eth8.200 type vlan id 200
        $ tc filter add block 1 ingress protocol 802.1q flower skip_sw vlan_id 200 action mirred egress mirror dev eth6

此外，需要注意的是，被镜像的流量将受到与任何其他流量相同的出站限制。这意味着当被镜像的数据包到达镜像端口时，如果数据包中发现的 VLAN 没有安装在该端口上，则会被丢弃。
DPAA2 交换机只支持单个镜像目的地，因此可以安装多个镜像规则，但它们的 'to' 端口必须相同：

        $ tc filter add block 1 ingress protocol 802.1q flower skip_sw vlan_id 200 action mirred egress mirror dev eth6
        $ tc filter add block 1 ingress protocol 802.1q flower skip_sw vlan_id 100 action mirred egress mirror dev eth7
        错误：fsl_dpaa2_switch: 不支持多个镜像端口
我们与内核通信时出现了错误。
