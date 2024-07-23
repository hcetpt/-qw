.. raw:: latex

	\renewcommand\thesection*
	\renewcommand\thesubsection*

.. _process_index:

=============================================
与内核开发社区合作
=============================================

你想成为一名Linux内核开发者吗？欢迎！虽然从技术角度需要学习很多关于内核的知识，了解我们的社区运作方式也同样重要。阅读这些文档将大大简化你合并更改的过程，减少不必要的麻烦。

内核开发工作入门
-----------------------------------------------

首先阅读以下文档：理解这里的内容将有助于你顺利进入内核社区。
.. toctree::
   :maxdepth: 1

   howto
   development-process
   submitting-patches
   submit-checklist

为内核开发者准备的工具和技术指南
------------------------------------------------

以下是内核开发者应熟悉的一系列资料。
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

这些是我们内核社区（以及更广泛的领域）努力遵循的规则。
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

bug是生活中不可避免的事实；重要的是我们应当妥善处理它们。
下面的文档描述了我们对于处理两类特殊bug——回归和安全问题——的政策。
.. toctree::
   :maxdepth: 1

   handling-regressions
   security-bugs
   cve
   embargoed-hardware-issues

维护者信息
----------------------

如何找到接受你的补丁的人。
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
