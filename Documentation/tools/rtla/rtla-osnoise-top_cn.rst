===================
rtla-osnoise-top
===================
-------------------------------------------------
显示操作系统噪声的汇总信息
-------------------------------------------------

:手册章节: 1

概要
======
**rtla osnoise top** [*选项*]

描述
======
**rtla osnoise top** 收集来自 *osnoise* 追踪器的周期性汇总，包括干扰源发生的计数器，并以用户友好的格式展示结果。该工具还允许对 *osnoise* 追踪器进行多种配置以及追踪输出的收集。

选项
======
.. include:: common_osnoise_options.rst

.. include:: common_top_options.rst

.. include:: common_options.rst

示例
======
在下面的例子中，**rtla osnoise top** 工具被设置为使用实时优先级 *FIFO:1*，在CPU *0-3* 上运行，每个周期 (*1秒* 默认) 的运行时间为 *900毫秒*。减少运行时间的原因是避免使 rtla 工具饿死。工具也被设定为运行 *一分钟* 并在会话结束时显示报告的总结::

  [root@f34 ~]# rtla osnoise top -P F:1 -c 0-3 -r 900000 -d 1M -q
                                          操作系统噪声
  持续时间:   0 00:01:00 | 时间单位为微秒
  CPU 周期       运行时间        噪声  % CPU 可用   最大噪声   单次最大         硬件         NMI         中断     软中断       线程
    0 #59         53100000       304896    99.42580        6978           56         549            0        53111         1590           13
    1 #59         53100000       338339    99.36282        8092           24         399            0        53130         1448           31
    2 #59         53100000       290842    99.45227        6582           39         855            0        53110         1406           12
    3 #59         53100000       204935    99.61405        6251           33         290            0        53156         1460           12

参考
======

**rtla-osnoise**\(1), **rtla-osnoise-hist**\(1)

Osnoise 追踪器文档: <https://www.kernel.org/doc/html/latest/trace/osnoise-tracer.html>

作者
======
由 Daniel Bristot de Oliveira <bristot@kernel.org> 编写

.. include:: common_appendix.rst
```
