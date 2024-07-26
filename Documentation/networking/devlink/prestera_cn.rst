SPDX 许可证标识符: GPL-2.0

========================
Prestera devlink 支持
========================

本文档描述了由 `prestera` 设备驱动程序实现的 devlink 功能。
驱动程序特有的陷阱
=====================

.. list-table:: Prestera 驱动程序注册的驱动程序特有陷阱列表
   :widths: 5 5 90

   * - 名称
     - 类型
     - 描述
   * - `arp_bc`
     - `trap`
     - 捕获 ARP 广播数据包（请求和响应）
   * - `is_is`
     - `trap`
     - 捕获 IS-IS 数据包
   * - `ospf`
     - `trap`
     - 捕获 OSPF 数据包
   * - `ip_bc_mac`
     - `trap`
     - 捕获具有广播目标 MAC 地址的 IPv4 数据包
   * - `stp`
     - `trap`
     - 捕获 STP BPDU
   * - `lacp`
     - `trap`
     - 捕获 LACP 数据包
   * - `lldp`
     - `trap`
     - 捕获 LLDP 数据包
   * - `router_mc`
     - `trap`
     - 捕获多播数据包
   * - `vrrp`
     - `trap`
     - 捕获 VRRP 数据包
   * - `dhcp`
     - `trap`
     - 捕获 DHCP 数据包
   * - `mtu_error`
     - `trap`
     - 捕获超过端口 MTU 的数据包（异常情况）
   * - `mac_to_me`
     - `trap`
     - 捕获具有交换机端口的目标 MAC 地址的数据包
   * - `ttl_error`
     - `trap`
     - 捕获 TTL 超出的 IPv4 数据包（异常情况）
   * - `ipv4_options`
     - `trap`
     - 捕获由于不正确的 IPv4 头选项而导致的数据包（异常情况）
   * - `ip_default_route`
     - `trap`
     - 捕获没有特定 IP 接口（IP 到我）且没有转发前缀的数据包
   * - `local_route`
     - `trap`
     - 捕获发送到交换机 IP 接口地址之一的数据包
   * - `ipv4_icmp_redirect`
     - `trap`
     - 捕获 IPv4 ICMP 重定向数据包（异常情况）
   * - `arp_response`
     - `trap`
     - 捕获具有交换机端口的目标 MAC 地址的 ARP 回复数据包
   * - `acl_code_0`
     - `trap`
     - 捕获 ACL 优先级设置为 0（tc pref 0）的数据包
   * - `acl_code_1`
     - `trap`
     - 捕获 ACL 优先级设置为 1（tc pref 1）的数据包
   * - `acl_code_2`
     - `trap`
     - 捕获 ACL 优先级设置为 2（tc pref 2）的数据包
   * - `acl_code_3`
     - `trap`
     - 捕获 ACL 优先级设置为 3（tc pref 3）的数据包
   * - `acl_code_4`
     - `trap`
     - 捕获 ACL 优先级设置为 4（tc pref 4）的数据包
   * - `acl_code_5`
     - `trap`
     - 捕获 ACL 优先级设置为 5（tc pref 5）的数据包
   * - `acl_code_6`
     - `trap`
     - 捕获 ACL 优先级设置为 6（tc pref 6）的数据包
   * - `acl_code_7`
     - `trap`
     - 捕获 ACL 优先级设置为 7（tc pref 7）的数据包
   * - `ipv4_bgp`
     - `trap`
     - 捕获 IPv4 BGP 数据包
   * - `ssh`
     - `trap`
     - 捕获 SSH 数据包
   * - `telnet`
     - `trap`
     - 捕获 Telnet 数据包
   * - `icmp`
     - `trap`
     - 捕获 ICMP 数据包
   * - `rxdma_drop`
     - `drop`
     - 由于缺乏入口缓冲区等原因丢弃数据包（RxDMA）
   * - `port_no_vlan`
     - `drop`
     - 由于网络配置错误或内部缺陷（配置问题）而丢弃数据包
   * - `local_port`
     - `drop`
     - 丢弃其决策（FDB 条目）是将数据包桥接到传入端口/链路的数据包
   * - `invalid_sa`
     - `drop`
     - 丢弃源 MAC 地址为组播的数据包
   * - `illegal_ip_addr`
     - `drop`
     - 丢弃具有非法 SIP/DIP 组播/单播地址的数据包
   * - `illegal_ipv4_hdr`
     - `drop`
     - 丢弃具有非法 IPv4 头的数据包
   * - `ip_uc_dip_da_mismatch`
     - `drop`
     - 丢弃目标 MAC 为单播，但目标 IP 地址为组播的数据包
   * - `ip_sip_is_zero`
     - `drop`
     - 丢弃源地址为零（0）的 IPv4 数据包
   * - `met_red`
     - `drop`
     - 丢弃不符合要求的数据包（入口策略器丢弃、计量丢弃），例如数据包速率超出配置带宽
您没有提供需要翻译的文本。请提供需要翻译成中文的英文或其他语言的文本。
