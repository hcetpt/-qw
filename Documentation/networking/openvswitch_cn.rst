SPDX 许可证标识符: GPL-2.0

=============================================
Open vSwitch 数据路径开发人员文档
=============================================

Open vSwitch 内核模块允许用户空间灵活地控制选定网络设备上的流级数据包处理。它可以用来实现简单的以太网交换机、网络设备绑定、VLAN 处理、网络访问控制、基于流的网络控制等。
内核模块实现了多个“数据路径”（类似于桥接器），每个数据路径可以有多个“虚拟端口”（类似于桥接器内的端口）。每个数据路径还关联有一个“流表”，用户空间会用“流”填充该表，这些流根据数据包头部和元数据键映射到一系列动作。最常见的动作是将数据包转发到另一个虚拟端口；也实现了其他动作。
当一个数据包到达虚拟端口时，内核模块通过提取其流键并在流表中查找来处理它。如果找到匹配的流，则执行关联的动作。如果没有匹配项，则将数据包队列化给用户空间进行处理（作为处理的一部分，用户空间可能会设置一个流来在内核中完全处理相同类型的进一步数据包）
流键兼容性
----------------------

网络协议随着时间发展而演进。新的协议变得重要，而现有协议则失去其重要性。为了使 Open vSwitch 内核模块保持相关性，必须可能让新版本解析作为流键一部分的附加协议。甚至将来有一天可能需要放弃对已过时协议的支持。因此，Open vSwitch 的 Netlink 接口被设计为允许精心编写的用户空间应用程序与任何版本的流键一起工作，无论是过去还是未来的版本。
为了支持这种向前和向后的兼容性，每当内核模块将数据包传递给用户空间时，也会传递从该数据包解析出的流键。然后用户空间从数据包中提取其自身的流键概念，并将其与内核提供的版本进行比较：

    - 如果用户空间对于数据包的流键概念与内核的一致，则无需特殊操作。
- 如果内核的流键包含比用户空间版本更多的字段，例如，如果内核解码了 IPv6 头部但用户空间在以太网类型处停止（因为它不理解 IPv6），那么同样不需要特殊操作。只要使用内核提供的流键，用户空间仍可以以通常的方式设置流。
- 如果用户空间的流键包含比内核更多的字段，例如，如果用户空间解码了 IPv6 头部但内核在以太网类型处停止，那么用户空间可以手动转发数据包，而不必在内核中设置流。这种情况对性能不利，因为内核认为属于同一流的每个数据包都必须转给用户空间，但是转发行为是正确的。（如果用户空间能够确定额外字段的值不会影响转发行为，则可以无论如何设置流。）

流键随时间演变的方式对于使这一切正常运行很重要，因此以下各节将详细说明
流键格式
---------------

流键通过 Netlink 套接字作为一系列 Netlink 属性传递。一些属性表示数据包元数据，定义为无法从数据包本身提取的数据包信息，例如数据包接收的虚拟端口。然而，大多数属性是从数据包内部的头部提取的，例如以太网、IP 或 TCP 头部中的源地址和目标地址。
<linux/openvswitch.h> 标头文件定义了流键属性的确切格式。出于非正式解释目的，在这里我们用逗号分隔的字符串来书写它们，括号表示参数和嵌套。例如，以下可以表示一个到达虚拟端口 1 的 TCP 数据包对应的流键：

    in_port(1), eth(src=e0:91:f5:21:d0:b2, dst=00:02:e3:0f:80:a4),
    eth_type(0x0800), ipv4(src=172.16.0.20, dst=172.18.0.52, proto=17, tos=0,
    frag=no), tcp(src=49163, dst=80)

通常我们会省略讨论中不重要的参数，例如：

    in_port(1), eth(...), eth_type(0x0800), ipv4(...), tcp(...)


通配符流键格式
--------------------------

一个具有通配符的流由通过 Netlink 套接字传递的两个 Netlink 属性序列描述。一个流键，正如上面所述，以及一个可选的对应流掩码。
一个具有通配符的流可以代表一组精确匹配的流。掩码中的每个 '1' 位指定与流键中相应位的精确匹配。
一个‘0’位表示无关紧要的位，它将匹配传入数据包中的‘1’或‘0’位。使用通配符流可以提高流设置速率，通过减少需要由用户空间程序处理的新流的数量。
对于内核和用户空间程序而言，支持掩码Netlink属性是可选的。内核可以忽略掩码属性，安装精确匹配的流，或者减少内核中无关紧要的位的数量，使其少于用户空间程序指定的数量。在这种情况下，内核未实现的位的变化将简单地导致更多的流设置。
内核模块也能与那些既不支持也不提供流掩码属性的用户空间程序协同工作。
由于内核可能会忽略或修改通配符位，用户空间程序很难确切知道安装了哪些匹配规则。有两种可能的方法：当数据包错过内核流表时，反应性地安装流（因此根本不尝试确定通配符的变化）；或者利用内核响应消息来确定已安装的通配符。
在与用户空间交互时，内核应保持键的确切匹配部分与最初安装时完全一致。这将为所有未来的操作提供一个标识符。然而，在报告已安装流的掩码时，掩码应当包括内核施加的任何限制。
使用重叠的通配符流的行为是未定义的。确保任何传入的数据包最多只能匹配一个流（无论是通配符还是非通配符）的责任在于用户空间程序。当前实现尽可能检测重叠的通配符流，并可能会拒绝其中的一部分但不是全部。然而，这种行为在未来版本中可能会改变。
独特的流标识符
-------------------

