.. _kernel_docs:

进一步内核文档索引
=====================

在 linux-kernel 邮件列表中，不断出现请求信息指针的相同问题，这使得编写此类文档的需求变得明显。幸运的是，随着越来越多的人使用 GNU/Linux，越来越多的人对内核产生了兴趣。但是阅读源代码并不总是足够的。理解代码很容易，但可能会错过其背后的原理、理念和设计决策。
不幸的是，适合初学者入门的文档并不多。即使存在，也没有一个“广为人知”的地方来跟踪这些文档。以下内容试图弥补这一不足。
请务必，如果您知道任何未列出的文章或撰写了一份新的文档，请按照内核补丁提交流程在此处添加引用。任何更正、想法或评论也都是受欢迎的。
所有文档都用以下字段进行编目：文档的“标题”、“作者”，可以在哪里找到它们的“URL”，以及一些有助于搜索特定主题的“关键词”，还有一个简短的“描述”。

.. note::

   本文档各部分中的文档按发布时间排序，从最新的到最旧的。维护者应定期淘汰过时或不再更新的资源；基础书籍除外。

Linux 内核树中的文档
-----------------------------

Sphinx 书籍应通过 ``make {htmldocs | pdfdocs | epubdocs}`` 构建
* 名称: **linux/Documentation**

    :作者: 多人
    :位置: Documentation/
    :关键词: 文本文件, Sphinx
描述：随内核源码一起提供的文档，位于Documentation目录中。此文档中的某些页面（包括本文档本身）已移至该目录，并且可能比网页版本更新。

在线文档
--------

* 标题：**Linux 内核邮件列表词汇表**

  :作者: 多位作者
  :网址: https://kernelnewbies.org/KernelGlossary
  :日期: 滚动版本
  :关键词: 词汇表, 术语, Linux 内核
  :描述: 从介绍部分：“本词汇表旨在简要描述您在讨论 Linux 内核时可能会听到的一些缩写和术语。”

* 标题：**Linux 内核模块编程指南**

  :作者: Peter Jay Salzman, Michael Burian, Ori Pomerantz, Bob Mottram, Jim Huang
  :网址: https://sysprog21.github.io/lkmpg/
  :日期: 2021
  :关键词: 模块, GPL 书籍, /proc, ioctl, 系统调用, 中断处理程序
  :描述: 一本非常不错的关于模块编程的 GPL 书籍。包含大量示例。目前新版本正在 https://github.com/sysprog21/lkmpg 积极维护。

* 标题：**Rust for Linux**

  :作者: 多位作者
  :网址: https://rust-for-linux.com/
  :日期: 滚动版本
  :关键词: 词汇表, 术语, Linux 内核
  :描述: 从网站上：“Rust for Linux 是一个将 Rust 语言支持添加到 Linux 内核的项目。本网站旨在作为与该项目相关的链接、文档和资源的中心。”

出版书籍
---------

* 标题：**实用 Linux 系统管理：安装、配置和管理指南，第一版**

  :作者: Kenneth Hess
  :出版社: O'Reilly Media
  :日期: 2023 年 5 月
  :页数: 246
  :ISBN: 978-1098109035
  :备注: 系统管理

* 标题：**Linux 内核调试：利用经过验证的工具和高级技术有效调试 Linux 内核和内核模块**

  :作者: Kaiwan N Billimoria
  :出版社: Packt Publishing Ltd
  :日期: 2022 年 8 月
  :页数: 638
  :ISBN: 978-1801075039
  :备注: 调试书籍

* 标题：**Linux 内核编程：全面了解内核内部机制、编写内核模块和内核同步**

  :作者: Kaiwan N Billimoria
  :出版社: Packt Publishing Ltd
  :日期: 2021 年 3 月（第二版于 2024 年出版）
  :页数: 754
  :ISBN: 978-1789953435（第二版 ISBN 为 978-1803232225）

