SPDX 许可证标识符: (GPL-2.0-only 或 BSD-2-Clause)

============
Devlink 信息
============

``devlink-info`` 机制使设备驱动程序能够以一种标准且可扩展的方式报告设备（硬件和固件）信息。最初开发 ``devlink-info`` API 的动机有两个：

- 使得在一大群机器中以厂商无关的方式自动化管理和更新设备及固件成为可能（参见 :ref:`Documentation/networking/devlink/devlink-flash.rst <devlink_flash>`）；
- 命名各个组件的固件版本（与拥挤的 ethtool 版本字符串相比）

``devlink-info`` 支持报告多种类型的对象。通常不鼓励报告驱动程序版本——无论是通过此接口还是任何其他 Linux API。

.. list-table:: 顶级信息对象列表
   :widths: 5 95

   * - 名称
     - 描述
   * - ``driver``
     - 当前使用的设备驱动程序名称，也可以通过 sysfs 获取
   * - ``serial_number``
     - 设备的序列号

这通常是 ASIC 的序列号，并且经常可以在设备的 PCI 配置空间中的 *Device Serial Number* 能力中找到。
序列号应当对每个物理设备都是唯一的。
有时设备的序列号只有 48 位长（即以太网 MAC 地址的长度），而 PCI DSN 是 64 位长的，因此设备会在序列号中填充或编码额外的信息。
一个例子是在额外的两个字节中添加端口 ID 或 PCI 接口 ID。
驱动程序应确保去除或标准化任何此类填充或接口 ID，并只报告唯一识别硬件的部分序列号。换句话说，在同一设备的两个端口之间或在同一多主机设备的两个主机之间报告的序列号应该是相同的。
* - ``board.serial_number``
     - 设备的主板序列号
这通常是主板的序列号，通常可以在 PCI *Vital Product Data* 中找到。
* - ``fixed``
     - 用于硬件标识符和不可现场更新的组件版本的分组
本节中的版本标识设备的设计。例如，组件标识符或 PCI VPD 中报告的主板版本。
在 ``devlink-info`` 中的数据应分解为最小的逻辑组件，例如 PCI VPD 可能会将各种信息拼接成 Part Number 字符串，而在 ``devlink-info`` 中所有部分都应作为单独项报告。
此分组中不得包含任何频繁更改的标识符，例如序列号。请参阅
:ref:`Documentation/networking/devlink/devlink-flash.rst <devlink_flash>`
以了解原因。
* - ``running``
     - 用于当前运行的软件/固件信息的分组
这些版本通常仅在重启后才会更新，有时需要设备重置。
* - ``stored``
     - 用于设备闪存中的软件/固件版本的分组
存储的值必须更新以反映闪存中的变化，即使尚未发生重启。如果设备无法在新软件刷入时更新 ``stored`` 版本，则不应报告它们。
每个版本组中的每个版本最多只能报告一次。存储在闪存中的固件组件如果设备能够报告“已存储”版本（参见 :ref:`Documentation/networking/devlink/devlink-flash.rst <devlink_flash>`），则应在“运行中”和“已存储”部分中列出。如果软件/固件组件是从磁盘加载的（例如 `/lib/firmware`），则仅应通过内核API报告运行中的版本。

通用版本
========

期望驱动程序使用以下通用名称导出版本信息。如果某个组件尚未存在通用名称，驱动程序作者应参考现有的驱动程序特定版本并尝试重用。作为最后手段，如果组件确实独特，则允许使用驱动程序特定的名称，但这些名称应在驱动程序特定文件中进行记录。

所有版本都应尽量使用以下术语：

.. list-table:: 常见版本后缀列表
   :widths: 10 90

   * - 名称
     - 描述
   * - ``id``, ``revision``
     - 设计和修订的标识符，主要用于硬件版本
   * - ``api``
     - 组件之间的API版本。API项通常对用户价值有限，并且供应商可以从其他版本推断出来，因此添加API版本一般不鼓励，因为它会增加噪音
   * - ``bundle_id``
     - 被烧录到设备上的分发包的标识符。这是固件包的一个属性，它涵盖了多个版本，以便于管理固件映像（参见 :ref:`Documentation/networking/devlink/devlink-flash.rst <devlink_flash>`）。``bundle_id`` 可以出现在“运行中”和“已存储”版本中，但如果包含在 ``bundle_id`` 中的任何组件被更改且不再匹配包中的版本，则不应报告 ``bundle_id``

board.id
--------

板卡设计的唯一标识符
```plaintext
board.rev
---------
板卡设计修订

asic.id
-------
ASIC 设计标识符

asic.rev
--------
ASIC 设计修订/步进

board.manufacture
-----------------
生产该部件的公司或设施标识

board.part_number
-----------------
板卡及其组件的零件号

fw
--
整体固件版本，通常代表了 fw.mgmt、fw.app 等集合

fw.mgmt
-------
控制单元固件版本。此固件负责维护任务、PHY 控制等，但不涉及逐包数据路径操作

fw.mgmt.api
-----------
驱动程序与固件之间软件接口规范的版本

fw.app
------
高速数据包处理的数据路径微码

fw.undi
-------
UNDI 软件，可能包括 UEFI 驱动程序、固件或两者
```
---

负责支持/处理网络控制器侧带接口（Network Controller Sideband Interface）的软件版本

fw.psid
---

固件参数集的唯一标识符。这些通常是制造时定义的特定板卡的参数

fw.roce
---

负责处理 RoCE 管理的 RoCE 固件版本

fw.bundle_id
---

整个固件包的唯一标识符

fw.bootloader
---

引导加载程序的版本

未来工作
===

以下扩展可能会有用：

- 磁盘上的固件文件名 - 驱动程序通过 `MODULE_FIRMWARE()` 宏列出它们可能需要加载到设备上的固件文件名。然而，这些是按模块而不是按设备来指定的。列出驱动程序将尝试为给定设备加载的固件文件名（按优先级顺序）会很有用。
