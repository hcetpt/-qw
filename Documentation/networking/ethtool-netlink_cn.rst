=============================
ethtool的Netlink接口
=============================


基本介绍
=================

ethtool的Netlink接口使用通用Netlink家族“ethtool”（用户空间应用程序应使用在`<linux/ethtool_netlink.h>`头文件中定义的宏`ETHTOOL_GENL_NAME`和`ETHTOOL_GENL_VERSION`）。此家族不使用特定的头部，所有请求和回复中的信息都通过Netlink属性传递。
ethtool的Netlink接口使用扩展ACK来报告错误和警告，建议用户空间应用程序开发者以适当的方式将这些消息提供给用户。
请求可以分为三类：“获取”（检索信息）、“设置”（设置参数）和“操作”（执行某个动作）。
所有“设置”和“操作”类型的请求都需要管理员权限（命名空间中的`CAP_NET_ADMIN`）。大多数“获取”类型的请求对任何人都允许，但也有例外情况（响应包含敏感信息）。在某些情况下，请求本身对任何人都允许，但无特权用户会忽略包含敏感信息（如WoL密码）的属性。
约定
===========

表示布尔值的属性通常使用NLA_U8类型，以便我们可以区分三种状态：“开启”，“关闭”和“不存在”（意味着在“获取”请求中信息不可用或在“设置”请求中值不需要更改）。对于这些属性，“真”值应作为数字1传递，但接收方应理解任何非零值为“真”。
在下面的表格中，“bool”表示按这种方式解释的NLA_U8属性。
在下面的消息结构描述中，如果属性名称后跟“+”，则父嵌套可以包含多个相同类型的属性。这实现了一组条目的数组。
设备驱动程序需要填充且基于其有效性向用户空间导出的属性不应使用零作为有效值。这避免了在设备驱动程序API中显式信号指示属性有效性的需求。
请求头部
==============

每个请求或回复消息都包含一个带有公共头部的嵌套属性。
此报头的结构如下：

  ==============================  ======  =============================
  ``ETHTOOL_A_HEADER_DEV_INDEX``  u32     设备索引
  ``ETHTOOL_A_HEADER_DEV_NAME``   字符串  设备名称
  ``ETHTOOL_A_HEADER_FLAGS``      u32     所有请求通用的标志位
  ==============================  ======  =============================

``ETHTOOL_A_HEADER_DEV_INDEX`` 和 ``ETHTOOL_A_HEADER_DEV_NAME`` 用于标识与消息相关的设备。在请求中使用其中一个就足够了，如果同时使用两者，则必须标识同一个设备。某些请求（例如全局字符串集）不需要设备标识。大多数“GET”请求也允许不带设备标识的转储请求，以查询所有提供该信息的设备的信息（每个设备分别发送一条消息）。

``ETHTOOL_A_HEADER_FLAGS`` 是一个适用于所有请求类型的请求标志位集合。这些标志位的解释对于所有请求类型都是相同的，但某些标志位可能不适用于某些请求。已识别的标志位包括：

  =================================  ===================================
  ``ETHTOOL_FLAG_COMPACT_BITSETS``   在回复中使用紧凑格式的位图
  ``ETHTOOL_FLAG_OMIT_REPLY``        省略可选回复（_SET和_ACT）
  ``ETHTOOL_FLAG_STATS``             包含可选的设备统计信息
  =================================  ===================================

新的请求标志位应遵循以下一般原则：如果未设置某个标志位，则行为应该是向后兼容的，即来自旧客户端（不了解该标志位）的请求应该按照客户端预期的方式进行解释。客户端不应设置其不理解的标志位。

位集
=====

对于较短且固定长度的位图，使用标准的 ``NLA_BITFIELD32`` 类型。对于任意长度的位图，ethtool netlink 使用嵌套属性，并且内容有两种形式：紧凑形式（两个二进制位图表示位值和受影响位的掩码）和详细形式（列出通过索引或名称标识的位）。

详细的（位-位）位集允许在传递位集时一起发送位的符号名称及其值，这可以节省一次往返时间（当位集作为请求的一部分传递时）或至少第二次请求（当位集作为回复的一部分时）。这对于传统的 ethtool 命令等一次性应用程序非常有用。另一方面，长期运行的应用程序（如 ethtool 监控器或网络管理守护进程）可能会倾向于只获取一次名称并使用紧凑形式以节省消息大小。ethtool netlink 接口的通知始终使用紧凑形式来表示位集。

位集可以表示值/掩码对（``ETHTOOL_A_BITSET_NOMASK`` 未设置）或单个位图（``ETHTOOL_A_BITSET_NOMASK`` 设置）。在修改位图的请求中，前者将掩码中的位设置为值中的值并保留其余部分；后者将位图中的位设置为1并将其余部分设置为0。

紧凑形式：嵌套（位集）属性的内容如下：

  ============================  ======  ============================
  ``ETHTOOL_A_BITSET_NOMASK``   标志    无掩码，只有列表
  ``ETHTOOL_A_BITSET_SIZE``     u32     有效位数
  ``ETHTOOL_A_BITSET_VALUE``    二进制  位值的位图
  ``ETHTOOL_A_BITSET_MASK``     二进制  有效位的掩码
  ============================  ======  ============================

值和掩码的长度至少应为 ``ETHTOOL_A_BITSET_SIZE`` 位，向上取最接近的32位倍数。它们由主机字节序的32位单词组成，从最低有效位到最高有效位排列（即与 ioctl 接口传递位图相同的方式）。

对于紧凑形式，``ETHTOOL_A_BITSET_SIZE`` 和 ``ETHTOOL_A_BITSET_VALUE`` 是必需的。如果未设置 ``ETHTOOL_A_BITSET_NOMASK``（位集表示值/掩码对），则 ``ETHTOOL_A_BITSET_MASK`` 属性是必需的；如果设置了 ``ETHTOOL_A_BITSET_NOMASK``（位集表示单个位图），则不允许 ``ETHTOOL_A_BITSET_MASK``。

内核位集长度可能与用户空间长度不同，如果使用较旧的应用程序在较新的内核上或反之亦然。如果用户空间位图较长，只有在请求实际尝试设置内核不认识的一些位的值时才会发出错误。

详细形式：嵌套（位集）属性的内容如下：

 +------------------------------------+--------+-----------------------------+
 | ``ETHTOOL_A_BITSET_NOMASK``        | 标志   | 无掩码，只有列表            |
 +------------------------------------+--------+-----------------------------+
 | ``ETHTOOL_A_BITSET_SIZE``          | u32    | 有效位数                   |
 +------------------------------------+--------+-----------------------------+
 | ``ETHTOOL_A_BITSET_BITS``          | 嵌套   | 位数组                      |
 +-+----------------------------------+--------+-----------------------------+
 | | ``ETHTOOL_A_BITSET_BITS_BIT+``   | 嵌套   | 单个位                       |
 +-+-+--------------------------------+--------+-----------------------------+
 | | | ``ETHTOOL_A_BITSET_BIT_INDEX`` | u32    | 位索引（最低有效位为0）      |
 +-+-+--------------------------------+--------+-----------------------------+
 | | | ``ETHTOOL_A_BITSET_BIT_NAME``  | 字符串 | 位名称                      |
 +-+-+--------------------------------+--------+-----------------------------+
 | | | ``ETHTOOL_A_BITSET_BIT_VALUE`` | 标志   | 如果位被设置则存在           |
 +-+-+--------------------------------+--------+-----------------------------+

位大小对于详细形式是可选的。``ETHTOOL_A_BITSET_BITS`` 嵌套只能包含 ``ETHTOOL_A_BITSET_BITS_BIT`` 属性，但可以包含任意数量的此类属性。位可以通过其索引或名称来标识。在请求中使用时，根据 ``ETHTOOL_A_BITSET_BIT_VALUE`` 将列出的位设置为0或1，其余部分保持不变。如果索引超过内核位长度或名称未被识别，请求将失败。

当存在 ``ETHTOOL_A_BITSET_NOMASK`` 标志时，位集被解释为简单的位图。在这种情况下不使用 ``ETHTOOL_A_BITSET_BIT_VALUE`` 属性。这种位集表示一个位图，其中列出的位被设置为1，其余位为0。
在请求中，应用程序可以使用两种形式。内核在回复时使用的格式由请求头中的 `ETHTOOL_FLAG_COMPACT_BITSETS` 标志决定。值和掩码的语义取决于属性。

消息类型列表
=====================

所有标识消息类型的常量都使用 `ETHTOOL_CMD_` 前缀和后缀，并根据消息目的进行区分：

  ==============    ======================================
  `_GET`            用户空间请求以获取数据
  `_SET`            用户空间请求以设置数据
  `_ACT`            用户空间请求执行某个动作
  `_GET_REPLY`      内核对 `GET` 请求的回复
  `_SET_REPLY`      内核对 `SET` 请求的回复
  `_ACT_REPLY`      内核对 `ACT` 请求的回复
  `_NTF`            内核的通知
  ==============    ======================================

用户空间到内核：

  ===================================== =================================
  `ETHTOOL_MSG_STRSET_GET`              获取字符串集
  `ETHTOOL_MSG_LINKINFO_GET`            获取链路设置
  `ETHTOOL_MSG_LINKINFO_SET`            设置链路设置
  `ETHTOOL_MSG_LINKMODES_GET`           获取链路模式信息
  `ETHTOOL_MSG_LINKMODES_SET`           设置链路模式信息
  `ETHTOOL_MSG_LINKSTATE_GET`           获取链路状态
  `ETHTOOL_MSG_DEBUG_GET`               获取调试设置
  `ETHTOOL_MSG_DEBUG_SET`               设置调试设置
  `ETHTOOL_MSG_WOL_GET`                 获取唤醒功能设置
  `ETHTOOL_MSG_WOL_SET`                 设置唤醒功能设置
  `ETHTOOL_MSG_FEATURES_GET`            获取设备特性
  `ETHTOOL_MSG_FEATURES_SET`            设置设备特性
  `ETHTOOL_MSG_PRIVFLAGS_GET`           获取私有标志
  `ETHTOOL_MSG_PRIVFLAGS_SET`           设置私有标志
  `ETHTOOL_MSG_RINGS_GET`               获取环形缓冲区大小
  `ETHTOOL_MSG_RINGS_SET`               设置环形缓冲区大小
  `ETHTOOL_MSG_CHANNELS_GET`            获取通道数量
  `ETHTOOL_MSG_CHANNELS_SET`            设置通道数量
  `ETHTOOL_MSG_COALESCE_GET`            获取合并参数
  `ETHTOOL_MSG_COALESCE_SET`            设置合并参数
  `ETHTOOL_MSG_PAUSE_GET`               获取暂停参数
  `ETHTOOL_MSG_PAUSE_SET`               设置暂停参数
  `ETHTOOL_MSG_EEE_GET`                 获取EEE设置
  `ETHTOOL_MSG_EEE_SET`                 设置EEE设置
  `ETHTOOL_MSG_TSINFO_GET`              获取时间戳信息
  `ETHTOOL_MSG_CABLE_TEST_ACT`          开始电缆测试的动作
  `ETHTOOL_MSG_CABLE_TEST_TDR_ACT`      开始原始TDR电缆测试的动作
  `ETHTOOL_MSG_TUNNEL_INFO_GET`         获取隧道卸载信息
  `ETHTOOL_MSG_FEC_GET`                 获取FEC设置
  `ETHTOOL_MSG_FEC_SET`                 设置FEC设置
  `ETHTOOL_MSG_MODULE_EEPROM_GET`       读取SFP模块EEPROM
  `ETHTOOL_MSG_STATS_GET`               获取标准统计信息
  `ETHTOOL_MSG_PHC_VCLOCKS_GET`         获取PHC虚拟时钟信息
  `ETHTOOL_MSG_MODULE_SET`              设置收发器模块参数
  `ETHTOOL_MSG_MODULE_GET`              获取收发器模块参数
  `ETHTOOL_MSG_PSE_SET`                 设置PSE参数
  `ETHTOOL_MSG_PSE_GET`                 获取PSE参数
  `ETHTOOL_MSG_RSS_GET`                 获取RSS设置
  `ETHTOOL_MSG_PLCA_GET_CFG`            获取PLCA RS参数
  `ETHTOOL_MSG_PLCA_SET_CFG`            设置PLCA RS参数
  `ETHTOOL_MSG_PLCA_GET_STATUS`         获取PLCA RS状态
  `ETHTOOL_MSG_MM_GET`                  获取MAC合并层状态
  `ETHTOOL_MSG_MM_SET`                  设置MAC合并层参数
  `ETHTOOL_MSG_MODULE_FW_FLASH_ACT`     刷新收发器模块固件
  ===================================== =================================

内核到用户空间：

  ======================================== =================================
  `ETHTOOL_MSG_STRSET_GET_REPLY`           字符串集内容
  `ETHTOOL_MSG_LINKINFO_GET_REPLY`         链路设置
  `ETHTOOL_MSG_LINKINFO_NTF`               链路设置通知
  `ETHTOOL_MSG_LINKMODES_GET_REPLY`        链路模式信息
  `ETHTOOL_MSG_LINKMODES_NTF`              链路模式通知
  `ETHTOOL_MSG_LINKSTATE_GET_REPLY`        链路状态信息
  `ETHTOOL_MSG_DEBUG_GET_REPLY`            调试设置
  `ETHTOOL_MSG_DEBUG_NTF`                  调试设置通知
  `ETHTOOL_MSG_WOL_GET_REPLY`              唤醒功能设置
  `ETHTOOL_MSG_WOL_NTF`                    唤醒功能设置通知
  `ETHTOOL_MSG_FEATURES_GET_REPLY`         设备特性
  `ETHTOOL_MSG_FEATURES_SET_REPLY`         对 `FEATURES_SET` 的可选回复
  `ETHTOOL_MSG_FEATURES_NTF`               网络设备特性通知
  `ETHTOOL_MSG_PRIVFLAGS_GET_REPLY`        私有标志
  `ETHTOOL_MSG_PRIVFLAGS_NTF`              私有标志
  `ETHTOOL_MSG_RINGS_GET_REPLY`            环形缓冲区大小
  `ETHTOOL_MSG_RINGS_NTF`                  环形缓冲区大小
  `ETHTOOL_MSG_CHANNELS_GET_REPLY`         通道数量
  `ETHTOOL_MSG_CHANNELS_NTF`               通道数量
  `ETHTOOL_MSG_COALESCE_GET_REPLY`         合并参数
  `ETHTOOL_MSG_COALESCE_NTF`               合并参数
  `ETHTOOL_MSG_PAUSE_GET_REPLY`            暂停参数
  `ETHTOOL_MSG_PAUSE_NTF`                  暂停参数
  `ETHTOOL_MSG_EEE_GET_REPLY`              EEE设置
  `ETHTOOL_MSG_EEE_NTF`                    EEE设置
  `ETHTOOL_MSG_TSINFO_GET_REPLY`           时间戳信息
  `ETHTOOL_MSG_CABLE_TEST_NTF`             电缆测试结果
  `ETHTOOL_MSG_CABLE_TEST_TDR_NTF`         电缆测试TDR结果
  `ETHTOOL_MSG_TUNNEL_INFO_GET_REPLY`      隧道卸载信息
  `ETHTOOL_MSG_FEC_GET_REPLY`              FEC设置
  `ETHTOOL_MSG_FEC_NTF`                    FEC设置
  `ETHTOOL_MSG_MODULE_EEPROM_GET_REPLY`    读取SFP模块EEPROM
  `ETHTOOL_MSG_STATS_GET_REPLY`            标准统计信息
  `ETHTOOL_MSG_PHC_VCLOCKS_GET_REPLY`      PHC虚拟时钟信息
  `ETHTOOL_MSG_MODULE_GET_REPLY`           收发器模块参数
  `ETHTOOL_MSG_PSE_GET_REPLY`              PSE参数
  `ETHTOOL_MSG_RSS_GET_REPLY`              RSS设置
  `ETHTOOL_MSG_PLCA_GET_CFG_REPLY`         PLCA RS参数
  `ETHTOOL_MSG_PLCA_GET_STATUS_REPLY`      PLCA RS状态
  `ETHTOOL_MSG_PLCA_NTF`                   PLCA RS参数
  `ETHTOOL_MSG_MM_GET_REPLY`               MAC合并层状态
  `ETHTOOL_MSG_MODULE_FW_FLASH_NTF`        收发器模块固件更新
  ======================================== =================================

