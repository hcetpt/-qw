.. SPDX 许可证标识符: GFDL-1.1-no-invariants-or-later

.. _fe_property_parameters:

*******************************
数字电视属性参数
*******************************

有几种不同的数字电视参数可以用于 :ref:`FE_SET_PROPERTY 和 FE_GET_PROPERTY 的 ioctl 操作 <FE_GET_PROPERTY>`
本节将描述其中的每一个。请注意，仅需要它们中的一部分来设置前端。
.. _DTV-UNDEFINED:

DTV_UNDEFINED
=============

内部使用。对此进行 GET/SET 操作不会更改或返回任何内容。
.. _DTV-TUNE:

DTV_TUNE
========

解释数据缓存，构建一个传统的前端调谐请求，以便我们可以通过 ``FE_SET_FRONTEND`` ioctl 中的验证。
.. _DTV-CLEAR:

DTV_CLEAR
=========

重置与前端相关的数据缓存。这不会影响硬件。
.. _DTV-FREQUENCY:

DTV_FREQUENCY
=============

数字电视转发器/频道的频率。

.. note::

  1. 对于卫星传输系统，频率以千赫兹 (kHz) 为单位。
  2. 对于有线和地面传输系统，频率以赫兹 (Hz) 为单位。
  3. 在大多数传输系统中，频率是转发器/频道的中心频率。ISDB-T 是例外，其主载波与中心频率有 1/7 的偏移。
  4. 对于 ISDB-T，频道通常以约 143 千赫兹的偏移进行传输。例如，一个有效的频率可能是 474,143 千赫兹。步进与频道带宽相关，通常是 6 兆赫兹。
#. 在 ISDB-Tsb 中，频道仅由一个或三个片段组成，频率步长分别为 429kHz 和 3 * 429kHz。
.. _DTV-MODULATION:

DTV_MODULATION
==============

指定了支持多种调制方式的前端传输系统的调制类型。
调制类型可以是枚举类型 :c:type:`fe_modulation` 中定义的任何一种类型。
大多数数字电视标准都提供了多种可能的调制类型。
下表总结了每个传输系统所支持的调制类型，根据当前规范定义：
======================= =======================================================
标准		调制类型
======================= =======================================================
ATSC（版本 1）	8-VSB 和 16-VSB
DMTB			4-QAM、16-QAM、32-QAM、64-QAM 和 4-QAM-NR
DVB-C 附录 A/C	16-QAM、32-QAM、64-QAM 和 256-QAM
DVB-C 附录 B	64-QAM
DVB-C2			QPSK、16-QAM、64-QAM、256-QAM、1024-QAM 和 4096-QAM
======================= =======================================================
DVB-T			QPSK、16-QAM 和 64-QAM
DVB-T2			QPSK、16-QAM、64-QAM 和 256-QAM
DVB-S			无需设置。仅支持 QPSK
DVB-S2			QPSK、8-PSK、16-APSK 和 32-APSK
DVB-S2X			8-APSK-L、16-APSK-L、32-APSK-L、64-APSK 和 64-APSK-L
ISDB-T			QPSK、DQPSK、16-QAM 和 64-QAM
ISDB-S			8-PSK、QPSK 和 BPSK
======================= =======================================================

.. note::

   由于 DVB-S2X 规定了对 DVB-S2 标准的扩展，因此使用相同的传输系统枚举值（SYS_DVBS2）。
请注意，上述一些调制类型可能目前尚未在内核中定义。原因是简单的：还没有驱动程序需要这样的定义。
.. _DTV-BANDWIDTH-HZ:

DTV_BANDWIDTH_HZ
================

频道的带宽，以赫兹（HZ）为单位
仅适用于地面传输系统
可选值：``1712000``，``5000000``，``6000000``，``7000000``，
``8000000``，``10000000``

======================= =======================================================
地面标准                可选的带宽值
======================= =======================================================
ATSC（版本1）           无需设置。始终为6MHz
DMTB                    无需设置。始终为8MHz
DVB-T                  6MHz、7MHz和8MHz
DVB-T2                 1.172 MHz、5MHz、6MHz、7MHz、8MHz和10MHz
ISDB-T                 5MHz、6MHz、7MHz和8MHz，尽管大多数地方使用6MHz
======================= =======================================================

