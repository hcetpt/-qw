NXP SJA1105 交换机驱动程序
=========================

概述
========

NXP SJA1105 是一系列通过 SPI 管理的汽车交换机：

- SJA1105E：第一代，无 TTEthernet
- SJA1105T：第一代，有 TTEthernet
- SJA1105P：第二代，无 TTEthernet，无 SGMII
- SJA1105Q：第二代，有 TTEthernet，无 SGMII
- SJA1105R：第二代，无 TTEthernet，有 SGMII
- SJA1105S：第二代，有 TTEthernet，有 SGMII
- SJA1110A：第三代，有 TTEthernet，有 SGMII，集成 100base-T1 和 100base-TX PHY
- SJA1110B：第三代，有 TTEthernet，有 SGMII，100base-T1，100base-TX
- SJA1110C：第三代，有 TTEthernet，有 SGMII，100base-T1，100base-TX
- SJA1110D：第三代，有 TTEthernet，有 SGMII，100base-T1

作为汽车部件，它们的配置接口主要面向设置后无需干预的使用场景，在运行时需要的动态交互非常少。它们需要一个静态配置由软件生成，并且包含 CRC 和表头，然后通过 SPI 发送。

静态配置由多个配置表组成。每个表包含若干条目。某些配置表可以在运行时（部分）重新配置，而有些则不能。有些表是必需的，有些不是：

============================= ================== =============================
表                           必须            可重新配置
============================= ================== =============================
调度表                         否              否
调度入口点                     如果启用调度     否
VL 查找表                      否              否
VL 警戒表                      如果启用 VL 查找  否
VL 转发表                      如果启用 VL 查找  否
L2 查找表                      否              否
L2 警戒表                      是              否
VLAN 查找表                    是              是
L2 转发表                      是              部分（完全在 P/Q/R/S 上）
MAC 配置表                     是              部分（完全在 P/Q/R/S 上）
调度参数表                     如果启用调度     否
调度入口点参数表               如果启用调度     否
VL 转发参数表                  如果启用 VL 转发  否
L2 查找参数表                  否              部分（完全在 P/Q/R/S 上）
L2 转发参数表                  是              否
时钟同步参数表                 否              否
AVB 参数表                     否              否
通用参数表                     是              部分
重标签表                      否              是
xMII 参数表                    是              否
SGMII 表                       否              是
============================= ================== =============================

此外，配置是只写模式（软件无法从交换机读取，除了少数例外）。
驱动程序在探测时创建一个静态配置，并始终将其保留在内存中，作为硬件状态的影子。当需要更改硬件设置时，也会更新静态配置。
如果可以将更改后的设置通过动态重新配置接口传输到交换机，则会这样做；否则，交换机会被重置并用更新后的静态配置重新编程。

交换功能
==================

该驱动程序支持在硬件中配置 L2 转发规则以实现端口桥接。端口之间的转发、广播和泛洪域可以通过两种方法进行限制：要么在 L2 转发级别（隔离一个桥接器的端口与另一个桥接器的端口），要么在 VLAN 端口成员资格级别（在同一桥接器内隔离端口）。硬件最终做出的转发决定是对这两组规则的逻辑“与”运算结果。
硬件内部通过基于端口的 VLAN（pvid）标记所有流量，或从 802.1Q 标签解码 VLAN 信息。高级 VLAN 分类是不可能的。一旦分配了 VLAN 标签，帧就会根据端口的成员资格规则进行检查，并在进入时不匹配任何 VLAN 时丢弃。
这种行为在交换机端口加入带有 `vlan_filtering 1` 的桥接器时可用。
通常硬件无法针对 VLAN 意识进行配置，但通过更改交换机搜索 802.1Q 标签所用的 TPID，可以保持 `vlan_filtering 0` 模式的语义（接受所有流量，无论是否带标签），因此也支持该模式。
支持将交换机端口划分为多个桥接器（例如 2+2），但所有桥接器应具有相同的 VLAN 意识级别（要么都为 `vlan_filtering` 0，要么都为 1）。
通过 STP 支持拓扑和环路检测。
卸载
=====

