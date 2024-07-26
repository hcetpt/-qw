... SPDX-License-Identifier: GPL-2.0

===============
网络接口卡 SR-IOV API
===============

现代的网络接口卡（NIC）被强烈建议专注于实现 `switchdev` 模型（参见 :ref:`switchdev` ），以配置SR-IOV功能的转发和安全性。
遗留API
==========

旧版的SR-IOV API是在`rtnetlink` Netlink家族中作为`RTM_GETLINK` 和 `RTM_SETLINK` 命令的一部分实现的。在驱动程序一侧，它由一系列`ndo_set_vf_*` 和 `ndo_get_vf_*` 回调函数组成。由于这些遗留API与系统的其他部分集成不佳，该API被视为冻结状态；不会接受任何新的功能或扩展。新驱动程序不应该实现不常见的回调函数；具体来说，以下回调函数是禁止使用的：

 - `ndo_get_vf_port`
 - `ndo_set_vf_port`
 - `ndo_set_vf_rss_query_en`
