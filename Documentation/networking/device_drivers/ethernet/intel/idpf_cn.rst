SPDX 许可声明标识符: GPL-2.0+

==========================================================================
idpf Linux* 基础驱动程序用于 Intel(R) 基础设施数据路径功能
==========================================================================

Intel idpf Linux 驱动程序
版权所有 (C) 2023 Intel Corporation
.. contents::

idpf 驱动程序同时作为 Intel(R) 基础设施数据路径功能的物理功能 (PF) 和虚拟功能 (VF) 驱动程序。
可以通过 ethtool、lspci 和 ip 获取驱动程序信息。
有关硬件要求的问题，请参阅随附的 Intel 适配器文档。所有列出的硬件要求适用于 Linux 系统。

识别您的适配器
========================
要了解如何识别您的适配器以及获取最新的 Intel 网络驱动程序，请访问 Intel 支持网站：
http://www.intel.com/support

附加功能和配置
======================

ethtool
-------
该驱动程序使用 ethtool 接口进行驱动程序配置和诊断，并显示统计信息。此功能需要最新版本的 ethtool。如果您还没有安装，可以从以下网址获取：
https://kernel.org/pub/software/network/ethtool/

查看链路消息
---------------------
如果发行版限制了系统消息，则不会在控制台上显示链路消息。为了在控制台上看到网络驱动程序的链路消息，请将 dmesg 设置为 8，方法如下：

  # dmesg -n 8

.. note::
   此设置不会跨重启保存。

巨型帧
------------
通过将最大传输单元（MTU）设置为大于默认值 1500 的值来启用巨型帧支持。
使用 ip 命令增加 MTU 大小。例如，输入以下命令，其中 `<ethX>` 是接口编号：

  # ip link set mtu 9000 dev <ethX>
  # ip link set up dev <ethX>

.. note::
   巨型帧的最大 MTU 设置为 9706。这对应于 9728 字节的最大巨型帧大小。

.. note::
   该驱动程序将尝试使用多个页面大小的缓冲区来接收每个巨型帧。这应该有助于避免分配接收数据包时的缓冲区饥饿问题。

.. note::
   启用巨型帧后，丢包可能对吞吐量产生更大的影响。如果您发现启用巨型帧后性能下降，启用流量控制可能会缓解问题。
性能优化
========================
驱动程序默认设置旨在适应各种工作负载，但如果需要进一步优化，我们建议尝试以下设置：

中断速率限制
-----------------------
此驱动程序支持一种自适应中断节流率（ITR）机制，该机制针对一般工作负载进行了调优。用户可以通过 `ethtool` 调整中断之间的微秒数来为特定工作负载定制中断速率控制。

要手动设置中断速率，必须禁用自适应模式：

```shell
# ethtool -C <ethX> adaptive-rx off adaptive-tx off
```

对于较低的CPU利用率：
- 禁用自适应ITR并降低Rx和Tx中断。下面的例子会影响指定接口的所有队列。
- 将 `rx-usecs` 和 `tx-usecs` 设置为80会将每个队列的中断限制为大约每秒12,500次：

```shell
# ethtool -C <ethX> adaptive-rx off adaptive-tx off rx-usecs 80 tx-usecs 80
```

对于减少延迟：
- 禁用自适应ITR并通过将 `rx-usecs` 和 `tx-usecs` 设置为0来禁用ITR：

```shell
# ethtool -C <ethX> adaptive-rx off adaptive-tx off rx-usecs 0 tx-usecs 0
```

按队列设置中断速率：
- 下面的例子是针对队列1和3的，但您可以调整其他队列。
- 要禁用队列1和3的Rx自适应ITR并将静态Rx ITR设置为10微秒（或约每秒100,000次中断），请执行以下命令：

```shell
# ethtool --per-queue <ethX> queue_mask 0xa --coalesce adaptive-rx off rx-usecs 10
```

- 要显示队列1和3当前的合并设置，请执行以下命令：

```shell
# ethtool --per-queue <ethX> queue_mask 0xa --show-coalesce
```

虚拟化环境
-----------------------
除了本节中的其他建议外，以下措施可能有助于在虚拟机中优化性能：
- 使用适当的机制（如 vcpupin）将CPU固定到单个 LCPUs，并确保使用设备的本地CPU列表中的CPU集：`/sys/class/net/<ethX>/device/local_cpulist`
- 在虚拟机中配置尽可能多的Rx/Tx队列。（参见 idpf 驱动程序文档以了解支持的队列数量。）例如：

```shell
# ethtool -L <virt_interface> rx <max> tx <max>
```

支持
======
有关一般信息，请访问 Intel 支持网站：
http://www.intel.com/support/

如果在支持内核上发布的源代码中发现与支持适配器相关的问题，请将具体问题相关信息发送至 intel-wired-lan@lists.osuosl.org

商标
==========
Intel 是 Intel Corporation 或其子公司在美国和其他国家的商标或注册商标。
* 其他名称和品牌可能属于他人所有。
