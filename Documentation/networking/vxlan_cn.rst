SPDX 许可证标识符: GPL-2.0

======================================
虚拟可扩展局域网文档
======================================

VXLAN 协议是一种隧道协议，旨在解决 IEEE 802.1q 中有限的 VLAN ID（4096）问题。通过 VXLAN，标识符的大小扩展到 24 位（16777216）。VXLAN 由 IETF RFC 7348 描述，并已被多个供应商实现。该协议在 UDP 上运行，使用单一目的端口。本文档描述了 Linux 内核隧道设备，还有 Openvswitch 的单独 VXLAN 实现。

与大多数隧道不同，VXLAN 是一个 1 到 N 的网络，而不仅仅是点对点。VXLAN 设备可以动态地学习另一端点的 IP 地址，类似于学习桥接的方式，或者利用静态配置的转发条目。

VXLAN 的管理方式类似于其两个最接近的邻居 GRE 和 VLAN。配置 VXLAN 需要与内核版本匹配的 iproute2 版本，这是 VXLAN 最初合并上游时所要求的。

1. 创建 vxlan 设备:

    ```
    # ip link add vxlan0 type vxlan id 42 group 239.1.1.1 dev eth1 dstport 4789
    ```

这创建了一个名为 vxlan0 的新设备。该设备使用 eth1 上的多播组 239.1.1.1 来处理转发表中没有条目的流量。目的端口号设置为 IANA 分配的值 4789。Linux 的 VXLAN 实现早于 IANA 选定的标准目的端口号，并默认使用 Linux 选择的值以保持向后兼容性。

2. 删除 vxlan 设备:

    ```
    # ip link delete vxlan0
    ```

3. 显示 vxlan 信息:

    ```
    # ip -d link show vxlan0
    ```

可以使用新的 bridge 命令来创建、销毁和显示 vxlan 转发表。

1. 创建转发表条目:

    ```
    # bridge fdb add 00:17:42:8a:b4:05 dst 192.19.0.2 dev vxlan0
    ```

2. 删除转发表条目:

    ```
    # bridge fdb delete 00:17:42:8a:b4:05 dev vxlan0
    ```

3. 显示转发表:

    ```
    # bridge fdb show dev vxlan0
    ```

以下 NIC 特性可能表明支持 UDP 隧道相关的卸载（最常见的 VXLAN 功能，但对特定封装协议的支持取决于 NIC）：

- `tx-udp_tnl-segmentation`
- `tx-udp_tnl-csum-segmentation`：执行 UDP 封装帧的 TCP 分段卸载的能力
- `rx-udp_tunnel-port-offload`：接收侧解析 UDP 封装帧，允许 NIC 执行协议感知卸载，如内部帧的校验和验证卸载（仅适用于无协议无关卸载的 NIC）

对于支持 `rx-udp_tunnel-port-offload` 的设备，当前已卸载端口的列表可以通过 `ethtool` 查看：

```
$ ethtool --show-tunnels eth0
eth0 的隧道信息：
    UDP 端口表 0：
      大小：4
      类型：vxlan
      没有条目
    UDP 端口表 1：
      大小：4
      类型：geneve, vxlan-gpe
      条目（1）：
          端口 1230, vxlan-gpe
```
