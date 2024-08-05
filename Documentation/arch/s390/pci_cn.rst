SPDX 许可证标识符: GPL-2.0

======
S/390 PCI
======

作者:
        - Pierre Morel

版权所有，IBM 公司 2020


命令行参数和 debugfs 条目
===========================================

命令行参数
-----------------------

* nomio

  不使用 PCI 映射 I/O (MIO) 指令
* norid

  忽略 RID 字段并强制每个 PCI 功能使用一个 PCI 域
debugfs 条目
---------------

S/390 调试功能 (s390dbf) 生成视图以在形如以下的 sysfs 目录中保存各种调试结果：

 * /sys/kernel/debug/s390dbf/pci_*/

例如：

  - /sys/kernel/debug/s390dbf/pci_msg/sprintf
    保存来自处理 PCI 事件（如机器检查处理）的消息以及设置全局功能（如 UID 检查）
要更改日志记录的详细程度，可以通过管道将 0 到 6 之间的数字写入 /sys/kernel/debug/s390dbf/pci_*/level。详情请参阅
S/390 调试功能文档：
Documentation/arch/s390/s390dbf.rst
Sysfs 条目
=============

特定于 zPCI 功能以及包含 zPCI 信息的条目
* /sys/bus/pci/slots/XXXXXXXX

  这些插槽条目使用 PCI 功能的函数标识符 (FID) 设置。上文所示的格式 XXXXXXXX 是 8 位十六进制数字，用 0 补齐，并使用小写十六进制数字。
- /sys/bus/pci/slots/XXXXXXXX/power

  当前支持虚拟功能的物理功能不能关闭电源，直到所有虚拟功能通过以下方式移除：
  echo 0 > /sys/bus/pci/devices/XXXX:XX:XX.X/sriov_numvf

* /sys/bus/pci/devices/XXXX:XX:XX.X/

  - function_id
    一个 zPCI 函数标识符，在 Z 服务器中唯一地标识该功能
- function_handle
    配置的 PCI 功能使用的低级标识符
这对于调试可能有用
- pchid
    与模型相关的 I/O 适配器位置
- pfgid
    PCI功能组ID，具有相同功能的函数使用相同的标识符
    一个PCI组定义了中断、IOMMU（输入输出内存管理单元）、IOTLB（输入输出转换后备缓冲）和DMA（直接内存访问）的具体配置
- vfn
    虚拟函数编号，对于虚拟函数从1到N，对于物理函数为0
- pft
    PCI函数类型
- 端口
    端口对应于函数所连接的物理端口
    同时也表明了虚拟函数所连接的物理函数
- uid
    用户标识符（UID）可以作为机器配置或z/VM或KVM客户机配置的一部分定义。如果伴随的uid_is_unique属性为1，则平台保证在该实例中UID是唯一的，并且在系统生命周期内不会有相同UID的设备被连接
- uid_is_unique
    表示用户标识符（UID）是否被保证在这个Linux实例中唯一并且保持不变
- pfip/segmentX
    段决定了函数的隔离程度
    它们与函数的物理路径相对应
    不同段之间的差异越大，函数间的隔离程度就越高
枚举与热插拔
=======================

PCI 地址由四部分组成：域、总线、设备和功能，其形式为：DDDD:BB:dd.f

* 当不使用多功能（设置了 norid 或固件不支持多功能）：

  - 每个域只有一个功能
- 域是从 zPCI 功能的 UID 设置的，该 UID 在创建 LPAR 时定义
* 当使用多功能（未设置 norid 参数）时，
  zPCI 功能有不同的地址方式：

  - 每个域仍然只有一条总线
- 每条总线上最多可以有 256 个功能
- 对于多功能设备的所有功能的地址中的域部分
    是从功能零（即 devfn 为 0 的功能）的 zPCI 功能的 UID 设置的，在创建 LPAR 时为功能零定义
- 新的功能只有在功能零（devfn 为 0 的功能）被枚举后才能使用
