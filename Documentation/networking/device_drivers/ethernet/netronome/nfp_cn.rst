许可标识符：(仅 GPL-2.0 或 BSD-2-Clause)
.. include:: <isonum.txt>

===========================================
网络流处理器（NFP）内核驱动程序
===========================================

:版权所有: |copy| 2019, Netronome Systems, Inc
:版权所有: |copy| 2022, Corigine, Inc
目录
========

- `概述`_
- `获取固件`_
- `Devlink 信息`_
- `配置设备`_
- `统计信息`_

概述
========

此驱动程序支持 Netronome 和 Corigine 的一系列网络流处理器设备，包括 NFP3800、NFP4000、NFP5000 和 NFP6000 型号，这些型号也被集成在公司的 Agilio 智能网卡系列中。该驱动程序支持这些设备的 SR-IOV 物理和虚拟功能。

获取固件
==================

NFP3800、NFP4000 和 NFP6000 设备需要特定于应用的固件才能运行。应用程序固件可以位于主机文件系统上或设备闪存中（如果由管理固件支持）。主机文件系统中的固件文件包含卡类型（`AMDA-*` 字符串）、媒体配置等信息。它们应放置在 `/lib/firmware/netronome` 目录中以便从主机文件系统加载固件。
用于基本 NIC 运行的固件可以在上游 `linux-firmware.git` 仓库中找到。
更全面的固件列表可以从 `Corigine 支持网站 <https://www.corigine.com/DPUDownload.html>`_ 下载。
NVRAM 中的固件
-----------------

最近版本的管理固件支持在主机驱动被探测时从闪存加载应用程序固件。可以通过固件加载策略配置来适当配置此功能。
可以使用 Devlink 或 ethtool 通过向相应的命令提供适当的 `nic_AMDA*.nffw` 文件来更新设备闪存中的应用程序固件。用户需要注意将正确的固件映像写入到闪存中以匹配所用的卡和媒体配置。
闪存中可用的存储空间取决于所使用的卡。
处理多个项目
------------------------------

NFP 硬件是完全可编程的，因此可以有不同的固件映像针对不同的应用。
当从主机使用应用固件时，我们建议将实际的固件文件放置在 `/lib/firmware/netronome` 目录下的以应用命名的子目录中，并链接所需的文件，例如：

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

    3 个目录， 8 个文件

您可能需要在使用旧的 `mkinitrd` 命令（而非 `dracut`）的发行版上使用硬链接而不是符号链接（如 Ubuntu）。
更改固件文件后，您可能需要重新生成 initramfs 映像。Initramfs 包含您的系统启动时可能需要的驱动程序和固件文件。
请参考您的发行版文档了解如何更新 initramfs。一个过时 initramfs 的良好指示是系统在启动时加载错误的驱动或固件，
但当驱动程序稍后手动重新加载时一切正常。

为设备选择固件
-----------------------------

通常系统中的所有卡都使用同一类型的固件。
如果您想为特定的卡加载特定的固件映像，您可以使用 PCI 总线地址或序列号。驱动程序将在识别到 NFP 设备时打印它正在寻找的文件：

    nfp: 按照优先级顺序查找固件文件：
    nfp:  netronome/serial-00-12-34-aa-bb-cc-10-ff.nffw: 未找到
    nfp:  netronome/pci-0000:02:00.0.nffw: 未找到
    nfp:  netronome/nic_AMDA0081-0001_1x40.nffw: 已找到，正在加载..

在这种情况下，如果名为 `serial-00-12-34-aa-bb-5d-10-ff.nffw` 或 `pci-0000:02:00.0.nffw` 的文件（或链接）存在于 `/lib/firmware/netronome` 中，则此固件文件将优先于 `nic_AMDA*` 文件。

请注意，`serial-*` 和 `pci-*` 文件不会自动包含在 initramfs 中，您需要参考适当工具的文档来了解如何将它们包含进来。

运行中的固件版本
------------------------

可以通过 ethtool 命令显示特定 `<netdev>` 接口（例如 enp4s0），或接口端口 `<netdev port>` （例如 enp4s0np0）加载的固件版本：

  $ ethtool -i <netdev>

固件加载策略
-----------------------

固件加载策略通过存储在设备闪存中的三个 HWinfo 参数进行控制，这些参数作为键值对存储：

app_fw_from_flash
    定义哪个固件应具有优先权，'Disk'（0）、'Flash'（1）还是 'Preferred'（2）的固件。当选择 'Preferred' 时，管理固件会通过比较闪存固件和主机提供的固件的版本来决定将加载哪个固件。
这个变量可以通过 'fw_load_policy' devlink 参数进行配置。
abi_drv_reset
    定义了驱动程序是否应该在驱动程序被探测时重置固件，取决于固件是否在磁盘上找到，'Disk'（0）表示不重置，'Always'（1）始终重置，或 'Never'（2）从不重置。需要注意的是，如果在驱动程序被探测时加载了固件，则设备总是在驱动程序卸载时被重置。
此变量可通过 'reset_dev_on_drv_probe' 
devlink 参数进行配置。
abi_drv_load_ifc
定义了允许在设备上加载固件的PF设备列表
此变量当前不可由用户配置
Devlink 信息
============