时间感知调度
---------------------

该交换机支持IEEE 802.1Q-2018（原为802.1Qbv）中指定的用于计划流量增强功能的一个变体。这意味着它可以用来确保在网络调度中的门开启事件时发送的优先级流量具有确定性的延迟。这种能力可以通过`tc-taprio`卸载（标志2）来管理。与软件实现的taprio相比，后者的区别在于它只能塑造来自CPU的流量，而不能自主转发流。该设备有8个流量类别，并根据VLAN PCP位（如果没有VLAN，则使用基于端口的默认值）映射传入帧。如前几节所述，根据`vlan_filtering`的值，交换机识别为VLAN的EtherType可以是典型的0x8100或驱动程序内部用于标记的自定义值。因此，在独立模式或桥接模式下，如果`vlan_filtering=0`，则交换机会忽略VLAN PCP，因为它不会识别0x8100的EtherType。在这些模式下，只有DSA网络设备能够通过填充标签头中的PCP字段将流量注入特定的TX队列。使用`vlan_filtering=1`时，情况相反：卸载流可以根据VLAN PCP被引导到TX队列，但DSA网络设备将无法做到这一点。为了在启用VLAN感知的情况下将帧注入硬件TX队列，必须在DSA通道端口上创建一个VLAN子接口，并向交换机发送带有适当设置VLAN PCP位的标准（0x8100）VLAN标记的帧。管理流量（具有DMAC 01-80-C2-xx-xx-xx或01-19-1B-xx-xx-xx）是一个显著例外：交换机总是以固定优先级处理它，即使存在VLAN PCP位也会忽略它们。目前管理流量的流量类值为7（最高优先级），这在驱动程序中是不可配置的。

下面是在出站端口`swp5`上配置500微秒周期性调度的一个示例。管理流量（7）的流量类门打开100微秒，其他所有流量类的门打开400微秒：

```bash
#!/bin/bash

set -e -u -o pipefail

NSEC_PER_SEC="1000000000"

gatemask() {
        local tc_list="$1"
        local mask=0

        for tc in ${tc_list}; do
                mask=$((${mask} | (1 << ${tc})))
        done

        printf "%02x" ${mask}
}

if ! systemctl is-active --quiet ptp4l; then
        echo "Please start the ptp4l service"
        exit
fi

now=$(phc_ctl /dev/ptp1 get | gawk '/clock time is/ { print $5; }')
# 将基准时间对齐到下一秒的开始
sec=$(echo "${now}" | gawk -F. '{ print $1; }')
base_time="$(((${sec} + 1) * ${NSEC_PER_SEC}))"

tc qdisc add dev swp5 parent root handle 100 taprio \
        num_tc 8 \
        map 0 1 2 3 5 6 7 \
        queues 1@0 1@1 1@2 1@3 1@4 1@5 1@6 1@7 \
        base-time ${base_time} \
        sched-entry S $(gatemask 7) 100000 \
        sched-entry S $(gatemask "0 1 2 3 4 5 6") 400000 \
        flags 2
```

可以在多个出站端口上应用`tc-taprio`卸载。由于硬件限制，不允许两个端口同时触发任何门事件。驱动程序会检查这些限制，并在适当情况下报错。避免这种情况需要进行调度分析，这超出了本文档的范围。

路由操作（重定向、捕获、丢弃）
--------------------------------------

交换机能够卸载用户指定的目的端口集上的基于流的包重定向。内部实现是通过使用虚拟链路（TTEthernet概念）来完成的。
驱动程序支持两种类型的虚拟链路键：

- 带VLAN感知的虚拟链路：这些匹配目标MAC地址、VLAN ID和VLAN PCP
- 不带VLAN感知的虚拟链路：这些仅匹配目标MAC地址
桥接器的VLAN感知状态（vlan_filtering）在存在虚拟链路规则时无法更改。

