设备驱动程序基础设施
=============================

基本的设备驱动模型结构
----------------------------------------

.. kernel-doc:: include/linux/device.h
   :internal:
   :no-identifiers: device_link_state

.. kernel-doc:: include/linux/device/bus.h
   :identifiers: bus_type bus_notifier_event

.. kernel-doc:: include/linux/device/class.h
   :identifiers: class

.. kernel-doc:: include/linux/device/driver.h
   :identifiers: probe_type device_driver

设备驱动基础
-------------------

.. kernel-doc:: drivers/base/init.c
   :internal:

.. kernel-doc:: include/linux/device/driver.h
   :no-identifiers: probe_type device_driver

.. kernel-doc:: drivers/base/driver.c
   :export:

.. kernel-doc:: drivers/base/core.c
   :export:

.. kernel-doc:: drivers/base/syscore.c
   :export:

.. kernel-doc:: include/linux/device/class.h
   :no-identifiers: class

.. kernel-doc:: drivers/base/class.c
   :export:

.. kernel-doc:: drivers/base/node.c
   :internal:

.. kernel-doc:: drivers/base/transport_class.c
   :export:

.. kernel-doc:: drivers/base/dd.c
   :export:

.. kernel-doc:: include/linux/platform_device.h
   :internal:

.. kernel-doc:: drivers/base/platform.c
   :export:

.. kernel-doc:: include/linux/device/bus.h
   :no-identifiers: bus_type bus_notifier_event

.. kernel-doc:: drivers/base/bus.c
   :export:

设备驱动DMA管理
-----------------------------

.. kernel-doc:: kernel/dma/mapping.c
   :export:

设备驱动程序即插即用支持
--------------------------

.. kernel-doc:: drivers/pnp/core.c
   :internal:

.. kernel-doc:: drivers/pnp/card.c
   :export:

.. kernel-doc:: drivers/pnp/driver.c
   :internal:

.. kernel-doc:: drivers/pnp/manager.c
   :export:

.. kernel-doc:: drivers/pnp/support.c
   :export:

用户空间I/O设备
--------------------

.. kernel-doc:: drivers/uio/uio.c
   :export:

.. kernel-doc:: include/linux/uio_driver.h
   :internal:
