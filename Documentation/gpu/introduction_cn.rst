简介
============

Linux DRM 层包含旨在支持复杂图形设备需求的代码，这些设备通常具有非常适合 3D 图形加速的可编程流水线。内核中的图形驱动程序可以使用 DRM 函数来简化内存管理、中断处理和 DMA 等任务，并为应用程序提供统一的接口。
关于版本：本指南涵盖了 DRM 树中的功能，包括 TTM 内存管理器、输出配置和模式设置，以及新的垂直同步（vblank）内部机制，此外还包括当前内核中常见的所有功能。
[在此插入典型的 DRM 堆栈图]

风格指南
================

为了保持一致性，本文档使用美式英语。缩写全部大写，例如：DRM、KMS、IOCTL、CRTC 等等。为了便于阅读，文档充分利用了 kerneldoc 提供的标记字符：@parameter 用于函数参数，@member 用于结构体成员（在同一结构体内），&struct 用于引用结构体，function() 用于函数。如果存在引用对象的 kerneldoc，则这些都会自动超链接。当引用函数虚表中的条目（以及一般结构体成员）时，请使用 &vtable_name.vfunc。不幸的是，这还不能直接链接到成员，只能链接到结构体。
除非在特殊情况下（将锁定和非锁定变体分开），否则不在 kerneldoc 中记录函数的锁定要求。
相反，应使用 `WARN_ON(!mutex_is_locked(...));` 在运行时检查锁定。由于忽略文档比忽略运行时错误更容易，这样更有价值。而且，当锁定规则改变时，运行时检查需要更新，从而增加它们正确的可能性。在文档中，锁定规则应在相关结构体中解释：要么在锁的注释中说明它保护的内容，要么数据字段需注明哪个锁保护它们，或两者都有。
对于返回值非 `void` 的函数，应有一个名为 "Returns" 的部分，解释不同情况下的预期返回值及其含义。目前还没有一致意见该部分名称是否应全大写，或者是否应以冒号结尾。请遵循文件内的风格。其他常见部分名称有 "Notes"，用于说明危险或棘手的边缘情况，以及 "FIXME"，用于说明接口可能需要清理的地方。
另外，请阅读整个内核文档的 :ref:`指导方针 <doc_guide>`。

kAPI 的文档要求
-----------------------------------

