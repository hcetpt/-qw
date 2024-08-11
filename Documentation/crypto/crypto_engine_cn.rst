### SPDX 许可证标识符: GPL-2.0

#### 加密引擎
===============

##### 概览
------
加密引擎（CE）API 是一个加密队列管理器。

##### 要求
------
您必须在转换上下文 your_tfm_ctx 的开头放置结构体 `crypto_engine`：

```c
struct your_tfm_ctx {
    struct crypto_engine engine;
    // ...
};
```

加密引擎仅管理形式为 `crypto_async_request` 的异步请求。它无法知道底层请求的类型，因此只能访问转换结构体。无法使用 `container_of` 访问上下文。此外，引擎对您的结构体 `"struct your_tfm_ctx"` 一无所知。引擎假定（要求）已知成员 `struct crypto_engine` 放置在开头。

##### 操作顺序
-------------------
您需要通过 `crypto_engine_alloc_init()` 获取 `struct crypto_engine`。然后通过 `crypto_engine_start()` 启动它。完成工作后，请使用 `crypto_engine_stop()` 关闭引擎，并使用 `crypto_engine_exit()` 销毁引擎。
在传输任何请求之前，您必须通过提供以下功能来填充上下文 enginectx：

* `prepare_crypt_hardware`: 在调用任何准备函数之前调用一次。
* `unprepare_crypt_hardware`: 在所有未准备函数被调用之后调用一次。
* `prepare_cipher_request`/`prepare_hash_request`: 在执行每个对应的请求之前调用。如果需要进行某些处理或其他准备工作，在这里完成。
* `unprepare_cipher_request`/`unprepare_hash_request`: 在每个请求处理之后调用。清理或撤销在准备函数中所做的操作。
* `cipher_one_request`/`hash_one_request`: 通过执行操作来处理当前请求。
请注意，这些函数会访问与接收到的请求相关联的 `crypto_async_request` 结构体。你可以通过以下方式来检索原始请求：

::

    container_of(areq, struct yourrequesttype_request, base);

当你的驱动程序接收到一个 crypto_request 时，你必须通过以下其中一个函数将其传递给 crypto 引擎：

* crypto_transfer_aead_request_to_engine()

* crypto_transfer_akcipher_request_to_engine()

* crypto_transfer_hash_request_to_engine()

* crypto_transfer_kpp_request_to_engine()

* crypto_transfer_skcipher_request_to_engine()

在请求处理结束时，需要调用以下其中一个函数：

* crypto_finalize_aead_request()

* crypto_finalize_akcipher_request()

* crypto_finalize_hash_request()

* crypto_finalize_kpp_request()

* crypto_finalize_skcipher_request()
