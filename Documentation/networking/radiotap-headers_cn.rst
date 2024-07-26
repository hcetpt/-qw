SPDX 许可证标识符: GPL-2.0

===========================
如何使用 radiotap 头部
===========================

指向 radiotap 包含文件的指针
------------------------------------

Radiotap 头部是可变长度且可扩展的，你可以从以下获取到你需要了解的大部分信息：
::
    ./include/net/ieee80211_radiotap.h

本文档提供了概述，并对一些特殊情况进行了警告。
头部结构
-----------------------

头部起始有一个固定部分，其中包含一个 u32 位图，该位图定义了与该位相关的可能参数是否存在。因此，如果 ieee80211_radiotap_header 的 it_present 成员中的 b0 被设置，则意味着索引为 0（IEEE80211_RADIOTAP_TSFT）的头部在参数区域中存在
::
   < 8 字节 ieee80211_radiotap_header >
   [ <可能的参数位图扩展 ... > ]
   [ <参数> ... ]

目前仅定义了 13 个可能的参数索引，但如果我们在 u32 it_present 成员中用尽了空间，那么被设置的 b31 表示后面还有一个 u32 位图（如上所示为“可能的参数位图扩展”），并且每次参数的开始位置会向前移动 4 字节。
需要注意的是，__le16 类型的 it_len 成员设置为由 ieee80211_radiotap_header 和其后跟随的任何参数覆盖的总字节数。
参数要求
--------------------------

在头部的固定部分之后，对于 ieee80211_radiotap_header 中 it_present 成员中对应的位被设置的每个参数索引，都会跟随着相应的参数
- 所有参数都是小端存储！

 - 给定参数索引的参数负载具有固定的大小。因此，IEEE80211_RADIOTAP_TSFT 的存在总是表示存在一个 8 字节的参数。查看 ./include/net/ieee80211_radiotap.h 中的所有参数大小的详细说明。

 - 参数必须通过填充对齐到参数大小的边界。因此，如果 u16 参数没有已经位于 u16 边界上，则必须从下一个 u16 边界开始；u32 参数必须从下一个 u32 边界开始，依此类推。
- “对齐”相对于 ieee80211_radiotap_header 的起始位置，即，radiotap 头部的第一个字节。第一个字节的绝对对齐方式并未定义。因此即使整个 radiotap 头部的起始地址例如在 0x00000003 上，仍然将 radiotap 头部的第一个字节视为对齐目的的 0。
- 上述关于在固定的 radiotap 头部或参数区域中多字节实体可能没有绝对对齐的点意味着当你尝试访问这些多字节实体时，你必须采取特殊的规避措施。某些架构（如 Blackfin）无法处理尝试解引用指向奇数地址的 u16 指针的尝试。相反，你必须使用内核 API get_unaligned() 来解引用指针，它将在需要的架构上按字节进行操作。
- 对于给定参数索引的参数可以是由多种类型组成的复合体。例如，IEEE80211_RADIOTAP_CHANNEL 的参数负载由两个 u16 组成，总长度为 4。当这种情况发生时，填充规则是针对 u16 进行的，而不是针对 4 字节的单一实体。
有效 radiotap 头部示例
-----------------------------

::
	0x00, 0x00, // <-- radiotap 版本 + 填充字节
	0x0b, 0x00, // <- radiotap 头部长度
	0x04, 0x0c, 0x00, 0x00, // <-- 位图
	0x6c, // <-- 速率（以 500kHz 单位）
	0x0c, // <-- 发射功率
	0x01 // <-- 天线

使用 Radiotap 解析器
-------------------------

如果你需要解析 radiotap 结构，可以通过使用位于 net/wireless/radiotap.c 中的 radiotap 解析器来极大地简化这项工作，它的原型在 include/net/cfg80211.h 中可用。使用方法如下：
::
    #include <net/cfg80211.h>

    /* buf 指向 radiotap 头部部分的起始位置 */

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
		    * 在解引用 iterator.this_arg 用于多字节类型时，你必须小心... 指针未对齐。使用
		    * get_unaligned((type *)iterator.this_arg) 安全地解引用 iterator.this_arg 用于类型 "type"，适用于所有架构
		    */
下面是给定代码段的中文翻译：

```c
    switch (header_type) {
        case IEEE80211_RADIOTAP_RATE:
            /* 
             * radiotap "rate" 的 u8 类型是以 500kbps 为单位的，例如，0x02 表示 1Mbps
             */
            pkt_rate_100kHz = (*iterator.this_arg) * 5;
            break;

        case IEEE80211_RADIOTAP_ANTENNA:
            /* 
             * radiotap 中使用 0 表示第一个天线
             */
            antenna = *iterator.this_arg;
            break;

        case IEEE80211_RADIOTAP_DBM_TX_POWER:
            pwr = *iterator.this_arg;
            break;

        default:
            break;
    }
}  /* while 处理更多的 radiotap 头部信息 */

/* 如果 ret 不等于 -ENOENT，则返回 TXRX_DROP */
if (ret != -ENOENT)
    return TXRX_DROP;

/* 丢弃 radiotap 头部部分 */
buf += iterator.max_length;
buflen -= iterator.max_length;

..

} /* Andy Green <andy@warmcat.com> */
```

请注意，我已将代码片段进行了适当的格式化以提高可读性，并且注释已经翻译成了中文。此外，保留了原始代码中的变量名和结构，以便于理解上下文。
