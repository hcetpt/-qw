SPDX许可证标识符: （GPL-2.0-only 或 BSD-2-Clause）
.. include:: <isonum.txt>

===========================================
网络流处理器（NFP）内核驱动程序
===========================================

:版权所有: |copy| 2019, Netronome Systems, Inc
:版权所有: |copy| 2022, Corigine, Inc
内容
========

- `概述`_
- `获取固件`_
- `Devlink 信息`_
- `配置设备`_
- `统计信息`_

概述
========

该驱动程序支持Netronome和Corigine的网络流处理器（NFP）系列设备，包括NFP3800、NFP4000、NFP5000和NFP6000型号，这些型号也集成在公司的Agilio智能网卡系列中。该驱动程序支持这些设备的SR-IOV物理功能和虚拟功能。

获取固件
==================

NFP3800、NFP4000和NFP6000设备需要特定于应用的固件才能运行。应用程序固件可以位于主机文件系统上或设备闪存中（如果由管理固件支持）。主机文件系统中的固件文件包含卡类型（`AMDA-*`字符串）、媒体配置等信息。它们应放置在`/lib/firmware/netronome`目录中以便从主机文件系统加载固件。
基本NIC操作所需的固件可以在上游`linux-firmware.git`仓库中找到。
更全面的固件列表可以从`Corigine支持网站 <https://www.corigine.com/DPUDownload.html>`_下载。

NVRAM中的固件
-----------------

最近版本的管理固件支持在主机驱动程序被探测时从闪存加载应用程序固件。可以通过配置固件加载策略来适当地配置此功能。
使用devlink或ethtool可以通过向相应的命令提供适当的`nic_AMDA*.nffw`文件来更新设备闪存中的应用程序固件。用户需要注意将正确的固件映像写入到闪存中以匹配卡和媒体配置。
闪存中的可用存储空间取决于所使用的卡。
处理多个项目
------------------------------

NFP硬件是完全可编程的，因此可以有不同的固件映像针对不同的应用。
当从主机使用应用程序固件时，我们建议将实际的固件文件放置在`/lib/firmware/netronome`目录下的以应用程序命名的子目录中，并链接所需的文件，例如：

    $ tree /lib/firmware/netronome/
    /lib/firmware/netronome/
    ├── bpf
    │   ├── nic_AMDA0081-0001_1x40.nffw
    │   └── nic_AMDA0081-0001_4x10.nffw
    ├── flower
    │   ├── nic_AMDA0081-0001_1x40.nffw
    │   └── nic_AMDA0081-0001_4x10.nffw
    ├── nic
    │   ├── nic_AMDA0081-0001_1x40.nffw
    │   └── nic_AMDA0081-0001_4x10.nffw
    ├── nic_AMDA0081-0001_1x40.nffw -> bpf/nic_AMDA0081-0001_1x40.nffw
    └── nic_AMDA0081-0001_4x10.nffw -> bpf/nic_AMDA0081-0001_4x10.nffw

    3 个目录，8 个文件

您可能需要在使用旧`mkinitrd`命令而不是`dracut`（例如Ubuntu）的发行版上使用硬链接而不是符号链接。更改固件文件后，您可能需要重新生成初始RAM磁盘（initramfs）图像。初始RAM磁盘包含系统启动时可能需要的驱动程序和固件文件。过时的初始RAM磁盘的一个明显迹象是在启动时加载了错误的驱动程序或固件，但手动重新加载驱动程序后一切正常。请参考您的发行版文档以了解如何更新初始RAM磁盘。

按设备选择固件
-----------------------------

通常情况下，系统中的所有卡都使用相同类型的固件。
如果您希望为特定的卡加载特定的固件映像，您可以使用PCI总线地址或序列号。驱动程序在识别到NFP设备时会打印它正在查找哪些文件：

    nfp: 按优先级顺序查找固件文件：
    nfp:  netronome/serial-00-12-34-aa-bb-cc-10-ff.nffw: 未找到
    nfp:  netronome/pci-0000:02:00.0.nffw: 未找到
    nfp:  netronome/nic_AMDA0081-0001_1x40.nffw: 找到，正在加载..

