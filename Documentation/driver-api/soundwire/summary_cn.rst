===========================
SoundWire 子系统概览
===========================

SoundWire 是一个由 MIPI 联盟在 2015 年批准的新接口。
SoundWire 用于传输与音频功能相关的数据。
SoundWire 接口针对移动设备或受移动设备启发的系统中的音频设备集成进行了优化。
SoundWire 是一个双线多点接口，包含数据线和时钟线。它有助于开发低成本、高效、高性能的系统。
SoundWire 接口的主要特点包括：

(1) 通过单一的双线接口传输所有有效负载数据通道、控制信息和设置命令；
(2) 通过使用 DDR（双倍数据速率）数据传输降低时钟频率，从而降低功耗；
(3) 提供时钟缩放及可选的多个数据通道以灵活匹配系统要求的数据率；
(4) 包括中断式警报在内的设备状态监控；

SoundWire 协议支持多达十一个从属接口。所有接口共享包含数据线和时钟线的通用总线。每个从属接口最多可以支持 14 个数据端口。其中 13 个数据端口专门用于音频传输。数据端口 0 专门用于传输批量控制信息。每个音频数据端口（1 至 14）可以在发送或接收模式下支持最多 8 个通道（通常为固定方向，但规范允许配置方向）。然而，带宽限制约为 19.2 到 24.576 Mbps，并不允许同时传输 11 * 13 * 8 个通道。

下面的图示显示了一个 SoundWire 主接口与两个从属设备之间连接的一个例子。:: 

        +---------------+                                       +---------------+
        |               |                       时钟信号        |               |
        |    主接口     |-------+-------------------------------|    从属接口   |
        |   接口        |       |               数据信号         |  1            |
        |               |-------|-------+-----------------------|               |
        +---------------+       |       |                       +---------------+
                                |       |
                                |       |
                                |       |
                             +--+-------+--+
                             |             |
                             |   从属      |
                             | 接口 2      |
                             |             |
                             +-------------+

术语
=====

MIPI SoundWire 规范中使用“设备”一词来指代主接口或从属接口，这可能会引起混淆。在这个概览和代码中，我们只用“接口”这个词来指硬件。我们遵循 Linux 设备模型，将总线上连接的每个从属接口映射为一个由特定驱动程序管理的设备。Linux SoundWire 子系统提供了一个框架来实现 SoundWire 从属驱动程序，该框架通过 API 允许第三方供应商启用实现定义的功能，而常见的设置/配置任务则由总线处理。
总线：
实现了 SoundWire Linux 总线，负责处理 SoundWire 协议。
程序设定所有 MIPI 定义的从属寄存器。代表一个 SoundWire 主设备。系统中可能存在多个总线实例。

从属设备(Slave):
作为 SoundWire 从属设备（Linux 设备）注册的寄存器。多个从属设备可以向一个总线实例注册。
从属驱动(Slave driver):
控制从属设备的驱动。MIPI 规定的寄存器直接由总线（并通过主驱动/接口传输）控制；任何实现定义的从属寄存器则由从属驱动控制。实际上，预计从属驱动会依赖于 `regmap` 并且不会请求直接访问寄存器。

编程接口（SoundWire 主设备接口驱动）
=====================================

SoundWire 总线支持针对 SoundWire 主设备实现和 SoundWire 从属设备的编程接口。所有的代码使用了 SoC 设计者和第三方供应商普遍采用的 "sdw" 前缀。
每个 SoundWire 主设备接口都需要向总线注册。总线实现了 API 来读取标准主设备 MIPI 属性，并在主操作中提供了回调以供主驱动实现其自身的功能，提供能力信息。当前并未实现设备树(Device Tree, DT)支持，但由于能力是通过 `device_property_` API 启用的，因此添加 DT 支持应当非常简单。
主设备接口及其能力基于板级文件、DT 或 ACPI 进行注册。
下面是用于注册 SoundWire 总线的总线 API：

```c
int sdw_bus_master_add(struct sdw_bus *bus,
                       struct device *parent,
                       struct fwnode_handle *fwnode)
{
    sdw_master_device_add(bus, parent, fwnode);

    mutex_init(&bus->lock);
    INIT_LIST_HEAD(&bus->slaves);

    /* 检查 ACPI 寻找从属设备 */
    sdw_acpi_find_slaves(bus);

    /* 检查 DT 寻找从属设备 */
    sdw_of_find_slaves(bus);

    return 0;
}
```

这将为主设备初始化 sdw_bus 对象。“sdw_master_ops” 和 “sdw_master_port_ops” 回调函数被提供给总线，“sdw_master_ops” 被总线用来以硬件特定的方式控制总线。它包括诸如在总线上发送 SoundWire 读/写消息、设置时钟频率及流同步点(SSP)等总线控制功能。“sdw_master_ops” 结构抽象了主设备与总线之间的硬件细节。
"sdw_master_port_ops"被总线用于设置主接口端口的参数。主接口端口寄存器映射不由MIPI规范定义，因此总线调用"sdw_master_port_ops"回调函数来执行诸如“端口准备”、“端口传输参数设置”、“端口启用和禁用”等操作。主驱动程序的实现可以执行特定于硬件的配置。

编程接口（SoundWire 从设备驱动）
==================================

MIPI规范要求每个从接口暴露一个唯一的48位标识符，该标识符存储在6个只读dev_id寄存器中。此dev_id标识符包含供应商和部件信息以及一个字段以区分相同的组件。目前，一个额外的类字段未使用。从设备驱动是为特定的供应商和部件标识编写的，总线根据这两个标识来枚举从设备。从设备与驱动之间的匹配基于这两个标识。当设备与驱动标识匹配成功时，总线会调用从驱动的probe函数。主设备和从设备之间强制执行父/子关系（逻辑表示与物理连接性一致）。
关于主/从依赖性的信息存储在平台数据、板文件、ACPI或设备树中。MIPI软件规范为具有多个主接口的控制器定义了额外的link_id参数。dev_id寄存器仅在一个链接范围内唯一，并且link_id在一个控制器范围内唯一。dev_id和link_id不一定在整个系统级别唯一，但通过父/子信息避免了歧义。

.. code-block:: c

    static const struct sdw_device_id slave_id[] = {
            SDW_SLAVE_ENTRY(0x025d, 0x700, 0),
            {},
    };
    MODULE_DEVICE_TABLE(sdw, slave_id);

    static struct sdw_driver slave_sdw_driver = {
            .driver = {
                       .name = "slave_xxx",
                       .pm = &slave_runtime_pm,
                       },
            .probe = slave_sdw_probe,
            .remove = slave_sdw_remove,
            .ops = &slave_slave_ops,
            .id_table = slave_id,
    };

对于功能，总线实现了API来读取标准的MIPI从属性，并且还在从操作中提供了回调函数供从驱动程序实现自己的函数以提供功能信息。总线需要知道一组从功能以编程从寄存器并控制总线的重新配置。

未来增强功能
=============

(1) 大批量寄存器访问（BRA）传输
(2) 支持多数据通道

链接
====

SoundWire MIPI规范1.1可在以下位置获取：
https://members.mipi.org/wg/All-Members/document/70290

SoundWire MIPI DisCo（发现和配置）规范可在此处获取：
https://www.mipi.org/specifications/mipi-disco-soundwire

（公开访问需注册或直接对MIPI成员开放）

MIPI联盟制造商ID页面：mid.mipi.org