`GET` 请求由用户空间应用程序发送以获取设备信息。它们通常不包含任何特定于消息的属性。内核通过相应的 `GET_REPLY` 消息进行回复。对于大多数类型，可以使用带有 `NLM_F_DUMP` 标志且没有设备标识的 `GET` 请求来查询支持该请求的所有设备的信息。
如果数据也可以被修改，则使用与相应 `GET_REPLY` 具有相同布局的 `SET` 消息来请求更改。请求中只包含需要更改的属性（并非所有属性都可以被更改）。大多数 `SET` 请求的回复仅包含错误代码和extack；如果内核提供了附加数据，则通过相应的 `SET_REPLY` 消息发送，可以通过在请求头中设置 `ETHTOOL_FLAG_OMIT_REPLY` 标志来抑制此回复。
数据修改还会触发发送一个 `NTF` 消息进行通知。这些通常只包含受影响的部分属性。如果通过其他手段（主要是ethtool ioctl接口）修改了数据，也会发出相同的通知。与仅在实际发生变化时才发送通知的ethtool netlink代码不同，ioctl接口可能即使请求没有实际更改任何数据也会发送通知。
`ACT` 消息请求内核（驱动程序）执行特定操作。如果内核报告了一些信息（可以通过在请求头中设置 `ETHTOOL_FLAG_OMIT_REPLY` 标志来抑制），则回复采用 `ACT_REPLY` 消息的形式。执行操作同样会触发通知（`NTF` 消息）。
后续部分将描述这些消息的格式和语义。

STRSET_GET
==========

请求字符串集的内容，类似于 ioctl 命令 `ETHTOOL_GSSET_INFO` 和 `ETHTOOL_GSTRINGS` 提供的内容。字符串集是不可写入用户空间的，因此对应的 `STRSET_SET` 消息仅用于内核回复。有两种类型的字符串集：全局（与设备无关，例如设备特性名称）和特定于设备（例如设备私有标志）。
请求内容：

 +---------------------------------------+--------+------------------------+
 | `ETHTOOL_A_STRSET_HEADER`             | nested | 请求头                 |
 +---------------------------------------+--------+------------------------+
 | `ETHTOOL_A_STRSET_STRINGSETS`         | nested | 要请求的字符串集       |
 +-+-------------------------------------+--------+------------------------+
 | | `ETHTOOL_A_STRINGSETS_STRINGSET+`   | nested | 一个字符串集           |
 +-+-+-----------------------------------+--------+------------------------+
 | | | `ETHTOOL_A_STRINGSET_ID`          | u32    | 集合ID                 |
 +-+-+-----------------------------------+--------+------------------------+

内核响应内容：

 +---------------------------------------+--------+-----------------------+
 | `ETHTOOL_A_STRSET_HEADER`             | nested | 回复头                |
 +---------------------------------------+--------+-----------------------+
 | `ETHTOOL_A_STRSET_STRINGSETS`         | nested | 字符串集数组           |
 +-+-------------------------------------+--------+-----------------------+
 | | `ETHTOOL_A_STRINGSETS_STRINGSET+`   | nested | 一个字符串集           |
 +-+-+-----------------------------------+--------+-----------------------+
 | | | `ETHTOOL_A_STRINGSET_ID`          | u32    | 集合ID                |
 +-+-+-----------------------------------+--------+-----------------------+
 | | | `ETHTOOL_A_STRINGSET_COUNT`       | u32    | 字符串数量            |
 +-+-+-----------------------------------+--------+-----------------------+
 | | | `ETHTOOL_A_STRINGSET_STRINGS`     | nested | 字符串数组            |
 +-+-+-+---------------------------------+--------+-----------------------+
 | | | | `ETHTOOL_A_STRINGS_STRING+`     | nested | 一个字符串             |
 +-+-+-+-+-------------------------------+--------+-----------------------+
 | | | | | `ETHTOOL_A_STRING_INDEX`      | u32    | 字符串索引            |
 +-+-+-+-+-------------------------------+--------+-----------------------+
 | | | | | `ETHTOOL_A_STRING_VALUE`      | string | 字符串值              |
 +-+-+-+-+-------------------------------+--------+-----------------------+
 | `ETHTOOL_A_STRSET_COUNTS_ONLY`        | flag   | 只返回数量            |
 +---------------------------------------+--------+-----------------------+

请求头中的设备标识是可选的。根据其是否存在以及 `NLM_F_DUMP` 标志，存在三种类型的 `STRSET_GET` 请求：

 - 没有 `NLM_F_DUMP`，没有设备：获取“全局”字符串集
 - 没有 `NLM_F_DUMP`，有设备：获取与设备相关的字符串集
 - `NLM_F_DUMP`，没有设备：获取所有设备的相关字符串集

如果没有 `ETHTOOL_A_STRSET_STRINGSETS` 数组，则返回所有请求类型的字符串集，否则只返回请求中指定的那些字符串集。
标志 ``ETHTOOL_A_STRSET_COUNTS_ONLY`` 告诉内核只返回集合的字符串计数，而不是实际的字符串。
LINKINFO_GET
============

请求链路设置，这些设置由 ``ETHTOOL_GLINKSETTINGS`` 提供，但不包括链路模式和自动协商相关信息。该请求不使用任何属性。
请求内容：

  ====================================  ======  ==========================
  ``ETHTOOL_A_LINKINFO_HEADER``         nested  请求头
  ====================================  ======  ==========================

内核响应内容：

  ====================================  ======  ==========================
  ``ETHTOOL_A_LINKINFO_HEADER``         nested  响应头
  ``ETHTOOL_A_LINKINFO_PORT``           u8      物理端口
  ``ETHTOOL_A_LINKINFO_PHYADDR``        u8      PHY MDIO 地址
  ``ETHTOOL_A_LINKINFO_TP_MDIX``        u8      MDI(-X) 状态
  ``ETHTOOL_A_LINKINFO_TP_MDIX_CTRL``   u8      MDI(-X) 控制
  ``ETHTOOL_A_LINKINFO_TRANSCEIVER``    u8      收发器
  ====================================  ======  ==========================

属性及其值与相应 ioctl 结构中的成员具有相同的意义。
``LINKINFO_GET`` 允许转储请求（内核为支持该请求的所有设备返回响应消息）。
LINKINFO_SET
============

``LINKINFO_SET`` 请求允许设置由 ``LINKINFO_GET`` 报告的一些属性。
请求内容：

  ====================================  ======  ==========================
  ``ETHTOOL_A_LINKINFO_HEADER``         nested  请求头
  ``ETHTOOL_A_LINKINFO_PORT``           u8      物理端口
  ``ETHTOOL_A_LINKINFO_PHYADDR``        u8      PHY MDIO 地址
  ``ETHTOOL_A_LINKINFO_TP_MDIX_CTRL``   u8      MDI(-X) 控制
  ====================================  ======  ==========================

MDI(-X) 状态和收发器不能被设置，包含相应属性的请求将被拒绝。
LINKMODES_GET
=============

请求链路模式（支持的、已通告的和对等体已通告的）及相关信息（自动协商状态、链路速度和双工模式），这些信息由 ``ETHTOOL_GLINKSETTINGS`` 提供。该请求不使用任何属性。
请求内容：

  ====================================  ======  ==========================
  ``ETHTOOL_A_LINKMODES_HEADER``        nested  请求头
  ====================================  ======  ==========================

内核响应内容：

  ==========================================  ======  ==========================
  ``ETHTOOL_A_LINKMODES_HEADER``              nested  响应头
  ``ETHTOOL_A_LINKMODES_AUTONEG``             u8      自动协商状态
  ``ETHTOOL_A_LINKMODES_OURS``                bitset  已通告的链路模式
  ``ETHTOOL_A_LINKMODES_PEER``                bitset  对等体链路模式
  ``ETHTOOL_A_LINKMODES_SPEED``               u32     链路速度（Mb/s）
  ``ETHTOOL_A_LINKMODES_DUPLEX``              u8      双工模式
  ``ETHTOOL_A_LINKMODES_MASTER_SLAVE_CFG``    u8      主/从端口模式
  ``ETHTOOL_A_LINKMODES_MASTER_SLAVE_STATE``  u8      主/从端口状态
  ``ETHTOOL_A_LINKMODES_RATE_MATCHING``       u8      PHY 速率匹配
  ==========================================  ======  ==========================

对于 ``ETHTOOL_A_LINKMODES_OURS``，值表示已通告的模式，掩码表示支持的模式。响应中的 ``ETHTOOL_A_LINKMODES_PEER`` 是一个位列表。
``LINKMODES_GET`` 允许转储请求（内核为支持该请求的所有设备返回响应消息）。
LINKMODES_SET
=============

请求内容：

  ==========================================  ======  ==========================
  ``ETHTOOL_A_LINKMODES_HEADER``              nested  请求头
  ``ETHTOOL_A_LINKMODES_AUTONEG``             u8      自动协商状态
  ``ETHTOOL_A_LINKMODES_OURS``                bitset  已通告的链路模式
  ``ETHTOOL_A_LINKMODES_PEER``                bitset  对等体链路模式
  ``ETHTOOL_A_LINKMODES_SPEED``               u32     链路速度（Mb/s）
  ``ETHTOOL_A_LINKMODES_DUPLEX``              u8      双工模式
  ``ETHTOOL_A_LINKMODES_MASTER_SLAVE_CFG``    u8      主/从端口模式
  ``ETHTOOL_A_LINKMODES_RATE_MATCHING``       u8      PHY 速率匹配
  ``ETHTOOL_A_LINKMODES_LANES``               u32     车道数
  ==========================================  ======  ==========================

``ETHTOOL_A_LINKMODES_OURS`` 的位集允许设置已通告的链路模式。如果自动协商已启用（无论是现在设置的还是之前保留的），则已通告的模式不会改变（没有 ``ETHTOOL_A_LINKMODES_OURS`` 属性），并且至少指定了速度、双工和车道之一，则内核会调整已通告的模式以匹配所有支持的速度、双工、车道或全部（根据指定的内容）。
此自动选择是通过 `ethtool` 的 `ioctl` 接口完成的，`netlink` 接口旨在允许在不知道内核具体支持哪些功能的情况下请求更改。

### LINKSTATE_GET
请求链路状态信息。提供由 `ETHTOOL_GLINK` ioctl 命令提供的链路上/下标志。可选地，还可能提供扩展状态。一般来说，扩展状态描述了端口为何处于关闭状态或为何以某种不明显的方式运行。此请求没有任何属性。
请求内容：

  - `ETHTOOL_A_LINKSTATE_HEADER`：嵌套的请求头

内核响应内容：

  - `ETHTOOL_A_LINKSTATE_HEADER`：嵌套的回复头
  - `ETHTOOL_A_LINKSTATE_LINK`：布尔值 链路状态（上/下）
  - `ETHTOOL_A_LINKSTATE_SQI`：u32 当前信号质量指数
  - `ETHTOOL_A_LINKSTATE_SQI_MAX`：u32 支持的最大SQI值
  - `ETHTOOL_A_LINKSTATE_EXT_STATE`：u8 扩展链路状态
  - `ETHTOOL_A_LINKSTATE_EXT_SUBSTATE`：u8 扩展链路子状态
  - `ETHTOOL_A_LINKSTATE_EXT_DOWN_CNT`：u32 链路断开事件计数

对于大多数 NIC 驱动程序，`ETHTOOL_A_LINKSTATE_LINK` 返回由 `netif_carrier_ok()` 提供的载波标志，但有些驱动程序定义了自己的处理程序。`ETHTOOL_A_LINKSTATE_EXT_STATE` 和 `ETHTOOL_A_LINKSTATE_EXT_SUBSTATE` 是可选值。`ethtool` 核心可以同时提供 `ETHTOOL_A_LINKSTATE_EXT_STATE` 和 `ETHTOOL_A_LINKSTATE_EXT_SUBSTATE`，或者只提供 `ETHTOOL_A_LINKSTATE_EXT_STATE`，或者都不提供。

`LINKSTATE_GET` 允许进行转储请求（内核返回支持该请求的所有设备的回复消息）。

#### 扩展链路状态：

  - `ETHTOOL_LINK_EXT_STATE_AUTONEG`：与自动协商相关的状态或问题
  - `ETHTOOL_LINK_EXT_STATE_LINK_TRAINING_FAILURE`：链路训练失败
  - `ETHTOOL_LINK_EXT_STATE_LINK_LOGICAL_MISMATCH`：物理编码子层或前向纠错子层的逻辑不匹配
  - `ETHTOOL_LINK_EXT_STATE_BAD_SIGNAL_INTEGRITY`：信号完整性问题
  - `ETHTOOL_LINK_EXT_STATE_NO_CABLE`：未连接电缆
  - `ETHTOOL_LINK_EXT_STATE_CABLE_ISSUE`：故障与电缆相关，例如不支持的电缆
  - `ETHTOOL_LINK_EXT_STATE_EEPROM_ISSUE`：故障与 EEPROM 相关，例如读取或解析数据时的失败
  - `ETHTOOL_LINK_EXT_STATE_CALIBRATION_FAILURE`：校准算法中的失败
  - `ETHTOOL_LINK_EXT_STATE_POWER_BUDGET_EXCEEDED`：硬件无法提供电缆或模块所需的功率
  - `ETHTOOL_LINK_EXT_STATE_OVERHEAT`：模块过热
  - `ETHTOOL_LINK_EXT_STATE_MODULE`：收发器模块问题

