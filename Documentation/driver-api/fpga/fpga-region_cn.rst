FPGA 区域
==========

概述
------

本文档旨在简要概述 FPGA 区域 API 的使用。关于区域的更概念性的介绍可以在设备树绑定文档中找到 [#f1]_。
对于本 API 文档的目的，我们可以简单地说一个区域将一个 FPGA 管理器和一座桥（或几座桥）与 FPGA 中可重新编程的区域或整个 FPGA 关联起来。该 API 提供了一种注册区域以及对区域进行编程的方法。
目前内核中 fpga-region.c 之上的唯一一层是设备树支持层 (of-fpga-region.c)，在 [#f1]_ 中有所描述。设备树支持层使用区域来对 FPGA 进行编程，然后使用设备树来处理枚举。通用的区域代码旨在被其他方案使用，这些方案有其他方式在编程后完成枚举。
一个 FPGA 区域可以设置为了解以下内容：

 * 使用哪个 FPGA 管理器来进行编程

 * 在编程前禁用哪些桥并在之后启用
为了对 FPGA 图像进行编程需要传递额外的信息，这些信息包含在结构体 fpga_image_info 中，包括：

 * 图像的指针，可以是分散-聚集缓冲区、连续缓冲区或者固件文件的名称

 * 标志位，指示具体信息如图像是否用于部分重构
如何添加新的 FPGA 区域
------------------------------

一个使用示例可以在 [#f2]_ 中的探测函数中看到。

添加新 FPGA 区域的 API
------------------------------

* struct fpga_region - FPGA 区域结构体
* struct fpga_region_info - __fpga_region_register_full() 函数的参数结构体
* __fpga_region_register_full() - 使用 fpga_region_info 结构体创建并注册一个 FPGA 区域以提供最大灵活性
* __fpga_region_register() - 使用标准参数创建并注册一个 FPGA 区域
* fpga_region_unregister() - 注销一个 FPGA 区域

辅助宏 `fpga_region_register()` 和 `fpga_region_register_full()` 自动将注册 FPGA 区域的模块设置为所有者
FPGA 区域的探测函数需要获取将用于编程的 FPGA 管理器的引用。这通常会在区域的探测函数期间发生
* fpga_mgr_get() - 获取对一个 FPGA 管理器的引用，并增加引用计数
* of_fpga_mgr_get() - 给定设备节点，获取对一个 FPGA 管理器的引用，并增加引用计数
* fpga_mgr_put() - 释放一个 FPGA 管理器

在编程 FPGA 时，FPGA 区域需要指定要控制的桥。区域驱动程序可以在探测期间构建桥列表 (:c:expr:`fpga_region->bridge_list`) 或者有一个函数在编程前创建要编程的桥列表 (:c:expr:`fpga_region->get_bridges`)。FPGA 桥框架提供了以下 API 来处理构建或拆解该列表。
* `fpga_bridge_get_to_list()` - 获取FPGA桥接器的引用，并将其添加到一个列表中
* `of_fpga_bridge_get_to_list()` - 根据设备节点获取FPGA桥接器的引用，并将其添加到一个列表中
* `fpga_bridges_put()` - 给定一个桥接器列表，释放这些桥接器

.. kernel-doc:: include/linux/fpga/fpga-region.h
   :functions: fpga_region

.. kernel-doc:: include/linux/fpga/fpga-region.h
   :functions: fpga_region_info

.. kernel-doc:: drivers/fpga/fpga-region.c
   :functions: __fpga_region_register_full

.. kernel-doc:: drivers/fpga/fpga-region.c
   :functions: __fpga_region_register

.. kernel-doc:: drivers/fpga/fpga-region.c
   :functions: fpga_region_unregister

.. kernel-doc:: drivers/fpga/fpga-mgr.c
   :functions: fpga_mgr_get

.. kernel-doc:: drivers/fpga/fpga-mgr.c
   :functions: of_fpga_mgr_get

.. kernel-doc:: drivers/fpga/fpga-mgr.c
   :functions: fpga_mgr_put

.. kernel-doc:: drivers/fpga/fpga-bridge.c
   :functions: fpga_bridge_get_to_list

.. kernel-doc:: drivers/fpga/fpga-bridge.c
   :functions: of_fpga_bridge_get_to_list

.. kernel-doc:: drivers/fpga/fpga-bridge.c
   :functions: fpga_bridges_put
