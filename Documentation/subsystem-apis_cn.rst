SPDX 许可证标识符: GPL-2.0

==============================
内核子系统文档
==============================

这些书籍深入探讨了特定内核子系统的工作原理，从内核开发者的角度出发。这里大部分信息直接来源于内核源代码，根据需要（或者至少在我们能够添加的情况下）补充了额外材料——可能**并非**所有所需的信息都已包含。
核心子系统
---------------

.. toctree::
   :maxdepth: 1

   core-api/index
   driver-api/index
   mm/index
   power/index
   scheduler/index
   timers/index
   locking/index

人机交互接口
----------------

.. toctree::
   :maxdepth: 1

   input/index
   hid/index
   sound/index
   gpu/index
   fb/index
   leds/index

网络接口
---------------------

.. toctree::
   :maxdepth: 1

   networking/index
   netlabel/index
   infiniband/index
   isdn/index
   mhi/index

存储接口
------------------

.. toctree::
   :maxdepth: 1

   filesystems/index
   block/index
   cdrom/index
   scsi/index
   target/index

其他子系统
----------------
**待修正**: 这里需要更多的组织工作
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

请注意，".. toctree::" 和 ":maxdepth: 1" 是 Sphinx 文档生成工具的指令，用于控制目录结构和深度，在中文翻译中通常保持不变。