在同一规则中组合多个操作是支持的。当仅请求路由操作时，驱动程序创建一个“非关键”虚拟链路。当操作列表中还包含tc-gate（详见下文）时，虚拟链路变为“时间关键”（从预留内存分区提取帧缓冲区等）。

支持的三种路由操作是“trap”、“drop”和“redirect”。

示例1：将swp2收到的目标地址为42:be:24:9b:76:20的数据帧发送到CPU和swp3。当端口的VLAN感知状态关闭时，此类键（仅目标地址）如下：

```sh
tc qdisc add dev swp2 clsact
tc filter add dev swp2 ingress flower skip_sw dst_mac 42:be:24:9b:76:20 \
          action mirred egress redirect dev swp3 \
          action trap
```

示例2：丢弃swp2收到的目标地址为42:be:24:9b:76:20、VID为100且PCP为0的数据帧：

```sh
tc filter add dev swp2 ingress protocol 802.1Q flower skip_sw \
          dst_mac 42:be:24:9b:76:20 vlan_id 100 vlan_prio 0 action drop
```

基于时间的入口策略
----------------------

交换机的TTEthernet硬件能力可以被限制以类似于IEEE 802.1Q-2018（原802.1Qci）规范中规定的Per-Stream Filtering and Policing (PSFP)条款的方式工作。这意味着它可以用于执行最多1024个流（由目标MAC地址、VLAN ID和VLAN PCP组成的元组标识）的精确基于时间的准入控制。在预期接收窗口之外接收到的数据包将被丢弃。

此功能可以通过卸载tc-gate操作来管理。由于路由操作是TTEthernet（执行显式的时间关键流量路由，并不依赖于FDB表、泛洪等）中的固有部分，因此当请求sja1105卸载tc-gate时，它不能单独出现。必须同时有一个或多个重定向或捕获动作。

示例：创建一个与tc-gate调度同步的tc-taprio调度（时钟必须通过1588应用堆栈进行同步，这超出了本文档的范围）。发送方发出的任何数据包都不会被丢弃。请注意，接收窗口比传输窗口大（在此示例中更是如此），以补偿链接的数据包传播延迟（可通过1588应用堆栈确定）。

接收端（sja1105）：

```sh
tc qdisc add dev swp2 clsact
now=$(phc_ctl /dev/ptp1 get | awk '/clock time is/ {print $5}') && \
        sec=$(echo $now | awk -F. '{print $1}') && \
        base_time="$(((sec + 2) * 1000000000))" && \
        echo "base time ${base_time}"
tc filter add dev swp2 ingress flower skip_sw \
        dst_mac 42:be:24:9b:76:20 \
        action gate base-time ${base_time} \
        sched-entry OPEN  60000 -1 -1 \
        sched-entry CLOSE 40000 -1 -1 \
        action trap
```

发送端：

```sh
now=$(phc_ctl /dev/ptp0 get | awk '/clock time is/ {print $5}') && \
        sec=$(echo $now | awk -F. '{print $1}') && \
        base_time="$(((sec + 2) * 1000000000))" && \
        echo "base time ${base_time}"
tc qdisc add dev eno0 parent root taprio \
        num_tc 8 \
        map 0 1 2 3 4 5 6 7 \
        queues 1@0 1@1 1@2 1@3 1@4 1@5 1@6 1@7 \
        base-time ${base_time} \
        sched-entry S 01  50000 \
        sched-entry S 00  50000 \
        flags 2
```

用于调度入口门控操作的引擎与用于tc-taprio卸载的引擎相同。因此，两个门控操作（无论是tc-gate还是tc-taprio门控）在同一时间（同一200纳秒时隙内）触发的限制仍然适用。

为了方便使用，可以通过流块在多个入口端口之间共享时间触发的虚拟链路。在这种情况下，同一时间触发的限制不适用，因为系统中只有一个调度，即共享虚拟链路的调度：

```sh
tc qdisc add dev swp2 ingress_block 1 clsact
tc qdisc add dev swp3 ingress_block 1 clsact
tc filter add block 1 flower skip_sw dst_mac 42:be:24:9b:76:20 \
        action gate index 2 \
        base-time 0 \
        sched-entry OPEN 50000000 -1 -1 \
        sched-entry CLOSE 50000000 -1 -1 \
        action trap
```

每个流的硬件统计信息也是可用的（“pkts”计数已丢弃的数据帧数量，这是因定时违规、缺少目标端口和MTU强制检查而丢弃的数据帧数量之和）。字节级别的计数器不可用。

限制
====

SJA1105交换机系列始终执行VLAN处理。当配置为VLAN无感知时，帧内部携带不同的VLAN标签，具体取决于端口是否独立或处于VLAN无感知桥接器之下。

虚拟链路键始终固定为{MAC DA, VLAN ID, VLAN PCP}，但驱动程序在端口处于VLAN感知桥接器下时请求VLAN ID和VLAN PCP。否则，它会根据端口是否独立或在VLAN无感知桥接器下自动填充VLAN ID和PCP，并且只接受“VLAN无感知”的tc-flower键（MAC DA）。
现有的通过虚拟链路卸载的tc-flower键在以下情况发生后将不再有效：

- 端口原来是独立的，现在加入了一个网桥（无论是VLAN感知的还是非VLAN感知的）
- 端口是网桥的一部分，该网桥的VLAN感知状态发生变化
- 端口原来是网桥的一部分，现在变为独立端口
- 端口原来是独立的，但另一个端口加入了一个VLAN感知的网桥，并且这改变了网桥的全局VLAN感知状态

驱动程序无法否决所有这些操作，也无法更新或移除现有的tc-flower过滤器。因此，为了正确运行，tc-flower过滤器应在端口的转发配置完成后安装，并且在对设备树绑定和板卡设计进行任何更改之前由用户空间移除。

### 设备树绑定和板卡设计

本节引用了 `Documentation/devicetree/bindings/net/dsa/nxp,sja1105.yaml`，旨在展示一些潜在的交换机问题。

#### RMII PHY角色和带外信号

根据RMII规范，50 MHz时钟信号可以由MAC或外部振荡器驱动（而不是由PHY驱动）。但是，该规范较为宽松，许多设备会超出规范的要求。

有些PHY违反了规范，可能会提供一个输出引脚来自己生成50 MHz时钟，试图提供帮助。另一方面，SJA1105只能通过二进制配置。当处于RMII MAC角色时，它也会尝试驱动时钟信号。为了避免这种情况，必须将其设置为RMII PHY角色。但是这样做会产生一些意想不到的后果。

根据RMII规范，PHY可以通过RXD[1:0]传输额外的带外信号。这些实际上是在每帧前导码之前的额外编码字（/J/ 和 /K/）。MAC没有定义这种带外信号机制。因此，当SJA1105端口被设置为PHY角色以避免两个驱动程序同时驱动时钟信号时，不可避免地创建了一个RMII PHY到PHY的连接。SJA1105完全模拟PHY接口并在帧前导码之前生成/J/ 和 /K/ 符号，而真正的PHY并不理解这些额外的符号。因此，PHY简单地将从SJA1105作为PHY接收到的额外符号编码到100Base-Tx线上。
在网线的另一端，一些链路伙伴可能会丢弃这些多余的符号，而其他链路伙伴可能会因为这些符号而导致整个以太网帧被丢弃。这在某些链路伙伴看来像是丢包现象，但在其他链路伙伴看来则不是。

结论是在RMII模式下，如果SJA1105连接到PHY，则必须让SJA1105驱动参考时钟。

RGMII固定链路和内部延迟
----------------------------

