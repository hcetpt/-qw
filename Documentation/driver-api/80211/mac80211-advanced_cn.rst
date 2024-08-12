=============================
mac80211子系统（高级）
=============================

本书这部分的内容仅对那些希望与mac80211进行高级交互以利用更多硬件功能并提高性能的驱动程序开发者感兴趣。
LED支持
===========

mac80211支持各种方式来使LED闪烁。只要可能，设备上的LED应作为LED类设备暴露，并连接到适当的触发器，该触发器将由mac80211适当触发。
.. kernel-doc:: include/net/mac80211.h
   :functions:
	ieee80211_get_tx_led_name
	ieee80211_get_rx_led_name
	ieee80211_get_assoc_led_name
	ieee80211_get_radio_led_name
	ieee80211_tpt_blink
	ieee80211_tpt_led_trigger_flags
	ieee80211_create_tpt_led_trigger

硬件加密加速
============================

.. kernel-doc:: include/net/mac80211.h
   :doc: 硬件加密加速

.. kernel-doc:: include/net/mac80211.h
   :functions:
	set_key_cmd
	ieee80211_key_conf
	ieee80211_key_flags
	ieee80211_get_tkip_p1k
	ieee80211_get_tkip_p1k_iv
	ieee80211_get_tkip_p2k

节能支持
=================

.. kernel-doc:: include/net/mac80211.h
   :doc: 节能支持

信标过滤支持
=====================

.. kernel-doc:: include/net/mac80211.h
   :doc: 信标过滤支持

.. kernel-doc:: include/net/mac80211.h
   :functions: ieee80211_beacon_loss

多队列和QoS支持
===============================

待定

.. kernel-doc:: include/net/mac80211.h
   :functions: ieee80211_tx_queue_params

接入点模式支持
=========================

待定

if_conf的部分内容应该在这里讨论。

在此处插入关于带有硬件加密的VLAN接口的说明，或者在硬件加密章节中。
支持节能客户端
-------------------------------

.. kernel-doc:: include/net/mac80211.h
   :doc: 接入点对节能客户端的支持

.. kernel-doc:: include/net/mac80211.h
   :functions:
	ieee80211_get_buffered_bc
	ieee80211_beacon_get
	ieee80211_sta_eosp
	ieee80211_frame_release_type
	ieee80211_sta_ps_transition
	ieee80211_sta_ps_transition_ni
	ieee80211_sta_set_buffered
	ieee80211_sta_block_awake

支持多个虚拟接口
======================================

待定

注意：WDS使用相同的MAC地址几乎总是可以接受的。

在此处插入有关具有不同MAC地址的多个虚拟接口的信息，注意mac80211支持哪些配置，并添加关于如何支持这些接口上的硬件加密的信息。
.. kernel-doc:: include/net/mac80211.h
   :functions:
	ieee80211_iterate_active_interfaces
	ieee80211_iterate_active_interfaces_atomic

站处理
================

待办事项

.. kernel-doc:: include/net/mac80211.h
   :functions:
	ieee80211_sta
	sta_notify_cmd
	ieee80211_find_sta
	ieee80211_find_sta_by_ifaddr

硬件扫描卸载
=====================

待定

.. kernel-doc:: include/net/mac80211.h
   :functions: ieee80211_scan_completed

聚合
===========

TX A-MPDU聚合
---------------------

.. kernel-doc:: net/mac80211/agg-tx.c
   :doc: TX A-MPDU聚合

RX A-MPDU聚合
---------------------

.. kernel-doc:: net/mac80211/agg-rx.c
   :doc: RX A-MPDU聚合

.. kernel-doc:: include/net/mac80211.h
   :functions: ieee80211_ampdu_mlme_action

空间多重化节能 (SMPS)
=====================================

.. kernel-doc:: include/net/mac80211.h
   :doc: 空间多重化节能

.. kernel-doc:: include/net/mac80211.h
   :functions:
	ieee80211_request_smps
	ieee80211_smps_mode

待定

本书这部分描述了速率控制算法接口及其与mac80211和驱动程序的关系。
速率控制API
================

待定

.. kernel-doc:: include/net/mac80211.h
   :functions:
	ieee80211_start_tx_ba_session
	ieee80211_start_tx_ba_cb_irqsafe
	ieee80211_stop_tx_ba_session
	ieee80211_stop_tx_ba_cb_irqsafe
	ieee80211_rate_control_changed
	ieee80211_tx_rate_control

待定

本书这部分描述了mac80211的内部实现。
密钥处理
============

密钥处理基础
-------------------

.. kernel-doc:: net/mac80211/key.c
   :doc: 密钥处理基础

待续
--------

待定

接收处理
==================

待定

发送处理
==================

待定

站信息处理
=====================

编程信息
-----------------------

.. kernel-doc:: net/mac80211/sta_info.h
   :functions:
	sta_info
	ieee80211_sta_info_flags

STA信息生命周期规则
------------------------------

.. kernel-doc:: net/mac80211/sta_info.c
   :doc: STA信息生命周期规则

聚合函数
=====================

.. kernel-doc:: net/mac80211/sta_info.h
   :functions:
	sta_ampdu_mlme
	tid_ampdu_tx
	tid_ampdu_rx

同步函数
=========================

待定

锁定，大量的RCU
