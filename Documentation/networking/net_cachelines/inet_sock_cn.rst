SPDX 许可证标识符: GPL-2.0
版权 (C) 2023 Google LLC

==========================================
inet_sock 结构快速路径使用情况分析
==========================================

类型                    名称                  快速路径发送访问  快速路径接收访问  注释
..struct                ..inet_sock                                                     
struct_sock             sk                    经常读取            经常读取            tcp_init_buffer_space, tcp_init_transfer, tcp_finish_connect, tcp_connect, tcp_send_rcvq, tcp_send_syn_data
struct_ipv6_pinfo*      pinet6                -                   -                   
be16                    inet_sport            经常读取            -                   __tcp_transmit_skb
be32                    inet_daddr            经常读取            -                   ip_select_ident_segs
be32                    inet_rcv_saddr        -                   -                   
be16                    inet_dport            经常读取            -                   __tcp_transmit_skb
u16                     inet_num              -                   -                   
be32                    inet_saddr            -                   -                   
s16                     uc_ttl                经常读取            -                   __ip_queue_xmit/ip_select_ttl
u16                     cmsg_flags            -                   -                   
struct_ip_options_rcu*  inet_opt              经常读取            -                   __ip_queue_xmit
u16                     inet_id               经常读取            -                   ip_select_ident_segs
u8                      tos                   经常读取            -                   ip_queue_xmit
u8                      min_ttl               -                   -                   
u8                      mc_ttl                -                   -                   
u8                      pmtudisc              -                   -                   
u8:1                    recverr               -                   -                   
u8:1                    is_icsk               -                   -                   
u8:1                    freebind              -                   -                   
u8:1                    hdrincl               -                   -                   
u8:1                    mc_loop               -                   -                   
u8:1                    transparent           -                   -                   
u8:1                    mc_all                -                   -                   
u8:1                    nodefrag              -                   -                   
u8:1                    bind_address_no_port  -                   -                   
u8:1                    recverr_rfc4884       -                   -                   
u8:1                    defer_connect         经常读取            -                   tcp_sendmsg_fastopen
u8                      rcv_tos               -                   -                   
u8                      convert_csum          -                   -                   
int                     uc_index              -                   -                   
int                     mc_index              -                   -                   
be32                    mc_addr               -                   -                   
struct_ip_mc_socklist*  mc_list               -                   -                   
struct_inet_cork_full   cork                  经常读取            -                   __tcp_transmit_skb
struct                  local_port_range      -                   -
