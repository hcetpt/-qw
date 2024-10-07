受信任和加密密钥是新增加到现有内核密钥环服务中的两种新型密钥。这两种新型密钥都是可变长度的对称密钥，并且所有密钥都在内核中创建，用户空间只看到、存储和加载加密后的数据块。受信任密钥要求有一个信任源以提高安全性，而加密密钥可以在任何系统上使用。所有用户级别的数据块都以十六进制ASCII形式显示和加载，以便于使用，并且经过完整性验证。

### 信任源

信任源为受信任密钥提供安全来源。本节列出了当前支持的信任源及其安全考虑。一个信任源是否足够安全取决于其实现的强度和正确性，以及特定使用场景下的威胁环境。由于内核不知道具体环境，并且没有信任度量标准，因此依赖于受信任密钥的使用者来判断信任源是否足够安全。

#### 存储的信任根

1. **可信平台模块（TPM：硬件设备）**

    - 基于存储根密钥（SRK），该密钥从不离开TPM，TPM提供了用于建立存储信任根的密码操作。

2. **可信执行环境（TEE：基于Arm TrustZone的OP-TEE）**

    - 基于硬件唯一密钥（HUK），通常烧录在芯片内部的熔丝中，只有TEE可以访问。

3. **加密加速与保证模块（CAAM：NXP SoC上的IP）**

    - 当高保证启动（HAB）启用且CAAM处于安全模式时，信任基于OTP密钥（OTP MK），这是一个在制造时随机生成并烧录到每个SoC中的256位密钥。否则，默认使用一个通用固定测试密钥。

4. **数据协处理器（DCP：各种i.MX SoC的加密加速器）**

    - 基于一次性编程密钥（OTP），通常烧录在芯片内部的熔丝中，只有DCP加密引擎可以访问。DCP提供了两个可用作信任根的密钥：OTP密钥和UNIQUE密钥。默认情况下使用UNIQUE密钥，但可以通过模块参数（dcp_use_otp_key）选择OTP密钥。

#### 执行隔离

1. **TPM**

    - 在隔离执行环境中运行的一组固定的操作。

2. **TEE**

    - 在隔离执行环境中运行的一组可定制的操作，并通过安全/可信引导过程进行验证。

3. **CAAM**

    - 在隔离的执行环境中运行的一组固定操作。

4. **DCP**

    - 在隔离的执行环境中运行的一组加密操作。仅执行基本的密钥加密。实际的密钥封存/解封在主处理器/内核空间中完成。

#### 可选地绑定到平台完整性状态

1. **TPM**

    - 密钥可以可选地根据指定的PCR（完整性测量）值进行封存，并且只有当PCR和blob完整性验证匹配时，才能由TPM解封。加载的可信密钥可以使用新的（未来的）PCR值进行更新，因此密钥可以轻松迁移到新的PCR值，例如在内核和initramfs更新时。相同的密钥可以在不同的PCR值下保存多个blob，从而支持多次启动。

2. **TEE**

    - 依赖于安全/受信任的引导过程来确保平台完整性。可以通过TEE基测量引导过程进行扩展。

3. **CAAM**

    - 依赖于NXP SoC的高保证引导（HAB）机制来确保平台完整性。

4. **DCP**

    - 依赖于安全/受信任的引导过程（供应商称为HAB）来确保平台完整性。

#### 接口和API

1. **TPM**

    - TPM具有详细记录的标准接口和API。

2. **TEE**

    - TEE具有详细记录的标准客户端接口和API。更多细节请参阅 ``Documentation/driver-api/tee.rst``。

3. **CAAM**

    - 接口特定于硅供应商。

4. **DCP**

    - 在 ``drivers/crypto/mxs-dcp.c`` 中作为 DCP 加密驱动程序一部分实现的供应商特定 API。

### 威胁模型

在使用特定的信任来源来保护与安全相关的数据时，必须评估其强度和适用性。

### 密钥生成

#### 受信任的密钥

新密钥由随机数生成。它们使用存储密钥层次结构中的子密钥进行加密/解密。子密钥的加密和解密必须受到信任来源内部强有力的访问控制策略保护。所使用的随机数生成器根据选定的信任来源有所不同：

- **TPM**：基于硬件设备的随机数生成器（RNG）

  - 密钥在TPM内部生成。随机数的强度可能因设备制造商而异。

- **TEE**：基于Arm TrustZone的OP-TEE随机数生成器

  - 随机数生成器可以根据平台需求进行定制。它可以是直接来自特定平台硬件RNG的输出，也可以是一个通过多个熵源播种的基于软件的Fortuna CSPRNG。

- **CAAM**：内核随机数生成器

  - 使用正常的内核随机数生成器。要从CAAM HWRNG播种，请启用CRYPTO_DEV_FSL_CAAM_RNG_API并确保设备被探测到。

- **DCP（数据协处理器：i.MX SoC的加密加速器）**

  - DCP硬件设备本身没有提供专用的RNG接口，因此使用内核默认的随机数生成器。具有DCP的SoC（如i.MX6ULL）确实有一个独立于DCP的专用硬件RNG，可以启用它来支持内核随机数生成器。

