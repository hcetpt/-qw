FPGA 设备特性列表 (DFL) 框架概述
=================================================

作者：

- Enno Luebbers <enno.luebbers@intel.com>
- Xiao Guangrong <guangrong.xiao@linux.intel.com>
- Wu Hao <hao.wu@intel.com>
- Xu Yilun <yilun.xu@intel.com>

设备特性列表 (DFL) FPGA 框架（以及根据该框架编写的驱动程序）隐藏了底层硬件的细节，并为用户空间提供了统一的接口。应用程序可以使用这些接口来配置、枚举、打开和访问实现在设备内存中的DFL平台上的FPGA加速器。此外，DFL框架还支持系统级别的管理功能，如FPGA重新配置。

设备特性列表 (DFL) 概述
==================================
设备特性列表 (DFL) 定义了在设备MMIO空间内的特性头链接列表，以提供一种可扩展的方式来添加特性。软件可以通过遍历这些预定义的数据结构来枚举FPGA特性：FPGA接口单元 (FIU)、加速功能单元 (AFU) 和私有特性，如下图所示：

```
    Header            Header            Header            Header
 +----------+  +-->+----------+  +-->+----------+  +-->+----------+
 |   Type   |  |   |  Type    |  |   |  Type    |  |   |  Type    |
 |   FIU    |  |   | Private  |  |   | Private  |  |   | Private  |
 +----------+  |   | Feature  |  |   | Feature  |  |   | Feature  |
 | Next_DFH |--+   +----------+  |   +----------+  |   +----------+
 +----------+      | Next_DFH |--+   | Next_DFH |--+   | Next_DFH |--> NULL
 |    ID    |      +----------+      +----------+      +----------+
 +----------+      |    ID    |      |    ID    |      |    ID    |
 | Next_AFU |--+   +----------+      +----------+      +----------+
 +----------+  |   | Feature  |      | Feature  |      | Feature  |
 |  Header  |  |   | Register |      | Register |      | Register |
 | Register |  |   |   Set    |      |   Set    |      |   Set    |
 |   Set    |  |   +----------+      +----------+      +----------+
 +----------+  |      Header
               +-->+----------+
                   |   Type   |
                   |   AFU    |
                   +----------+
                   | Next_DFH |--> NULL
                   +----------+
                   |   GUID   |
                   +----------+
                   |  Header  |
                   | Register |
                   |   Set    |
                   +----------+
```

- FPGA接口单元 (FIU) 表示一个独立的功能单元，用于FPGA接口，例如FPGA管理引擎 (FME) 和端口（关于FME和端口的更多描述见后文）
- 加速功能单元 (AFU) 表示一个FPGA可编程区域，并且始终连接到一个FIU（例如一个端口）作为其子节点，如上图所示
- 私有特性表示FIU和AFU的子特性。它们可以是具有不同ID的各种功能块，但属于同一FIU或AFU的所有私有特性必须通过下一个设备特性头 (Next_DFH) 指针链接到一个列表中
- 每个FIU、AFU和私有特性都可以实现自己的功能寄存器
- FIU和AFU的功能寄存器集被称为头寄存器集，例如FME头寄存器集，而私有特性的功能寄存器集则被称为特性寄存器集，例如FME部分重配置特性寄存器集
- 这个设备特性列表提供了一种将特性链接在一起的方式，便于软件通过遍历这个列表来定位每个特性，并且可以在任何FPGA设备的寄存器区域中实现

设备特性头 - 版本0
=================================
版本0 (DFHv0) 是设备特性头的原始版本
DFHv0 中所有多字节的数量都是小端格式
DFHv0 的格式如下所示：

```
    +-----------------------------------------------------------------------+
    |63 Type 60|59 DFH VER 52|51 Rsvd 41|40 EOL|39 Next 16|15 REV 12|11 ID 0| 0x00
    +-----------------------------------------------------------------------+
    |63                                 GUID_L                             0| 0x08
    +-----------------------------------------------------------------------+
    |63                                 GUID_H                             0| 0x10
    +-----------------------------------------------------------------------+
```

- 偏移量 0x00

  * Type - 特性头的类型（例如FME、AFU或私有特性）