.. 注意::

  1. 对于ISDB-Tsb，带宽可以根据连接的段数变化
     可以从其他参数轻松得出
     （DTV_ISDBT_SB_SEGMENT_IDX, DTV_ISDBT_SB_SEGMENT_COUNT）
  2. 在卫星和有线传输系统中，带宽取决于符号率。因此，内核将忽略任何
     :ref:`DTV-BANDWIDTH-HZ` 设置。但是，它会根据估计的带宽重新填充该值
     这种带宽估计考虑了通过 :ref:`DTV-SYMBOL-RATE` 设置的符号率以及滚降因子，
     其中滚降因子对于DVB-C和DVB-S是固定的
对于DVB-S2，滚降系数也应通过 :ref:`DTV-ROLLOFF` 设置。
.. _DTV-INVERSION:

DTV_INVERSION
=============

指定前端是否进行频谱反转。
可接受的值由 :c:type:`fe_spectral_inversion` 定义。
.. _DTV-DISEQC-MASTER:

DTV_DISEQC_MASTER
=================

当前未实现。
.. _DTV-SYMBOL-RATE:

DTV_SYMBOL_RATE
===============

用于有线和卫星传输系统。
数字电视符号率，单位为波特（符号/秒）。
.. _DTV-INNER-FEC:

DTV_INNER_FEC
=============

用于有线和卫星传输系统。
可接受的值由 :c:type:`fe_code_rate` 定义。
.. _DTV-VOLTAGE:

DTV_VOLTAGE
===========

用于卫星传输系统。
电压通常与非DiSEqC兼容的LNB一起使用来切换极化（水平/垂直）。当使用DiSEqC设备时，此电压必须与DiSEqC命令一致地切换，具体描述参见DiSEqC规范。
可接受的值由 :c:type:`fe_sec_voltage` 定义。

.. _DTV-TONE:

DTV_TONE
========

当前未使用
.. _DTV-PILOT:

DTV_PILOT
=========

用于 DVB-S2
设置 DVB-S2 的导频信号
可接受的值由 :c:type:`fe_pilot` 定义
.. _DTV-ROLLOFF:

DTV_ROLLOFF
===========

用于 DVB-S2
设置 DVB-S2 的滚降系数
可接受的值由 :c:type:`fe_rolloff` 定义
.. _DTV-DISEQC-SLAVE-REPLY:

DTV_DISEQC_SLAVE_REPLY
======================

当前未实现
.. _DTV-FE-CAPABILITY-COUNT:

DTV_FE_CAPABILITY_COUNT
=======================

当前未实现
.. _DTV-FE-CAPABILITY:

DTV_FE_CAPABILITY
=================

当前未实现

.. _DTV-DELIVERY-SYSTEM:

DTV_DELIVERY_SYSTEM
===================

指定传输系统的类型
可接受的值由 :c:type:`fe_delivery_system` 定义

.. _DTV-ISDBT-PARTIAL-RECEPTION:

DTV_ISDBT_PARTIAL_RECEPTION
===========================

仅在 ISDB 中使用
如果 ``DTV_ISDBT_SOUND_BROADCASTING`` 的值为 '0'，则此位字段表示该频道是否处于部分接收模式
如果值为 '1'，则 ``DTV_ISDBT_LAYERA_*`` 值被分配到中心段，并且 ``DTV_ISDBT_LAYERA_SEGMENT_COUNT`` 必须为 '1'
此外，如果 ``DTV_ISDBT_SOUND_BROADCASTING`` 的值也为 '1'，则 ``DTV_ISDBT_PARTIAL_RECEPTION`` 表示此 ISDB-Tsb 频道是否由一个段和一层或三个段和两层组成
可能的值：0, 1, -1（AUTO）

.. _DTV-ISDBT-SOUND-BROADCASTING:

DTV_ISDBT_SOUND_BROADCASTING
============================

仅在 ISDB 中使用
此字段表示其他 DTV_ISDBT_* 参数是针对 ISDB-T 还是 ISDB-Tsb 频道。（参见 ``DTV_ISDBT_PARTIAL_RECEPTION``）
可能的值：0, 1, -1（AUTO）

.. _DTV-ISDBT-SB-SUBCHANNEL-ID:

DTV_ISDBT_SB_SUBCHANNEL_ID
==========================

仅在 ISDB 中使用
此字段仅在 `DTV_ISDBT_SOUND_BROADCASTING` 设置为 '1' 时适用。
（作者注：以下对 `SUBCHANNEL-ID` 的描述可能并非完全准确，但这是我理解的技术背景，对于编程设备来说是必要的。）

