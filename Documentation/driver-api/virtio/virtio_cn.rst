### SPDX 许可证标识符: GPL-2.0

### _virtio_

===============
Linux 上的 Virtio
===============

#### 简介
============

Virtio 是一个开放标准，定义了一个协议，用于不同类型设备与驱动程序之间的通信，详情参见 virtio 规范第 5 章("设备类型")([1]_)。最初作为由虚拟机监控器实现的准虚拟化设备的标准开发，它可以用来使任何符合标准的设备（真实的或模拟的）与驱动程序进行交互。为了说明的目的，本文档将重点放在最常见的案例上：在虚拟机中运行的 Linux 内核使用虚拟机监控器提供的准虚拟化设备，这些设备通过 PCI 等标准机制作为 virtio 设备暴露给虚拟机。

设备 - 驱动通信：virtqueues
=====================================

虽然 virtio 设备实际上是虚拟机监控器中的抽象层，但它们对客户机来说像是通过特定传输方法（如 PCI、MMIO 或 CCW）暴露的物理设备，这与设备本身是正交的。virtio 规范详细定义了这些传输方法，包括设备发现、功能和中断处理。
驱动程序与虚拟机监控器中的设备之间的通信是通过共享内存完成的（这就是 virtio 设备如此高效的原因），使用称为 virtqueues 的特殊数据结构，实际上是类似于网络设备中使用的缓冲区描述符环形缓冲区：

.. kernel-doc:: include/uapi/linux/virtio_ring.h
    :identifiers: struct vring_desc

所有描述符指向的缓冲区都由客户机分配，并被主机用于读取或写入但不能同时用于两者。
请参考 virtio 规范第 2.5 章("Virtqueues")([1]_)了解 virtqueues 的定义，以及 "Virtqueues 和 virtio ring: 数据如何传输" 博客文章([2]_)以获得主机设备和客户机驱动程序之间通信的插图概述。
:c:type:`vring_virtqueue` 结构体建模了一个 virtqueue，包括环形缓冲区和管理数据。嵌入在这个结构体中的 :c:type:`virtqueue` 结构体是最终由 virtio 驱动程序使用的数据结构：

.. kernel-doc:: include/linux/virtio.h
    :identifiers: struct virtqueue

该结构体指向的回调函数会在设备消耗了驱动程序提供的缓冲区时被触发。更具体地说，触发器将是虚拟机监控器发出的中断（参见 vring_interrupt()）。在 virtqueue 设置过程中（传输方式特定），为 virtqueue 注册中断请求处理器。

.. kernel-doc:: drivers/virtio/virtio_ring.c
    :identifiers: vring_interrupt

#### 设备发现与探测
=======================

在内核中，virtio 核心包含 virtio 总线驱动程序和特定于传输方式的驱动程序，如 `virtio-pci` 和 `virtio-mmio`。然后有针对特定设备类型的单独 virtio 驱动程序，它们注册到 virtio 总线驱动程序。
virtio 设备如何被内核发现和配置取决于虚拟机监控器如何定义它。以 `QEMU virtio-console <https://gitlab.com/qemu-project/qemu/-/blob/master/hw/char/virtio-console.c>`__ 设备为例。当使用 PCI 作为传输方式时，该设备将以供应商 0x1af4（红帽公司）和设备 ID 0x1003（virtio 控制台）出现在 PCI 总线上，如规范所定义，因此内核会像检测其他任何 PCI 设备一样检测它。
在 PCI 枚举过程中，如果找到匹配 virtio-pci 驱动程序的设备（根据 virtio-pci 设备表，任何具有供应商 ID 0x1af4 的 PCI 设备）：

	/* Qumranet 捐赠了用于设备 0x1000 至 0x10FF 的供应商 ID。*/
	static const struct pci_device_id virtio_pci_id_table[] = {
		{ PCI_DEVICE(PCI_VENDOR_ID_REDHAT_QUMRANET, PCI_ANY_ID) },
		{ 0 }
	};

那么 virtio-pci 驱动程序将被探测，如果探测成功，该设备将注册到 virtio 总线上：

	static int virtio_pci_probe(struct pci_dev *pci_dev,
				    const struct pci_device_id *id)
	{
		..
if (force_legacy) {
			rc = virtio_pci_legacy_probe(vp_dev);
			/* 如果我们无法映射 BAR0（没有 I/O 空间），也尝试现代模式。*/
			if (rc == -ENODEV || rc == -ENOMEM)
				rc = virtio_pci_modern_probe(vp_dev);
			if (rc)
				goto err_probe;
		} else {
			rc = virtio_pci_modern_probe(vp_dev);
			if (rc == -ENODEV)
				rc = virtio_pci_legacy_probe(vp_dev);
			if (rc)
				goto err_probe;
		}

		..
这段英文描述可以翻译为如下中文：

`rc = register_virtio_device(&vp_dev->vdev);`

当设备注册到virtio总线时，内核会查找总线上能够处理该设备的驱动，并调用该驱动的“probe”方法。
此时，通过调用相应的“virtio_find”辅助函数（例如virtio_find_single_vq()或virtio_find_vqs()），将分配并配置virtqueues，这些函数最终会调用特定传输层的“find_vqs”方法。

参考文献
========

_`[1]` Virtio规范v1.2:
https://docs.oasis-open.org/virtio/virtio/v1.2/virtio-v1.2.html

.. 也请检查规范的后续版本
_`[2]` Virtqueues和virtio环：数据如何传输
https://www.redhat.com/zh_cn/blog/virtqueues-and-virtio-ring-数据如何传输

.. 注释

.. [#f1] 这就是为什么它们也可以被称为virtrings的原因
