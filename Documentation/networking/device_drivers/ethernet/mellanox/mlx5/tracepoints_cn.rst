### SPDX 许可证标识符: GPL-2.0 或 Linux-OpenIB
### 包含: <isonum.txt>

=================
跟踪点
=================

版权所有 © 2023，NVIDIA CORPORATION 及其附属公司。保留所有权利。

mlx5 驱动程序提供了内部跟踪点，用于使用内核跟踪点接口进行追踪和调试（参考 `Documentation/trace/ftrace.rst`）。
要查看支持的 mlx5 事件列表，请检查 `/sys/kernel/tracing/events/mlx5/`。
TC 和交换机卸载跟踪点如下：

- **mlx5e_configure_flower**: 跟踪被卸载到 mlx5 的花卉过滤器的动作和 Cookie。

  ```
  $ echo mlx5:mlx5e_configure_flower >> /sys/kernel/tracing/set_event
  $ cat /sys/kernel/tracing/trace
  ...
  tc-6535  [019] ...1  2672.404466: mlx5e_configure_flower: cookie=0000000067874a55 actions= REDIRECT
  ```

- **mlx5e_delete_flower**: 跟踪从 mlx5 删除的花卉过滤器的动作和 Cookie。

  ```
  $ echo mlx5:mlx5e_delete_flower >> /sys/kernel/tracing/set_event
  $ cat /sys/kernel/tracing/trace
  ...
  tc-6569  [010] .N.1  2686.379075: mlx5e_delete_flower: cookie=0000000067874a55 actions= NULL
  ```

- **mlx5e_stats_flower**: 跟踪花卉统计请求。

  ```
  $ echo mlx5:mlx5e_stats_flower >> /sys/kernel/tracing/set_event
  $ cat /sys/kernel/tracing/trace
  ...
  tc-6546  [010] ...1  2679.704889: mlx5e_stats_flower: cookie=0000000060eb3d6a bytes=0 packets=0 lastused=4295560217
  ```

- **mlx5e_tc_update_neigh_used_value**: 跟踪被卸载到 mlx5 的隧道规则邻接更新值。

  ```
  $ echo mlx5:mlx5e_tc_update_neigh_used_value >> /sys/kernel/tracing/set_event
  $ cat /sys/kernel/tracing/trace
  ...
  kworker/u48:4-8806  [009] ...1 55117.882428: mlx5e_tc_update_neigh_used_value: netdev: ens1f0 IPv4: 1.1.1.10 IPv6: ::ffff:1.1.1.10 neigh_used=1
  ```

- **mlx5e_rep_neigh_update**: 跟踪因邻接状态改变事件而调度的邻接更新任务。

  ```
  $ echo mlx5:mlx5e_rep_neigh_update >> /sys/kernel/tracing/set_event
  $ cat /sys/kernel/tracing/trace
  ...
  kworker/u48:7-2221  [009] ...1  1475.387435: mlx5e_rep_neigh_update: netdev: ens1f0 MAC: 24:8a:07:9a:17:9a IPv4: 1.1.1.10 IPv6: ::ffff:1.1.1.10 neigh_connected=1
  ```

桥接卸载跟踪点：

- **mlx5_esw_bridge_fdb_entry_init**: 跟踪被卸载到 mlx5 的桥接 FDB 条目。

  ```
  $ echo mlx5:mlx5_esw_bridge_fdb_entry_init >> /sys/kernel/tracing/set_event
  $ cat /sys/kernel/tracing/trace
  ...
  kworker/u20:9-2217    [003] ...1   318.582243: mlx5_esw_bridge_fdb_entry_init: net_device=enp8s0f0_0 addr=e4:fd:05:08:00:02 vid=0 flags=0 used=0
  ```

- **mlx5_esw_bridge_fdb_entry_cleanup**: 跟踪从 mlx5 删除的桥接 FDB 条目。

  ```
  $ echo mlx5:mlx5_esw_bridge_fdb_entry_cleanup >> /sys/kernel/tracing/set_event
  $ cat /sys/kernel/tracing/trace
  ...
  ```