ISDB-Tsb 信道（1 或 3 段）可以单独广播或以一组相连的 ISDB-Tsb 信道的形式广播。在这个信道组中，每个信道都可以独立接收。相连的 ISDB-Tsb 段的数量可能会有所不同，例如根据可用的频谱带宽。
示例：假设广播了 8 个相连的 ISDB-Tsb 段。广播商有多种方式将这些信道广播出去：
假设是一个标准的 13 段 ISDB-T 频谱，他可以从位置 1-8 或 5-13 等位置排列这 8 段。

段的基础层是子信道：每个段由若干具有预定义 ID 的子信道组成。子信道用于帮助解调器同步信道。
ISDB-T 信道始终位于所有子信道的中心。在 ISDB-Tsb 中，情况不再那么简单。
`DTV_ISDBT_SB_SUBCHANNEL_ID` 参数用于指定要解调的段的子信道 ID。
可能的值：0 .. 41, -1 (AUTO)

.. _DTV-ISDBT-SB-SEGMENT-IDX:

DTV_ISDBT_SB_SEGMENT_IDX
========================

仅适用于 ISDB
此字段仅在 `DTV_ISDBT_SOUND_BROADCASTING` 设置为 '1' 时适用。
`DTV_ISDBT_SB_SEGMENT_IDX` 给出了一个 ISDB-Tsb 信道中的多个段被相连传输时需要解调的段索引。
可能的值：0 .. `DTV_ISDBT_SB_SEGMENT_COUNT` - 1

注意：此值无法通过自动频道搜索确定。
.. _DTV-ISDBT-SB-SEGMENT-COUNT:

DTV_ISDBT_SB_SEGMENT_COUNT
==========================

仅在 ISDB 中使用
此字段仅在 ``DTV_ISDBT_SOUND_BROADCASTING`` 设置为 '1' 时适用
``DTV_ISDBT_SB_SEGMENT_COUNT`` 给出了连接的 ISDB-Tsb 信道总数
可能的值：1 到 13

注意：此值无法通过自动频道搜索确定
.. _isdb-hierq-layers:

DTV-ISDBT-LAYER[A-C] 参数
===============================

仅在 ISDB 中使用
ISDB-T 信道可以进行分层编码。与 DVB-T 不同，ISDB-T 的分层可以在解码过程中同时解码。因此，ISDB-T 解调器具有 3 个维特比（Viterbi）解码器和 3 个里德-所罗门（Reed-Solomon）解码器。ISDB-T 具有 3 个分层，每个分层都可以使用一部分可用的段。所有分层的总段数必须是 13。
存在 3 组参数，分别对应于 A 层、B 层和 C 层。
.. _DTV-ISDBT-LAYER-ENABLED:

DTV_ISDBT_LAYER_ENABLED
-----------------------

仅在 ISDB 中使用
在 ISDB-T 中，通过在解码过程中启用或禁用分层来实现分层接收。将 ``DTV_ISDBT_LAYER_ENABLED`` 的所有位设置为 '1' 会强制解调所有分层（如果适用）。这是默认设置。
如果信道处于部分接收模式（`DTV_ISDBT_PARTIAL_RECEPTION` = 1），则中央段可以独立于其他12个段进行解码。在这种模式下，层A必须有一个`SEGMENT_COUNT`值为1。
在ISDB-Tsb中仅使用层A，其值可以是1或3，具体取决于`DTV_ISDBT_PARTIAL_RECEPTION`。`SEGMENT_COUNT`必须相应地填充。
只使用前3位的值，其他位将被忽略：

`DTV_ISDBT_LAYER_ENABLED` 第0位：启用层A

`DTV_ISDBT_LAYER_ENABLED` 第1位：启用层B

`DTV_ISDBT_LAYER_ENABLED` 第2位：启用层C

`DTV_ISDBT_LAYER_ENABLED` 第3到31位：未使用

.. _DTV-ISDBT-LAYER-FEC:

DTV_ISDBT_LAYER[A-C]_FEC
------------------------

仅用于ISDB
由给定ISDB层使用的前向纠错机制，如:c:type:`fe_code_rate`所定义
可能的值包括：`FEC_AUTO`、`FEC_1_2`、`FEC_2_3`、`FEC_3_4`、`FEC_5_6`、`FEC_7_8`

