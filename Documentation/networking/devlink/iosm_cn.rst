SPDX 许可证标识符: GPL-2.0

====================
iosm devlink 支持
====================

本文档描述了由 ``iosm`` 设备驱动程序实现的 devlink 功能。
参数
======

``iosm`` 驱动程序实现了以下特定于驱动程序的参数：

.. list-table:: 实现的驱动程序特定参数
   :widths: 5 5 5 85

   * - 名称
     - 类型
     - 模式
     - 描述
   * - ``erase_full_flash``
     - u8
     - 运行时
     - ``erase_full_flash`` 参数用于检查在固件刷新过程中是否需要对设备进行全擦除
如果设置，将向设备发送完整的 NAND 擦除命令。默认情况下，仅启用条件擦除支持

闪存更新
============

``iosm`` 驱动程序通过 ``devlink-flash`` 接口实现了闪存更新的支持。
它支持使用包含引导加载程序图像和其他调制解调器软件图像的组合闪存图像来更新设备闪存。
该驱动程序使用 `DEVLINK_SUPPORT_FLASH_UPDATE_COMPONENT` 来识别用户空间应用程序请求的需要刷新的固件图像类型。

支持的固件图像类型
.. list-table:: 固件图像类型
    :widths: 15 85

    * - 名称
      - 描述
    * - ``PSI RAM``
      - 主签名图像
    * - ``EBL``
      - 外部引导加载程序
    * - ``FLS``
      - 调制解调器软件图像

PSI RAM 和 EBL 是 RAM 图像，在设备处于引导 ROM 阶段时注入到设备中。一旦成功，实际的调制解调器固件图像将被刷新到设备中。调制解调器软件图像包含多个文件，每个文件都有一个安全二进制文件和至少一个载入图/区域文件。为了刷新这些文件，会向调制解调器设备发送适当的命令以及刷新所需的其他数据。例如，区域数量和每个区域的地址等信息需要通过 `devlink param` 命令传递给驱动程序。

如果在固件刷新之前需要对设备进行全擦除，用户应用程序需要使用 `devlink param` 命令设置 ``erase_full_flash`` 参数。
默认情况下，支持有条件擦除功能
Flash 命令：
==============
1) 当调制解调器处于 Boot ROM 阶段时，用户可以使用以下命令通过 devlink flash 命令注入 PSI RAM 映像
$ devlink dev flash pci/0000:02:00.0 file <PSI_RAM_File_name>

2) 如果用户需要执行全盘擦除，则需要发出以下命令来设置全盘擦除参数（仅在需要全盘擦除时设置）
$ devlink dev param set pci/0000:02:00.0 name erase_full_flash value true cmode runtime

3) 在调制解调器进入 PSI 阶段后注入 EBL
$ devlink dev flash pci/0000:02:00.0 file <EBL_File_name>

4) 一旦 EBL 注入成功，实际的固件刷新将开始。以下是用于每个固件映像的命令序列
a) 刷新安全二进制文件
$ devlink dev flash pci/0000:02:00.0 file <Secure_bin_file_name>

b) 刷新 Loadmap/Region 文件
$ devlink dev flash pci/0000:02:00.0 file <Load_map_file_name>

区域：
======

``iosm`` 驱动程序支持转储 core dump 日志
如果固件遇到异常，驱动程序将拍摄快照。以下区域用于访问设备内部数据
.. list-table:: 实现的区域
    :widths: 15 85

    * - 名称
      - 描述
    * - ``report.json``
      - 作为此区域的一部分记录的异常详细信息摘要
    * - ``coredump.fcd``
      - 此区域包含与设备中发生的异常相关的详细信息（RAM 转储）
* - ``cdd.log``
      - 该区域包含与调制解调器 CDD 驱动相关的日志
* - ``eeprom.bin``
      - 该区域包含 EEPROM 日志
* - ``bootcore_trace.bin``
      - 该区域包含当前引导加载程序的日志实例
* - ``bootcore_prev_trace.bin``
      - 该区域包含前一个引导加载程序的日志实例

区域命令
===============

$ devlink region show

$ devlink region new pci/0000:02:00.0/report.json

$ devlink region dump pci/0000:02:00.0/report.json snapshot 0

$ devlink region del pci/0000:02:00.0/report.json snapshot 0

$ devlink region new pci/0000:02:00.0/coredump.fcd

$ devlink region dump pci/0000:02:00.0/coredump.fcd snapshot 1

$ devlink region del pci/0000:02:00.0/coredump.fcd snapshot 1

$ devlink region new pci/0000:02:00.0/cdd.log

$ devlink region dump pci/0000:02:00.0/cdd.log snapshot 2

$ devlink region del pci/0000:02:00.0/cdd.log snapshot 2

$ devlink region new pci/0000:02:00.0/eeprom.bin

$ devlink region dump pci/0000:02:00.0/eeprom.bin snapshot 3

$ devlink region del pci/0000:02:00.0/eeprom.bin snapshot 3

$ devlink region new pci/0000:02:00.0/bootcore_trace.bin

$ devlink region dump pci/0000:02:00.0/bootcore_trace.bin snapshot 4

$ devlink region del pci/0000:02:00.0/bootcore_trace.bin snapshot 4

$ devlink region new pci/0000:02:00.0/bootcore_prev_trace.bin

$ devlink region dump pci/0000:02:00.0/bootcore_prev_trace.bin snapshot 5

$ devlink region del pci/0000:02:00.0/bootcore_prev_trace.bin snapshot 5
