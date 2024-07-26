SPDX 许可证标识符: GPL-2.0

===================
DNS 解析器模块
===================

.. 目录：

- 概览
- 编译
- 配置
- 使用
- 机制
- 调试

概览
========

DNS 解析器模块为内核服务提供了一种通过请求类型为 dns_resolver 的密钥来进行 DNS 查询的方法。这些查询通过 `/sbin/request-key` 被上层调用到用户空间。这些例程必须得到用户空间工具 `dns.upcall`、`cifs.upcall` 和 `request-key` 的支持。它正在开发中，尚未提供完整功能集。它目前支持以下特性：

 (*) 实现了用于联系用户空间的 dns_resolver 密钥类型
它尚不支持以下 AFS 特性：

 (*) 对 AFSDB 资源记录的支持
此代码是从 CIFS 文件系统中提取出来的。
### 编译
==========

应通过开启内核配置选项来启用该模块：

	CONFIG_DNS_RESOLVER	- 三态 "DNS 解析器支持"

### 设置
==========

要设置此功能，必须修改 `/etc/request-key.conf` 文件，以便 `/sbin/request-key` 能够正确地指引上层调用。例如，为了处理基本的域名到 IPv4/IPv6 地址解析，应该添加以下行：

	#OP	TYPE		DESC	CO-INFO	PROGRAM ARG1 ARG2 ARG3 ..
	#======	============	=======	=======	==========================
	create	dns_resolver  	*	*	/usr/sbin/cifs.upcall %k

为了将查询类型为 'foo' 的请求导向特定程序，应在上述更为通用的行之前添加如下行，因为最先匹配的行会被采纳：

	create	dns_resolver  	foo:*	*	/usr/sbin/dns.foo %k

### 使用
=====

要使用此功能，在包含 `<linux/dns_resolver.h>` 后，可以调用以下函数之一：

     ::

	int dns_query(const char *type, const char *name, size_t namelen,
		     const char *options, char **_result, time_t *_expiry);

这是基础访问函数。它会查找缓存中的 DNS 查询结果，如果没有找到，则会调用用户空间程序进行新的 DNS 查询，然后可能将结果缓存起来。密钥描述由如下形式的字符串构成：

		[<type>:]<name>

其中，<type> 可选地指定了要调用的特定上层程序以及要执行的查询类型，而 <name> 指定了要查找的字符串。默认查询类型是直接从主机名查找 IP 地址集合。
参数 `name` 不必是空字符终止的字符串，并且其长度由 `namelen` 参数给出。
参数 `options` 可以为空，也可以是一组与查询类型相关的选项。
返回值是一个与查询类型相适应的字符串。例如，对于默认查询类型，它仅仅是一系列逗号分隔的 IPv4 和 IPv6 地址。调用者需要释放这个结果。
在成功时返回结果字符串的长度，否则返回负的错误代码。如果 DNS 查找失败，则返回 `-EKEYREJECTED`。
如果 `_expiry` 非空，则同时返回结果的有效期（TTL）。
内核维护一个内部密钥环，用于缓存查找过的密钥。
具有 `CAP_SYS_ADMIN` 权限的任何进程都可以使用 `KEYCTL_KEYRING_CLEAR` 对密钥环 ID 进行清除。

### 从用户空间读取 DNS 密钥
===============================

可以通过 `keyctl_read()` 或 `keyctl read/print/pipe` 命令从用户空间读取 `dns_resolver` 类型的密钥。
### 机制

`dns_resolver` 模块注册了一种称为“dns_resolver”的密钥类型。这种类型的密钥用于从用户空间传输和缓存 DNS 查询结果。当调用 `dns_query()` 时，它会调用 `request_key()` 来搜索本地密钥环以查找缓存的 DNS 结果。如果未能找到这样的缓存，则向上调用到用户空间以获取新的结果。

向上调用到用户空间是通过 `request_key()` 的上层调用向量进行的，并且通过 `/etc/request-key.conf` 中的配置行来指导 `/sbin/request-key` 程序运行以实例化密钥。

上层调用处理器程序负责查询 DNS，并将结果处理成适合传递给 `keyctl_instantiate_key()` 函数的形式。然后该函数将数据传递给 `dns_resolver_instantiate()`，后者剥离并处理数据中包含的任何选项，并将字符串剩余部分作为有效载荷附加到密钥上。

上层调用处理器程序应将密钥的有效期设置为从所有记录中提取结果的最低 TTL（生存时间）。这意味着当它持有的数据过期时，密钥会被丢弃并重新创建。

`dns_query()` 返回附加到密钥的值的副本，或者如果指示错误则返回错误。

有关 `request-key` 功能的更多信息，请参阅 `<file:Documentation/security/keys/request-key.rst>`。

### 调试

可以动态地通过写入数字 1 到以下文件来开启调试消息：

```
/sys/module/dns_resolver/parameters/debug
```
