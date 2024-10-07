.. SPDX 许可证标识符: GFDL-1.1-no-invariants-or-later

.. _frontend-stat-properties:

*******************************
前端统计指标
*******************************

这些值通过 ``dtv_property.stat`` 返回。如果支持该属性，则 ``dtv_property.stat.len`` 大于零。
对于大多数传输系统，如果支持统计信息，``dtv_property.stat.len`` 将为 1，并且每个参数将返回一个值。
然而，需要注意的是，新的 OFDM 传输系统（如 ISDB）可以为每组载波使用不同的调制类型。在这种标准下，最多可以提供三组统计数据，并且 ``dtv_property.stat.len`` 会更新以反映“全局”度量，再加上每个载波组（在 ISDB 中称为“层”）的一个度量。
为了与其他传输系统保持一致，:c:type:`dtv_property.stat.dtv_stats <dtv_stats>` 数组中的第一个值指的是全局度量。数组的其他元素代表每一层，从层 A（索引 1），层 B（索引 2）等开始。
填充的元素数量存储在 ``dtv_property.stat.len`` 中。
``dtv_property.stat.dtv_stats`` 数组中的每个元素包含两个部分：

-  ``svalue`` 或 ``uvalue``，其中 ``svalue`` 是用于测量值的有符号值（分贝测量），而 ``uvalue`` 是用于无符号值（计数器、相对比例）

-  ``scale`` - 值的比例尺。它可以是：

   -  ``FE_SCALE_NOT_AVAILABLE`` - 前端支持该参数，但无法收集到该参数（可能是暂时性或永久性条件）

   -  ``FE_SCALE_DECIBEL`` - 参数是有符号值，以 1/1000 分贝为单位

   -  ``FE_SCALE_RELATIVE`` - 参数是无符号值，其中 0 表示 0%，65535 表示 100%

-  ``FE_SCALE_COUNTER`` - 参数是一个无符号值，用于计数事件的发生次数，例如比特错误、块错误或经过的时间

.. _DTV-STAT-SIGNAL-STRENGTH:

DTV_STAT_SIGNAL_STRENGTH
========================

指示调谐器或解调器模拟部分的信号强度水平。
此度量可能的比例尺如下：

-  ``FE_SCALE_NOT_AVAILABLE`` - 测量失败或测量尚未完成
-  ``FE_SCALE_DECIBEL`` - 信号强度以 0.001 分贝毫瓦（dBm）为单位，功率以毫瓦为单位。此值通常为负数
``FE_SCALE_RELATIVE`` - 前端提供了一个从 0% 到 100% 的功率测量值（实际上是从 0 到 65535）

.. _DTV-STAT-CNR:

DTV_STAT_CNR
============

指示主载波的信噪比
此指标可能的刻度包括：

-  ``FE_SCALE_NOT_AVAILABLE`` - 测量失败，或者测量尚未完成
-  ``FE_SCALE_DECIBEL`` - 信噪比以 0.001 分贝为单位
-  ``FE_SCALE_RELATIVE`` - 前端提供了一个从 0% 到 100% 的信噪比测量值（实际上是从 0 到 65535）

.. _DTV-STAT-PRE-ERROR-BIT-COUNT:

DTV_STAT_PRE_ERROR_BIT_COUNT
============================

测量在内码块中前向纠错（FEC）之前的比特错误数量（即在维特比、LDPC 或其他内码之前）
此测量与 ``DTV_STAT_PRE_TOTAL_BIT_COUNT`` 在同一时间间隔内进行
为了获得比特误码率（BER）测量值，应将其除以 :ref:`DTV_STAT_PRE_TOTAL_BIT_COUNT <DTV-STAT-PRE-TOTAL-BIT-COUNT>`
此测量值是单调递增的，随着前端获取更多的比特计数。当调谐到一个新频道或转发器时，前端可能会重置该测量值
此指标可能的刻度包括：

-  ``FE_SCALE_NOT_AVAILABLE`` - 测量失败，或者测量尚未完成
``FE_SCALE_COUNTER`` - 在内部编码前计数的错误位数
.. _DTV-STAT-PRE-TOTAL-BIT-COUNT:

DTV_STAT_PRE_TOTAL_BIT_COUNT
============================

