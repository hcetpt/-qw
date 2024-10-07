受信任和加密密钥
==========================

受信任和加密密钥是新增加到现有内核密钥环服务中的两种新型密钥。这两种新型密钥都是可变长度的对称密钥，并且在两种情况下，所有密钥都在内核中创建，用户空间仅看到、存储和加载加密后的数据块。受信任密钥需要一个信任源以提供更高的安全性，而加密密钥可以在任何系统上使用。所有用户级别的数据块都以十六进制ASCII形式显示和加载，以便于使用，并经过完整性验证。

信任源
============

信任源为受信任密钥提供了安全来源。本节列出了当前支持的信任源及其安全性考虑。一个信任源是否足够安全取决于其实施的强度和正确性以及特定用例下的威胁环境。由于内核不知道所处的环境，并且没有信任度量标准，因此依赖于受信任密钥的使用者来判断信任源是否足够安全。

* 存储的信任根

    (1) 可信平台模块（TPM：硬件设备）

        基于存储根密钥（SRK），该密钥永远不会离开TPM，TPM提供密码操作以建立存储的信任根。
    (2) 可信执行环境（TEE：基于Arm TrustZone的OP-TEE）

        基于硬件唯一密钥（HUK），通常烧录在芯片内部的熔丝中，并且只有TEE可以访问。
    (3) 加密加速和保证模块（CAAM：NXP SoC上的IP）

        当高保证启动（HAB）启用且CAAM处于安全模式时，信任根基于OTP MK，这是一把随机生成并烧录到每个SoC中的256位密钥，从不泄露。
        否则，使用一个通用的固定测试密钥。
    (4) 数据协处理器（DCP：各种i.MX SoC的加密加速器）

        基于一次性可编程密钥（OTP），通常烧录在芯片内部的熔丝中，并且只有DCP加密引擎可以访问。
        DCP提供了两个可用作信任根的密钥：OTP密钥和UNIQUE密钥。默认使用UNIQUE密钥，但可以通过模块参数（dcp_use_otp_key）选择OTP密钥。

* 执行隔离

    (1) TPM

        在隔离执行环境中运行的一组固定操作。
    (2) TEE

        在隔离执行环境中运行的一组自定义操作，并通过安全/可信引导过程进行验证。
(3) CAAM

   在隔离的执行环境中运行的一组固定操作。

(4) DCP

   在隔离的执行环境中运行的一组加密操作。仅执行基本的密钥加密。实际的密钥封存/解封在主处理器/内核空间中完成。
   * 可选地绑定到平台完整性状态。

     (1) TPM

         密钥可以可选地封存到指定的PCR（完整性度量）值，并且只有当PCR和数据块的完整性验证匹配时，才能由TPM解封。加载的可信密钥可以用新的（未来的）PCR值进行更新，因此密钥可以轻松迁移到新的PCR值，例如在内核和初始RAM磁盘更新时。同一密钥可以在不同的PCR值下保存多个数据块，因此可以轻松支持多次启动。
(2) TEE

         依赖于安全/可信引导过程来保证平台完整性。可以通过TEE基测量引导过程进行扩展。
(3) CAAM

         依赖于NXP系统级芯片（SoC）的高保证引导（HAB）机制来保证平台完整性。
(4) DCP

         依赖于安全/可信引导过程（供应商称为HAB）来保证平台完整性。
* 接口和API

     (1) TPM

         TPM具有详细记录的标准接口和API。
(2) TEE

         TEE具有详细记录的标准客户端接口和API。更多细节请参阅``Documentation/driver-api/tee.rst``。
(3) CAAM

         接口特定于硅供应商。
(4) DCP

    在``drivers/crypto/mxs-dcp.c``中实现的特定供应商API，作为DCP加密驱动程序的一部分

* 威胁模型

    在使用特定的信任来源来保护与安全相关的数据时，必须评估其强度和适用性

密钥生成
========

受信任的密钥
-------------

新密钥由随机数创建。它们使用存储密钥层次结构中的子密钥进行加密/解密。子密钥的加密和解密必须通过信任来源内的强访问控制策略进行保护。所使用的随机数生成器根据选定的信任来源而有所不同：

  *  TPM：基于硬件设备的随机数生成器（RNG）

    密钥在TPM内部生成。不同设备制造商提供的随机数强度可能有所不同。
  *  TEE：基于Arm TrustZone的OP-TEE随机数生成器（RNG）

    随机数生成器可以根据平台需求进行定制。它可以是直接来自平台特定硬件随机数生成器的输出，也可以是一个基于多个熵源的软件Fortuna CSPRNG。
  *  CAAM：内核随机数生成器

    使用普通的内核随机数生成器。为了从CAAM HWRNG对其进行初始化，请启用CRYPTO_DEV_FSL_CAAM_RNG_API并确保设备被探测到。
  *  DCP（数据协处理器：各种i.MX SoC的加密加速器）

    DCP硬件设备本身不提供专用的随机数生成器接口，因此使用内核默认的随机数生成器。具有DCP的SoC（如i.MX6ULL）确实有一个独立于DCP的专用硬件随机数生成器，可以启用以支持内核随机数生成器。