* DFH_VER - DFH 的版本
* Rsvd - 当前未使用
* EOL - 如果 DFH 是 Device Feature List (DFL) 的结尾，则设置此标志
* Next - 下一个 DFH 在 DFL 中的偏移量（以字节为单位），从当前 DFH 开始计算，且 DFH 的起始位置必须对齐到 8 字节边界
  如果设置了 EOL 标志，则 Next 表示列表中最后一个功能的 MMIO 大小
* REV - 与此头文件关联的功能的修订版本
* ID - 如果 Type 是私有功能，则表示功能 ID
- 偏移量 0x08

  * GUID_L - 128 位全局唯一标识符的最低有效 64 位（仅当 Type 是 FME 或 AFU 时出现）
- 偏移量 0x10

  * GUID_H - 128 位全局唯一标识符的最高有效 64 位（仅当 Type 是 FME 或 AFU 时出现）

Device Feature Header - 版本 1
=================================
Device Feature Header 的版本 1（DFHv1）增加了以下功能：

* 提供了一种标准化机制，用于描述功能的参数/能力给软件
* 对所有DFHv1类型统一使用GUID
* 将DFH位置与特性本身的寄存器空间解耦
DFHv1中的所有多字节数据量均为小端模式
设备特性头（DFH）版本1的格式如下所示：

    +-----------------------------------------------------------------------+
    |63 Type 60|59 DFH VER 52|51 Rsvd 41|40 EOL|39 Next 16|15 REV 12|11 ID 0| 0x00
    +-----------------------------------------------------------------------+
    |63                                 GUID_L                             0| 0x08
    +-----------------------------------------------------------------------+
    |63                                 GUID_H                             0| 0x10
    +-----------------------------------------------------------------------+
    |63                   Reg Address/Offset                      1|  Rel  0| 0x18
    +-----------------------------------------------------------------------+
    |63        Reg Size       32|Params 31|30 Group    16|15 Instance      0| 0x20
    +-----------------------------------------------------------------------+
    |63 Next    35|34RSV33|EOP32|31 Param Version 16|15 Param ID           0| 0x28
    +-----------------------------------------------------------------------+
    |63                 Parameter Data                                     0| 0x30
    +-----------------------------------------------------------------------+

                                  ..
+-----------------------------------------------------------------------+
    |63 Next    35|34RSV33|EOP32|31 Param Version 16|15 Param ID           0|
    +-----------------------------------------------------------------------+
    |63                 Parameter Data                                     0|
    +-----------------------------------------------------------------------+

- 偏移量 0x00

  * Type - DFH的类型（例如FME、AFU或私有特性）
* DFH VER - DFH的版本
* Rsvd - 当前未使用
* EOL - 如果DFH是设备特性列表（DFL）的末尾，则设置该位
* Next - 下一个DFH在DFL中的偏移量（以字节为单位），从DFH开始，并且DFH的起始位置必须对齐到8字节边界
如果设置了EOL，Next表示列表中最后一个特性的MMIO大小
* REV - 与该标题关联的功能的修订版本
* ID - 如果类型为私有功能，则为功能ID
- 偏移量 0x08

  * GUID_L - 128位全局唯一标识符的最低有效64位
- 偏移量 0x10

  * GUID_H - 128位全局唯一标识符的最高有效64位
- 偏移量 0x18

  * Reg Address/Offset - 如果Rel位被设置，则该值为功能寄存器的16字节对齐绝对地址的高63位。否则，该值是从DFH开始到功能寄存器的偏移量
- 偏移量 0x20

  * Reg Size - 功能寄存器集的大小（以字节为单位）
* Params - 如果DFH包含参数块列表，则设置此字段
* Group - 如果功能是某个组的一部分，则为组ID
* Instance - 在组内的功能实例ID
- 偏移量 0x28（如果功能有参数）

  * Next - 到下一个参数块的偏移量（以8字节为单位）。如果EOP被设置，则表示最后一个参数的大小（以8字节为单位）
* Param Version - 参数版本
* Param ID - 参数ID
- 偏移 0x30

* Parameter Data - 参数数据，其大小和格式由参数的版本和ID定义