这些是Linux内核追踪点（tracepoints）的输出示例，主要用于监控和调试与Mellanox ConnectX网络适配器相关的事件。下面是翻译后的解释：

- `mlx5_esw_bridge_fdb_entry_cleanup`: 清理桥接FDB条目
  - 在`mlx5`中：
    - `echo mlx5:mlx5_esw_bridge_fdb_entry_cleanup >> set_event`
    - 查看`/sys/kernel/tracing/trace`文件内容：
      - `ip-2581 [005] ...1 318.629871: mlx5_esw_bridge_fdb_entry_cleanup: net_device=enp8s0f0_1 addr=e4:fd:05:08:00:03 vid=0 flags=0 used=16`
        - 网络设备：`enp8s0f0_1`
        - MAC地址：`e4:fd:05:08:00:03`
        - VLAN ID：`0`
        - 标志：`0`
        - 使用次数：`16`

- `mlx5_esw_bridge_fdb_entry_refresh`: 桥接FDB条目的卸载刷新
  - 在`mlx5`中：
    - `echo mlx5:mlx5_esw_bridge_fdb_entry_refresh >> set_event`
    - 查看`/sys/kernel/tracing/trace`文件内容：
      - `kworker/u20:8-3849 [003] ...1 466716: mlx5_esw_bridge_fdb_entry_refresh: net_device=enp8s0f0_0 addr=e4:fd:05:08:00:02 vid=3 flags=0 used=0`

- `mlx5_esw_bridge_vlan_create`: 在`mlx5`代表器上创建桥接VLAN对象
  - 在`mlx5`中：
    - `echo mlx5:mlx5_esw_bridge_vlan_create >> set_event`
    - 查看`/sys/kernel/tracing/trace`文件内容：
      - `ip-2560 [007] ...1 318.460258: mlx5_esw_bridge_vlan_create: vid=1 flags=6`

- `mlx5_esw_bridge_vlan_cleanup`: 从`mlx5`代表器删除桥接VLAN对象
  - 在`mlx5`中：
    - `echo mlx5:mlx5_esw_bridge_vlan_cleanup >> set_event`
    - 查看`/sys/kernel/tracing/trace`文件内容：
      - `bridge-2582 [007] ...1 318.653496: mlx5_esw_bridge_vlan_cleanup: vid=2 flags=8`

- `mlx5_esw_bridge_vport_init`: 在桥接上层设备中分配`mlx5`虚拟端口
  - 在`mlx5`中：
    - `echo mlx5:mlx5_esw_bridge_vport_init >> set_event`
    - 查看`/sys/kernel/tracing/trace`文件内容：
      - `ip-2560 [007] ...1 318.458915: mlx5_esw_bridge_vport_init: vport_num=1`

- `mlx5_esw_bridge_vport_cleanup`: 从桥接上层设备移除`mlx5`虚拟端口
  - 在`mlx5`中：
    - `echo mlx5:mlx5_esw_bridge_vport_cleanup >> set_event`
    - 查看`/sys/kernel/tracing/trace`文件内容：
      - `ip-5387 [000] ...1 573713: mlx5_esw_bridge_vport_cleanup: vport_num=1`

### Eswitch QoS 跟踪点

- `mlx5_esw_vport_qos_create`: 创建vport的发送调度程序仲裁器
  - `echo mlx5:mlx5_esw_vport_qos_create >> /sys/kernel/tracing/set_event`
  - 查看`/sys/kernel/tracing/trace`文件内容：
    - `<...>-23496 [018] .... 73136.838831: mlx5_esw_vport_qos_create: (0000:82:00.0) vport=2 tsar_ix=4 bw_share=0, max_rate=0 group=000000007b576bb3`

- `mlx5_esw_vport_qos_config`: 配置vport的发送调度程序仲裁器
  - `echo mlx5:mlx5_esw_vport_qos_config >> /sys/kernel/tracing/set_event`
  - 查看`/sys/kernel/tracing/trace`文件内容：
    - `<...>-26548 [023] .... 75754.223823: mlx5_esw_vport_qos_config: (0000:82:00.0) vport=1 tsar_ix=3 bw_share=34, max_rate=10000 group=000000007b576bb3`

