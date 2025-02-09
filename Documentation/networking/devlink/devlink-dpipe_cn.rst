### SPDX 许可证标识符：GPL-2.0

#### Devlink DPIPE

##### 背景

在执行硬件卸载过程中，许多硬件特性的细节无法直接展现。这些细节对于调试非常有用，而`devlink-dpipe`提供了一种标准化的方式来洞察卸载过程。例如，Linux 内核中使用的路由最长前缀匹配（LPM）算法可能与硬件实现不同。管道调试API（DPIPE）旨在以一种通用的方式为用户提供对ASIC管道的可见性。

硬件卸载过程期望以用户无法区分硬件和软件实现的方式进行。在这个过程中，忽视了硬件的具体特性。实际上，这些细节具有重要意义，并且应该以某种标准方式暴露出来。

当希望将整个网络栈的控制路径卸载到交换ASIC时，这个问题变得更加复杂。由于硬件和软件模型之间的差异，某些过程无法正确表示。

一个例子是内核中的LPM算法，在很多情况下与硬件实现大相径庭。配置API是相同的，但不能依赖转发信息库（FIB）看起来像硬件中的级别路径压缩trie（LPC-trie）。

在很多情况下，仅根据内核的转储来分析系统故障可能不够。通过将这些数据与底层硬件的相关信息相结合，可以使调试变得更容易；此外，这些信息在调试性能问题时也很有用。

##### 概览

`devlink-dpipe`接口弥补了这一差距。硬件的管道被建模为匹配/动作表的图。每个表代表特定的硬件块。这种模型并非新事物，最初由P4语言使用。

传统上，它作为一种替代模型用于硬件配置，但`devlink-dpipe`接口将其作为标准化的辅助工具用于可见性目的。从`devlink-dpipe`看到的系统的视图应该随着标准配置工具所做的更改而变化。

例如，使用三态内容可寻址内存（TCAM）实现访问控制列表（ACL）是很常见的做法。TCAM内存可以分为TCAM区域。复杂的TC过滤器可以包含多个具有不同优先级和不同查找键的规则。另一方面，硬件TCAM区域具有预定义的查找键。使用TCAM引擎卸载TC过滤器规则可能导致多个TCAM区域以链的形式相互连接（这可能影响数据路径延迟）。响应新的TC过滤器，应创建新的表来描述那些区域。

##### 模型

DPIPE模型引入了几个对象：

* 头部
* 表
* 条目

“头部”描述包格式并为包内的字段提供名称。“表”描述硬件块。“条目”描述特定表的实际内容。
硬件管道并非针对特定端口，而是描述整个ASIC。因此，它与"devlink"基础设施的顶层相关联。
驱动程序可以在运行时注册和注销表，以支持动态行为。这种动态行为对于描述像TCAM区域这样的硬件模块是必须的，这些模块可以被动态分配和释放。
通常来说，"devlink-dpipe"并不用于配置目的。唯一的例外是在特定表上进行的硬件计数。
以下命令用于从用户空间获取"dpipe"对象：

  * `table_get`：接收一个表的描述
* `headers_get`：接收设备所支持的头部信息
* `entries_get`：接收表中的当前条目
* `counters_set`：启用或禁用表上的计数器
表
-----

对于每个表，驱动程序应实现以下操作：

  * `matches_dump`：输出支持的匹配项
* `actions_dump`：输出支持的动作
* `entries_dump`：输出表的实际内容
* ``counters_set_update``: 同步硬件中的计数器启用或禁用状态
Header/Field
------------

与 P4 中的报头和字段类似，用于描述表的行为。协议报头与特定 ASIC 元数据之间存在细微差别。协议报头应在 ``devlink`` 核心 API 中声明。另一方面，ASIC 元数据是驱动程序特有的，应在驱动程序中定义。此外，每个特定于驱动程序的 devlink 文档文件应记录该驱动程序实现的特定于驱动程序的 ``dpipe`` 报头。通过枚举来识别报头和字段。为了提供进一步的可见性，一些 ASIC 元数据字段可以映射到内核对象上。例如，内部路由器接口索引可以直接映射到网络设备的 ifindex。不同虚拟路由转发（VRF）表使用的 FIB 表索引可以映射到内部路由表索引。
Match
-----

