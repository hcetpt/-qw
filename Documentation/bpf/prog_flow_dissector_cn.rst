SPDX 许可证标识符：GPL-2.0

============================
BPF_PROG_TYPE_FLOW_DISSECTOR
============================

概述
========

流解析器是一种从数据包中解析元数据的例程。它在网络子系统的各个地方（如RFS、流哈希等）使用。BPF流解析器试图在BPF中重新实现基于C的流解析器逻辑，以获得BPF验证器的所有好处（尤其是对指令数量和尾调用的限制）。

API
===

BPF流解析器程序在`__sk_buff`上运行。然而，只允许使用有限的一组字段：`data`、`data_end`和`flow_keys`。
`flow_keys`是`struct bpf_flow_keys`类型，包含流解析器的输入和输出参数。
输入包括：
  * `nhoff` - 网络头部的初始偏移量
  * `thoff` - 运输头部的初始偏移量，初始化为`nhoff`
  * `n_proto` - 从第二层头部解析出的L3协议类型
  * `flags` - 可选标志

BPF流解析器程序应该填充`struct bpf_flow_keys`的其余字段。输入参数`nhoff/thoff/n_proto`也应相应调整。
BPF程序的返回代码是BPF_OK表示成功解析，或BPF_DROP表示解析错误。

__sk_buff->data
===============

在没有VLAN的情况下，这是BPF流解析器初始状态的样子：

```
+------+------+------------+-----------+
| DMAC | SMAC | ETHER_TYPE | L3_HEADER |
+------+------+------------+-----------+
                              ^          |
                              |          +-- 流解析器从这里开始
```

代码如下：

```
skb->data + flow_keys->nhoff 指向L3_HEADER的第一个字节
flow_keys->thoff = nhoff
flow_keys->n_proto = ETHER_TYPE
```

在VLAN情况下，流解析器可以被调用处理两种不同的状态：

VLAN前解析：

```
+------+------+------+-----+-----------+-----------+
| DMAC | SMAC | TPID | TCI |ETHER_TYPE | L3_HEADER |
+------+------+------+-----+-----------+-----------+
                        ^              |
                        |              +-- 流解析器从这里开始
```

代码如下：

```
skb->data + flow_keys->nhoff指向TCI的第一个字节
flow_keys->thoff = nhoff
flow_keys->n_proto = TPID
```

请注意，TPID可能是802.1AD，因此，对于双标记的数据包，BPF程序可能需要解析两次VLAN信息。

VLAN后解析：

```
+------+------+------+-----+-----------+-----------+
| DMAC | SMAC | TPID | TCI |ETHER_TYPE | L3_HEADER |
+------+------+------+-----+-----------+-----------+
                                          ^          |
                                          |          +-- 流解析器从这里开始
```

代码如下：

```
skb->data + flow_keys->nhoff指向L3_HEADER的第一个字节
flow_keys->thoff = nhoff
flow_keys->n_proto = ETHER_TYPE
```

在这种情况下，VLAN信息在调用流解析器之前已被处理，BPF流解析器不需要处理它。

要点如下：BPF流解析器程序可能会被调用处理可选的VLAN头部，并且应该优雅地处理两种情况：存在单个或双VLAN以及不存在VLAN的情况。同一程序可以在这两种情况下被调用，必须仔细编写以处理这两种情况。
标题：标志

`flow_keys->flags` 可能包含可选的输入标志，其工作方式如下：

* `BPF_FLOW_DISSECTOR_F_PARSE_1ST_FRAG` - 告诉 BPF 流分发器继续解析第一个片段；默认预期行为是流分发器一旦发现数据包被分片就会返回；由 `eth_get_headlen` 使用来估计所有头部的长度以供 GRO（通用接收卸载）使用。
* `BPF_FLOW_DISSECTOR_F_STOP_AT_FLOW_LABEL` - 告诉 BPF 流分发器在到达 IPv6 流标签时停止解析；由 `___skb_get_hash` 使用来获取流哈希值。
* `BPF_FLOW_DISSECTOR_F_STOP_AT_ENCAP` - 告诉 BPF 流分发器在到达封装头部时停止解析；由路由基础设施使用。

参考实现
========================

请参阅 `tools/testing/selftests/bpf/progs/bpf_flow.c` 以获取参考实现，并参阅 `tools/testing/selftests/bpf/flow_dissector_load.[hc]` 以获取加载器。bpftool 也可以用于加载 BPF 流分发器程序。
参考实现的组织结构如下：
  * `jmp_table` 映射，其中包含每个支持的 L3 协议的子程序
  * `_dissect` 常规 - 入口点；它解析输入的 `n_proto` 并对适当的 L3 处理程序执行 `bpf_tail_call`

由于当前 BPF 不支持循环（或任何向后跳转），因此使用 jmp_table 来处理多层封装（以及 IPv6 选项）

当前限制
===================
BPF 流分发器不支持导出内核 C 基础实现可以导出的所有元数据。一个显著的例子是单 VLAN（802.1Q）和双 VLAN（802.1AD）标签。请参阅 `struct bpf_flow_keys`，以获取目前可以从 BPF 上下文导出的信息集。
当 BPF 流分发器附加到根网络命名空间（机器范围策略）时，用户不能在其子网络命名空间中覆盖它。
