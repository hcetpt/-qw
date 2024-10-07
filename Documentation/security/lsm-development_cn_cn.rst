=================================
Linux 安全模块开发
=================================

根据 https://lore.kernel.org/r/20071026073721.618b4778@laptopd505.fenrus.org，
当一个新的 LSM（Linux 安全模块）被内核接受时，其意图（描述了它试图保护的内容以及在哪些情况下会使用它）需要适当地记录在 `Documentation/admin-guide/LSM/` 目录中。这使得 LSM 的代码可以轻松地与其目标进行对比，从而让用户和发行版能够更明智地选择适合他们需求的 LSM。

对于可用的 LSM 钩子接口的详细文档，请参阅 `security/security.c` 及其相关的结构：

.. kernel-doc:: security/security.c
   :export:
