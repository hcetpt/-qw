.. SPDX 许可证标识符: GPL-2.0
.. include:: <isonum.txt>

====================================
PCI Express I/O 虚拟化指南
====================================

:版权: |copy| 2009 Intel Corporation
:作者: - 赵宇 <yu.zhao@intel.com>
          - Donald Dutile <ddutile@redhat.com>

概述
========

什么是 SR-IOV
--------------

单根 I/O 虚拟化（SR-IOV）是一种 PCI Express 扩展功能，使一个物理设备看起来像是多个虚拟设备。物理设备被称为物理功能（PF），而虚拟设备则被称为虚拟功能（VF）。PF 可以通过封装在该功能中的寄存器动态控制 VF 的分配。默认情况下，此功能未启用，PF 表现为传统的 PCIe 设备。一旦启用，每个 VF 的 PCI 配置空间可以通过其自身的总线、设备和功能编号（路由 ID）进行访问。每个 VF 还有一个用于映射其寄存器集的 PCI 内存空间。VF 设备驱动程序操作寄存器集，使其具有功能并表现为实际存在的 PCI 设备。

用户指南
==========

如何启用 SR-IOV 功能
----------------------------------

有多种方法可以启用 SR-IOV 功能。
在第一种方法中，设备驱动程序（PF 驱动程序）将通过 SR-IOV 核心提供的 API 控制该功能的启用和禁用。如果硬件具有 SR-IOV 功能，则加载其 PF 驱动程序会启用它以及与 PF 相关的所有 VF。一些 PF 驱动程序需要设置模块参数来确定要启用的 VF 数量。
在第二种方法中，对 sysfs 文件 `sriov_numvfs` 的写入将启用或禁用与 PCIe PF 相关联的 VF。此方法允许按 PF 启用或禁用 VF，而第一种方法适用于同一设备的所有 PF。此外，PCI SRIOV 核心支持确保启用/禁用操作有效，从而减少多个驱动程序中重复检查的次数，例如，在启用 VF 时检查 `numvfs == 0`，确保 `numvfs <= totalvfs`。
第二种方法是推荐的新/未来 VF 设备的方法。

如何使用虚拟功能
-----------------------------------

内核将 VF 视为热插拔的 PCI 设备，因此它们应该能够像真实的 PCI 设备一样工作。VF 需要与普通 PCI 设备相同的设备驱动程序。

开发者指南
===============

SR-IOV API
----------

为了启用 SR-IOV 功能：

(a) 对于第一种方法，在驱动程序中：

```c
int pci_enable_sriov(struct pci_dev *dev, int nr_virtfn);
```

`nr_virtfn` 是要启用的 VF 数量。
(b) 对于第二种方法，从 sysfs 中：

```sh
echo 'nr_virtfn' > /sys/bus/pci/devices/<DOMAIN:BUS:DEVICE.FUNCTION>/sriov_numvfs
```

为了禁用 SR-IOV 功能：

(a) 对于第一种方法，在驱动程序中：

```c
void pci_disable_sriov(struct pci_dev *dev);
```

(b) 对于第二种方法，从 sysfs 中：

```sh
echo 0 > /sys/bus/pci/devices/<DOMAIN:BUS:DEVICE.FUNCTION>/sriov_numvfs
```

要在主机上通过兼容驱动程序自动探测 VF，请在启用 SR-IOV 功能之前运行以下命令。这是默认行为。
```sh
echo 1 > \
    /sys/bus/pci/devices/<DOMAIN:BUS:DEVICE.FUNCTION>/sriov_drivers_autoprobe
```

要禁用主机上兼容驱动程序自动探测虚拟功能（VF），请在启用 SR-IOV 功能之前运行以下命令。更新此条目不会影响已经探测到的 VF。

```sh
echo 0 > \
    /sys/bus/pci/devices/<DOMAIN:BUS:DEVICE.FUNCTION>/sriov_drivers_autoprobe
```

使用示例
--------

下面的代码片段展示了 SR-IOV API 的使用方法：

```c
static int dev_probe(struct pci_dev *dev, const struct pci_device_id *id)
{
    pci_enable_sriov(dev, NR_VIRTFN);

    ..
    return 0;
}

static void dev_remove(struct pci_dev *dev)
{
    pci_disable_sriov(dev);

    ..
}

static int dev_suspend(struct device *dev)
{
    ..
    return 0;
}

static int dev_resume(struct device *dev)
{
    ..
    return 0;
}

static void dev_shutdown(struct pci_dev *dev)
{
    ..
}

static int dev_sriov_configure(struct pci_dev *dev, int numvfs)
{
    if (numvfs > 0) {
        ..
        pci_enable_sriov(dev, numvfs);
        ..
        return numvfs;
    }
    if (numvfs == 0) {
        ...
```
```c
pci_disable_sriov(dev);
			..
return 0;
	}

static struct pci_driver dev_driver = {
	.name =		"SR-IOV 物理功能驱动程序",
	.id_table =	dev_id_table,
	.probe =	dev_probe,
	.remove =	dev_remove,
	.driver.pm =	&dev_pm_ops,
	.shutdown =	dev_shutdown,
	.sriov_configure = dev_sriov_configure,
};
```