FIU - FME（FPGA 管理引擎）
=============================
FPGA 管理引擎执行重新配置和其他基础设施功能。每个 FPGA 设备只有一个 FME。
用户空间应用程序可以通过使用 `open()` 获取对 FME 的独占访问，并通过 `close()` 释放它。

以下函数通过 ioctl 暴露：

- 获取驱动程序 API 版本（DFL_FPGA_GET_API_VERSION）
- 检查扩展（DFL_FPGA_CHECK_EXTENSION）
- 编程比特流（DFL_FPGA_FME_PORT_PR）
- 将端口分配给 PF（DFL_FPGA_FME_PORT_ASSIGN）
- 从 PF 释放端口（DFL_FPGA_FME_PORT_RELEASE）
- 获取 FME 全局错误的中断数量（DFL_FPGA_FME_ERR_GET_IRQ_NUM）
- 设置 FME 错误的中断触发器（DFL_FPGA_FME_ERR_SET_IRQ）

更多函数通过 sysfs 暴露（/sys/class/fpga_region/regionX/dfl-fme.n/）：

- 读取比特流 ID（bitstream_id）
    - bitstream_id 表示静态 FPGA 区域的版本
- 读取比特流元数据（bitstream_metadata）
    - bitstream_metadata 包含静态 FPGA 区域的详细信息，例如综合日期和种子
- 读取端口数量（ports_num）
    - 一个 FPGA 设备可能有多个端口，此 sysfs 接口指示 FPGA 设备有多少个端口
- 全局错误报告管理（errors/）
    - 错误报告 sysfs 接口允许用户读取硬件检测到的错误并清除记录的错误
- 电源管理（dfl_fme_power hwmon）
    - 电源管理 hwmon sysfs 接口允许用户读取电源管理信息（功耗、阈值、阈值状态、限制等），并为不同的节流级别配置电源阈值
热管理 (dfl_fme_thermal hwmon)
热管理 hwmon sysfs 接口允许用户读取热管理信息（当前温度、阈值、阈值状态等）。

性能报告
性能计数器通过 perf PMU API 暴露。标准的 perf 工具可用于监控所有可用的性能事件。更多详细信息，请参见下面的性能计数器部分。

FIU - 端口
端口表示静态 FPGA 布局与包含 AFU 的部分可重构区域之间的接口。它控制从软件到加速器的通信，并提供重置和调试等功能。每个 FPGA 设备可能有多个端口，但每个端口始终只有一个 AFU。

AFU
AFU 附属于一个端口 FIU，并暴露一个固定长度的 MMIO 区域，用于加速器特定的控制寄存器。
用户空间应用程序可以通过对端口设备节点使用 `open()` 来获取对连接到端口的 AFU 的独占访问权，并使用 `close()` 释放该访问权。以下功能通过 ioctl 暴露：

- 获取驱动程序 API 版本 (DFL_FPGA_GET_API_VERSION)
- 检查扩展 (DFL_FPGA_CHECK_EXTENSION)
- 获取端口信息 (DFL_FPGA_PORT_GET_INFO)
- 获取 MMIO 区域信息 (DFL_FPGA_PORT_GET_REGION_INFO)
- 映射 DMA 缓冲区 (DFL_FPGA_PORT_DMA_MAP)
- 取消映射 DMA 缓冲区 (DFL_FPGA_PORT_DMA_UNMAP)
- 重置 AFU (DFL_FPGA_PORT_RESET)
- 获取端口错误中断的数量 (DFL_FPGA_PORT_ERR_GET_IRQ_NUM)
- 设置端口错误中断触发 (DFL_FPGA_PORT_ERR_SET_IRQ)
- 获取 UINT 中断的数量 (DFL_FPGA_PORT_UINT_GET_IRQ_NUM)
- 设置 UINT 中断触发 (DFL_FPGA_PORT_UINT_SET_IRQ)

DFL_FPGA_PORT_RESET：
重置 FPGA 端口及其 AFU。用户空间可以在任何时候执行端口重置，例如在 DMA 或部分重新配置期间。但它不应导致任何系统级别的问题，只应导致功能失败（如 DMA 或 PR 操作失败），并且可以从失败中恢复。
用户空间应用程序还可以使用 `mmap()` 映射加速器的 MMIO 区域。
更多功能通过 sysfs 暴露：
(`/sys/class/fpga_region/<regionX>/<dfl-port.m>/`)：

