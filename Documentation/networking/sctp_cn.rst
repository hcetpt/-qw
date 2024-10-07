SPDX 许可证标识符: GPL-2.0

=================
Linux 内核 SCTP
=================

这是当前的 Linux 内核 SCTP 参考实现的 BETA 版本。
SCTP（流控制传输协议）是一种基于 IP 的、面向消息的、可靠的传输协议，具有拥塞控制功能，支持透明多归属，并且有多条有序的消息流。
RFC2960 定义了核心协议。IETF SIGTRAN 工作组最初开发了 SCTP 协议，并随后将其移交给运输区域 (TSVWG) 工作组，以继续将 SCTP 发展为一种通用传输协议。
请访问 IETF 网站 (http://www.ietf.org) 获取更多关于 SCTP 的文档。
参见 http://www.ietf.org/rfc/rfc2960.txt。

初始项目目标是创建一个符合 RFC 2960 并提供编程接口（称为 SCTP 套接字扩展中的 UDP 风格 API）的 Linux 内核 SCTP 参考实现，如 IETF Internet-Drafts 中所提议的那样。
注意事项
=======

- lksctp 可以静态构建或作为模块构建。但是，请注意，目前模块移除 lksctp 还不是一个安全的操作。
- 目前有初步的 IPv6 支持，但大部分工作集中在 IPv4 上实现和测试 lksctp。
更多信息，请访问 lksctp 项目网站：

   http://www.sf.net/projects/lksctp

或者通过邮件列表联系 lksctp 开发者：

   <linux-sctp@vger.kernel.org>
