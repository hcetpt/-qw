SPDX 许可证标识符: GPL-2.0

==========================
etas_es58x devlink 支持
==========================

本文档描述了由 ``etas_es58x`` 设备驱动程序实现的 devlink 功能。

信息版本
=============

``etas_es58x`` 驱动程序报告以下版本：

.. list-table:: 实现的 devlink 信息版本
   :widths: 5 5 90

   * - 名称
     - 类型
     - 描述
   * - ``fw``
     - 运行中
     - 设备上运行的固件版本。也可以通过 ``ethtool -i`` 作为 ``firmware-version`` 的第一个成员获取。
* - ``fw.bootloader``
     - 运行中
     - 设备上运行的引导加载程序版本。也可以通过 ``ethtool -i`` 作为 ``firmware-version`` 的第二个成员获取。
* - ``board.rev``
     - 固定
     - 设备的硬件版本。
* - ``serial_number``
     - 固定
     - USB 序列号。也可以通过 ``lsusb -v`` 获取。