读取加速器 GUID (afu_id)
`afu_id` 表示编程到此 AFU 的 PR 位流。
错误报告 (errors/)
错误报告 sysfs 接口允许用户读取硬件检测到的端口/AFU 错误，并清除已记录的错误。

DFL 框架概述
```
+----------+    +--------+ +--------+ +--------+
|   FME    |    |  AFU   | |  AFU   | |  AFU   |
|  Module  |    | Module | | Module | | Module |
+----------+    +--------+ +--------+ +--------+
        +-----------------------+
        | FPGA Container Device |    Device Feature List
        |  (FPGA Base Region)   |         Framework
        +-----------------------+
  ------------------------------------------------------------------
        +----------------------------+
        |   FPGA DFL Device Module   |
        | (e.g. PCIE/Platform Device)|
        +----------------------------+
          +------------------------+
          |  FPGA Hardware Device  |
          +------------------------+
```

内核中的 DFL 框架提供了通用接口来创建容器设备（FPGA 基础区域），从给定的设备特征列表中发现特征设备及其私有特征，并为特征设备（例如 FME、端口和 AFU）创建平台设备及其相关资源。它还抽象了私有特征的操作，并向特征设备驱动程序暴露通用操作。
FPGA DFL 设备可以是不同的硬件，例如 PCIe 设备、平台设备等。一旦该设备由系统创建，其驱动模块将首先加载。此驱动在驱动架构中起基础作用。它定位设备内存中的 DFL，并通过 DFL 框架处理它们及其相关资源以提供通用接口（详细枚举 API 请参阅 drivers/fpga/dfl.c）。

FPGA 管理引擎 (FME) 驱动是一个平台驱动，在 DFL 设备模块创建 FME 平台设备后自动加载。它提供了 FPGA 管理的关键功能，包括：

a) 暴露静态 FPGA 区域信息，例如版本和元数据。用户可以通过 FME 驱动暴露的 sysfs 接口读取相关信息。
b) 部分重配置。FME 驱动在初始化 PR 子特性时创建 FPGA 管理器、FPGA 桥接器和 FPGA 区域。一旦收到用户发出的 DFL_FPGA_FME_PORT_PR ioctl 请求，它会调用来自 FPGA 区域的通用接口函数，完成给定端口的 PR 位流的部分重配置。

与 FME 驱动类似，FPGA 加速功能单元 (AFU) 驱动在 AFU 平台设备创建后被探测。此模块的主要功能是为用户空间应用程序提供访问各个加速器的接口，包括端口的基本复位控制、AFU MMIO 区域导出以及 DMA 缓冲区映射服务函数。

在功能平台设备创建后，相应的平台驱动将自动加载以处理不同功能。有关已在此 DFL 框架下实现的功能单元的详细信息，请参阅后续章节。

部分重配置
=============
如上所述，加速器可以通过部分重配置 PR 位流文件来重新配置。PR 位流文件必须为确切的静态 FPGA 区域和目标可重配置区域（端口）生成，否则重配置操作将会失败并可能导致系统不稳定。这种兼容性可以通过比较 PR 位流文件头部记录的兼容性 ID 与目标 FPGA 区域暴露的 compat_id 来检查。此检查通常由用户空间在调用重配置 IOCTL 前完成。

FPGA 虚拟化 - PCIe SRIOV
==========================
本节描述了基于 DFL 的 FPGA 设备的虚拟化支持，以便从运行在虚拟机 (VM) 中的应用程序访问加速器。本节仅描述具有 SRIOV 支持的 PCIe 基础 FPGA 设备。特定 FPGA 设备支持的功能通过设备特征列表 (Device Feature Lists) 暴露，如下图所示：

