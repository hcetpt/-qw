=============================
Ethtool 的 Netlink 接口
=============================


基本信息
=================

Ethtool 的 Netlink 接口使用通用的 Netlink 家族 `ethtool`（用户空间的应用程序应当使用在 `<linux/ethtool_netlink.h>` 用户接口头文件中定义的宏 `ETHTOOL_GENL_NAME` 和 `ETHTOOL_GENL_VERSION`）。这个家族不使用特定的头部，所有的信息通过 Netlink 属性在网络请求和回复中传递。
Ethtool 的 Netlink 接口使用扩展确认（ACK）来报告错误和警告，鼓励用户空间应用程序开发者以适当的方式将这些消息提供给用户。
请求可以分为三类："获取"（检索信息）、"设置"（设置参数）和"动作"（触发一个动作）。
所有 "设置" 和 "动作" 类型的请求都需要管理员权限 (`CAP_NET_ADMIN` 在命名空间中)。大多数 "获取" 类型的请求对任何人都允许，但也有例外（响应包含敏感信息的情况）。在某些情况下，请求本身对任何人都允许，但未授权用户会忽略掉含有敏感信息（例如，局域网唤醒密码）的属性。
约定
===========

表示布尔值的属性通常使用 NLA_U8 类型，以便我们可以区分三种状态："开启"、"关闭" 和 "不存在"（意味着 "获取" 请求中的信息不可用或 "设置" 请求中的值不会被改变）。对于这些属性，"真" 值应当作为数字 1 传递，但接收方应当理解任何非零值都为 "真"。
在下面的表格中，"bool" 表示按照这种方式解释的 NLA_U8 属性。
在下面的消息结构描述中，如果属性名称后跟 "+"，则父级嵌套可以包含多个相同类型的属性。这实现了一个条目的数组。
需要由设备驱动填充，并根据是否有效而输出到用户空间的属性不应使用零作为有效值。这避免了在设备驱动程序 API 中明确标记属性有效性的必要性。
请求头部
==============

每个请求或回复消息都包含一个嵌套属性，其中包含了通用的头部。
此头部的结构为：

  ==============================  ======  =============================
  ``ETHTOOL_A_HEADER_DEV_INDEX``  u32     设备索引
  ``ETHTOOL_A_HEADER_DEV_NAME``   字符串  设备名称
  ``ETHTOOL_A_HEADER_FLAGS``      u32     所有请求共有的标志
  ==============================  ======  =============================

``ETHTOOL_A_HEADER_DEV_INDEX`` 和 ``ETHTOOL_A_HEADER_DEV_NAME`` 用于标识与消息相关的设备。在请求中使用其中之一就足够了；如果两者都使用，则必须标识同一个设备。某些请求（例如全局字符串集）不需要设备标识。大多数 `GET` 请求也允许在没有设备标识的情况下进行转储请求，以查询所有提供该信息的设备的相同信息（每个设备一条单独的消息）。``ETHTOOL_A_HEADER_FLAGS`` 是所有请求类型通用的请求标志位图。这些标志的解释对于所有请求类型都是相同的，但这些标志可能不适用于某些请求。被识别的标志包括：

  =================================  ===================================
  ``ETHTOOL_FLAG_COMPACT_BITSETS``   在回复中使用紧凑格式位图
  ``ETHTOOL_FLAG_OMIT_REPLY``        省略可选回复 (_SET 和 _ACT)
  ``ETHTOOL_FLAG_STATS``             包含可选的设备统计信息
  =================================  ===================================

新请求标志应该遵循这样的总体思路：如果未设置标志，则行为向后兼容，即来自旧客户端（对标志不了解）的请求应按照客户端预期的方式解释。客户端不应设置它不理解的标志。
### 位集

对于较短且长度相对固定的位图，使用标准的 ``NLA_BITFIELD32`` 类型。对于任意长度的位图，ethtool netlink 使用嵌套属性，其内容有两种形式之一：紧凑型（两个二进制位图表示位值和受影响位的掩码）和详细型（按位列出，由索引或名称标识）。

详细的（按位列出）位集允许将位的符号名称与其值一起发送，这节省了一个往返的时间（当位集作为请求的一部分时）或者至少减少了一个额外的请求（当位集包含在回复中）。这对于像传统的 ethtool 命令这样的单次运行应用程序非常有用。另一方面，长时间运行的应用程序（如 ethtool 监控器（显示通知）或网络管理守护进程）可能更倾向于只获取一次名称，并使用紧凑形式来节省消息大小。从 ethtool netlink 接口发出的通知总是使用紧凑形式的位集。

位集可以表示一个值/掩码对（``ETHTOOL_A_BITSET_NOMASK`` 未设置）或一个单独的位图（``ETHTOOL_A_BITSET_NOMASK`` 设置）。在修改位图的请求中，前者将掩码中的位设置为值中的位，并保留其余部分；后者将位图中的位设置，并清除其余部分。
### 紧凑形式：嵌套（位集）属性的内容：

  ============================  ======  ============================
  ``ETHTOOL_A_BITSET_NOMASK``   标志    没有掩码，仅列表
  ``ETHTOOL_A_BITSET_SIZE``     u32     显著位的数量
  ``ETHTOOL_A_BITSET_VALUE``    二进制  位值的位图
  ``ETHTOOL_A_BITSET_MASK``     二进制  有效位的位图
  ============================  ======  ============================

值和掩码的长度必须至少为 ``ETHTOOL_A_BITSET_SIZE`` 位，向上取最近的32位倍数。它们由主机字节序中的32位单词组成，从最低有效位到最高有效位排列（即与 ioctl 接口传递位图的方式相同）。

对于紧凑形式，``ETHTOOL_A_BITSET_SIZE`` 和 ``ETHTOOL_A_BITSET_VALUE`` 是必需的。如果未设置 ``ETHTOOL_A_BITSET_NOMASK``（位集代表值/掩码对），则 ``ETHTOOL_A_BITSET_MASK`` 属性也是必需的；如果设置了 ``ETHTOOL_A_BITSET_NOMASK``，则不允许使用 ``ETHTOOL_A_BITSET_MASK``（位集代表单一的位图）。

内核位集长度可能与用户空间长度不同，如果在较新内核上使用较老的应用程序，反之亦然。如果用户空间位图较长，只有在请求实际尝试设置内核未识别的某些位的值时才会产生错误。
### 逐位形式：嵌套（位集）属性的内容：

 +------------------------------------+--------+-----------------------------+
 | ``ETHTOOL_A_BITSET_NOMASK``        | 标志   | 没有掩码，仅列表            |
 +------------------------------------+--------+-----------------------------+
 | ``ETHTOOL_A_BITSET_SIZE``          | u32    | 显著位的数量                |
 +------------------------------------+--------+-----------------------------+
 | ``ETHTOOL_A_BITSET_BITS``          | 嵌套   | 位数组                      |
 +-+----------------------------------+--------+-----------------------------+
 | | ``ETHTOOL_A_BITSET_BITS_BIT+``   | 嵌套   | 单个位                       |
 +-+-+--------------------------------+--------+-----------------------------+
 | | | ``ETHTOOL_A_BITSET_BIT_INDEX`` | u32    | 位索引（最低有效位为0）     |
 +-+-+--------------------------------+--------+-----------------------------+
 | | | ``ETHTOOL_A_BITSET_BIT_NAME``  | 字符串 | 位名称                      |
 +-+-+--------------------------------+--------+-----------------------------+
 | | | ``ETHTOOL_A_BITSET_BIT_VALUE`` | 标志   | 如果位被设置则存在           |
 +-+-+--------------------------------+--------+-----------------------------+

逐位形式中的位数量是可选的。``ETHTOOL_A_BITSET_BITS`` 嵌套只能包含 ``ETHTOOL_A_BITSET_BITS_BIT`` 属性，但可以包含任意数量的此类属性。位可以通过其索引或名称来标识。在请求中使用时，根据 ``ETHTOOL_A_BITSET_BIT_VALUE`` 列出的位被设置为0或1，其余保持不变。如果索引超过内核位长度或名称未被识别，请求失败。

当存在 ``ETHTOOL_A_BITSET_NOMASK`` 标志时，位集被视为简单的位图。在这种情况下不会使用 ``ETHTOOL_A_BITSET_BIT_VALUE`` 属性。此类位集表示一个位图，其中列出的位被设置，其余位为零。
在请求中，应用程序可以使用两种形式中的任意一种。内核在回复中使用的格式由请求头的 `ETHTOOL_FLAG_COMPACT_BITSETS` 标志决定。值和掩码的语义取决于属性。

消息类型列表
=============

所有标识消息类型的常量都使用 `ETHTOOL_CMD_` 前缀和后缀，并根据消息的目的来定义：

  ==============    ======================================
  `_GET`            用户空间请求获取数据
  `_SET`            用户空间请求设置数据
  `_ACT`            用户空间请求执行操作
  `_GET_REPLY`      内核对 `GET` 请求的回复
  `_SET_REPLY`      内核对 `SET` 请求的回复
  `_ACT_REPLY`      内核对 `ACT` 请求的回复
  `_NTF`            内核通知
  ==============    ======================================

从用户空间到内核：

  ===================================== =================================
  `ETHTOOL_MSG_STRSET_GET`              获取字符串集
  `ETHTOOL_MSG_LINKINFO_GET`            获取链路设置
  `ETHTOOL_MSG_LINKINFO_SET`            设置链路设置
  `ETHTOOL_MSG_LINKMODES_GET`           获取链路模式信息
  `ETHTOOL_MSG_LINKMODES_SET`           设置链路模式信息
  `ETHTOOL_MSG_LINKSTATE_GET`           获取链路状态
  `ETHTOOL_MSG_DEBUG_GET`               获取调试设置
  `ETHTOOL_MSG_DEBUG_SET`               设置调试设置
  `ETHTOOL_MSG_WOL_GET`                 获取局域唤醒设置
  `ETHTOOL_MSG_WOL_SET`                 设置局域唤醒设置
  `ETHTOOL_MSG_FEATURES_GET`            获取设备特性
  `ETHTOOL_MSG_FEATURES_SET`            设置设备特性
  `ETHTOOL_MSG_PRIVFLAGS_GET`           获取私有标志
  `ETHTOOL_MSG_PRIVFLAGS_SET`           设置私有标志
  `ETHTOOL_MSG_RINGS_GET`               获取环形缓冲区大小
  `ETHTOOL_MSG_RINGS_SET`               设置环形缓冲区大小
  `ETHTOOL_MSG_CHANNELS_GET`            获取通道计数
  `ETHTOOL_MSG_CHANNELS_SET`            设置通道计数
  `ETHTOOL_MSG_COALESCE_GET`            获取合并参数
  `ETHTOOL_MSG_COALESCE_SET`            设置合并参数
  `ETHTOOL_MSG_PAUSE_GET`               获取暂停参数
  `ETHTOOL_MSG_PAUSE_SET`               设置暂停参数
  `ETHTOOL_MSG_EEE_GET`                 获取EEE设置
  `ETHTOOL_MSG_EEE_SET`                 设置EEE设置
  `ETHTOOL_MSG_TSINFO_GET`              获取时间戳信息
  `ETHTOOL_MSG_CABLE_TEST_ACT`          开始电缆测试动作
  `ETHTOOL_MSG_CABLE_TEST_TDR_ACT`      开始原始TDR电缆测试动作
  `ETHTOOL_MSG_TUNNEL_INFO_GET`         获取隧道卸载信息
  `ETHTOOL_MSG_FEC_GET`                 获取FEC设置
  `ETHTOOL_MSG_FEC_SET`                 设置FEC设置
  `ETHTOOL_MSG_MODULE_EEPROM_GET`       读取SFP模块EEPROM
  `ETHTOOL_MSG_STATS_GET`               获取标准统计
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

从内核到用户空间：

  ======================================== =================================
  `ETHTOOL_MSG_STRSET_GET_REPLY`           字符串集内容
  `ETHTOOL_MSG_LINKINFO_GET_REPLY`         链路设置
  `ETHTOOL_MSG_LINKINFO_NTF`               链路设置通知
  `ETHTOOL_MSG_LINKMODES_GET_REPLY`        链路模式信息
  `ETHTOOL_MSG_LINKMODES_NTF`              链路模式通知
  `ETHTOOL_MSG_LINKSTATE_GET_REPLY`        链路状态信息
  `ETHTOOL_MSG_DEBUG_GET_REPLY`            调试设置
  `ETHTOOL_MSG_DEBUG_NTF`                  调试设置通知
  `ETHTOOL_MSG_WOL_GET_REPLY`              局域唤醒设置
  `ETHTOOL_MSG_WOL_NTF`                    局域唤醒设置通知
  `ETHTOOL_MSG_FEATURES_GET_REPLY`         设备特性
  `ETHTOOL_MSG_FEATURES_SET_REPLY`         `FEATURES_SET` 的可选回复
  `ETHTOOL_MSG_FEATURES_NTF`               网络设备特性通知
  `ETHTOOL_MSG_PRIVFLAGS_GET_REPLY`        私有标志
  `ETHTOOL_MSG_PRIVFLAGS_NTF`              私有标志通知
  `ETHTOOL_MSG_RINGS_GET_REPLY`            环形缓冲区大小
  `ETHTOOL_MSG_RINGS_NTF`                  环形缓冲区大小通知
  `ETHTOOL_MSG_CHANNELS_GET_REPLY`         通道计数
  `ETHTOOL_MSG_CHANNELS_NTF`               通道计数通知
  `ETHTOOL_MSG_COALESCE_GET_REPLY`         合并参数
  `ETHTOOL_MSG_COALESCE_NTF`               合并参数通知
  `ETHTOOL_MSG_PAUSE_GET_REPLY`            暂停参数
  `ETHTOOL_MSG_PAUSE_NTF`                  暂停参数通知
  `ETHTOOL_MSG_EEE_GET_REPLY`              EEE设置
  `ETHTOOL_MSG_EEE_NTF`                    EEE设置通知
  `ETHTOOL_MSG_TSINFO_GET_REPLY`           时间戳信息
  `ETHTOOL_MSG_CABLE_TEST_NTF`             电缆测试结果
  `ETHTOOL_MSG_CABLE_TEST_TDR_NTF`         电缆测试TDR结果
  `ETHTOOL_MSG_TUNNEL_INFO_GET_REPLY`      隧道卸载信息
  `ETHTOOL_MSG_FEC_GET_REPLY`              FEC设置
  `ETHTOOL_MSG_FEC_NTF`                    FEC设置通知
  `ETHTOOL_MSG_MODULE_EEPROM_GET_REPLY`    读取SFP模块EEPROM
  `ETHTOOL_MSG_STATS_GET_REPLY`            标准统计
  `ETHTOOL_MSG_PHC_VCLOCKS_GET_REPLY`      PHC虚拟时钟信息
  `ETHTOOL_MSG_MODULE_GET_REPLY`           收发器模块参数
  `ETHTOOL_MSG_PSE_GET_REPLY`              PSE参数
  `ETHTOOL_MSG_RSS_GET_REPLY`              RSS设置
  `ETHTOOL_MSG_PLCA_GET_CFG_REPLY`         PLCA RS参数
  `ETHTOOL_MSG_PLCA_GET_STATUS_REPLY`      PLCA RS状态
  `ETHTOOL_MSG_PLCA_NTF`                   PLCA RS参数通知
  `ETHTOOL_MSG_MM_GET_REPLY`               MAC合并层状态
  `ETHTOOL_MSG_MODULE_FW_FLASH_NTF`        收发器模块固件更新
  ======================================== =================================