测量在相同时间段内，在内部码块之前接收到的位数，同时记录
:ref:`DTV_STAT_PRE_ERROR_BIT_COUNT <DTV-STAT-PRE-ERROR-BIT-COUNT>`
的测量值。
需要注意的是，此测量值可能小于传输流中的总位数，因为前端可能需要手动重启测量，在每次测量间隔期间丢失一些数据。
此测量值是单调递增的，随着前端获取更多的位计数测量。当调谐频道/转发器时，前端可能会重置此测量值。
此指标可能的尺度有：

-  ``FE_SCALE_NOT_AVAILABLE`` - 测量失败或测量尚未完成
-  ``FE_SCALE_COUNTER`` - 在测量
   :ref:`DTV_STAT_PRE_ERROR_BIT_COUNT <DTV-STAT-PRE-ERROR-BIT-COUNT>` 时计数的位数
.. _DTV-STAT-POST-ERROR-BIT-COUNT:

DTV_STAT_POST_ERROR_BIT_COUNT
=============================

测量经过内部码块（Viterbi、LDPC 或其他内部码）完成前向纠错（FEC）后的位错误数。
此测量是在与 ``DTV_STAT_POST_TOTAL_BIT_COUNT`` 相同的时间段内进行的。
为了得到误码率（BER）测量值，应该将其除以
:ref:`DTV_STAT_POST_TOTAL_BIT_COUNT <DTV-STAT-POST-TOTAL-BIT-COUNT>`。
此测量值是单调递增的，随着前端获取更多的位计数测量。当调谐频道/转发器时，前端可能会重置此测量值。
此度量的可能尺度如下：

-  ``FE_SCALE_NOT_AVAILABLE`` —— 测量失败，或者测量尚未完成
-  ``FE_SCALE_COUNTER`` —— 内码之后计数的错误位数
.. _DTV-STAT-POST-TOTAL-BIT-COUNT:

DTV_STAT_POST_TOTAL_BIT_COUNT
=============================

在与 :ref:`DTV_STAT_POST_ERROR_BIT_COUNT <DTV-STAT-POST-ERROR-BIT-COUNT>` 测量相同的周期内，测量经过内码后的接收比特数。
需要注意的是，此测量值可能小于传输流中的总比特数，因为前端可能需要手动重启测量，导致每次测量间隔期间丢失一些数据。
随着前端获取更多的比特计数测量值，此测量值单调增加。当调谐到某个频道/转发器时，前端可能会重置该值。
此度量的可能尺度如下：

-  ``FE_SCALE_NOT_AVAILABLE`` —— 测量失败，或者测量尚未完成
-  ``FE_SCALE_COUNTER`` —— 在测量 :ref:`DTV_STAT_POST_ERROR_BIT_COUNT <DTV-STAT-POST-ERROR-BIT-COUNT>` 时计数的比特数
.. _DTV-STAT-ERROR-BLOCK-COUNT:

DTV_STAT_ERROR_BLOCK_COUNT
==========================

测量在外向纠错编码（如里德-所罗门编码或其他外码）之后的块错误数量。
随着前端获取更多的比特计数测量值，此测量值单调增加。当调谐到某个频道/转发器时，前端可能会重置该值。
此度量的可能尺度如下：

-  ``FE_SCALE_NOT_AVAILABLE`` —— 测量失败，或者测量尚未完成
``FE_SCALE_COUNTER`` - 在外码之后计数的错误块数量

.. _DTV-STAT-TOTAL-BLOCK-COUNT:

DTV-STAT_TOTAL_BLOCK_COUNT
==========================

在进行 :ref:`DTV_STAT_ERROR_BLOCK_COUNT <DTV-STAT-ERROR-BLOCK-COUNT>` 测量的同一时间段内，测量接收到的总块数。
它可以用来通过将 :ref:`DTV_STAT_ERROR_BLOCK_COUNT <DTV-STAT-ERROR-BLOCK-COUNT>` 除以 :ref:`DTV-STAT-TOTAL-BLOCK-COUNT` 来计算 PER 指标。
此指标可能的尺度有：

-  ``FE_SCALE_NOT_AVAILABLE`` - 测量失败或测量尚未完成
-  ``FE_SCALE_COUNTER`` - 在测量 :ref:`DTV_STAT_ERROR_BLOCK_COUNT <DTV-STAT-ERROR-BLOCK-COUNT>` 时计数的块数量