::

    +-------------------------------+  +-------------+
    |              PF               |  |     VF      |
    +-------------------------------+  +-------------+
        ^            ^         ^              ^
        |            |         |              |
  +-----|------------|---------|--------------|-------+
  |     |            |         |              |       |
  |  +-----+     +-------+ +-------+      +-------+   |
  |  | FME |     | Port0 | | Port1 |      | Port2 |   |
  |  +-----+     +-------+ +-------+      +-------+   |
  |                  ^         ^              ^       |
  |                  |         |              |       |
  |              +-------+ +------+       +-------+   |
  |              |  AFU  | |  AFU |       |  AFU  |   |
  |              +-------+ +------+       +-------+   |
  |                                                   |
  |            DFL based FPGA PCIe Device             |
  +---------------------------------------------------+

FME 总是通过物理功能 (PF) 访问。
端口（及其相关的AFU）默认通过PF访问，但可以通过PCIe SRIOV通过虚拟功能（VF）设备暴露。每个VF只包含一个端口和一个AFU以实现隔离。用户可以将通过PCIe SRIOV接口创建的各个VF（加速器）分配给虚拟机。
下面展示了虚拟化场景下的驱动程序组织结构：

```
+-------++------++------+             |
| FME   || FME  || FME  |             |
| FPGA  || FPGA || FPGA |             |
|Manager||Bridge||Region|             |
+-------++------++------+             |
+-----------------------+  +--------+ |             +--------+
|          FME          |  |  AFU   | |             |  AFU   |
|         Module        |  | Module | |             | Module |
+-----------------------+  +--------+ |             +--------+
          +-----------------------+       |       +-----------------------+
          | FPGA Container Device |       |       | FPGA Container Device |
          |  (FPGA Base Region)   |       |       |  (FPGA Base Region)   |
          +-----------------------+       |       +-----------------------+
            +------------------+          |         +------------------+
            | FPGA PCIE Module |          | Virtual | FPGA PCIE Module |
            +------------------+   Host   | Machine +------------------+
   -------------------------------------- | ------------------------------
             +---------------+            |          +---------------+
             | PCI PF Device |            |          | PCI VF Device |
             +---------------+            |          +---------------+
```

一旦检测到FPGA PCIe PF或VF设备，FPGA PCIe设备驱动程序总是首先加载。它：
- 使用DFL框架中的通用接口完成对FPGA PCIe PF和VF设备的枚举。
- 支持SRIOV。

FME设备驱动程序在这个驱动架构中起管理作用，它提供ioctl来从PF释放端口并将其分配给PF。在从PF释放端口后，就可以安全地通过PCIe SRIOV sysfs接口通过VF暴露该端口。
为了使应用程序能够从虚拟机中访问加速器，需要按照以下步骤将相应的AFU端口分配给VF：

1. 默认情况下，PF拥有所有AFU端口。任何需要重新分配给VF的端口必须先通过DFL_FPGA_FME_PORT_RELEASE ioctl在FME设备上释放。
2. 一旦N个端口从PF释放，用户可以使用以下命令启用SRIOV和VF。每个VF仅拥有一个带有AFU的端口。

```shell
echo N > $PCI_DEVICE_PATH/sriov_numvfs
```

3. 将VF传递给VM。
4. VF下的AFU可以从VM中的应用程序访问（使用VF内的相同驱动程序）。

请注意，FME不能分配给VF，因此PR和其他管理功能只能通过PF访问。
设备枚举
========
本节介绍了应用程序如何从/sys/class/fpga_region下的sysfs层次结构中枚举FPGA设备。
在下面的例子中，主机安装了两个基于DFL的FPGA设备。每个FPGA设备有一个FME和两个端口（AFU）。
FPGA区域在`/sys/class/fpga_region/`下创建：

```
/sys/class/fpga_region/region0
/sys/class/fpga_region/region1
/sys/class/fpga_region/region2
...
```

应用程序需要搜索每个`regionX`文件夹，如果找到特性设备（例如“dfl-port.n”或“dfl-fme.m”），则表示这是代表FPGA设备的基本FPGA区域。每个基本区域都有一个FME和两个端口（AFU）作为子设备：

```
/sys/class/fpga_region/region0/dfl-fme.0
/sys/class/fpga_region/region0/dfl-port.0
/sys/class/fpga_region/region0/dfl-port.1
...
/sys/class/fpga_region/region3/dfl-fme.1
/sys/class/fpga_region/region3/dfl-port.2
/sys/class/fpga_region/region3/dfl-port.3
...
```