用户可以通过在内核命令行上指定`trusted.rng=kernel`来覆盖使用的随机数生成器，用内核的随机数池替代
加密密钥
--------------

加密密钥不依赖于信任来源，并且速度更快，因为它们使用AES进行加密/解密。新密钥可以由内核生成的随机数或用户提供的已解密数据创建，并使用指定的‘主’密钥进行加密/解密。‘主’密钥可以是受信任密钥或用户密钥类型。加密密钥的主要缺点是，如果它们不是基于受信任密钥，则仅与其加密的用户密钥一样安全。因此，主用户密钥应尽可能安全地加载，最好是在启动早期进行。

使用
=====

受信任密钥使用：TPM
-----------------------

TPM 1.2：默认情况下，受信任密钥在SRK下被封存，SRK具有默认授权值（20字节的0）。这可以在获取所有权时通过TrouSerS工具设置："tpm_takeownership -u -z"
TPM 2.0：用户首先需要创建一个存储密钥并使其持久化，以便密钥在重启后仍然可用。这可以通过以下命令完成：（具体命令未给出，请根据实际需要填写）
使用IBM TSS 2堆栈：

  ```
  #> tsscreateprimary -hi o -st
  Handle 80000000
  #> tssevictcontrol -hi o -ho 80000000 -hp 81000001
  ```

或者使用Intel TSS 2堆栈：

  ```
  #> tpm2_createprimary --hierarchy o -G rsa2048 -c key.ctxt
  [...]
  #> tpm2_evictcontrol -c key.ctxt 0x81000001
  persistentHandle: 0x81000001
  ```

用法：

    keyctl add trusted name "new keylen [options]" ring
    keyctl add trusted name "load hex_blob [pcrlock=pcrnum]" ring
    keyctl update key "update [options]"
    keyctl print keyid

    选项:
       keyhandle=    封装密钥的ASCII十六进制值
                       TPM 1.2：默认值为0x40000000（SRK）
                       TPM 2.0：没有默认值；每次必须传递
       keyauth=      封装密钥的ASCII十六进制认证，默认值为0x00...i
                     （40个ASCII零）
       blobauth=     封装数据的ASCII十六进制认证，默认值为0x00...
                     （40个ASCII零）
       pcrinfo=      PCR_INFO或PCR_INFO_LONG的ASCII十六进制值（无默认值）
       pcrlock=      要扩展以“锁定”blob的PCR编号
       migratable=   0|1，指示是否允许重新封装到新的PCR值，默认值为1（允许重新封装）
       hash=         哈希算法名称。对于TPM 1.x，唯一允许的值是sha1。对于TPM 2.x，允许的值是sha1、sha256、sha384、sha512和sm3-256
       policydigest= 授权策略的摘要，必须使用由'hash='选项指定的相同哈希算法计算
       policyhandle= 定义相同策略并使用相同哈希算法密封密钥的授权策略会话句柄

`keyctl print`返回一个ASCII十六进制格式的封装密钥副本，该格式遵循标准TPM_STORED_DATA格式。新密钥的长度始终以字节表示。
可信密钥可以是32至128字节（256至1024位），上限是为了适应2048位SRK（RSA）密钥长度，并包含所有必要的结构/填充。

### 可信密钥用法：TEE

用法：

    keyctl add trusted name "new keylen" ring
    keyctl add trusted name "load hex_blob" ring
    keyctl print keyid

`keyctl print`返回一个ASCII十六进制格式的封装密钥副本，该格式特定于TEE设备实现。新密钥的长度始终以字节表示。可信密钥可以是32至128字节（256至1024位）。

### 可信密钥用法：CAAM

用法：

    keyctl add trusted name "new keylen" ring
    keyctl add trusted name "load hex_blob" ring
    keyctl print keyid

`keyctl print`返回一个ASCII十六进制格式的封装密钥副本，该格式特定于CAAM。新密钥的长度始终以字节表示。可信密钥可以是32至128字节（256至1024位）。

### 可信密钥用法：DCP

用法：

    keyctl add trusted name "new keylen" ring
    keyctl add trusted name "load hex_blob" ring
    keyctl print keyid

`keyctl print`返回一个ASCII十六进制格式的封装密钥副本，该格式特定于DCP密钥blob实现。新密钥的长度始终以字节表示。可信密钥可以是32至128字节（256至1024位）。
加密密钥使用
--------------------

