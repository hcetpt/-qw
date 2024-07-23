... SPDX-License-Identifier: GPL-2.0

===============
网络接口卡 SR-IOV API
===============

现代网络接口卡（NIC）被强烈建议集中实现 `switchdev` 模型（参见 :ref:`switchdev`），以配置SR-IOV功能的转发和安全。
遗留API
======

旧版SR-IOV API在`rtnetlink` Netlink家族中作为`RTM_GETLINK`和`RTM_SETLINK`命令的一部分实现。在驱动程序端，它由一系列`ndo_set_vf_*`和`ndo_get_vf_*`回调函数组成。
由于遗留API与其余堆栈集成不佳，该API被视为冻结；不会接受任何新功能或扩展。新的驱动程序不应实现不常用的回调；具体来说，以下回调不在允许范围内：

 - `ndo_get_vf_port`
 - `ndo_set_vf_port`
 - `ndo_set_vf_rss_query_en`
