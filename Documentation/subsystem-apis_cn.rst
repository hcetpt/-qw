SPDX 许可证标识符: GPL-2.0

==============================
内核子系统文档
==============================

这些书籍深入介绍了从内核开发者的角度出发，特定的内核子系统是如何工作的。这里的许多信息直接来源于内核源代码，并根据需要添加了补充材料（或者至少是我们设法添加的部分——可能**并非**所有需要的信息）。
核心子系统
-----------

.. toctree::
   :maxdepth: 1

   core-api/index
   driver-api/index
   mm/index
   power/index
   scheduler/index
   timers/index
   locking/index

人机接口
---------

.. toctree::
   :maxdepth: 1

   input/index
   hid/index
   sound/index
   gpu/index
   fb/index
   leds/index

网络接口
--------

.. toctree::
   :maxdepth: 1

   networking/index
   netlabel/index
   infiniband/index
   isdn/index
   mhi/index

存储接口
--------

.. toctree::
   :maxdepth: 1

   filesystems/index
   block/index
   cdrom/index
   scsi/index
   target/index

其他子系统
----------

**待办事项**: 这里还需要大量的组织工作
.. toctree::
   :maxdepth: 1

   accounting/index
   cpu-freq/index
   fpga/index
   i2c/index
   iio/index
   pcmcia/index
   spi/index
   w1/index
   watchdog/index
   virt/index
   hwmon/index
   accel/index
   security/index
   crypto/index
   bpf/index
   usb/index
   PCI/index
   misc-devices/index
   peci/index
   wmi/index
   tee/index