通常情况下，FME/AFU的sysfs接口命名如下：

```
/sys/class/fpga_region/<regionX>/<dfl-fme.n>/
/sys/class/fpga_region/<regionX>/<dfl-port.m>/
```

其中'n'连续编号所有FME，'m'连续编号所有端口。

用于ioctl()或mmap()的设备节点可以通过以下路径引用：

```
/sys/class/fpga_region/<regionX>/<dfl-fme.n>/dev
/sys/class/fpga_region/<regionX>/<dfl-port.n>/dev
```

性能计数器
===========
性能报告是FME中实现的一个私有特性。它可以支持多个独立的、系统范围内的硬件性能计数器集来监控和统计性能事件，包括“basic”、“cache”、“fabric”、“vtd”和“vtd_sip”计数器。用户可以使用标准的perf工具来监控FPGA缓存命中率、事务数量、AFU的接口时钟计数和其他FPGA性能事件。
不同的FPGA设备可能有不同的计数器集，这取决于硬件实现。例如，一些独立的FPGA卡没有缓存。用户可以使用“perf list”来检查目标硬件支持哪些性能事件。
为了允许用户使用标准的perf API访问这些性能计数器，驱动程序创建了一个perf PMU，并在`/sys/bus/event_source/devices/dfl_fme*`中创建了相关的sysfs接口来描述可用的性能事件和配置选项。
“format”目录描述了struct perf_event_attr的config字段格式。config字段包含3个位字段：“evtype”定义了性能事件所属的类型；“event”是该类别中的事件标识；“portid”被引入以决定是在整体数据上还是特定端口上进行计数。
“events”目录描述了所有可用事件的配置模板，这些事件可以直接与perf工具一起使用。例如，fab_mmio_read的配置为“event=0x06,evtype=0x02,portid=0xff”，这表明该事件属于fabric类型（0x02），本地事件ID为0x06，并且用于整体监控（portid=0xff）。
### `perf` 示例用法：

```
$# perf list | grep dfl_fme

dfl_fme0/fab_mmio_read/                              [Kernel PMU 事件]
<...>
dfl_fme0/fab_port_mmio_read,portid=?/                [Kernel PMU 事件]
<...>

$# perf stat -a -e dfl_fme0/fab_mmio_read/ <command>
或
$# perf stat -a -e dfl_fme0/event=0x06,evtype=0x02,portid=0xff/ <command>
或
$# perf stat -a -e dfl_fme0/config=0xff2006/ <command>
```

另一个示例，`fab_port_mmio_read` 监控特定端口的 MMIO 读取。因此其配置模板是 "event=0x06,evtype=0x01,portid=?"。`portid` 应该明确设置。
其 `perf` 使用方法如下：

```
$# perf stat -a -e dfl_fme0/fab_port_mmio_read,portid=0x0/ <command>
或
$# perf stat -a -e dfl_fme0/event=0x06,evtype=0x02,portid=0x0/ <command>
或
$# perf stat -a -e dfl_fme0/config=0x2006/ <command>
```

请注意对于 Fabric 计数器，整体 `perf` 事件（`fab_*`）和端口 `perf` 事件（`fab_port_*`）实际上在硬件中共享一组计数器，因此不能同时监控两者。如果这组计数器被配置为监控整体数据，则不支持每个端口的 `perf` 数据。请参见以下示例：

```
$# perf stat -e dfl_fme0/fab_mmio_read/,dfl_fme0/fab_port_mmio_write,portid=0/ sleep 1

Performance counter stats for 'system wide':

                 3      dfl_fme0/fab_mmio_read/
   <不支持>      dfl_fme0/fab_port_mmio_write,portid=0x0/

       1.001750904 seconds time elapsed
```

驱动程序还提供了一个 `cpumask` 的 sysfs 属性，其中包含唯一一个用于访问这些 `perf` 事件的 CPU ID。由于它们是 FPGA 设备上的系统级计数器，因此不允许在多个 CPU 上计数。
当前驱动程序不支持采样。因此 `perf record` 不受支持。