加密密钥的解密部分可以包含一个简单的对称密钥或更复杂的结构。更复杂结构的格式是应用程序特定的，通过“format”来标识。使用方法如下：

    keyctl add encrypted name "new [format] key-type:master-key-name keylen" 环
    keyctl add encrypted name "new [format] key-type:master-key-name keylen 解密数据" 环
    keyctl add encrypted name "load hex_blob" 环
    keyctl update keyid "update key-type:master-key-name"

其中：

    format := 'default | ecryptfs | enc32'
    key-type := 'trusted' | 'user'

受信任和加密密钥使用的示例
-------------------------------------------

创建并保存一个长度为32字节的受信任密钥“kmk”
注意：当使用带有持久密钥句柄0x81000001的TPM 2.0时，在引号内的语句后追加'keyhandle=0x81000001'，例如"new 32 keyhandle=0x81000001"
::

    $ keyctl add trusted kmk "new 32" @u
    440502848

    $ keyctl show
    会话密钥环
           -3 --alswrv    500   500  密钥环: _ses
     97833714 --alswrv    500    -1   \_ 密钥环: _uid.500
    440502848 --alswrv    500   500       \_ 受信任: kmk

    $ keyctl print 440502848
    0101000000000000000001005d01b7e3f4a6be5709930f3b70a743cbb42e0cc95e18e915
    3f60da455bbf1144ad12e4f92b452f966929f6105fd29ca28e4d4d5a031d068478bacb0b
    27351119f822911b0a11ba3d3498ba6a32e50dac7f32894dd890eb9ad578e4e292c83722
    a52e56a097e6a68b3f56f7a52ece0cdccba1eb62cad7d817f6dc58898b3ac15f36026fec
    d568bd4a706cb60bb37be6d8f1240661199d640b66fb0fe3b079f97f450b9ef9c22c6d5d
    dd379f0facd1cd020281dfa3c70ba21a3fa6fc2471dc6d13ecf8298b946f65345faa5ef0
    f1f8fff03ad0acb083725535636addb08d73dedb9832da198081e5deae84bfaf0409c22b
    e4a8aea2b607ec96931e6f4d4fe563ba

    $ keyctl pipe 440502848 > kmk.blob

从保存的blob加载受信任密钥::

    $ keyctl add trusted kmk "load `cat kmk.blob`" @u
    268728824

    $ keyctl print 268728824
    0101000000000000000001005d01b7e3f4a6be5709930f3b70a743cbb42e0cc95e18e915
    3f60da455bbf1144ad12e4f92b452f966929f6105fd29ca28e4d4d5a031d068478bacb0b
    27351119f822911b0a11ba3d3498ba6a32e50dac7f32894dd890eb9ad578e4e292c83722
    a52e56a097e6a68b3f56f7a52ece0cdccba1eb62cad7d817f6dc58898b3ac15f36026fec
    d568bd4a706cb60bb37be6d8f1240661199d640b66fb0fe3b079f97f450b9ef9c22c6d5d
    dd379f0facd1cd020281dfa3c70ba21a3fa6fc2471dc6d13ecf8298b946f65345faa5ef0
    f1f8fff03ad0acb083725535636addb08d73dedb9832da198081e5deae84bfaf0409c22b
    e4a8aea2b607ec96931e6f4d4fe563ba

重新密封（TPM特有）受信任密钥以新的PCR值::

    $ keyctl update 268728824 "update pcrinfo=`cat pcr.blob`"
    $ keyctl print 268728824
    010100000000002c0002800093c35a09b70fff26e7a98ae786c641e678ec6ffb6b46d805
    77c8a6377aed9d3219c6dfec4b23ffe3000001005d37d472ac8a44023fbb3d18583a4f73
    d3a076c0858f6f1dcaa39ea0f119911ff03f5406df4f7f27f41da8d7194f45c9f4e00f2e
    df449f266253aa3f52e55c53de147773e00f0f9aca86c64d94c95382265968c354c5eab4
    9638c5ae99c89de1e0997242edfb0b501744e11ff9762dfd951cffd93227cc513384e7e6
    e782c29435c7ec2edafaa2f4c1fe6e7a781b59549ff5296371b42133777dcc5b8b971610
    94bc67ede19e43ddb9dc2baacad374a36feaf0314d700af0a65c164b7082401740e489c9
    7ef6a24defe4846104209bf0c3eced7fa1a672ed5b125fc9d8cd88b476a658a4434644ef
    df8ae9a178e9f83ba9f08d10fa47e4226b98b0702f06b3b8

受信任密钥的初始消费者是EVM，它在启动时需要一个高质量的对称密钥用于HMAC保护文件元数据。使用受信任密钥提供了强有力的保证，即EVM密钥没有被用户级别的问题所破坏，并且当密封到平台完整性状态时，可防止启动和离线攻击。创建并保存一个使用上述受信任密钥“kmk”的加密密钥“evm”：

