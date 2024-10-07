SPDX 许可证标识符: GPL-2.0

==============================
跟踪缓冲区扩展 (TRBE)
==============================

    :作者:   Anshuman Khandual <anshuman.khandual@arm.com>
    :日期:     2020年11月

硬件描述
--------------------

跟踪缓冲区扩展 (TRBE) 是一种每CPU的硬件，它在系统内存中捕获由对应的每CPU追踪单元生成的CPU追踪数据。这作为核心视图接收设备插入，因为相应的追踪生成器（ETE）作为源设备插入。
TRBE 不符合 CoreSight 架构规范，但通过 CoreSight 驱动框架进行驱动，以支持 ETE（符合 CoreSight 规范）的集成。

Sysfs 文件和目录
---------------------------

TRBE 设备会出现在现有的 coresight 总线上的其他 coresight 设备旁边，如下所示：

	>$ ls /sys/bus/coresight/devices
	trbe0  trbe1  trbe2 trbe3

名为 ``trbe<N>`` 的 TRBE 与一个 CPU 相关联：

	>$ ls /sys/bus/coresight/devices/trbe0/
        align flag

*关键文件项包括：*
   * ``align``: TRBE 写指针对齐
   * ``flag``: TRBE 使用访问和脏标志更新内存