`GET` 请求由用户空间的应用程序发送以获取设备信息。它们通常不包含任何特定于消息的属性。内核通过对应的 "GET_REPLY" 消息进行回复。对于大多数类型，可以使用带有 `NLM_F_DUMP` 和无设备标识的 `GET` 请求来查询所有支持该请求的设备的信息。
如果数据也可以被修改，则使用与相应的 `GET_REPLY` 相同布局的 `SET` 消息来请求更改。只有请求更改的属性才包含在这样的请求中（并且并非所有属性都可以被更改）。对于大多数 `SET` 请求的回复仅包含错误代码和扩展确认；如果内核提供了额外的数据，则以对应的 `SET_REPLY` 消息的形式发送，可以通过在请求头中设置 `ETHTOOL_FLAG_OMIT_REPLY` 标志来抑制此回复。
数据的修改也会触发发送一个 `NTF` 消息作为通知。这些通常只包含受更改影响的属性子集。如果通过其他方式（主要是ethtool ioctl接口）修改了数据，也会发出相同的通知。与仅当确实发生更改时才会发送的通知不同，由ioctl接口触发的通知即使请求没有实际更改任何数据也可能被发送。
`ACT` 消息请求内核（驱动程序）执行特定的操作。如果内核报告了一些信息（这可以通过在请求头中设置 `ETHTOOL_FLAG_OMIT_REPLY` 标志来抑制），回复将以 `ACT_REPLY` 消息的形式出现。执行操作同样会触发通知 (`NTF` 消息)。

STRSET_GET
==========

请求的内容是通过 ioctl 命令 `ETHTOOL_GSSET_INFO` 和 `ETHTOOL_GSTRINGS` 提供的字符串集。字符串集不是用户可写的，因此相应的 `STRSET_SET` 消息仅用于内核回复。有两种类型的字符串集：全局（独立于设备，例如设备特性名称）和特定于设备的（例如设备私有标志）。
请求的内容为：

 +---------------------------------------+--------+------------------------+
 | `ETHTOOL_A_STRSET_HEADER`             | 嵌套   | 请求头                 |
 +---------------------------------------+--------+------------------------+
 | `ETHTOOL_A_STRSET_STRINGSETS`         | 嵌套   | 请求的字符串集         |
 +-+-------------------------------------+--------+------------------------+
 | | `ETHTOOL_A_STRINGSETS_STRINGSET+`   | 嵌套   | 一个字符串集           |
 +-+-+-----------------------------------+--------+------------------------+
 | | | `ETHTOOL_A_STRINGSET_ID`          | u32    | 集合ID                 |
 +-+-+-----------------------------------+--------+------------------------+

内核响应的内容为：

 +---------------------------------------+--------+-----------------------+
 | `ETHTOOL_A_STRSET_HEADER`             | 嵌套   | 回复头                |
 +---------------------------------------+--------+-----------------------+
 | `ETHTOOL_A_STRSET_STRINGSETS`         | 嵌套   | 字符串集数组           |
 +-+-------------------------------------+--------+-----------------------+
 | | `ETHTOOL_A_STRINGSETS_STRINGSET+`   | 嵌套   | 一个字符串集           |
 +-+-+-----------------------------------+--------+-----------------------+
 | | | `ETHTOOL_A_STRINGSET_ID`          | u32    | 集合ID                |
 +-+-+-----------------------------------+--------+-----------------------+
 | | | `ETHTOOL_A_STRINGSET_COUNT`       | u32    | 字符串数量            |
 +-+-+-----------------------------------+--------+-----------------------+
 | | | `ETHTOOL_A_STRINGSET_STRINGS`     | 嵌套   | 字符串数组            |
 +-+-+-+---------------------------------+--------+-----------------------+
 | | | | `ETHTOOL_A_STRINGS_STRING+`     | 嵌套   | 一个字符串             |
 +-+-+-+-+-------------------------------+--------+-----------------------+
 | | | | | `ETHTOOL_A_STRING_INDEX`      | u32    | 字符串索引             |
 +-+-+-+-+-------------------------------+--------+-----------------------+
 | | | | | `ETHTOOL_A_STRING_VALUE`      | 字符串 | 字符串值              |
 +-+-+-+-+-------------------------------+--------+-----------------------+
 | `ETHTOOL_A_STRSET_COUNTS_ONLY`        | 标志   | 仅返回计数            |
 +---------------------------------------+--------+-----------------------+

请求头中的设备标识是可选的。根据它的存在与否以及 `NLM_F_DUMP` 标志的存在与否，存在三种类型的 `STRSET_GET` 请求：

 - 没有 `NLM_F_DUMP`，没有设备：获取“全局”字符串集
 - 没有 `NLM_F_DUMP`，有设备：获取与该设备相关的字符串集
 - 有 `NLM_F_DUMP`，没有设备：获取所有设备相关的字符串集

如果没有 `ETHTOOL_A_STRSET_STRINGSETS` 数组，将返回请求类型的全部字符串集，否则只返回请求中指定的那些字符串集。
标志 "ETHTOOL_A_STRSET_COUNTS_ONLY" 告知内核仅返回集合的字符串计数，而不是实际的字符串。
LINKINFO_GET
============

请求链路设置，这些设置由 `ETHTOOL_GLINKSETTINGS` 提供，但不包括与链路模式和自动协商相关的信息。该请求不使用任何属性。
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

属性及其值具有与相应 ioctl 结构中匹配成员相同的含义。
`LINKINFO_GET` 允许执行转储请求（内核为所有支持该请求的设备返回响应消息）。
LINKINFO_SET
============

`LINKINFO_SET` 请求允许设置 `LINKINFO_GET` 报告的一些属性。
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

请求链路模式（支持的、已发布的和对等方已发布的）及相关信息（自动协商状态、链路速度和双工模式），这些信息由 `ETHTOOL_GLINKSETTINGS` 提供。该请求不使用任何属性。
请求内容：

  ====================================  ======  ==========================
  ``ETHTOOL_A_LINKMODES_HEADER``        nested  请求头
  ====================================  ======  ==========================

内核响应内容：

  ==========================================  ======  ==========================
  ``ETHTOOL_A_LINKMODES_HEADER``              nested  响应头
  ``ETHTOOL_A_LINKMODES_AUTONEG``             u8      自动协商状态
  ``ETHTOOL_A_LINKMODES_OURS``                bitset  已发布的链路模式
  ``ETHTOOL_A_LINKMODES_PEER``                bitset  对方链路模式
  ``ETHTOOL_A_LINKMODES_SPEED``               u32     链路速度 (Mb/s)
  ``ETHTOOL_A_LINKMODES_DUPLEX``              u8      双工模式
  ``ETHTOOL_A_LINKMODES_MASTER_SLAVE_CFG``    u8      主/从端口模式
  ``ETHTOOL_A_LINKMODES_MASTER_SLAVE_STATE``  u8      主/从端口状态
  ``ETHTOOL_A_LINKMODES_RATE_MATCHING``       u8      PHY 速率匹配
  ==========================================  ======  ==========================

对于 `ETHTOOL_A_LINKMODES_OURS`，值表示已发布的模式，而掩码表示支持的模式。响应中的 `ETHTOOL_A_LINKMODES_PEER` 是一个位列表。
`LINKMODES_GET` 允许执行转储请求（内核为所有支持该请求的设备返回响应消息）。
LINKMODES_SET
=============

请求内容：

  ==========================================  ======  ==========================
  ``ETHTOOL_A_LINKMODES_HEADER``              nested  请求头
  ``ETHTOOL_A_LINKMODES_AUTONEG``             u8      自动协商状态
  ``ETHTOOL_A_LINKMODES_OURS``                bitset  已发布的链路模式
  ``ETHTOOL_A_LINKMODES_PEER``                bitset  对方链路模式
  ``ETHTOOL_A_LINKMODES_SPEED``               u32     链路速度 (Mb/s)
  ``ETHTOOL_A_LINKMODES_DUPLEX``              u8      双工模式
  ``ETHTOOL_A_LINKMODES_MASTER_SLAVE_CFG``    u8      主/从端口模式
  ``ETHTOOL_A_LINKMODES_RATE_MATCHING``       u8      PHY 速率匹配
  ``ETHTOOL_A_LINKMODES_LANES``               u32     车道
  ==========================================  ======  ==========================

`ETHTOOL_A_LINKMODES_OURS` 位集允许设置已发布的链路模式。如果自动协商处于打开状态（现在设置或之前保留的状态），未更改已发布的模式（没有 `ETHTOOL_A_LINKMODES_OURS` 属性），并且至少指定了速度、双工和车道之一，则内核会根据速度、双工、车道或全部（按指定的内容）调整已发布的模式以匹配所有支持的模式。
此自动选择是在 ethtool 层面通过 ioctl 接口完成的，netlink 接口旨在允许请求更改而无需确切知道内核支持什么功能。

LINKSTATE_GET
=============
请求链路状态信息。提供链路上/下标志（由 `ETHTOOL_GLINK` ioctl 命令提供）。可选地，也可以提供扩展状态。一般来说，扩展状态描述了端口为何处于关闭状态或为何以某种非直观模式运行的原因。此请求没有属性。
请求内容：

  * `ETHTOOL_A_LINKSTATE_HEADER`：嵌套 - 请求头

内核响应内容：

  * `ETHTOOL_A_LINKSTATE_HEADER`：嵌套 - 回复头
  * `ETHTOOL_A_LINKSTATE_LINK`：布尔值 - 链路状态（上/下）
  * `ETHTOOL_A_LINKSTATE_SQI`：u32 - 当前信号质量指数
  * `ETHTOOL_A_LINKSTATE_SQI_MAX`：u32 - 最大支持 SQI 值
  * `ETHTOOL_A_LINKSTATE_EXT_STATE`：u8 - 链路扩展状态
  * `ETHTOOL_A_LINKSTATE_EXT_SUBSTATE`：u8 - 链路扩展子状态
  * `ETHTOOL_A_LINKSTATE_EXT_DOWN_CNT`：u32 - 链路关闭事件计数

对于大多数 NIC 驱动程序，`ETHTOOL_A_LINKSTATE_LINK` 的值返回由 `netif_carrier_ok()` 提供的载波标志，但也有驱动程序定义了它们自己的处理方法。
`ETHTOOL_A_LINKSTATE_EXT_STATE` 和 `ETHTOOL_A_LINKSTATE_EXT_SUBSTATE` 是可选值。ethtool 核心可以同时提供 `ETHTOOL_A_LINKSTATE_EXT_STATE` 和 `ETHTOOL_A_LINKSTATE_EXT_SUBSTATE`，或者只提供 `ETHTOOL_A_LINKSTATE_EXT_STATE`，或者两者都不提供。
`LINKSTATE_GET` 允许进行转储请求（内核为所有支持该请求的设备返回回复消息）。

链路扩展状态：

  * `ETHTOOL_LINK_EXT_STATE_AUTONEG`：与自动协商相关或其中的问题
  * `ETHTOOL_LINK_EXT_STATE_LINK_TRAINING_FAILURE`：链接训练期间失败
  * `ETHTOOL_LINK_EXT_STATE_LINK_LOGICAL_MISMATCH`：物理编码子层或前向纠错子层中的逻辑不匹配
  * `ETHTOOL_LINK_EXT_STATE_BAD_SIGNAL_INTEGRITY`：信号完整性问题
  * `ETHTOOL_LINK_EXT_STATE_NO_CABLE`：未连接电缆
  * `ETHTOOL_LINK_EXT_STATE_CABLE_ISSUE`：故障与电缆相关，例如不支持的电缆
  * `ETHTOOL_LINK_EXT_STATE_EEPROM_ISSUE`：故障与 EEPROM 相关，例如读取或解析数据时出错
  * `ETHTOOL_LINK_EXT_STATE_CALIBRATION_FAILURE`：校准算法期间失败
  * `ETHTOOL_LINK_EXT_STATE_POWER_BUDGET_EXCEEDED`：硬件无法提供电缆或模块所需的功率
  * `ETHTOOL_LINK_EXT_STATE_OVERHEAT`：模块过热
  * `ETHTOOL_LINK_EXT_STATE_MODULE`：收发器模块问题

