==========
rtla
==========

--------------------------------
实时 Linux 分析工具
--------------------------------

:手册章节: 1

概要
========
**rtla** *COMMAND* [*OPTIONS*]

描述
===========
**rtla** 是一个元工具，包含了一系列命令，旨在分析 Linux 的实时特性。但与将 Linux 当作黑盒测试不同，**rtla** 利用了内核跟踪功能来提供关于特性和意外结果的根本原因的精确信息。

命令
========
**osnoise**

        提供有关操作系统噪声（osnoise）的信息
**timerlat**

        测量中断请求（IRQ）和线程定时器的延迟

选项
=======
**-h**, **--help**

        显示帮助文本
对于其他选项，请参阅相应命令的手册页

另见
========
**rtla-osnoise**\(1), **rtla-timerlat**\(1)

作者
======
Daniel Bristot de Oliveira <bristot@kernel.org>

.. include:: common_appendix.rst