* 标题：**Linux 内核编程 第二部分 - 字符设备驱动程序和内核同步：创建用户-内核接口，处理外围 I/O 和硬件中断**

  :作者: Kaiwan N Billimoria
  :出版社: Packt Publishing Ltd
  :日期: 2021 年 3 月
  :页数: 452
  :ISBN: 978-1801079518

* 标题：**Linux 系统编程：直接与内核和 C 库通信**

  :作者: Robert Love
  :出版社: O'Reilly Media
  :日期: 2013 年 6 月
  :页数: 456
  :ISBN: 978-1449339531
  :备注: 基础书籍

* 标题：**Linux 内核开发，第三版**

  :作者: Robert Love
  :出版社: Addison-Wesley
  :日期: 2010 年 7 月
  :页数: 440
  :ISBN: 978-0672329463
  :备注: 基础书籍

.. _ldd3_published:

* 标题：**Linux 设备驱动程序，第三版**

  :作者: Jonathan Corbet, Alessandro Rubini, 和 Greg Kroah-Hartman
  :出版社: O'Reilly & Associates
  :日期: 2005
  :页数: 636
  :ISBN: 0-596-00590-3
  :备注: 基础书籍。更多信息见 http://www.oreilly.com/catalog/linuxdrive3/。PDF 格式，网址：https://lwn.net/Kernel/LDD3/

* 标题：**UNIX 操作系统的设计**

  :作者: Maurice J. Bach
  :出版社: Prentice Hall
  :日期: 1986
  :页数: 471
  :ISBN: 0-13-201757-1
  :备注: 基础书籍

杂项
-----

* 名称：**交叉引用 Linux**

  :网址: https://elixir.bootlin.com/
  :关键词: 浏览源代码
  :描述: 另一个基于 Web 的 Linux 内核源代码浏览器
许多变量和函数的交叉引用。你可以看到它们的定义位置和使用位置。

* 名称：**Linux Weekly News**
  * URL: https://lwn.net
  * 关键词: 最新的内核新闻
  * 描述: 标题说明了一切。有一个固定的内核部分，总结了开发人员在本周的工作、错误修复、新功能以及发布的版本。

* 名称：**Linux-MM 主页**
  * 作者: Linux-MM 团队
  * URL: https://linux-mm.org/
  * 关键词: 内存管理、Linux-MM、mm 补丁、待办事项、文档、邮件列表
  * 描述: 一个致力于 Linux 内存管理开发的网站。包含内存相关的补丁、教程、链接、mm 开发者等信息。如果你对内存管理开发感兴趣，不要错过这个网站！

* 名称：**Kernel Newbies IRC 频道和网站**
  * URL: https://www.kernelnewbies.org
  * 关键词: IRC、新手、频道、询问问题
  * 描述: #kernelnewbies 在 irc.oftc.net 上
  * #kernelnewbies 是一个专门面向“新手”内核黑客的 IRC 网络。观众主要由正在学习内核、从事内核项目或希望帮助不太有经验的内核开发者的专业内核黑客组成。
  * #kernelnewbies 位于 OFTC IRC 网络上。
尝试将 irc.oftc.net 作为服务器，并使用命令 /join #kernelnewbies 进入频道。
kernelnewbies 网站还托管了文章、文档和常见问题解答等内容。

* 名称：**linux-kernel 邮件列表存档和搜索引擎**

      :URL: https://subspace.kernel.org
      :URL: https://lore.kernel.org
      :关键词: linux-kernel, 存档, 搜索
:描述: 一些 linux-kernel 邮件列表的存档。如果您有更好或其他的存档，请告诉我。

* 名称：**Linux 基金会 YouTube 频道**

      :URL: https://www.youtube.com/user/thelinuxfoundation
      :关键词: linux, 视频, linux-基金会, youtube
:描述: Linux 基金会上载了他们的协作活动、Linux 会议（包括 LinuxCon）以及其他与 Linux 和软件开发相关的原创研究和内容的视频录像。

---

此文档最初基于：

https://www.dit.upm.es/~jmseyas/linux/kernel/hackers-docs.html

由 Juan-Mariano de Goyeneche 编写。