链路扩展子状态：

  自动协商子状态：

  * `ETHTOOL_LINK_EXT_SUBSTATE_AN_NO_PARTNER_DETECTED`：对等方已关闭
  * `ETHTOOL_LINK_EXT_SUBSTATE_AN_ACK_NOT_RECEIVED`：未从对等方收到确认
  * `ETHTOOL_LINK_EXT_SUBSTATE_AN_NEXT_PAGE_EXCHANGE_FAILED`：下一页交换失败
  * `ETHTOOL_LINK_EXT_SUBSTATE_AN_NO_PARTNER_DETECTED_FORCE_MODE`：强制模式下对等方已关闭或双方速度不一致
  * `ETHTOOL_LINK_EXT_SUBSTATE_AN_FEC_MISMATCH_DURING_OVERRIDE`：双方的前向纠错模式不一致
  * `ETHTOOL_LINK_EXT_SUBSTATE_AN_NO_HCD`：没有最高公因数

  链路训练子状态：

  * `ETHTOOL_LINK_EXT_SUBSTATE_LT_KR_FRAME_LOCK_NOT_ACQUIRED`：帧未被识别，锁定失败
  * `ETHTOOL_LINK_EXT_SUBSTATE_LT_KR_LINK_INHIBIT_TIMEOUT`：在超时前未发生锁定
  * `ETHTOOL_LINK_EXT_SUBSTATE_LT_KR_LINK_PARTNER_DID_NOT_SET_RECEIVER_READY`：训练过程后，对等方未发送准备信号
  * `ETHTOOL_LINK_EXT_SUBSTATE_LT_REMOTE_FAULT`：远端尚未准备好

  链路逻辑不匹配子状态：

  * `ETHTOOL_LINK_EXT_SUBSTATE_LLM_PCS_DID_NOT_ACQUIRE_BLOCK_LOCK`：物理编码子层在第一阶段未锁定 - 块锁
  * `ETHTOOL_LINK_EXT_SUBSTATE_LLM_PCS_DID_NOT_ACQUIRE_AM_LOCK`：物理编码子层在第二阶段未锁定 - 对齐标记锁
  * `ETHTOOL_LINK_EXT_SUBSTATE_LLM_PCS_DID_NOT_GET_ALIGN_STATUS`：物理编码子层未获得对齐状态
  * `ETHTOOL_LINK_EXT_SUBSTATE_LLM_FC_FEC_IS_NOT_LOCKED`：FC 前向纠错未锁定
  * `ETHTOOL_LINK_EXT_SUBSTATE_LLM_RS_FEC_IS_NOT_LOCKED`：RS 前向纠错未锁定

  信号完整性问题子状态：

  * `ETHTOOL_LINK_EXT_SUBSTATE_BSI_LARGE_NUMBER_OF_PHYSICAL_ERRORS`：大量物理错误
  * `ETHTOOL_LINK_EXT_SUBSTATE_BSI_UNSUPPORTED_RATE`：系统试图以正式不支持的速度运行电缆，导致信号完整性问题
  * `ETHTOOL_LINK_EXT_SUBSTATE_BSI_SERDES_REFERENCE_CLOCK_LOST`：SerDes 的外部时钟信号太弱或不可用
  * `ETHTOOL_LINK_EXT_SUBSTATE_BSI_SERDES_ALOS`：SerDes 接收到的信号太弱，因为模拟信号丢失

  电缆问题子状态：

  * `ETHTOOL_LINK_EXT_SUBSTATE_CI_UNSUPPORTED_CABLE`：不支持的电缆
  * `ETHTOOL_LINK_EXT_SUBSTATE_CI_CABLE_TEST_FAILURE`：电缆测试失败

  收发器模块问题子状态：

  * `ETHTOOL_LINK_EXT_SUBSTATE_MODULE_CMIS_NOT_READY`：CMIS 模块状态机未达到模块就绪状态。例如，如果模块卡在模块故障状态

DEBUG_GET
=========
请求设备的调试设置。目前，仅提供消息掩码。
请求内容：

  * `ETHTOOL_A_DEBUG_HEADER`：嵌套 - 请求头

内核响应内容：

  * `ETHTOOL_A_DEBUG_HEADER`：嵌套 - 回复头
  * `ETHTOOL_A_DEBUG_MSGMASK`：位集 - 消息掩码

消息掩码 (`ETHTOOL_A_DEBUG_MSGMASK`) 等同于由 ioctl 接口中 `ETHTOOL_GMSGLVL` 提供并由 `ETHTOOL_SMSGLVL` 设置的消息级别。虽然由于历史原因它被称为消息级别，但大多数驱动程序以及几乎所有较新的驱动程序将其用作启用消息类别的掩码（由 `NETIF_MSG_*` 常量表示）；因此 netlink 接口遵循其实际使用情况。
`DEBUG_GET` 允许进行转储请求（内核为所有支持该请求的设备返回回复消息）。
### DEBUG_SET
=====

设置或更新设备的调试设置。目前，仅支持消息掩码。
请求内容：

  ====================================  ======  ==========================
  ``ETHTOOL_A_DEBUG_HEADER``            嵌套    请求头
  ``ETHTOOL_A_DEBUG_MSGMASK``           位集    消息掩码
  ====================================  ======  ==========================

通过``ETHTOOL_A_DEBUG_MSGMASK``位集可以设置或修改设备启用的调试消息类型的掩码。

### WOL_GET
=====

查询设备的唤醒局域网（Wake-on-LAN, WoL）设置。与大多数“GET”类型请求不同的是，“ETHTOOL_MSG_WOL_GET”需要（网络命名空间）`CAP_NET_ADMIN`权限，因为它可能提供保密的SecureOn™密码。
请求内容：

  ====================================  ======  ==========================
  ``ETHTOOL_A_WOL_HEADER``              嵌套    请求头
  ====================================  ======  ==========================

内核响应内容：

  ====================================  ======  ==========================
  ``ETHTOOL_A_WOL_HEADER``              嵌套    响应头
  ``ETHTOOL_A_WOL_MODES``               位集    启用的WoL模式掩码
  ``ETHTOOL_A_WOL_SOPASS``              二进制   SecureOn™密码
  ====================================  ======  ==========================

在响应中，``ETHTOOL_A_WOL_MODES``掩码由设备支持的模式组成，并表示已启用模式的值。“ETHTOOL_A_WOL_SOPASS”仅在设备支持“WAKE_MAGICSECURE”模式时包含在响应中。

### WOL_SET
=====

设置或更新唤醒局域网（WoL）设置。
请求内容：

  ====================================  ======  ==========================
  ``ETHTOOL_A_WOL_HEADER``              嵌套    请求头
  ``ETHTOOL_A_WOL_MODES``               位集    启用的WoL模式
  ``ETHTOOL_A_WOL_SOPASS``              二进制   SecureOn™密码
  ====================================  ======  ==========================

``ETHTOOL_A_WOL_SOPASS``仅允许用于支持`WAKE_MAGICSECURE`模式的设备。

### FEATURES_GET
=====

获取网络设备特性，类似于`ETHTOOL_GFEATURES` ioctl请求。
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

内核响应中的位图具有与ioctl干扰中使用的位图相同的含义，但属性名称不同（基于net_device结构的相关成员）。传统“标志”未提供，如果用户空间需要它们（最有可能是为了向后兼容性），它可以自己从相关的特性位计算它们的值。
`ETHA_FEATURES_HW`使用由内核识别的所有特性组成的掩码（为了在使用详细的位图格式时提供所有名称），其他三个使用无掩码（简单的位列表）。

### FEATURES_SET
=====

设置网络设备特性的请求，类似于`ETHTOOL_SFEATURES` ioctl请求。
请求内容：

  ====================================  ======  ==========================
  ``ETHTOOL_A_FEATURES_HEADER``         嵌套    请求头
  ``ETHTOOL_A_FEATURES_WANTED``         位集    请求的功能
  ====================================  ======  ==========================

内核响应内容：

  ====================================  ======  ==========================
  ``ETHTOOL_A_FEATURES_HEADER``         嵌套    响应头
  ``ETHTOOL_A_FEATURES_WANTED``         位集    请求与结果的差异
  ``ETHTOOL_A_FEATURES_ACTIVE``         位集    新旧活动功能的差异
  ====================================  ======  ==========================

请求中仅包含一个位集，它可以是一个值/掩码对（请求更改特定功能位并保持其余部分不变），或者仅是一个值（请求将所有功能设置为指定的集合）。
由于请求需经过 `netdev_change_features()` 的合理性检查，可选的内核响应（可通过在请求头中设置 `ETHTOOL_FLAG_OMIT_REPLY` 标志来抑制）会告知客户端实际的结果。`ETHTOOL_A_FEATURES_WANTED` 报告客户端请求与实际结果之间的差异：掩码包含请求的功能与结果（操作后的 dev->features）之间不同的位；值则包含这些位在请求中的值（即结果功能的反值）。`ETHTOOL_A_FEATURES_ACTIVE` 报告新旧 dev->features 之间的差异：掩码包含发生变化的位，值则是这些位在新的 dev->features（操作后）中的值。

`ETHTOOL_MSG_FEATURES_NTF` 通知不仅会在使用 `ETHTOOL_MSG_FEATURES_SET` 请求或 ethtool ioctl 请求修改设备功能时发送，而且在每次使用 `netdev_update_features()` 或 `netdev_change_features()` 修改功能时也会发送。

PRIVFLAGS_GET
=============

获取私有标志，类似于 `ETHTOOL_GPFLAGS` ioctl 请求
请求内容：

  ====================================  ======  ==========================
  ``ETHTOOL_A_PRIVFLAGS_HEADER``        嵌套    请求头
  ====================================  ======  ==========================

内核响应内容：

  ====================================  ======  ==========================
  ``ETHTOOL_A_PRIVFLAGS_HEADER``        嵌套    响应头
  ``ETHTOOL_A_PRIVFLAGS_FLAGS``         位集    私有标志
  ====================================  ======  ==========================

`ETHTOOL_A_PRIVFLAGS_FLAGS` 是一个位集，包含了设备的私有标志值。
这些标志由驱动程序定义，它们的数量和名称（以及含义）依赖于设备。为了紧凑的位集格式，名称可以通过 `ETH_SS_PRIV_FLAGS` 字符串集获取。如果请求详细的位集格式，响应会使用设备支持的所有私有标志作为掩码，以便客户端能够获取完整的信息而无需获取带有名称的字符串集。

PRIVFLAGS_SET
=============

设置或修改设备私有标志的值，类似于 `ETHTOOL_SPFLAGS` ioctl 请求
请求内容：

  ====================================  ======  ==========================
  ``ETHTOOL_A_PRIVFLAGS_HEADER``        嵌套    请求头
  ``ETHTOOL_A_PRIVFLAGS_FLAGS``         位集    私有标志
  ====================================  ======  ==========================

`ETHTOOL_A_PRIVFLAGS_FLAGS` 可以设置整个私有标志集或仅修改其中某些值。

RINGS_GET
=========

获取环大小，类似于 `ETHTOOL_GRINGPARAM` ioctl 请求
请求内容：

  ====================================  ======  ==========================
  ``ETHTOOL_A_RINGS_HEADER``            嵌套    请求头
  ====================================  ======  ==========================

内核响应内容：

  =======================================   ======  ===========================
  ``ETHTOOL_A_RINGS_HEADER``                嵌套    响应头
  ``ETHTOOL_A_RINGS_RX_MAX``                u32     RX 环的最大尺寸
  ``ETHTOOL_A_RINGS_RX_MINI_MAX``           u32     RX 小环的最大尺寸
  ``ETHTOOL_A_RINGS_RX_JUMBO_MAX``          u32     RX 大环的最大尺寸
  ``ETHTOOL_A_RINGS_TX_MAX``                u32     TX 环的最大尺寸
  ``ETHTOOL_A_RINGS_RX``                    u32     RX 环的尺寸
  ``ETHTOOL_A_RINGS_RX_MINI``               u32     RX 小环的尺寸
  ``ETHTOOL_A_RINGS_RX_JUMBO``              u32     RX 大环的尺寸
  ``ETHTOOL_A_RINGS_TX``                    u32     TX 环的尺寸
  ``ETHTOOL_A_RINGS_RX_BUF_LEN``            u32     环上缓冲区的尺寸
  ``ETHTOOL_A_RINGS_TCP_DATA_SPLIT``        u8      TCP 头/数据分离
  ``ETHTOOL_A_RINGS_CQE_SIZE``              u32     TX/RX CQE 的尺寸
  ``ETHTOOL_A_RINGS_TX_PUSH``               u8      TX 推送模式标志
  ``ETHTOOL_A_RINGS_RX_PUSH``               u8      RX 推送模式标志
  ``ETHTOOL_A_RINGS_TX_PUSH_BUF_LEN``       u32     TX 推送缓冲区尺寸
  ``ETHTOOL_A_RINGS_TX_PUSH_BUF_LEN_MAX``   u32     TX 推送缓冲区最大尺寸
  =======================================   ======  ===========================

`ETHTOOL_A_RINGS_TCP_DATA_SPLIT` 表示设备是否可用于页翻转 TCP 零复制接收 (`getsockopt(TCP_ZEROCOPY_RECEIVE)`)。
如果启用，设备将被配置为将帧头和数据分别放入不同的缓冲区。设备配置必须能够接收完整的内存页数据，例如因为MTU足够大或者通过硬件巨型帧聚合（HW-GRO）实现。
`ETHTOOL_A_RINGS_[RX|TX]_PUSH` 标志用于启用快速路径来发送或接收数据包。在普通路径中，驱动程序在DRAM中填充描述符并通知NIC硬件。在快速路径中，驱动程序通过MMIO写操作将描述符推送到设备，从而减少了延迟。然而，启用此功能可能会增加CPU成本。驱动程序可能强制实施额外的每个数据包资格检查（例如，基于数据包大小的检查）。
`ETHTOOL_A_RINGS_TX_PUSH_BUF_LEN` 指定了驱动程序可以直接推送到底层设备（“推送”模式）的一个发送数据包的最大字节数。将部分有效负载字节推送到设备的优点在于避免了DMA映射，从而减少了小数据包的延迟（与 `ETHTOOL_A_RINGS_TX_PUSH` 参数相同），同时也允许底层设备在获取其有效负载之前处理数据包头部。
这有助于设备根据数据包的头部快速采取行动。
这类似于“tx-copybreak”参数，该参数将数据包复制到预先分配的DMA内存区域而不是映射新内存。但是，“tx-push-buff”参数将数据包直接复制到设备中，以便设备能够对数据包采取更快的动作。

### RINGS_SET
#### 设置环大小，类似 `ETHTOOL_SRINGPARAM` ioctl 请求
请求内容：

  - `ETHTOOL_A_RINGS_HEADER`    嵌套回复头
  - `ETHTOOL_A_RINGS_RX`        u32 接收环大小
  - `ETHTOOL_A_RINGS_RX_MINI`   u32 接收微型环大小
  - `ETHTOOL_A_RINGS_RX_JUMBO`  u32 接收巨型环大小
  - `ETHTOOL_A_RINGS_TX`        u32 发送环大小
  - `ETHTOOL_A_RINGS_RX_BUF_LEN`u32 环上的缓冲区大小
  - `ETHTOOL_A_RINGS_CQE_SIZE`  u32 TX/RX 完成队列事件（CQE）大小
  - `ETHTOOL_A_RINGS_TX_PUSH`   u8 发送推送模式标志
  - `ETHTOOL_A_RINGS_RX_PUSH`   u8 接收推送模式标志
  - `ETHTOOL_A_RINGS_TX_PUSH_BUF_LEN`u32 发送推送缓冲区大小

