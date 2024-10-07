=================================
Linux 安全模块开发
=================================

根据 https://lore.kernel.org/r/20071026073721.618b4778@laptopd505.fenrus.org，
一个新的 LSM（Linux 安全模块）在以下情况下会被接受进入内核：其意图（描述了它试图保护的内容以及在哪些情况下可以使用它）已经在 ``Documentation/admin-guide/LSM/`` 中进行了适当的文档说明。这使得 LSM 的代码可以很容易地与其目标进行比较，从而让最终用户和发行版能够更明智地决定哪些 LSM 符合他们的需求。

对于可用的 LSM 钩子接口的详细文档，请参阅 ``security/security.c`` 及其相关结构：

.. kernel-doc:: security/security.c
   :export:
