SPDX 许可声明标识符: GPL-2.0

=========================================
如何使用 mac80211 进行数据包注入
=========================================

现在，mac80211 允许从用户空间向任何处于监控模式的接口注入任意数据包。您注入的数据包需要按照以下格式构建：

[ 无线电 tap 头 ]
[ IEEE80211 头 ]
[ 载荷 ]

无线电 tap 格式在 ./Documentation/networking/radiotap-headers.rst 中进行了讨论。尽管当前定义了许多无线电 tap 参数，但大多数只适用于接收的数据包。从无线电 tap 头中解析出以下信息用于控制注入：

* IEEE80211_RADIOTAP_FLAGS

   =========================  ===========================================
   IEEE80211_RADIOTAP_F_FCS   FCS 将被移除并重新计算
   IEEE80211_RADIOTAP_F_WEP   如果有密钥，则帧将被加密
   IEEE80211_RADIOTAP_F_FRAG  如果帧长度超过当前的分片阈值，则将被分片
   =========================  ===========================================

* IEEE80211_RADIOTAP_TX_FLAGS

   =============================  ========================================
   IEEE80211_RADIOTAP_F_TX_NOACK  即使是单播帧，发送时也不应等待 ACK
   =============================  ========================================

* IEEE80211_RADIOTAP_RATE

   发送的遗留速率（仅对没有自己速率控制的设备）

* IEEE80211_RADIOTAP_MCS

   发送的 HT 速率（仅对没有自己速率控制的设备）
同时解析了一些标志位

   ============================  ========================
   IEEE80211_RADIOTAP_MCS_SGI    使用短保护间隔
   IEEE80211_RADIOTAP_MCS_BW_40  使用 HT40 模式发送
   ============================  ========================

* IEEE80211_RADIOTAP_DATA_RETRIES

   当使用 IEEE80211_RADIOTAP_RATE 或 IEEE80211_RADIOTAP_MCS 时重试次数

* IEEE80211_RADIOTAP_VHT

   发送时使用的 VHT MCS 和流数（仅对没有自己的速率控制的设备）。还解析了其他字段

   标志字段
       IEEE80211_RADIOTAP_VHT_FLAG_SGI: 使用短保护间隔

   带宽字段
       * 1: 使用 40MHz 信道宽度发送
       * 4: 使用 80MHz 信道宽度发送
       * 11: 使用 160MHz 信道宽度发送

注入代码也可以跳过所有其他当前定义的无线电 tap 字段，便于直接重放捕获的无线电 tap 头。
下面是一个定义某些参数的有效无线电 tap 头的例子：

    0x00, 0x00, // <-- 无线电 tap 版本
    0x0b, 0x00, // <-- 无线电 tap 头长度
    0x04, 0x0c, 0x00, 0x00, // <-- 位图
    0x6c, // <-- 速率
    0x0c, // <-- 发射功率
    0x01 // <-- 天线

紧接着是 IEEE80211 头，例如可能如下所示：

    0x08, 0x01, 0x00, 0x00,
    0xFF, 0xFF, 0xFF, 0xFF, 0xFF, 0xFF,
    0x13, 0x22, 0x33, 0x44, 0x55, 0x66,
    0x13, 0x22, 0x33, 0x44, 0x55, 0x66,
    0x10, 0x86

最后是载荷部分。
构建完数据包内容后，可以通过向处于监控模式的逻辑 mac80211 接口发送（send()）它来发送。也可以使用 libpcap，这样做比绑定套接字到正确的接口要简单，具体操作如下：

    ppcap = pcap_open_live(szInterfaceName, 800, 1, 20, szErrbuf);
    ...
    r = pcap_inject(ppcap, u8aSendBuffer, nLength);

您还可以在这里找到一个完整的注入应用链接：

https://wireless.wiki.kernel.org/en/users/Documentation/packetspammer

Andy Green <andy@warmcat.com>