内核会检查请求的环大小是否超过了驱动程序报告的限制。驱动程序可能施加额外的约束，并且可能不支持所有属性。
`ETHTOOL_A_RINGS_CQE_SIZE` 指定了完成队列事件（CQE）的大小。完成队列事件（CQE）是由NIC发布的事件，用来指示数据包发送（如发送成功或错误）或接收（如指向数据包片段的指针）时的状态。如果NIC支持的话，可以通过CQE大小参数来修改CQE的大小而非默认值。
较大的CQE可以包含更多的接收缓冲区指针，从而使得NIC可以从网络线传输更大的帧。根据NIC硬件，如果修改了CQE大小，则可以在驱动程序中调整整个完成队列的大小。
### CHANNELS_GET
获取通道数量，类似于`ETHTOOL_GCHANNELS` ioctl 请求。
请求内容：

  - `ETHTOOL_A_CHANNELS_HEADER`：嵌套的请求头

内核响应内容：

  - `ETHTOOL_A_CHANNELS_HEADER`：嵌套的回复头
  - `ETHTOOL_A_CHANNELS_RX_MAX`：u32 类型，最大接收通道数
  - `ETHTOOL_A_CHANNELS_TX_MAX`：u32 类型，最大发送通道数
  - `ETHTOOL_A_CHANNELS_OTHER_MAX`：u32 类型，最大其他类型通道数
  - `ETHTOOL_A_CHANNELS_COMBINED_MAX`：u32 类型，最大组合通道数
  - `ETHTOOL_A_CHANNELS_RX_COUNT`：u32 类型，当前接收通道数
  - `ETHTOOL_A_CHANNELS_TX_COUNT`：u32 类型，当前发送通道数
  - `ETHTOOL_A_CHANNELS_OTHER_COUNT`：u32 类型，当前其他类型通道数
  - `ETHTOOL_A_CHANNELS_COMBINED_COUNT`：u32 类型，当前组合通道数

### CHANNELS_SET
设置通道数量，类似于`ETHTOOL_SCHANNELS` ioctl 请求。
请求内容：

  - `ETHTOOL_A_CHANNELS_HEADER`：嵌套的请求头
  - `ETHTOOL_A_CHANNELS_RX_COUNT`：u32 类型，接收通道数
  - `ETHTOOL_A_CHANNELS_TX_COUNT`：u32 类型，发送通道数
  - `ETHTOOL_A_CHANNELS_OTHER_COUNT`：u32 类型，其他类型通道数
  - `ETHTOOL_A_CHANNELS_COMBINED_COUNT`：u32 类型，组合通道数

内核会检查请求的通道数是否超过由驱动程序报告的限制。驱动程序可能会施加额外的约束，并且可能不支持所有属性。

### COALESCE_GET
获取合并参数，类似于`ETHTOOL_GCOALESCE` ioctl 请求。
请求内容：

  - `ETHTOOL_A_COALESCE_HEADER`：嵌套的请求头

内核响应内容：

  - `ETHTOOL_A_COALESCE_HEADER`：嵌套的回复头
  - `ETHTOOL_A_COALESCE_RX_USECS`：u32 类型，正常接收时的延迟（微秒）
  - `ETHTOOL_A_COALESCE_RX_MAX_FRAMES`：u32 类型，正常接收时的最大数据包数
  - `ETHTOOL_A_COALESCE_RX_USECS_IRQ`：u32 类型，中断上下文中的接收延迟（微秒）
  - `ETHTOOL_A_COALESCE_RX_MAX_FRAMES_IRQ`：u32 类型，中断上下文中的接收最大数据包数
  - `ETHTOOL_A_COALESCE_TX_USECS`：u32 类型，正常发送时的延迟（微秒）
  - `ETHTOOL_A_COALESCE_TX_MAX_FRAMES`：u32 类型，正常发送时的最大数据包数
  - `ETHTOOL_A_COALESCE_TX_USECS_IRQ`：u32 类型，中断上下文中的发送延迟（微秒）
  - `ETHTOOL_A_COALESCE_TX_MAX_FRAMES_IRQ`：u32 类型，中断上下文中的发送最大数据包数
  - `ETHTOOL_A_COALESCE_STATS_BLOCK_USECS`：u32 类型，统计更新的延迟
  - `ETHTOOL_A_COALESCE_USE_ADAPTIVE_RX`：布尔值，自适应接收合并
  - `ETHTOOL_A_COALESCE_USE_ADAPTIVE_TX`：布尔值，自适应发送合并
  - `ETHTOOL_A_COALESCE_PKT_RATE_LOW`：u32 类型，低速率阈值
  - `ETHTOOL_A_COALESCE_RX_USECS_LOW`：u32 类型，低速率接收时的延迟（微秒）
  - `ETHTOOL_A_COALESCE_RX_MAX_FRAMES_LOW`：u32 类型，低速率接收时的最大数据包数
  - `ETHTOOL_A_COALESCE_TX_USECS_LOW`：u32 类型，低速率发送时的延迟（微秒）
  - `ETHTOOL_A_COALESCE_TX_MAX_FRAMES_LOW`：u32 类型，低速率发送时的最大数据包数
  - `ETHTOOL_A_COALESCE_PKT_RATE_HIGH`：u32 类型，高速率阈值
  - `ETHTOOL_A_COALESCE_RX_USECS_HIGH`：u32 类型，高速率接收时的延迟（微秒）
  - `ETHTOOL_A_COALESCE_RX_MAX_FRAMES_HIGH`：u32 类型，高速率接收时的最大数据包数
  - `ETHTOOL_A_COALESCE_TX_USECS_HIGH`：u32 类型，高速率发送时的延迟（微秒）
  - `ETHTOOL_A_COALESCE_TX_MAX_FRAMES_HIGH`：u32 类型，高速率发送时的最大数据包数
  - `ETHTOOL_A_COALESCE_RATE_SAMPLE_INTERVAL`：u32 类型，速率采样间隔
  - `ETHTOOL_A_COALESCE_USE_CQE_TX`：布尔值，发送时使用完成队列事件模式
  - `ETHTOOL_A_COALESCE_USE_CQE_RX`：布尔值，接收时使用完成队列事件模式
  - `ETHTOOL_A_COALESCE_TX_AGGR_MAX_BYTES`：u32 类型，发送聚合的最大字节数
  - `ETHTOOL_A_COALESCE_TX_AGGR_MAX_FRAMES`：u32 类型，发送聚合的最大帧数
  - `ETHTOOL_A_COALESCE_TX_AGGR_TIME_USECS`：u32 类型，发送聚合的时间（微秒）
  - `ETHTOOL_A_COALESCE_RX_PROFILE`：嵌套的接收维度配置文件
  - `ETHTOOL_A_COALESCE_TX_PROFILE`：嵌套的发送维度配置文件

只有当某个属性的值非零或在`ethtool_ops::supported_coalesce_params`中对应的位被设置（即被声明为驱动程序支持）时，该属性才会包含在回复中。
完成队列事件模式（`ETHTOOL_A_COALESCE_USE_CQE_TX` 和 `ETHTOOL_A_COALESCE_USE_CQE_RX`）控制数据包到达与基于时间的延迟参数之间的交互。默认情况下，定时器预计用于限制任何数据包到达/离开和相应中断之间最大延迟。在这种模式下，定时器应由数据包到达（有时是前一个中断的传递）启动，并在中断传递时重置。
将相应的属性设置为1将启用`CQE`模式，在这种模式下每个数据包事件都会重置定时器。在这种模式下，定时器用于在队列空闲时强制中断，而繁忙队列依赖于数据包限制来触发中断。
发送聚合包括将帧复制到连续缓冲区以便作为单个I/O操作提交。`ETHTOOL_A_COALESCE_TX_AGGR_MAX_BYTES`描述了提交缓冲区的最大字节数。
`ETHTOOL_A_COALESCE_TX_AGGR_MAX_FRAMES`描述了可以聚合到单个缓冲区中的最大帧数。
``ETHTOOL_A_COALESCE_TX_AGGR_TIME_USECS`` 描述了自聚合块中第一个数据包到达后，经过的微秒数，在这段时间结束后应该发送该块。
此功能主要对某些处理频繁的小尺寸URB传输不好的USB设备感兴趣。

``ETHTOOL_A_COALESCE_RX_PROFILE`` 和 ``ETHTOOL_A_COALESCE_TX_PROFILE`` 指向DIM参数，详情请参阅 `通用网络动态中断调节 (Net DIM) <https://www.kernel.org/doc/Documentation/networking/net_dim.rst>`_。

**COALESCE_SET**

设置类似于 ``ETHTOOL_SCOALESCE`` ioctl请求的聚合参数。请求内容如下：

  ===========================================  ======  =======================
  ``ETHTOOL_A_COALESCE_HEADER``                nested  请求头
  ``ETHTOOL_A_COALESCE_RX_USECS``              u32     延迟（微秒），正常接收
  ``ETHTOOL_A_COALESCE_RX_MAX_FRAMES``         u32     最大数据包数，正常接收
  ``ETHTOOL_A_COALESCE_RX_USECS_IRQ``          u32     延迟（微秒），IRQ中的接收
  ``ETHTOOL_A_COALESCE_RX_MAX_FRAMES_IRQ``     u32     最大数据包数，IRQ中的接收
  ``ETHTOOL_A_COALESCE_TX_USECS``              u32     延迟（微秒），正常发送
  ``ETHTOOL_A_COALESCE_TX_MAX_FRAMES``         u32     最大数据包数，正常发送
  ``ETHTOOL_A_COALESCE_TX_USECS_IRQ``          u32     延迟（微秒），IRQ中的发送
  ``ETHTOOL_A_COALESCE_TX_MAX_FRAMES_IRQ``     u32     IRQ数据包数，IRQ中的发送
  ``ETHTOOL_A_COALESCE_STATS_BLOCK_USECS``     u32     统计更新延迟
  ``ETHTOOL_A_COALESCE_USE_ADAPTIVE_RX``       bool    自适应接收聚合
  ``ETHTOOL_A_COALESCE_USE_ADAPTIVE_TX``       bool    自适应发送聚合
  ``ETHTOOL_A_COALESCE_PKT_RATE_LOW``          u32     低速率阈值
  ``ETHTOOL_A_COALESCE_RX_USECS_LOW``          u32     延迟（微秒），低接收速率
  ``ETHTOOL_A_COALESCE_RX_MAX_FRAMES_LOW``     u32     最大数据包数，低接收速率
  ``ETHTOOL_A_COALESCE_TX_USECS_LOW``          u32     延迟（微秒），低发送速率
  ``ETHTOOL_A_COALESCE_TX_MAX_FRAMES_LOW``     u32     最大数据包数，低发送速率
  ``ETHTOOL_A_COALESCE_PKT_RATE_HIGH``         u32     高速率阈值
  ``ETHTOOL_A_COALESCE_RX_USECS_HIGH``         u32     延迟（微秒），高接收速率
  ``ETHTOOL_A_COALESCE_RX_MAX_FRAMES_HIGH``    u32     最大数据包数，高接收速率
  ``ETHTOOL_A_COALESCE_TX_USECS_HIGH``         u32     延迟（微秒），高发送速率
  ``ETHTOOL_A_COALESCE_TX_MAX_FRAMES_HIGH``    u32     最大数据包数，高发送速率
  ``ETHTOOL_A_COALESCE_RATE_SAMPLE_INTERVAL``  u32     速率采样间隔
  ``ETHTOOL_A_COALESCE_USE_CQE_TX``            bool    定时器重置模式，发送
  ``ETHTOOL_A_COALESCE_USE_CQE_RX``            bool    定时器重置模式，接收
  ``ETHTOOL_A_COALESCE_TX_AGGR_MAX_BYTES``     u32     最大聚合大小，发送
  ``ETHTOOL_A_COALESCE_TX_AGGR_MAX_FRAMES``    u32     最大聚合数据包数，发送
  ``ETHTOOL_A_COALESCE_TX_AGGR_TIME_USECS``    u32     时间（微秒），聚合，发送
  ``ETHTOOL_A_COALESCE_RX_PROFILE``            nested  DIM配置文件，接收
  ``ETHTOOL_A_COALESCE_TX_PROFILE``            nested  DIM配置文件，发送
  ===========================================  ======  =======================

如果驱动程序声明请求属性不受支持（即在 ``ethtool_ops::supported_coalesce_params`` 中对应的位未被设置），无论其值如何，请求都会被拒绝。驱动程序可能会对聚合参数及其值施加额外的约束。
与通过 ``ioctl()`` netlink版本的请求相比，此请求将更努力地确保用户指定的值已应用，并可能调用驱动程序两次。

**PAUSE_GET**

获取类似于 ``ETHTOOL_GPAUSEPARAM`` ioctl请求的暂停帧设置。请求内容如下：

  =====================================  ======  ==========================
  ``ETHTOOL_A_PAUSE_HEADER``             nested  请求头
  ``ETHTOOL_A_PAUSE_STATS_SRC``          u32     统计来源
  =====================================  ======  ==========================

``ETHTOOL_A_PAUSE_STATS_SRC`` 是可选的。它取值自：

.. kernel-doc:: include/uapi/linux/ethtool.h
    :identifiers: ethtool_mac_stats_src

如果请求中没有提供，则响应中会以 ``ETHTOOL_A_PAUSE_STATS_SRC`` 属性提供统计信息，其值等于 ``ETHTOOL_MAC_STATS_SRC_AGGREGATE``。
内核响应内容如下：

  =====================================  ======  ==========================
  ``ETHTOOL_A_PAUSE_HEADER``             nested  请求头
  ``ETHTOOL_A_PAUSE_AUTONEG``            bool    暂停自动协商
  ``ETHTOOL_A_PAUSE_RX``                 bool    接收暂停帧
  ``ETHTOOL_A_PAUSE_TX``                 bool    发送暂停帧
  ``ETHTOOL_A_PAUSE_STATS``              nested  暂停统计
  =====================================  ======  ==========================

