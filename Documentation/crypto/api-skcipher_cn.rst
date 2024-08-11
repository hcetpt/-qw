# 块密码算法定义
----------------------------------

.. kernel-doc:: include/linux/crypto.h
   :doc: 块密码算法定义

.. kernel-doc:: include/linux/crypto.h
   :functions: crypto_alg cipher_alg compress_alg

## 对称密钥密码API
------------------------

.. kernel-doc:: include/crypto/skcipher.h
   :doc: 对称密钥密码API

.. kernel-doc:: include/crypto/skcipher.h
   :functions: crypto_alloc_skcipher crypto_free_skcipher crypto_has_skcipher crypto_skcipher_ivsize crypto_skcipher_blocksize crypto_skcipher_setkey crypto_skcipher_reqtfm crypto_skcipher_encrypt crypto_skcipher_decrypt

## 对称密钥密码请求句柄
-----------------------------------

.. kernel-doc:: include/crypto/skcipher.h
   :doc: 对称密钥密码请求句柄

.. kernel-doc:: include/crypto/skcipher.h
   :functions: crypto_skcipher_reqsize skcipher_request_set_tfm skcipher_request_alloc skcipher_request_free skcipher_request_set_callback skcipher_request_set_crypt

## 单块密码API
-----------------------

.. kernel-doc:: include/crypto/internal/cipher.h
   :doc: 单块密码API

.. kernel-doc:: include/crypto/internal/cipher.h
   :functions: crypto_alloc_cipher crypto_free_cipher crypto_has_cipher crypto_cipher_blocksize crypto_cipher_setkey crypto_cipher_encrypt_one crypto_cipher_decrypt_one
