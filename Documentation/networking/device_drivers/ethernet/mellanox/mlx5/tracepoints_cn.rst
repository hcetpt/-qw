```
SPDX 许可证标识符: GPL-2.0 或 Linux-OpenIB
.. include:: <isonum.txt>

===========
追踪点
===========

:版权: © 2023，NVIDIA CORPORATION 及其关联公司。保留所有权利。
mlx5 驱动程序提供了用于跟踪和调试的内部追踪点，使用内核追踪点接口（参考 Documentation/trace/ftrace.rst）。
对于支持的 mlx5 事件列表，请检查 /sys/kernel/tracing/events/mlx5/。
TC 和交换卸载追踪点：

- mlx5e_configure_flower: 追踪卸载到 mlx5 的花形过滤器动作和 cookie ::

    $ echo mlx5:mlx5e_configure_flower >> /sys/kernel/tracing/set_event
    $ cat /sys/kernel/tracing/trace
    ..
    tc-6535  [019] ...1  2672.404466: mlx5e_configure_flower: cookie=0000000067874a55 actions= REDIRECT

- mlx5e_delete_flower: 追踪从 mlx5 删除的花形过滤器动作和 cookie ::

    $ echo mlx5:mlx5e_delete_flower >> /sys/kernel/tracing/set_event
    $ cat /sys/kernel/tracing/trace
    ..
    tc-6569  [010] .N.1  2686.379075: mlx5e_delete_flower: cookie=0000000067874a55 actions= NULL

- mlx5e_stats_flower: 追踪花形统计请求 ::

    $ echo mlx5:mlx5e_stats_flower >> /sys/kernel/tracing/set_event
    $ cat /sys/kernel/tracing/trace
    ..
    tc-6546  [010] ...1  2679.704889: mlx5e_stats_flower: cookie=0000000060eb3d6a bytes=0 packets=0 lastused=4295560217

- mlx5e_tc_update_neigh_used_value: 追踪卸载到 mlx5 的隧道规则邻接更新值 ::

    $ echo mlx5:mlx5e_tc_update_neigh_used_value >> /sys/kernel/tracing/set_event
    $ cat /sys/kernel/tracing/trace
    ..
    kworker/u48:4-8806  [009] ...1 55117.882428: mlx5e_tc_update_neigh_used_value: netdev: ens1f0 IPv4: 1.1.1.10 IPv6: ::ffff:1.1.1.10 neigh_used=1

- mlx5e_rep_neigh_update: 追踪由于邻接状态变更事件而调度的邻接更新任务 ::

    $ echo mlx5:mlx5e_rep_neigh_update >> /sys/kernel/tracing/set_event
    $ cat /sys/kernel/tracing/trace
    ..
    kworker/u48:7-2221  [009] ...1  1475.387435: mlx5e_rep_neigh_update: netdev: ens1f0 MAC: 24:8a:07:9a:17:9a IPv4: 1.1.1.10 IPv6: ::ffff:1.1.1.10 neigh_connected=1

桥接卸载追踪点：

- mlx5_esw_bridge_fdb_entry_init: 追踪卸载到 mlx5 的桥接 FDB 条目 ::

    $ echo mlx5:mlx5_esw_bridge_fdb_entry_init >> set_event
    $ cat /sys/kernel/tracing/trace
    ..
    kworker/u20:9-2217    [003] ...1   318.582243: mlx5_esw_bridge_fdb_entry_init: net_device=enp8s0f0_0 addr=e4:fd:05:08:00:02 vid=0 flags=0 used=0

- mlx5_esw_bridge_fdb_entry_cleanup: 追踪从 mlx5 删除的桥接 FDB 条目 ::

    $ echo mlx5:mlx5_esw_bridge_fdb_entry_cleanup >> set_event
    $ cat /sys/kernel/tracing/trace
    ..
```
```plaintext
ip-2581    [005] ...1   318.629871: mlx5_esw_bridge_fdb_entry_cleanup: net_device=enp8s0f0_1 addr=e4:fd:05:08:00:03 vid=0 flags=0 used=16

- mlx5_esw_bridge_fdb_entry_refresh: 跟踪 mlx5 中的桥接 FDB 条目卸载刷新情况::

    $ echo mlx5:mlx5_esw_bridge_fdb_entry_refresh >> set_event
    $ cat /sys/kernel/tracing/trace
    ..
kworker/u20:8-3849    [003] ...1       466716: mlx5_esw_bridge_fdb_entry_refresh: net_device=enp8s0f0_0 addr=e4:fd:05:08:00:02 vid=3 flags=0 used=0

- mlx5_esw_bridge_vlan_create: 跟踪 mlx5 表示器上的桥接 VLAN 对象添加情况::

    $ echo mlx5:mlx5_esw_bridge_vlan_create >> set_event
    $ cat /sys/kernel/tracing/trace
    ..
ip-2560    [007] ...1   318.460258: mlx5_esw_bridge_vlan_create: vid=1 flags=6

- mlx5_esw_bridge_vlan_cleanup: 跟踪从 mlx5 表示器删除桥接 VLAN 对象的情况::

    $ echo mlx5:mlx5_esw_bridge_vlan_cleanup >> set_event
    $ cat /sys/kernel/tracing/trace
    ..
bridge-2582    [007] ...1   318.653496: mlx5_esw_bridge_vlan_cleanup: vid=2 flags=8

- mlx5_esw_bridge_vport_init: 跟踪与桥接上层设备关联的 mlx5 端口分配情况::

    $ echo mlx5:mlx5_esw_bridge_vport_init >> set_event
    $ cat /sys/kernel/tracing/trace
    ..
ip-2560    [007] ...1   318.458915: mlx5_esw_bridge_vport_init: vport_num=1

- mlx5_esw_bridge_vport_cleanup: 跟踪从桥接上层设备移除 mlx5 端口的情况::

    $ echo mlx5:mlx5_esw_bridge_vport_cleanup >> set_event
    $ cat /sys/kernel/tracing/trace
    ..
ip-5387    [000] ...1       573713: mlx5_esw_bridge_vport_cleanup: vport_num=1

Eswitch QoS 跟踪点:

- mlx5_esw_vport_qos_create: 跟踪为端口创建传输调度仲裁器的情况::

    $ echo mlx5:mlx5_esw_vport_qos_create >> /sys/kernel/tracing/set_event
    $ cat /sys/kernel/tracing/trace
    ..
<...>-23496   [018] .... 73136.838831: mlx5_esw_vport_qos_create: (0000:82:00.0) vport=2 tsar_ix=4 bw_share=0, max_rate=0 group=000000007b576bb3

- mlx5_esw_vport_qos_config: 跟踪配置端口传输调度仲裁器的情况::

    $ echo mlx5:mlx5_esw_vport_qos_config >> /sys/kernel/tracing/set_event
    $ cat /sys/kernel/tracing/trace
    ..
<...>-26548   [023] .... 75754.223823: mlx5_esw_vport_qos_config: (0000:82:00.0) vport=1 tsar_ix=3 bw_share=34, max_rate=10000 group=000000007b576bb3

- mlx5_esw_vport_qos_destroy: 跟踪删除端口传输调度仲裁器的情况::

    $ echo mlx5:mlx5_esw_vport_qos_destroy >> /sys/kernel/tracing/set_event
    $ cat /sys/kernel/tracing/trace
    ..
<...>-27418   [004] .... 76546.680901: mlx5_esw_vport_qos_destroy: (0000:82:00.0) vport=1 tsar_ix=3

- mlx5_esw_group_qos_create: 跟踪为速率组创建传输调度仲裁器的情况::

    $ echo mlx5:mlx5_esw_group_qos_create >> /sys/kernel/tracing/set_event
    $ cat /sys/kernel/tracing/trace
    ..
<...>-26578   [008] .... 75776.022112: mlx5_esw_group_qos_create: (0000:82:00.0) group=000000008dac63ea tsar_ix=5

- mlx5_esw_group_qos_config: 跟踪配置速率组传输调度仲裁器的情况::

    $ echo mlx5:mlx5_esw_group_qos_config >> /sys/kernel/tracing/set_event
    $ cat /sys/kernel/tracing/trace
    ..
```

