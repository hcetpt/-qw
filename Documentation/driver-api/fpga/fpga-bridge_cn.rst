FPGA 桥接器
==========

实现新的 FPGA 桥接器的 API
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

* `struct fpga_bridge` - FPGA 桥接器结构体
* `struct fpga_bridge_ops` - 低级桥接器驱动程序操作
* `__fpga_bridge_register()` - 创建并注册一个桥接器
* `fpga_bridge_unregister()` - 注销一个桥接器

辅助宏 `fpga_bridge_register()` 自动将注册 FPGA 桥接器的模块设置为所有者

.. kernel-doc:: include/linux/fpga/fpga-bridge.h
   :functions: fpga_bridge

.. kernel-doc:: include/linux/fpga/fpga-bridge.h
   :functions: fpga_bridge_ops

.. kernel-doc:: drivers/fpga/fpga-bridge.c
   :functions: __fpga_bridge_register

.. kernel-doc:: drivers/fpga/fpga-bridge.c
   :functions: fpga_bridge_unregister