.. _DTV-ISDBT-LAYER-MODULATION:

DTV_ISDBT_LAYER[A-C]_MODULATION
-------------------------------

仅用于ISDB
由给定ISDB层使用的调制方式，如:c:type:`fe_modulation`所定义
可能的值包括：`QAM_AUTO`、`QPSK`、`QAM_16`、`QAM_64`、`DQPSK`

.. note::

   1. 如果层C为`DQPSK`，则层B也必须为`DQPSK`
   2. 如果层B为`DQPSK`且`DTV_ISDBT_PARTIAL_RECEPTION`=0，则层A也必须为`DQPSK`

.. _DTV-ISDBT-LAYER-SEGMENT-COUNT:

DTV_ISDBT_LAYER[A-C]_SEGMENT_COUNT
----------------------------------

仅用于ISDB
可能的值：0、1、2、3、4、5、6、7、8、9、10、11、12、13、-1（AUTO）

注意：`DTV_ISDBT_SOUND_BROADCASTING`、`DTV_ISDBT_PARTIAL_RECEPTION`和`LAYER[A-C]_SEGMENT_COUNT`的真值表

.. _isdbt-layer_seg-cnt-table:

.. flat-table:: ISDB-T音频广播的真值表
    :header-rows:  1
    :stub-columns: 0


    -  .. 行1

       -  部分接收

       -  音频广播

       -  层A宽度

       -  层B宽度

       -  层C宽度

       -  总宽度

    -  .. 行2

       -  0

       -  0

       -  1 ~ 13

       -  1 ~ 13

       -  1 ~ 13

       -  13

    -  .. 行3

       -  1

       -  0

       -  1

       -  1 ~ 13

       -  1 ~ 13

       -  13

    -  .. 行4

       -  0

       -  1

       -  1

       -  0

       -  0

       -  1

    -  .. 行5

       -  1

       -  1

       -  1

       -  2

       -  0

       -  13

.. _DTV-ISDBT-LAYER-TIME-INTERLEAVING:

DTV_ISDBT_LAYER[A-C]_TIME_INTERLEAVING
--------------------------------------

仅用于ISDB
有效值：0、1、2、4、-1（AUTO）

当 DTV_ISDBT_SOUND_BROADCASTING 生效时，值 8 也是有效的。
注意：实际的交织长度取决于模式（FFT 大小）。
这里的值指的是 TMCC 结构中的内容，如下表所示。

.. c:type:: isdbt_layer_interleaving_table

.. flat-table:: ISDB-T 时间交织模式
    :header-rows:  1
    :stub-columns: 0

    -  .. row 1

       -  ``DTV_ISDBT_LAYER[A-C]_TIME_INTERLEAVING``

       -  模式 1（2K FFT）

       -  模式 2（4K FFT）

       -  模式 3（8K FFT）

    -  .. row 2

       -  0

       -  0

       -  0

       -  0

    -  .. row 3

       -  1

       -  4

       -  2

       -  1

    -  .. row 4

       -  2

       -  8

       -  4

       -  2

    -  .. row 5

       -  4

       -  16

       -  8

       -  4

.. _DTV-ATSCMH-FIC-VER:

DTV_ATSCMH_FIC_VER
------------------

仅用于 ATSC-MH
FIC（快速信息信道）信号数据的版本号
FIC 用于传递信息以使接收器能够快速获取服务
可能的值：0、1、2、3、...、30、31

.. _DTV-ATSCMH-PARADE-ID:

DTV_ATSCMH_PARADE_ID
--------------------

仅用于 ATSC-MH
Parade 标识号

一个 Parade 是最多包含八个 MH 组的集合，传输一个或两个 Ensemble
可能的值：0、1、2、3、...、126、127

.. _DTV-ATSCMH-NOG:

DTV_ATSCMH_NOG
--------------

仅用于 ATSC-MH
指定 Parade 中每个 MH 子帧的 MH 组数
可能的值：1，2，3，4，5，6，7，8

.. _DTV-ATSCMH-TNOG:

DTV_ATSCMH_TNOG
---------------

仅在ATSC-MH中使用
一个MH子帧中包含的所有MH组的数量，包括属于所有MH游行的所有MH组
可能的值：0，1，2，3，...，30，31


.. _DTV-ATSCMH-SGN:

DTV_ATSCMH_SGN
--------------

