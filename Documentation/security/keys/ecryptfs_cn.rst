加密的 eCryptfs 文件系统密钥
==========================================

eCryptfs 是一种堆叠式文件系统，它可以透明地使用随机生成的文件加密密钥 (FEK) 加密和解密每个文件。
每个 FEK 又通过文件加密密钥加密密钥 (FEKEK) 进行加密，这可以在内核空间或用户空间中完成，后者借助名为 'ecryptfsd' 的守护进程。
在前者的情况下，操作直接由内核的 CryptoAPI 完成，使用的密钥（FEKEK）是从用户输入的口令派生出来的；而在后者的情况下，FEK 由 'ecryptfsd' 使用外部库进行加密，以支持其他机制，如公钥加密、PKCS#11 和基于可信平台模块 (TPM) 的操作。
eCryptfs 定义的数据结构用于存储 FEK 解密所需的信息，称为认证令牌。目前，它可以存储在一个“用户”类型的内核密钥中，并由与 'ecryptfs-utils' 包一起提供的用户空间工具 'mount.ecryptfs' 插入到用户的会话特定密钥环中。
加密密钥类型已经通过引入新的格式 'ecryptfs' 而扩展，以便与 eCryptfs 文件系统配合使用。新引入的格式的加密密钥在其有效负载中存储一个认证令牌，该令牌使用内核随机生成的 FEKEK 并受父级主密钥保护。
为了防止已知明文攻击，通过命令 'keyctl print' 或 'keyctl pipe' 获取的数据块不包含完整的认证令牌，而是仅包含加密形式的 FEKEK，因为认证令牌的内容是众所周知的。
eCryptfs 文件系统确实可以从使用加密密钥中受益，因为所需的密钥可以由管理员安全地生成，并且在引导时，在解封了“可信”密钥后提供，以便在受控环境中执行挂载。另一个优势是密钥不会暴露于恶意软件的威胁下，因为它只在内核级别以明文形式存在。

使用方法如下：

```
keyctl add encrypted 名称 "新 ecryptfs 密钥类型:主密钥名称 密钥长度" 密钥环
keyctl add encrypted 名称 "加载 hex_blob" 密钥环
keyctl update 密钥ID "更新 密钥类型:主密钥名称"
```

其中：
```
名称 := '<16 个十六进制字符>'
密钥类型 := 'trusted' | 'user'
密钥长度 := 64
```

使用加密密钥与 eCryptfs 文件系统的示例：

创建一个长度为 64 字节的加密密钥 "1000100010001000"，格式为 'ecryptfs'，并使用之前加载的用户密钥 "test" 保存它：

```
$ keyctl add encrypted 1000100010001000 "新 ecryptfs user:test 64" @u
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
$ mount -i -t ecryptfs -o ecryptfs_sig=1000100010001000, \
      ecryptfs_cipher=aes,ecryptfs_key_bytes=32 /secret /secret
```
