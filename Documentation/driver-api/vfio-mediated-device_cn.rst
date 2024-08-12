SPDX 许可证标识符：仅 GPL-2.0
.. include:: <isonum.txt>

=====================
VFIO 中介设备
=====================

:版权所有: |copy| 2016，NVIDIA CORPORATION。保留所有权利
:作者: Neo Jia <cjia@nvidia.com>
:作者: Kirti Wankhede <kwankhede@nvidia.com>



虚拟功能I/O（VFIO）中介设备[1]
===============================================

对于没有内置SR_IOV能力的DMA设备进行虚拟化的使用案例数量正在增加。以前，为了虚拟化此类设备，开发者必须创建他们自己的管理接口和API，然后将它们与用户空间软件集成。为了简化与用户空间软件的集成，我们已经确定了通用需求和统一的管理接口用于这类设备。
VFIO驱动框架提供了直接设备访问的统一API。它是一个IOMMU/设备无关的框架，在安全、IOMMU保护的环境中向用户空间暴露直接设备访问。此框架被多种设备使用，如GPU、网络适配器和计算加速器。通过直接设备访问，虚拟机或用户空间应用程序可以直接访问物理设备。该框架在中介设备中重用。
中介核心驱动提供了一个通用接口用于中介设备管理，可以被不同设备的驱动所使用。此模块提供了执行以下操作的通用接口：

* 创建和销毁一个中介设备
* 将中介设备添加到和从中移除中介总线驱动
* 将中介设备添加到和从中移除IOMMU组

中介核心驱动还提供了一个接口来注册总线驱动。
例如，中介VFIO mdev驱动是为中介设备设计的，并支持VFIO API。中介总线驱动会将中介设备添加到和从中移除VFIO组。
下面的高级块图展示了VFIO中介驱动框架中的主要组件和接口。图中显示了NVIDIA、Intel和IBM设备作为示例，因为这些设备是首批使用此模块的设备。

     +---------------+
     |               |
     | +-----------+ |  mdev_register_driver() +--------------+
     | |           | +<------------------------+              |
     | |  mdev     | |                         |              |
     | |  bus      | +------------------------>+ vfio_mdev.ko |<-> VFIO 用户
     | |  driver   | |     probe()/remove()    |              |    API
     | |           | |                         +--------------+
     | +-----------+ |
     |               |
     |  MDEV CORE    |
     |   MODULE      |
     |   mdev.ko     |
     | +-----------+ |  mdev_register_parent() +--------------+
     | |           | +<------------------------+              |
     | |           | |                         | ccw_device.ko|<-> 物理
     | |           | +------------------------>+              |    设备
     | | Physical  | |
     | |  device   | |  mdev_register_parent() +--------------+
     | | interface | |<------------------------+              |
     | |           | |                         |  i915.ko     |<-> 物理
     | |           | +------------------------>+              |    设备
     | |           | |        回调函数        +--------------+
     | +-----------+ |
     +---------------+

注册接口
=======================

中介核心驱动提供了以下类型的注册接口：

* 中介总线驱动的注册接口
* 物理设备驱动接口

中介总线驱动的注册接口
------------------------------------------------

中介设备驱动的注册接口提供了以下结构来表示中介设备的驱动程序：

     /*
      * 结构 mdev_driver [2] - 中介设备的驱动程序
      * @probe: 当新设备创建时调用
      * @remove: 当设备移除时调用
      * @driver: 设备驱动程序结构
      */
     结构 mdev_driver {
	     int  (*probe)  (结构 mdev_device *dev);
	     void (*remove) (结构 mdev_device *dev);
	     unsigned int (*get_available)(结构 mdev_type *mtype);
	     ssize_t (*show_description)(结构 mdev_type *mtype, 字符 *buf);
	     结构 device_driver    driver;
     };

中介总线驱动mdev应该使用这个结构在函数调用中注册和注销自身与核心驱动：

* 注册：

    int mdev_register_driver(结构 mdev_driver *drv);

* 注销：

    void mdev_unregister_driver(结构 mdev_driver *drv);

中介总线驱动的probe函数应该在mdev_device上创建一个vfio_device，并将其连接到适当的vfio_device_ops实现。
当驱动想要为其已probe过的现有设备添加GUID创建sysfs时，则应调用：

    int mdev_register_parent(结构 mdev_parent *parent, 结构 device *dev,
			结构 mdev_driver *mdev_driver);

