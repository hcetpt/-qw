SPDX许可证标识符: GPL-2.0

============================
BPF_PROG_TYPE_FLOW_DISSECTOR
============================

概述
========

流分解器是一种从数据包中解析元数据的例程。它在网络子系统的多个地方（如RFS、流哈希等）被使用。BPF流分解器是尝试用BPF重新实现基于C语言的流分解器逻辑，以获得BPF验证器的所有优势（特别是对指令数量和尾调用的限制）。
API
===

BPF流分解器程序在`__sk_buff`上运行。然而，只允许使用有限的一组字段：`data`、`data_end` 和 `flow_keys`。
`flow_keys` 是 `struct bpf_flow_keys` 类型，并包含流分解器的输入和输出参数。
输入包括：
  * `nhoff` - 网络头部的初始偏移量
  * `thoff` - 传输头部的初始偏移量，初始化为 `nhoff`
  * `n_proto` - 从第二层头部解析出的第三层协议类型
  * `flags` - 可选标志

BPF流分解器程序应该填充 `struct bpf_flow_keys` 的其余字段。输入参数 `nhoff/thoff/n_proto` 应该相应地调整。
BPF程序的返回码要么是 BPF_OK 表示成功分解，要么是 BPF_DROP 表示解析错误。

__sk_buff->data
===============

在没有VLAN的情况下，这是BPF流分解器初始状态的样子：

```
+------+------+------------+-----------+
| DMAC | SMAC | ETHER_TYPE | L3_HEADER |
+------+------+------------+-----------+
                              ^
                              |
                              +-- 流分解器从这里开始
```

```c
skb->data + flow_keys->nhoff 指向L3_HEADER的第一个字节
flow_keys->thoff = nhoff
flow_keys->n_proto = ETHER_TYPE
```

在VLAN情况下，流分解器可以被调用处理两种不同的状态。
预VLAN解析：

```
+------+------+------+-----+-----------+-----------+
| DMAC | SMAC | TPID | TCI |ETHER_TYPE | L3_HEADER |
+------+------+------+-----+-----------+-----------+
                        ^
                        |
                        +-- 流分解器从这里开始
```

```c
skb->data + flow_keys->nhoff 指向TCI的第一个字节
flow_keys->thoff = nhoff
flow_keys->n_proto = TPID
```

请注意TPID可能是802.1AD，因此对于双标记的数据包，BPF程序可能需要解析两次VLAN信息。
后VLAN解析：

```
+------+------+------+-----+-----------+-----------+
| DMAC | SMAC | TPID | TCI |ETHER_TYPE | L3_HEADER |
+------+------+------+-----+-----------+-----------+
                                          ^
                                          |
                                          +-- 流分解器从这里开始
```

```c
skb->data + flow_keys->nhoff 指向L3_HEADER的第一个字节
flow_keys->thoff = nhoff
flow_keys->n_proto = ETHER_TYPE
```

在这种情况下，VLAN信息已经在流分解器之前被处理，所以BPF流分解器不需要处理它。
总结：BPF流分解器程序可能会被调用来处理可选的VLAN头部，并且应该优雅地处理这两种情况：存在单个或双VLAN以及不存在VLAN的情况。相同的程序可以在这两种情况下被调用，并且需要仔细编写来处理这两种情况。
`flow_keys->flags`可能包含可选的输入标志，其工作方式如下：

* `BPF_FLOW_DISSECTOR_F_PARSE_1ST_FRAG` - 告知BPF流解析器继续解析第一个分片；默认预期行为是，一旦发现数据包被分片，流解析器就会返回；由`eth_get_headlen`使用来估算GRO的所有头部长度；
* `BPF_FLOW_DISSECTOR_F_STOP_AT_FLOW_LABEL` - 告知BPF流解析器到达IPv6流标签时停止解析；由`___skb_get_hash`使用来获取流哈希值；
* `BPF_FLOW_DISSECTOR_F_STOP_AT_ENCAP` - 告知BPF流解析器到达封装头部时停止解析；由路由基础设施使用；

参考实现
==================

参见`tools/testing/selftests/bpf/progs/bpf_flow.c`中的参考实现以及`tools/testing/selftests/bpf/flow_dissector_load.[hc]`中的加载器。bpftool也可以用来加载BPF流解析器程序。
参考实现组织结构如下：
  * `jmp_table`映射表，其中包含每个支持的L3协议对应的子程序
  * `_dissect`例程 - 入口点；它解析输入的`n_proto`并调用`bpf_tail_call`到适当的L3处理器

由于当前BPF不支持循环（或任何向后的跳转），因此使用`jmp_table`来处理多层封装（和IPv6选项）。

当前限制
==================
BPF流解析器不支持导出内核C语言实现可以导出的所有元数据。一个显著的例子是单VLAN（802.1Q）和双VLAN（802.1AD）标签。请参阅`struct bpf_flow_keys`以了解当前可以从BPF上下文中导出的信息集。
当BPF流解析器附加到根网络命名空间（机器级策略）时，用户不能在他们的子网络命名空间中覆盖它。
