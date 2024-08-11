开发密码算法
============================

注册与注销转换
--------------------------------------------

在Crypto API中存在三种不同的注册函数。其中一种用于注册通用的密码转换，而另外两种则专门针对HASH转换和压缩（COMPRESSion）。我们将在单独的一章中讨论后两种，在这里我们只关注通用的注册函数。
在讨论注册函数之前，必须考虑要填充的`struct crypto_alg`数据结构——请参见下面对该数据结构的描述。
通用的注册函数可以在`include/linux/crypto.h`中找到，其定义如下所示。前者函数注册单个转换，而后者则对转换描述数组进行操作。后者在批量注册转换时非常有用，例如当一个驱动程序实现了多个转换时：
::

       int crypto_register_alg(struct crypto_alg *alg);
       int crypto_register_algs(struct crypto_alg *algs, int count);

这些函数的对应反操作如下所示：
::

       void crypto_unregister_alg(struct crypto_alg *alg);
       void crypto_unregister_algs(struct crypto_alg *algs, int count);

注册函数在成功时返回0，失败时返回负的errno值。`crypto_register_algs()`只有在成功注册所有给定算法时才成功；如果它在过程中失败，则会回滚任何更改。
注销函数总是成功的，因此它们没有返回值。不要试图注销当前未注册的算法。
单块对称密码[CIPHER]
---------------------------------------

转换示例：aes, serpent, ...
本节描述了最简单的转换实现，即用于对称密码的[CIPHER]类型。
[CIPHER]类型用于每次处理恰好一个块且块之间没有任何依赖关系的转换。

注册细节
~~~~~~~~~~~~~~~~~~~~~~

[CIPHER]算法的注册具有特定性，即`struct crypto_alg`字段`.cra_type`为空。`.cra_u.cipher`必须用适当的回调函数填充以实现此转换。
### 结构体 `cipher_alg` 下的密码定义
#### 使用结构体 `cipher_alg` 定义的单块密码
结构体 `cipher_alg` 定义了一个单块密码。以下是当从内核其他部分操作时，这些函数如何被调用的示意图。请注意，`.cia_setkey()` 的调用可能发生在这些示意图中的任何一个之前或之后，但不能在这些操作正在进行时发生。
```
KEY ---.    PLAINTEXT ---
v                 v
              .cia_setkey() -> .cia_encrypt()
                                      |
                                      '-----> CIPHERTEXT
```

请注意，多次调用 `.cia_setkey()` 也是有效的：
```
KEY1 --.    PLAINTEXT1 --.         KEY2 --.    PLAINTEXT2 --
v                 v                v                 v
       .cia_setkey() -> .cia_encrypt() -> .cia_setkey() -> .cia_encrypt()
                               |                                  |
                               '---> CIPHERTEXT1                  '---> CIPHERTEXT2
```

#### 多块密码
##### 示例转换：cbc(aes)，chacha20 等
本节描述了多块密码转换实现。多块密码用于处理传递给转换函数的数据散列表。它们也将结果输出到一个数据散列表中。

##### 注册细节
多块密码算法的注册是整个密码API中最标准的过程之一。注意，如果密码实现要求数据有适当的对齐，则调用者应使用 `crypto_skcipher_alignmask()` 函数来识别内存对齐掩码。内核密码API能够处理未对齐的请求。然而，这意味着额外的开销，因为内核密码API需要执行数据的重新对齐，这可能涉及到数据移动。

### 使用结构体 `skcipher_alg` 定义的密码
#### 使用结构体 `skcipher_alg` 定义的多块密码
结构体 `skcipher_alg` 定义了一个多块密码，或者更一般地说，定义了一个长度保持不变的对称密码算法。
散列列表处理
~~~~~~~~~~~~~~~~~~~~

某些驱动程序可能希望使用通用的散列遍历（ScatterWalk），当硬件需要被分别供给包含明文和将包含密文的散列列表中的独立数据块时。请参考由Linux内核提供的散列/聚集列表实现中所给出的ScatterWalk接口。
哈希 [HASH]
--------------

变换示例：crc32、md5、sha1、sha256等。
注册与注销变换
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

注册HASH变换有多种方式，这取决于变换是同步的[SHASH]还是异步的[AHASH]，以及我们正在注册的HASH变换数量。你可以在`include/crypto/internal/hash.h`中找到这些函数原型定义：

```
int crypto_register_ahash(struct ahash_alg *alg);

int crypto_register_shash(struct shash_alg *alg);
int crypto_register_shashes(struct shash_alg *algs, int count);
```

相应的用于注销HASH变换的函数如下：

```
void crypto_unregister_ahash(struct ahash_alg *alg);

void crypto_unregister_shash(struct shash_alg *alg);
void crypto_unregister_shashes(struct shash_alg *algs, int count);
```

使用`struct shash_alg` 和 `ahash_alg` 定义密码
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

下面是这些函数在从内核其他部分调用时的操作流程图。请注意，`.setkey()` 调用可能会在这些操作之前或之后发生，但不应在任何这些操作正在进行时发生。需要注意的是，调用 `.init()` 紧接着 `.final()` 也是完全有效的变换过程。
```
I)   数据 -----------
v
             .init() -> .update() -> .final()      ! .update() 可能不会在这个场景下被调用
                         ^    |         |            在这种情况下可能根本不被调用
'----'         '---> 哈希

II)  数据 -----------.-----------
v           v
             .init() -> .update() -> .finup()      ! .update() 可能在这种场景下不被调用
                         ^    |         |            在这种情况下可能根本不被调用
'----'         '---> 哈希

III) 数据 -----------
v
                        .digest()                  ! 整个过程由 .digest() 调用来处理
                            |
'---------------> 哈希
```

下面是`.export()` 和 `.import()` 函数在从内核其他部分调用时的操作流程图。
注意，在这种情况下 `.update()` 可能不会被调用：
```
KEY--.                 DATA--
v                       v                  ! .update() 在此场景中可能根本不会被调用
        .setkey() -> .init() -> .update() -> .export()  
^     |         |
                                 '-----'         '--> PARTIAL_HASH

       ----------- 其他转换在此发生 -----------

       PARTIAL_HASH--.   DATA1--
v          v
                 .import -> .update() -> .final()     ! .update() 在此场景中可能根本不会被调用
                             ^    |         |           不会被调用
'----'         '--> HASH1

       PARTIAL_HASH--.   DATA2-
v         v
                 .import -> .finup()
                               |
                               '---------------> HASH2
```

请注意，放弃请求对象是完全合法的：
- 调用 `.init()` 然后（尽可能多次）调用 `.update()`
- 在未来任何时候不调用 `.final()`, `.finup()` 或者 `.export()`

换句话说，实现应当注意资源分配和清理。
在调用 `.init()` 或 `.update()` 后，不应有任何与请求对象相关的资源保持分配状态，因为可能没有机会释放它们。

### 异步哈希转换的具体事项
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

某些驱动程序希望使用通用散列漫步（Generic ScatterWalk），在这种情况下，实现需要分别处理包含输入数据的分散列表中的各个部分。
