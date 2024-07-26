SPDX 许可证标识符: GPL-2.0+ 

================================================================================
idpf Linux* 基本驱动程序用于 Intel® 基础设施数据路径功能
================================================================================

Intel idpf Linux 驱动程序
版权所有 (C) 2023 Intel Corporation
.. contents::

idpf 驱动程序同时作为 Intel® 基础设施数据路径功能的物理功能 (PF) 和虚拟功能 (VF) 驱动程序。
可以通过 ethtool、lspci 和 ip 获取驱动程序信息。
有关硬件要求的问题，请参阅随附的 Intel 适配器文档。所有列出的硬件要求均适用于 Linux 的使用。

识别您的适配器
==================
有关如何识别您的适配器的信息以及最新的 Intel 网络驱动程序，请参阅 Intel 支持网站：
http://www.intel.com/support

附加特性和配置
==================

ethtool
-------
该驱动程序利用 ethtool 接口进行驱动程序配置和诊断，以及显示统计信息。为此功能需要最新版本的 ethtool。如果您还没有安装它，可以从以下位置获取：
https://kernel.org/pub/software/network/ethtool/

查看链路消息
---------------------
如果发行版限制了系统消息，则不会在控制台显示链路消息。为了在您的控制台上看到网络驱动程序的链路消息，请设置 dmesg 为 8，方法如下：

```
# dmesg -n 8
```

.. note::
   此设置不会在重启后保存。

巨型帧
------------
通过将最大传输单元 (MTU) 设置为大于默认值 1500 的值来启用巨型帧支持。
使用 ip 命令增加 MTU 大小。例如，输入以下命令，其中 `<ethX>` 是接口编号：

```
# ip link set mtu 9000 dev <ethX>
# ip link set up dev <ethX>
```

.. note::
   巨型帧的最大 MTU 设置为 9706。这对应于最大巨型帧大小 9728 字节。

.. note::
   该驱动程序将尝试使用多个页面大小的缓冲区接收每个巨型数据包。这应该有助于避免在分配接收数据包时出现缓冲区饥饿问题。

.. note::
   使用巨型帧时，丢包可能会对吞吐量产生更大的影响。如果您发现在启用巨型帧后性能下降，启用流控可能有助于缓解问题。
性能优化
========================
驱动程序默认设置旨在适应各种工作负载，但如果需要进一步的优化，我们建议尝试以下设置：

中断速率限制
-----------------------
此驱动程序支持一种针对一般工作负载调优的自适应中断阈值率（ITR）机制。用户可以通过 ethtool 调整两次中断之间的微秒数来为特定工作负载定制中断速率控制。

要手动设置中断速率，必须禁用自适应模式：

```bash
# ethtool -C <ethX> adaptive-rx off adaptive-tx off
```

为了降低CPU利用率：
- 禁用自适应 ITR 并降低接收 (Rx) 和发送 (Tx) 中断。下面的例子影响指定接口的所有队列。
- 将 `rx-usecs` 和 `tx-usecs` 设置为 80 将把每个队列的中断限制在大约每秒 12,500 次：

```bash
# ethtool -C <ethX> adaptive-rx off adaptive-tx off rx-usecs 80 tx-usecs 80
```

为了减少延迟：
- 禁用自适应 ITR，并通过将 `rx-usecs` 和 `tx-usecs` 设置为 0 来取消 ITR 的使用：

```bash
# ethtool -C <ethX> adaptive-rx off adaptive-tx off rx-usecs 0 tx-usecs 0
```

按队列的中断速率设置：
- 下面的例子是针对队列 1 和 3，但您可以调整其他队列。
- 要禁用接收 (Rx) 自适应 ITR 并为队列 1 和 3 设置静态接收 (Rx) ITR 为 10 微秒（或约每秒 100,000 次中断）：

```bash
# ethtool --per-queue <ethX> queue_mask 0xa --coalesce adaptive-rx off rx-usecs 10
```

- 查看队列 1 和 3 当前的合并设置：

```bash
# ethtool --per-queue <ethX> queue_mask 0xa --show-coalesce
```

虚拟化环境
-----------------------
除了本节中的其他建议外，以下内容可能有助于优化虚拟机中的性能：
- 使用适当的机制（例如 vcpupin）在虚拟机中将 CPU 绑定到单个本地 CPU，并确保使用设备的 `local_cpulist` 中包含的一组 CPU：`/sys/class/net/<ethX>/device/local_cpulist`
- 在虚拟机中配置尽可能多的接收 (Rx) 和发送 (Tx) 队列。（参见 idpf 驱动程序文档以了解受支持的队列数量。）例如：

```bash
# ethtool -L <virt_interface> rx <max> tx <max>
```

支持
=======
有关一般信息，请访问 Intel 支持网站：
http://www.intel.com/support/

如果在受支持内核上发现已发布源代码与受支持适配器之间存在问题，请将与问题相关的信息发送至 intel-wired-lan@lists.osuosl.org

商标
==========
Intel 是 Intel Corporation 或其子公司在美国和/或其他国家/地区的商标或注册商标。
* 其他名称和品牌可能是他人财产。
