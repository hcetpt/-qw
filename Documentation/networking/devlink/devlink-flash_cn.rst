SPDX 许可证标识符: (GPL-2.0-only 或 BSD-2-Clause)

.. _devlink_flash:

=============
Devlink Flash
=============

``devlink-flash`` API 允许更新设备固件。它取代了旧的 ``ethtool-flash`` 机制，并且在执行固件更新时不需要在内核中获取任何网络锁。示例用法如下：

  $ devlink dev flash pci/0000:05:00.0 文件 flash-boot.bin

请注意，文件名是相对于固件加载路径的路径（通常是 `/lib/firmware/`）。驱动程序可以发送状态更新以通知用户空间关于更新操作的进度。

覆盖掩码
==============

``devlink-flash`` 命令允许可选地指定一个掩码，指示设备在更新时如何处理闪存组件的小节。
此掩码指示允许被覆盖的部分集合。

.. list-table:: 覆盖掩码位列表
   :widths: 5 95

   * - 名称
     - 描述
   * - ``DEVLINK_FLASH_OVERWRITE_SETTINGS``
     - 表示设备应该使用提供的映像中的设置覆盖正在更新的组件中的设置。
   * - ``DEVLINK_FLASH_OVERWRITE_IDENTIFIERS``
     - 表示设备应该使用提供的映像中的标识符覆盖正在更新的组件中的标识符。这包括 MAC 地址、序列号和类似的设备标识符。

多个覆盖位可以组合在一起请求。如果没有提供任何位，则预期设备仅更新正在更新的组件中的固件二进制文件。设置和标识符应跨更新保留。设备可能不支持所有组合，对于此类设备，其驱动程序必须拒绝无法忠实实现的任何组合。

固件加载
================

需要固件才能运行的设备通常将固件存储在板载的非易失性内存中，例如闪存。有些设备只在板上存储基本固件，在探测过程中驱动程序从磁盘加载其余部分。
``devlink-info`` 允许用户查询固件信息（已加载的组件和版本）。

在其他情况下，设备可以在板上存储映像，从磁盘加载，或自动从磁盘刷新新映像。可以通过 ``fw_load_policy`` devlink 参数来控制这种行为（:ref:`Documentation/networking/devlink/devlink-params.rst <devlink_params_generic>`）。

磁盘上的固件文件通常存储在 `/lib/firmware/` 中。
固件版本管理
===========================

驱动程序应实现 `devlink-flash` 和 `devlink-info` 功能，这些功能共同提供了实施与供应商无关的自动化固件更新设施的能力。
`devlink-info` 暴露了 `driver` 名称和三个版本组（`fixed`、`running`、`stored`）。
`driver` 属性和 `fixed` 组标识具体的设备设计，例如用于查找适用的固件更新。这就是为什么 `serial_number` 不属于 `fixed` 版本（尽管它是固定的）——`fixed` 版本应该标识设计，而不是单个设备。
`running` 和 `stored` 固件版本标识设备上正在运行的固件以及在重启或设备重置后将被激活的固件。
固件更新代理应能够遵循以下简单算法来更新固件内容，无论设备供应商是谁：

```sh
# 获取唯一的硬件设计标识符
$hw_id = devlink-dev-info['fixed']

# 查找适用于此网卡的固件版本
$want_flash_vers = some-db-backed.lookup($hw_id, 'flash')

# 如果需要，更新固件
if $want_flash_vers != devlink-dev-info['stored']:
    $file = some-db-backed.download($hw_id, 'flash')
    devlink-dev-flash($file)

# 查找预期的整体固件版本
$want_fw_vers = some-db-backed.lookup($hw_id, 'all')

# 如果需要，更新磁盘上的文件
if $want_fw_vers != devlink-dev-info['running']:
    $file = some-db-backed.download($hw_id, 'disk')
    write($file, '/lib/firmware/')

# 尝试设备重置，如果可用的话
if $want_fw_vers != devlink-dev-info['running']:
    devlink-reset()

# 如果重置无效，则重启
if $want_fw_vers != devlink-dev-info['running']:
    reboot()
```

请注意，在这个伪代码中每次引用 `devlink-dev-info` 都期望从内核获取最新信息。
为了方便识别固件文件，一些供应商在固件版本中添加了 `bundle_id` 信息。这种元版本覆盖了多个组件版本，并且可以用于固件文件名（所有组件版本可能会变得相当长）。