#### 扩展链路子状态：

##### 自动协商子状态：

  - `ETHTOOL_LINK_EXT_SUBSTATE_AN_NO_PARTNER_DETECTED`：对端已关闭
  - `ETHTOOL_LINK_EXT_SUBSTATE_AN_ACK_NOT_RECEIVED`：未收到对端确认
  - `ETHTOOL_LINK_EXT_SUBSTATE_AN_NEXT_PAGE_EXCHANGE_FAILED`：下一页交换失败
  - `ETHTOOL_LINK_EXT_SUBSTATE_AN_NO_PARTNER_DETECTED_FORCE_MODE`：强制模式下对端已关闭或速度未达成一致
  - `ETHTOOL_LINK_EXT_SUBSTATE_AN_FEC_MISMATCH_DURING_OVERRIDE`：双方的前向纠错模式不一致
  - `ETHTOOL_LINK_EXT_SUBSTATE_AN_NO_HCD`：没有最高公倍数

##### 链路训练子状态：

  - `ETHTOOL_LINK_EXT_SUBSTATE_LT_KR_FRAME_LOCK_NOT_ACQUIRED`：帧未被识别，锁定失败
  - `ETHTOOL_LINK_EXT_SUBSTATE_LT_KR_LINK_INHIBIT_TIMEOUT`：在超时之前未发生锁定
  - `ETHTOOL_LINK_EXT_SUBSTATE_LT_KR_LINK_PARTNER_DID_NOT_SET_RECEIVER_READY`：对端在训练过程后未发送准备信号
  - `ETHTOOL_LINK_EXT_SUBSTATE_LT_REMOTE_FAULT`：远端尚未准备好

##### 链路逻辑不匹配子状态：

  - `ETHTOOL_LINK_EXT_SUBSTATE_LLM_PCS_DID_NOT_ACQUIRE_BLOCK_LOCK`：物理编码子层在第一阶段未锁定——块锁
  - `ETHTOOL_LINK_EXT_SUBSTATE_LLM_PCS_DID_NOT_ACQUIRE_AM_LOCK`：物理编码子层在第二阶段未锁定——对齐标记锁
  - `ETHTOOL_LINK_EXT_SUBSTATE_LLM_PCS_DID_NOT_GET_ALIGN_STATUS`：物理编码子层未获取对齐状态
  - `ETHTOOL_LINK_EXT_SUBSTATE_LLM_FC_FEC_IS_NOT_LOCKED`：FC前向纠错未锁定
  - `ETHTOOL_LINK_EXT_SUBSTATE_LLM_RS_FEC_IS_NOT_LOCKED`：RS前向纠错未锁定

##### 信号完整性问题子状态：

  - `ETHTOOL_LINK_EXT_SUBSTATE_BSI_LARGE_NUMBER_OF_PHYSICAL_ERRORS`：大量物理错误
  - `ETHTOOL_LINK_EXT_SUBSTATE_BSI_UNSUPPORTED_RATE`：系统尝试以不正式支持的速度运行电缆，导致信号完整性问题
  - `ETHTOOL_LINK_EXT_SUBSTATE_BSI_SERDES_REFERENCE_CLOCK_LOST`：SerDes 的外部时钟信号太弱或不可用
  - `ETHTOOL_LINK_EXT_SUBSTATE_BSI_SERDES_ALOS`：SerDes 接收到的信号太弱，因为模拟信号丢失

##### 电缆问题子状态：

  - `ETHTOOL_LINK_EXT_SUBSTATE_CI_UNSUPPORTED_CABLE`：不支持的电缆
  - `ETHTOOL_LINK_EXT_SUBSTATE_CI_CABLE_TEST_FAILURE`：电缆测试失败

##### 收发器模块问题子状态：

  - `ETHTOOL_LINK_EXT_SUBSTATE_MODULE_CMIS_NOT_READY`：CMIS 模块状态机未达到模块就绪状态，例如模块卡在故障状态

### DEBUG_GET
请求设备的调试设置。目前仅提供消息掩码。
请求内容：

  - `ETHTOOL_A_DEBUG_HEADER`：嵌套的请求头

内核响应内容：

  - `ETHTOOL_A_DEBUG_HEADER`：嵌套的回复头
  - `ETHTOOL_A_DEBUG_MSGMASK`：位集 消息掩码

消息掩码 (`ETHTOOL_A_DEBUG_MSGMASK`) 等同于由 `ETHTOOL_GMSGLVL` 提供并通过 `ETHTOOL_SMSGLVL` 在 ioctl 接口中设置的消息级别。虽然由于历史原因称其为消息级别，但大多数驱动程序和几乎所有的新驱动程序将其作为启用的消息类别的掩码（由 `NETIF_MSG_*` 常量表示），因此 `netlink` 接口遵循实际使用情况。

`DEBUG_GET` 允许进行转储请求（内核返回支持该请求的所有设备的回复消息）。
### DEBUG_SET
=========
设置或更新设备的调试设置。目前，仅支持消息掩码。
请求内容：

  ====================================  ======  ==========================
  ``ETHTOOL_A_DEBUG_HEADER``            嵌套    请求头
  ``ETHTOOL_A_DEBUG_MSGMASK``           位集    消息掩码
  ====================================  ======  ==========================

``ETHTOOL_A_DEBUG_MSGMASK`` 位集允许设置或修改设备启用的调试消息类型的掩码。

### WOL_GET
=======
查询设备的网络唤醒设置。与大多数“GET”类型请求不同，``ETHTOOL_MSG_WOL_GET`` 需要（网络命名空间）``CAP_NET_ADMIN`` 权限，因为它（可能）提供了保密的 SecureOn™ 密码。
请求内容：

  ====================================  ======  ==========================
  ``ETHTOOL_A_WOL_HEADER``              嵌套    请求头
  ====================================  ======  ==========================

内核响应内容：

  ====================================  ======  ==========================
  ``ETHTOOL_A_WOL_HEADER``              嵌套    响应头
  ``ETHTOOL_A_WOL_MODES``               位集    启用的 WoL 模式掩码
  ``ETHTOOL_A_WOL_SOPASS``              二进制   SecureOn™ 密码
  ====================================  ======  ==========================

响应中，``ETHTOOL_A_WOL_MODES`` 掩码由设备支持的模式组成，并且包含已启用模式的值。``ETHTOOL_A_WOL_SOPASS`` 只有在支持 ``WAKE_MAGICSECURE`` 模式时才包含在响应中。

### WOL_SET
=======
设置或更新网络唤醒设置。
请求内容：

  ====================================  ======  ==========================
  ``ETHTOOL_A_WOL_HEADER``              嵌套    请求头
  ``ETHTOOL_A_WOL_MODES``               位集    启用的 WoL 模式
  ``ETHTOOL_A_WOL_SOPASS``              二进制   SecureOn™ 密码
  ====================================  ======  ==========================

``ETHTOOL_A_WOL_SOPASS`` 只允许用于支持 ``WAKE_MAGICSECURE`` 模式的设备。

### FEATURES_GET
============
获取 netdev 特性，类似于 ``ETHTOOL_GFEATURES`` ioctl 请求。
请求内容：

  ====================================  ======  ==========================
  ``ETHTOOL_A_FEATURES_HEADER``         嵌套    请求头
  ====================================  ======  ==========================

内核响应内容：

  ====================================  ======  ==========================
  ``ETHTOOL_A_FEATURES_HEADER``         嵌套    响应头
  ``ETHTOOL_A_FEATURES_HW``             位集    dev->hw_features
  ``ETHTOOL_A_FEATURES_WANTED``         位集    dev->wanted_features
  ``ETHTOOL_A_FEATURES_ACTIVE``         位集    dev->features
  ``ETHTOOL_A_FEATURES_NOCHANGE``       位集    NETIF_F_NEVER_CHANGE
  ====================================  ======  ==========================

内核响应中的位图具有与 ioctl 干涉中使用的位图相同的含义，但属性名称不同（它们基于 `struct net_device` 的相应成员）。遗留的 “标志” 不提供，如果用户空间需要它们（很可能只是为了向后兼容），可以从相关的特性位自行计算其值。
`ETHA_FEATURES_HW` 使用由内核识别的所有特性组成的掩码（为了在使用详细的位图格式时提供所有名称），其他三个不使用掩码（简单的位列表）。

### FEATURES_SET
============
请求设置 netdev 特性，类似于 ``ETHTOOL_SFEATURES`` ioctl 请求。
请求内容：

  ====================================  ======  ==========================
  ``ETHTOOL_A_FEATURES_HEADER``         嵌套    请求头
  ``ETHTOOL_A_FEATURES_WANTED``         位图    请求的功能
  ====================================  ======  ==========================

内核响应内容：

  ====================================  ======  ==========================
  ``ETHTOOL_A_FEATURES_HEADER``         嵌套    响应头
  ``ETHTOOL_A_FEATURES_WANTED``         位图    请求与结果的差异
  ``ETHTOOL_A_FEATURES_ACTIVE``         位图    新旧活动功能的差异
  ====================================  ======  ==========================

请求中仅包含一个位图，可以是值/掩码对（请求更改特定功能位并保留其余部分）或仅一个值（请求将所有功能设置为指定集）。由于请求需经过`netdev_change_features()`的一致性检查，可选的内核响应（可以通过请求头中的`ETHTOOL_FLAG_OMIT_REPLY`标志来抑制）会通知客户端实际结果。`ETHTOOL_A_FEATURES_WANTED`报告了客户端请求与实际结果之间的差异：掩码由请求功能与结果（操作后的`dev->features`）之间的不同位组成，值则由这些位在请求中的值（即来自结果功能的否定值）组成。`ETHTOOL_A_FEATURES_ACTIVE`报告了新旧`dev->features`之间的差异：掩码由已更改的位组成，值则为新`dev->features`（操作后）中的这些位的值。

`ETHTOOL_MSG_FEATURES_NTF`通知不仅在使用`ETHTOOL_MSG_FEATURES_SET`请求或ethtool ioctl请求修改设备功能时发送，而且每次使用`netdev_update_features()`或`netdev_change_features()`修改功能时也会发送。

PRIVFLAGS_GET
=============

获取私有标志，类似于`ETHTOOL_GPFLAGS` ioctl请求
请求内容：

  ====================================  ======  ==========================
  ``ETHTOOL_A_PRIVFLAGS_HEADER``        嵌套    请求头
  ====================================  ======  ==========================

内核响应内容：

  ====================================  ======  ==========================
  ``ETHTOOL_A_PRIVFLAGS_HEADER``        嵌套    响应头
  ``ETHTOOL_A_PRIVFLAGS_FLAGS``         位图    私有标志
  ====================================  ======  ==========================

`ETHTOOL_A_PRIVFLAGS_FLAGS`是一个位图，包含了设备的私有标志。
这些标志由驱动程序定义，其数量和名称（以及含义）取决于设备。为了紧凑的位图格式，名称可以通过`ETH_SS_PRIV_FLAGS`字符串集检索。如果请求详细的位图格式，响应将使用设备支持的所有私有标志作为掩码，以便客户端能够获得完整信息而无需获取带有名称的字符串集。

PRIVFLAGS_SET
=============

设置或修改设备的私有标志，类似于`ETHTOOL_SPFLAGS` ioctl请求
请求内容：

  ====================================  ======  ==========================
  ``ETHTOOL_A_PRIVFLAGS_HEADER``        嵌套    请求头
  ``ETHTOOL_A_PRIVFLAGS_FLAGS``         位图    私有标志
  ====================================  ======  ==========================

`ETHTOOL_A_PRIVFLAGS_FLAGS`可以设置整个私有标志集或仅修改某些值。

RINGS_GET
=========

获取环大小，类似于`ETHTOOL_GRINGPARAM` ioctl请求
请求内容：

  ====================================  ======  ==========================
  ``ETHTOOL_A_RINGS_HEADER``            嵌套    请求头
  ====================================  ======  ==========================

内核响应内容：

  =======================================   ======  ===========================
  ``ETHTOOL_A_RINGS_HEADER``                嵌套    响应头
  ``ETHTOOL_A_RINGS_RX_MAX``                u32     RX环的最大尺寸
  ``ETHTOOL_A_RINGS_RX_MINI_MAX``           u32     RX迷你环的最大尺寸
  ``ETHTOOL_A_RINGS_RX_JUMBO_MAX``          u32     RX巨环的最大尺寸
  ``ETHTOOL_A_RINGS_TX_MAX``                u32     TX环的最大尺寸
  ``ETHTOOL_A_RINGS_RX``                    u32     RX环的尺寸
  ``ETHTOOL_A_RINGS_RX_MINI``               u32     RX迷你环的尺寸
  ``ETHTOOL_A_RINGS_RX_JUMBO``              u32     RX巨环的尺寸
  ``ETHTOOL_A_RINGS_TX``                    u32     TX环的尺寸
  ``ETHTOOL_A_RINGS_RX_BUF_LEN``            u32     环上的缓冲区大小
  ``ETHTOOL_A_RINGS_TCP_DATA_SPLIT``        u8      TCP报头/数据拆分
  ``ETHTOOL_A_RINGS_CQE_SIZE``              u32     TX/RX CQE的大小
  ``ETHTOOL_A_RINGS_TX_PUSH``               u8      TX推送模式标志
  ``ETHTOOL_A_RINGS_RX_PUSH``               u8      RX推送模式标志
  ``ETHTOOL_A_RINGS_TX_PUSH_BUF_LEN``       u32     TX推送缓冲区大小
  ``ETHTOOL_A_RINGS_TX_PUSH_BUF_LEN_MAX``   u32     TX推送缓冲区的最大尺寸
  =======================================   ======  ===========================

