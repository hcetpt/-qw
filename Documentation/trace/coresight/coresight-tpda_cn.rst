SPDX 许可证标识符: GPL-2.0

=================================================================
追踪性能监控与诊断聚合器（TPDA）
=================================================================

    :作者:   毛金龙 <quic_jinlmao@quicinc.com>
    :日期:   2023年1月

硬件描述
--------------------

TPDA（追踪性能监控与诊断聚合器）或简称TPDA，作为性能监控和诊断网络规范的仲裁和包封装引擎。TPDA 的主要用途是提供监控数据的包封装、汇聚和时间戳。

sysfs 文件和目录
---------------------------
根目录: ``/sys/bus/coresight/devices/tpda<N>``

配置详情
---------------------------

tpdm 和 tpda 节点应在 coresight 路径下观察:
"/sys/bus/coresight/devices"

例如:
```
/sys/bus/coresight/devices # ls -l | grep tpd
tpda0 -> ../../../devices/platform/soc@0/6004000.tpda/tpda0
tpdm0 -> ../../../devices/platform/soc@0/6c08000.mm.tpdm/tpdm0
```

我们可以使用类似于以下命令来验证 TPDMs：
首先启用 coresight 输出端。执行以下命令后，连接到 tpdm 的 tpda 端口将被启用。
```
echo 1 > /sys/bus/coresight/devices/tmc_etf0/enable_sink
echo 1 > /sys/bus/coresight/devices/tpdm0/enable_source
echo 1 > /sys/bus/coresight/devices/tpdm0/integration_test
echo 2 > /sys/bus/coresight/devices/tpdm0/integration_test
```

测试数据将在已启用的 coresight 输出端中收集。如果在执行集成测试时（通过 `cat tmc_etf0/mgmt/rwp`），输出端的 rwp 寄存器不断更新，则表示有数据从 TPDM 生成并传输到输出端。
在 tpdm 和输出端之间必须有一个 tpda。当在同一硬件模块中有其他追踪事件硬件组件时，这些组件和 tpdm 将连接到 coresight 汇聚器。当硬件模块中只有 tpdm 追踪硬件时，tpdm 将直接连接到 tpda。
