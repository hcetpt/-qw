... SPDX 许可证标识符: GPL-2.0

==========================
Devlink E-Switch 属性
==========================

Devlink E-Switch 支持两种操作模式：传统模式（legacy）和 switchdev 模式。
- 传统模式（legacy）基于传统的 MAC/VLAN 转发规则运行。交换决策是基于 MAC 地址、VLAN 等因素做出的。其硬件卸载能力有限。
- 另一方面，switchdev 模式允许 E-Switch 更高级的硬件卸载功能。在 switchdev 模式下，更多的交换规则和逻辑可以卸载到硬件交换 ASIC 中。它支持表示虚拟功能（VFs）或设备的可扩展功能（SFs）慢路径的代表网卡（representor netdevices）。更多关于 switchdev 和 representors 的信息，请参阅 :ref:`Documentation/networking/switchdev.rst <switchdev>` 和 :ref:`Documentation/networking/representors.rst <representors>`。

此外，devlink E-Switch 还具有以下属性：
Attributes Description
======================

以下是 E-Switch 的属性列表：
.. list-table:: E-Switch 属性
   :widths: 8 5 45

   * - 名称
     - 类型
     - 描述
   * - ``mode``
     - 枚举类型
     - 设备的模式。模式可以是以下之一：

       * ``legacy`` 基于传统的 MAC/VLAN 转发规则运行
       * ``switchdev`` 允许 E-Switch 进行更高级的硬件卸载功能
   * - ``inline-mode``
     - 枚举类型
     - 一些硬件需要 VF 驱动程序将部分数据包头部放在 TX 描述符上，以便 E-Switch 能够进行正确的匹配和转发。支持 switchdev 模式和传统模式。
       * ``none`` 无
       * ``link`` L2 模式
* ``network`` L3模式
* ``transport`` L4模式
* - ``encap-mode``
     - 枚举类型
     - 设备的封装模式。支持switchdev模式和legacy模式。模式可以是以下之一：

       * ``none`` 禁用封装支持
       * ``basic`` 启用封装支持

示例用法
========

.. code:: shell

    # 启用switchdev模式
    $ devlink dev eswitch set pci/0000:08:00.0 mode switchdev

    # 设置inline-mode和encap-mode
    $ devlink dev eswitch set pci/0000:08:00.0 inline-mode none encap-mode basic

    # 显示devlink设备eswitch属性
    $ devlink dev eswitch show pci/0000:08:00.0
      pci/0000:08:00.0: mode switchdev inline-mode none encap-mode basic

    # 启用legacy模式下的encap-mode
    $ devlink dev eswitch set pci/0000:08:00.0 mode legacy inline-mode none encap-mode basic