仅在ATSC-MH中使用
起始组号
可能的值：0，1，2，3，...，14，15


.. _DTV-ATSCMH-PRC:

DTV_ATSCMH_PRC
--------------

仅在ATSC-MH中使用
游行重复周期
可能的值：1，2，3，4，5，6，7，8


.. _DTV-ATSCMH-RS-FRAME-MODE:

DTV_ATSCMH_RS_FRAME_MODE
------------------------

仅在ATSC-MH中使用
里德-所罗门（Reed Solomon，RS）帧模式
可接受的值由:c:type:`atscmh_rs_frame_mode`定义

.. _DTV-ATSCMH-RS-FRAME-ENSEMBLE:

DTV_ATSCMH_RS_FRAME_ENSEMBLE
----------------------------

仅在ATSC-MH中使用
Reed Solomon (RS) 帧集合
可接受的值由 `atscmh_rs_frame_ensemble` 类型定义

.. _DTV-ATSCMH-RS-CODE-MODE-PRI:

DTV_ATSCMH_RS_CODE_MODE_PRI
---------------------------

仅在 ATSC-MH 中使用
Reed Solomon (RS) 编码模式（主）
可接受的值由 `atscmh_rs_code_mode` 类型定义

.. _DTV-ATSCMH-RS-CODE-MODE-SEC:

DTV_ATSCMH_RS_CODE_MODE_SEC
---------------------------

仅在 ATSC-MH 中使用
Reed Solomon (RS) 编码模式（次）
可接受的值由 `atscmh_rs_code_mode` 类型定义

.. _DTV-ATSCMH-SCCC-BLOCK-MODE:

DTV_ATSCMH_SCCC_BLOCK_MODE
--------------------------

仅在 ATSC-MH 中使用
级联卷积码块模式
可接受的值由 :c:type:`atscmh_sccc_block_mode` 定义。

.. _DTV-ATSCMH-SCCC-CODE-MODE-A:

DTV_ATSCMH_SCCC_CODE_MODE_A
---------------------------

仅用于 ATSC-MH
级联卷积码率
可接受的值由 :c:type:`atscmh_sccc_code_mode` 定义。

.. _DTV-ATSCMH-SCCC-CODE-MODE-B:

DTV_ATSCMH_SCCC_CODE_MODE_B
---------------------------

仅用于 ATSC-MH
级联卷积码率
可能的值与枚举中记录的一致
:c:type:`atscmh_sccc_code_mode`

.. _DTV-ATSCMH-SCCC-CODE-MODE-C:

DTV_ATSCMH_SCCC_CODE_MODE_C
---------------------------

仅用于 ATSC-MH
级联卷积码率
可能的值与枚举中记录的一致
:c:type:`atscmh_sccc_code_mode`
.. _DTV-ATSCMH-SCCC-CODE-MODE-D:

DTV_ATSCMH_SCCC_CODE_MODE_D
---------------------------

仅在 ATSC-MH 中使用  
级联卷积码率  
可能的值与枚举类型 `atscmh_sccc_code_mode` 文档中定义的相同

.. _DTV-API-VERSION:

DTV_API_VERSION
===============

返回数字电视 API 的主版本和次版本号

.. _DTV-CODE-RATE-HP:

DTV_CODE_RATE_HP
================

用于地面传输  
可接受的值由 `fe_transmit_mode` 类型定义

.. _DTV-CODE-RATE-LP:

DTV_CODE_RATE_LP
================

用于地面传输  
可接受的值由 `fe_transmit_mode` 类型定义

.. _DTV-GUARD-INTERVAL:

DTV_GUARD_INTERVAL
==================

可接受的值由 `fe_guard_interval` 类型定义

.. note::

   1. 如果将 ``DTV_GUARD_INTERVAL`` 设置为 ``GUARD_INTERVAL_AUTO``，硬件将尝试找到正确的保护间隔（如果具备此能力），并使用 TMCC 填充缺失的参数。
   2. 保护间隔 ``GUARD_INTERVAL_1_64`` 仅用于 DVB-C2。
#. 间隔 ``GUARD_INTERVAL_1_128`` 用于 DVB-C2 和 DVB-T2
#. 间隔 ``GUARD_INTERVAL_19_128`` 和 ``GUARD_INTERVAL_19_256`` 仅用于 DVB-T2
#. 间隔 ``GUARD_INTERVAL_PN420``、``GUARD_INTERVAL_PN595`` 和 ``GUARD_INTERVAL_PN945`` 目前仅用于 DMTB
在该标准中，只有这些间隔和 ``GUARD_INTERVAL_AUTO`` 是有效的

