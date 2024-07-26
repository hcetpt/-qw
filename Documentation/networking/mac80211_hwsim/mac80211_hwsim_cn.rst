```plaintext
SPDX 许可证标识符: GPL-2.0
.. include:: <isonum.txt>

===================================================================
mac80211_hwsim - 用于 mac80211 的 802.11 无线设备软件模拟器
===================================================================

:版权所有: |copy| 2008, Jouni Malinen <j@w1.fi>

本程序是自由软件；您可以按照由自由软件基金会发布的 GNU 通用公共许可证第 2 版重新分发或修改它。
介绍
============

mac80211_hwsim 是一个 Linux 内核模块，可用于为 mac80211 模拟任意数量的 IEEE 802.11 无线设备。它可以用来以非常接近使用真实 WLAN 硬件的方式测试大多数 mac80211 功能和用户空间工具（例如，hostapd 和 wpa_supplicant）。从 mac80211 的角度来看，mac80211_hwsim 只不过是另一个硬件驱动程序，即无需对 mac80211 进行任何更改即可使用此测试工具。
mac80211_hwsim 的主要目标是使开发者更容易测试他们的代码并为 mac80211、hostapd 和 wpa_supplicant 添加新功能。模拟的无线设备没有真实硬件的限制，因此可以轻松生成任意测试环境，并且总能在未来的测试中重现相同的环境。此外，由于所有无线操作都是模拟的，因此在测试中可以使用任意频道，而不受监管规则的限制。
mac80211_hwsim 内核模块有一个参数 'radios'，可用于选择要模拟的无线设备数量（默认为 2）。这允许配置非常简单的设置（例如，仅一个接入点和一个工作站）或大规模测试（多个接入点带有数百个工作站）。
mac80211_hwsim 通过跟踪每个虚拟无线设备当前所在的频道，并将所有传输的帧复制给所有启用且处于与发送无线设备相同频道上的其他无线设备来工作。mac80211 中的软件加密被用来确保帧实际上通过虚拟空中接口进行加密，以便更全面地测试加密。
创建了一个独立于 mac80211 的全局监控网络设备 hwsim#，该接口可用于监控所有传输的帧，无论其频道如何。
简单示例
==============

此示例展示了如何使用 mac80211_hwsim 来模拟两个无线设备：一个作为接入点，另一个作为与 AP 关联的工作站。使用 hostapd 和 wpa_supplicant 来处理 WPA2-PSK 认证。此外，hostapd 还处理了接入点端的关联过程。
::


    # 在内核配置中构建 mac80211_hwsim

    # 加载模块
    modprobe mac80211_hwsim

    # 为 wlan0 运行 hostapd (AP)
    hostapd hostapd.conf

    # 为 wlan1 运行 wpa_supplicant (工作站)
    wpa_supplicant -Dnl80211 -iwlan1 -c wpa_supplicant.conf


更多测试用例可以在 hostap.git 中找到：
git://w1.fi/srv/git/hostap.git 和 mac80211_hwsim/tests 子目录
(http://w1.fi/gitweb/gitweb.cgi?p=hostap.git;a=tree;f=mac80211_hwsim/tests)
```
