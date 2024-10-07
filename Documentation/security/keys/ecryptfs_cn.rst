加密密钥用于 eCryptfs 文件系统
==========================================

eCryptfs 是一个堆叠文件系统，它使用随机生成的文件加密密钥（FEK）透明地加密和解密每个文件。
每个 FEK 又通过文件加密密钥加密密钥（FEKEK）进行加密，这可以在内核空间或用户空间中由名为 'ecryptfsd' 的守护进程完成。在前一种情况下，操作直接由内核 CryptoAPI 使用从用户提示的密码派生的 FEKEK 完成；在后一种情况下，FEK 由 'ecryptfsd' 使用外部库进行加密，以支持其他机制如公钥加密、PKCS#11 和基于可信平台模块（TPM）的操作。

eCryptfs 定义的数据结构包含了解密 FEK 所需的信息，称为身份验证令牌，并且目前可以存储在一个“用户”类型的内核密钥中，该密钥由随 eCryptfs-utils 包提供的用户空间工具 'mount.ecryptfs' 插入到用户的会话特定密钥环中。

“加密”密钥类型通过引入新的格式 'ecryptfs' 进行了扩展，以便与 eCryptfs 文件系统结合使用。新引入格式的加密密钥在其有效负载中存储了一个身份验证令牌，并且这个 FEKEK 由内核随机生成并受父主密钥保护。

为了避免已知明文攻击，通过命令 'keyctl print' 或 'keyctl pipe' 获得的数据块不包含整个身份验证令牌的内容，因为其内容是众所周知的，而只包含加密形式的 FEKEK。

eCryptfs 文件系统确实可以从使用加密密钥中受益，因为所需的密钥可以由管理员安全生成，并在引导时通过解锁一个“可信”密钥来提供，以便在受控环境中执行挂载。另一个优点是密钥不会暴露给恶意软件威胁，因为它仅在内核级别以明文形式存在。

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

使用 eCryptfs 文件系统的加密密钥示例：

创建一个长度为 64 字节的加密密钥 "1000100010001000"，格式为 'ecryptfs'，并使用之前加载的用户密钥 "test" 保存：

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

使用创建的加密密钥 "1000100010001000" 挂载 eCryptfs 文件系统到 '/secret' 目录：

```
$ mount -i -t ecryptfs -oecryptfs_sig=1000100010001000, \
      ecryptfs_cipher=aes,ecryptfs_key_bytes=32 /secret /secret
```