在这种情况下，如果`/lib/firmware/netronome`中存在名为`serial-00-12-34-aa-bb-5d-10-ff.nffw`或`pci-0000:02:00.0.nffw`的文件（或链接），则这些固件文件将优先于`nic_AMDA*`文件。
请注意，`serial-*`和`pci-*`文件不会自动包含在初始RAM磁盘中，您需要查阅相应工具的文档以了解如何将其包含进去。

运行中的固件版本
------------------------

可以通过ethtool命令显示特定<netdev>接口（例如enp4s0）或接口端口<netdev port>（例如enp4s0np0）所加载的固件版本：

  $ ethtool -i <netdev>

固件加载策略
-----------------------

固件加载策略通过存储在设备闪存中的三个HWinfo参数进行控制：

app_fw_from_flash
    定义哪个固件应该具有优先权，'Disk'（0）、'Flash'（1）或'Preferred'（2）。当选择'Preferred'时，管理固件将通过比较闪存固件版本和主机提供的固件版本来决定加载哪个固件。
此变量可以通过'devlink'参数'fw_load_policy'进行配置。
abi_drv_reset
    定义驱动程序在探测时是否应重置固件，如果固件是在磁盘上找到的，则为'Disk'（0），总是重置为'Always'（1），从不重置为'Never'（2）。请注意，如果在驱动程序探测时加载了固件，则在卸载驱动程序时设备总是会被重置。
此变量可以通过 `reset_dev_on_drv_probe` devlink 参数进行配置。
`abi_drv_load_ifc`
定义了允许加载设备固件的PF设备列表。
此变量目前不支持用户配置。

Devlink 信息
============
`devlink info` 命令显示设备上运行和存储的固件版本、序列号和板卡信息。
Devlink info 命令示例（替换PCI地址）：

```
$ devlink dev info pci/0000:03:00.0
pci/0000:03:00.0:
  driver nfp
  serial_number CSAAMDA2001-1003000111
  versions:
      fixed:
        board.id AMDA2001-1003
        board.rev 01
        board.manufacture CSA
        board.model mozart
      running:
        fw.mgmt 22.10.0-rc3
        fw.cpld 0x1000003
        fw.app nic-22.09.0
        chip.init AMDA-2001-1003  1003000111
      stored:
        fw.bundle_id bspbundle_1003000111
        fw.mgmt 22.10.0-rc3
        fw.cpld 0x0
        chip.init AMDA-2001-1003  1003000111
```

配置设备
=========

本节解释如何使用运行基本NIC固件的Agilio SmartNICs。
配置接口链路速度
-----------------
以下步骤说明了如何在Agilio CX 2x25GbE卡上切换10G模式和25G模式。更改端口速度必须按顺序进行，端口0（p0）必须先设置为10G，然后才能将端口1（p1）设置为10G。
关闭相应的接口：

```
$ ip link set dev <netdev port 0> down
$ ip link set dev <netdev port 1> down
```

将接口链路速度设置为10G：

```
$ ethtool -s <netdev port 0> speed 10000
$ ethtool -s <netdev port 1> speed 10000
```

将接口链路速度设置为25G：

```
$ ethtool -s <netdev port 0> speed 25000
$ ethtool -s <netdev port 1> speed 25000
```

重新加载驱动程序以使更改生效：

```
$ rmmod nfp; modprobe nfp
```

配置接口最大传输单元（MTU）
-----------------------------
可以使用iproute2、ip link或ifconfig工具临时设置接口的MTU。请注意，这种更改不会持久化。建议通过Network Manager或其他适当的OS配置工具来设置MTU，因为使用Network Manager设置的MTU更改可以持久化。
将接口MTU设置为9000字节：

```
$ ip link set dev <netdev port> mtu 9000
```

处理巨型帧或使用隧道时，用户或编排层需要负责设置适当的MTU值。例如，如果从VM发送的报文要在卡上封装并通过物理端口出站，则VF的MTU应设置得低于物理端口的MTU，以考虑额外报头添加的字节数。如果预期会有SmartNIC与内核之间的回退流量，则用户还应确保PF MTU设置适当，以避免在此路径上的意外丢包。