如果在 ``ETHTOOL_A_HEADER_FLAGS`` 中设置了 ``ETHTOOL_FLAG_STATS`` 标志，则会报告 ``ETHTOOL_A_PAUSE_STATS``。
如果驱动程序没有报告任何统计信息，则该统计信息将是空的。驱动程序按照以下结构填写统计信息：

.. kernel-doc:: include/linux/ethtool.h
    :identifiers: ethtool_pause_stats

每个成员都有一个对应的属性定义

PAUSE_SET
=========

设置暂停参数，类似于 `ETHTOOL_GPAUSEPARAM` ioctl 请求
请求内容：

  =====================================  ======  ==========================
  ``ETHTOOL_A_PAUSE_HEADER``             嵌套    请求头
  ``ETHTOOL_A_PAUSE_AUTONEG``            布尔    暂停自动协商
  ``ETHTOOL_A_PAUSE_RX``                 布尔    接收暂停帧
  ``ETHTOOL_A_PAUSE_TX``                 布尔    发送暂停帧
  =====================================  ======  ==========================


EEE_GET
=======

获取能源效率以太网（EEE）设置，类似于 `ETHTOOL_GEEE` ioctl 请求
请求内容：

  =====================================  ======  ==========================
  ``ETHTOOL_A_EEE_HEADER``               嵌套    请求头
  =====================================  ======  ==========================

内核响应内容：

  =====================================  ======  ==========================
  ``ETHTOOL_A_EEE_HEADER``               嵌套    请求头
  ``ETHTOOL_A_EEE_MODES_OURS``           布尔    支持/宣告的模式
  ``ETHTOOL_A_EEE_MODES_PEER``           布尔    对端宣告的链路模式
  ``ETHTOOL_A_EEE_ACTIVE``               布尔    EEE正在使用中
  ``ETHTOOL_A_EEE_ENABLED``              布尔    EEE已启用
  ``ETHTOOL_A_EEE_TX_LPI_ENABLED``       布尔    发送LPI已启用
  ``ETHTOOL_A_EEE_TX_LPI_TIMER``         u32     发送LPI超时时间（微秒）
  =====================================  ======  ==========================

在 ``ETHTOOL_A_EEE_MODES_OURS`` 中，掩码由启用了EEE的链路模式组成，值为宣告了EEE的链路模式。对端宣告了EEE的链路模式列在 ``ETHTOOL_A_EEE_MODES_PEER`` 中（没有掩码）。Netlink接口允许报告所有链路模式的EEE状态，但只有前32个是由 `ethtool_ops` 回调提供的。
EEE_SET
=======

设置能源效率以太网（EEE）参数，类似于 `ETHTOOL_SEEE` ioctl 请求
请求内容：

  =====================================  ======  ==========================
  ``ETHTOOL_A_EEE_HEADER``               嵌套    请求头
  ``ETHTOOL_A_EEE_MODES_OURS``           布尔    宣告的模式
  ``ETHTOOL_A_EEE_ENABLED``              布尔    EEE已启用
  ``ETHTOOL_A_EEE_TX_LPI_ENABLED``       布尔    发送LPI已启用
  ``ETHTOOL_A_EEE_TX_LPI_TIMER``         u32     发送LPI超时时间（微秒）
  =====================================  ======  ==========================

``ETHTOOL_A_EEE_MODES_OURS`` 用于列出要宣告EEE的链路模式（如果没有掩码），或者指定列表的更改（如果有掩码）。Netlink接口允许报告所有链路模式的EEE状态，但目前只能设置前32个，因为这是 `ethtool_ops` 回调所支持的。
TSINFO_GET
==========

获取时间戳信息，类似于 `ETHTOOL_GET_TS_INFO` ioctl 请求
请求内容：

  =====================================  ======  ==========================
  ``ETHTOOL_A_TSINFO_HEADER``            嵌套    请求头
  =====================================  ======  ==========================

内核响应内容：

  =====================================  ======  ==========================
  ``ETHTOOL_A_TSINFO_HEADER``            嵌套    请求头
  ``ETHTOOL_A_TSINFO_TIMESTAMPING``      位集    SO_TIMESTAMPING 标志
  ``ETHTOOL_A_TSINFO_TX_TYPES``          位集    支持的发送类型
  ``ETHTOOL_A_TSINFO_RX_FILTERS``        位集    支持的接收过滤器
  ``ETHTOOL_A_TSINFO_PHC_INDEX``         u32     PTP硬件时钟索引
  ``ETHTOOL_A_TSINFO_STATS``             嵌套    硬件时间戳统计信息
  =====================================  ======  ==========================

如果不存在关联的PHC（没有特殊值来表示这种情况），则不包含 ``ETHTOOL_A_TSINFO_PHC_INDEX`` 。如果位集为空（没有位被设置），则省略位集属性。
额外的硬件时间戳统计信息响应内容：

  =====================================  ======  ===================================
  ``ETHTOOL_A_TS_STAT_TX_PKTS``          uint    具有发送硬件时间戳的报文数
  ``ETHTOOL_A_TS_STAT_TX_LOST``          uint    发送硬件时间戳未到达计数
  ``ETHTOOL_A_TS_STAT_TX_ERR``           uint    请求发送时间戳的硬件错误计数
  =====================================  ======  ===================================

CABLE_TEST
==========

启动电缆测试
请求内容：

  ====================================  ======  ==========================
  ``ETHTOOL_A_CABLE_TEST_HEADER``       嵌套    请求头
  ====================================  ======  ==========================

通知内容：

一条以太网电缆通常包含1、2或4对线。只有当一对线存在故障并且因此产生反射时，才能测量出这组线的长度。关于故障的信息可能不可用，具体取决于特定的硬件。因此，通知消息的内容大多是可选的。这些属性可以任意次数重复，以任意顺序排列，适用于任意数量的线对。
该示例展示了对T2线缆（即两对线）完成测试时发送的通知。一对线正常，因此没有长度信息；第二对线存在故障，并带有长度信息。
+---------------------------------------------+--------+---------------------+
| ``ETHTOOL_A_CABLE_TEST_HEADER``             | 嵌套    | 回复头              |
+---------------------------------------------+--------+---------------------+
| ``ETHTOOL_A_CABLE_TEST_STATUS``             | u8     | 完成                |
+---------------------------------------------+--------+---------------------+
| ``ETHTOOL_A_CABLE_TEST_NTF_NEST``           | 嵌套    | 所有结果            |
+-+-------------------------------------------+--------+---------------------+
 | ``ETHTOOL_A_CABLE_NEST_RESULT``            | 嵌套    | 线缆测试结果         |
 +-+-+-----------------------------------------+--------+---------------------+
  | ``ETHTOOL_A_CABLE_RESULTS_PAIR``          | u8     | 对号                |
 +-+-+-----------------------------------------+--------+---------------------+
  | ``ETHTOOL_A_CABLE_RESULTS_CODE``          | u8     | 结果代码            |
 +-+-+-----------------------------------------+--------+---------------------+
 | ``ETHTOOL_A_CABLE_NEST_RESULT``            | 嵌套    | 线缆测试结果         |
 +-+-+-----------------------------------------+--------+---------------------+
  | ``ETHTOOL_A_CABLE_RESULTS_PAIR``          | u8     | 对号                |
 +-+-+-----------------------------------------+--------+---------------------+
  | ``ETHTOOL_A_CABLE_RESULTS_CODE``          | u8     | 结果代码            |
 +-+-+-----------------------------------------+--------+---------------------+
 | ``ETHTOOL_A_CABLE_NEST_FAULT_LENGTH``      | 嵌套    | 线缆长度            |
 +-+-+-----------------------------------------+--------+---------------------+
  | ``ETHTOOL_A_CABLE_FAULT_LENGTH_PAIR``     | u8     | 对号                |
 +-+-+-----------------------------------------+--------+---------------------+
  | ``ETHTOOL_A_CABLE_FAULT_LENGTH_CM``       | u32    | 长度（厘米）         |
 +-+-+-----------------------------------------+--------+---------------------+

CABLE_TEST TDR
==============

启动线缆测试并报告原始TDR数据

请求内容：

+--------------------------------------------+--------+-----------------------+
| ``ETHTOOL_A_CABLE_TEST_TDR_HEADER``        | 嵌套    | 回复头                |
+--------------------------------------------+--------+-----------------------+
| ``ETHTOOL_A_CABLE_TEST_TDR_CFG``           | 嵌套    | 测试配置              |
+-+------------------------------------------+--------+-----------------------+
 | ``ETHTOOL_A_CABLE_STEP_FIRST_DISTANCE``   | u32    | 第一个数据距离        |
 +-+-+----------------------------------------+--------+-----------------------+
 | ``ETHTOOL_A_CABLE_STEP_LAST_DISTANCE``    | u32    | 最后一个数据距离      |
 +-+-+----------------------------------------+--------+-----------------------+
 | ``ETHTOOL_A_CABLE_STEP_STEP_DISTANCE``    | u32    | 每步的距离            |
 +-+-+----------------------------------------+--------+-----------------------+
 | ``ETHTOOL_A_CABLE_TEST_TDR_CFG_PAIR``     | u8     | 要测试的对            |
 +-+-+----------------------------------------+--------+-----------------------+

``ETHTOOL_A_CABLE_TEST_TDR_CFG``及其所有成员都是可选的。所有距离均以厘米为单位表示。PHY将这些距离作为参考，并四舍五入到它实际支持的最近的距离。如果指定了某一对，则只测试这一对；否则，所有对都将被测试。
通知内容：

通过向线缆发送脉冲并记录反射脉冲的幅度来收集原始TDR数据。收集TDR数据可能需要几秒钟的时间，尤其是当在1米间隔下探测完整的100米时。当开始测试时，将发送包含仅``ETHTOOL_A_CABLE_TEST_TDR_STATUS``和值``ETHTOOL_A_CABLE_TEST_NTF_STATUS_STARTED``的通知。当测试完成后，将发送第二个通知，其中包含``ETHTOOL_A_CABLE_TEST_TDR_STATUS``和值``ETHTOOL_A_CABLE_TEST_NTF_STATUS_COMPLETED``以及TDR数据。
消息中可选地包含发送到线缆中的脉冲的幅度。这以毫伏(mV)为单位测量。反射不应大于发射脉冲。
在原始TDR数据之前应该有一个``ETHTOOL_A_CABLE_TDR_NEST_STEP``嵌套，其中包含第一次读取、最后一次读取以及每次读取之间的步长所对应线缆上的距离信息。这些距离以厘米为单位测量。这些应该是PHY实际使用的精确值。这些值可能与用户请求的不同，如果原生测量分辨率大于1厘米。
对于线缆上的每一步，使用一个``ETHTOOL_A_CABLE_TDR_NEST_AMPLITUDE``来报告给定对的反射幅度。
+---------------------------------------------+--------+----------------------+
| ``ETHTOOL_A_CABLE_TEST_TDR_HEADER``         | 嵌套    | 回复头               |
+---------------------------------------------+--------+----------------------+
| ``ETHTOOL_A_CABLE_TEST_TDR_STATUS``         | u8     | 完成                 |
+---------------------------------------------+--------+----------------------+
| ``ETHTOOL_A_CABLE_TEST_TDR_NTF_NEST``       | 嵌套    | 所有结果             |
+-+-------------------------------------------+--------+----------------------+
 | ``ETHTOOL_A_CABLE_TDR_NEST_PULSE``         | 嵌套    | 发射脉冲幅度         |
 +-+-+-----------------------------------------+--------+----------------------+
  | ``ETHTOOL_A_CABLE_PULSE_mV``              | s16    | 脉冲幅度             |
 +-+-+-----------------------------------------+--------+----------------------+
 | ``ETHTOOL_A_CABLE_NEST_STEP``              | 嵌套    | TDR步骤信息          |
 +-+-+-----------------------------------------+--------+----------------------+
  | ``ETHTOOL_A_CABLE_STEP_FIRST_DISTANCE``   | u32    | 第一个数据距离       |
 +-+-+-----------------------------------------+--------+----------------------+
  | ``ETHTOOL_A_CABLE_STEP_LAST_DISTANCE``    | u32    | 最后一个数据距离     |
 +-+-+-----------------------------------------+--------+----------------------+
  | ``ETHTOOL_A_CABLE_STEP_STEP_DISTANCE``    | u32    | 每步的距离           |
 +-+-+-----------------------------------------+--------+----------------------+
 | ``ETHTOOL_A_CABLE_TDR_NEST_AMPLITUDE``     | 嵌套    | 反射幅度             |
 +-+-+-----------------------------------------+--------+----------------------+
  | ``ETHTOOL_A_CABLE_RESULTS_PAIR``          | u8     | 对号                 |
 +-+-+-----------------------------------------+--------+----------------------+
  | ``ETHTOOL_A_CABLE_AMPLITUDE_mV``          | s16    | 反射幅度             |
 +-+-+-----------------------------------------+--------+----------------------+
 | ``ETHTOOL_A_CABLE_TDR_NEST_AMPLITUDE``     | 嵌套    | 反射幅度             |
 +-+-+-----------------------------------------+--------+----------------------+
  | ``ETHTOOL_A_CABLE_RESULTS_PAIR``          | u8     | 对号                 |
 +-+-+-----------------------------------------+--------+----------------------+
  | ``ETHTOOL_A_CABLE_AMPLITUDE_mV``          | s16    | 反射幅度             |
 +-+-+-----------------------------------------+--------+----------------------+
 | ``ETHTOOL_A_CABLE_TDR_NEST_AMPLITUDE``     | 嵌套    | 反射幅度             |
 +-+-+-----------------------------------------+--------+----------------------+
  | ``ETHTOOL_A_CABLE_RESULTS_PAIR``          | u8     | 对号                 |
 +-+-+-----------------------------------------+--------+----------------------+
  | ``ETHTOOL_A_CABLE_AMPLITUDE_mV``          | s16    | 反射幅度             |
 +-+-+-----------------------------------------+--------+----------------------+