用户可以通过在内核命令行中指定`trusted.rng=kernel`来覆盖所使用的随机数生成器，从而覆盖内核的随机数池。

#### 加密密钥

加密密钥不依赖于信任来源，并且速度更快，因为它们使用AES进行加密/解密。新密钥可以从内核生成的随机数或用户提供的解密数据创建，并使用指定的‘主’密钥进行加密/解密。‘主’密钥可以是受信任密钥或用户密钥类型。加密密钥的主要缺点是，如果它们不是基于受信任密钥，则仅与其加密的用户密钥一样安全。因此，主用户密钥应尽可能安全地加载，最好是在启动早期加载。

### 使用

#### 受信任密钥的使用：TPM

TPM 1.2：默认情况下，受信任密钥被封存在SRK下，该SRK具有默认授权值（20字节的0）。这可以在获取所有权时使用TrouSerS工具设置：“tpm_takeownership -u -z”

TPM 2.0：用户首先需要创建一个存储密钥并使其持久化，以便密钥在重启后仍然可用。这可以通过以下命令完成：

- 使用IBM TSS 2堆栈：

  ```
  #> tsscreateprimary -hi o -st
  句柄 80000000
  #> tssevictcontrol -hi o -ho 80000000 -hp 81000001
  ```

- 或使用Intel TSS 2堆栈：

  ```
  #> tpm2_createprimary --hierarchy o -G rsa2048 -c key.ctxt
  [...]
  #> tpm2_evictcontrol -c key.ctxt 0x81000001
  持久句柄: 0x81000001
  ```

用法：

```
keyctl add trusted name "new keylen [选项]" ring
keyctl add trusted name "load hex_blob [pcrlock=pcrnum]" ring
keyctl update key "update [选项]"
keyctl print keyid
```

选项：

- `keyhandle=`：密封密钥的ASCII十六进制值
  - TPM 1.2：默认值为0x40000000（SRK）
  - TPM 2.0：没有默认值；每次必须传递
- `keyauth=`：密封密钥的ASCII十六进制认证，默认值为0x00...i（40个ASCII零）
- `blobauth=`：密封数据的ASCII十六进制认证，默认值为0x00...i（40个ASCII零）
- `pcrinfo=`：PCR_INFO或PCR_INFO_LONG的ASCII十六进制值（没有默认值）
- `pcrlock=`：要扩展以“锁定”blob的PCR编号
- `migratable=`：0|1表示是否允许重新密封到新的PCR值，默认值为1（允许重新密封）
- `hash=`：哈希算法名称。对于TPM 1.x，唯一允许的值是sha1。对于TPM 2.x，允许的值有sha1、sha256、sha384、sha512和sm3-256
- `policydigest=`：授权策略的摘要，必须使用由'hash='选项指定的相同哈希算法计算
- `policyhandle=`：定义相同策略并使用相同哈希算法密封密钥的授权策略会话句柄

"keyctl print"返回一个ASCII十六进制形式的密封密钥副本，其格式遵循标准TPM_STORED_DATA格式。新密钥的长度始终以字节为单位。可信密钥可以是32至128字节（256至1024位），上限是为了适应2048位SRK（RSA）密钥长度，并包含所有必要的结构/填充。

#### 可信密钥用法：TEE

用法：

```
keyctl add trusted name "new keylen" ring
keyctl add trusted name "load hex_blob" ring
keyctl print keyid
```

"keyctl print"返回一个ASCII十六进制形式的密封密钥副本，其格式特定于TEE设备实现。新密钥的长度始终以字节为单位。可信密钥可以是32至128字节（256至1024位）。

#### 可信密钥用法：CAAM

用法：

```
keyctl add trusted name "new keylen" ring
keyctl add trusted name "load hex_blob" ring
keyctl print keyid
```

"keyctl print"返回一个ASCII十六进制形式的密封密钥副本，其格式特定于CAAM。新密钥的长度始终以字节为单位。可信密钥可以是32至128字节（256至1024位）。

#### 可信密钥用法：DCP

用法：

```
keyctl add trusted name "new keylen" ring
keyctl add trusted name "load hex_blob" ring
keyctl print keyid
```

"keyctl print"返回一个ASCII十六进制形式的密封密钥副本，其格式特定于该DCP密钥blob实现。新密钥的长度始终以字节为单位。可信密钥可以是32至128字节（256至1024位）。

#### 加密密钥的使用

解密后的加密密钥可以包含一个简单的对称密钥或更复杂的结构。更复杂结构的格式是特定于应用程序的，由“format”标识。用法如下：

```
keyctl add encrypted name "new [format] key-type:master-key-name keylen" ring
keyctl add encrypted name "new [format] key-type:master-key-name keylen decrypted-data" ring
keyctl add encrypted name "load hex_blob" ring
keyctl update keyid "update key-type:master-key-name"
```

其中：

- `format=`：'default | ecryptfs | enc32'
- `key-type=`：'trusted' | 'user'

### 示例

创建并保存一个名为“kmk”的长度为32字节的受信任密钥：

