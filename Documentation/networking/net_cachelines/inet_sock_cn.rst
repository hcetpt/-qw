### SPDX 许可证标识符: GPL-2.0
### 版权所有 (C) 2023 Google LLC

==========================================
`inet_sock` 结构快速路径使用情况细分
==========================================

类型 | 名称 | 快速路径发送访问 | 快速路径接收访问 | 注释
---|---|---|---|---
结构体 | `inet_sock` ||
结构体_sock | `sk` | 大部分读取 | 大部分读取 | `tcp_init_buffer_space`, `tcp_init_transfer`, `tcp_finish_connect`, `tcp_connect`, `tcp_send_rcvq`, `tcp_send_syn_data`
指针(struct_ipv6_pinfo*) | `pinet6` | - | - |
基本整型(16位, 大端) | `inet_sport` | 大部分读取 | - | `__tcp_transmit_skb`
基本整型(32位, 大端) | `inet_daddr` | 大部分读取 | - | `ip_select_ident_segs`
基本整型(32位, 大端) | `inet_rcv_saddr` | - | - |
基本整型(16位, 大端) | `inet_dport` | 大部分读取 | - | `__tcp_transmit_skb`
无符号16位整型 | `inet_num` | - | - |
基本整型(32位, 大端) | `inet_saddr` | - | - |
有符号16位整型 | `uc_ttl` | 大部分读取 | - | `__ip_queue_xmit`, `ip_select_ttl`
无符号16位整型 | `cmsg_flags` | - | - |
指针(struct_ip_options_rcu*) | `inet_opt` | 大部分读取 | - | `__ip_queue_xmit`
无符号16位整型 | `inet_id` | 大部分读取 | - | `ip_select_ident_segs`
无符号8位整型 | `tos` | 大部分读取 | - | `ip_queue_xmit`
无符号8位整型 | `min_ttl` | - | - |
无符号8位整型 | `mc_ttl` | - | - |
无符号8位整型 | `pmtudisc` | - | - |
8位整型:1 | `recverr` | - | - |
8位整型:1 | `is_icsk` | - | - |
8位整型:1 | `freebind` | - | - |
8位整型:1 | `hdrincl` | - | - |
8位整型:1 | `mc_loop` | - | - |
8位整型:1 | `transparent` | - | - |
8位整型:1 | `mc_all` | - | - |
8位整型:1 | `nodefrag` | - | - |
8位整型:1 | `bind_address_no_port` | - | - |
8位整型:1 | `recverr_rfc4884` | - | - |
8位整型:1 | `defer_connect` | 大部分读取 | - | `tcp_sendmsg_fastopen`
无符号8位整型 | `rcv_tos` | - | - |
无符号8位整型 | `convert_csum` | - | - |
整型 | `uc_index` | - | - |
整型 | `mc_index` | - | - |
基本整型(32位, 大端) | `mc_addr` | - | - |
指针(struct_ip_mc_socklist*) | `mc_list` | - | - |
结构体(struct_inet_cork_full) | `cork` | 大部分读取 | - | `__tcp_transmit_skb`
结构体 | `local_port_range` | - | - |