TUNNEL_INFO
===========

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
  | ``ETHTOOL_A_TUNNEL_UDP_TABLE_TYPES``      | 位集   | 表可以持有的隧道类型 |
 +-+-+-----------------------------------------+--------+---------------------+
  | ``ETHTOOL_A_TUNNEL_UDP_TABLE_ENTRY``      | 嵌套    | 卸载的UDP端口        |
 +-+-+-+---------------------------------------+--------+---------------------+
   | ``ETHTOOL_A_TUNNEL_UDP_ENTRY_PORT``      | be16   | UDP端口              |
 +-+-+-+---------------------------------------+--------+---------------------+
   | ``ETHTOOL_A_TUNNEL_UDP_ENTRY_TYPE``      | u32    | 隧道类型             |
 +-+-+-+---------------------------------------+--------+---------------------+

对于UDP隧道表，“ETHTOOL_A_TUNNEL_UDP_TABLE_TYPES”为空表示该表包含静态条目，由NIC硬编码。
FEC_GET
=======

获取类似于 `ETHTOOL_GFECPARAM` ioctl 请求的 FEC 配置和状态
请求内容：

  =====================================  ======  ==========================
  ``ETHTOOL_A_FEC_HEADER``               嵌套     请求头
  =====================================  ======  ==========================

内核响应内容：

  =====================================  ======  ==========================
  ``ETHTOOL_A_FEC_HEADER``               嵌套     请求头
  ``ETHTOOL_A_FEC_MODES``                位集     已配置的模式
  ``ETHTOOL_A_FEC_AUTO``                 布尔值   FEC 模式自动选择
  ``ETHTOOL_A_FEC_ACTIVE``               u32      当前活动 FEC 模式的索引
  ``ETHTOOL_A_FEC_STATS``                嵌套     FEC 统计信息
  =====================================  ======  ==========================

``ETHTOOL_A_FEC_ACTIVE`` 表示接口上当前激活的 FEC 链路模式的位索引。如果设备不支持 FEC，此属性可能不存在。
``ETHTOOL_A_FEC_MODES`` 和 ``ETHTOOL_A_FEC_AUTO`` 只有在禁用自动协商时才有意义。如果 ``ETHTOOL_A_FEC_AUTO`` 不为零，则驱动程序将根据 SFP 模块参数自动选择 FEC 模式。
这相当于 ioctl 接口中 `ETHTOOL_FEC_AUTO` 位。
``ETHTOOL_A_FEC_MODES`` 使用链路模式位（而非旧的 `ETHTOOL_FEC_*` 位）来表示当前的 FEC 配置。
``ETHTOOL_A_FEC_STATS`` 在 `ETHTOOL_A_HEADER_FLAGS` 中设置了 `ETHTOOL_FLAG_STATS` 标志时报告。

每个属性携带一个 64 位统计信息数组。数组中的第一个条目包含端口上的总事件数，而后续条目对应于车道 / PCS 实例的计数器。数组中条目的数量将是：

+--------------+---------------------------------------------+
| `0`          | 设备不支持 FEC 统计信息                     |
+--------------+---------------------------------------------+
| `1`          | 设备不支持按车道细分                        |
+--------------+---------------------------------------------+
| `1 + #lanes` | 设备完全支持 FEC 统计信息                   |
+--------------+---------------------------------------------+

驱动程序按照以下结构填充统计信息：

.. kernel-doc:: include/linux/ethtool.h
    :identifiers: ethtool_fec_stats

FEC_SET
=======

设置类似于 `ETHTOOL_SFECPARAM` ioctl 请求的 FEC 参数
请求内容：

  =====================================  ======  ==========================
  ``ETHTOOL_A_FEC_HEADER``               嵌套     请求头
  ``ETHTOOL_A_FEC_MODES``                位集     配置的模式
  ``ETHTOOL_A_FEC_AUTO``                 布尔值   FEC 模式自动选择
  =====================================  ======  ==========================

只有当禁用自动协商时，`FEC_SET` 才有意义。否则，FEC 模式作为自动协商的一部分被选择。
``ETHTOOL_A_FEC_MODES`` 用于选择要使用的 FEC 模式。建议只设置一个位，如果设置了多个位，驱动程序可能会以实现特定的方式从中进行选择。
``ETHTOOL_A_FEC_AUTO`` 请求驱动程序基于 SFP 模块参数选择 FEC 模式。但这并不意味着启用自动协商。
### MODULE_EEPROM_GET
=================

获取模块EEPROM数据转储
此接口设计允许每次最多转储半页数据。这意味着只允许转储128字节（或更少）的数据，且不能跨越位于偏移量128处的半页边界。对于非0页，只能访问高128字节。
请求内容：

  =======================================  ======  ==========================
  ``ETHTOOL_A_MODULE_EEPROM_HEADER``       nested  请求头
  ``ETHTOOL_A_MODULE_EEPROM_OFFSET``       u32     页内的偏移量
  ``ETHTOOL_A_MODULE_EEPROM_LENGTH``       u32     要读取的字节数
  ``ETHTOOL_A_MODULE_EEPROM_PAGE``         u8      页号
  ``ETHTOOL_A_MODULE_EEPROM_BANK``         u8      银行号
  ``ETHTOOL_A_MODULE_EEPROM_I2C_ADDRESS``  u8      页I2C地址
  =======================================  ======  ==========================

如果未指定``ETHTOOL_A_MODULE_EEPROM_BANK``，则假定为银行0
内核响应内容：

 +---------------------------------------------+--------+---------------------+
 | ``ETHTOOL_A_MODULE_EEPROM_HEADER``          | nested | 响应头              |
 +---------------------------------------------+--------+---------------------+
 | ``ETHTOOL_A_MODULE_EEPROM_DATA``            | binary | 来自模块EEPROM的字节数组 |
 +---------------------------------------------+--------+---------------------+

``ETHTOOL_A_MODULE_EEPROM_DATA``的属性长度等于驱动程序实际读取的字节数。

### STATS_GET
=========

获取接口的标准统计信息。请注意，这并不是``ETHTOOL_GSTATS``的重新实现，后者暴露了由驱动程序定义的统计信息。
请求内容：

  =======================================  ======  ==========================
  ``ETHTOOL_A_STATS_HEADER``               nested  请求头
  ``ETHTOOL_A_STATS_SRC``                  u32     统计信息来源
  ``ETHTOOL_A_STATS_GROUPS``               bitset  请求的统计信息组
  =======================================  ======  ==========================

内核响应内容：

 +-----------------------------------+--------+--------------------------------+
 | ``ETHTOOL_A_STATS_HEADER``        | nested | 响应头                         |
 +-----------------------------------+--------+--------------------------------+
 | ``ETHTOOL_A_STATS_SRC``           | u32    | 统计信息来源                   |
 +-----------------------------------+--------+--------------------------------+
 | ``ETHTOOL_A_STATS_GRP``           | nested | 一个或多个统计信息组           |
 +-+---------------------------------+--------+--------------------------------+
 | | ``ETHTOOL_A_STATS_GRP_ID``      | u32    | 组ID - ``ETHTOOL_STATS_*``     |
 +-+---------------------------------+--------+--------------------------------+
 | | ``ETHTOOL_A_STATS_GRP_SS_ID``   | u32    | 名称字符串集ID                 |
 +-+---------------------------------+--------+--------------------------------+
 | | ``ETHTOOL_A_STATS_GRP_STAT``    | nested | 包含统计信息的嵌套             |
 +-+---------------------------------+--------+--------------------------------+
 | | ``ETHTOOL_A_STATS_GRP_HIST_RX`` | nested | 直方图统计信息（接收方向）     |
 +-+---------------------------------+--------+--------------------------------+
 | | ``ETHTOOL_A_STATS_GRP_HIST_TX`` | nested | 直方图统计信息（发送方向）     |
 +-+---------------------------------+--------+--------------------------------+

用户通过``ETHTOOL_A_STATS_GROUPS``位集指定他们请求哪些统计信息组。当前定义的值包括：

 ====================== ======== ===============================================
 ETHTOOL_STATS_ETH_MAC  eth-mac  基本IEEE 802.3 MAC统计信息（30.3.1.1.*）
 ETHTOOL_STATS_ETH_PHY  eth-phy  基本IEEE 802.3 PHY统计信息（30.3.2.1.*）
 ETHTOOL_STATS_ETH_CTRL eth-ctrl 基本IEEE 802.3 MAC控制统计信息（30.3.3.*）
 ETHTOOL_STATS_RMON     rmon     RMON（RFC 2819）统计信息
 ====================== ======== ===============================================

每个组在响应中应该有一个对应的``ETHTOOL_A_STATS_GRP``
``ETHTOOL_A_STATS_GRP_ID``标识哪个组的统计信息嵌套包含
``ETHTOOL_A_STATS_GRP_SS_ID``标识该组统计信息名称的字符串集ID（如果可用）
统计信息添加到``ETHTOOL_A_STATS_GRP``嵌套下的``ETHTOOL_A_STATS_GRP_STAT``。``ETHTOOL_A_STATS_GRP_STAT``应包含单个8字节（u64）属性——该属性的类型是统计信息ID，其值是统计信息的值
每个组对统计信息ID有自己的解释。
属性ID对应由``ETHTOOL_A_STATS_GRP_SS_ID``标识的字符串集中的字符串。复杂的统计信息（如RMON直方图条目）也列在``ETHTOOL_A_STATS_GRP``内，并且在字符串集中没有定义字符串。
RMON "直方图"计数器计算给定大小范围内的数据包数量。由于RFC没有指定超出标准1518 MTU的范围，设备在桶定义上存在差异。因此，数据包范围的定义留给每个驱动程序。
``ETHTOOL_A_STATS_GRP_HIST_RX``和``ETHTOOL_A_STATS_GRP_HIST_TX``嵌套包含以下属性：

 ================================= ====== ===================================
 ETHTOOL_A_STATS_RMON_HIST_BKT_LOW u32    数据包大小桶的下界
 ETHTOOL_A_STATS_RMON_HIST_BKT_HI  u32    桶的上界
 ETHTOOL_A_STATS_RMON_HIST_VAL     u64    数据包计数器
 ================================= ====== ===================================

下界和上界都是包含在内的，例如：

 ============================= ==== ====
 RFC统计                     下界   上界
 ============================= ==== ====
 etherStatsPkts64Octets           0    64
 etherStatsPkts512to1023Octets 512  1023
 ============================= ==== ====

``ETHTOOL_A_STATS_SRC``是可选的。类似于``PAUSE_GET``，它取``enum ethtool_mac_stats_src``中的值。如果请求中不存在，则响应中将提供带有等于``ETHTOOL_MAC_STATS_SRC_AGGREGATE``的``ETHTOOL_A_STATS_SRC``属性的统计信息。

PHC_VCLOCKS_GET
===============

查询设备PHC虚拟时钟信息
请求内容：

  ====================================  ======  ==========================
  ``ETHTOOL_A_PHC_VCLOCKS_HEADER``      嵌套    请求头
  ====================================  ======  ==========================

内核响应内容：

  ====================================  ======  ==========================
  ``ETHTOOL_A_PHC_VCLOCKS_HEADER``      嵌套    响应头
  ``ETHTOOL_A_PHC_VCLOCKS_NUM``         u32     PHC虚拟时钟的数量
  ``ETHTOOL_A_PHC_VCLOCKS_INDEX``       s32     PHC索引数组
  ====================================  ======  ==========================

MODULE_GET
==========

获取收发器模块参数
请求内容：

  =====================================  ======  ==========================
  ``ETHTOOL_A_MODULE_HEADER``            嵌套    请求头
  =====================================  ======  ==========================

内核响应内容：

  ======================================  ======  ==========================
  ``ETHTOOL_A_MODULE_HEADER``             嵌套    响应头
  ``ETHTOOL_A_MODULE_POWER_MODE_POLICY``  u8      功率模式策略
  ``ETHTOOL_A_MODULE_POWER_MODE``         u8      运行功率模式
  ======================================  ======  ==========================

可选的``ETHTOOL_A_MODULE_POWER_MODE_POLICY``属性编码了主机强制执行的收发器模块功率模式策略。默认策略取决于驱动程序，但推荐的默认值为"自动"，并且应当被新的驱动程序或不需要与遗留行为保持一致的驱动程序实现。
可选的``ETHTOOL_A_MODULE_POWER_MODE``属性编码了收发器模块的操作功率模式。仅当插入模块时报告。可能的值为：

.. kernel-doc:: include/uapi/linux/ethtool.h
    :identifiers: ethtool_module_power_mode

MODULE_SET
==========

设置收发器模块参数
请求内容：

  ======================================  ======  ==========================
  ``ETHTOOL_A_MODULE_HEADER``             嵌套    请求头
  ``ETHTOOL_A_MODULE_POWER_MODE_POLICY``  u8      功率模式策略
  ======================================  ======  ==========================

设置时，可选的``ETHTOOL_A_MODULE_POWER_MODE_POLICY``属性用于设置主机强制执行的收发器模块功率策略。可能的值为：

.. kernel-doc:: include/uapi/linux/ethtool.h
    :identifiers: ethtool_module_power_mode_policy

对于SFF-8636模块，根据规范2.10a版表6-10，低功耗模式由主机强制执行；
对于CMIS模块，根据规范5.0版表6-12，低功耗模式由主机强制执行。
PSE_GET
=======

获取PSE属性
请求内容：

  =====================================  ======  ==========================
  ``ETHTOOL_A_PSE_HEADER``               nested  请求头
  =====================================  ======  ==========================

内核响应内容：

  ==========================================  ======  =============================
  ``ETHTOOL_A_PSE_HEADER``                    nested  响应头
  ``ETHTOOL_A_PODL_PSE_ADMIN_STATE``             u32  PoDL PSE功能的操作状态
  ``ETHTOOL_A_PODL_PSE_PW_D_STATUS``             u32  PoDL PSE的电源检测状态
  ``ETHTOOL_A_C33_PSE_ADMIN_STATE``              u32  PoE PSE功能的操作状态
  ``ETHTOOL_A_C33_PSE_PW_D_STATUS``              u32  PoE PSE的电源检测状态
  ``ETHTOOL_A_C33_PSE_PW_CLASS``                 u32  PoE PSE的电源等级
  ``ETHTOOL_A_C33_PSE_ACTUAL_PW``                u32  PoE PSE实际消耗的功率
  ``ETHTOOL_A_C33_PSE_EXT_STATE``                u32  PoE PSE的扩展电源状态
  ``ETHTOOL_A_C33_PSE_EXT_SUBSTATE``             u32  PoE PSE的扩展子状态
  ``ETHTOOL_A_C33_PSE_AVAIL_PW_LIMIT``           u32  PoE PSE当前配置的功率限制
  ``ETHTOOL_A_C33_PSE_PW_LIMIT_RANGES``       nested  支持的功率限制配置范围
  ==========================================  ======  =============================
