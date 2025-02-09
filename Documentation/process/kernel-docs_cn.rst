_Kernel_Docs:

进一步内核文档索引
=====================

对于需要像本文档这样的文件的认识，在linux-kernel邮件列表中变得明显，因为不断有询问信息来源的相同问题反复出现。
幸运的是，随着越来越多的人接触到GNU/Linux，越来越多的人对内核产生了兴趣。但是仅仅阅读源代码往往是不够的。理解代码很容易，但往往会忽略其背后的原理、哲学和设计决策。
不幸的是，对于初学者来说，可利用的文档并不多。
即便存在一些文档，也没有一个“广为人知”的地方来跟踪它们。这些文字试图弥补这一不足。
请注意：如果您知道任何未在此列出的文章或者撰写了新的文档，请按照内核补丁提交流程在此添加引用。任何更正、想法或评论也都是受欢迎的。
所有文档都按以下字段进行编目：文档的“标题”，“作者”/s，可以在其中找到它们的“URL”，在搜索特定主题时有用的“关键词”，以及文档的简短“描述”。
.. note::

   本文档每个部分中的文档是按照发布日期排列的，从最新的到最旧的。维护者应该定期淘汰那些过时或已不再适用的资源；基础书籍除外。
Linux 内核树中的文档
-----------------------------

Sphinx书籍应使用`make {htmldocs | pdfdocs | epubdocs}`构建
* 名称: **linux/Documentation**

      :作者: 多人
:位置: Documentation/
      :关键词: 文本文件, Sphinx
### 文档：随内核源码一同提供的文档，位于Documentation目录中。此文档中的某些页面（包括本页本身）已被移至该位置，并可能比网页版本更为更新。
在线文档
--------

    * **标题：Linux 内核邮件列表词汇表**

      :作者: 多人
      :网址: https://kernelnewbies.org/KernelGlossary
      :日期: 滚动版本
      :关键词: 词汇表、术语、linux-kernel
:描述: 根据介绍：“本词汇表旨在简要描述您在讨论 Linux 内核时可能会听到的一些缩写和术语。”

    * **标题：Linux 内核模块编程指南**

      :作者: 彼得·杰伊·萨尔兹曼、迈克尔·布里安、奥里·波默兰茨、鲍勃·莫特拉姆、黄吉姆
:网址: https://sysprog21.github.io/lkmpg/
      :日期: 2021年
      :关键词: 模块、GPL书籍、/proc、ioctl、系统调用、中断处理程序
:描述: 这是一本关于模块编程的非常好的 GPL 许可书籍。包含大量示例。目前新版正在 https://github.com/sysprog21/lkmpg 积极维护中。

    * **标题：为 Linux 使用 Rust**

      :作者: 多人
      :网址: https://rust-for-linux.com/
      :日期: 滚动版本
      :关键词: 词汇表、术语、linux-kernel
:描述: 根据网站介绍：“为 Linux 使用 Rust 是一个将 Rust 语言添加到 Linux 内核的项目。这个网站旨在作为与该项目相关的链接、文档和资源的中心。”

已出版书籍
----------

    * **标题：实用 Linux 系统管理：安装、配置与管理指南，第一版**

      :作者: 肯尼斯·赫斯
      :出版社: O'Reilly Media
      :日期: 2023年5月
      :页数: 246
      :ISBN: 978-1098109035
      :备注: 系统管理

    * **标题：Linux 内核调试：利用成熟的工具和高级技术有效调试 Linux 内核及内核模块**

      :作者: 凯万·N·比利莫里亚
      :出版社: Packt Publishing Ltd
      :日期: 2022年8月
      :页数: 638
      :ISBN: 978-1801075039
      :备注: 调试书籍

    * **标题：Linux 内核编程：全面指南了解内核内部机制、编写内核模块以及内核同步**

      :作者: 凯万·N·比利莫里亚
      :出版社: Packt Publishing Ltd
      :日期: 2021年3月（第二版于2024年出版）
      :页数: 754
      :ISBN: 978-1789953435（第二版 ISBN 为 978-1803232225）

    * **标题：Linux 内核编程 第二部分 — 字符设备驱动程序与内核同步：创建用户-内核接口、操作外围 I/O 并处理硬件中断**

      :作者: 凯万·N·比利莫里亚
      :出版社: Packt Publishing Ltd
      :日期: 2021年3月
      :页数: 452
      :ISBN: 978-1801079518

    * **标题：Linux 系统编程：直接与内核和 C 库对话**

      :作者: 罗伯特·洛夫
      :出版社: O'Reilly Media
      :日期: 2013年6月
      :页数: 456
      :ISBN: 978-1449339531
      :备注: 基础书籍

    * **标题：Linux 内核开发，第三版**

      :作者: 罗伯特·洛夫
      :出版社: Addison-Wesley
      :日期: 2010年7月
      :页数: 440
      :ISBN: 978-0672329463
      :备注: 基础书籍

.. _ldd3_published:

    * **标题：Linux 设备驱动程序，第三版**

      :作者: 乔纳森·科贝特、阿莱桑德罗·鲁比尼、格雷格·克罗哈-哈特曼
      :出版社: O'Reilly & Associates
      :日期: 2005年
      :页数: 636
      :ISBN: 0-596-00590-3
      :备注: 基础书籍。更多信息参见 http://www.oreilly.com/catalog/linuxdrive3/。PDF格式，网址: https://lwn.net/Kernel/LDD3/

    * **标题：UNIX 操作系统的设计**

      :作者: 摩里斯·J·巴赫
      :出版社: Prentice Hall
      :日期: 1986年
      :页数: 471
      :ISBN: 0-13-201757-1
      :备注: 基础书籍

杂项
--------------

    * **名称：Linux 的交叉引用**

      :网址: https://elixir.bootlin.com/
      :关键词: 浏览源代码
:描述: 另一个基于网络的 Linux 内核源代码浏览器。
包含大量对变量和函数的交叉引用。你可以看到它们在哪里被定义以及在哪里被使用。

* 名称：**Linux Weekly News**

      :网址: https://lwn.net
      :关键词: 最新的内核新闻
:描述: 标题说明了一切。有一个固定的内核版块，总结了开发者的成果、错误修复、新特性以及一周内产生的版本。
* 名称：**Linux-MM 主页**

      :作者: Linux-MM 团队
:网址: https://linux-mm.org/
      :关键词: 内存管理, Linux-MM, mm 补丁, 待办事项, 文档, 邮件列表
:描述: 一个致力于 Linux 内存管理开发的网站
包含与内存相关的补丁、教程、链接以及 mm 开发者等信息……如果你对内存管理开发感兴趣的话，一定不要错过它！

* 名称：**Kernel Newbies IRC 频道及网站**

      :网址: https://www.kernelnewbies.org
      :关键词: IRC, 新手, 频道, 解答疑惑
:描述: 在 irc.oftc.net 上的 #kernelnewbies
#kernelnewbies 是一个专门面向“新手”级别的内核开发者的 IRC 网络。其参与者主要由正在学习内核知识、从事内核项目或希望帮助经验较少的新手内核开发者的职业内核开发者构成。
#kernelnewbies 位于 OFTC IRC 网络上。
