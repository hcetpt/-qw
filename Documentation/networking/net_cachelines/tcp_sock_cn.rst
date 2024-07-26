### SPDX 许可证标识符: GPL-2.0
### 版权所有 © 2023 Google LLC

=========================================
tcp_sock 结构快速路径使用情况分析
=========================================

类型 | 名称 | 快速发送访问 | 快速接收访问 | 注释
---|---|---|---|---
结构体 | tcp_sock |
结构体 | inet_connection_sock | inet_conn |
u16 | tcp_header_len | 经常读取 | 经常读取 | tcp_bound_to_half_wnd, tcp_current_mss(tx); tcp_rcv_established(rx) |
u16 | gso_segs | 经常读取 | - | tcp_xmit_size_goal |
__be32 | pred_flags | 读写 | 经常读取 | tcp_select_window(tx); tcp_rcv_established(rx) |
u64 | bytes_received | - | 读写 | tcp_rcv_nxt_update(rx) |
u32 | segs_in | - | 读写 | tcp_v6_rcv(rx) |
u32 | data_segs_in | - | 读写 | tcp_v6_rcv(rx) |
u32 | rcv_nxt | 经常读取 | 读写 | tcp_cleanup_rbuf, tcp_send_ack, tcp_inq_hint, tcp_transmit_skb, tcp_receive_window(tx); tcp_v6_do_rcv, tcp_rcv_established, tcp_data_queue, tcp_receive_window, tcp_rcv_nxt_update(写)(rx) |
u32 | copied_seq | - | 经常读取 | tcp_cleanup_rbuf, tcp_rcv_space_adjust, tcp_inq_hint |
u32 | rcv_wup | - | 读写 | __tcp_cleanup_rbuf, tcp_receive_window, tcp_receive_established |
u32 | snd_nxt | 读写 | 经常读取 | tcp_rate_check_app_limited, __tcp_transmit_skb, tcp_event_new_data_sent(写)(tx); tcp_rcv_established, tcp_ack, tcp_clean_rtx_queue(rx) |
u32 | segs_out | 读写 | - | __tcp_transmit_skb |
u32 | data_segs_out | 读写 | - | __tcp_transmit_skb, tcp_update_skb_after_send |
u64 | bytes_sent | 读写 | - | __tcp_transmit_skb |
u64 | bytes_acked | - | 读写 | tcp_snd_una_update/tcp_ack |
u32 | dsack_dups | |
u32 | snd_una | 经常读取 | 读写 | tcp_wnd_end, tcp_urg_mode, tcp_minshall_check, tcp_cwnd_validate(tx); tcp_ack, tcp_may_update_window, tcp_clean_rtx_queue(写), tcp_ack_tstamp(rx) |
u32 | snd_sml | 读写 | - | tcp_minshall_check, tcp_minshall_update |
u32 | rcv_tstamp | - | 经常读取 | tcp_ack |
u32 | lsndtime | 读写 | - | tcp_slow_start_after_idle_check, tcp_event_data_sent |
u32 | last_oow_ack_time | |
u32 | compressed_ack_rcv_nxt | |
u32 | tsoffset | 经常读取 | 经常读取 | tcp_established_options(tx); tcp_fast_parse_options(rx) |
列表头 | tsq_node | - | - |
列表头 | tsorted_sent_queue | 读写 | - | tcp_update_skb_after_send |
u32 | snd_wl1 | - | 经常读取 | tcp_may_update_window |
u32 | snd_wnd | 经常读取 | 经常读取 | tcp_wnd_end, tcp_tso_should_defer(tx); tcp_fast_path_on(rx) |
u32 | max_window | 经常读取 | - | tcp_bound_to_half_wnd, forced_push |
u32 | mss_cache | 经常读取 | 经常读取 | tcp_rate_check_app_limited, tcp_current_mss, tcp_sync_mss, tcp_sndbuf_expand, tcp_tso_should_defer(tx); tcp_update_pacing_rate, tcp_clean_rtx_queue(rx) |
u32 | window_clamp | 经常读取 | 读写 | tcp_rcv_space_adjust, __tcp_select_window |
u32 | rcv_ssthresh | 经常读取 | - | __tcp_select_window |
u8 | scaling_ratio | 经常读取 | 经常读取 | tcp_win_from_space |
结构体 | tcp_rack |
u16 | advmss | - | 经常读取 | tcp_rcv_space_adjust |
u8 | compressed_ack | |
u8:2 | dup_ack_counter | |
u8:1 | tlp_retrans | |
u8:1 | tcp_usec_ts | 经常读取 | 经常读取 |
u32 | chrono_start | 读写 | - | tcp_chrono_start/stop(tcp_write_xmit, tcp_cwnd_validate, tcp_send_syn_data) |
u32[3] | chrono_stat | 读写 | - | tcp_chrono_start/stop(tcp_write_xmit, tcp_cwnd_validate, tcp_send_syn_data) |
u8:2 | chrono_type | 读写 | - | tcp_chrono_start/stop(tcp_write_xmit, tcp_cwnd_validate, tcp_send_syn_data) |
u8:1 | rate_app_limited | - | 读写 | tcp_rate_gen |
u8:1 | fastopen_connect | |
u8:1 | fastopen_no_cookie | |
u8:1 | is_sack_reneg | - | 经常读取 | tcp_skb_entail, tcp_ack |
u8:2 | fastopen_client_fail | |
u8:4 | nonagle | 读写 | - | tcp_skb_entail, tcp_push_pending_frames |
u8:1 | thin_lto | |
u8:1 | recvmsg_inq | |
u8:1 | repair | 经常读取 | - | tcp_write_xmit |
u8:1 | frto | |
u8 | repair_queue | - | - |
u8:2 | save_syn | |
u8:1 | syn_data | |
u8:1 | syn_fastopen | |
u8:1 | syn_fastopen_exp | |
u8:1 | syn_fastopen_ch | |
u8:1 | syn_data_acked | |
u8:1 | is_cwnd_limited | 经常读取 | - | tcp_cwnd_validate, tcp_is_cwnd_limited |
u32 | tlp_high_seq | - | 经常读取 | tcp_ack |
u32 | tcp_tx_delay | |
u64 | tcp_wstamp_ns | 读写 | - | tcp_pacing_check, tcp_tso_should_defer, tcp_update_skb_after_send |
u64 | tcp_clock_cache | 读写 | 读写 | tcp_mstamp_refresh(tcp_write_xmit/tcp_rcv_space_adjust), __tcp_transmit_skb, tcp_tso_should_defer; 定时器 |
u64 | tcp_mstamp | 读写 | 读写 | tcp_mstamp_refresh(tcp_write_xmit/tcp_rcv_space_adjust)(tx); tcp_rcv_space_adjust, tcp_rate_gen, tcp_clean_rtx_queue, tcp_ack_update_rtt/tcp_time_stamp(rx); 定时器 |
u32 | srtt_us | 经常读取 | 读写 | tcp_tso_should_defer(tx); tcp_update_pacing_rate, __tcp_set_rto, tcp_rtt_estimator(rx) |
u32 | mdev_us | 读写 | - | tcp_rtt_estimator |
u32 | mdev_max_us | |
u32 | rttvar_us | - | 经常读取 | __tcp_set_rto |
u32 | rtt_seq | 读写 | | tcp_rtt_estimator |
最小最大值结构 | rtt_min | - | 经常读取 | tcp_min_rtt/tcp_rate_gen, tcp_min_rtttcp_update_rtt_min |
u32 | packets_out | 读写 | 读写 | tcp_packets_in_flight(tx/rx); tcp_slow_start_after_idle_check, tcp_nagle_check, tcp_rate_skb_sent, tcp_event_new_data_sent, tcp_cwnd_validate, tcp_write_xmit(tx); tcp_ack, tcp_clean_rtx_queue, tcp_update_pacing_rate(rx) |
u32 | retrans_out | - | 经常读取 | tcp_packets_in_flight, tcp_rate_check_app_limited |
u32 | max_packets_out | - | 读写 | tcp_cwnd_validate |
u32 | cwnd_usage_seq | - | 读写 | tcp_cwnd_validate |
u16 | urg_data | - | 经常读取 | tcp_fast_path_check |
u8 | ecn_flags | 读写 | - | tcp_ecn_send |
u8 | keepalive_probes | |
u32 | reordering | 经常读取 | - | tcp_sndbuf_expand |
u32 | reord_seen | |
u32 | snd_up | 读写 | 经常读取 | tcp_mark_urg, tcp_urg_mode, __tcp_transmit_skb(tx); tcp_clean_rtx_queue(rx) |
结构体 | tcp_options_received | rx_opt | 经常读取 | 读写 | tcp_established_options(tx); tcp_fast_path_on, tcp_ack_update_window, tcp_is_sack, tcp_data_queue, tcp_rcv_established, tcp_ack_update_rtt(rx) |
u32 | snd_ssthresh | - | 经常读取 | tcp_update_pacing_rate |
u32 | snd_cwnd | 经常读取 | 经常读取 | tcp_snd_cwnd, tcp_rate_check_app_limited, tcp_tso_should_defer(tx); tcp_update_pacing_rate |
u32 | snd_cwnd_cnt | |
u32 | snd_cwnd_clamp | |
u32 | snd_cwnd_used | |
u32 | snd_cwnd_stamp | |
u32 | prior_cwnd | |
u32 | prr_delivered | |
u32 | prr_out | 经常读取 | 经常读取 | tcp_rate_skb_sent, tcp_newly_delivered(tx); tcp_ack, tcp_rate_gen, tcp_clean_rtx_queue(rx) |
u32 | delivered | 经常读取 | 读写 | tcp_rate_skb_sent, tcp_newly_delivered(tx); tcp_ack, tcp_rate_gen, tcp_clean_rtx_queue(rx) |
u32 | delivered_ce | 经常读取 | 读写 | tcp_rate_skb_sent(tx); tcp_rate_gen(rx) |
u32 | lost | - | 经常读取 | tcp_ack |
u32 | app_limited | 读写 | 经常读取 | tcp_rate_check_app_limited, tcp_rate_skb_sent(tx); tcp_rate_gen(rx) |
u64 | first_tx_mstamp | 读写 | - | tcp_rate_skb_sent |
u64 | delivered_mstamp | 读写 | - | tcp_rate_skb_sent |
u32 | rate_delivered | - | 经常读取 | tcp_rate_gen |
u32 | rate_interval_us | - | 经常读取 | rate_delivered, rate_app_limited |
u32 | rcv_wnd | 读写 | 经常读取 | tcp_select_window, tcp_receive_window, tcp_fast_path_check |
u32 | write_seq | 读写 | - | tcp_rate_check_app_limited, tcp_write_queue_empty, tcp_skb_entail, forced_push, tcp_mark_push |
u32 | notsent_lowat | 经常读取 | - | tcp_stream_memory_free |
u32 | pushed_seq | 读写 | - | tcp_mark_push, forced_push |
u32 | lost_out | 经常读取 | 经常读取 | tcp_left_out(tx); tcp_packets_in_flight(tx/rx); tcp_rate_check_app_limited(rx) |
u32 | sacked_out | 经常读取 | 经常读取 | tcp_left_out(tx); tcp_packets_in_flight(tx/rx); tcp_clean_rtx_queue(rx) |
定时器 | pacing_timer | |
定时器 | compressed_ack_timer | |
struct_sk_buff* | lost_skb_hint | 经常读取 | | tcp_clean_rtx_queue |
struct_sk_buff* | retransmit_skb_hint | 经常读取 | - | tcp_clean_rtx_queue |
红黑树根 | out_of_order_queue | - | 经常读取 | tcp_data_queue, tcp_fast_path_check |
struct_sk_buff* | ooo_last_skb | |
tcp_sack_block[1] | duplicate_sack | |
tcp_sack_block[4] | selective_acks | |
tcp_sack_block[4] | recv_sack_cache | |
struct_sk_buff* | highest_sack | 读写 | - | tcp_event_new_data_sent |
int | lost_cnt_hint | |
u32 | prior_ssthresh | |
u32 | high_seq | |
u32 | retrans_stamp | |
u32 | undo_marker | |
int | undo_retrans | |
u64 | bytes_retrans | |
u32 | total_retrans | |
u32 | rto_stamp | |
u16 | total_rto | |
u16 | total_rto_recoveries | |
u32 | total_rto_time | |
u32 | urg_seq | - | - |
无符号整型 | keepalive_time | |
无符号整型 | keepalive_intvl | |
整型 | linger2 | |
u8 | bpf_sock_ops_cb_flags | |
u8:1 | bpf_chg_cc_inprogress | |
u16 | timeout_rehash | |
u32 | rcv_ooopack | |
u32 | rcv_rtt_last_tsecr | |
结构体 | rcv_rtt_est | - | 读写 | tcp_rcv_space_adjust, tcp_rcv_established |
结构体 | rcvq_space | - | 读写 | tcp_rcv_space_adjust |
结构体 | mtu_probe | |
u32 | plb_rehash | |
u32 | mtu_info | |
布尔 | is_mptcp | |
布尔 | smc_hs_congested | |
布尔 | syn_smc | |
结构体指针 | tcp_sock_af_ops | af_specific | |
结构体指针 | tcp_md5sig_info | md5sig_info | |
结构体指针 | tcp_fastopen_request | fastopen_req | |
结构体指针 | request_sock | fastopen_rsk | |
结构体指针 | saved_syn | saved_syn |