当设置时，可选的 `ETHTOOL_A_PODL_PSE_ADMIN_STATE` 属性标识了 PoDL PSE 功能的操作状态。PSE 功能的操作状态可以通过使用 `ETHTOOL_A_PODL_PSE_ADMIN_CONTROL` 操作进行更改。此选项对应于 `IEEE 802.3-2018` 30.15.1.1.2 中的 aPoDLPSEAdminState。可能的值为：

.. kernel-doc:: include/uapi/linux/ethtool.h
    :identifiers: ethtool_podl_pse_admin_state

`ETHTOOL_A_C33_PSE_ADMIN_STATE` 同样如此，实现了 `IEEE 802.3-2022` 30.9.1.1.2 中的 aPSEAdminState。
.. kernel-doc:: include/uapi/linux/ethtool.h
    :identifiers: ethtool_c33_pse_admin_state

当设置时，可选的 `ETHTOOL_A_PODL_PSE_PW_D_STATUS` 属性标识了 PoDL PSE 的功率检测状态。该状态取决于内部 PSE 状态机和自动 PD 分类支持。此选项对应于 `IEEE 802.3-2018` 30.15.1.1.3 中的 aPoDLPSEPowerDetectionStatus。可能的值为：

.. kernel-doc:: include/uapi/linux/ethtool.h
    :identifiers: ethtool_podl_pse_pw_d_status

`ETHTOOL_A_C33_PSE_ADMIN_PW_D_STATUS` 同样如此，实现了 `IEEE 802.3-2022` 30.9.1.1.5 中的 aPSEPowerDetectionStatus。
.. kernel-doc:: include/uapi/linux/ethtool.h
    :identifiers: ethtool_c33_pse_pw_d_status

当设置时，可选的 `ETHTOOL_A_C33_PSE_PW_CLASS` 属性标识了 C33 PSE 的功率等级。它取决于 PSE 和 PD 之间协商的等级。此选项对应于 `IEEE 802.3-2022` 30.9.1.1.8 中的 aPSEPowerClassification。

当设置时，可选的 `ETHTOOL_A_C33_PSE_ACTUAL_PW` 属性标识实际功率。此选项对应于 `IEEE 802.3-2022` 30.9.1.1.23 中的 aPSEActualPower。实际功率以毫瓦 (mW) 报告。

当设置时，可选的 `ETHTOOL_A_C33_PSE_EXT_STATE` 属性标识了 C33 PSE 的扩展错误状态。可能的值为：

.. kernel-doc:: include/uapi/linux/ethtool.h
    :identifiers: ethtool_c33_pse_ext_state

当设置时，可选的 `ETHTOOL_A_C33_PSE_EXT_SUBSTATE` 属性标识了 C33 PSE 的扩展错误子状态。可能的值为：
可能的值为：

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

当设置时，可选的 `ETHTOOL_A_C33_PSE_AVAIL_PW_LIMIT` 属性标识了 C33 PSE 的功率限制（以毫瓦 (mW) 计）。

当设置时，可选的嵌套属性 `ETHTOOL_A_C33_PSE_PW_LIMIT_RANGES` 通过 `ETHTOOL_A_C33_PSE_PWR_VAL_LIMIT_RANGE_MIN` 和 `ETHTOOL_A_C33_PSE_PWR_VAL_LIMIT_RANGE_MAX` 标识了 C33 PSE 的功率限制范围。如果控制器采用固定等级工作，则最小值和最大值将相等。

PSE_SET
=======

设置 PSE 参数
请求内容:

  ======================================  ======  =============================
  ``ETHTOOL_A_PSE_HEADER``                嵌套    请求头
  ``ETHTOOL_A_PODL_PSE_ADMIN_CONTROL``       u32   控制 PoDL PSE 管理状态
  ``ETHTOOL_A_C33_PSE_ADMIN_CONTROL``        u32   控制 PSE 管理状态
  ``ETHTOOL_A_C33_PSE_AVAIL_PWR_LIMIT``      u32   控制 PoE PSE 可用功率限制
  ======================================  ======  =============================

当设置时，可选的 ``ETHTOOL_A_PODL_PSE_ADMIN_CONTROL`` 属性用于控制 PoDL PSE 管理功能。此选项实现了 ``IEEE 802.3-2018`` 的 30.15.1.2.1 acPoDLPSEAdminControl。参见 ``ETHTOOL_A_PODL_PSE_ADMIN_STATE`` 以获取支持的值。
对于 ``ETHTOOL_A_C33_PSE_ADMIN_CONTROL`` 同样适用，它实现了 ``IEEE 802.3-2022`` 的 30.9.1.2.1 acPSEAdminControl。
当设置时，可选的 ``ETHTOOL_A_C33_PSE_AVAIL_PWR_LIMIT`` 属性用于控制 C33 PSE 的可用功率值限制（单位：毫瓦）。
此属性对应于在 ``IEEE 802.3-2022`` 的 33.2.4.4 变量中描述的 `pse_available_power` 变量以及 145.2.5.4 变量中的 `pse_avail_pwr`，这些变量在功率类别中被描述。
决定使用毫瓦作为此接口的单位是为了统一其他功率监控接口，它们也使用毫瓦，并与许多记录功率消耗以瓦特而非类别的现有产品保持一致。如果需要基于类别的功率限制配置，转换可以在用户空间中完成，例如通过 ethtool。

RSS_GET
=======

获取与接口的 RSS 上下文相关的间接表、哈希键和哈希函数信息，类似于 ``ETHTOOL_GRSSH`` ioctl 请求。
请求内容:

=====================================  ======  ==========================
  ``ETHTOOL_A_RSS_HEADER``             嵌套    请求头
  ``ETHTOOL_A_RSS_CONTEXT``            u32     上下文编号
=====================================  ======  ==========================

内核响应内容:

=====================================  ======  ==========================
  ``ETHTOOL_A_RSS_HEADER``             嵌套    回复头
  ``ETHTOOL_A_RSS_HFUNC``              u32     RSS 哈希函数
  ``ETHTOOL_A_RSS_INDIR``              二进制  间接表字节
  ``ETHTOOL_A_RSS_HKEY``               二进制  哈希键字节
  ``ETHTOOL_A_RSS_INPUT_XFRM``         u32     RSS 输入数据转换
=====================================  ======  ==========================

``ETHTOOL_A_RSS_HFUNC`` 属性是一个位图，指示正在使用的哈希函数。当前支持的选项有 toeplitz、xor 和 crc32。
``ETHTOOL_A_RSS_INDIR`` 属性返回 RSS 间接表，其中每个字节表示队列编号。
``ETHTOOL_A_RSS_INPUT_XFRM`` 属性是一个位图，指示在将输入协议字段提供给 RSS 哈希函数之前所应用的转换类型。当前支持的选项是 symmetric-xor。

PLCA_GET_CFG
============

获取 IEEE 802.3cg-2019 第 148 条物理层碰撞避免 (PLCA) 调和子层 (RS) 属性。
请求内容：

  =====================================  ======  ==========================
  ``ETHTOOL_A_PLCA_HEADER``              嵌套    请求头部
  =====================================  ======  ==========================

内核响应内容：

  ======================================  ======  =============================
  ``ETHTOOL_A_PLCA_HEADER``               嵌套    响应头部
  ``ETHTOOL_A_PLCA_VERSION``              u16     支持的PLCA管理接口标准/版本
  ``ETHTOOL_A_PLCA_ENABLED``              u8      PLCA 管理状态
  ``ETHTOOL_A_PLCA_NODE_ID``              u32     PLCA 独特本地节点ID
  ``ETHTOOL_A_PLCA_NODE_CNT``             u32     网络上的PLCA节点数，包括协调器
  ``ETHTOOL_A_PLCA_TO_TMR``               u32     传输机会定时器值（比特时间）
  ``ETHTOOL_A_PLCA_BURST_CNT``            u32     节点在单个TO中被允许发送的额外数据包数量
  ``ETHTOOL_A_PLCA_BURST_TMR``            u32     在终止突发之前等待MAC发送新帧的时间（比特时间）
  ======================================  ======  =============================

当设置时，可选的 ``ETHTOOL_A_PLCA_VERSION`` 属性表示PLCA管理接口遵循的标准和版本。如果不设置，则接口为厂商特定，并且（可能）由驱动程序提供。
OPEN Alliance SIG为嵌入了PLCA调解子层的10BASE-T1S PHY指定了标准寄存器映射。参见 "10BASE-T1S PLCA管理寄存器"：https://www.opensig.org/about/specifications/
当设置时，可选的 ``ETHTOOL_A_PLCA_ENABLED`` 属性表示PLCA RS的管理状态。如果不设置，则节点以“普通”CSMA/CD模式运行。此选项对应于 ``IEEE 802.3cg-2019`` 30.16.1.1.1 aPLCAAdminState / 30.16.1.2.1 acPLCAAdminControl
当设置时，可选的 ``ETHTOOL_A_PLCA_NODE_ID`` 属性表示PHY配置的本地节点ID。该ID决定了哪个传输机会（TO）为节点预留用于传输。此选项对应于 ``IEEE 802.3cg-2019`` 30.16.1.1.4 aPLCALocalNodeID。此属性的有效范围为 [0 .. 255]，其中255意味着“未配置”
当设置时，可选的 ``ETHTOOL_A_PLCA_NODE_CNT`` 属性表示混合段上配置的最大PLCA节点数。这个数字决定了一个PLCA周期中生成的传输机会总数。此属性仅对PLCA协调器相关，即节点的aPLCALocalNodeID设置为0。跟随节点忽略此设置。
此选项对应于 ``IEEE 802.3cg-2019`` 30.16.1.1.3 aPLCANodeCount。此属性的有效范围为 [1 .. 255]
当设置时，可选的 ``ETHTOOL_A_PLCA_TO_TMR`` 属性表示传输机会定时器配置的值（比特时间）。为了使PLCA正确工作，此值必须在所有共享介质的节点上设置相等。此选项对应于 ``IEEE 802.3cg-2019`` 30.16.1.1.5 aPLCATransmitOpportunityTimer。此属性的有效范围为 [0 .. 255]
当设置时，可选的 ``ETHTOOL_A_PLCA_BURST_CNT`` 属性表示节点在单个传输机会期间被允许发送的额外数据包数量。默认情况下，此属性为0，这意味着节点每个TO只能发送一个帧。当大于0时，PLCA RS会在任何传输后保留TO，等待MAC发送新帧，最长等待aPLCABurstTimer比特时间。这每PLCA周期只能发生一定次数，直到达到此参数的值。之后，突发结束，正常的TO计数恢复。此选项对应于 ``IEEE 802.3cg-2019`` 30.16.1.1.6 aPLCAMaxBurstCount。此属性的有效范围为 [0 .. 255]
当设置时，可选的 ``ETHTOOL_A_PLCA_BURST_TMR`` 属性表示当aPLCAMaxBurstCount大于0时，PLCA RS等待MAC启动新传输的比特时间数。如果MAC未能在此时间内发送新帧，则突发结束，TO计数恢复；否则，新帧作为当前突发的一部分发送。此选项对应于 ``IEEE 802.3cg-2019`` 30.16.1.1.7 aPLCABurstTimer。此属性的有效范围为 [0 .. 255]。然而，为了使PLCA突发模式按预期工作，该值应该设置得大于MAC的帧间间隔(IFG)时间（加上一些余量）。
### PLCA_SET_CFG
设置 PLCA RS 参数  
请求内容：

  ======================================  ======  =============================
  ``ETHTOOL_A_PLCA_HEADER``               嵌套     请求头
  ``ETHTOOL_A_PLCA_ENABLED``              u8      PLCA 管理状态
  ``ETHTOOL_A_PLCA_NODE_ID``              u8      PLCA 唯一本地节点 ID
  ``ETHTOOL_A_PLCA_NODE_CNT``             u8      网络上 PLCA 节点的数量，包括协调器
  ``ETHTOOL_A_PLCA_TO_TMR``               u8      发送机会定时器值（以比特时间 BT 计）
  ``ETHTOOL_A_PLCA_BURST_CNT``            u8      节点在单个发送机会内允许发送的额外数据包数量
  ``ETHTOOL_A_PLCA_BURST_TMR``            u8      在终止突发之前等待 MAC 发送新帧的时间
  ======================================  ======  =============================

有关每个属性的描述，请参阅 `PLCA_GET_CFG`

### PLCA_GET_STATUS
获取 PLCA RS 状态信息  
请求内容：

  =====================================  ======  ==========================
  ``ETHTOOL_A_PLCA_HEADER``              嵌套     请求头
  =====================================  ======  ==========================

内核响应内容：

  ======================================  ======  =============================
  ``ETHTOOL_A_PLCA_HEADER``               嵌套     响应头
  ``ETHTOOL_A_PLCA_STATUS``               u8      PLCA RS 运行状态
  ======================================  ======  =============================

当设置时，`ETHTOOL_A_PLCA_STATUS` 属性表示节点是否检测到网络上的 BEACON。此标志对应于 `IEEE 802.3cg-2019` 30.16.1.1.2 中的 aPLCAStatus。

### MM_GET
检索 802.3 MAC Merge 参数  
请求内容：

  ====================================  ======  ==========================
  ``ETHTOOL_A_MM_HEADER``               嵌套     请求头
  ====================================  ======  ==========================

内核响应内容：

  =================================  ======  ===================================
  ``ETHTOOL_A_MM_HEADER``            嵌套     请求头
  ``ETHTOOL_A_MM_PMAC_ENABLED``      布尔型   如果启用了可抢占和 SMD-V 帧的接收，则设置
  ``ETHTOOL_A_MM_TX_ENABLED``        布尔型   如果启用了可抢占帧的发送，则设置（如果验证失败可能会处于非活动状态）
  ``ETHTOOL_A_MM_TX_ACTIVE``         布尔型   如果可抢占帧的发送处于运行状态，则设置
  ``ETHTOOL_A_MM_TX_MIN_FRAG_SIZE``  u32     发送的非最终片段的最小大小（以字节为单位）
  ``ETHTOOL_A_MM_RX_MIN_FRAG_SIZE``  u32     接收的非最终片段的最小大小（以字节为单位）
  ``ETHTOOL_A_MM_VERIFY_ENABLED``    布尔型   如果启用了 SMD-V 帧的发送，则设置
  ``ETHTOOL_A_MM_VERIFY_STATUS``     u8      验证功能的状态
  ``ETHTOOL_A_MM_VERIFY_TIME``       u32     验证尝试之间的延迟
  ``ETHTOOL_A_MM_MAX_VERIFY_TIME``   u32     设备支持的最大验证间隔
  ``ETHTOOL_A_MM_STATS``             嵌套     IEEE 802.3-2018 子条款 30.14.1 中的 oMACMergeEntity 统计计数器
  =================================  ======  ===================================

