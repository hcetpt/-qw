.. SPDX-License-Identifier: GPL-2.0

===================================================================
TDX 客户端 API 文档
===================================================================

1. 一般描述
======================

TDX 客户端驱动通过 `/dev/tdx-guest` 杂项设备暴露 IOCTL 接口，允许用户空间获取特定的 TDX 客户端详细信息。

2. API 描述
==================

在本节中，对于每个支持的 IOCTL，提供了以下信息以及通用描述：
- 输入参数：传递给 IOCTL 的参数及其相关细节。
- 输出：输出数据和返回值的详情（包括非常见错误值的详情）。

2.1 TDX_CMD_GET_REPORT0
-----------------------

- 输入参数：struct tdx_report_req
- 输出：成功执行后，TDREPORT 数据将被复制到 `tdx_report_req.tdreport` 并返回 0。如果操作数无效则返回 `-EINVAL`；如果 TDCALL 失败则返回 `-EIO` 或其他常见失败的标准错误号。

TDX_CMD_GET_REPORT0 IOCTL 可以让验证软件使用 TDCALL[TDG.MR.REPORT] 从 TDX 模块获取 TDREPORT0（也称为 TDREPORT 子类型 0）。在 IOCTL 命令末尾添加了子类型索引以唯一标识特定子类型的 TDREPORT 请求。尽管 TDX 模块 v1.0 规范中标题为“TDG.MR.REPORT”的部分提到了子类型选项，但目前并未使用该选项，并且期望此值为 0。因此，为了使 IOCTL 实现简单化，子类型选项未作为输入 ABI 的一部分包含进来。然而，如果将来 TDX 模块支持多个子类型，则会创建一个新的 IOCTL 命令来处理它。为了保持 IOCTL 命名的一致性，在 IOCTL 命令中加入了子类型索引。

参考
---------

TDX 参考资料收集如下：

https://www.intel.com/content/www/us/en/developer/articles/technical/intel-trust-domain-extensions.html

该驱动基于 TDX 模块规范 v1.0 和 TDX GHCI 规范 v1.0。
