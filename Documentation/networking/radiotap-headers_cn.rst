SPDX 许可证标识符：GPL-2.0

===========================
如何使用 radiotap 头部
===========================

指向 radiotap 包含文件的指针
------------------------------------

Radiotap 头部是可变长度且可扩展的，你可以从以下获取你需要了解的大部分信息：

    ./include/net/ieee80211_radiotap.h

本文档提供了一个概览，并警告了一些特殊情况。
头部结构
-----------------------

在开始处有一个固定部分，其中包含一个 u32 位图，该位图定义了与该位关联的可能参数是否存在。因此，如果 ieee80211_radiotap_header 的 it_present 成员的 b0 被设置，则意味着索引 0（IEEE80211_RADIOTAP_TSFT）的头部存在于参数区域中：

   < 8 字节 ieee80211_radiotap_header >
   [ <可能的参数位图扩展...> ]
   [ <参数> ... ]

目前只定义了 13 个可能的参数索引，但如果我们在 u32 it_present 成员中空间不足，定义为 b31 设置表示后面跟着另一个 u32 位图（如上所示为“可能的参数位图扩展...”），并且每次参数的起始位置向前移动 4 字节。
注意，__le16 类型的 it_len 成员被设置为由 ieee80211_radiotap_header 和其后任何参数覆盖的总字节数。
参数要求
--------------------------

在头部的固定部分之后，对于 ieee80211_radiotap_header 的 it_present 成员中匹配位设置的每个参数索引，将跟随参数
- 所有参数都以小端存储！

- 给定参数索引的参数负载具有固定大小。因此，IEEE80211_RADIOTAP_TSFT 的存在始终表示存在一个 8 字节的参数。参见 ./include/net/ieee80211_radiotap.h 中对所有参数大小的详细分解。

- 必须使用填充使参数对齐到参数大小的边界。因此，如果它不在 u16 边界上，则 u16 参数必须从下一个 u16 边界开始，u32 必须从下一个 u32 边界开始，依此类推。
- “对齐”相对于 ieee80211_radiotap_header 的开始，即，radiotap 头部的第一个字节。那个第一个字节的绝对对齐方式未定义。因此，即使整个 radiotap 头部从例如地址 0x00000003 开始，仍然将 radiotap 头部的第一个字节视为对齐目的的 0。
- 上面关于在固定的 radiotap 头部或参数区域中多字节实体可能没有绝对对齐的点意味着在尝试访问这些多字节实体时，你必须采取特别的规避行动。一些架构（如 Blackfin）无法处理尝试解除引用指向奇数地址的 u16 指针的尝试。相反，你必须使用内核 API get_unaligned() 来解除引用指针，这将在需要的架构上逐字节地完成。
- 对于给定参数索引的参数可以是多种类型的复合体。例如，IEEE80211_RADIOTAP_CHANNEL 具有一个由两个 u16 组成的参数负载，总长度为 4。当这种情况发生时，填充规则适用于 u16，而不是处理一个 4 字节的单一实体。

示例有效的 radiotap 头部
-----------------------------

```
	0x00, 0x00, // <-- radiotap 版本 + 填充字节
	0x0b, 0x00, // <- radiotap 头部长度
	0x04, 0x0c, 0x00, 0x00, // <-- 位图
	0x6c, // <-- 速率（以 500kHz 单位）
	0x0c, //<-- 发射功率
	0x01 //<-- 天线
```

使用 Radiotap 解析器
-------------------------

如果你必须解析 radiotap 结构，你可以通过使用位于 net/wireless/radiotap.c 中的 radiotap 解析器来极大地简化工作，其原型可在 include/net/cfg80211.h 中获得。你像这样使用它：

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

		    /* 看看这个参数是否是我们可以使用的东西 */

		    switch (iterator.this_arg_index) {
		    /*
		    * 当解除引用 iterator.this_arg 用于多字节类型时，你必须小心... 指针不对齐。使用
		    * get_unaligned((type *)iterator.this_arg) 来安全地解除引用 iterator.this_arg 以获取“type”类型的所有架构
```
以下是给定代码段的中文翻译：

```plaintext
    根据 IEEE80211_RADIOTAP_RATE 的情况：
        /* radiotap 中的 "rate" u8 是以 500kbps 为单位的，例如，0x02=1Mbps */
        pkt_rate_100kHz = (*iterator.this_arg) * 5;
        break;

    根据 IEEE80211_RADIOTAP_ANTENNA 的情况：
        /* radiotap 使用 0 表示第一个天线 */
        antenna = *iterator.this_arg;
        break;

    根据 IEEE80211_RADIOTAP_DBM_TX_POWER 的情况：
        pwr = *iterator.this_arg;
        break;

    默认情况：
        break;
}   /* 当有更多 rt 头部时 */

如果 (ret != -ENOENT)
    返回 TXRX_DROP;

/* 抛弃 radiotap 头部部分 */
buf += iterator.max_length;
buflen -= iterator.max_length;

..
}

Andy Green <andy@warmcat.com>
```

请注意，我将代码注释和实际代码都翻译成了中文。但是，原始代码中的变量名和类型没有翻译，因为它们是编程中特定的术语，并且在所有语言中通常保持一致。此外，`TXRX_DROP` 和 `-ENOENT` 这样的预定义常量也没有被翻译，因为它们也是特定于编程环境的标识符。
