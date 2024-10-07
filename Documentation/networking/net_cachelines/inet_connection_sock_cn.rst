.. SPDX 许可证标识符: GPL-2.0
.. 版权所有 (C) 2023 Google LLC

=====================================================
inet_connection_sock 结构的快速路径使用分析
=====================================================

类型                                名称                   快速路径发送访问  快速路径接收访问  注释
..struct                            ..inet_connection_sock                                         
struct_inet_sock                    icsk_inet              大部分读取         大部分读取         tcp_init_buffer_space, tcp_init_transfer, tcp_finish_connect, tcp_connect, tcp_send_rcvq, tcp_send_syn_data
struct_request_sock_queue           icsk_accept_queue      -                   -                   
struct_inet_bind_bucket             icsk_bind_hash         大部分读取         -                   tcp_set_state
struct_inet_bind2_bucket            icsk_bind2_hash        大部分读取         -                   tcp_set_state, inet_put_port
unsigned_long                       icsk_timeout           大部分读取         -                   inet_csk_reset_xmit_timer, tcp_connect
struct_timer_list                   icsk_retransmit_timer  大部分读取         -                   inet_csk_reset_xmit_timer, tcp_connect
struct_timer_list                   icsk_delack_timer      大部分读取         -                   inet_csk_reset_xmit_timer, tcp_connect
u32                                 icsk_rto               读写              -                   tcp_cwnd_validate, tcp_schedule_loss_probe, tcp_connect_init, tcp_connect, tcp_write_xmit, tcp_push_one
u32                                 icsk_rto_min           -                   -                   
u32                                 icsk_delack_max        -                   -                   
u32                                 icsk_pmtu_cookie       读写              -                   tcp_sync_mss, tcp_current_mss, tcp_send_syn_data, tcp_connect_init, tcp_connect
struct_tcp_congestion_ops           icsk_ca_ops            读写              -                   tcp_cwnd_validate, tcp_tso_segs, tcp_ca_dst_init, tcp_connect_init, tcp_connect, tcp_write_xmit
struct_inet_connection_sock_af_ops  icsk_af_ops            大部分读取         -                   tcp_finish_connect, tcp_send_syn_data, tcp_mtup_init, tcp_mtu_check_reprobe, tcp_mtu_probe, tcp_connect_init, tcp_connect, __tcp_transmit_skb
struct_tcp_ulp_ops*                 icsk_ulp_ops           -                   -                   
void*                               icsk_ulp_data          -                   -                   
u8:5                                icsk_ca_state          读写              -                   tcp_cwnd_application_limited, tcp_set_ca_state, tcp_enter_cwr, tcp_tso_should_defer, tcp_mtu_probe, tcp_schedule_loss_probe, tcp_write_xmit, __tcp_transmit_skb
u8:1                                icsk_ca_initialized    读写              -                   tcp_init_transfer, tcp_init_congestion_control, tcp_init_transfer, tcp_finish_connect, tcp_connect
u8:1                                icsk_ca_setsockopt     -                   -                   
u8:1                                icsk_ca_dst_locked     大部分写入         -                   tcp_ca_dst_init, tcp_connect_init, tcp_connect
u8                                  icsk_retransmits       大部分写入         -                   tcp_connect_init, tcp_connect
u8                                  icsk_pending           读写              -                   inet_csk_reset_xmit_timer, tcp_connect, tcp_check_probe_timer, __tcp_push_pending_frames, tcp_rearm_rto, tcp_event_new_data_sent, tcp_event_new_data_sent
u8                                  icsk_backoff           大部分写入         -                   tcp_write_queue_purge, tcp_connect_init
u8                                  icsk_syn_retries       -                   -                   
u8                                  icsk_probes_out        -                   -                   
u16                                 icsk_ext_hdr_len       大部分读取         -                   __tcp_mtu_to_mss, tcp_mtu_to_rss, tcp_mtu_probe, tcp_write_xmit, tcp_mtu_to_mss,
struct_icsk_ack_u8                  pending                读写              读写              inet_csk_ack_scheduled, __tcp_cleanup_rbuf, tcp_cleanup_rbuf, inet_csk_clear_xmit_timer, tcp_event_ack_sent, inet_csk_reset_xmit_timer
struct_icsk_ack_u8                  quick                  读写              大部分写入         tcp_dec_quickack_mode, tcp_event_ack_sent, __tcp_transmit_skb, __tcp_select_window, __tcp_cleanup_rbuf
struct_icsk_ack_u8                  pingpong               -                   -                   
struct_icsk_ack_u8                  retry                  大部分写入         读写              inet_csk_clear_xmit_timer, tcp_rearm_rto, tcp_event_new_data_sent, tcp_write_xmit, __tcp_send_ack, tcp_send_ack,
struct_icsk_ack_u8                  ato                    大部分读取         大部分写入         tcp_dec_quickack_mode, tcp_event_ack_sent, __tcp_transmit_skb, __tcp_send_ack, tcp_send_ack
struct_icsk_ack_unsigned_long       timeout                读写              读写              inet_csk_reset_xmit_timer, tcp_connect
struct_icsk_ack_u32                 lrcvtime               读写              -                   tcp_finish_connect, tcp_connect, tcp_event_data_sent, __tcp_transmit_skb
struct_icsk_ack_u16                 rcv_mss                大部分写入         大部分读取         __tcp_select_window, __tcp_cleanup_rbuf, tcp_initialize_rcv_mss, tcp_connect_init
struct_icsk_mtup_int                search_high            读写              -                   tcp_mtup_init, tcp_sync_mss, tcp_connect_init, tcp_mtu_check_reprobe, tcp_write_xmit
struct_icsk_mtup_int                search_low             读写              -                   tcp_mtu_probe, tcp_mtu_check_reprobe, tcp_write_xmit, tcp_sync_mss, tcp_connect_init, tcp_mtup_init
struct_icsk_mtup_u32:31             probe_size             读写              -                   tcp_mtup_init, tcp_connect_init, __tcp_transmit_skb
struct_icsk_mtup_u32:1              enabled                读写              -                   tcp_mtup_init, tcp_sync_mss, tcp_connect_init, tcp_mtu_probe, tcp_write_xmit
struct_icsk_mtup_u32                probe_timestamp        读写              -                   tcp_mtup_init, tcp_connect_init, tcp_mtu_check_reprobe, tcp_mtu_probe
u32                                 icsk_probes_tstamp     -                   -                   
u32                                 icsk_user_timeout      -                   -                   
u64[104/sizeof(u64)]                icsk_ca_priv           -                   -