devlink info 命令显示设备上的运行中和已存储的固件版本、序列号及板卡信息。
devlink info 命令示例（替换PCI地址）::

  $ devlink dev info pci/0000:03:00.0
    pci/0000:03:00.0:
      驱动 nfp
      序列号 CSAAMDA2001-1003000111
      版本：
          固定：
            board.id AMDA2001-1003
            board.rev 01
            board.manufacture CSA
            board.model mozart
          运行中：
            fw.mgmt 22.10.0-rc3
            fw.cpld 0x1000003
            fw.app nic-22.09.0
            chip.init AMDA-2001-1003  1003000111
          已存储：
            fw.bundle_id bspbundle_1003000111
            fw.mgmt 22.10.0-rc3
            fw.cpld 0x0
            chip.init AMDA-2001-1003  1003000111

配置设备
================

本节解释如何使用运行基本网卡固件的Agilio SmartNICs
配置接口链路速度
------------------------------
以下步骤说明了如何在Agilio CX 2x25GbE卡上切换10G模式和25G模式。更改端口速度必须按顺序进行，端口 0 (p0) 必须设置为10G之后端口 1 (p1) 才能设置为10G。
关闭相应的接口(s)::

  $ ip link set dev <网络设备端口 0> down
  $ ip link set dev <网络设备端口 1> down

将接口链路速度设置为10G::

  $ ethtool -s <网络设备端口 0> speed 10000
  $ ethtool -s <网络设备端口 1> speed 10000

将接口链路速度设置为25G::

  $ ethtool -s <网络设备端口 0> speed 25000
  $ ethtool -s <网络设备端口 1> speed 25000

重新加载驱动以使更改生效::

  $ rmmod nfp; modprobe nfp

配置接口最大传输单元 (MTU)
---------------------------------------------------

可以暂时使用iproute2、ip link或ifconfig工具设置接口的MTU。请注意，这种更改不会持久化。建议通过Network Manager或其他适当的OS配置工具来设置，因为使用Network Manager对MTU的更改可以被持久化。
将接口MTU设置为9000字节::

  $ ip link set dev <网络设备端口> mtu 9000

处理巨型帧或使用隧道时，设置适当的MTU值是用户的职责或编排层的责任。例如，如果从VM发送的数据包要在卡上封装并从物理端口离开，则VF的MTU应设置得低于物理端口的MTU，以考虑到额外的头部添加的额外字节数。如果预期会看到SmartNIC与内核之间的回退流量，用户还应确保PF的MTU适当设置，以避免在此路径上出现意外丢包。
配置前向纠错(FEC)模式
----------------------------------------------

Agilio SmartNICs支持FEC模式配置，如Auto、Firecode Base-R、ReedSolomon 和 Off 模式。每个物理端口的FEC模式都可以独立使用ethtool进行设置。可以通过以下命令查看接口支持的FEC模式::

  $ ethtool <网络设备>

可以通过以下命令查看当前配置的FEC模式::

  $ ethtool --show-fec <网络设备>

为了强制某端口的FEC模式，必须禁用自动协商（参见 `自动协商`_ 部分）。设置FEC模式为Reed-Solomon的一个示例是::

  $ ethtool --set-fec <网络设备> encoding rs

自动协商
----------------

要更改自动协商设置，首先需要将链路关闭。链路关闭后，可以使用以下命令启用或禁用自动协商::

  ethtool -s <网络设备> autoneg <on|off>

统计信息
==========

以下设备统计信息可通过 `ethtool -S` 接口获得：

.. flat-table:: NFP 设备统计信息
   :header-rows: 1
   :widths: 3 1 11

   * - 名称
     - ID
     - 含义

   * - dev_rx_discards
     - 1
     - 数据包可能因以下原因之一在接收路径中被丢弃：

        * 网卡未处于混杂模式，且目标MAC地址
          不匹配接口的MAC地址
        * 接收的数据包大于主机上的最大缓冲区大小
即，它超过了第三层的最大接收单元（MRU）。
* 在主机上没有可供该数据包使用的空闲列表描述符
很可能是网卡未能及时缓存一个空闲描述符
* 一个BPF程序丢弃了该数据包
* 执行了数据路径的丢包操作
* 由于网卡上缺乏足够的接收缓冲空间，MAC层丢弃了数据包
* - dev_rx_errors
     - 2
     - 数据包可能因为以下原因被计为接收错误（并被丢弃）：

       * VEB查找出现问题（仅当使用SR-IOV时）
* 物理层问题导致以太网错误，例如帧校验序列（FCS）或对齐错误。通常原因是故障的电缆或SFP模块
* - dev_rx_bytes
     - 3
     - 接收的总字节数
* - dev_rx_uc_bytes
     - 4
     - 接收的单播字节数
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
     - 当MAC正在执行流控制且网卡的TX队列空间耗尽时，可以在发送方向丢弃一个数据包
* - dev_tx_errors
     - 11
     - 数据包可能因为以下原因之一被计为发送错误（并被丢弃）：

       * 数据包是LSO分段，但无法确定第3层或第4层偏移量。因此无法继续进行LSO处理
* 通过PCIe接收到无效的数据包描述符
* 数据包的第3层长度超过了设备的MTU
* MAC/物理层上的错误。通常由于故障的电缆或SFP引起
* 无法分配 CTM 缓冲区
* 数据包的偏移量不正确，且无法通过网卡（NIC）进行修复
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
请注意，对于驱动程序未知的统计信息，将以
``dev_unknown_stat$ID`` 的形式显示，其中 ``$ID`` 指的是上表中的第二列。
您没有提供需要翻译的文本。请提供需要翻译成中文的英文或其他语言的文本。
