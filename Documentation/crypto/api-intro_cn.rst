### SPDX 许可证标识符：GPL-2.0

=============================
散列列表加密 API
=============================

简介
============

散列列表加密 API 接受页面向量（散列列表）作为参数，并直接在页面上操作。在某些情况下（例如 ECB 模式密码），这将允许在原地对页面进行加密而无需复制数据。
该设计的一个初始目标是方便支持 IPsec，以便可以在分页的 skb 上应用处理而无需线性化。

详细信息
=======

在最低层的是算法，它们会动态注册到 API 中。
“转换”是由用户实例化的对象，它们维护状态、处理所有实现逻辑（例如操纵页面向量）并为底层算法提供抽象。但在用户层面，它们非常简单。
从概念上看，API 的分层如下所示：

```
[转换 API]  （用户接口）
[转换操作]  （每种类型的逻辑粘合，例如 cipher.c, compress.c）
[算法 API]  （用于注册算法）
```

目的是让用户接口和算法注册 API 非常简单，同时将核心逻辑隐藏于两者之外。许多现有 API（如 Cryptoapi 和 Nettle）中的好想法已被采纳并应用于此。
API 当前支持五种主要类型的转换：AEAD（附带相关数据的身份验证加密）、块密码、流密码、压缩器和哈希。
请注意，“块密码”这个名字有些误导。它实际上旨在支持所有密码，包括流密码。块密码与流密码的区别在于后者只在一个块上操作，而前者可以对任意数量的数据进行操作，但需符合块大小的要求（即非流密码只能处理块的倍数）。
以下是使用该 API 的示例：

```c
#include <crypto/hash.h>
#include <linux/err.h>
#include <linux/scatterlist.h>

struct scatterlist sg[2];
char result[128];
struct crypto_ahash *tfm;
struct ahash_request *req;

tfm = crypto_alloc_ahash("md5", 0, CRYPTO_ALG_ASYNC);
if (IS_ERR(tfm))
    fail();

/* ... 设置散列列表 ... */

req = ahash_request_alloc(tfm, GFP_ATOMIC);
if (!req)
    fail();

ahash_request_set_callback(req, 0, NULL, NULL);
ahash_request_set_crypt(req, sg, result, 2);

if (crypto_ahash_digest(req))
    fail();

ahash_request_free(req);
crypto_free_ahash(tfm);
```

在回归测试模块 (tcrypt.c) 中有许多实际示例。

开发者注意事项
===============

转换只能在用户上下文中分配，加密方法只能从软中断和用户上下文中调用。对于具有设置密钥方法的转换，该方法也应仅从用户上下文中调用。
当使用 API 进行密码操作时，如果每个散列列表包含的数据是密码块大小的倍数（通常为 8 字节），则性能将是最佳的。这避免了需要在未对齐的页面片段边界之间进行任何复制。
添加新算法
=====================

提交新算法以纳入时，必须满足的要求之一是至少包含几个来自已知来源（最好是标准）的测试向量。
转换现有的知名代码是首选，因为这种代码更有可能经过审查和广泛测试。如果提交的是来自LGPL源码的代码，请考虑将其许可改为GPL（参见LGPL第3节）。
提交的算法还必须通常是无专利限制的（例如，IDEA直到大约2011年左右才会被纳入主线），并且必须基于公认的标准或已经过适当的同行评审。
同时也要检查任何可能与特定算法使用相关的RFC，以及像RFC2451（“ESP CBC模式加密算法”）这样的通用应用说明。
避免大量使用宏并改用内联函数是个好主意，因为GCC在内联方面做得很好，而过度使用宏可能会在某些平台上导致编译问题。
同时请查看下面列出的网站上的TODO列表，看看其他人可能已经在做什么工作。

错误报告
====

请将错误报告发送至：
    linux-crypto@vger.kernel.org

抄送：
    Herbert Xu <herbert@gondor.apana.org.au>,
    David S. Miller <davem@redhat.com>

更多信息
===================

对于更多补丁和各种更新，包括当前的TODO列表，请参见：
http://gondor.apana.org.au/~herbert/crypto/

作者
=======

- James Morris
- David S. Miller
- Herbert Xu

致谢
=======

以下人士在API开发过程中提供了宝贵的反馈：

  - Alexey Kuznetzov
  - Rusty Russell
  - Herbert Valerio Riedel
  - Jeff Garzik
  - Michael Richardson
  - Andrew Morton
  - Ingo Oeser
  - Christoph Hellwig

本API的部分内容源自以下项目：

  Kerneli Cryptoapi（http://www.kerneli.org/）
   - Alexander Kjeldaas
   - Herbert Valerio Riedel
   - Kyle McMartin
   - Jean-Luc Cooke
   - David Bryson
   - Clemens Fruhwirth
   - Tobias Ringstrom
   - Harald Welte

以及；

  Nettle（https://www.lysator.liu.se/~nisse/nettle/）
   - Niels Möller

加密算法的原始开发者：

  - Dana L. How（DES）
  - Andrew Tridgell和Steve French（MD4）
  - Colin Plumb（MD5）
  - Steve Reid（SHA1）
  - Jean-Luc Cooke（SHA256、SHA384、SHA512）
  - Kazunori Miyazawa / USAGI（HMAC）
  - Matthew Skala（Twofish）
  - Dag Arne Osvik（Serpent）
  - Brian Gladman（AES）
  - Kartikey Mahendra Bhatt（CAST6）
  - Jon Oberheide（ARC4）
  - Jouni Malinen（Michael MIC）
  - NTT（日本电报电话公司）（Camellia）

SHA1算法贡献者：
  - Jean-Francois Dive

DES算法贡献者：
  - Raimar Falke
  - Gisle Sælensminde
  - Niels Möller

Blowfish算法贡献者：
  - Herbert Valerio Riedel
  - Kyle McMartin

Twofish算法贡献者：
  - Werner Koch
  - Marc Mutz

SHA256/384/512算法贡献者：
  - Andrew McDonald
  - Kyle McMartin
  - Herbert Valerio Riedel

AES算法贡献者：
  - Alexander Kjeldaas
  - Herbert Valerio Riedel
  - Kyle McMartin
  - Adam J. Richter
  - Fruhwirth Clemens（i586）
  - Linus Torvalds（i586）

CAST5算法贡献者：
  - Kartikey Mahendra Bhatt（原始开发者未知，FSF版权）

TEA/XTEA算法贡献者：
  - Aaron Grothe
  - Michael Ringe

Khazad算法贡献者：
  - Aaron Grothe

Whirlpool算法贡献者：
  - Aaron Grothe
  - Jean-Luc Cooke

Anubis算法贡献者：
  - Aaron Grothe

Tiger算法贡献者：
  - Aaron Grothe

VIA PadLock贡献者：
  - Michal Ludvig

Camellia算法贡献者：
  - NTT（日本电报电话公司）（Camellia）

通用散列步进代码由Adam J. Richter <adam@yggdrasil.com>编写

如果有任何致谢更新或更正，请发送至：
Herbert Xu <herbert@gondor.apana.org.au>