配置前向纠错（FEC）模式
-------------------------
Agilio SmartNICs支持FEC模式配置，例如Auto、Firecode Base-R、ReedSolomon和Off模式。每个物理端口的FEC模式可以独立使用ethtool设置。可以通过以下命令查看接口支持的FEC模式：

```
$ ethtool <netdev>
```

当前配置的FEC模式可以通过以下命令查看：

```
$ ethtool --show-fec <netdev>
```

要强制特定端口的FEC模式，必须禁用自动协商（参见“自动协商”部分）。将FEC模式设置为Reed-Solomon的一个示例如下：

```
$ ethtool --set-fec <netdev> encoding rs
```

自动协商
----------
要更改自动协商设置，首先必须关闭链路。链路关闭后，可以使用以下命令启用或禁用自动协商：

```
ethtool -s <netdev> autoneg <on|off>
```

统计信息
=========
以下设备统计信息可通过 `ethtool -S` 接口获取：

.. flat-table:: NFP 设备统计信息
   :header-rows: 1
   :widths: 3 1 11

   * - 名称
     - ID
     - 含义

   * - dev_rx_discards
     - 1
     - 报文可能因以下原因之一在接收路径中被丢弃：

        * 网卡未处于混杂模式，并且目标MAC地址与接口的MAC地址不匹配
        * 接收到的报文大于主机上的最大缓冲区大小
即，它超过了第3层的最大接收单元（MRU）。

* 在主机上没有可用的空闲列表描述符来处理该数据包。
很可能网卡未能及时缓存一个描述符。
* 一个BPF程序丢弃了该数据包。
* 执行了数据路径丢弃操作。
* 由于网卡上缺乏入站缓冲区空间，MAC层丢弃了该数据包。
* `- dev_rx_errors`
    - 2
    - 数据包可能因以下原因被计为接收错误（并被丢弃）：

      * VEB查找问题（仅在使用SR-IOV时）
* 物理层问题导致以太网错误，如FCS或对齐错误。通常原因是故障的电缆或SFP模块。
* `- dev_rx_bytes`
    - 3
    - 接收到的总字节数。
* `- dev_rx_uc_bytes`
    - 4
    - 接收到的单播字节数。
* - dev_rx_mc_bytes
     - 5
     - 接收的组播字节数
* - dev_rx_bc_bytes
     - 6
     - 接收的广播字节数
* - dev_rx_pkts
     - 7
     - 接收的数据包总数
* - dev_rx_mc_pkts
     - 8
     - 接收的组播数据包数
* - dev_rx_bc_pkts
     - 9
     - 接收的广播数据包数
* - dev_tx_discards
     - 10
     - 如果MAC正在进行流控制并且NIC的TX队列空间耗尽，可以在TX方向丢弃一个数据包
* - dev_tx_errors
     - 11
     - 数据包可能因以下原因之一被计为TX错误（并被丢弃）：

       * 该数据包是LSO分段，但无法确定第3层或第4层的偏移量。因此LSO无法继续
       * 通过PCIe接收到无效的数据包描述符
       * 第3层长度超过设备MTU的数据包
       * MAC/物理层上的错误。通常由于故障的电缆或SFP模块引起
* 无法分配CTM缓冲区
* 数据包偏移不正确，且无法通过NIC修复
* - dev_tx_bytes
     - 12
     - 发送的总字节数
* - dev_tx_uc_bytes
     - 13
     - 发送的单播字节数
* - dev_tx_mc_bytes
     - 14
     - 发送的组播字节数
* - dev_tx_bc_bytes
     - 15
     - 发送的广播字节数
* - dev_tx_pkts
     - 16
     - 发送的总数据包数
* - dev_tx_mc_pkts
     - 17
     - 发送的组播数据包数
* - dev_tx_bc_pkts
     - 18
     - 发送的广播数据包数

注意：驱动程序中未知的统计信息将显示为``dev_unknown_stat$ID``，其中``$ID``指的是上面第二列的内容。
当然，请提供您需要翻译的文本。