如绑定文档中所述，第二代设备的MAC部分具有可调延迟线，可以用来建立正确的RGMII定时预算。上电后，这些延迟线可以使Rx和Tx时钟产生73.8至101.7度之间的相位差。需要注意的是，这些延迟线需要锁定在一个稳定的频率信号上。这意味着在旧频率与新频率之间的时钟之间至少要有2微秒的静默时间。否则会失去锁定，需要重置延迟线（关闭并重新启动）。

在RGMII中，时钟频率随链路速度变化（1000 Mbps时为125 MHz，100 Mbps时为25 MHz，10 Mbps时为2.5 MHz），并且链路速度可能在自动协商（AN）过程中发生变化。

当交换机端口通过RGMII固定链路连接到一个链路状态生命周期不受Linux控制的链路伙伴（例如不同的SoC）时，延迟线将保持未锁定（且不活动），直到有人工干预（在交换机端口上执行ifdown/ifup操作）。

结论是在RGMII模式下，只有当链路伙伴从不改变链路速度或在改变链路速度时与交换机端口协调一致（实际上，固定链路两端都受同一Linux系统的控制）的情况下，交换机的内部延迟才是可靠的。

为什么固定链路接口可能会改变链路速度：有些以太网控制器在复位后默认工作在100 Mbps模式下，并且其驱动程序不可避免地需要改变速度和时钟频率，以便在千兆模式下工作。

MDIO总线和PHY管理
--------------------------

SJA1105没有MDIO总线，也不进行带内自动协商（AN）。
因此，交换机设备没有发出任何链路状态通知。
需要将连接到交换机的PHY连接到系统内Linux可用的其他MDIO总线上（例如，连接到DSA通道的MDIO总线）。链路状态管理通过驱动程序手动同步MAC链路速度与PHY协商的设置（通过SPI命令）来实现。
相比之下，SJA1110支持一个MDIO从访问点，通过该访问点可以从主机访问其内部的100base-T1 PHY。然而，驱动程序并未使用这一点，而是通过SPI命令访问内部的100base-T1和100base-TX PHY，在Linux中将其建模为虚拟MDIO总线。
连接到SJA1110端口0的微控制器也有一个以主模式运行的MDIO控制器，但是驱动程序也不支持这一点，因为当Linux驱动程序运行时，微控制器会被禁用。
连接到交换机端口的独立PHY应将其MDIO接口连接到主机系统的MDIO控制器上，而不是连接到交换机上，类似于SJA1105。

端口兼容性矩阵
-------------------------

SJA1105的端口兼容性矩阵如下：

===== ============== ============== ==============
端口   SJA1105E/T     SJA1105P/Q     SJA1105R/S
===== ============== ============== ==============
0      xMII           xMII           xMII
1      xMII           xMII           xMII
2      xMII           xMII           xMII
3      xMII           xMII           xMII
4      xMII           xMII           SGMII
===== ============== ============== ==============

SJA1110的端口兼容性矩阵如下：

===== ============== ============== ============== ==============
端口   SJA1110A       SJA1110B       SJA1110C       SJA1110D
===== ============== ============== ============== ==============
0      RevMII (uC)    RevMII (uC)    RevMII (uC)    RevMII (uC)
1      100base-TX     100base-TX     100base-TX
       或 SGMII                                      SGMII
2      xMII           xMII           xMII           xMII
       或 SGMII                                      或 SGMII
3      xMII           xMII           xMII
       或 SGMII       或 SGMII                        SGMII
       或 2500base-X  或 2500base-X                 或 2500base-X
4      SGMII          SGMII          SGMII          SGMII
       或 2500base-X  或 2500base-X  或 2500base-X  或 2500base-X
5      100base-T1     100base-T1     100base-T1     100base-T1
6      100base-T1     100base-T1     100base-T1     100base-T1
7      100base-T1     100base-T1     100base-T1     100base-T1
8      100base-T1     100base-T1     不适用         不适用
9      100base-T1     100base-T1     不适用         不适用
10     100base-T1     不适用         不适用         不适用
===== ============== ============== ============== ==============