这将提供'mdev_supported_types/XX/create'文件，然后可以用来触发mdev_device的创建。创建的mdev_device将附加到指定的驱动。
当驱动需要移除自身时，它应调用：

    void mdev_unregister_parent(结构 mdev_parent *parent);

这将解除绑定并销毁所有创建的mdev，并移除sysfs文件。
中介设备通过sysfs的管理接口
==================================================

通过sysfs的管理接口使用户空间软件（如libvirt）能够以硬件无关的方式查询和配置中介设备。
此管理接口为底层物理设备的驱动提供了灵活性以支持如下特性：

* 中介设备热插拔
* 单个虚拟机中的多个中介设备
* 不同物理设备的多个中介设备

mdev_bus类目录中的链接
-------------------------------------
/sys/class/mdev_bus/ 目录包含已注册到mdev核心驱动的设备链接
每个物理设备下的 sysfs 目录和文件
--------------------------------------------------------------

::

  |- [父级物理设备]
  |--- 设备商特定属性 [可选]
  |--- [mdev_supported_types]
  |     |--- [<type-id>]
  |     |   |--- create
  |     |   |--- name
  |     |   |--- available_instances
  |     |   |--- device_api
  |     |   |--- description
  |     |   |--- [devices]
  |     |--- [<type-id>]
  |     |   |--- create
  |     |   |--- name
  |     |   |--- available_instances
  |     |   |--- device_api
  |     |   |--- description
  |     |   |--- [devices]
  |     |--- [<type-id>]
  |          |--- create
  |          |--- name
  |          |--- available_instances
  |          |--- device_api
  |          |--- description
  |          |--- [devices]

* [mdev_supported_types]

  当前支持的中介设备类型及其详细信息列表。
  [<type-id>]、device_api 和 available_instances 是必须由设备商驱动提供的属性。
* [<type-id>]

  [<type-id>] 的名称是通过将设备驱动字符串作为前缀添加到设备商驱动提供的字符串来创建的。此名称的格式如下所示：

    ::

      sprintf(buf, "%s-%s", dev_driver_string(parent->dev), group->name);

* device_api

  此属性显示正在创建的设备API是什么，例如对于PCI设备为 "vfio-pci"。
* available_instances

  此属性显示可以创建的 <type-id> 类型的设备数量。
* [device]

  此目录包含已创建的 <type-id> 类型设备的链接。
* name

  此属性显示一个便于人阅读的名称。
* description

  此属性可以显示类型的简要特性/描述。这是一个可选属性。

每个 mdev 设备下的 sysfs 目录和文件
----------------------------------------------------------

::

  |- [父级物理设备]
  |--- [$MDEV_UUID]
         |--- remove
         |--- mdev_type {指向其类型的链接}
         |--- 设备商特定属性 [可选]

* remove (只写)

  在 'remove' 文件中写入 '1' 将销毁 mdev 设备。如果该设备处于活动状态并且设备商驱动不支持热插拔，则设备商驱动可以拒绝 remove() 回调。
  示例:

    ::

      # echo 1 > /sys/bus/mdev/devices/$mdev_UUID/remove

中介设备热插拔
------------------------

中介设备可以在运行时创建并分配。中介设备热插拔的过程与PCI设备热插拔过程相同。

中介设备的转换API
=====================================

以下API用于在VFIO驱动中从用户页框号(user pfn)转换为主页框号(host pfn)::

  int vfio_pin_pages(struct vfio_device *device, dma_addr_t iova,
                  int npage, int prot, struct page **pages);

  void vfio_unpin_pages(struct vfio_device *device, dma_addr_t iova,
                    int npage);

这些函数通过使用 struct vfio_iommu_driver_ops[4] 中的 pin_pages 和 unpin_pages 回调回调回到后端IOMMU模块。目前这些回调仅在TYPE1 IOMMU模块中得到支持。为了在其他IOMMU后端模块（如PPC64 sPAPR模块）中启用它们，需要提供这两个回调函数。
参考
==========

1. 有关 VFIO 的更多信息，请参阅 `Documentation/driver-api/vfio.rst`。
2. `struct mdev_driver` 在 `include/linux/mdev.h` 中。
3. `struct mdev_parent_ops` 在 `include/linux/mdev.h` 中。
4. `struct vfio_iommu_driver_ops` 在 `include/linux/vfio.h` 中。
