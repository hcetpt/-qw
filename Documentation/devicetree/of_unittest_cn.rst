SPDX 许可证标识符: GPL-2.0

=================================
开放固件设备树单元测试
=================================

作者: Gaurav Minocha <gaurav.minocha.os@gmail.com>

1. 引言
===============

本文档解释了如何动态地将执行 OF 单元测试所需的测试数据附加到实时树上，且独立于机器的架构。
在继续之前建议阅读以下文档：
(1) 文档/devicetree/usage-model.rst
(2) http://www.devicetree.org/Device_Tree_Usage

OF 自测旨在测试提供给设备驱动开发者从非扁平化设备树数据结构中获取设备信息等接口（include/linux/of.h）。
大多数设备驱动在各种用例中使用此接口。
2. 详细输出（EXPECT）
==========================

如果单元测试检测到问题，它会向控制台打印警告或错误消息。单元测试还会由于故意设置的不良单元测试数据触发来自内核其他部分的警告和错误消息。
这导致了一些混淆，即触发的消息是否是测试预期的结果，还是与单元测试无关的真实问题。
已在单元测试中添加了 'EXPECT \ : text'（开始）和 'EXPECT / : text'（结束）消息来报告警告或错误是预期的。
开始在触发警告或错误之前打印，而结束则在触发警告或错误之后打印。
EXPECT 消息会导致非常嘈杂的控制台消息，难以阅读。脚本 scripts/dtc/of_unittest_expect 已创建来过滤这些冗余信息，并突出显示触发的警告和错误与预期的警告和错误之间的不匹配。更多信息可通过 'scripts/dtc/of_unittest_expect --help' 获取。
3. 测试数据
============

设备树源文件（drivers/of/unittest-data/testcases.dts）包含了执行 drivers/of/unittest.c 中自动化的单元测试所需的测试数据。目前，以下设备树源包含文件 (.dtsi) 被包含在 testcases.dts 中：

-   drivers/of/unittest-data/tests-interrupts.dtsi
-   drivers/of/unittest-data/tests-platform.dtsi
-   drivers/of/unittest-data/tests-phandle.dtsi
-   drivers/of/unittest-data/tests-match.dtsi

当内核构建时启用了 OF_SELFTEST，那么以下 make 规则用于将 DT 源文件（testcases.dts）编译为二进制块（testcases.dtb），也称为扁平化 DT：

    $(obj)/%.dtb: $(src)/%.dts FORCE
	    $(call if_changed_dep, dtc)

之后，通过以下规则将上述二进制块包装为汇编文件（testcases.dtb.S）：

    $(obj)/%.dtb.S: $(obj)/%.dtb
	    $(call cmd, dt_S_dtb)

汇编文件被编译为对象文件（testcases.dtb.o），并链接到内核映像中。
3.1. 添加测试数据
-------------------------

非扁平化设备树结构：

非扁平化设备树由以树状结构相连的 device_node(s) 构成，如下所示：

    // 下面的结构成员用于构建树
    struct device_node {
        ..
```c
// 设备节点结构体定义
struct device_node *parent;     // 父节点指针
struct device_node *child;      // 子节点指针
struct device_node *sibling;    // 同级兄弟节点指针
// ...
```

图 1 描述了机器未扁平化的设备树的一般结构，这里只考虑子节点和同级兄弟节点指针。还存在一个 `parent` 指针用于反向遍历树。在特定层级上，子节点和所有同级兄弟节点都将有一个指向共同父节点的 `parent` 指针（例如：`child1`、`sibling2`、`sibling3`、`sibling4` 的 `parent` 指向 `root` 节点）：

```
root ('/') 
|
child1 -> sibling2 -> sibling3 -> sibling4 -> null
|         |           |           |
|         |           |          null
|         |           |
|         |        child31 -> sibling32 -> null
|         |           |          |
|         |          null       null
|         |
|      child21 -> sibling22 -> sibling23 -> null
|         |          |            |
|        null       null         null
|
child11 -> sibling12 -> sibling13 -> sibling14 -> null
|           |           |            |
|           |           |           null
|           |           |
null        null       child131 -> null
			    |
			    null
```

图 1: 未扁平化设备树的一般结构

在执行 OF 单元测试之前，需要将测试数据附加到机器的设备树（如果存在）。因此，当调用 `selftest_data_add()` 时，它首先通过以下内核符号读取链接到内核映像中的扁平化设备树数据：

- `__dtb_testcases_begin` — 标记测试数据块开始的地址
- `__dtb_testcases_end` — 标记测试数据块结束的地址

其次，它调用 `of_fdt_unflatten_tree()` 来展开扁平化的数据块。最后，如果机器的设备树（即活动树）存在，则将未扁平化的测试数据树附加到活动树上；否则，它将自身作为活动设备树。`attach_node_and_children()` 使用 `of_attach_node()` 将节点按照如下方式附加到活动树中。为了说明这一点，图 2 中描述的测试数据树将被附加到图 1 中描述的活动树上：

```
root ('/') 
|
testcase-data
|
test-child0 -> test-sibling1 -> test-sibling2 -> test-sibling3 -> null
|               |                |                |
test-child01      null             null             null
```

图 2: 示例测试数据树，将被附加到活动树上

根据上述场景，活动树已经存在，因此不需要附加根 (`'/'`) 节点。其他所有节点都通过调用 `of_attach_node()` 进行附加。在 `of_attach_node()` 函数中，新节点作为给定父节点在活动树中的子节点进行附加。但是，如果父节点已经有子节点，则新节点将替换当前的子节点，并使其成为新节点的同级兄弟节点。因此，当测试案例数据节点附加到上面的活动树（图 1）时，最终结构如图 3 所示：

```
root ('/') 
|
testcase-data -> child1 -> sibling2 -> sibling3 -> sibling4 -> null
|               |          |           |           |
|             (...)      (...)       (...)        null
|
test-sibling3 -> test-sibling2 -> test-sibling1 -> test-child0 -> null
|                |                   |                |
null             null                null         test-child01
```

图 3: 在附加了测试案例数据之后的活动设备树结构

细心的读者会注意到，`test-child0` 节点变成了最后一个同级兄弟节点，与之前的结构（图 2）相比。在附加第一个 `test-child0` 节点后，`test-sibling1` 被附加，这将子节点（即 `test-child0`）推到了同级兄弟节点的位置，并使自己成为了子节点。

如果发现重复节点（即具有相同 `full_name` 属性的节点已经存在于活动树中），则不会附加该节点，而是通过调用 `update_node_properties()` 函数更新活动树中节点的属性。

### 3.2 删除测试数据

一旦测试用例执行完成，将调用 `selftest_data_remove` 以移除最初附加的设备节点（首先移除叶子节点，然后向上移除父节点，最终整个树都会被移除）。`selftest_data_remove()` 调用 `detach_node_and_children()`，后者使用 `of_detach_node()` 来从活动设备树中分离节点。

为了分离一个节点，`of_detach_node()` 要么更新给定节点的父节点的子节点指针为它的同级兄弟节点，要么将前一个同级兄弟节点连接到给定节点的同级兄弟节点，具体取决于情况。就是这样。
