SPDX 许可证标识符: GPL-2.0

===============
NIC SR-IOV API
===============

建议现代 NIC 集中实现 `switchdev` 模型（参见 :ref:`switchdev`），以配置 SR-IOV 功能的转发和安全。
遗留 API
==========

旧版 SR-IOV API 实现于作为 `RTM_GETLINK` 和 `RTM_SETLINK` 命令一部分的 `rtnetlink` Netlink 家族。在驱动程序端，它包含多个 `ndo_set_vf_*` 和 `ndo_get_vf_*` 回调函数。由于这些遗留 API 与其余堆栈不兼容，该 API 被视为冻结；不接受任何新功能或扩展。新的驱动程序不应实现不常用的回调；以下回调是被禁止的：

 - `ndo_get_vf_port`
 - `ndo_set_vf_port`
 - `ndo_set_vf_rss_query_en`
