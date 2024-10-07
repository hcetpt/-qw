SPDX 许可证标识符: GPL-2.0

========================
Prestera devlink 支持
========================

本文档描述了由 ``prestera`` 设备驱动程序实现的 devlink 功能。
驱动程序特定的陷阱
=====================

.. list-table:: 由 ``prestera`` 注册的驱动程序特定陷阱列表
   :widths: 5 5 90

   * - 名称
     - 类型
     - 描述

.. list-table:: 由 ``prestera`` 注册的驱动程序特定陷阱列表
   :widths: 5 5 90

   * - 名称
     - 类型
     - 描述
   * - ``arp_bc``
     - ``trap``
     - 捕获 ARP 广播包（请求和响应）
   * - ``is_is``
     - ``trap``
     - 捕获 IS-IS 包
   * - ``ospf``
     - ``trap``
     - 捕获 OSPF 包
   * - ``ip_bc_mac``
     - ``trap``
     - 捕获带有广播目的 MAC 地址的 IPv4 包
   * - ``stp``
     - ``trap``
     - 捕获 STP BPDU
   * - ``lacp``
     - ``trap``
     - 捕获 LACP 包
   * - ``lldp``
     - ``trap``
     - 捕获 LLDP 包
   * - ``router_mc``
     - ``trap``
     - 捕获组播包
   * - ``vrrp``
     - ``trap``
     - 捕获 VRRP 包
   * - ``dhcp``
     - ``trap``
     - 捕获 DHCP 包
   * - ``mtu_error``
     - ``trap``
     - 捕获超出端口 MTU 的包（异常）
   * - ``mac_to_me``
     - ``trap``
     - 捕获具有交换端口目的 MAC 地址的包
   * - ``ttl_error``
     - ``trap``
     - 捕获 TTL 超出的 IPv4 包（异常）
   * - ``ipv4_options``
     - ``trap``
     - 捕获由于畸形的 IPv4 头选项而导致的包（异常）
   * - ``ip_default_route``
     - ``trap``
     - 捕获没有特定 IP 接口（IP 到我）且没有转发前缀的包
   * - ``local_route``
     - ``trap``
     - 捕获发送到交换机 IP 接口地址之一的包
   * - ``ipv4_icmp_redirect``
     - ``trap``
     - 捕获 IPv4 ICMP 重定向包（异常）
   * - ``arp_response``
     - ``trap``
     - 捕获具有交换端口目的 MAC 地址的 ARP 回应包
   * - ``acl_code_0``
     - ``trap``
     - 捕获具有 ACL 优先级设置为 0（tc pref 0）的包
   * - ``acl_code_1``
     - ``trap``
     - 捕获具有 ACL 优先级设置为 1（tc pref 1）的包
   * - ``acl_code_2``
     - ``trap``
     - 捕获具有 ACL 优先级设置为 2（tc pref 2）的包
   * - ``acl_code_3``
     - ``trap``
     - 捕获具有 ACL 优先级设置为 3（tc pref 3）的包
   * - ``acl_code_4``
     - ``trap``
     - 捕获具有 ACL 优先级设置为 4（tc pref 4）的包
   * - ``acl_code_5``
     - ``trap``
     - 捕获具有 ACL 优先级设置为 5（tc pref 5）的包
   * - ``acl_code_6``
     - ``trap``
     - 捕获具有 ACL 优先级设置为 6（tc pref 6）的包
   * - ``acl_code_7``
     - ``trap``
     - 捕获具有 ACL 优先级设置为 7（tc pref 7）的包
   * - ``ipv4_bgp``
     - ``trap``
     - 捕获 IPv4 BGP 包
   * - ``ssh``
     - ``trap``
     - 捕获 SSH 包
   * - ``telnet``
     - ``trap``
     - 捕获 Telnet 包
   * - ``icmp``
     - ``trap``
     - 捕获 ICMP 包
   * - ``rxdma_drop``
     - ``drop``
     - 丢弃包（RxDMA），因为缺乏入口缓冲区等
   * - ``port_no_vlan``
     - ``drop``
     - 丢弃包，因为网络配置错误或内部 bug（配置问题）
   * - ``local_port``
     - ``drop``
     - 丢弃包，因为决策（FDB 条目）是将包桥接到进入端口/链路
   * - ``invalid_sa``
     - ``drop``
     - 丢弃具有多播源 MAC 地址的包
   * - ``illegal_ip_addr``
     - ``drop``
     - 丢弃具有非法 SIP/DIP 多播/单播地址的包
   * - ``illegal_ipv4_hdr``
     - ``drop``
     - 丢弃具有非法 IPv4 头的包
   * - ``ip_uc_dip_da_mismatch``
     - ``drop``
     - 丢弃具有单播目的 MAC 但多播目的 IP 地址的包
   * - ``ip_sip_is_zero``
     - ``drop``
     - 丢弃具有零（0）IPv4 源地址的包
   * - ``met_red``
     - ``drop``
     - 丢弃不符合规定的包（被入口策略器丢弃、计费丢弃），例如包速率超过配置带宽
当然，请提供你需要翻译的文本。
