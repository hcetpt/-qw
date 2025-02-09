SPDX 许可声明标识符：GPL-2.0+

========================================================
AMD/Pensando® DSC 适配器家族的 Linux 驱动程序
========================================================

版权所有 (C) 2023 Advanced Micro Devices, Inc.

识别适配器
=======================

要检查一个或多个 AMD/Pensando PCI 核心设备是否已安装在主机上，可以查看 PCI 设备列表：

```shell
# lspci -d 1dd8:100c
b5:00.0 处理加速器: Pensando Systems 设备 100c
b6:00.0 处理加速器: Pensando Systems 设备 100c
```

如果列出了上述设备，则 pds_core.ko 驱动程序应该能够找到并配置这些设备以供使用。内核消息中应有类似以下的日志条目：

```shell
$ dmesg | grep pds_core
pds_core 0000:b5:00.0: 可用的 PCIe 带宽为 252.048 Gb/s（16.0 GT/s 的 PCIe x16 链路）
pds_core 0000:b5:00.0: 固件: 1.60.0-73
pds_core 0000:b6:00.0: 可用的 PCIe 带宽为 252.048 Gb/s（16.0 GT/s 的 PCIe x16 链路）
pds_core 0000:b6:00.0: 固件: 1.60.0-73
```

可以通过 `devlink` 收集驱动程序和固件版本信息：

```shell
$ devlink dev info pci/0000:b5:00.0
pci/0000:b5:00.0:
  驱动程序 pds_core
  序列号 FLM18420073
  版本：
      固定：
        asic.id 0x0
        asic.rev 0x0
      运行中：
        固件 1.51.0-73
      存储：
        固件.goldfw 1.15.9-C-22
        固件.mainfwa 1.60.0-73
        固件.mainfwb 1.60.0-57
```

版本信息
=============

`pds_core` 驱动程序报告了以下版本信息：

.. list-table:: 实现的 devlink 信息版本
   :widths: 5 5 90

   * - 名称
     - 类型
     - 描述
   * - ``fw``
     - 运行中
     - 设备上正在运行的固件版本
   * - ``fw.goldfw``
     - 存储
     - goldfw 槽位中存储的固件版本
   * - ``fw.mainfwa``
     - 存储
     - mainfwa 槽位中存储的固件版本
   * - ``fw.mainfwb``
     - 存储
     - mainfwb 槽位中存储的固件版本
   * - ``asic.id``
     - 固定
     - 此设备的 ASIC 类型
   * - ``asic.rev``
     - 固定
     - 此设备的 ASIC 修订版本

参数
==========

`pds_core` 驱动程序实现了以下通用参数来控制通过辅助总线设备提供的功能：

.. list-table:: 实现的通用参数
   :widths: 5 5 8 82

   * - 名称
     - 模式
     - 类型
     - 描述
   * - ``enable_vnet``
     - 运行时
     - 布尔值
     - 通过辅助总线设备启用 vDPA 功能

固件管理
===================

`flash` 命令可以更新 DSC 固件。下载的固件将被保存到固件库 1 或库 2 中的一个（取决于当前哪个未在使用），并且在下次启动时将使用该库中的固件：

```shell
# devlink dev flash pci/0000:b5:00.0 \
            file pensando/dsc_fw_1.63.0-22.tar
```

健康报告
=================

驱动程序支持用于固件状态的 devlink 健康报告：

```shell
# devlink health show pci/0000:2b:00.0 reporter fw
pci/0000:2b:00.0:
  报告者 fw
    状态 健康 错误 0 恢复 0
# devlink health diagnose pci/0000:2b:00.0 reporter fw
状态: 健康 状态: 1 代: 0 恢复次数: 0
```

启用驱动程序
===================

驱动程序是通过标准的内核配置系统启用的，使用 make 命令：

```shell
make oldconfig/menuconfig/etc
```
驱动程序位于菜单结构的以下位置：

  -> 设备驱动程序
    -> 网络设备支持 (NETDEVICES [=y])
      -> 以太网驱动程序支持
        -> AMD 设备
          -> AMD/Pensando 以太网 PDS_CORE 支持

支持
=======

对于一般 Linux 网络支持，请使用 netdev 邮件列表，该列表由 AMD/Pensando 工作人员监控：

  netdev@vger.kernel.org
