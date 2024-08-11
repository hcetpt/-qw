### 代码示例
-------------

### 对称密钥密码操作的代码示例
-----------------------------------

此代码使用AES-256-XTS加密一些数据。为了示例的目的，所有输入都是随机字节，加密是在原地进行的，并且假设代码运行在一个可以睡眠的上下文中：

```c
static int test_skcipher(void)
{
        struct crypto_skcipher *tfm = NULL;
        struct skcipher_request *req = NULL;
        u8 *data = NULL;
        const size_t datasize = 512; /* 数据大小（以字节为单位） */
        struct scatterlist sg;
        DECLARE_CRYPTO_WAIT(wait);
        u8 iv[16];  /* AES-256-XTS 需要一个 16 字节的初始化向量 */
        u8 key[64]; /* AES-256-XTS 需要一个 64 字节的密钥 */
        int err;

        /*
         * 分配一个 tfm（转换对象）并设置密钥
*
         * 在实际应用中，通常会对 tfm 和密钥执行多次加密/解密操作。
         * 但在本示例中，我们将仅执行一次加密操作（这不是很高效）
*/

        tfm = crypto_alloc_skcipher("xts(aes)", 0, 0);
        if (IS_ERR(tfm)) {
                pr_err("分配 xts(aes) 处理失败: %ld\n", PTR_ERR(tfm));
                return PTR_ERR(tfm);
        }

        get_random_bytes(key, sizeof(key));
        err = crypto_skcipher_setkey(tfm, key, sizeof(key));
        if (err) {
                pr_err("设置密钥时出错: %d\n", err);
                goto out;
        }

        /* 分配请求对象 */
        req = skcipher_request_alloc(tfm, GFP_KERNEL);
        if (!req) {
                err = -ENOMEM;
                goto out;
        }

        /* 准备输入数据 */
        data = kmalloc(datasize, GFP_KERNEL);
        if (!data) {
                err = -ENOMEM;
                goto out;
        }
        get_random_bytes(data, datasize);

        /* 初始化初始化向量 */
        get_random_bytes(iv, sizeof(iv));

        /*
         * 就地加密数据
*
         * 为了简单起见，在这个示例中我们在继续之前等待请求完成，
         * 即使底层实现是异步的
*
         * 要解密而不是加密，只需将 crypto_skcipher_encrypt() 更改为
         * crypto_skcipher_decrypt()
*/
        sg_init_one(&sg, data, datasize);
        skcipher_request_set_callback(req, CRYPTO_TFM_REQ_MAY_BACKLOG |
                                                 CRYPTO_TFM_REQ_MAY_SLEEP,
                                       crypto_req_done, &wait);
        skcipher_request_set_crypt(req, &sg, &sg, datasize, iv);
        err = crypto_wait_req(crypto_skcipher_encrypt(req), &wait);
        if (err) {
                pr_err("加密数据时出错: %d\n", err);
                goto out;
        }

        pr_debug("加密成功\n");
out:
        crypto_free_skcipher(tfm);
        skcipher_request_free(req);
        kfree(data);
        return err;
}
```

### 使用 SHASH 的操作状态内存的代码示例
---------------------------------------------

```
struct sdesc {
        struct shash_desc shash;
        char ctx[];
};

static struct sdesc *init_sdesc(struct crypto_shash *alg)
{
        struct sdesc *sdesc;
        int size;

        size = sizeof(struct shash_desc) + crypto_shash_descsize(alg);
        sdesc = kmalloc(size, GFP_KERNEL);
        if (!sdesc)
                return ERR_PTR(-ENOMEM);
        sdesc->shash.tfm = alg;
        return sdesc;
}

static int calc_hash(struct crypto_shash *alg,
                 const unsigned char *data, unsigned int datalen,
                 unsigned char *digest)
{
        struct sdesc *sdesc;
        int ret;

        sdesc = init_sdesc(alg);
        if (IS_ERR(sdesc)) {
                pr_info("无法分配 sdesc\n");
                return PTR_ERR(sdesc);
        }

        ret = crypto_shash_digest(&sdesc->shash, data, datalen, digest);
        kfree(sdesc);
        return ret;
}

static int test_hash(const unsigned char *data, unsigned int datalen,
                 unsigned char *digest)
{
        struct crypto_shash *alg;
        char *hash_alg_name = "sha1-padlock-nano";
        int ret;

        alg = crypto_alloc_shash(hash_alg_name, 0, 0);
        if (IS_ERR(alg)) {
                pr_info("无法分配算法 %s\n", hash_alg_name);
                return PTR_ERR(alg);
        }
        ret = calc_hash(alg, data, datalen, digest);
        crypto_free_shash(alg);
        return ret;
}
```

### 随机数生成器使用的代码示例
----------------------------------

```
static int get_random_numbers(u8 *buf, unsigned int len)
{
        struct crypto_rng *rng = NULL;
        char *drbg = "drbg_nopr_sha256"; /* 使用 SHA-256 的哈希 DRBG，无 PR */
        int ret;

        if (!buf || !len) {
                pr_debug("未提供输出缓冲区\n");
                return -EINVAL;
        }

        rng = crypto_alloc_rng(drbg, 0, 0);
        if (IS_ERR(rng)) {
                pr_debug("无法为 %s 分配 RNG 处理\n", drbg);
                return PTR_ERR(rng);
        }

        ret = crypto_rng_get_bytes(rng, buf, len);
        if (ret < 0)
                pr_debug("生成随机数失败\n");
        else if (ret == 0)
                pr_debug("RNG 没有返回数据");
        else
                pr_debug("RNG 返回了 %d 字节的数据\n", ret);

out:
        crypto_free_rng(rng);
        return ret;
}
```
