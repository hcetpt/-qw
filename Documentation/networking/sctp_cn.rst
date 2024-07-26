... SPDX 许可证标识符: GPL-2.0

=================
Linux 内核 SCTP
=================

这是当前 Linux 内核 SCTP 参考实现的 BETA 版本。
SCTP（流控制传输协议）是一种基于 IP、面向消息且可靠的传输协议，具有拥塞控制、对透明多归属的支持以及多条有序的消息流。
RFC2960 定义了该协议的核心部分。IETF 的 SIGTRAN 工作组最初开发了 SCTP 协议，并随后将其移交给传输区域 (TSVWG) 工作组，以便继续作为通用传输协议发展。
请访问 IETF 网站 (http://www.ietf.org) 获取更多关于 SCTP 的文档。
请参阅 http://www.ietf.org/rfc/rfc2960.txt。

该项目的初始目标是创建一个符合 RFC 2960 并提供编程接口（称为 SCTP 的套接字扩展中的 UDP 风格 API）的 Linux 内核 SCTP 参考实现，如 IETF Internet-Drafts 中所提议。
注意事项
=======

- lksctp 可以被构建为静态链接或模块形式。但是，请注意，目前模块卸载 lksctp 还不是一个安全的操作。
- 对 IPv6 有初步支持，但大部分工作集中在 IPv4 上实现和测试 lksctp。
欲了解更多信息，请访问 lksctp 项目网站：

   http://www.sf.net/projects/lksctp

或者通过邮件列表联系 lksctp 开发者：

   <linux-sctp@vger.kernel.org>
