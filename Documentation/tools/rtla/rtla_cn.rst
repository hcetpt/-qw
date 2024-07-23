实时Linux分析工具手册

=================
rtla
=================

--------------------------
实时Linux分析工具
--------------------------

:手册章节: 1

概要
======
**rtla** *命令* [*选项*]

描述
===========
**rtla**是一个元工具，包含了一系列的命令，旨在分析Linux的实时特性。但与将Linux作为黑盒进行测试不同，**rtla**利用内核追踪功能来提供关于特性和意外结果的根本原因的精确信息。

命令
========
**osnoise**

        提供关于操作系统噪声（osnoise）的信息。
**timerlat**

        测量IRQ和线程定时器延迟。

选项
=======
**-h**, **--help**

        显示帮助文本。
对于其他选项，请参阅相应命令的手册页。

参考
======
**rtla-osnoise**(1), **rtla-timerlat**(1)

作者
======
Daniel Bristot de Oliveira <bristot@kernel.org>

.. include:: common_appendix.rst

注：最后的`.. include:: common_appendix.rst`是reStructuredText中的指令，用于在文档中包含另一个文件的内容，通常用于包含通用的附录或脚注信息，在实际的文本输出中不会直接显示这部分内容。
