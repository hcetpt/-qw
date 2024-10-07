### mac80211_hwsim - 用于mac80211的802.11无线软件模拟器

:版权: © 2008, Jouni Malinen <j@w1.fi>

本程序是自由软件；你可以根据由自由软件基金会发布的GNU通用公共许可证第2版进行分发和/或修改。

#### 引言

`mac80211_hwsim` 是一个Linux内核模块，可以用来为mac80211模拟任意数量的IEEE 802.11无线设备。它可以用来测试mac80211的大部分功能以及用户空间工具（例如，hostapd和wpa_supplicant），其方式与使用真实WLAN硬件的情况非常接近。从mac80211的角度来看，`mac80211_hwsim` 只是一个硬件驱动程序，即不需要对mac80211进行任何更改即可使用这个测试工具。

`mac80211_hwsim` 的主要目标是让开发者更容易测试他们的代码，并在mac80211、hostapd和wpa_supplicant中开发新特性。由于模拟的无线设备没有真实硬件的限制，因此可以轻松生成任意测试环境，并且在未来的测试中始终能够重现相同的设置。此外，由于所有无线操作都是模拟的，因此在测试中可以使用任何信道，而不受法规限制的影响。

`mac80211_hwsim` 内核模块有一个参数 `radios`，可用于选择模拟的无线设备数量（默认为2）。这允许配置非常简单的环境（例如，只有一个接入点和一个站点）或大规模测试（多个接入点带有数百个站点）。

`mac80211_hwsim` 通过跟踪每个虚拟无线设备当前所在的信道，并将所有传输的帧复制到所有其他启用且在同一信道上的无线设备上。mac80211中的软件加密用于确保这些帧在虚拟空中接口上被加密，从而可以更全面地测试加密功能。

一个全局监控网卡 `hwsim#` 独立于mac80211创建。该接口可以用来监控所有传输的帧，无论其所在信道如何。

#### 简单示例

此示例展示了如何使用 `mac80211_hwsim` 模拟两个无线设备：一个作为接入点，另一个作为关联到AP的站点。使用hostapd和wpa_supplicant处理WPA2-PSK认证。此外，hostapd还处理接入点端的关联：

```
# 在内核配置中构建mac80211_hwsim

# 加载模块
modprobe mac80211_hwsim

# 运行hostapd（AP）用于wlan0
hostapd hostapd.conf

# 运行wpa_supplicant（站点）用于wlan1
wpa_supplicant -Dnl80211 -iwlan1 -c wpa_supplicant.conf
```

更多的测试用例可以在hostap.git中找到：
`git://w1.fi/srv/git/hostap.git` 和 `mac80211_hwsim/tests` 子目录（http://w1.fi/gitweb/gitweb.cgi?p=hostap.git;a=tree;f=mac80211_hwsim/tests）