匹配项保持原始并接近硬件操作。不支持如 LPM 这类匹配类型，因为我们希望详细描述这一过程。匹配示例包括：

  * ``field_exact``: 对特定字段进行精确匹配
* ``field_exact_mask``: 在应用掩码后对特定字段进行精确匹配
* ``field_range``: 匹配特定范围
为了识别特定字段，需要指定报头和字段的 ID。此外，为了区分包中的同类型多个报头，还应指定报头索引（例如，在隧道场景中）。
Action
------

与匹配类似，动作也保持原始且接近硬件操作。例如：

  * ``field_modify``: 修改字段值
* ``field_inc``: 增加字段值
* ``push_header``: 添加一个报头
* ``pop_header``: 移除一个头部
条目
-----

特定表中的条目可以根据需要进行转储。每个条目都通过索引进行标识，并且其属性由一系列匹配/操作值和特定计数器来描述。通过转储表的内容，可以解决表之间的交互。
抽象示例
===================

以下是对Mellanox Spectrum ASIC的L3部分抽象模型的一个示例。这些模块按照它们在管道中出现的顺序进行描述。下面示例中的表大小并非实际硬件大小，仅用于演示目的。
最长前缀匹配（LPM）
---

最长前缀匹配算法可以通过一系列哈希表实现。每个哈希表包含具有相同前缀长度的路由。列表的根是/32，在未命中时，硬件将继续到下一个哈希表。搜索深度会影响数据路径延迟。
在命中情况下，条目包含了关于下一阶段的信息，该阶段负责解析MAC地址。下一阶段可能是直接连接路由的本地主机表，或者是下一跳的邻接表。
`meta.lpm_prefix`字段被用来连接两个LPM表。
.. code::

    表 lpm_prefix_16 {
      大小: 4096,
      启用计数器: 真,
      匹配: { meta.vr_id: 精确匹配,
               ipv4.目标地址: 精确掩码匹配,
               ipv6.目标地址: 精确掩码匹配,
               meta.lpm_prefix: 精确匹配 },
      操作: { meta.adj_index: 设置,
                meta.adj_group_size: 设置,
                meta.rif_port: 设置,
                meta.lpm_prefix: 设置 },
    }

本地主机
----------

对于本地路由的情况，LPM查找已经解析了出口路由器接口（RIF），但确切的MAC地址仍然未知。本地主机表是一个哈希表，它将输出接口ID与目标IP地址作为键。结果则是MAC地址。
.. code::

    表 local_host {
      大小: 4096,
      启用计数器: 真,
      匹配: { meta.rif_port: 精确匹配,
               ipv4.目标地址: 精确匹配},
      操作: { 以太网.目的地址: 设置 }
    }

邻接表
---------

对于远程路由的情况，此表实现了ECMP（等价多路径）。LPM查找的结果是ECMP组大小和索引，后者作为全局偏移量指向该表。
同时，生成包的哈希值。根据ECMP组大小和包的哈希值，生成局部偏移量。多个LPM条目可能指向同一个邻接组。
.. code::

    表 adjacency {
      大小: 4096,
      启用计数器: 真,
      匹配: { meta.adj_index: 精确匹配,
               meta.adj_group_size: 精确匹配,
               meta.packet_hash_index: 精确匹配 },
      操作: { 以太网.目的地址: 设置,
                meta.erif: 设置 }
    }

出口RIF
----

如果出口RIF和目的MAC已经在前面的表中解析出来，则此表执行多个操作，如TTL递减和MTU检查。
然后根据数据包的类型（广播、单播、多播）做出转发或丢弃的决定，并据此更新端口L3统计信息。

.. code::

    表 erif {
      大小: 800,
      启用计数器: 真,
      匹配: { 元数据.rif_port: 精确匹配,
               元数据.is_l3_unicast: 精确匹配,
               元数据.is_l3_broadcast: 精确匹配,
               元数据.is_l3_multicast: 精确匹配 },
      操作: { 元数据.l3_drop: 设置,
                元数据.l3_forward: 设置 }
    }
