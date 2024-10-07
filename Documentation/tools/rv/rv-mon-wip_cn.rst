```plaintext
.. SPDX 许可证标识符: GPL-2.0

==========
rv-mon-wip
==========

----------------------------
抢占式监控中的唤醒
----------------------------

:手册章节: 1

概要
========

**rv mon wip** [*选项*]

描述
===========

抢占式唤醒（**wip**）监控器是一个示例的每 CPU 监控器，用于检查唤醒事件是否总是在禁用抢占的情况下发生。有关此监控器的更多信息，请参阅内核文档：<https://docs.kernel.org/trace/rv/monitor_wip.html>

选项
=======

.. include:: common_ikm.rst

参考
========

**rv**\(1), **rv-mon**\(1)

Linux 内核 *RV* 文档:
<https://www.kernel.org/doc/html/latest/trace/rv/index.html>

作者
======

由 Daniel Bristot de Oliveira 编写 <bristot@kernel.org>

.. include:: common_appendix.rst
```
