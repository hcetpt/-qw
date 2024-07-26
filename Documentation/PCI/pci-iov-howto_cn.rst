### SPDX 许可证标识符: GPL-2.0
### 包含: <isonum.txt>

======================================
PCI Express I/O 虚拟化指南
======================================

**版权所有:** |copy| 2009 Intel Corporation
**作者:** 
- 尤钊 <yu.zhao@intel.com>
- 唐纳德·杜蒂尔 <ddutile@redhat.com>

概述
=====

什么是 SR-IOV
---------------

单根 I/O 虚拟化 (SR-IOV) 是一种 PCI Express 扩展功能，它可以让一个物理设备表现为多个虚拟设备。物理设备被称为物理功能 (PF)，而虚拟设备被称为虚拟功能 (VF)。PF 可以通过封装在该功能中的寄存器来动态控制 VF 的分配。默认情况下，此功能未启用，PF 行为与传统的 PCIe 设备相同。一旦启用，每个 VF 的 PCI 配置空间都可以通过其自身的总线、设备和功能编号（路由 ID）进行访问。每个 VF 还具有用于映射其寄存器集的 PCI 内存空间。VF 设备驱动程序在寄存器集上操作，因此它可以具有功能性并表现为一个真实的存在的 PCI 设备。

用户指南
=========

如何启用 SR-IOV 功能
-----------------------

有多种方法可以启用 SR-IOV 功能。
第一种方法中，设备驱动程序（PF 驱动程序）将通过 SR-IOV 核心提供的 API 来控制该功能的启用和禁用。如果硬件具备 SR-IOV 功能，加载 PF 驱动程序将会启用该功能以及与 PF 相关的所有 VF。一些 PF 驱动程序需要设置模块参数来确定要启用的 VF 数量。
第二种方法是向 sysfs 文件 `sriov_numvfs` 写入数据，以启用和禁用与 PCIe PF 相关联的 VF。这种方法允许按 PF 设置 VF 的启用/禁用值，而第一种方法则适用于同一设备的所有 PF。此外，PCI SRIOV 核心支持确保启用/禁用操作的有效性，减少在多个驱动程序中进行相同检查的重复工作，例如，在启用 VF 时检查 `numvfs == 0`，确保 `numvfs <= totalvfs`。
第二种方法是推荐用于新/未来 VF 设备的方法。

如何使用虚拟功能
--------------------

内核中将 VF 视为热插拔的 PCI 设备，因此它们应该能够像真正的 PCI 设备一样工作。VF 需要有与普通 PCI 设备相同的设备驱动程序。

开发者指南
===========

SR-IOV API
-----------

为了启用 SR-IOV 功能：

1. 对于第一种方法，在驱动程序中：
   
   ```c
   int pci_enable_sriov(struct pci_dev *dev, int nr_virtfn);
   ```

   `nr_virtfn` 是要启用的 VF 数量。

2. 对于第二种方法，从 sysfs 中：

   ```bash
   echo 'nr_virtfn' > /sys/bus/pci/devices/<DOMAIN:BUS:DEVICE.FUNCTION>/sriov_numvfs
   ```

为了禁用 SR-IOV 功能：

1. 对于第一种方法，在驱动程序中：
   
   ```c
   void pci_disable_sriov(struct pci_dev *dev);
   ```

2. 对于第二种方法，从 sysfs 中：

   ```bash
   echo 0 > /sys/bus/pci/devices/<DOMAIN:BUS:DEVICE.FUNCTION>/sriov_numvfs
   ```

为了使主机上的兼容驱动程序能够自动探测 VF，请在启用 SR-IOV 功能之前运行以下命令。这是默认行为。
下面的命令会将值设置为1，以使兼容的驱动程序在主机上自动探测虚拟功能（VF）：

```shell
echo 1 > \
        /sys/bus/pci/devices/<DOMAIN:BUS:DEVICE.FUNCTION>/sriov_drivers_autoprobe
```

为了禁用主机上兼容驱动程序对虚拟功能（VF）的自动探测，在启用SR-IOV功能之前运行以下命令：

```shell
echo  0 > \
        /sys/bus/pci/devices/<DOMAIN:BUS:DEVICE.FUNCTION>/sriov_drivers_autoprobe
```

更新这个条目不会影响已经探测过的虚拟功能（VF）。

### 使用示例

下面的代码片段展示了SR-IOV API的使用方法：

```c
static int dev_probe(struct pci_dev *dev, const struct pci_device_id *id)
{
	pci_enable_sriov(dev, NR_VIRTFN);

	// 其他代码...
	return 0;
}

static void dev_remove(struct pci_dev *dev)
{
	pci_disable_sriov(dev);

	// 其他代码...
}

static int dev_suspend(struct device *dev)
{
	// 其他代码...
	return 0;
}

static int dev_resume(struct device *dev)
{
	// 其他代码...
	return 0;
}

static void dev_shutdown(struct pci_dev *dev)
{
	// 其他代码...
}

static int dev_sriov_configure(struct pci_dev *dev, int numvfs)
{
	if (numvfs > 0) {
		// 其他代码...
		pci_enable_sriov(dev, numvfs);
		// 其他代码...
		return numvfs;
	}
	if (numvfs == 0) {
		// 其他代码...
	}
}
```

这里假设`NR_VIRTFN`是一个预先定义好的常量，表示需要创建的虚拟功能数量。
```c
// 禁用设备dev的SR-IOV功能
pci_disable_sriov(dev);

// ...
return 0;
}

// 定义一个PCI驱动结构体dev_driver
static struct pci_driver dev_driver = {
    .name = "SR-IOV Physical Function driver", // 驱动名称
    .id_table = dev_id_table, // 设备ID表
    .probe = dev_probe, // 探测函数
    .remove = dev_remove, // 移除函数
    .driver.pm = &dev_pm_ops, // 电源管理操作
    .shutdown = dev_shutdown, // 关闭函数
    .sriov_configure = dev_sriov_configure, // SR-IOV配置函数
};
```
