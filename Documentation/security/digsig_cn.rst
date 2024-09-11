数字签名验证API
==================

作者: Dmitry Kasatkin  
日期: 2011年10月6日

目录

   1. 引言
   2. API
   3. 用户空间工具


引言
============

数字签名验证API提供了一种验证数字签名的方法。
目前，数字签名被IMA/EVM完整性保护子系统使用。
数字签名验证是通过简化版的内核端口GnuPG多精度整数（MPI）库实现的。该内核端口提供了内存分配错误处理，并根据内核编码风格进行了重构，修复了checkpatch.pl报告的错误和警告。
公钥和签名由头部和MPI组成：

```c
struct pubkey_hdr {
    uint8_t     version;      /* 密钥格式版本 */
    time_t      timestamp;    /* 密钥创建时间，目前总是0 */
    uint8_t     algo;
    uint8_t     nmpi;
    char        mpi[0];
} __packed;

struct signature_hdr {
    uint8_t     version;      /* 签名格式版本 */
    time_t      timestamp;    /* 签名创建时间 */
    uint8_t     algo;
    uint8_t     hash;
    uint8_t     keyid[8];
    uint8_t     nmpi;
    char        mpi[0];
} __packed;
```

`keyid` 等于整个密钥内容的SHA1[12-19]。
签名头部用于生成签名。
这种方法确保密钥或签名头部不能被更改。
它保护了时间戳不被更改，并且可以用于回滚保护。

API
===

当前API只包含一个函数：

`digsig_verify()` — 使用公钥进行数字签名验证

```c
/**
 * digsig_verify() - 使用公钥进行数字签名验证
 * @keyring: 要搜索密钥的密钥环
 * @sig: 数字签名
 * @sigen: 签名长度
 * @data: 数据
 * @datalen: 数据长度
 * @return: 成功返回0，否则返回-EINVAL
 *
 * 验证数据完整性与数字签名相符
 * 目前仅支持RSA
 * 通常情况下，内容的哈希值作为此函数的数据
 */
```
```c
/*
 * 验证数字签名的函数
 */
int digsig_verify(struct key *keyring, const char *sig, int siglen,
		  const char *data, int datalen);

用户空间工具
==============

签名和密钥管理工具 `evm-utils` 提供了生成签名及将密钥加载到内核密钥环的功能。
密钥可以是 PEM 格式或转换为内核格式。
当密钥被添加到内核密钥环时，密钥 ID 定义了密钥的名字：例如下面的 5D2B05FC633EE3E8。
以下是 `keyctl` 工具的一个示例输出：

	$ keyctl show
	Session Keyring
	-3 --alswrv      0     0  keyring: _ses
	603976250 --alswrv      0    -1   \_ keyring: _uid.0
	817777377 --alswrv      0     0       \_ user: kmk
	891974900 --alswrv      0     0       \_ encrypted: evm-key
	170323636 --alswrv      0     0       \_ keyring: _module
	548221616 --alswrv      0     0       \_ keyring: _ima
	128198054 --alswrv      0     0       \_ keyring: _evm

	$ keyctl list 128198054
	1 key in keyring:
	620789745: --alswrv     0     0 user: 5D2B05FC633EE3E8
```
