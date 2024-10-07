SPDX 许可证标识符: GPL-2.0

========================
tcm_qla2xxx 驱动程序说明
========================

tcm_qla2xxx 的 jam_host 属性
------------------------------
现在有一个新的模块端点属性叫做 jam_host 属性：

    jam_host: 布尔值=0/1

此属性及其相关代码仅在 Kconfig 参数 TCM_QLA2XXX_DEBUG 被设置为 Y 时才包含。

默认情况下，此阻塞器代码和功能是禁用的。

使用此属性来控制对选定主机的 SCSI 命令的丢弃。
这可能有助于测试错误处理以及模拟缓慢耗尽和其他结构问题。
将特定主机的 jam_host 属性布尔值设置为 1 将会丢弃该主机的命令。
将其重置为 0 来停止阻塞。
启用主机 4 的阻塞：

  echo 1 > /sys/kernel/config/target/qla2xxx/21:00:00:24:ff:27:8f:ae/tpgt_1/attrib/jam_host

禁用主机 4 上的阻塞：

  echo 0 > /sys/kernel/config/target/qla2xxx/21:00:00:24:ff:27:8f:ae/tpgt_1/attrib/jam_host