选项1：省略'format'::

    $ keyctl add encrypted evm "new trusted:kmk 32" @u
    159771175

选项2：明确定义'format'为'default'::

    $ keyctl add encrypted evm "new default trusted:kmk 32" @u
    159771175

    $ keyctl print 159771175
    default trusted:kmk 32 2375725ad57798846a9bbd240de8906f006e66c03af53b1b3
    82dbbc55be2a44616e4959430436dc4f2a7a9659aa60bb4652aeb2120f149ed197c564e0
    24717c64 5972dcb82ab2dde83376d82b2e3c09ffc

    $ keyctl pipe 159771175 > evm.blob

从保存的blob加载加密密钥“evm”::

    $ keyctl add encrypted evm "load `cat evm.blob`" @u
    831684262

    $ keyctl print 831684262
    default trusted:kmk 32 2375725ad57798846a9bbd240de8906f006e66c03af53b1b3
    82dbbc55be2a44616e4959430436dc4f2a7a9659aa60bb4652aeb2120f149ed197c564e0
    24717c64 5972dcb82ab2dde83376d82b2e3c09ffc

使用用户提供的解密数据实例化加密密钥“evm”::

    $ evmkey=$(dd if=/dev/urandom bs=1 count=32 | xxd -c32 -p)
    $ keyctl add encrypted evm "new default user:kmk 32 $evmkey" @u
    794890253

    $ keyctl print 794890253
    default user:kmk 32 2375725ad57798846a9bbd240de8906f006e66c03af53b1b382d
    bbc55be2a44616e4959430436dc4f2a7a9659aa60bb4652aeb2120f149ed197c564e0247
    17c64 5972dcb82ab2dde83376d82b2e3c09ffc

受信任和加密密钥的其他用途，如磁盘和文件加密，也是预期的。特别是新格式'ecryptfs'已被定义以便使用加密密钥挂载eCryptfs文件系统。更多用法细节可以在文件``Documentation/security/keys/ecryptfs.rst``中找到。
另一个新格式'enc32'已被定义以支持具有32字节有效负载大小的加密密钥。这最初将用于nvdimm安全性，但可能会扩展到其他需要32字节有效负载的用途。

TPM 2.0 ASN.1 密钥格式
------------------------

TPM 2.0 ASN.1密钥格式设计为易于识别，即使是在二进制形式下（解决了我们在TPM 1.2 ASN.1格式中的问题），并且可以扩展以添加导入密钥和策略等特性：

    TPMKey ::= SEQUENCE {
        type		OBJECT IDENTIFIER
        emptyAuth	[0] EXPLICIT BOOLEAN OPTIONAL
        parent		INTEGER
        pubkey		OCTET STRING
        privkey		OCTET STRING
    }

type 是区分密钥的关键，因为OID由TCG提供以确保唯一性，从而在密钥偏移量3处形成可识别的二进制模式。目前可用的OID有：

    2.23.133.10.1.3 TPM 可加载密钥。这是一个非对称密钥（通常是RSA2048或椭圆曲线），可以通过TPM2_Load()操作导入
    2.23.133.10.1.4 TPM 可导入密钥。这是一个非对称密钥（通常是RSA2048或椭圆曲线），可以通过TPM2_Import()操作导入
    2.23.133.10.1.5 TPM 封装数据。这是一组数据（最多128字节），由TPM封装。它通常代表一个对称密钥，在使用前必须解封
受信任密钥代码仅使用TPM 封装数据OID
emptyAuth 如果密钥具有已知授权""则为真。如果它是假的或不存在，则密钥需要一个显式的授权短语。这主要用于大多数用户空间消费者决定是否提示密码
父键句柄表示父键，位于 0x81 MSO 空间中，例如 RSA 主存储键的 0x81000001。用户空间程序也支持在 0x40 MSO 空间中指定主句柄。如果发生这种情况，则会根据 TCG 定义的模板即时生成主键的椭圆曲线变体到一个易失性对象中，并用作父键。当前内核代码仅支持 0x81 MSO 形式。
公钥（pubkey）是 TPM2B_PRIVATE 的二进制表示形式，不包括初始的 TPM2B 头部，该头部可以从 ASN.1 八位字节字符串长度中重建。
私钥（privkey）是 TPM2B_PUBLIC 的二进制表示形式，不包括初始的 TPM2B 头部，该头部也可以从 ASN.1 八位字节字符串长度中重建。

DCP Blob 格式
--------------

.. kernel-doc:: security/keys/trusted-keys/trusted_dcp.c
   :doc: dcp blob format

.. kernel-doc:: security/keys/trusted-keys/trusted_dcp.c
   :identifiers: struct dcp_blob_fmt