```
$ keyctl add trusted kmk "new 32" @u
440502848

$ keyctl show
Session Keyring
           -3 --alswrv    500   500  keyring: _ses
     97833714 --alswrv    500    -1   \_ keyring: _uid.500
    440502848 --alswrv    500   500       \_ trusted: kmk

$ keyctl print 440502848
0101000000000000000001005d01b7e3f4a6be5709930f3b70a743cbb42e0cc95e18e915...
```

从保存的blob加载一个受信任密钥：

```
$ keyctl add trusted kmk "load `cat kmk.blob`" @u
268728824

$ keyctl print 268728824
0101000000000000000001005d01b7e3f4a6be5709930f3b70a743cbb42e0cc95e18e915...
```

重新密封（TPM特定）一个受信任密钥以新的PCR值：

```
$ keyctl update 268728824 "update pcrinfo=`cat pcr.blob`"
$ keyctl print 268728824
010100000000002c0002800093c35a09b70fff26e7a98ae786c641e678ec6ffb6b46d805...
```

使用上述受信任密钥“kmk”创建并保存一个加密密钥“evm”：

选项1：省略'format'：

```
$ keyctl add encrypted evm "new trusted:kmk 32" @u
159771175
```

选项2：显式定义'format'为'default'：

```
$ keyctl add encrypted evm "new default trusted:kmk 32" @u
159771175

$ keyctl print 159771175
default trusted:kmk 32 2375725ad57798846a9bbd240de8906f006e66c03af53b1b3...
```

从保存的blob加载一个加密密钥“evm”：

```
$ keyctl add encrypted evm "load `cat evm.blob`" @u
831684262

$ keyctl print 831684262
default trusted:kmk 32 2375725ad57798846a9bbd240de8906f006e66c03af53b1b3...
```

使用用户提供的解密数据实例化一个加密密钥“evm”：

```
$ evmkey=$(dd if=/dev/urandom bs=1 count=32 | xxd -c32 -p)
$ keyctl add encrypted evm "new default user:kmk 32 $evmkey" @u
794890253

$ keyctl print 794890253
default user:kmk 32 2375725ad57798846a9bbd240de8906f006e66c03af53b1b3...
```

### 其他用途

受信任和加密密钥的其他用途，如磁盘和文件加密，是预期中的。特别是新格式'ecryptfs'已被定义，以便使用加密密钥挂载eCryptfs文件系统。更多关于使用方法的详细信息可以在文件``Documentation/security/keys/ecryptfs.rst``中找到。另一个新格式'enc32'已被定义，以支持有效负载大小为32字节的加密密钥。这最初将用于NVDIMM安全，但可能会扩展到其他需要32字节有效负载的用途。

### TPM 2.0 ASN.1密钥格式

TPM 2.0 ASN.1密钥格式设计为即使在二进制形式下也能易于识别（解决了我们在TPM 1.2 ASN.1格式中遇到的问题），并且为了添加像可导入密钥和策略这样的功能而具有可扩展性：

```
TPMKey ::= SEQUENCE {
    type          OBJECT IDENTIFIER
    emptyAuth     [0] EXPLICIT BOOLEAN OPTIONAL
    parent        INTEGER
    pubkey        OCTET STRING
    privkey       OCTET STRING
}
```

type区分了密钥，即使在二进制形式下也是如此，因为OID由TCG提供以确保唯一性，从而在密钥的第3个偏移处形成一个可识别的二进制模式。目前提供的OID有：

- 2.23.133.10.1.3 TPM Loadable key. 这是一个非对称密钥（通常是RSA2048或椭圆曲线），可以通过TPM2_Load()操作导入
- 2.23.133.10.1.4 TPM Importable Key. 这是一个非对称密钥（通常是RSA2048或椭圆曲线），可以通过TPM2_Import()操作导入
- 2.23.133.10.1.5 TPM Sealed Data. 这是一组数据（最多128字节），由TPM密封。通常代表一个对称密钥，必须在使用前解封

受信任密钥代码仅使用TPM Sealed Data OID。
emptyAuth为true表示密钥有已知授权""。如果它是false或不存在，则密钥需要显式授权短语。大多数用户空间消费者都使用此功能来决定是否提示输入密码。
父键句柄代表父键的句柄，可以在 0x81 MSO 空间中表示，例如 RSA 主存储键的句柄为 0x81000001。用户空间程序也支持在 0x40 MSO 空间中指定主句柄。如果发生这种情况，将根据 TCG 定义的模板即时生成一个易失性对象作为主键的椭圆曲线变体，并用作父键。当前内核代码仅支持 0x81 MSO 形式。
公钥（pubkey）是 TPM2B_PRIVATE 的二进制表示，不包括初始的 TPM2B 头部，该头部可以从 ASN.1 八位字节字符串长度中重建。
私钥（privkey）是 TPM2B_PUBLIC 的二进制表示，不包括初始的 TPM2B 头部，该头部也可以从 ASN.1 八位字节字符串长度中重建。

### DCP Blob 格式

.. kernel-doc:: security/keys/trusted-keys/trusted_dcp.c
   :doc: dcp blob format

.. kernel-doc:: security/keys/trusted-keys/trusted_dcp.c
   :identifiers: struct dcp_blob_fmt
