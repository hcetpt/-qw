SPDX许可证标识符: GPL-2.0+
注意：可以使用 /usr/bin/formiko-vim 编辑和查看

==========================================================
适用于 AMD/Pensando® DSC 适配器系列的 PCI VFIO 驱动程序
==========================================================

AMD/Pensando Linux VFIO PCI 设备驱动程序
版权所有 (c) 2023 Advanced Micro Devices, Inc
概述
========

`pds-vfio-pci` 模块是一个支持 DSC 硬件中 Live Migration 功能的虚拟功能（VF）设备的 PCI 驱动程序。
使用该设备
================

`pds-vfio-pci` 设备通过多个配置步骤启用，并依赖于 `pds_core` 驱动程序来创建和启用 SR-IOV 虚拟功能设备。下面展示了将驱动程序绑定到一个 VF 以及由 `pds_core` 驱动程序创建的相关辅助设备的步骤。此示例假设 pds_core 和 pds-vfio-pci 模块已加载。

```bash
#!/bin/bash

PF_BUS="0000:60"
PF_BDF="0000:60:00.0"
VF_BDF="0000:60:00.1"

# 防止非 vfio 的 VF 驱动程序探测 VF 设备
echo 0 > /sys/class/pci_bus/$PF_BUS/device/$PF_BDF/sriov_drivers_autoprobe

# 通过 pds_core 创建用于 Live Migration 的单个 VF
echo 1 > /sys/bus/pci/drivers/pds_core/$PF_BDF/sriov_numvfs

# 允许 VF 绑定到 pds-vfio-pci 驱动程序
echo "pds-vfio-pci" > /sys/class/pci_bus/$PF_BUS/device/$VF_BDF/driver_override

# 将 VF 绑定到 pds-vfio-pci 驱动程序
echo "$VF_BDF" > /sys/bus/pci/drivers/pds-vfio-pci/bind
```

执行上述步骤后，应在 /dev/vfio/<iommu_group> 中创建一个文件。
启用驱动程序
==================

通过标准内核配置系统使用 make 命令启用驱动程序：

```
make oldconfig/menuconfig/etc
```

驱动程序位于以下菜单结构中：

```
-> 设备驱动程序
  -> VFIO 非特权用户空间驱动程序框架
    -> 对 PDS PCI 设备的支持
```

支持
======

对于通用的 Linux 网络支持，请使用 netdev 邮件列表，该列表由 Pensando 人员监控：

```
netdev@vger.kernel.org
```

对于更具体的帮助需求，请使用 Pensando 驱动程序支持电子邮件：

```
drivers@pensando.io
```
