SPDX 许可声明标识符: GPL-2.0

===========================
如何使用 radiotap 头部
===========================

指向 radiotap 包含文件的指针
------------------------------------

Radiotap 头部是可变长度且可扩展的，您可以从以下文件获取有关它们的大部分信息：

    ./include/net/ieee80211_radiotap.h

本文档提供了概述，并对一些特殊情况进行了警告。

头部结构
-----------------------

头部的开始部分有一个固定部分，其中包含一个 u32 位图，该位图定义了与该位相关的可能参数是否存在。因此，如果 ieee80211_radiotap_header 的 it_present 成员的 b0 被设置，则表示索引为 0（IEEE80211_RADIOTAP_TSFT）的参数头在参数区域中存在：

   < 8 字节 ieee80211_radiotap_header >
   [ <可能的参数位图扩展...> ]
   [ <参数> ... ]

目前仅定义了 13 个可能的参数索引，但如果我们在 u32 it_present 成员中用尽了空间，则定义了 b31 设置表示后面还有一个 u32 位图（如上所示为“可能的参数位图扩展...”），并且参数的起始位置每次向前移动 4 字节。
还请注意，__le16 类型的 it_len 成员设置为由 ieee80211_radiotap_header 及其后跟的任何参数覆盖的总字节数。

参数要求
--------------------------

在头部的固定部分之后，对于每个 it_present 成员中相应位被设置的参数索引，都会跟随相应的参数
- 所有参数都以小端格式存储！

 - 给定参数索引的参数有效负载具有固定大小。例如，IEEE80211_RADIOTAP_TSFT 的存在始终表示存在一个 8 字节的参数。查看 ./include/net/ieee80211_radiotap.h 中的注释以获得所有参数大小的详细分解。

 - 必须使用填充将参数对齐到参数大小的边界。因此，如果 u16 参数未处于 u16 边界上，则必须从下一个 u16 边界开始，u32 必须从下一个 u32 边界开始，以此类推。
- “对齐”相对于 ieee80211_radiotap_header 的开始处，即 radiotap 头部的第一个字节。该第一个字节的绝对对齐方式没有定义。因此即使整个 radiotap 头部从地址 0x00000003 开始，仍然将 radiotap 头部的第一个字节视为 0 进行对齐处理。
- 上述关于在固定的 radiotap 头部或参数区域中可能存在多字节实体没有绝对对齐方式的观点意味着您在尝试访问这些多字节实体时需要采取特别的规避措施。一些架构（如 Blackfin）无法处理尝试反引用指向奇数地址的 u16 指针的操作。相反，您必须使用内核 API get_unaligned() 来反引用指针，这将在需要的架构上按字节进行操作。
- 给定参数索引的参数可以由多种类型的组合组成。例如，IEEE80211_RADIOTAP_CHANNEL 的参数有效负载由两个 u16 组成，总长度为 4。在这种情况下，应用的是针对 u16 的填充规则，而不是针对 4 字节单个实体的规则。

示例有效的 radiotap 头部
-----------------------------

```
    0x00, 0x00, // <-- radiotap 版本 + 填充字节
    0x0b, 0x00, // <- radiotap 头部长度
    0x04, 0x0c, 0x00, 0x00, // <-- 位图
    0x6c, // <-- 速率（单位为 500kHz）
    0x0c, // <-- 发射功率
    0x01 // <-- 天线
```

使用 Radiotap 解析器
-------------------------

如果您需要解析 radiotap 结构，可以通过使用位于 net/wireless/radiotap.c 中并在 include/net/cfg80211.h 中提供原型的 radiotap 解析器来极大地简化任务。使用方法如下：

```c
#include <net/cfg80211.h>

/* buf 指向 radiotap 头部部分的开始 */

int MyFunction(u8 * buf, int buflen)
{
	int pkt_rate_100kHz = 0, antenna = 0, pwr = 0;
	struct ieee80211_radiotap_iterator iterator;
	int ret = ieee80211_radiotap_iterator_init(&iterator, buf, buflen);

	while (!ret) {

		ret = ieee80211_radiotap_iterator_next(&iterator);

		if (ret)
			continue;

		/* 看看这个参数是否是我们可以使用的 */

		switch (iterator.this_arg_index) {
		/*
		* 在反引用 iterator.this_arg 用于多字节类型时必须小心……指针未对齐。使用
		* get_unaligned((type *)iterator.this_arg) 安全地反引用 iterator.this_arg 用于所有架构上的“类型”类型
		*/
```
```c
switch (header_type) {
    case IEEE80211_RADIOTAP_RATE:
        /* radiotap "rate" u8 以 500kbps 为单位，例如，0x02 表示 1Mbps */
        pkt_rate_100kHz = (*iterator.this_arg) * 5;
        break;

    case IEEE80211_RADIOTAP_ANTENNA:
        /* radiotap 中 0 表示第一个天线 */
        antenna = *iterator.this_arg;
        break;

    case IEEE80211_RADIOTAP_DBM_TX_POWER:
        pwr = *iterator.this_arg;
        break;

    default:
        break;
}
/* 当有更多无线电头信息时继续处理 */
}  // while 更多无线电头信息

if (ret != -ENOENT)
    return TXRX_DROP;

/* 丢弃 radiotap 头部部分 */
buf += iterator.max_length;
buflen -= iterator.max_length;

..
}

// Andy Green <andy@warmcat.com>
```

这是将您提供的代码段翻译成中文后的版本。如果您有任何进一步的问题或需要更多的帮助，请告诉我！
