非对称密码算法定义
-------------------------------

.. kernel-doc:: include/crypto/akcipher.h
   :functions: akcipher_alg akcipher_request

非对称密码 API
---------------------

.. kernel-doc:: include/crypto/akcipher.h
   :doc: 通用公钥 API

.. kernel-doc:: include/crypto/akcipher.h
   :functions: crypto_alloc_akcipher crypto_free_akcipher crypto_akcipher_set_pub_key crypto_akcipher_set_priv_key crypto_akcipher_maxsize crypto_akcipher_encrypt crypto_akcipher_decrypt crypto_akcipher_sign crypto_akcipher_verify

非对称密码请求句柄
------------------------------

.. kernel-doc:: include/crypto/akcipher.h
   :functions: akcipher_request_alloc akcipher_request_free akcipher_request_set_callback akcipher_request_set_crypt