除了使用键的原始匹配部分作为流识别的句柄外，另一种选择是独特的流标识符，或“UFID”。UFID对于内核和用户空间程序都是可选的。
支持UFID的用户空间程序预计会在流设置时提供它，除了流本身之外，然后在所有未来的操作中通过UFID引用该流。如果指定了UFID，内核不需要按原始流键索引流。
基本规则以演变流键
-----------------------------

为了确实维护遵循上述“流键兼容性”规则的应用程序的向前和向后兼容性，需要一些注意。
基本规则是显而易见的：

    ==================================================================
    新的网络协议支持只能补充现有的流键属性。不得更改已经定义的流键属性的意义。
这条规则确实有一些不那么显而易见的后果，因此值得通过几个例子来探讨。例如，假设内核模块尚未实现VLAN解析功能。相反，它只是将802.1Q的TPID（0x8100）解释为以太网类型，然后停止解析数据包。对于任何带有802.1Q头部的数据包，忽略元数据的情况下，其流键大致如下：

    eth(...), eth_type(0x8100)

直观地看，为了添加VLAN支持，合理的方法是添加一个新的“vlan”流键属性来包含VLAN标签，然后继续使用现有的字段定义解码VLAN标签之后的封装头。在这种变化下，一个位于VLAN 10中的TCP数据包的流键会类似于这样：

    eth(...), vlan(vid=10, pcp=0), eth_type(0x0800), ip(proto=6, ...), tcp(...)

但是这种改变会对那些未更新以理解新的“vlan”流键属性的用户空间应用程序产生负面影响。根据上面的流兼容性规则，应用程序可以忽略它不理解的“vlan”属性，并因此假设流中包含的是IP数据包。这是一个糟糕的假设（只有解析并跳过802.1Q头部时，流才只包含IP数据包），并且可能导致应用程序的行为在不同版本的内核之间发生变化，尽管它遵循了兼容性规则。解决方案是使用嵌套属性。例如，这就是为什么802.1Q支持使用嵌套属性的原因。一个位于VLAN 10中的TCP数据包实际上表示为：

    eth(...), eth_type(0x8100), vlan(vid=10, pcp=0), encap(eth_type(0x0800), ip(proto=6, ...), tcp(...))

请注意，“eth_type”、“ip”和“tcp”流键属性是如何嵌套在“encap”属性之内的。因此，不理解“vlan”键的应用程序不会看到这些属性，也就不会误解它们。（此外，外部的eth_type仍然是0x8100，而不是变为0x0800。）

处理畸形数据包
------------------

不要因为协议头部格式错误、校验和错误等原因而在内核中丢弃数据包。这会阻止用户空间实现一个简单的以太网交换机，后者转发所有数据包。
相反，在这种情况下，应该包括一个具有“空”内容的属性。即使空内容可能对应有效的协议值也没关系，只要这些值在实际中很少出现即可，因为用户空间总是可以将所有具有这些值的数据包转发到用户空间并单独处理它们。
例如，考虑一个含有IP头部的数据包，该头部表明协议6代表TCP，但该数据包在IP头部之后就被截断了，因此缺失TCP头部。这个数据包的流键将包含一个源端口和目的端口均为零的tcp属性，如下面所示：

    eth(...), eth_type(0x0800), ip(proto=6, ...), tcp(src=0, dst=0)

作为另一个例子，考虑一个以太网类型为0x8100的数据包，表明后面应跟有一个VLAN TCI，但该数据包在以太网类型之后就被截断了。这个数据包的流键将包含一个全零位的vlan属性和一个空的encap属性，如下面所示：

    eth(...), eth_type(0x8100), vlan(0), encap()

与源端口和目的端口都为0的TCP数据包不同，全零位的VLAN TCI并不是那么罕见，因此通常在vlan属性中设置CFI位（即内核中的VLAN_TAG_PRESENT）明确地允许这种情况被区分。因此，第二个例子中的流键明确地指示了缺失或畸形的VLAN TCI。

其他规则
---------

流键的其他规则要明显得多：

- 在给定的嵌套级别不允许有重复的属性。
- 属性的顺序不重要。
- 当内核向用户空间发送给定的流键时，它总是以相同的方式组合流键。这使得用户空间能够对整个流键进行哈希和比较，即使它无法完全解释这些流键。
您没有提供需要翻译的文本。请提供需要翻译成中文的英文或其他语言的文本。
