SPDX 许可证标识符: BSD-3-Clause

======================================================
对原始 Netlink 家族的 Netlink 规格支持
======================================================

本文档描述了诸如 `NETLINK_ROUTE` 这样的原始 Netlink 家族所需的附加属性，这些家族使用 `netlink-raw` 协议规范。
规格
=============

`netlink-raw` 模式扩展了 `genetlink-legacy`<genetlink-legacy> 模式，以包含用于指定原始 Netlink 家族所使用的协议号和多播 ID 的属性。有关更多信息，请参阅 `classic_netlink`。原始 Netlink 家族也使用类型特定的子消息。
全局变量
-------

protonum
~~~~~~~~

`protonum` 属性用于指定打开 Netlink 套接字时要使用的协议号。
.. 代码块:: yaml

  # SPDX 许可证标识符: ((GPL-2.0 WITH Linux-syscall-note) OR BSD-3-Clause)

  名称: rt-addr
  协议: netlink-raw
  protonum: 0             # NETLINK_ROUTE 协议的一部分

多播组属性
--------------------------

值
~~~~~

`value` 属性用于指定多播组注册时要使用的组 ID。
.. 代码块:: yaml

  mcast-groups:
    列表:
      -
        名称: rtnlgrp-ipv4-ifaddr
        值: 5
      -
        名称: rtnlgrp-ipv6-ifaddr
        值: 9
      -
        名称: rtnlgrp-mctp-ifaddr
        值: 34

子消息
------------

一些原始 Netlink 家族如 `rt_link`<../../networking/netlink_spec/rt_link> 和 `tc`<../../networking/netlink_spec/tc> 使用属性嵌套作为抽象来携带模块特定信息。
概念上如下所示::

    [外部嵌套或消息级别]
      [通用属性 1]
      [通用属性 2]
      [通用属性 3]
      [通用属性 - 包装器]
        [模块特定属性 1]
        [模块特定属性 2]

外部级别的“通用属性”定义在核心（或 rt_link 或核心 TC）中，而具体的驱动程序、TC 分类器、qdisc 等可以在“通用属性 - 包装器”中携带自己的信息。虽然上面的例子显示属性嵌套在包装器内部，但模块通常有完全的自由来定义嵌套格式。实际上，包装属性的有效负载与 Netlink 消息非常相似。它可以包含固定的头部/结构、Netlink 属性或两者都有。由于这些共享特性，我们将包装属性的有效负载称为子消息。
子消息属性使用另一个属性的值作为选择键来选择正确的子消息格式。例如，如果以下属性已被解码：

.. 代码块:: json

  { "种类": "gre" }

并且我们遇到以下属性规范：

.. 代码块:: yaml

  -
    名称: 数据
    类型: 子消息
    子消息: linkinfo-data-msg
    选择器: 种类

然后我们查找名为 `linkinfo-data-msg` 的子消息定义，并使用 `种类` 属性的值，即 `gre`，作为选择正确子消息格式的键：

.. 代码块:: yaml

  子消息:
    名称: linkinfo-data-msg
    格式:
      -
        值: 桥接
        属性集: linkinfo-bridge-attrs
      -
        值: gre
        属性集: linkinfo-gre-attrs
      -
        值: geneve
        属性集: linkinfo-geneve-attrs

这将把属性值解码为具有名为 `linkinfo-gre-attrs` 的属性集作为属性空间的子消息。
子消息可以有一个可选的 `固定头部` 后跟零个或多个来自 `属性集` 的属性。例如，下面的 `tc-options-msg` 子消息定义了使用混合 `固定头部`、`属性集` 或两者的消息格式：

.. 代码块:: yaml

  子消息:
    -
      名称: tc-options-msg
      格式:
        -
          值: bfifo
          固定头部: tc-fifo-qopt
        -
          值: cake
          属性集: tc-cake-attrs
        -
          值: netem
          固定头部: tc-netem-qopt
          属性集: tc-netem-attrs

请注意，选择器属性必须出现在任何依赖于它的子消息属性之前。
如果像 `种类` 这样的属性在一个以上的嵌套级别上定义，则子消息选择器将使用离选择器‘最近’的值进行解析。
例如，如果相同的属性名称在一个嵌套的 `属性集` 中定义，该属性集与子消息选择器相邻，并且也在顶级 `属性集` 中定义，则选择器将使用离选择器‘最近’的值进行解析。如果消息中在同一级别上没有定义该值，则这是一个错误。
嵌套的结构体定义
-------------------------

许多原始 netlink 家族（如 :doc:`tc<../../networking/netlink_spec/tc>`）
使用了嵌套的结构体定义。``netlink-raw`` 模式允许在结构体定义中嵌入另一个结构体，通过使用 ``struct`` 属性来实现。例如，下面的结构体定义在 ``struct tc-tbf-qopt`` 的 ``rate`` 和 ``peakrate`` 成员中嵌入了 ``tc-ratespec`` 结构体定义。
```yaml
-
  name: tc-tbf-qopt
  type: struct
  members:
    -
      name: rate
      type: binary
      struct: tc-ratespec
    -
      name: peakrate
      type: binary
      struct: tc-ratespec
    -
      name: limit
      type: u32
    -
      name: buffer
      type: u32
    -
      name: mtu
      type: u32
```
