.. raw:: latex

	\renewcommand\thesection*
	\renewcommand\thesubsection*

.. _process_index:

=============================================
与内核开发社区合作
=============================================

你想成为一名 Linux 内核开发者吗？欢迎！虽然在技术层面上有很多关于内核的知识需要学习，但了解我们的社区运作方式也很重要。阅读这些文档将使你在提交变更时遇到的麻烦大大减少。

内核开发入门介绍
-----------------------------------------------

请先阅读以下文档：理解这些内容将有助于你进入内核社区。
.. toctree::
   :maxdepth: 1

   howto
   development-process
   submitting-patches
   submit-checklist

内核开发者的工具和技术指南
------------------------------------------------

这是内核开发者应熟悉的一些材料。
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

政策指南和开发者声明
--------------------------------------

以下是我们在内核社区（及其他方面）努力遵守的规定。
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

处理错误
-----------------

错误是生活中不可避免的事实；重要的是我们要正确处理它们。
以下文档描述了我们对处理某些特殊类型错误（如倒退和安全问题）的政策。
.. toctree::
   :maxdepth: 1

   handling-regressions
   security-bugs
   cve
   embargoed-hardware-issues

维护者信息
----------------------

如何找到接收你的补丁的人。
.. toctree::
   :maxdepth: 1

   maintainer-handbooks
   maintainers

其他资料
--------------

以下是一些大多数开发者感兴趣的社区指南：

.. toctree::
   :maxdepth: 1

   kernel-docs
   deprecated

.. only::  subproject and html

   索引
   =======

   * :ref:`genindex`
