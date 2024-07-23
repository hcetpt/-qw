===================
rtla-osnoise-hist
===================
------------------------------------------------------
显示osnoise追踪器样本的直方图
------------------------------------------------------

:手册章节: 1

概要
========
**rtla osnoise hist** [*选项*]

描述
===========
.. include:: common_osnoise_description.rst

**rtla osnoise hist**工具将所有**osnoise:sample_threshold**的发生收集到一个直方图中，以用户友好的方式展示结果。该工具还允许对*osnoise*追踪器进行多种配置以及追踪输出的收集。
选项
=======
.. include:: common_osnoise_options.rst

.. include:: common_hist_options.rst

.. include:: common_options.rst

示例
=======
在下面的示例中，设置*osnoise*追踪器线程以实时优先级*FIFO:1*运行，在CPU*0-11*上，每个周期(*默认为1s*)运行*900ms*。减少运行时间的原因是避免*rtla*工具被饿死。工具也被设置为运行*一分钟*。输出直方图被设置为按*10us*和*25*条目分组::

  [root@f34 ~/]# rtla osnoise hist -P F:1 -c 0-11 -r 900000 -d 1M -b 10 -E 25
  # RTLA osnoise 直方图
  # 时间单位是微秒(us)
  # 持续时间:   0 00:01:00
  索引   CPU-000   CPU-001   CPU-002   CPU-003   CPU-004   CPU-005   CPU-006   CPU-007   CPU-008   CPU-009   CPU-010   CPU-011
  0         42982     46287     51779     53740     52024     44817     49898     36500     50408     50128     49523     52377
  10        12224      8356      2912       878      2667     10155      4573     18894      4214      4836      5708      2413
  20            8         5        12         2        13        24        20        41        29        53        39        39
  30            1         1         0         0        10         3         6        19        15        31        30        38
  40            0         0         0         0         0         4         2         7         2         3         8        11
  50            0         0         0         0         0         0         0         0         0         1         1         2
  超过:         0         0         0         0         0         0         0         0         0         0         0         0
  计数:    55215     54649     54703     54620     54714     55003     54499     55461     54668     55052     55309     54880
  最小值:       0         0         0         0         0         0         0         0         0         0         0         0
  平均值:       0         0         0         0         0         0         0         0         0         0         0         0
  最大值:        30        30        20        20        30        40        40        40        40        50        50        50

参考
========
**rtla-osnoise**\(1), **rtla-osnoise-top**\(1)

*osnoise*追踪器文档: <https://www.kernel.org/doc/html/latest/trace/osnoise-tracer.html>

作者
======
由Daniel Bristot de Oliveira编写 <bristot@kernel.org>

.. include:: common_appendix.rst