以上是将英文内容翻译成中文的结果。
```plaintext
<...>-27303   [020] .... 76461.455356: mlx5_esw_group_qos_config: (0000:82:00.0) group=000000008dac63ea tsar_ix=5 bw_share=100 max_rate=20000

- mlx5_esw_group_qos_destroy: 跟踪传输调度仲裁器的删除：

    $ echo mlx5:mlx5_esw_group_qos_destroy >> /sys/kernel/tracing/set_event
    $ cat /sys/kernel/tracing/trace
    ..
<...>-27418   [006] .... 76547.187258: mlx5_esw_group_qos_destroy: (0000:82:00.0) group=000000007b576bb3 tsar_ix=1

SF tracepoints（跟踪点）：

- mlx5_sf_add: 跟踪SF端口的添加：

    $ echo mlx5:mlx5_sf_add >> /sys/kernel/tracing/set_event
    $ cat /sys/kernel/tracing/trace
    ..
devlink-9363    [031] ..... 24610.188722: mlx5_sf_add: (0000:06:00.0) port_index=32768 controller=0 hw_id=0x8000 sfnum=88

- mlx5_sf_free: 跟踪SF端口的释放：

    $ echo mlx5:mlx5_sf_free >> /sys/kernel/tracing/set_event
    $ cat /sys/kernel/tracing/trace
    ..
devlink-9830    [038] ..... 26300.404749: mlx5_sf_free: (0000:06:00.0) port_index=32768 controller=0 hw_id=0x8000

- mlx5_sf_activate: 跟踪SF端口的激活：

    $ echo mlx5:mlx5_sf_activate >> /sys/kernel/tracing/set_event
    $ cat /sys/kernel/tracing/trace
    ..
devlink-29841   [008] .....  3669.635095: mlx5_sf_activate: (0000:08:00.0) port_index=32768 controller=0 hw_id=0x8000

- mlx5_sf_deactivate: 跟踪SF端口的去激活：

    $ echo mlx5:mlx5_sf_deactivate >> /sys/kernel/tracing/set_event
    $ cat /sys/kernel/tracing/trace
    ..
devlink-29994   [008] .....  4015.969467: mlx5_sf_deactivate: (0000:08:00.0) port_index=32768 controller=0 hw_id=0x8000

- mlx5_sf_hwc_alloc: 跟踪硬件SF上下文的分配：

    $ echo mlx5:mlx5_sf_hwc_alloc >> /sys/kernel/tracing/set_event
    $ cat /sys/kernel/tracing/trace
    ..
devlink-9775    [031] ..... 26296.385259: mlx5_sf_hwc_alloc: (0000:06:00.0) controller=0 hw_id=0x8000 sfnum=88

- mlx5_sf_hwc_free: 跟踪硬件SF上下文的释放：

    $ echo mlx5:mlx5_sf_hwc_free >> /sys/kernel/tracing/set_event
    $ cat /sys/kernel/tracing/trace
    ..
kworker/u128:3-9093    [046] ..... 24625.365771: mlx5_sf_hwc_free: (0000:06:00.0) hw_id=0x8000

- mlx5_sf_hwc_deferred_free: 跟踪硬件SF上下文的延迟释放：

    $ echo mlx5:mlx5_sf_hwc_deferred_free >> /sys/kernel/tracing/set_event
    $ cat /sys/kernel/tracing/trace
    ..
devlink-9519    [046] ..... 24624.400271: mlx5_sf_hwc_deferred_free: (0000:06:00.0) hw_id=0x8000

- mlx5_sf_update_state: 跟踪SF上下文的状态更新：

    $ echo mlx5:mlx5_sf_update_state >> /sys/kernel/tracing/set_event
    $ cat /sys/kernel/tracing/trace
    ..
kworker/u20:3-29490   [009] .....  4141.453530: mlx5_sf_update_state: (0000:08:00.0) port_index=32768 controller=0 hw_id=0x8000 state=2

- mlx5_sf_vhca_event: 跟踪SF vhca 事件和状态：

    $ echo mlx5:mlx5_sf_vhca_event >> /sys/kernel/tracing/set_event
    $ cat /sys/kernel/tracing/trace
    ..
```

以上是将原文翻译成中文的结果。
kworker/u128:3-9093    [046] ..... 24625.365525: mlx5_sf_vhca_event: (0000:06:00.0) hw_id=0x8000 sfnum=88 vhca_state=1

- mlx5_sf_dev_add: 追踪 SF 设备添加事件::

    $ echo mlx5:mlx5_sf_dev_add>> /sys/kernel/tracing/set_event
    $ cat /sys/kernel/tracing/trace
    ..
kworker/u128:3-9093    [000] ..... 24616.524495: mlx5_sf_dev_add: (0000:06:00.0) sfdev=00000000fc5d96fd aux_id=4 hw_id=0x8000 sfnum=88

- mlx5_sf_dev_del: 追踪 SF 设备删除事件::

    $ echo mlx5:mlx5_sf_dev_del >> /sys/kernel/tracing/set_event
    $ cat /sys/kernel/tracing/trace
    ..
kworker/u128:3-9093    [044] ..... 24624.400749: mlx5_sf_dev_del: (0000:06:00.0) sfdev=00000000fc5d96fd aux_id=4 hw_id=0x8000 sfnum=88
