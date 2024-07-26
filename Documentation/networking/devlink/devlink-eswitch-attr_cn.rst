... SPDX 许可证标识符: GPL-2.0

==========================
Devlink E-Switch 属性
==========================

Devlink E-Switch 支持两种操作模式：传统模式和 switchdev 模式。
传统模式基于传统的 MAC/VLAN 转发规则进行操作。交换决策依据 MAC 地址、VLAN 等因素做出。这种模式下，向硬件卸载转发规则的能力有限。
另一方面，switchdev 模式允许将更多的 E-Switch 功能卸载到硬件中。在 switchdev 模式下，更多的转发规则和逻辑可以被卸载到硬件交换 ASIC 中。它支持代表虚拟功能（VF）或可扩展功能（SF）的设备慢路径的代表网络设备。更多关于 :ref:`Documentation/networking/switchdev.rst <switchdev>` 和 :ref:`Documentation/networking/representors.rst <representors>` 的信息可见相关文档。
此外，devlink E-Switch 还包括以下列出的其他属性。
属性描述
======================

以下是 E-Switch 的属性列表。
.. list-table:: E-Switch 属性
   :widths: 8 5 45

   * - 名称
     - 类型
     - 描述
   * - ``mode``
     - 枚举类型
     - 设备的模式。模式可以是以下之一：

       * ``legacy`` 基于传统的 MAC/VLAN 转发规则操作
       * ``switchdev`` 允许更高级的功能卸载到硬件
   * - ``inline-mode``
     - 枚举类型
     - 部分硬件需要 VF 驱动程序将部分数据包头部放置在发送描述符上，以便 E-Switch 能够正确匹配和转发。此特性同时支持 switchdev 模式和传统模式
       * ``none`` 无
       * ``link`` 第二层（L2）模式
* ``network`` L3 模式
* ``transport`` L4 模式
* - ``encap-mode``
     - 枚举类型
     - 设备的封装模式。同时支持 switchdev 模式和传统模式。模式可以是以下之一：

       * ``none`` 禁用封装支持
       * ``basic`` 启用封装支持

示例用法
========

.. code:: shell

    # 启用 switchdev 模式
    $ devlink dev eswitch set pci/0000:08:00.0 mode switchdev

    # 设置 inline-mode 和 encap-mode
    $ devlink dev eswitch set pci/0000:08:00.0 inline-mode none encap-mode basic

    # 显示 devlink 设备 eswitch 的属性
    $ devlink dev eswitch show pci/0000:08:00.0
      pci/0000:08:00.0: mode switchdev inline-mode none encap-mode basic

    # 在传统模式下启用 encap-mode
    $ devlink dev eswitch set pci/0000:08:00.0 mode legacy inline-mode none encap-mode basic
