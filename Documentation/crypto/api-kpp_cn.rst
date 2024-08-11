Key-agreement Protocol Primitives (KPP) 密码算法定义
------------------------------------------------------

.. kernel-doc:: include/crypto/kpp.h
   :functions: kpp_request crypto_kpp kpp_alg kpp_secret

Key-agreement Protocol Primitives (KPP) 密码 API
--------------------------------------------------

.. kernel-doc:: include/crypto/kpp.h
   :doc: 通用 Key-agreement Protocol Primitives API

.. kernel-doc:: include/crypto/kpp.h
   :functions: crypto_alloc_kpp crypto_free_kpp crypto_kpp_set_secret crypto_kpp_generate_public_key crypto_kpp_compute_shared_secret crypto_kpp_maxsize

Key-agreement Protocol Primitives (KPP) 密码请求句柄
-------------------------------------------------------------

.. kernel-doc:: include/crypto/kpp.h
   :functions: kpp_request_alloc kpp_request_free kpp_request_set_callback kpp_request_set_input kpp_request_set_output

ECDH 辅助函数
---------------------

.. kernel-doc:: include/crypto/ecdh.h
   :doc: ECDH 辅助函数

.. kernel-doc:: include/crypto/ecdh.h
   :functions: ecdh crypto_ecdh_key_len crypto_ecdh_encode_key crypto_ecdh_decode_key

DH 辅助函数
-------------------

.. kernel-doc:: include/crypto/dh.h
   :doc: DH 辅助函数

.. kernel-doc:: include/crypto/dh.h
   :functions: dh crypto_dh_key_len crypto_dh_encode_key crypto_dh_decode_key