设备驱动程序通过以下结构填充这些属性：

.. kernel-doc:: include/linux/ethtool.h
    :identifiers: ethtool_mm_state

`ETHTOOL_A_MM_VERIFY_STATUS` 将报告以下值之一：

.. kernel-doc:: include/uapi/linux/ethtool.h
    :identifiers: ethtool_mm_verify_status

如果在 `MM_SET` 命令中将 `ETHTOOL_A_MM_VERIFY_ENABLED` 传递为 false，则 `ETHTOOL_A_MM_VERIFY_STATUS` 将报告 `ETHTOOL_MM_VERIFY_STATUS_INITIAL` 或 `ETHTOOL_MM_VERIFY_STATUS_DISABLED`，否则它应该报告其他状态之一。

建议驱动程序从禁用 pMAC 开始，并根据用户空间请求启用它。还建议用户空间不要依赖于来自 `ETHTOOL_MSG_MM_GET` 请求的默认值。
如果在 `ETHTOOL_A_HEADER_FLAGS` 中设置了 `ETHTOOL_FLAG_STATS`，则会报告 `ETHTOOL_A_MM_STATS`。如果驱动程序没有报告任何统计数据，则该属性为空。驱动程序在以下结构中填写统计信息：

.. kernel-doc:: include/linux/ethtool.h
    :identifiers: ethtool_mm_stats

### MM_SET
修改 802.3 MAC Merge 层的配置  
请求内容：

  =================================  ======  ==========================
  ``ETHTOOL_A_MM_VERIFY_TIME``       u32     参见 MM_GET 描述
  ``ETHTOOL_A_MM_VERIFY_ENABLED``    布尔型   参见 MM_GET 描述
  ``ETHTOOL_A_MM_TX_ENABLED``        布尔型   参见 MM_GET 描述
  ``ETHTOOL_A_MM_PMAC_ENABLED``      布尔型   参见 MM_GET 描述
  ``ETHTOOL_A_MM_TX_MIN_FRAG_SIZE``  u32     参见 MM_GET 描述
  =================================  ======  ==========================

这些属性通过以下结构传播给驱动程序：

.. kernel-doc:: include/linux/ethtool.h
    :identifiers: ethtool_mm_cfg

### MODULE_FW_FLASH_ACT
刷新收发器模块固件  
请求内容：

  =======================================  ======  ===========================
  ``ETHTOOL_A_MODULE_FW_FLASH_HEADER``     嵌套     请求头
  ``ETHTOOL_A_MODULE_FW_FLASH_FILE_NAME``  字符串   固件映像文件名
  ``ETHTOOL_A_MODULE_FW_FLASH_PASSWORD``   u32     收发器模块密码
  =======================================  ======  ===========================

固件更新过程由三个逻辑步骤组成：

1. 向收发器模块下载固件映像并验证它
### 2. 运行固件映像
### 3. 提交固件映像以便在重置时运行
当发出`flash`命令时，这三个步骤按顺序执行。
此消息仅安排更新过程并立即返回，不会阻塞。该过程随后异步运行。
由于可能需要几分钟才能完成，在更新过程中内核会向用户空间发送通知，以更新关于状态和进度的信息。
属性`ETHTOOL_A_MODULE_FW_FLASH_FILE_NAME`编码固件映像文件名。固件映像被下载到收发器模块中，经过验证、运行和提交。
可选的属性`ETHTOOL_A_MODULE_FW_FLASH_PASSWORD`编码密码，该密码可能是收发器模块固件更新过程中所必需的。
固件更新过程可能需要几分钟来完成。因此，在更新过程中内核会向用户空间发送通知，以更新关于状态和进度的信息。

#### 通知内容：

+---------------------------------------------------+--------+----------------+
| `ETHTOOL_A_MODULE_FW_FLASH_HEADER`                | 嵌套   | 回复头         |
+---------------------------------------------------+--------+----------------+
| `ETHTOOL_A_MODULE_FW_FLASH_STATUS`                | u32    | 状态           |
+---------------------------------------------------+--------+----------------+
| `ETHTOOL_A_MODULE_FW_FLASH_STATUS_MSG`            | 字符串 | 状态消息       |
+---------------------------------------------------+--------+----------------+
| `ETHTOOL_A_MODULE_FW_FLASH_DONE`                  | uint   | 完成量         |
+---------------------------------------------------+--------+----------------+
| `ETHTOOL_A_MODULE_FW_FLASH_TOTAL`                 | uint   | 总量           |
+---------------------------------------------------+--------+----------------+

属性`ETHTOOL_A_MODULE_FW_FLASH_STATUS`编码固件更新过程的当前状态。可能的值为：

.. kernel-doc:: include/uapi/linux/ethtool.h
    :identifiers: ethtool_module_fw_flash_status

属性`ETHTOOL_A_MODULE_FW_FLASH_STATUS_MSG`编码一个状态消息字符串。
属性`ETHTOOL_A_MODULE_FW_FLASH_DONE` 和 `ETHTOOL_A_MODULE_FW_FLASH_TOTAL` 分别编码已完成的工作量和总工作量。
下表将ioctl命令映射到提供相同功能的netlink命令。右列中标注为"n/a"的条目表示尚未有对应的netlink替代命令。左列中标注为"n/a"的条目仅适用于netlink。
=================================== =====================================
  ioctl命令                           netlink命令
  =================================== =====================================
  ``ETHTOOL_GSET``                    ``ETHTOOL_MSG_LINKINFO_GET``
                                      ``ETHTOOL_MSG_LINKMODES_GET``
  ``ETHTOOL_SSET``                    ``ETHTOOL_MSG_LINKINFO_SET``
                                      ``ETHTOOL_MSG_LINKMODES_SET``
  ``ETHTOOL_GDRVINFO``                n/a
  ``ETHTOOL_GREGS``                   n/a
  ``ETHTOOL_GWOL``                    ``ETHTOOL_MSG_WOL_GET``
  ``ETHTOOL_SWOL``                    ``ETHTOOL_MSG_WOL_SET``
  ``ETHTOOL_GMSGLVL``                 ``ETHTOOL_MSG_DEBUG_GET``
  ``ETHTOOL_SMSGLVL``                 ``ETHTOOL_MSG_DEBUG_SET``
  ``ETHTOOL_NWAY_RST``                n/a
  ``ETHTOOL_GLINK``                   ``ETHTOOL_MSG_LINKSTATE_GET``
  ``ETHTOOL_GEEPROM``                 n/a
  ``ETHTOOL_SEEPROM``                 n/a
  ``ETHTOOL_GCOALESCE``               ``ETHTOOL_MSG_COALESCE_GET``
  ``ETHTOOL_SCOALESCE``               ``ETHTOOL_MSG_COALESCE_SET``
  ``ETHTOOL_GRINGPARAM``              ``ETHTOOL_MSG_RINGS_GET``
  ``ETHTOOL_SRINGPARAM``              ``ETHTOOL_MSG_RINGS_SET``
  ``ETHTOOL_GPAUSEPARAM``             ``ETHTOOL_MSG_PAUSE_GET``
  ``ETHTOOL_SPAUSEPARAM``             ``ETHTOOL_MSG_PAUSE_SET``
  ``ETHTOOL_GRXCSUM``                 ``ETHTOOL_MSG_FEATURES_GET``
  ``ETHTOOL_SRXCSUM``                 ``ETHTOOL_MSG_FEATURES_SET``
  ``ETHTOOL_GTXCSUM``                 ``ETHTOOL_MSG_FEATURES_GET``
  ``ETHTOOL_STXCSUM``                 ``ETHTOOL_MSG_FEATURES_SET``
  ``ETHTOOL_GSG``                     ``ETHTOOL_MSG_FEATURES_GET``
  ``ETHTOOL_SSG``                     ``ETHTOOL_MSG_FEATURES_SET``
  ``ETHTOOL_TEST``                    n/a
  ``ETHTOOL_GSTRINGS``                ``ETHTOOL_MSG_STRSET_GET``
  ``ETHTOOL_PHYS_ID``                 n/a
  ``ETHTOOL_GSTATS``                  n/a
  ``ETHTOOL_GTSO``                    ``ETHTOOL_MSG_FEATURES_GET``
  ``ETHTOOL_STSO``                    ``ETHTOOL_MSG_FEATURES_SET``
  ``ETHTOOL_GPERMADDR``               rtnetlink ``RTM_GETLINK``
  ``ETHTOOL_GUFO``                    ``ETHTOOL_MSG_FEATURES_GET``
  ``ETHTOOL_SUFO``                    ``ETHTOOL_MSG_FEATURES_SET``
  ``ETHTOOL_GGSO``                    ``ETHTOOL_MSG_FEATURES_GET``
  ``ETHTOOL_SGSO``                    ``ETHTOOL_MSG_FEATURES_SET``
  ``ETHTOOL_GFLAGS``                  ``ETHTOOL_MSG_FEATURES_GET``
  ``ETHTOOL_SFLAGS``                  ``ETHTOOL_MSG_FEATURES_SET``
  ``ETHTOOL_GPFLAGS``                 ``ETHTOOL_MSG_PRIVFLAGS_GET``
  ``ETHTOOL_SPFLAGS``                 ``ETHTOOL_MSG_PRIVFLAGS_SET``
  ``ETHTOOL_GRXFH``                   n/a
  ``ETHTOOL_SRXFH``                   n/a
  ``ETHTOOL_GGRO``                    ``ETHTOOL_MSG_FEATURES_GET``
  ``ETHTOOL_SGRO``                    ``ETHTOOL_MSG_FEATURES_SET``
  ``ETHTOOL_GRXRINGS``                n/a
  ``ETHTOOL_GRXCLSRLCNT``             n/a
  ``ETHTOOL_GRXCLSRULE``              n/a
  ``ETHTOOL_GRXCLSRLALL``             n/a
  ``ETHTOOL_SRXCLSRLDEL``             n/a
  ``ETHTOOL_SRXCLSRLINS``             n/a
  ``ETHTOOL_FLASHDEV``                n/a
  ``ETHTOOL_RESET``                   n/a
  ``ETHTOOL_SRXNTUPLE``               n/a
  ``ETHTOOL_GRXNTUPLE``               n/a
  ``ETHTOOL_GSSET_INFO``              ``ETHTOOL_MSG_STRSET_GET``
  ``ETHTOOL_GRXFHINDIR``              n/a
  ``ETHTOOL_SRXFHINDIR``              n/a
  ``ETHTOOL_GFEATURES``               ``ETHTOOL_MSG_FEATURES_GET``
  ``ETHTOOL_SFEATURES``               ``ETHTOOL_MSG_FEATURES_SET``
  ``ETHTOOL_GCHANNELS``               ``ETHTOOL_MSG_CHANNELS_GET``
  ``ETHTOOL_SCHANNELS``               ``ETHTOOL_MSG_CHANNELS_SET``
  ``ETHTOOL_SET_DUMP``                n/a
  ``ETHTOOL_GET_DUMP_FLAG``           n/a
  ``ETHTOOL_GET_DUMP_DATA``           n/a
  ``ETHTOOL_GET_TS_INFO``             ``ETHTOOL_MSG_TSINFO_GET``
  ``ETHTOOL_GMODULEINFO``             ``ETHTOOL_MSG_MODULE_EEPROM_GET``
  ``ETHTOOL_GMODULEEEPROM``           ``ETHTOOL_MSG_MODULE_EEPROM_GET``
  ``ETHTOOL_GEEE``                    ``ETHTOOL_MSG_EEE_GET``
  ``ETHTOOL_SEEE``                    ``ETHTOOL_MSG_EEE_SET``
  ``ETHTOOL_GRSSH``                   ``ETHTOOL_MSG_RSS_GET``
  ``ETHTOOL_SRSSH``                   n/a
  ``ETHTOOL_GTUNABLE``                n/a
  ``ETHTOOL_STUNABLE``                n/a
  ``ETHTOOL_GPHYSTATS``               n/a
  ``ETHTOOL_PERQUEUE``                n/a
  ``ETHTOOL_GLINKSETTINGS``           ``ETHTOOL_MSG_LINKINFO_GET``
                                      ``ETHTOOL_MSG_LINKMODES_GET``
  ``ETHTOOL_SLINKSETTINGS``           ``ETHTOOL_MSG_LINKINFO_SET``
                                      ``ETHTOOL_MSG_LINKMODES_SET``
  ``ETHTOOL_PHY_GTUNABLE``            n/a
  ``ETHTOOL_PHY_STUNABLE``            n/a
  ``ETHTOOL_GFECPARAM``               ``ETHTOOL_MSG_FEC_GET``
  ``ETHTOOL_SFECPARAM``               ``ETHTOOL_MSG_FEC_SET``
  n/a                                 ``ETHTOOL_MSG_CABLE_TEST_ACT``
  n/a                                 ``ETHTOOL_MSG_CABLE_TEST_TDR_ACT``
  n/a                                 ``ETHTOOL_MSG_TUNNEL_INFO_GET``
  n/a                                 ``ETHTOOL_MSG_PHC_VCLOCKS_GET``
  n/a                                 ``ETHTOOL_MSG_MODULE_GET``
  n/a                                 ``ETHTOOL_MSG_MODULE_SET``
  n/a                                 ``ETHTOOL_MSG_PLCA_GET_CFG``
  n/a                                 ``ETHTOOL_MSG_PLCA_SET_CFG``
  n/a                                 ``ETHTOOL_MSG_PLCA_GET_STATUS``
  n/a                                 ``ETHTOOL_MSG_MM_GET``
  n/a                                 ``ETHTOOL_MSG_MM_SET``
  n/a                                 ``ETHTOOL_MSG_MODULE_FW_FLASH_ACT``
  =================================== =====================================
