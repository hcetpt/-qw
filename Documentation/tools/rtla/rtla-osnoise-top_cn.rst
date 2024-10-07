===================
rtla-osnoise-top
===================

-----------------------------------------------
显示操作系统噪声的摘要信息
-----------------------------------------------

:Manual section: 1

SYNOPSIS
========
**rtla osnoise top** [*OPTIONS*]

DESCRIPTION
===========
.. include:: common_osnoise_description.rst

**rtla osnoise top** 收集来自 *osnoise* 跟踪器的周期性摘要，包括干扰源的发生计数，并以用户友好的格式显示结果。该工具还允许对 *osnoise* 跟踪器进行多种配置并收集跟踪输出。

OPTIONS
=======
.. include:: common_osnoise_options.rst

.. include:: common_top_options.rst

.. include:: common_options.rst

EXAMPLE
=======
在下面的例子中，**rtla osnoise top** 工具设置为以实时优先级 *FIFO:1* 在 CPU *0-3* 上运行，每个周期（默认为 *1s*）运行 *900ms*。减少运行时间的原因是为了避免使 rtla 工具饥饿。该工具还被设置为运行 *一分钟* 并在会话结束时显示报告摘要：

```
[root@f34 ~]# rtla osnoise top -P F:1 -c 0-3 -r 900000 -d 1M -q
                                          操作系统噪声
  duration:   0 00:01:00 | 时间单位为 μs
  CPU Period       Runtime        Noise  % CPU Aval   Max Noise   Max Single          HW          NMI          IRQ      Softirq       Thread
    0 #59         53100000       304896    99.42580        6978           56         549            0        53111         1590           13
    1 #59         53100000       338339    99.36282        8092           24         399            0        53130         1448           31
    2 #59         53100000       290842    99.45227        6582           39         855            0        53110         1406           12
    3 #59         53100000       204935    99.61405        6251           33         290            0        53156         1460           12
```

SEE ALSO
========

**rtla-osnoise**\(1), **rtla-osnoise-hist**\(1)

Osnoise 跟踪器文档: <https://www.kernel.org/doc/html/latest/trace/osnoise-tracer.html>

AUTHOR
======
由 Daniel Bristot de Oliveira 编写 <bristot@kernel.org>

.. include:: common_appendix.rst
