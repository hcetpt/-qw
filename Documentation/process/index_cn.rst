```latex
\renewcommand\thesection*
\renewcommand\thesubsection*

.. _process_index:

=============================================
与内核开发社区合作
=============================================

你想成为一名Linux内核开发者吗？欢迎加入！虽然从技术角度了解内核有许多内容需要学习，但同样重要的是要了解我们的社区是如何运作的。阅读这些文档将使你能够更轻松地将自己的变更合并到主分支中，避免遇到麻烦。

内核开发简介
-----------------------------------------------

请首先阅读以下文档：理解这里的材料将有助于你更快地融入内核社区。
.. toctree::
   :maxdepth: 1

   howto
   development-process
   submitting-patches
   submit-checklist

面向内核开发者的工具和技术指南
------------------------------------------------

以下是内核开发者应该熟悉的一些资料。
.. toctree::
   :maxdepth: 1

   changes
   programming-language
   coding-style
   maintainer-pgp-guide
   email-clients
   applying-patches
   backporting
   adding-syscalls
   volatile-considered-harmful
   botching-up-ioctls

政策指导和开发者声明
--------------------------------------

以下是我们在内核社区（以及其他方面）遵循的规则。
.. toctree::
   :maxdepth: 1

   license-rules
   code-of-conduct
   code-of-conduct-interpretation
   contribution-maturity-model
   kernel-enforcement-statement
   kernel-driver-statement
   stable-api-nonsense
   stable-kernel-rules
   management-style
   researcher-guidelines

处理bug
-----------------

bug是不可避免的事实；重要的是我们要妥善处理它们。
以下文档描述了我们关于处理一些特殊类型的bug（即倒退和安全问题）的政策。
.. toctree::
   :maxdepth: 1

   handling-regressions
   security-bugs
   cve
   embargoed-hardware-issues

维护者信息
----------------------

如何找到愿意接受你的补丁的人。
.. toctree::
   :maxdepth: 1

   maintainer-handbooks
   maintainers

其他资料
--------------

以下是一些大多数开发者感兴趣的关于社区的其他指南：

.. toctree::
   :maxdepth: 1

   kernel-docs
   deprecated

.. only::  subproject and html

   索引
   =======

   * :ref:`genindex`
```
请注意，上述翻译中的 `toctree` 和 `only::` 指令在 Markdown 或普通文本环境中可能无法正常工作，因为它们是 Sphinx 文档生成器特有的指令。
