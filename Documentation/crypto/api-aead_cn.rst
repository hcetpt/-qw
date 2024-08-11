认证加密与关联数据 (AEAD) 算法定义
---------------------------------------------------

.. kernel-doc:: include/crypto/aead.h
   :doc: 认证加密与关联数据 (AEAD) 加密算法 API

.. kernel-doc:: include/crypto/aead.h
   :functions: aead_request aead_alg

认证加密与关联数据 (AEAD) 加密算法 API
--------------------------------------------------------------

.. kernel-doc:: include/crypto/aead.h
   :functions: crypto_alloc_aead crypto_free_aead crypto_aead_ivsize crypto_aead_authsize crypto_aead_blocksize crypto_aead_setkey crypto_aead_setauthsize crypto_aead_encrypt crypto_aead_decrypt

异步 AEAD 请求句柄
---------------------------------------

.. kernel-doc:: include/crypto/aead.h
   :doc: 异步 AEAD 请求句柄

.. kernel-doc:: include/crypto/aead.h
   :functions: crypto_aead_reqsize aead_request_set_tfm aead_request_alloc aead_request_free aead_request_set_callback aead_request_set_crypt aead_request_set_ad
