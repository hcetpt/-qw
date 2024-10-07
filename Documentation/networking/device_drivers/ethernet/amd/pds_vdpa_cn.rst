SPDX 许可证标识符: GPL-2.0+
注意：可以使用 /usr/bin/formiko-vim 编辑和查看

==========================================================
适用于 AMD/Pensando® DSC 适配器系列的 PCI vDPA 驱动程序
==========================================================

AMD/Pensando vDPA 虚拟功能设备驱动程序

版权所有 © 2023 Advanced Micro Devices, Inc

概述
========

``pds_vdpa`` 驱动程序是一个辅助总线驱动程序，提供一个用于 virtio 网络堆栈的 vDPA 设备。它与提供 vDPA 和 virtio 队列服务的 Pensando 虚拟功能设备一起使用。它依赖于 ``pds_core`` 驱动程序及其硬件来处理 PF 和 VF 的 PCI，并提供设备配置服务。

使用设备
================

``pds_vdpa`` 设备通过多个配置步骤启用，并且依赖于 ``pds_core`` 驱动程序创建并启用 SR-IOV 虚拟功能设备。在启用 VF 后，我们会在 ``pds_core`` 设备中启用 vDPA 服务以创建由 pds_vdpa 使用的辅助设备。示例步骤：

.. code-block:: bash

  #!/bin/bash

  modprobe pds_core
  modprobe vdpa
  modprobe pds_vdpa

  PF_BDF=`ls /sys/module/pds_core/drivers/pci:pds_core/*/sriov_numvfs | awk -F / '{print $7}'`

  # 在 PF 中启用 vDPA 虚拟功能辅助设备
  devlink dev param set pci/$PF_BDF name enable_vnet cmode runtime value true

  # 创建一个用于 vDPA 的 VF
  echo 1 > /sys/bus/pci/drivers/pds_core/$PF_BDF/sriov_numvfs

  # 查找可用的 vDPA 服务/设备
  PDS_VDPA_MGMT=`vdpa mgmtdev show | grep vDPA | head -1 | cut -d: -f1`

  # 创建一个用于 virtio 网络配置的 vDPA 设备
  vdpa dev add name vdpa1 mgmtdev $PDS_VDPA_MGMT mac 00:11:22:33:44:55

  # 在 vdpa 设备上设置以太网接口
  modprobe virtio_vdpa

启用驱动程序
===================

驱动程序通过标准内核配置系统启用，使用 `make` 命令：

  make oldconfig/menuconfig/etc

驱动程序位于以下菜单结构中：

  -> 设备驱动程序
    -> 网络设备支持 (NETDEVICES [=y])
      -> 以太网驱动程序支持
        -> Pensando 设备
          -> Pensando 以太网 PDS_VDPA 支持

支持
=======

对于一般 Linux 网络支持，请使用 netdev 邮件列表，该列表由 Pensando 人员监控：

  netdev@vger.kernel.org

对于更具体的驱动程序支持需求，请使用 Pensando 驱动程序支持电子邮件：

  drivers@pensando.io