所有导出给其他模块的内核 API 必须进行文档记录，包括其数据结构和至少一个简短的介绍部分来解释总体概念。文档应尽可能地放在代码本身作为 kerneldoc 注释。
不要盲目地记录一切，而只记录对驱动程序作者相关的部分：drm.ko 的内部函数和静态函数不应有正式的 kerneldoc 注释。如果您认为需要注释，请使用普通的 C 注释。您可以在注释中使用 kerneldoc 语法，但不应以 /** kerneldoc 标记开头。对于数据结构也是如此，使用 `/* private: */` 注释标注完全私有的内容，如文档指南所述。
入门指南
===============

欢迎有兴趣帮助开发DRM子系统的开发者们。
通常，人们会提交针对checkpatch或sparse报告的各种问题的补丁。我们非常欢迎这样的贡献。
任何希望更进一步的人可以在 :ref:`TODO列表<todo>` 中找到一系列维护任务。
贡献流程
====================

DRM子系统的工作方式与其他内核子系统大致相同，请参阅 :ref:`主要流程指南和文档<process_index>` 了解具体操作方法。
在这里，我们只记录GPU子系统的一些特殊之处。
特性合并截止日期
-----------------------

所有特性工作必须在当前发布周期的-rc6版本之前进入linux-next树中，否则必须推迟，并且不能进入下一个合并窗口。
所有补丁必须最晚在-rc7之前合并到drm-next树中，但如果您的分支不在linux-next中，则必须在-rc6之前完成。
在此之后只能进行bug修复（如同上游合并窗口关闭后的-rc1版本）。
不允许新的平台支持或新驱动程序的加入。
这意味着大约有一个月的时间窗口，在此期间无法合并特性工作。
推荐的做法是拥有一个始终开放的-next树，但在冻结期内不要将其并入linux-next树中。例如，drm-misc就是这样运作的。
行为准则
---------------

作为freedesktop.org项目的一部分，dri-devel以及DRM社区遵循贡献者公约，详情见：https://www.freedesktop.org/wiki/CodeOfConduct

请在邮件列表、IRC或bug跟踪器上与社区成员互动时保持尊重和文明的态度。
整个社区代表项目的整体形象，任何形式的滥用或欺凌行为都是不可容忍的。
简单的DRM驱动示例
=====================================

DRM子系统包含了许多辅助函数，以简化简单图形设备驱动程序的编写。例如，`drivers/gpu/drm/tiny/`目录中有一组足够简单的驱动程序，可以实现在一个源文件中完成。
这些驱动程序使用了 `struct drm_simple_display_pipe_funcs`，该结构隐藏了DRM子系统的复杂性，并且只需要驱动程序实现一些操作设备所需的基本函数。这可以用于只需要一个全屏扫描缓冲区输出到一个显示设备的情况。小型DRM驱动程序是理解DRM驱动程序应该如何设计的好例子。由于这些驱动程序只有几百行代码，因此它们非常容易阅读。

外部参考
========

首次深入Linux内核子系统可能会是一次令人不知所措的经历，需要熟悉所有概念并了解子系统的内部细节等其他信息。为了降低学习曲线，本节包含了一系列可用于了解DRM/KMS及一般图形知识的演讲和文档列表。有人可能出于多种原因想要深入了解DRM：移植现有的fbdev驱动程序、为新硬件编写DRM驱动程序、修复在处理图形用户空间栈时可能遇到的bug等等。因此，学习材料涵盖了Linux图形栈的许多方面，从内核和用户空间栈的概述到非常具体的主题。以下列表按时间倒序排列，以便将最新的资料放在前面。但所有资料都包含有用的信息，阅读较旧的资料有助于理解DRM子系统变更的背景和理由。

会议演讲
---------

* [《Linux和用户空间图形栈概览》](https://www.youtube.com/watch?v=wjAJmqwg47k) - Paul Kocialkowski (2020)
* [《在Linux上显示像素：内核模式设置简介》](https://www.youtube.com/watch?v=haes4_Xnc5Q) - Simon Ser (2020)
* [《上游图形的精华》](https://www.youtube.com/watch?v=kVzHOgt6WGE) - Daniel Vetter (2019)
* [《Linux DRM子系统简介》](https://www.youtube.com/watch?v=LbDOCJcDRoo) - Maxime Ripard (2017)
* [《拥抱原子（显示）时代》](https://www.youtube.com/watch?v=LjiB_JeDn2M) - Daniel Vetter (2016)
* [《原子KMS驱动程序剖析》](https://www.youtube.com/watch?v=lihqR9sENpc) - Laurent Pinchart (2015)
* [《驱动程序的原子模式设置》](https://www.youtube.com/watch?v=kl9suFgbTc8) - Daniel Vetter (2015)
* [《嵌入式KMS驱动程序剖析》](https://www.youtube.com/watch?v=Ja8fM7rTae4) - Laurent Pinchart (2013)

幻灯片和文章
-------------

* [《Linux图形栈简述，第一部分》](https://lwn.net/Articles/955376/) - Thomas Zimmermann (2023)
* [《Linux图形栈简述，第二部分》](https://lwn.net/Articles/955708/) - Thomas Zimmermann (2023)
* [《理解Linux图形栈》](https://bootlin.com/doc/training/graphics/graphics-slides.pdf) - Bootlin (2022)
* [《DRM KMS概述》](https://wiki.st.com/stm32mpu/wiki/DRM_KMS_overview) - STMicroelectronics (2021)
* [《Linux图形栈》](https://studiopixl.com/2017-05-13/linux-graphic-stack-an-overview) - Nathan Gauër (2017)
* [《原子模式设置设计概述，第一部分》](https://lwn.net/Articles/653071/) - Daniel Vetter (2015)
* [《原子模式设置设计概述，第二部分》](https://lwn.net/Articles/653466/) - Daniel Vetter (2015)
* [《新手视角下的DRM/KMS子系统》](https://bootlin.com/pub/conferences/2014/elce/brezillon-drm-kms/brezillon-drm-kms.pdf) - Boris Brezillon (2014)
* [《Linux图形栈简介》](https://blogs.igalia.com/itoral/2014/07/29/a-brief-introduction-to-the-linux-graphics-stack/) - Iago Toral (2014)
* [《Linux图形栈》](https://blog.mecheye.net/2012/06/the-linux-graphics-stack/) - Jasper St. Pierre (2012)