- `mlx5_esw_vport_qos_destroy`: 删除vport的发送调度程序仲裁器
  - `echo mlx5:mlx5_esw_vport_qos_destroy >> /sys/kernel/tracing/set_event`
  - 查看`/sys/kernel/tracing/trace`文件内容：
    - `<...>-27418 [004] .... 76546.680901: mlx5_esw_vport_qos_destroy: (0000:82:00.0) vport=1 tsar_ix=3`

- `mlx5_esw_group_qos_create`: 创建速率组的发送调度程序仲裁器
  - `echo mlx5:mlx5_esw_group_qos_create >> /sys/kernel/tracing/set_event`
  - 查看`/sys/kernel/tracing/trace`文件内容：
    - `<...>-26578 [008] .... 75776.022112: mlx5_esw_group_qos_create: (0000:82:00.0) group=000000008dac63ea tsar_ix=5`

- `mlx5_esw_group_qos_config`: 配置速率组的发送调度程序仲裁器
  - `echo mlx5:mlx5_esw_group_qos_config >> /sys/kernel/tracing/set_event`
  - 查看`/sys/kernel/tracing/trace`文件内容：
    - `<...>-26578 [008] .... 75776.022112: mlx5_esw_group_qos_config: (0000:82:00.0) group=000000008dac63ea tsar_ix=5`
这些是内核追踪点（tracepoints）的示例，用于监控和调试 Mellanox 网络设备驱动程序中的特定事件。下面是翻译后的中文描述：

- `mlx5_esw_group_qos_config`: 跟踪组 QoS 配置的设置：

    ```
    $ echo mlx5:mlx5_esw_group_qos_config >> /sys/kernel/tracing/set_event
    $ cat /sys/kernel/tracing/trace
    ..
    <...>-27303   [020] .... 76461.455356: mlx5_esw_group_qos_config: (0000:82:00.0) group=000000008dac63ea tsar_ix=5 bw_share=100 max_rate=20000
    ```

- `mlx5_esw_group_qos_destroy`: 跟踪删除组的传输调度仲裁器：

    ```
    $ echo mlx5:mlx5_esw_group_qos_destroy >> /sys/kernel/tracing/set_event
    $ cat /sys/kernel/tracing/trace
    ..
    <...>-27418   [006] .... 76547.187258: mlx5_esw_group_qos_destroy: (0000:82:00.0) group=000000007b576bb3 tsar_ix=1
    ```

**SF tracepoints（单功能端口追踪点）:**

- `mlx5_sf_add`: 跟踪添加 SF 端口：

    ```
    $ echo mlx5:mlx5_sf_add >> /sys/kernel/tracing/set_event
    $ cat /sys/kernel/tracing/trace
    ..
    devlink-9363    [031] ..... 24610.188722: mlx5_sf_add: (0000:06:00.0) port_index=32768 controller=0 hw_id=0x8000 sfnum=88
    ```

- `mlx5_sf_free`: 跟踪释放 SF 端口：

    ```
    $ echo mlx5:mlx5_sf_free >> /sys/kernel/tracing/set_event
    $ cat /sys/kernel/tracing/trace
    ..
    devlink-9830    [038] ..... 26300.404749: mlx5_sf_free: (0000:06:00.0) port_index=32768 controller=0 hw_id=0x8000
    ```

- `mlx5_sf_activate`: 跟踪激活 SF 端口：

    ```
    $ echo mlx5:mlx5_sf_activate >> /sys/kernel/tracing/set_event
    $ cat /sys/kernel/tracing/trace
    ..
    devlink-29841   [008] .....  3669.635095: mlx5_sf_activate: (0000:08:00.0) port_index=32768 controller=0 hw_id=0x8000
    ```

- `mlx5_sf_deactivate`: 跟踪停用 SF 端口：

    ```
    $ echo mlx5:mlx5_sf_deactivate >> /sys/kernel/tracing/set_event
    $ cat /sys/kernel/tracing/trace
    ..
    devlink-29994   [008] .....  4015.969467: mlx5_sf_deactivate: (0000:08:00.0) port_index=32768 controller=0 hw_id=0x8000
    ```

- `mlx5_sf_hwc_alloc`: 跟踪分配硬件 SF 上下文：

    ```
    $ echo mlx5:mlx5_sf_hwc_alloc >> /sys/kernel/tracing/set_event
    $ cat /sys/kernel/tracing/trace
    ..
    devlink-9775    [031] ..... 26296.385259: mlx5_sf_hwc_alloc: (0000:06:00.0) controller=0 hw_id=0x8000 sfnum=88
    ```

- `mlx5_sf_hwc_free`: 跟踪释放硬件 SF 上下文：

    ```
    $ echo mlx5:mlx5_sf_hwc_free >> /sys/kernel/tracing/set_event
    $ cat /sys/kernel/tracing/trace
    ..
    kworker/u128:3-9093    [046] ..... 24625.365771: mlx5_sf_hwc_free: (0000:06:00.0) hw_id=0x8000
    ```

- `mlx5_sf_hwc_deferred_free`: 跟踪延迟释放硬件 SF 上下文：

    ```
    $ echo mlx5:mlx5_sf_hwc_deferred_free >> /sys/kernel/tracing/set_event
    $ cat /sys/kernel/tracing/trace
    ..
    devlink-9519    [046] ..... 24624.400271: mlx5_sf_hwc_deferred_free: (0000:06:00.0) hw_id=0x8000
    ```

- `mlx5_sf_update_state`: 跟踪 SF 上下文的状态更新：

    ```
    $ echo mlx5:mlx5_sf_update_state >> /sys/kernel/tracing/set_event
    $ cat /sys/kernel/tracing/trace
    ..
    kworker/u20:3-29490   [009] .....  4141.453530: mlx5_sf_update_state: (0000:08:00.0) port_index=32768 controller=0 hw_id=0x8000 state=2
    ```

- `mlx5_sf_vhca_event`: 跟踪 SF vhca 事件和状态：

    ```
    $ echo mlx5:mlx5_sf_vhca_event >> /sys/kernel/tracing/set_event
    $ cat /sys/kernel/tracing/trace
    ..
    ```
翻译如下：

`kworker/u128:3-9093    [046] ..... 24625.365525: mlx5_sf_vhca_event: (0000:06:00.0) hw_id=0x8000 sfnum=88 vhca_state=1`

- `mlx5_sf_dev_add`: 追踪SF设备添加事件:

    ```
    $ echo mlx5:mlx5_sf_dev_add>> /sys/kernel/tracing/set_event
    $ cat /sys/kernel/tracing/trace
    ..
    kworker/u128:3-9093    [000] ..... 24616.524495: mlx5_sf_dev_add: (0000:06:00.0) sfdev=00000000fc5d96fd aux_id=4 hw_id=0x8000 sfnum=88
    ```

- `mlx5_sf_dev_del`: 追踪SF设备删除事件:

    ```
    $ echo mlx5:mlx5_sf_dev_del >> /sys/kernel/tracing/set_event
    $ cat /sys/kernel/tracing/trace
    ..
    kworker/u128:3-9093    [044] ..... 24624.400749: mlx5_sf_dev_del: (0000:06:00.0) sfdev=00000000fc5d96fd aux_id=4 hw_id=0x8000 sfnum=88
    ```

解释：
- `mlx5_sf_vhca_event`: 显示了与硬件ID (`hw_id`) 为`0x8000`的设备相关的虚拟主机控制适配器 (`vhca`) 事件，该事件的`sfnum`（子功能编号）为88，且`vhca_state`为1。
  
- `mlx5_sf_dev_add`: 表示在设备`0000:06:00.0`上添加了一个SF设备，其设备指针为`00000000fc5d96fd`，辅助ID (`aux_id`) 为4，硬件ID (`hw_id`) 为`0x8000`，子功能编号 (`sfnum`) 为88。

- `mlx5_sf_dev_del`: 表示在设备`0000:06:00.0`上删除了一个SF设备，其设备指针为`00000000fc5d96fd`，辅助ID (`aux_id`) 为4，硬件ID (`hw_id`) 为`0x8000`，子功能编号 (`sfnum`) 为88。
