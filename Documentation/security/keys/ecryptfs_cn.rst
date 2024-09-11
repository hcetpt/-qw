加密密钥用于 eCryptfs 文件系统
==========================================

eCryptfs 是一个堆叠文件系统，它可以透明地使用随机生成的文件加密密钥（FEK）对每个文件进行加密和解密。每个 FEK 随后会使用文件加密密钥加密密钥（FEKEK）在内核空间或用户空间中通过名为 'ecryptfsd' 的守护进程进行加密。在前一种情况下，操作直接由内核的 CryptoAPI 使用从用户提示的密码派生出的 FEKEK 完成；在后一种情况下，FEK 通过 'ecryptfsd' 和外部库的帮助进行加密，以支持其他机制如公钥加密、PKCS#11 和基于可信平台模块（TPM）的操作。

eCryptfs 定义的数据结构用于包含 FEK 解密所需的信息，称为认证令牌。目前，它可以存储在一个“用户”类型的内核密钥中，并通过用户空间工具 'mount.ecryptfs' 插入到用户的会话特定密钥环中，该工具随 'ecryptfs-utils' 包一起提供。

加密密钥类型通过引入新的格式 'ecryptfs' 进行了扩展，以便与 eCryptfs 文件系统结合使用。新引入格式的加密密钥在其有效负载中存储了一个由内核随机生成并受父主密钥保护的认证令牌。

为了防止已知明文攻击，通过命令 'keyctl print' 或 'keyctl pipe' 获得的数据块不包含整个认证令牌的内容，而只包含加密形式的 FEKEK。

eCryptfs 文件系统确实可以从使用加密密钥中受益，因为所需的密钥可以由管理员安全生成，并在引导时通过解封一个“受信任”的密钥来提供，从而在受控环境中执行挂载。另一个优势是密钥不会暴露于恶意软件的威胁，因为它仅在内核级别以明文形式存在。

用法如下：

```
keyctl add encrypted name "new ecryptfs key-type:master-key-name keylen" ring
keyctl add encrypted name "load hex_blob" ring
keyctl update keyid "update key-type:master-key-name"
```

其中：

```
name := '<16 个十六进制字符>'
key-type := 'trusted' | 'user'
keylen := 64
```

使用加密密钥与 eCryptfs 文件系统的示例：

创建一个长度为 64 字节的加密密钥 "1000100010001000"，格式为 'ecryptfs'，并使用之前加载的用户密钥 "test" 保存它：

```
$ keyctl add encrypted 1000100010001000 "new ecryptfs user:test 64" @u
19184530

$ keyctl print 19184530
ecryptfs user:test 64 490045d4bfe48c99f0d465fbbbb79e7500da954178e2de0697
dd85091f5450a0511219e9f7cd70dcd498038181466f78ac8d4c19504fcc72402bfc41c2
f253a41b7507ccaa4b2b03fff19a69d1cc0b16e71746473f023a95488b6edfd86f7fdd40
9d292e4bacded1258880122dd553a661

$ keyctl pipe 19184530 > ecryptfs.blob
```

使用创建的加密密钥 "1000100010001000" 将 eCryptfs 文件系统挂载到 '/secret' 目录：

```
$ mount -i -t ecryptfs -oecryptfs_sig=1000100010001000, \
      ecryptfs_cipher=aes,ecryptfs_key_bytes=32 /secret /secret
```
