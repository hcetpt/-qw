SPDX许可证标识符: GPL-2.0+
注意：可以使用/usr/bin/formiko-vim进行编辑和查看

==========================================================
AMD/Pensando® DSC 适配器家族的 PCI VFIO 驱动程序
==========================================================

AMD/Pensando Linux VFIO PCI 设备驱动程序
版权所有 © 2023 Advanced Micro Devices, Inc
概述
========

`pds-vfio-pci` 模块是一个 PCI 驱动程序，支持 DSC 硬件中的可实时迁移的虚拟功能（VF）设备。
使用该设备
================

`pds-vfio-pci` 设备通过多个配置步骤启用，并依赖于 `pds_core` 驱动程序来创建并启用 SR-IOV 虚拟功能设备。以下步骤展示了如何将驱动程序绑定到一个 VF 和 `pds_core` 驱动程序创建的相关辅助设备。本例假设 `pds_core` 和 `pds-vfio-pci` 模块已经加载。

```bash
#!/bin/bash

PF_BUS="0000:60"
PF_BDF="0000:60:00.0"
VF_BDF="0000:60:00.1"

# 防止非 vfio 的 VF 驱动程序探测 VF 设备
echo 0 > /sys/class/pci_bus/$PF_BUS/device/$PF_BDF/sriov_drivers_autoprobe

# 通过 pds_core 创建单个 VF 以实现实时迁移
echo 1 > /sys/bus/pci/drivers/pds_core/$PF_BDF/sriov_numvfs

# 允许 VF 绑定到 pds-vfio-pci 驱动程序
echo "pds-vfio-pci" > /sys/class/pci_bus/$PF_BUS/device/$VF_BDF/driver_override

# 将 VF 绑定到 pds-vfio-pci 驱动程序
echo "$VF_BDF" > /sys/bus/pci/drivers/pds-vfio-pci/bind
```

执行上述步骤后，应在 /dev/vfio/<iommu_group> 中创建一个文件。
启用驱动程序
===================

该驱动程序通过标准内核配置系统启用，使用 make 命令：

```
make oldconfig/menuconfig/etc
```

该驱动程序位于菜单结构中：

  -> 设备驱动程序
    -> VFIO 非特权用户空间驱动框架
      -> 支持 PDS PCI 设备的 VFIO

支持
=======

对于通用 Linux 网络支持，请使用 netdev 邮件列表，该列表由 Pensando 工作人员监控：

```
netdev@vger.kernel.org
```

对于更具体的驱动支持需求，请使用 Pensando 驱动支持电子邮件：

```
drivers@pensando.io
```