.. _DTV-TRANSMISSION-MODE:

DTV_TRANSMISSION_MODE
=====================

仅在基于 OFDM 的标准（如 DVB-T/T2、ISDB-T、DTMB）中使用  
指定了标准所使用的 FFT 大小（即载波数量的近似值）
可接受的值由 :c:type:`fe_transmit_mode` 定义
.. note::

   #. ISDB-T 支持三种载波/符号大小：8K、4K、2K。在该标准中称为 **模式**，编号为 1 到 3：

      ====	========	========================
      模式	FFT 大小	传输模式
      ====	========	========================
      1		2K		``TRANSMISSION_MODE_2K``
      2		4K		``TRANSMISSION_MODE_4K``
      3		8K		``TRANSMISSION_MODE_8K``
      ====	========	========================

   #. 如果将 ``DTV_TRANSMISSION_MODE`` 设置为 ``TRANSMISSION_MODE_AUTO``，硬件将尝试找到正确的 FFT 大小（如果具备能力），并使用 TMCC 填充缺失的参数
#. DVB-T 规定 2K 和 8K 为有效大小
#. DVB-T2 规定 1K、2K、4K、8K、16K 和 32K 为有效大小
#. DTMB 指定 C1 和 C3780

.. _DTV-HIERARCHY:

DTV_HIERARCHY
=============

仅在 DVB-T 和 DVB-T2 中使用
前端层次结构
可接受的值由 :c:type:`fe_hierarchy` 定义
.. _DTV-STREAM-ID:

DTV_STREAM_ID
=============

在 DVB-C2、DVB-S2、DVB-T2 和 ISDB-S 中使用
DVB-C2、DVB-S2、DVB-T2 和 ISDB-S 支持在一个传输流中传输多个流。此属性使数字电视驱动程序能够在硬件支持的情况下处理子流过滤。
默认情况下，子流过滤是禁用的。
对于 DVB-C2、DVB-S2 和 DVB-T2，有效的子流 ID 范围是从 0 到 255。
对于 ISDB，有效的子流 ID 范围是从 1 到 65535。
要禁用它，应使用特殊宏 NO_STREAM_ID_FILTER。
注意：任何超出ID范围的值也会禁用过滤
.. _DTV-DVBT2-PLP-ID-LEGACY:

DTV_DVBT2_PLP_ID_LEGACY
=======================

已过时，已被DTV_STREAM_ID取代
.. _DTV-ENUM-DELSYS:

DTV_ENUM_DELSYS
===============

一个多标准前端需要提供传输系统信息。应用程序在使用前端的其他操作之前，必须枚举所提供的传输系统。在此功能引入之前，使用FE_GET_INFO来确定前端类型。如果一个前端提供了多个传输系统，FE_GET_INFO帮助不大。打算使用多标准前端的应用程序必须枚举与之关联的传输系统，而不是尝试使用FE_GET_INFO。对于传统前端，结果与FE_GET_INFO相同，但格式更为规范。

可接受的值由:c:type:`fe_delivery_system`定义
.. _DTV-INTERLEAVING:

DTV_INTERLEAVING
================

要使用的时间交织方式
可接受的值由:c:type:`fe_interleaving`定义
.. _DTV-LNA:

DTV_LNA
=======

低噪声放大器
硬件可能提供可控的LNA，可以使用该参数手动设置。通常LNA仅在地面设备中找到（如果有的话）
可能的值：0、1、LNA_AUTO

0，LNA关闭

1，LNA开启

使用特殊宏LNA_AUTO设置LNA自动模式
.. _DTV-SCRAMBLING-SEQUENCE-INDEX:

DTV_SCRAMBLING_SEQUENCE_INDEX
=============================

用于DVB-S2
当存在时，这个18位字段携带了DVB-S2物理层加扰序列索引，如EN 302 307第5.5.4条所定义
没有明确的方法将加扰序列索引传送给接收机。如果S2卫星传输系统描述符可用，则可以用来读取加扰序列索引（EN 300 468表41）
默认情况下，使用黄金扰码序列索引 0
有效的扰码序列索引范围是从 0 到 262142
