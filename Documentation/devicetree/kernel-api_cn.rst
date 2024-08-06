```SPDX 许可证标识符: GPL-2.0
.. _设备树:

======================================
设备树(DeviceTree)内核API
======================================

核心函数
--------------

.. 内核文档:: drivers/of/base.c
   :导出:

.. 内核文档:: include/linux/of.h
   :内部:

.. 内核文档:: drivers/of/property.c
   :导出:

.. 内核文档:: include/linux/of_graph.h
   :内部:

.. 内核文档:: drivers/of/address.c
   :导出:

.. 内核文档:: drivers/of/irq.c
   :导出:

.. 内核文档:: drivers/of/fdt.c
   :导出:

驱动模型函数
----------------------

.. 内核文档:: include/linux/of_device.h
   :内部:

.. 内核文档:: drivers/of/device.c
   :导出:

.. 内核文档:: include/linux/of_platform.h
   :内部:

.. 内核文档:: drivers/of/platform.c
   :导出:

覆盖层和动态DT函数
--------------------------------

.. 内核文档:: drivers/of/resolver.c
   :导出:

.. 内核文档:: drivers/of/dynamic.c
   :导出:

.. 内核文档:: drivers/of/overlay.c
   :导出:
```

注释中的`.. kernel-doc::`表示文档引用，用于标记内核源码中需要展示的部分，不是实际的代码或文本内容。在实际的文档中，这部分会被解析并展示为相应的函数、宏等API文档。