### 中断支持
一些 FME 和 AFU 私有特性能够生成中断。如上所述，用户可以通过调用 ioctl (`DFL_FPGA_*_GET_IRQ_NUM`) 来了解这些私有特性支持多少个中断。驱动程序还实现了一个基于 eventfd 的中断处理机制，以便在中断发生时通知用户。用户可以通过 ioctl (`DFL_FPGA_*_SET_IRQ`) 将 eventfd 设置到驱动程序，并通过轮询或选择这些 eventfd 等待通知。
在当前的 DFL 中，三个子特性（端口错误、FME 全局错误和 AFU 中断）支持中断。

### 添加新的 FIU 支持
在 DFL 框架下，开发人员可能会创建一些新的功能块（FIU）。此时需要为新功能设备（FIU）开发一个新的平台设备驱动程序，类似于现有的功能设备驱动程序（例如 FME 和端口/AFU 平台设备驱动程序）。除此之外，还需要修改 DFL 框架中的枚举代码，以检测新的 FIU 类型并创建相关的平台设备。
参考文件：`drivers/fpga/dfl-fme-pr.c`（FME 部分重构子特性驱动程序）。

### 添加新的私有特性支持
在某些情况下，我们可能需要向现有的 FIU（例如 FME 或端口）添加一些新的私有特性。开发人员不需要修改 DFL 框架中的枚举代码，因为每个私有特性都会自动解析，并且相关的 MMIO 资源可以在由 DFL 框架创建的 FIU 平台设备下找到。
开发人员只需要提供一个与特性 ID 匹配的子特性驱动程序。
现有特性 ID 表及申请新特性 ID 的指南，请参见以下链接。
### PCI 设备上的 DFL 位置

找到 PCI 设备上 DFL 的原始方法假设第一个 DFL 从 BAR 0 的偏移量 0 开始。如果 DFL 的第一个节点是 FME，则端口中的其他 DFL 将在 FME 头部寄存器中指定。或者，可以使用 PCIe 厂商特定功能结构来指定设备上所有 DFL 的位置，从而为 DFL 中的起始节点类型提供灵活性。英特尔为此目的保留了 VSEC ID 0x43。厂商特定数据以一个 4 字节的厂商特定寄存器开始，用于存储 DFL 的数量，随后每个 DFL 都有一个 4 字节的 Offset/BIR 厂商特定寄存器。Offset/BIR 寄存器的低 3 位指示 BAR，高 29 位表示 8 字节对齐的偏移量，其中低 3 位为零：
```
+----------------------------+
|31     Number of DFLS      0|
+----------------------------+
|31     Offset     3|2 BIR  0|
+----------------------------+
                      . .
+----------------------------+
|31     Offset     3|2 BIR  0|
+----------------------------+
```

考虑过在每个 BAR 中指定多个 DFL，但最终确定该用例没有实际价值。每个 BAR 指定一个 DFL 可简化实现并允许进行额外的错误检查。

### 用户空间驱动程序支持 DFL 设备

FPGA 的目的是被重新编程以包含新开发的硬件组件。新的硬件可以在 DFL 中实例化一个新的私有特性，并在系统中呈现一个 DFL 设备。在某些情况下，用户可能需要一个用户空间驱动程序来支持 DFL 设备：

- 用户可能需要为他们的硬件运行一些诊断测试。
- 用户可能需要在用户空间中原型化内核驱动程序。
- 有些硬件设计用于特定用途，并不适合标准内核子系统之一。
这需要直接访问 MMIO 空间和用户空间中的中断处理。uio_dfl 模块为此提供了 UIO 设备接口。

目前，uio_dfl 驱动程序仅支持没有硬件中断的 Ether Group 子特性。因此，此驱动程序中未添加中断处理。应选择 UIO_DFL 以启用 uio_dfl 模块。为了通过 UIO 直接访问支持新的 DFL 特性，应将其特征 ID 添加到驱动程序的 id_table 中。
开放式讨论
===============
FME驱动程序现在为部分重新配置导出了一个ioctl（DFL_FPGA_FME_PORT_PR）。将来，如果添加了统一的重新配置用户界面，FME驱动程序应该从ioctl接口切换到这些新界面。
