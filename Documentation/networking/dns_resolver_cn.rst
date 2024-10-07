SPDX 许可证标识符: GPL-2.0

===================
DNS 解析模块
===================

.. 目录:

- 概览
- 编译
- 设置
- 使用
- 机制
- 调试

概览
========

DNS 解析模块为内核服务提供了一种通过请求类型为 dns_resolver 的密钥来进行 DNS 查询的方式。这些查询通过 `/sbin/request-key` 上调至用户空间。这些例程必须得到用户空间工具 `dns.upcall`、`cifs.upcall` 和 `request-key` 的支持。该模块仍在开发中，尚未提供完整的功能集。它目前支持以下功能：

(*) 实现了用于联系用户空间的 dns_resolver 密钥类型。

尚未支持以下 AFS 功能：

(*) 对 AFSDB 资源记录的 DNS 查询支持。

此代码是从 CIFS 文件系统中提取出来的。
编译
===========

要启用该模块，需要开启内核配置选项：

```
CONFIG_DNS_RESOLVER	- 三态 "DNS 解析器支持"
```

设置
==========

为了设置此功能，必须修改 `/etc/request-key.conf` 文件，以便 `/sbin/request-key` 能够正确地调度上层调用。例如，为了处理基本的域名到 IPv4/IPv6 地址解析，应添加以下行：

```
#OP	TYPE		DESC	CO-INFO	PROGRAM ARG1 ARG2 ARG3 ..
#======	============	=======	=======	==========================
create	dns_resolver  	*	*	/usr/sbin/cifs.upcall %k
```

为了处理特定查询类型 'foo' 的请求，应在上述通用行之前添加如下行，以便首先匹配特定类型：

```
create	dns_resolver  	foo:*	*	/usr/sbin/dns.foo %k
```

使用
=====

要使用此功能，可以在执行以下操作后调用模块中实现的以下函数之一：

```c
#include <linux/dns_resolver.h>
```

```c
int dns_query(const char *type, const char *name, size_t namelen,
	      const char *options, char **_result, time_t *_expiry);
```

这是基本访问函数。它会查找缓存中的 DNS 查询，如果没有找到，则会上调用户空间进行新的 DNS 查询，并可能将结果缓存。键描述将以如下形式构造：

```
[<type>:]<name>
```

其中 `<type>` 可选地指定了要调用的特定上层程序，从而决定了查询类型，而 `<name>` 指定了要查找的字符串。默认查询类型是直接从主机名到 IP 地址集的查找。

`name` 参数不需要是一个以 NUL 结尾的字符串，其长度应由 `namelen` 参数给出。
`options` 参数可以为 NULL 或者是一组与查询类型相关的选项。
返回值是一个与查询类型相符的字符串。例如，对于默认查询类型，它只是一个逗号分隔的 IPv4 和 IPv6 地址列表。调用者必须释放结果。
成功时返回结果字符串的长度，否则返回一个负的错误码。如果 DNS 查找失败，将返回 `-EKEYREJECTED`。
如果 `_expiry` 不为 NULL，则还会返回结果的有效期（TTL）。
内核维护一个内部密钥环，在其中缓存查找到的密钥。具有 `CAP_SYS_ADMIN` 权限的任何进程可以通过在密钥环 ID 上使用 `KEYCTL_KEYRING_CLEAR` 来清除它。

从用户空间读取 DNS 密钥
===============================

可以使用 `keyctl_read()` 或 `keyctl read/print/pipe` 从用户空间读取 `dns_resolver` 类型的密钥。
机制
=========

dns_resolver 模块注册了一种称为 "dns_resolver" 的密钥类型。这种类型的密钥用于传输和缓存用户空间中的 DNS 查询结果。当调用 dns_query() 函数时，它会调用 request_key() 来搜索本地密钥环中是否有缓存的 DNS 结果。如果没有找到缓存结果，则会调用用户空间来获取新的结果。

调用用户空间是通过 request_key() 的上层调用向量进行的，并且通过 /etc/request-key.conf 文件中的配置行来指导 /sbin/request-key 应该运行哪个程序来实例化密钥。

上层调用处理程序程序负责查询 DNS，并将结果处理成适合传递给 keyctl_instantiate_key() 函数的形式。然后该数据会被传递给 dns_resolver_instantiate() 函数，该函数会剥离并处理包含在数据中的任何选项，然后将字符串的其余部分作为有效负载附加到密钥上。

上层调用处理程序程序应该将密钥的有效期设置为从所有提取的结果记录中得到的最低 TTL（生存时间）。这意味着当密钥持有的数据过期时，密钥将会被丢弃并重新创建。

dns_query() 返回附着在密钥上的值的副本，或者如果有必要则返回一个错误。

更多关于 request-key 功能的信息，请参见 <file:Documentation/security/keys/request-key.rst>

调试
=========

可以通过向以下文件写入 1 来动态开启调试信息：

```
/sys/module/dns_resolver/parameters/debug
```
