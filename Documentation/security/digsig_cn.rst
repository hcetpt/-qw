数字签名验证 API
================

:作者: Dmitry Kasatkin
:日期: 2011年10月6日


.. 目录

   1. 引言
   2. API
   3. 用户空间工具


引言
====

数字签名验证 API 提供了一种验证数字签名的方法。
目前，数字签名被 IMA/EVM 完整性保护子系统所使用。
数字签名验证是通过精简的内核端口实现的，该端口基于 GnuPG 的多精度整数 (MPI) 库。该内核端口提供了内存分配错误处理、已根据内核编码风格进行了重构，并且修复了 checkpatch.pl 报告的错误和警告。
公钥和签名由头部和 MPI（多精度整数）组成：


    struct pubkey_hdr {
        uint8_t      version;       /* 密钥格式版本 */
        time_t       timestamp;     /* 密钥创建时间，目前总是为 0 */
        uint8_t      algo;
        uint8_t      nmpi;
        char         mpi[0];
    } __packed;

    struct signature_hdr {
        uint8_t      version;       /* 签名格式版本 */
        time_t       timestamp;     /* 签名创建时间 */
        uint8_t      algo;
        uint8_t      hash;
        uint8_t      keyid[8];
        uint8_t      nmpi;
        char         mpi[0];
    } __packed;

`keyid` 等于对整个密钥内容进行 SHA1 哈希后的第 12 到 19 位。
签名头部用作生成签名的输入。
这种方法确保了密钥或签名头部不能被篡改。
它保护了时间戳不被更改，并且可以用于回滚保护。
API
===

当前 API 仅包含一个函数：

    digsig_verify() — 使用公钥进行数字签名验证


    /**
     * digsig_verify() — 使用公钥进行数字签名验证
     * @keyring: 在其中搜索密钥的密钥环
     * @sig: 数字签名
     * @sigen: 签名的长度
     * @data: 数据
     * @datalen: 数据的长度
     * @return: 成功时返回 0，否则返回 -EINVAL
     *
     * 验证数据的完整性与数字签名相符
     * 当前仅支持 RSA
     * 通常情况下，该函数的数据参数是内容的哈希值
     */
```plaintext
// 验证数字签名的函数
int digsig_verify(struct key *keyring, const char *sig, int siglen,
                  const char *data, int datalen);

用户空间工具
=============

签名和密钥管理工具 evm-utils 提供了生成签名、将密钥加载到内核密钥环中的功能。
密钥可以是 PEM 格式，或者转换为内核格式。
当密钥被添加到内核密钥环时，keyid 定义了密钥的名字：例如下面的 5D2B05FC633EE3E8。
下面是 keyctl 工具的示例输出：

	$ keyctl show
	会话密钥环
	-3 --alswrv      0     0  密钥环: _ses
	603976250 --alswrv      0    -1   \_ 密钥环: _uid.0
	817777377 --alswrv      0     0       \_ 用户: kmk
	891974900 --alswrv      0     0       \_ 加密: evm-key
	170323636 --alswrv      0     0       \_ 密钥环: _module
	548221616 --alswrv      0     0       \_ 密钥环: _ima
	128198054 --alswrv      0     0       \_ 密钥环: _evm

	$ keyctl list 128198054
	密钥环中有 1 个密钥:
	620789745: --alswrv     0     0 用户: 5D2B05FC633EE3E8
```
This translation keeps the structure and context of the original text while converting it to Chinese.