`ETHTOOL_A_RINGS_TCP_DATA_SPLIT`指示设备是否可用于页翻转TCP零拷贝接收(`getsockopt(TCP_ZEROCOPY_RECEIVE)`）。
如果启用，设备将被配置为将帧头和数据分别放入不同的缓冲区。设备配置必须能够接收完整的内存页数据，例如因为MTU足够大或通过硬件大型接收（HW-GRO）实现。

``ETHTOOL_A_RINGS_[RX|TX]_PUSH`` 标志用于启用快速路径以发送或接收数据包。在普通路径中，驱动程序在DRAM中填充描述符并通知NIC硬件。而在快速路径中，驱动程序通过MMIO写操作将描述符推送到设备，从而减少延迟。然而，启用此功能可能会增加CPU成本。驱动程序可能强制实施额外的每个数据包资格检查（例如，基于数据包大小的检查）。

``ETHTOOL_A_RINGS_TX_PUSH_BUF_LEN`` 指定了驱动程序可以推送到底层设备的最大字节数（“推送”模式）。将部分有效负载推送到设备具有避免DMA映射的优势，从而减少了小数据包的延迟（与 ``ETHTOOL_A_RINGS_TX_PUSH`` 参数相同），并且允许底层设备提前处理数据包头部，在获取其有效负载之前。

这有助于设备根据数据包的头部信息快速采取行动。这类似于“tx-copybreak”参数，该参数将数据包复制到预先分配的DMA内存区域而不是映射新的内存。然而，“tx-push-buff”参数直接将数据包复制到设备，使设备能够更快地对数据包采取行动。

RINGS_SET
=========

设置环形缓冲区大小，类似于 ``ETHTOOL_SRINGPARAM`` ioctl 请求。
请求内容：

  ====================================  ======  ===========================
  ``ETHTOOL_A_RINGS_HEADER``            嵌套    回复头
  ``ETHTOOL_A_RINGS_RX``                u32     接收环大小
  ``ETHTOOL_A_RINGS_RX_MINI``           u32     接收小型环大小
  ``ETHTOOL_A_RINGS_RX_JUMBO``          u32     接收巨型环大小
  ``ETHTOOL_A_RINGS_TX``                u32     发送环大小
  ``ETHTOOL_A_RINGS_RX_BUF_LEN``        u32     环上缓冲区的大小
  ``ETHTOOL_A_RINGS_CQE_SIZE``          u32     发送/接收CQE的大小
  ``ETHTOOL_A_RINGS_TX_PUSH``           u8      发送推送模式标志
  ``ETHTOOL_A_RINGS_RX_PUSH``           u8      接收推送模式标志
  ``ETHTOOL_A_RINGS_TX_PUSH_BUF_LEN``   u32     发送推送缓冲区的大小
  ====================================  ======  ===========================

内核会检查请求的环大小是否超过了由驱动程序报告的限制。驱动程序可能会施加额外的约束，并且可能不支持所有属性。

``ETHTOOL_A_RINGS_CQE_SIZE`` 指定了完成队列事件的大小。完成队列事件（CQE）是由NIC发布的事件，用于指示数据包发送（如成功或错误）或接收（如指向数据包片段的指针）时的状态。如果NIC支持，可以通过修改CQE大小来调整CQE大小。更大的CQE可以包含更多的接收缓冲区指针，从而使得NIC可以从网络传输更大的帧。根据NIC硬件，如果修改了CQE大小，可以在驱动程序中调整整体完成队列的大小。
### CHANNELS_GET
============

获取类似于 `ETHTOOL_GCHANNELS` ioctl 请求的通道数量。
请求内容：

  - `ETHTOOL_A_CHANNELS_HEADER`：嵌套请求头

内核响应内容：

  - `ETHTOOL_A_CHANNELS_HEADER`：嵌套响应头
  - `ETHTOOL_A_CHANNELS_RX_MAX`：u32 最大接收通道数
  - `ETHTOOL_A_CHANNELS_TX_MAX`：u32 最大发送通道数
  - `ETHTOOL_A_CHANNELS_OTHER_MAX`：u32 最大其他通道数
  - `ETHTOOL_A_CHANNELS_COMBINED_MAX`：u32 最大组合通道数
  - `ETHTOOL_A_CHANNELS_RX_COUNT`：u32 接收通道数
  - `ETHTOOL_A_CHANNELS_TX_COUNT`：u32 发送通道数
  - `ETHTOOL_A_CHANNELS_OTHER_COUNT`：u32 其他通道数
  - `ETHTOOL_A_CHANNELS_COMBINED_COUNT`：u32 组合通道数

### CHANNELS_SET
============

设置类似于 `ETHTOOL_SCHANNELS` ioctl 请求的通道数量。
请求内容：

  - `ETHTOOL_A_CHANNELS_HEADER`：嵌套请求头
  - `ETHTOOL_A_CHANNELS_RX_COUNT`：u32 接收通道数
  - `ETHTOOL_A_CHANNELS_TX_COUNT`：u32 发送通道数
  - `ETHTOOL_A_CHANNELS_OTHER_COUNT`：u32 其他通道数
  - `ETHTOOL_A_CHANNELS_COMBINED_COUNT`：u32 组合通道数

内核会检查请求的通道数量是否超过由驱动程序报告的限制。驱动程序可能施加额外的约束，并且可能不支持所有属性。

### COALESCE_GET
============

获取类似于 `ETHTOOL_GCOALESCE` ioctl 请求的合并参数。
请求内容：

  - `ETHTOOL_A_COALESCE_HEADER`：嵌套请求头

内核响应内容：

  - `ETHTOOL_A_COALESCE_HEADER`：嵌套响应头
  - `ETHTOOL_A_COALESCE_RX_USECS`：u32 延迟（微秒），正常接收
  - `ETHTOOL_A_COALESCE_RX_MAX_FRAMES`：u32 最大包数，正常接收
  - `ETHTOOL_A_COALESCE_RX_USECS_IRQ`：u32 延迟（微秒），IRQ 中接收
  - `ETHTOOL_A_COALESCE_RX_MAX_FRAMES_IRQ`：u32 最大包数，IRQ 中接收
  - `ETHTOOL_A_COALESCE_TX_USECS`：u32 延迟（微秒），正常发送
  - `ETHTOOL_A_COALESCE_TX_MAX_FRAMES`：u32 最大包数，正常发送
  - `ETHTOOL_A_COALESCE_TX_USECS_IRQ`：u32 延迟（微秒），IRQ 中发送
  - `ETHTOOL_A_COALESCE_TX_MAX_FRAMES_IRQ`：u32 IRQ 包数，IRQ 中发送
  - `ETHTOOL_A_COALESCE_STATS_BLOCK_USECS`：u32 统计更新延迟
  - `ETHTOOL_A_COALESCE_USE_ADAPTIVE_RX`：bool 自适应接收合并
  - `ETHTOOL_A_COALESCE_USE_ADAPTIVE_TX`：bool 自适应发送合并
  - `ETHTOOL_A_COALESCE_PKT_RATE_LOW`：u32 低速率阈值
  - `ETHTOOL_A_COALESCE_RX_USECS_LOW`：u32 延迟（微秒），低速率接收
  - `ETHTOOL_A_COALESCE_RX_MAX_FRAMES_LOW`：u32 最大包数，低速率接收
  - `ETHTOOL_A_COALESCE_TX_USECS_LOW`：u32 延迟（微秒），低速率发送
  - `ETHTOOL_A_COALESCE_TX_MAX_FRAMES_LOW`：u32 最大包数，低速率发送
  - `ETHTOOL_A_COALESCE_PKT_RATE_HIGH`：u32 高速率阈值
  - `ETHTOOL_A_COALESCE_RX_USECS_HIGH`：u32 延迟（微秒），高速率接收
  - `ETHTOOL_A_COALESCE_RX_MAX_FRAMES_HIGH`：u32 最大包数，高速率接收
  - `ETHTOOL_A_COALESCE_TX_USECS_HIGH`：u32 延迟（微秒），高速率发送
  - `ETHTOOL_A_COALESCE_TX_MAX_FRAMES_HIGH`：u32 最大包数，高速率发送
  - `ETHTOOL_A_COALESCE_RATE_SAMPLE_INTERVAL`：u32 速率采样间隔
  - `ETHTOOL_A_COALESCE_USE_CQE_TX`：bool 定时器重置模式，发送
  - `ETHTOOL_A_COALESCE_USE_CQE_RX`：bool 定时器重置模式，接收
  - `ETHTOOL_A_COALESCE_TX_AGGR_MAX_BYTES`：u32 最大聚合大小，发送
  - `ETHTOOL_A_COALESCE_TX_AGGR_MAX_FRAMES`：u32 最大聚合包数，发送
  - `ETHTOOL_A_COALESCE_TX_AGGR_TIME_USECS`：u32 时间（微秒），聚合，发送
  - `ETHTOOL_A_COALESCE_RX_PROFILE`：嵌套接收配置文件
  - `ETHTOOL_A_COALESCE_TX_PROFILE`：嵌套发送配置文件

只有当属性值非零或在 `ethtool_ops::supported_coalesce_params` 中对应的位被设置（即它们被驱动程序声明为支持）时，这些属性才会包含在响应中。

定时器重置模式（`ETHTOOL_A_COALESCE_USE_CQE_TX` 和 `ETHTOOL_A_COALESCE_USE_CQE_RX`）控制包到达与各种基于时间的延迟参数之间的交互。默认情况下，定时器用于限制任何包到达/离开和相应中断之间的最大延迟。在这种模式下，定时器应由包到达（有时是前一个中断的传递）启动，并在中断传递时重置。

将相应的属性设置为 1 将启用 `CQE` 模式，在这种模式下，每个包事件都会重置定时器。在这种模式下，定时器用于在队列空闲时强制中断，而繁忙队列则依赖于包限制来触发中断。

发送聚合包括将帧复制到连续缓冲区中，以便可以作为一个单一的 I/O 操作提交。`ETHTOOL_A_COALESCE_TX_AGGR_MAX_BYTES` 描述了提交缓冲区的最大字节数。
`ETHTOOL_A_COALESCE_TX_AGGR_MAX_FRAMES` 描述了可以聚合到单个缓冲区中的最大帧数。
``ETHTOOL_A_COALESCE_TX_AGGR_TIME_USECS`` 表示自聚合块中第一个数据包到达以来的时间（以微秒为单位），在此时间之后应发送该块。
此功能主要针对某些无法很好地处理频繁小尺寸URB传输的USB设备。
``ETHTOOL_A_COALESCE_RX_PROFILE`` 和 ``ETHTOOL_A_COALESCE_TX_PROFILE`` 指向DIM参数，详见 `通用网络动态中断调节 (Net DIM) <https://www.kernel.org/doc/Documentation/networking/net_dim.rst>`_。

### COALESCE_SET

设置诸如 ``ETHTOOL_SCOALESCE`` ioctl请求那样的合并参数。
请求内容：

  ===========================================  ======  =======================
  ``ETHTOOL_A_COALESCE_HEADER``                nested  请求头
  ``ETHTOOL_A_COALESCE_RX_USECS``              u32     延迟（μs），普通接收
  ``ETHTOOL_A_COALESCE_RX_MAX_FRAMES``         u32     最大包数，普通接收
  ``ETHTOOL_A_COALESCE_RX_USECS_IRQ``          u32     延迟（μs），IRQ中的接收
  ``ETHTOOL_A_COALESCE_RX_MAX_FRAMES_IRQ``     u32     最大包数，IRQ中的接收
  ``ETHTOOL_A_COALESCE_TX_USECS``              u32     延迟（μs），普通发送
  ``ETHTOOL_A_COALESCE_TX_MAX_FRAMES``         u32     最大包数，普通发送
  ``ETHTOOL_A_COALESCE_TX_USECS_IRQ``          u32     延迟（μs），IRQ中的发送
  ``ETHTOOL_A_COALESCE_TX_MAX_FRAMES_IRQ``     u32     IRQ中的包数，IRQ中的发送
  ``ETHTOOL_A_COALESCE_STATS_BLOCK_USECS``     u32     统计更新延迟
  ``ETHTOOL_A_COALESCE_USE_ADAPTIVE_RX``       bool    自适应接收合并
  ``ETHTOOL_A_COALESCE_USE_ADAPTIVE_TX``       bool    自适应发送合并
  ``ETHTOOL_A_COALESCE_PKT_RATE_LOW``          u32     低速率阈值
  ``ETHTOOL_A_COALESCE_RX_USECS_LOW``          u32     延迟（μs），低速率接收
  ``ETHTOOL_A_COALESCE_RX_MAX_FRAMES_LOW``     u32     最大包数，低速率接收
  ``ETHTOOL_A_COALESCE_TX_USECS_LOW``          u32     延迟（μs），低速率发送
  ``ETHTOOL_A_COALESCE_TX_MAX_FRAMES_LOW``     u32     最大包数，低速率发送
  ``ETHTOOL_A_COALESCE_PKT_RATE_HIGH``         u32     高速率阈值
  ``ETHTOOL_A_COALESCE_RX_USECS_HIGH``         u32     延迟（μs），高速率接收
  ``ETHTOOL_A_COALESCE_RX_MAX_FRAMES_HIGH``    u32     最大包数，高速率接收
  ``ETHTOOL_A_COALESCE_TX_USECS_HIGH``         u32     延迟（μs），高速率发送
  ``ETHTOOL_A_COALESCE_TX_MAX_FRAMES_HIGH``    u32     最大包数，高速率发送
  ``ETHTOOL_A_COALESCE_RATE_SAMPLE_INTERVAL``  u32     速率采样间隔
  ``ETHTOOL_A_COALESCE_USE_CQE_TX``            bool    定时器重置模式，发送
  ``ETHTOOL_A_COALESCE_USE_CQE_RX``            bool    定时器重置模式，接收
  ``ETHTOOL_A_COALESCE_TX_AGGR_MAX_BYTES``     u32     最大聚合大小，发送
  ``ETHTOOL_A_COALESCE_TX_AGGR_MAX_FRAMES``    u32     最大聚合包数，发送
  ``ETHTOOL_A_COALESCE_TX_AGGR_TIME_USECS``    u32     时间（μs），聚合，发送
  ``ETHTOOL_A_COALESCE_RX_PROFILE``            nested  DIM配置文件，接收
  ``ETHTOOL_A_COALESCE_TX_PROFILE``            nested  DIM配置文件，发送
  ===========================================  ======  =======================

如果驱动程序声明了这些属性不支持（即相应的位在 ``ethtool_ops::supported_coalesce_params`` 中未被设置），则无论其值如何，请求都将被拒绝。驱动程序可能会对合并参数及其值施加额外的限制。
与通过 ``ioctl()`` 发出的请求相比，netlink版本的此请求将更加努力地确保用户指定的值已应用，并且可能会调用两次驱动程序。

### PAUSE_GET

获取类似于 ``ETHTOOL_GPAUSEPARAM`` ioctl请求的暂停帧设置。
请求内容：

  =====================================  ======  ==========================
  ``ETHTOOL_A_PAUSE_HEADER``             nested  请求头
  ``ETHTOOL_A_PAUSE_STATS_SRC``          u32     统计信息来源
  =====================================  ======  ==========================

``ETHTOOL_A_PAUSE_STATS_SRC`` 是可选的。它取值自：

.. kernel-doc:: include/uapi/linux/ethtool.h
    :identifiers: ethtool_mac_stats_src

如果请求中没有提供，则响应中将包含一个 ``ETHTOOL_A_PAUSE_STATS_SRC`` 属性，其值等于 ``ETHTOOL_MAC_STATS_SRC_AGGREGATE``。
内核响应内容：

  =====================================  ======  ==========================
  ``ETHTOOL_A_PAUSE_HEADER``             nested  请求头
  ``ETHTOOL_A_PAUSE_AUTONEG``            bool    暂停自动协商
  ``ETHTOOL_A_PAUSE_RX``                 bool    接收暂停帧
  ``ETHTOOL_A_PAUSE_TX``                 bool    发送暂停帧
  ``ETHTOOL_A_PAUSE_STATS``              nested  暂停统计信息
  =====================================  ======  ==========================

如果在 ``ETHTOOL_A_HEADER_FLAGS`` 中设置了 ``ETHTOOL_FLAG_STATS``，则会报告 ``ETHTOOL_A_PAUSE_STATS``。
如果驱动程序未报告任何统计信息，则该字段将为空。驱动程序以以下结构填写统计信息：

.. kernel-doc:: include/linux/ethtool.h
    :identifiers: ethtool_pause_stats

每个成员都有一个对应的属性定义。

### PAUSE_SET
设置暂停参数，类似于 `ETHTOOL_GPAUSEPARAM` ioctl 请求。
请求内容：

  =====================================  ======  ==========================
  ``ETHTOOL_A_PAUSE_HEADER``             嵌套     请求头
  ``ETHTOOL_A_PAUSE_AUTONEG``            布尔     暂停自动协商
  ``ETHTOOL_A_PAUSE_RX``                 布尔     接收暂停帧
  ``ETHTOOL_A_PAUSE_TX``                 布尔     发送暂停帧
  =====================================  ======  ==========================

### EEE_GET
获取类似 `ETHTOOL_GEEE` ioctl 请求的节能以太网（EEE）设置。
请求内容：

  =====================================  ======  ==========================
  ``ETHTOOL_A_EEE_HEADER``               嵌套     请求头
  =====================================  ======  ==========================

内核响应内容：

  =====================================  ======  ==========================
  ``ETHTOOL_A_EEE_HEADER``               嵌套     请求头
  ``ETHTOOL_A_EEE_MODES_OURS``           布尔     支持/宣传的模式
  ``ETHTOOL_A_EEE_MODES_PEER``           布尔     对端宣传的链路模式
  ``ETHTOOL_A_EEE_ACTIVE``               布尔     EEE 正在使用
  ``ETHTOOL_A_EEE_ENABLED``              布尔     EEE 已启用
  ``ETHTOOL_A_EEE_TX_LPI_ENABLED``       布尔     启用 Tx LPI
  ``ETHTOOL_A_EEE_TX_LPI_TIMER``         u32      Tx LPI 超时时间（微秒）
  =====================================  ======  ==========================

在 ``ETHTOOL_A_EEE_MODES_OURS`` 中，掩码由启用了 EEE 的链路模式组成，值表示宣传了 EEE 的链路模式。对端宣传了 EEE 的链路模式列在 ``ETHTOOL_A_EEE_MODES_PEER`` 中（无掩码）。Netlink 接口允许报告所有链路模式的 EEE 状态，但只有前 32 个由 `ethtool_ops` 回调提供。

### EEE_SET
设置类似 `ETHTOOL_SEEE` ioctl 请求的节能以太网（EEE）参数。
请求内容：

  =====================================  ======  ==========================
  ``ETHTOOL_A_EEE_HEADER``               嵌套     请求头
  ``ETHTOOL_A_EEE_MODES_OURS``           布尔     宣传的模式
  ``ETHTOOL_A_EEE_ENABLED``              布尔     EEE 已启用
  ``ETHTOOL_A_EEE_TX_LPI_ENABLED``       布尔     启用 Tx LPI
  ``ETHTOOL_A_EEE_TX_LPI_TIMER``         u32      Tx LPI 超时时间（微秒）
  =====================================  ======  ==========================

``ETHTOOL_A_EEE_MODES_OURS`` 用于列出要宣传 EEE 的链路模式（如果没有掩码），或指定列表中的更改（如果有掩码）。Netlink 接口允许报告所有链路模式的 EEE 状态，但目前只能设置前 32 个，因为 `ethtool_ops` 回调仅支持这些。

### TSINFO_GET
获取类似 `ETHTOOL_GET_TS_INFO` ioctl 请求的时间戳信息。
请求内容：

  =====================================  ======  ==========================
  ``ETHTOOL_A_TSINFO_HEADER``            嵌套     请求头
  =====================================  ======  ==========================

内核响应内容：

  =====================================  ======  ==========================
  ``ETHTOOL_A_TSINFO_HEADER``            嵌套     请求头
  ``ETHTOOL_A_TSINFO_TIMESTAMPING``      位集     SO_TIMESTAMPING 标志
  ``ETHTOOL_A_TSINFO_TX_TYPES``          位集     支持的 Tx 类型
  ``ETHTOOL_A_TSINFO_RX_FILTERS``        位集     支持的 Rx 过滤器
  ``ETHTOOL_A_TSINFO_PHC_INDEX``         u32      PTP 硬件时钟索引
  ``ETHTOOL_A_TSINFO_STATS``             嵌套     硬件时间戳统计信息
  =====================================  ======  ==========================

如果不存在关联的 PHC（没有特殊值用于这种情况），则不会包含 ``ETHTOOL_A_TSINFO_PHC_INDEX``。如果位集为空（没有设置位），则会省略位集属性。

额外的硬件时间戳统计信息响应内容：

  =====================================  ======  ===================================
  ``ETHTOOL_A_TS_STAT_TX_PKTS``          uint    具有 Tx 硬件时间戳的报文数
  ``ETHTOOL_A_TS_STAT_TX_LOST``          uint    未到达的 Tx 硬件时间戳计数
  ``ETHTOOL_A_TS_STAT_TX_ERR``           uint    请求 Tx 时间戳的硬件错误计数
  =====================================  ======  ===================================

### CABLE_TEST
开始电缆测试。
请求内容：

  ====================================  ======  ==========================
  ``ETHTOOL_A_CABLE_TEST_HEADER``       嵌套     请求头
  ====================================  ======  ==========================

通知内容：
一条以太网电缆通常包含 1、2 或 4 对线。只有当一对线中存在故障并因此产生反射时，才能测量这对线的长度。根据特定硬件的不同，可能无法获得关于故障的信息。因此，通知消息的内容大多是可选的。这些属性可以重复任意次数，以任意顺序，为任意数量的对线提供。
示例展示了在完成T2电缆（即两对线）测试时发送的通知。一对正常，因此没有长度信息；第二对有故障，并且具有长度信息。

+---------------------------------------------+--------+---------------------+
| ``ETHTOOL_A_CABLE_TEST_HEADER``             | 嵌套    | 回复头              |
+---------------------------------------------+--------+---------------------+
| ``ETHTOOL_A_CABLE_TEST_STATUS``             | u8     | 完成                |
+---------------------------------------------+--------+---------------------+
| ``ETHTOOL_A_CABLE_TEST_NTF_NEST``           | 嵌套    | 所有结果            |
+-+-------------------------------------------+--------+---------------------+
 | ``ETHTOOL_A_CABLE_NEST_RESULT``            | 嵌套    | 电缆测试结果         |
 +-+-+-----------------------------------------+--------+---------------------+
  | ``ETHTOOL_A_CABLE_RESULTS_PAIR``          | u8     | 线对编号            |
 +-+-+-----------------------------------------+--------+---------------------+
  | ``ETHTOOL_A_CABLE_RESULTS_CODE``          | u8     | 结果代码            |
 +-+-+-----------------------------------------+--------+---------------------+
 | ``ETHTOOL_A_CABLE_NEST_RESULT``            | 嵌套    | 电缆测试结果         |
 +-+-+-----------------------------------------+--------+---------------------+
  | ``ETHTOOL_A_CABLE_RESULTS_PAIR``          | u8     | 线对编号            |
 +-+-+-----------------------------------------+--------+---------------------+
  | ``ETHTOOL_A_CABLE_RESULTS_CODE``          | u8     | 结果代码            |
 +-+-+-----------------------------------------+--------+---------------------+
 | ``ETHTOOL_A_CABLE_NEST_FAULT_LENGTH``      | 嵌套    | 电缆长度            |
 +-+-+-----------------------------------------+--------+---------------------+
  | ``ETHTOOL_A_CABLE_FAULT_LENGTH_PAIR``     | u8     | 线对编号            |
 +-+-+-----------------------------------------+--------+---------------------+
  | ``ETHTOOL_A_CABLE_FAULT_LENGTH_CM``       | u32    | 长度（厘米）         |
 +-+-+-----------------------------------------+--------+---------------------+

### CABLE_TEST TDR

开始电缆测试并报告原始TDR数据

请求内容：

+--------------------------------------------+--------+-----------------------+
| ``ETHTOOL_A_CABLE_TEST_TDR_HEADER``        | 嵌套    | 回复头                |
+--------------------------------------------+--------+-----------------------+
| ``ETHTOOL_A_CABLE_TEST_TDR_CFG``           | 嵌套    | 测试配置              |
+-+------------------------------------------+--------+-----------------------+
 | ``ETHTOOL_A_CABLE_STEP_FIRST_DISTANCE``   | u32    | 第一个数据距离         |
 +-+-+----------------------------------------+--------+-----------------------+
 | ``ETHTOOL_A_CABLE_STEP_LAST_DISTANCE``    | u32    | 最后一个数据距离       |
 +-+-+----------------------------------------+--------+-----------------------+
 | ``ETHTOOL_A_CABLE_STEP_STEP_DISTANCE``    | u32    | 每步的距离            |
 +-+-+----------------------------------------+--------+-----------------------+
 | ``ETHTOOL_A_CABLE_TEST_TDR_CFG_PAIR``     | u8     | 要测试的线对          |
 +-+-+----------------------------------------+--------+-----------------------+

``ETHTOOL_A_CABLE_TEST_TDR_CFG``是可选的，以及所有嵌套成员。所有距离以厘米表示。PHY将这些距离作为参考，并四舍五入到其实际支持的最近距离。如果指定了一个线对，则仅测试该线对。否则测试所有线对。

通知内容：

通过向电缆发送脉冲并记录反射脉冲的幅度来收集原始TDR数据。收集TDR数据可能需要几秒钟的时间，特别是当以1米间隔探测全长100米时。当测试开始时，将发送包含``ETHTOOL_A_CABLE_TEST_TDR_STATUS``和值为``ETHTOOL_A_CABLE_TEST_NTF_STATUS_STARTED``的通知。当测试完成时，将发送第二个通知，包含``ETHTOOL_A_CABLE_TEST_TDR_STATUS``和值为``ETHTOOL_A_CABLE_TEST_NTF_STATUS_COMPLETED``以及TDR数据。消息可选择性地包含发送到电缆中的脉冲幅度。这以毫伏（mV）为单位测量。反射幅度不应超过传输脉冲的幅度。

在原始TDR数据之前应有一个``ETHTOOL_A_CABLE_TDR_NEST_STEP``嵌套，包含第一次读取、最后一次读取及每次读取之间的步长信息。距离以厘米表示。这些应该是PHY实际使用的精确值。如果原生测量分辨率大于1厘米，这些值可能与用户请求的不同。

对于电缆上的每个步骤，使用``ETHTOOL_A_CABLE_TDR_NEST_AMPLITUDE``来报告给定线对的反射幅度。
+---------------------------------------------+--------+----------------------+
 | ``ETHTOOL_A_CABLE_TEST_TDR_HEADER``         | 嵌套    | 回复头               |
 +---------------------------------------------+--------+----------------------+
 | ``ETHTOOL_A_CABLE_TEST_TDR_STATUS``         | u8     | 完成                 |
 +---------------------------------------------+--------+----------------------+
 | ``ETHTOOL_A_CABLE_TEST_TDR_NTF_NEST``       | 嵌套    | 所有结果             |
 +-+-------------------------------------------+--------+----------------------+
  | ``ETHTOOL_A_CABLE_TDR_NEST_PULSE``         | 嵌套    | 发射脉冲幅度          |
 +-+-+-----------------------------------------+--------+----------------------+
   | ``ETHTOOL_A_CABLE_PULSE_mV``              | s16    | 脉冲幅度             |
 +-+-+-----------------------------------------+--------+----------------------+
  | ``ETHTOOL_A_CABLE_NEST_STEP``              | 嵌套    | TDR步骤信息           |
 +-+-+-----------------------------------------+--------+----------------------+
   | ``ETHTOOL_A_CABLE_STEP_FIRST_DISTANCE``   | u32    | 第一个数据距离        |
 +-+-+-----------------------------------------+--------+----------------------+
   | ``ETHTOOL_A_CABLE_STEP_LAST_DISTANCE``    | u32    | 最后一个数据距离      |
 +-+-+-----------------------------------------+--------+----------------------+
   | ``ETHTOOL_A_CABLE_STEP_STEP_DISTANCE``    | u32    | 每步的距离           |
 +-+-+-----------------------------------------+--------+----------------------+
  | ``ETHTOOL_A_CABLE_TDR_NEST_AMPLITUDE``     | 嵌套    | 反射幅度             |
 +-+-+-----------------------------------------+--------+----------------------+
   | ``ETHTOOL_A_CABLE_RESULTS_PAIR``          | u8     | 线对编号             |
 +-+-+-----------------------------------------+--------+----------------------+
   | ``ETHTOOL_A_CABLE_AMPLITUDE_mV``          | s16    | 反射幅度             |
 +-+-+-----------------------------------------+--------+----------------------+
  | ``ETHTOOL_A_CABLE_TDR_NEST_AMPLITUDE``     | 嵌套    | 反射幅度             |
 +-+-+-----------------------------------------+--------+----------------------+
   | ``ETHTOOL_A_CABLE_RESULTS_PAIR``          | u8     | 线对编号             |
 +-+-+-----------------------------------------+--------+----------------------+
   | ``ETHTOOL_A_CABLE_AMPLITUDE_mV``          | s16    | 反射幅度             |
 +-+-+-----------------------------------------+--------+----------------------+
  | ``ETHTOOL_A_CABLE_TDR_NEST_AMPLITUDE``     | 嵌套    | 反射幅度             |
 +-+-+-----------------------------------------+--------+----------------------+
   | ``ETHTOOL_A_CABLE_RESULTS_PAIR``          | u8     | 线对编号             |
 +-+-+-----------------------------------------+--------+----------------------+
   | ``ETHTOOL_A_CABLE_AMPLITUDE_mV``          | s16    | 反射幅度             |
 +-+-+-----------------------------------------+--------+----------------------+

### TUNNEL_INFO

获取NIC已知的隧道状态信息

请求内容：

  =====================================  ======  ==========================
  ``ETHTOOL_A_TUNNEL_INFO_HEADER``       嵌套    | 请求头
  =====================================  ======  ==========================

内核响应内容：

+---------------------------------------------+--------+---------------------+
| ``ETHTOOL_A_TUNNEL_INFO_HEADER``            | 嵌套    | 回复头              |
+---------------------------------------------+--------+---------------------+
| ``ETHTOOL_A_TUNNEL_INFO_UDP_PORTS``         | 嵌套    | 所有UDP端口表        |
+-+-------------------------------------------+--------+---------------------+
 | ``ETHTOOL_A_TUNNEL_UDP_TABLE``             | 嵌套    | 一个UDP端口表        |
 +-+-+-----------------------------------------+--------+---------------------+
  | ``ETHTOOL_A_TUNNEL_UDP_TABLE_SIZE``       | u32    | 表的最大大小         |
 +-+-+-----------------------------------------+--------+---------------------+
  | ``ETHTOOL_A_TUNNEL_UDP_TABLE_TYPES``      | 位图   | 表可以容纳的隧道类型 |
 +-+-+-----------------------------------------+--------+---------------------+
  | ``ETHTOOL_A_TUNNEL_UDP_TABLE_ENTRY``      | 嵌套    | 卸载的UDP端口        |
 +-+-+-+---------------------------------------+--------+---------------------+
   | ``ETHTOOL_A_TUNNEL_UDP_ENTRY_PORT``      | be16   | UDP端口              |
 +-+-+-+---------------------------------------+--------+---------------------+
   | ``ETHTOOL_A_TUNNEL_UDP_ENTRY_TYPE``      | u32    | 隧道类型             |
 +-+-+-+---------------------------------------+--------+---------------------+

对于空的UDP隧道表，“ETHTOOL_A_TUNNEL_UDP_TABLE_TYPES”为空表示表中包含静态条目，由NIC硬编码。
### FEC_GET
获取FEC配置和状态，类似于`ETHTOOL_GFECPARAM` ioctl请求。
请求内容：

  - `ETHTOOL_A_FEC_HEADER`   嵌套   请求头

内核响应内容：

  - `ETHTOOL_A_FEC_HEADER`   嵌套   请求头
  - `ETHTOOL_A_FEC_MODES`    位集   配置的模式
  - `ETHTOOL_A_FEC_AUTO`     布尔值   FEC模式自动选择
  - `ETHTOOL_A_FEC_ACTIVE`   u32   当前激活的FEC模式索引
  - `ETHTOOL_A_FEC_STATS`    嵌套   FEC统计信息

`ETHTOOL_A_FEC_ACTIVE` 是当前接口上激活的FEC链路模式的位索引。如果设备不支持FEC，则此属性可能不存在。
`ETHTOOL_A_FEC_MODES` 和 `ETHTOOL_A_FEC_AUTO` 只有在禁用自动协商时才有意义。如果 `ETHTOOL_A_FEC_AUTO` 不为零，则驱动程序将根据SFP模块的参数自动选择FEC模式。
这等同于 ioctl 接口中的 `ETHTOOL_FEC_AUTO` 位。
`ETHTOOL_A_FEC_MODES` 使用链路模式位（而非旧的 `ETHTOOL_FEC_*` 位）来表示当前的FEC配置。
如果在 `ETHTOOL_A_HEADER_FLAGS` 中设置了 `ETHTOOL_FLAG_STATS` 标志，则会报告 `ETHTOOL_A_FEC_STATS`。
每个属性包含一个64位统计信息数组。数组的第一个条目包含端口上的总事件数，随后的条目对应于车道/PCS实例的计数器。数组中的条目数量如下表所示：

+--------------+---------------------------------------------+
| `0`          | 设备不支持FEC统计信息                        |
+--------------+---------------------------------------------+
| `1`          | 设备不支持按车道细分                        |
+--------------+---------------------------------------------+
| `1 + #lanes` | 设备完全支持FEC统计信息                      |
+--------------+---------------------------------------------+

驱动程序按照以下结构填充统计信息：

.. kernel-doc:: include/linux/ethtool.h
    :identifiers: ethtool_fec_stats

### FEC_SET
设置FEC参数，类似于 `ETHTOOL_SFECPARAM` ioctl请求。
请求内容：

  - `ETHTOOL_A_FEC_HEADER`   嵌套   请求头
  - `ETHTOOL_A_FEC_MODES`    位集   配置的模式
  - `ETHTOOL_A_FEC_AUTO`     布尔值   FEC模式自动选择

`FEC_SET` 只有在禁用自动协商时才有意义。否则，FEC模式作为自动协商的一部分被选择。
`ETHTOOL_A_FEC_MODES` 用于选择应使用的FEC模式。建议仅设置一个位，如果设置了多个位，驱动程序可能会以实现特定的方式在它们之间进行选择。
`ETHTOOL_A_FEC_AUTO` 请求驱动程序根据SFP模块参数选择FEC模式。这并不意味着自动协商。
### MODULE_EEPROM_GET
获取模块的EEPROM数据转储
此接口设计为一次最多转储半个页面的数据。这意味着只允许转储128字节（或更少）的数据，且不得跨越位于偏移量128处的半页边界。对于非0页面，只能访问高128字节。
请求内容：

| 字段名                           | 类型    | 描述                                    |
|----------------------------------|---------|-----------------------------------------|
| `ETHTOOL_A_MODULE_EEPROM_HEADER` | 嵌套    | 请求头                                   |
| `ETHTOOL_A_MODULE_EEPROM_OFFSET` | u32     | 页面内的偏移量                            |
| `ETHTOOL_A_MODULE_EEPROM_LENGTH` | u32     | 要读取的字节数                            |
| `ETHTOOL_A_MODULE_EEPROM_PAGE`   | u8      | 页面编号                                 |
| `ETHTOOL_A_MODULE_EEPROM_BANK`   | u8      | 银行编号                                 |
| `ETHTOOL_A_MODULE_EEPROM_I2C_ADDRESS` | u8 | 页面I2C地址                              |

如果未指定`ETHTOOL_A_MODULE_EEPROM_BANK`，则默认使用银行0。
内核响应内容：

| 字段名                           | 类型    | 描述                                  |
|----------------------------------|---------|---------------------------------------|
| `ETHTOOL_A_MODULE_EEPROM_HEADER` | 嵌套    | 响应头                                 |
| `ETHTOOL_A_MODULE_EEPROM_DATA`   | 二进制  | 模块EEPROM中的字节数组                 |

`ETHTOOL_A_MODULE_EEPROM_DATA`的属性长度等于驱动程序实际读取的字节数。

### STATS_GET
获取接口的标准统计信息。注意这不是对`ETHTOOL_GSTATS`的重新实现，后者暴露了由驱动程序定义的统计信息。
请求内容：

| 字段名                           | 类型    | 描述                                        |
|----------------------------------|---------|---------------------------------------------|
| `ETHTOOL_A_STATS_HEADER`         | 嵌套    | 请求头                                      |
| `ETHTOOL_A_STATS_SRC`            | u32     | 统计信息的来源                               |
| `ETHTOOL_A_STATS_GROUPS`         | 位图    | 请求的统计信息组                             |

内核响应内容：

| 字段名                           | 类型    | 描述                                      |
|----------------------------------|---------|-------------------------------------------|
| `ETHTOOL_A_STATS_HEADER`         | 嵌套    | 响应头                                     |
| `ETHTOOL_A_STATS_SRC`            | u32     | 统计信息的来源                              |
| `ETHTOOL_A_STATS_GRP`            | 嵌套    | 一个或多个统计信息组                         |
| `-`                              |         |                                           |
| `ETHTOOL_A_STATS_GRP_ID`         | u32     | 组ID - `ETHTOOL_STATS_*`                    |
| `ETHTOOL_A_STATS_GRP_SS_ID`      | u32     | 名称的字符串集ID                            |
| `ETHTOOL_A_STATS_GRP_STAT`       | 嵌套    | 包含一个统计信息的嵌套                       |
| `ETHTOOL_A_STATS_GRP_HIST_RX`    | 嵌套    | 历史统计信息（接收方向）                     |
| `ETHTOOL_A_STATS_GRP_HIST_TX`    | 嵌套    | 历史统计信息（发送方向）                     |

用户通过`ETHTOOL_A_STATS_GROUPS`位图指定请求哪些统计信息组。目前定义的值如下：

| 统计信息组                | 缩写    | 描述                                       |
|---------------------------|---------|--------------------------------------------|
| `ETHTOOL_STATS_ETH_MAC`   | eth-mac | 基本IEEE 802.3 MAC统计信息（30.3.1.1.*）    |
| `ETHTOOL_STATS_ETH_PHY`   | eth-phy | 基本IEEE 802.3 PHY统计信息（30.3.2.1.*）    |
| `ETHTOOL_STATS_ETH_CTRL`  | eth-ctrl| 基本IEEE 802.3 MAC控制统计信息（30.3.3.*）  |
| `ETHTOOL_STATS_RMON`      | rmon    | RMON（RFC 2819）统计信息                     |

每个组在响应中应有一个对应的`ETHTOOL_A_STATS_GRP`。
`ETHTOOL_A_STATS_GRP_ID`标识哪个组的统计信息嵌套。
`ETHTOOL_A_STATS_GRP_SS_ID`标识该组统计信息名称的字符串集ID（如果可用）。
统计信息被添加到`ETHTOOL_A_STATS_GRP`嵌套下的`ETHTOOL_A_STATS_GRP_STAT`中。
`ETHTOOL_A_STATS_GRP_STAT`应包含一个8字节（u64）的属性 - 该属性的类型是统计信息ID，值是统计信息的值。
每个组对统计信息ID有自己的解释。
属性ID对应由`ETHTOOL_A_STATS_GRP_SS_ID`标识的字符串集中的字符串。复杂的统计信息（如RMON直方图条目）也列在`ETHTOOL_A_STATS_GRP`中，并且在字符串集中没有定义字符串。
RMON "直方图"计数器计算特定大小范围内的数据包数量。由于RFC没有指定超出标准1518 MTU的范围，因此设备在桶的定义上有所不同。出于这个原因，数据包范围的定义留给每个驱动程序。
`ETHTOOL_A_STATS_GRP_HIST_RX`和`ETHTOOL_A_STATS_GRP_HIST_TX`嵌套结构包含以下属性：

| 属性名称 | 类型   | 描述                   |
|----------|--------|------------------------|
| ETHTOOL_A_STATS_RMON_HIST_BKT_LOW | u32 | 数据包大小桶的下限 |
| ETHTOOL_A_STATS_RMON_HIST_BKT_HI  | u32 | 桶的上限           |
| ETHTOOL_A_STATS_RMON_HIST_VAL     | u64 | 数据包计数         |

下限和上限是包含在内的，例如：

| RFC统计项              | 下限 | 上限 |
|-----------------------|------|------|
| etherStatsPkts64Octets | 0    | 64   |
| etherStatsPkts512to1023Octets | 512 | 1023 |

`ETHTOOL_A_STATS_SRC`是可选的。类似于`PAUSE_GET`，它取值自`enum ethtool_mac_stats_src`。如果请求中缺少该属性，则响应中将提供一个等于`ETHTOOL_MAC_STATS_SRC_AGGREGATE`的`ETHTOOL_A_STATS_SRC`属性。

### PHC_VCLOCKS_GET

查询设备PHC虚拟时钟信息
请求内容：

| 属性名称                         | 类型   | 描述         |
|----------------------------------|--------|--------------|
| `ETHTOOL_A_PHC_VCLOCKS_HEADER`   | 嵌套   | 请求头       |

内核响应内容：

| 属性名称                         | 类型   | 描述                     |
|----------------------------------|--------|--------------------------|
| `ETHTOOL_A_PHC_VCLOCKS_HEADER`   | 嵌套   | 响应头                  |
| `ETHTOOL_A_PHC_VCLOCKS_NUM`      | u32    | PHC虚拟时钟数量          |
| `ETHTOOL_A_PHC_VCLOCKS_INDEX`    | s32[]  | PHC索引数组              |

### MODULE_GET

获取收发器模块参数
请求内容：

| 属性名称                         | 类型   | 描述         |
|----------------------------------|--------|--------------|
| `ETHTOOL_A_MODULE_HEADER`        | 嵌套   | 请求头       |

内核响应内容：

| 属性名称                         | 类型   | 描述                     |
|----------------------------------|--------|--------------------------|
| `ETHTOOL_A_MODULE_HEADER`        | 嵌套   | 响应头                  |
| `ETHTOOL_A_MODULE_POWER_MODE_POLICY` | u8 | 功率模式策略          |
| `ETHTOOL_A_MODULE_POWER_MODE`    | u8 | 运行功率模式          |

可选的`ETHTOOL_A_MODULE_POWER_MODE_POLICY`属性编码了主机强制执行的收发器模块功率模式策略。默认策略取决于驱动程序，但推荐的默认值是“自动”，并且应该在新的驱动程序或不需要遵循传统行为的驱动程序中实现。
可选的`ETHTOOL_A_MODULE_POWER_MODE`属性编码了收发器模块的操作功率模式策略。仅当模块插入时才报告。可能的值为：

.. kernel-doc:: include/uapi/linux/ethtool.h
    :identifiers: ethtool_module_power_mode

### MODULE_SET

设置收发器模块参数
请求内容：

| 属性名称                         | 类型   | 描述                     |
|----------------------------------|--------|--------------------------|
| `ETHTOOL_A_MODULE_HEADER`        | 嵌套   | 请求头                  |
| `ETHTOOL_A_MODULE_POWER_MODE_POLICY` | u8 | 功率模式策略          |

当设置时，可选的`ETHTOOL_A_MODULE_POWER_MODE_POLICY`属性用于设置主机强制执行的收发器模块功率策略。可能的值为：

.. kernel-doc:: include/uapi/linux/ethtool.h
    :identifiers: ethtool_module_power_mode_policy

对于SFF-8636模块，根据规范修订版2.10a表6-10，低功耗模式由主机强制执行。
对于CMIS模块，根据规范修订版5.0表6-12，低功耗模式由主机强制执行。
PSE_GET
=======

获取PSE属性
请求内容：

  =====================================  ======  ==========================
  ``ETHTOOL_A_PSE_HEADER``               嵌套    请求头
  =====================================  ======  ==========================

内核响应内容：

  ==========================================  ======  =============================
  ``ETHTOOL_A_PSE_HEADER``                    嵌套    响应头
  ``ETHTOOL_A_PODL_PSE_ADMIN_STATE``             u32  PoDL PSE 功能的操作状态
  ``ETHTOOL_A_PODL_PSE_PW_D_STATUS``             u32  PoDL PSE 的电源检测状态
  ``ETHTOOL_A_C33_PSE_ADMIN_STATE``              u32  PoE PSE 功能的操作状态
  ``ETHTOOL_A_C33_PSE_PW_D_STATUS``              u32  PoE PSE 的电源检测状态
  ``ETHTOOL_A_C33_PSE_PW_CLASS``                 u32  PoE PSE 的电源等级
  ``ETHTOOL_A_C33_PSE_ACTUAL_PW``                u32  PoE PSE 实际消耗的功率
  ``ETHTOOL_A_C33_PSE_EXT_STATE``                u32  PoE PSE 的扩展电源状态
  ``ETHTOOL_A_C33_PSE_EXT_SUBSTATE``             u32  PoE PSE 的扩展子状态
  ``ETHTOOL_A_C33_PSE_AVAIL_PW_LIMIT``           u32  PoE PSE 当前配置的功率限制
  ``ETHTOOL_A_C33_PSE_PW_LIMIT_RANGES``       嵌套    支持的功率限制配置范围
  ==========================================  ======  =============================
当设置时，可选的 ``ETHTOOL_A_PODL_PSE_ADMIN_STATE`` 属性标识 PoDL PSE 功能的操作状态。使用 ``ETHTOOL_A_PODL_PSE_ADMIN_CONTROL`` 操作可以更改 PSE 功能的操作状态。此选项对应于 ``IEEE 802.3-2018`` 30.15.1.1.2 中的 aPoDLPSEAdminState。可能的值为：

.. kernel-doc:: include/uapi/linux/ethtool.h
    :identifiers: ethtool_podl_pse_admin_state

同样地，``ETHTOOL_A_C33_PSE_ADMIN_STATE`` 实现了 ``IEEE 802.3-2022`` 30.9.1.1.2 中的 aPSEAdminState。
.. kernel-doc:: include/uapi/linux/ethtool.h
    :identifiers: ethtool_c33_pse_admin_state

当设置时，可选的 ``ETHTOOL_A_PODL_PSE_PW_D_STATUS`` 属性标识 PoDL PSE 的电源检测状态。该状态取决于内部 PSE 状态机和自动 PD 分类支持。此选项对应于 ``IEEE 802.3-2018`` 30.15.1.1.3 中的 aPoDLPSEPowerDetectionStatus。可能的值为：

.. kernel-doc:: include/uapi/linux/ethtool.h
    :identifiers: ethtool_podl_pse_pw_d_status

同样地，``ETHTOOL_A_C33_PSE_ADMIN_PW_D_STATUS`` 实现了 ``IEEE 802.3-2022`` 30.9.1.1.5 中的 aPSEPowerDetectionStatus。
.. kernel-doc:: include/uapi/linux/ethtool.h
    :identifiers: ethtool_c33_pse_pw_d_status

当设置时，可选的 ``ETHTOOL_A_C33_PSE_PW_CLASS`` 属性标识 C33 PSE 的电源类别。这取决于 PSE 和 PD 之间协商的类别。此选项对应于 ``IEEE 802.3-2022`` 30.9.1.1.8 中的 aPSEPowerClassification。
当设置时，可选的 ``ETHTOOL_A_C33_PSE_ACTUAL_PW`` 属性标识实际功率（单位为 mW）。此选项对应于 ``IEEE 802.3-2022`` 30.9.1.1.23 中的 aPSEActualPower。
当设置时，可选的 ``ETHTOOL_A_C33_PSE_EXT_STATE`` 属性标识 C33 PSE 的扩展错误状态。可能的值为：

.. kernel-doc:: include/uapi/linux/ethtool.h
    :identifiers: ethtool_c33_pse_ext_state

当设置时，可选的 ``ETHTOOL_A_C33_PSE_EXT_SUBSTATE`` 属性标识 C33 PSE 的扩展错误状态。可能的值为：

.. kernel-doc:: include/uapi/linux/ethtool.h
    :identifiers: ethtool_c33_pse_ext_substate_class_num_events
		  ethtool_c33_pse_ext_substate_error_condition
		  ethtool_c33_pse_ext_substate_mr_pse_enable
		  ethtool_c33_pse_ext_substate_option_detect_ted
		  ethtool_c33_pse_ext_substate_option_vport_lim
		  ethtool_c33_pse_ext_substate_ovld_detected
		  ethtool_c33_pse_ext_substate_pd_dll_power_type
		  ethtool_c33_pse_ext_substate_power_not_available
		  ethtool_c33_pse_ext_substate_short_detected

当设置时，可选的 ``ETHTOOL_A_C33_PSE_AVAIL_PW_LIMIT`` 属性标识 C33 PSE 的功率限制（单位为 mW）。
当设置时，可选的嵌套属性 ``ETHTOOL_A_C33_PSE_PW_LIMIT_RANGES`` 通过 ``ETHTOOL_A_C33_PSE_PWR_VAL_LIMIT_RANGE_MIN`` 和 ``ETHTOOL_A_C33_PSE_PWR_VAL_LIMIT_RANGE_MAX`` 标识 C33 PSE 的功率限制范围。如果控制器使用固定类别，则最小值和最大值将相等。

PSE_SET
=======

设置 PSE 参数
请求内容：

  ======================================  ======  =============================
  ``ETHTOOL_A_PSE_HEADER``                嵌套    请求头
  ``ETHTOOL_A_PODL_PSE_ADMIN_CONTROL``       u32   控制 PoDL PSE 管理状态
  ``ETHTOOL_A_C33_PSE_ADMIN_CONTROL``        u32   控制 PSE 管理状态
  ``ETHTOOL_A_C33_PSE_AVAIL_PWR_LIMIT``      u32   控制 PoE PSE 可用功率限制
  ======================================  ======  =============================

当设置时，可选的 ``ETHTOOL_A_PODL_PSE_ADMIN_CONTROL`` 属性用于控制 PoDL PSE 管理功能。此选项实现了 ``IEEE 802.3-2018`` 的 30.15.1.2.1 acPoDLPSEAdminControl。参见 ``ETHTOOL_A_PODL_PSE_ADMIN_STATE`` 以获取支持的值。
同样的规则适用于 ``ETHTOOL_A_C33_PSE_ADMIN_CONTROL``，其实现了 ``IEEE 802.3-2022`` 的 30.9.1.2.1 acPSEAdminControl。
当设置时，可选的 ``ETHTOOL_A_C33_PSE_AVAIL_PWR_LIMIT`` 属性用于控制 C33 PSE 的可用功率值限制（单位为毫瓦）。
此属性对应于在 ``IEEE 802.3-2022`` 33.2.4.4 变量中描述的 `pse_available_power` 变量，以及在 145.2.5.4 变量中描述的 `pse_avail_pwr`，这些变量是根据功率类别定义的。
决定使用毫瓦作为此接口的单位，以统一其他功率监控接口，并与许多记录功率消耗为瓦特而不是类别的现有产品对齐。如果需要基于类别的功率限制配置，可以在用户空间进行转换，例如通过 ethtool RSS_GET。

RSS_GET
=======

获取与接口的 RSS 上下文相关的间接表、哈希键和哈希函数信息，类似于 ``ETHTOOL_GRSSH`` ioctl 请求。
请求内容：

=====================================  ======  ==========================
  ``ETHTOOL_A_RSS_HEADER``             嵌套    请求头
  ``ETHTOOL_A_RSS_CONTEXT``            u32     上下文编号
=====================================  ======  ==========================

内核响应内容：

=====================================  ======  ==========================
  ``ETHTOOL_A_RSS_HEADER``             嵌套    响应头
  ``ETHTOOL_A_RSS_HFUNC``              u32     RSS 哈希函数
  ``ETHTOOL_A_RSS_INDIR``              二进制  间接表字节
  ``ETHTOOL_A_RSS_HKEY``               二进制  哈希键字节
  ``ETHTOOL_A_RSS_INPUT_XFRM``         u32     RSS 输入数据变换
=====================================  ======  ==========================

``ETHTOOL_A_RSS_HFUNC`` 属性是一个位图，指示正在使用的哈希函数。当前支持的选项包括 Toeplitz、XOR 或 CRC32。
``ETHTOOL_A_RSS_INDIR`` 属性返回 RSS 间接表，其中每个字节表示队列编号。
``ETHTOOL_A_RSS_INPUT_XFRM`` 属性是一个位图，指示在将输入协议字段提供给 RSS 哈希函数之前所应用的变换类型。当前支持的选项是对称-XOR。

PLCA_GET_CFG
============

获取 IEEE 802.3cg-2019 第 148 条款物理层碰撞避免 (PLCA) 和和解子层 (Reconciliation Sublayer, RS) 属性。
请求内容：

  =====================================  ======  ==========================
  ``ETHTOOL_A_PLCA_HEADER``              嵌套    请求头
  =====================================  ======  ==========================

内核响应内容：

  ======================================  ======  =============================
  ``ETHTOOL_A_PLCA_HEADER``               嵌套    响应头
  ``ETHTOOL_A_PLCA_VERSION``              u16     支持的PLCA管理接口标准/版本
  ``ETHTOOL_A_PLCA_ENABLED``              u8      PLCA 管理状态
  ``ETHTOOL_A_PLCA_NODE_ID``              u32     PLCA 独特的本地节点ID
  ``ETHTOOL_A_PLCA_NODE_CNT``             u32     网络上的PLCA节点数量，包括协调器
  ``ETHTOOL_A_PLCA_TO_TMR``               u32     发送机会定时器值（以比特时间计）
  ``ETHTOOL_A_PLCA_BURST_CNT``            u32     节点在单个发送机会期间允许发送的额外数据包数
  ``ETHTOOL_A_PLCA_BURST_TMR``            u32     在终止突发之前等待MAC传输新帧的时间（以比特时间计）
  ======================================  ======  =============================

当设置了可选的 ``ETHTOOL_A_PLCA_VERSION`` 属性时，表示PLCA管理接口遵循的标准和版本。未设置时，接口是特定于供应商的，并且（可能）由驱动程序提供。
OPEN Alliance SIG 指定了一个用于嵌入PLCA调和子层的10BASE-T1S PHY的标准寄存器映射。详见 "10BASE-T1S PLCA 管理寄存器"：https://www.opensig.org/about/specifications/
当设置了可选的 ``ETHTOOL_A_PLCA_ENABLED`` 属性时，表示PLCA RS的管理状态。未设置时，节点运行在“普通”CSMA/CD模式下。此选项对应于 ``IEEE 802.3cg-2019`` 30.16.1.1.1 aPLCAAdminState / 30.16.1.2.1 acPLCAAdminControl。
当设置了可选的 ``ETHTOOL_A_PLCA_NODE_ID`` 属性时，表示PHY配置的本地节点ID。该ID决定了哪个发送机会（TO）为节点保留。此选项对应于 ``IEEE 802.3cg-2019`` 30.16.1.1.4 aPLCALocalNodeID。此属性的有效范围是 [0 .. 255]，其中255表示“未配置”。
当设置了可选的 ``ETHTOOL_A_PLCA_NODE_CNT`` 属性时，表示混合段上PLCA节点的最大配置数量。这个数字决定了在一个PLCA周期中生成的发送机会总数。此属性仅对PLCA协调器相关，即具有aPLCALocalNodeID设置为0的节点。跟随节点忽略此设置。此选项对应于 ``IEEE 802.3cg-2019`` 30.16.1.1.3 aPLCANodeCount。此属性的有效范围是 [1 .. 255]。
当设置了可选的 ``ETHTOOL_A_PLCA_TO_TMR`` 属性时，表示发送机会定时器在比特时间中的配置值。为了使PLCA正常工作，此值必须在共享介质的所有节点上设置相同。此选项对应于 ``IEEE 802.3cg-2019`` 30.16.1.1.5 aPLCATransmitOpportunityTimer。此属性的有效范围是 [0 .. 255]。
当设置了可选的 ``ETHTOOL_A_PLCA_BURST_CNT`` 属性时，表示节点在单个发送机会期间允许发送的额外数据包数量。默认情况下，此属性为0，这意味着节点每TO只能发送一个帧。当大于0时，PLCA RS会在任何传输后保持TO，等待MAC在最多aPLCABurstTimer BT的时间内发送新帧。这在一个PLCA周期内只能发生指定次数。之后，突发结束，正常的TO计数恢复。此选项对应于 ``IEEE 802.3cg-2019`` 30.16.1.1.6 aPLCAMaxBurstCount。此属性的有效范围是 [0 .. 255]。
当设置了可选的 ``ETHTOOL_A_PLCA_BURST_TMR`` 属性时，表示当aPLCAMaxBurstCount大于0时，PLCA RS等待MAC启动新传输所需的比特时间数。如果MAC未能在此时间内发送新帧，则突发结束，TO计数恢复；否则，新帧作为当前突发的一部分发送。此选项对应于 ``IEEE 802.3cg-2019`` 30.16.1.1.7 aPLCABurstTimer。此属性的有效范围是 [0 .. 255]。虽然，为了使PLCA突发模式按预期工作，此值应大于MAC的帧间间隔（IFG）时间（加上一些余量）。
PLCA_SET_CFG
============

设置 PLCA RS 参数
请求内容：

  ======================================  ======  =============================
  ``ETHTOOL_A_PLCA_HEADER``               嵌套    请求头
  ``ETHTOOL_A_PLCA_ENABLED``              u8      PLCA 管理状态
  ``ETHTOOL_A_PLCA_NODE_ID``              u8      PLCA 独特的本地节点 ID
  ``ETHTOOL_A_PLCA_NODE_CNT``             u8      网络上的 PLCA 节点数，包括协调器
  ``ETHTOOL_A_PLCA_TO_TMR``               u8      传输机会定时器值（以比特时间 BT 计算）
  ``ETHTOOL_A_PLCA_BURST_CNT``            u8      节点在单个 TO 内允许发送的额外数据包数量
  ``ETHTOOL_A_PLCA_BURST_TMR``            u8      在终止突发前等待 MAC 发送新帧的时间
  ======================================  ======  =============================

有关每个属性的描述，请参见 ``PLCA_GET_CFG``

PLCA_GET_STATUS
===============

获取 PLCA RS 状态信息
请求内容：

  =====================================  ======  ==========================
  ``ETHTOOL_A_PLCA_HEADER``              嵌套    请求头
  =====================================  ======  ==========================

内核响应内容：

  ======================================  ======  =============================
  ``ETHTOOL_A_PLCA_HEADER``               嵌套    响应头
  ``ETHTOOL_A_PLCA_STATUS``               u8      PLCA RS 运行状态
  ======================================  ======  =============================

当设置时，``ETHTOOL_A_PLCA_STATUS`` 属性指示节点是否检测到网络上的 BEACON。此标志对应于 ``IEEE 802.3cg-2019`` 的 30.16.1.1.2 aPLCAStatus

MM_GET
======

检索 802.3 MAC 合并参数
请求内容：

  ====================================  ======  ==========================
  ``ETHTOOL_A_MM_HEADER``               嵌套    请求头
  ====================================  ======  ==========================

内核响应内容：

  =================================  ======  ===================================
  ``ETHTOOL_A_MM_HEADER``            嵌套    请求头
  ``ETHTOOL_A_MM_PMAC_ENABLED``      布尔    如果启用了可抢占和 SMD-V 帧的接收，则设置为 true
  ``ETHTOOL_A_MM_TX_ENABLED``        布尔    如果启用了可抢占帧的 TX 管理状态（如果验证失败可能处于非活动状态）
  ``ETHTOOL_A_MM_TX_ACTIVE``         布尔    如果启用了可抢占帧的 TX 操作状态
  ``ETHTOOL_A_MM_TX_MIN_FRAG_SIZE``  u32     发送的非最终片段的最小大小（以字节计）
  ``ETHTOOL_A_MM_RX_MIN_FRAG_SIZE``  u32     接收的非最终片段的最小大小（以字节计）
  ``ETHTOOL_A_MM_VERIFY_ENABLED``    布尔    如果启用了 SMD-V 帧的 TX 管理状态
  ``ETHTOOL_A_MM_VERIFY_STATUS``     u8      验证功能的状态
  ``ETHTOOL_A_MM_VERIFY_TIME``       u32     验证尝试之间的延迟
  ``ETHTOOL_A_MM_MAX_VERIFY_TIME``   u32     设备支持的最大验证间隔
  ``ETHTOOL_A_MM_STATS``             嵌套    IEEE 802.3-2018 子条款 30.14.1 oMACMergeEntity 统计计数器
  =================================  ======  ===================================

这些属性通过以下结构由设备驱动程序填充：

.. kernel-doc:: include/linux/ethtool.h
    :identifiers: ethtool_mm_state

``ETHTOOL_A_MM_VERIFY_STATUS`` 将报告以下值之一：

.. kernel-doc:: include/uapi/linux/ethtool.h
    :identifiers: ethtool_mm_verify_status

如果在 ``MM_SET`` 命令中将 ``ETHTOOL_A_MM_VERIFY_ENABLED`` 设置为 false，则 ``ETHTOOL_A_MM_VERIFY_STATUS`` 将报告 ``ETHTOOL_MM_VERIFY_STATUS_INITIAL`` 或 ``ETHTOOL_MM_VERIFY_STATUS_DISABLED``，否则应报告其他状态之一。

建议驱动程序最初禁用 pMAC，并根据用户空间请求启用它。同样建议用户空间不要依赖于从 ``ETHTOOL_MSG_MM_GET`` 请求获得的默认值。

如果在 ``ETHTOOL_A_HEADER_FLAGS`` 中设置了 ``ETHTOOL_FLAG_STATS``，则会报告 ``ETHTOOL_A_MM_STATS``。如果驱动程序未报告任何统计数据，该属性将是空的。驱动程序在以下结构中填充统计数据：

.. kernel-doc:: include/linux/ethtool.h
    :identifiers: ethtool_mm_stats

MM_SET
======

修改 802.3 MAC 合并层的配置
请求内容：

  =================================  ======  ==========================
  ``ETHTOOL_A_MM_VERIFY_TIME``       u32     参见 MM_GET 描述
  ``ETHTOOL_A_MM_VERIFY_ENABLED``    布尔    参见 MM_GET 描述
  ``ETHTOOL_A_MM_TX_ENABLED``        布尔    参见 MM_GET 描述
  ``ETHTOOL_A_MM_PMAC_ENABLED``      布尔    参见 MM_GET 描述
  ``ETHTOOL_A_MM_TX_MIN_FRAG_SIZE``  u32     参见 MM_GET 描述
  =================================  ======  ==========================

这些属性通过以下结构传递给驱动程序：

.. kernel-doc:: include/linux/ethtool.h
    :identifiers: ethtool_mm_cfg

MODULE_FW_FLASH_ACT
===================

刷新收发器模块固件
请求内容：

  =======================================  ======  ===========================
  ``ETHTOOL_A_MODULE_FW_FLASH_HEADER``     嵌套    请求头
  ``ETHTOOL_A_MODULE_FW_FLASH_FILE_NAME``  字符串  固件映像文件名
  ``ETHTOOL_A_MODULE_FW_FLASH_PASSWORD``   u32     收发器模块密码
  =======================================  ======  ===========================

固件更新过程包括三个逻辑步骤：

1. 将固件映像下载到收发器模块并进行验证
2. 运行固件镜像  
3. 提交固件镜像以便在复位时运行  

当发出闪存命令时，会按照上述顺序执行这三个步骤。  
此消息仅调度更新过程并立即返回，不会阻塞。该过程随后异步运行。由于整个过程可能需要几分钟时间，在更新过程中内核会向用户空间发送通知，以更新状态和进度信息。  
`ETHTOOL_A_MODULE_FW_FLASH_FILE_NAME` 属性编码了固件镜像文件名。固件镜像被下载到收发器模块中，经过验证后运行并提交。  
可选的 `ETHTOOL_A_MODULE_FW_FLASH_PASSWORD` 属性编码了一个密码，该密码可能是收发器模块固件更新过程中所需的。  
固件更新过程可能需要几分钟才能完成。因此，在更新过程中内核会向用户空间发送通知，以更新状态和进度信息。

通知内容：

+---------------------------------------------------+--------+----------------+
| `ETHTOOL_A_MODULE_FW_FLASH_HEADER`                | 嵌套    | 回复头         |
+---------------------------------------------------+--------+----------------+
| `ETHTOOL_A_MODULE_FW_FLASH_STATUS`                | u32    | 状态           |
+---------------------------------------------------+--------+----------------+
| `ETHTOOL_A_MODULE_FW_FLASH_STATUS_MSG`            | 字符串  | 状态信息       |
+---------------------------------------------------+--------+----------------+
| `ETHTOOL_A_MODULE_FW_FLASH_DONE`                  | uint   | 完成进度       |
+---------------------------------------------------+--------+----------------+
| `ETHTOOL_A_MODULE_FW_FLASH_TOTAL`                 | uint   | 总量           |
+---------------------------------------------------+--------+----------------+

`ETHTOOL_A_MODULE_FW_FLASH_STATUS` 属性编码了当前固件更新过程的状态。可能的值为：

.. kernel-doc:: include/uapi/linux/ethtool.h
    :identifiers: ethtool_module_fw_flash_status

`ETHTOOL_A_MODULE_FW_FLASH_STATUS_MSG` 属性编码了一个状态信息字符串。
`ETHTOOL_A_MODULE_FW_FLASH_DONE` 和 `ETHTOOL_A_MODULE_FW_FLASH_TOTAL` 属性分别编码了已完成的工作量和总工作量。
以下表格将ioctl命令映射到netlink命令，提供其功能。右列中标记为“n/a”的条目是没有netlink替代命令的命令。左列中标记为“n/a”的条目是仅适用于netlink的命令。

| ioctl命令                          | netlink命令                                             |
|------------------------------------|--------------------------------------------------------|
| `ETHTOOL_GSET`                     | `ETHTOOL_MSG_LINKINFO_GET`                             |
|                                    | `ETHTOOL_MSG_LINKMODES_GET`                            |
| `ETHTOOL_SSET`                     | `ETHTOOL_MSG_LINKINFO_SET`                             |
|                                    | `ETHTOOL_MSG_LINKMODES_SET`                            |
| `ETHTOOL_GDRVINFO`                 | n/a                                                     |
| `ETHTOOL_GREGS`                    | n/a                                                     |
| `ETHTOOL_GWOL`                     | `ETHTOOL_MSG_WOL_GET`                                  |
| `ETHTOOL_SWOL`                     | `ETHTOOL_MSG_WOL_SET`                                  |
| `ETHTOOL_GMSGLVL`                  | `ETHTOOL_MSG_DEBUG_GET`                                |
| `ETHTOOL_SMSGLVL`                  | `ETHTOOL_MSG_DEBUG_SET`                                |
| `ETHTOOL_NWAY_RST`                 | n/a                                                     |
| `ETHTOOL_GLINK`                    | `ETHTOOL_MSG_LINKSTATE_GET`                            |
| `ETHTOOL_GEEPROM`                  | n/a                                                     |
| `ETHTOOL_SEEPROM`                  | n/a                                                     |
| `ETHTOOL_GCOALESCE`                | `ETHTOOL_MSG_COALESCE_GET`                             |
| `ETHTOOL_SCOALESCE`                | `ETHTOOL_MSG_COALESCE_SET`                             |
| `ETHTOOL_GRINGPARAM`               | `ETHTOOL_MSG_RINGS_GET`                                |
| `ETHTOOL_SRINGPARAM`               | `ETHTOOL_MSG_RINGS_SET`                                |
| `ETHTOOL_GPAUSEPARAM`              | `ETHTOOL_MSG_PAUSE_GET`                                |
| `ETHTOOL_SPAUSEPARAM`              | `ETHTOOL_MSG_PAUSE_SET`                                |
| `ETHTOOL_GRXCSUM`                  | `ETHTOOL_MSG_FEATURES_GET`                             |
| `ETHTOOL_SRXCSUM`                  | `ETHTOOL_MSG_FEATURES_SET`                             |
| `ETHTOOL_GTXCSUM`                  | `ETHTOOL_MSG_FEATURES_GET`                             |
| `ETHTOOL_STXCSUM`                  | `ETHTOOL_MSG_FEATURES_SET`                             |
| `ETHTOOL_GSG`                      | `ETHTOOL_MSG_FEATURES_GET`                             |
| `ETHTOOL_SSG`                      | `ETHTOOL_MSG_FEATURES_SET`                             |
| `ETHTOOL_TEST`                     | n/a                                                     |
| `ETHTOOL_GSTRINGS`                 | `ETHTOOL_MSG_STRSET_GET`                               |
| `ETHTOOL_PHYS_ID`                  | n/a                                                     |
| `ETHTOOL_GSTATS`                   | n/a                                                     |
| `ETHTOOL_GTSO`                     | `ETHTOOL_MSG_FEATURES_GET`                             |
| `ETHTOOL_STSO`                     | `ETHTOOL_MSG_FEATURES_SET`                             |
| `ETHTOOL_GPERMADDR`                | rtnetlink `RTM_GETLINK`                                |
| `ETHTOOL_GUFO`                     | `ETHTOOL_MSG_FEATURES_GET`                             |
| `ETHTOOL_SUFO`                     | `ETHTOOL_MSG_FEATURES_SET`                             |
| `ETHTOOL_GGSO`                     | `ETHTOOL_MSG_FEATURES_GET`                             |
| `ETHTOOL_SGSO`                     | `ETHTOOL_MSG_FEATURES_SET`                             |
| `ETHTOOL_GFLAGS`                   | `ETHTOOL_MSG_FEATURES_GET`                             |
| `ETHTOOL_SFLAGS`                   | `ETHTOOL_MSG_FEATURES_SET`                             |
| `ETHTOOL_GPFLAGS`                  | `ETHTOOL_MSG_PRIVFLAGS_GET`                            |
| `ETHTOOL_SPFLAGS`                  | `ETHTOOL_MSG_PRIVFLAGS_SET`                            |
| `ETHTOOL_GRXFH`                    | n/a                                                     |
| `ETHTOOL_SRXFH`                    | n/a                                                     |
| `ETHTOOL_GGRO`                     | `ETHTOOL_MSG_FEATURES_GET`                             |
| `ETHTOOL_SGRO`                     | `ETHTOOL_MSG_FEATURES_SET`                             |
| `ETHTOOL_GRXRINGS`                 | n/a                                                     |
| `ETHTOOL_GRXCLSRLCNT`              | n/a                                                     |
| `ETHTOOL_GRXCLSRULE`               | n/a                                                     |
| `ETHTOOL_GRXCLSRLALL`              | n/a                                                     |
| `ETHTOOL_SRXCLSRLDEL`              | n/a                                                     |
| `ETHTOOL_SRXCLSRLINS`              | n/a                                                     |
| `ETHTOOL_FLASHDEV`                 | n/a                                                     |
| `ETHTOOL_RESET`                    | n/a                                                     |
| `ETHTOOL_SRXNTUPLE`                | n/a                                                     |
| `ETHTOOL_GRXNTUPLE`                | n/a                                                     |
| `ETHTOOL_GSSET_INFO`               | `ETHTOOL_MSG_STRSET_GET`                               |
| `ETHTOOL_GRXFHINDIR`               | n/a                                                     |
| `ETHTOOL_SRXFHINDIR`               | n/a                                                     |
| `ETHTOOL_GFEATURES`                | `ETHTOOL_MSG_FEATURES_GET`                             |
| `ETHTOOL_SFEATURES`                | `ETHTOOL_MSG_FEATURES_SET`                             |
| `ETHTOOL_GCHANNELS`                | `ETHTOOL_MSG_CHANNELS_GET`                             |
| `ETHTOOL_SCHANNELS`                | `ETHTOOL_MSG_CHANNELS_SET`                             |
| `ETHTOOL_SET_DUMP`                 | n/a                                                     |
| `ETHTOOL_GET_DUMP_FLAG`            | n/a                                                     |
| `ETHTOOL_GET_DUMP_DATA`            | n/a                                                     |
| `ETHTOOL_GET_TS_INFO`              | `ETHTOOL_MSG_TSINFO_GET`                               |
| `ETHTOOL_GMODULEINFO`              | `ETHTOOL_MSG_MODULE_EEPROM_GET`                        |
| `ETHTOOL_GMODULEEEPROM`            | `ETHTOOL_MSG_MODULE_EEPROM_GET`                        |
| `ETHTOOL_GEEE`                     | `ETHTOOL_MSG_EEE_GET`                                  |
| `ETHTOOL_SEEE`                     | `ETHTOOL_MSG_EEE_SET`                                  |
| `ETHTOOL_GRSSH`                    | `ETHTOOL_MSG_RSS_GET`                                  |
| `ETHTOOL_SRSSH`                    | n/a                                                     |
| `ETHTOOL_GTUNABLE`                 | n/a                                                     |
| `ETHTOOL_STUNABLE`                 | n/a                                                     |
| `ETHTOOL_GPHYSTATS`                | n/a                                                     |
| `ETHTOOL_PERQUEUE`                 | n/a                                                     |
| `ETHTOOL_GLINKSETTINGS`            | `ETHTOOL_MSG_LINKINFO_GET`                             |
|                                    | `ETHTOOL_MSG_LINKMODES_GET`                            |
| `ETHTOOL_SLINKSETTINGS`            | `ETHTOOL_MSG_LINKINFO_SET`                             |
|                                    | `ETHTOOL_MSG_LINKMODES_SET`                            |
| `ETHTOOL_PHY_GTUNABLE`             | n/a                                                     |
| `ETHTOOL_PHY_STUNABLE`             | n/a                                                     |
| `ETHTOOL_GFECPARAM`                | `ETHTOOL_MSG_FEC_GET`                                  |
| `ETHTOOL_SFECPARAM`                | `ETHTOOL_MSG_FEC_SET`                                  |
| n/a                                 | `ETHTOOL_MSG_CABLE_TEST_ACT`                           |
| n/a                                 | `ETHTOOL_MSG_CABLE_TEST_TDR_ACT`                       |
| n/a                                 | `ETHTOOL_MSG_TUNNEL_INFO_GET`                          |
| n/a                                 | `ETHTOOL_MSG_PHC_VCLOCKS_GET`                          |
| n/a                                 | `ETHTOOL_MSG_MODULE_GET`                               |
| n/a                                 | `ETHTOOL_MSG_MODULE_SET`                               |
| n/a                                 | `ETHTOOL_MSG_PLCA_GET_CFG`                             |
| n/a                                 | `ETHTOOL_MSG_PLCA_SET_CFG`                             |
| n/a                                 | `ETHTOOL_MSG_PLCA_GET_STATUS`                          |
| n/a                                 | `ETHTOOL_MSG_MM_GET`                                   |
| n/a                                 | `ETHTOOL_MSG_MM_SET`                                   |
| n/a                                 | `ETHTOOL_MSG_MODULE_FW_FLASH_ACT`                      |
