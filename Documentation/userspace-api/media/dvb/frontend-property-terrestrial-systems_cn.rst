许可协议标识符：GFDL-1.1-no-invariants-or-later

.. _frontend-property-terrestrial-systems:

***********************************************
用于地面传输系统的属性
***********************************************

.. _dvbt-params:

DVB-T 传输系统
=====================

以下参数适用于 DVB-T：

-  :ref:`DTV_API_VERSION <DTV-API-VERSION>`

-  :ref:`DTV_DELIVERY_SYSTEM <DTV-DELIVERY-SYSTEM>`

-  :ref:`DTV_TUNE <DTV-TUNE>`

-  :ref:`DTV_CLEAR <DTV-CLEAR>`

-  :ref:`DTV_FREQUENCY <DTV-FREQUENCY>`

-  :ref:`DTV_MODULATION <DTV-MODULATION>`

-  :ref:`DTV_BANDWIDTH_HZ <DTV-BANDWIDTH-HZ>`

-  :ref:`DTV_INVERSION <DTV-INVERSION>`

-  :ref:`DTV_CODE_RATE_HP <DTV-CODE-RATE-HP>`

-  :ref:`DTV_CODE_RATE_LP <DTV-CODE-RATE-LP>`

-  :ref:`DTV_GUARD_INTERVAL <DTV-GUARD-INTERVAL>`

-  :ref:`DTV_TRANSMISSION_MODE <DTV-TRANSMISSION-MODE>`

-  :ref:`DTV_HIERARCHY <DTV-HIERARCHY>`

-  :ref:`DTV_LNA <DTV-LNA>`

此外，:ref:`DTV QoS 统计信息 <frontend-stat-properties>` 也适用。

.. _dvbt2-params:

DVB-T2 传输系统
======================

DVB-T2 的支持目前处于早期开发阶段，因此预计这一部分将来会更加详细。以下参数适用于 DVB-T2：

-  :ref:`DTV_API_VERSION <DTV-API-VERSION>`

-  :ref:`DTV_DELIVERY_SYSTEM <DTV-DELIVERY-SYSTEM>`

-  :ref:`DTV_TUNE <DTV-TUNE>`

-  :ref:`DTV_CLEAR <DTV-CLEAR>`

-  :ref:`DTV_FREQUENCY <DTV-FREQUENCY>`

-  :ref:`DTV_MODULATION <DTV-MODULATION>`

-  :ref:`DTV_BANDWIDTH_HZ <DTV-BANDWIDTH-HZ>`

-  :ref:`DTV_INVERSION <DTV-INVERSION>`

-  :ref:`DTV_CODE_RATE_HP <DTV-CODE-RATE-HP>`

-  :ref:`DTV_CODE_RATE_LP <DTV-CODE-RATE-LP>`

-  :ref:`DTV_GUARD_INTERVAL <DTV-GUARD-INTERVAL>`

-  :ref:`DTV_TRANSMISSION_MODE <DTV-TRANSMISSION-MODE>`

-  :ref:`DTV_HIERARCHY <DTV-HIERARCHY>`

-  :ref:`DTV_STREAM_ID <DTV-STREAM-ID>`

-  :ref:`DTV_LNA <DTV-LNA>`

此外，:ref:`DTV QoS 统计信息 <frontend-stat-properties>` 也适用。

.. _isdbt:

ISDB-T 传输系统
======================

这个 ISDB-T/ISDB-Tsb API 扩展应反映所有需要的信息来调谐任何 ISDB-T/ISDB-Tsb 硬件。当然，某些非常复杂的设备可能不需要某些参数即可调谐。这里提供的信息将帮助应用程序编写者了解如何使用 Linux 数字电视 API 处理 ISDB-T 和 ISDB-Tsb 硬件。关于 ISDB-T 和 ISDB-Tsb 的详细信息足以基本展示所需参数值之间的依赖关系，但肯定有一些信息被省略了。对于更详细的信息，请参阅以下文档：

ARIB STD-B31 - “数字地面电视广播传输系统” 和

ARIB TR-B14 - “数字地面电视广播操作指南”

为了理解 ISDB 特定的参数，需要了解 ISDB-T 和 ISDB-Tsb 中的信道结构。例如，读者需要知道 ISDB-T 信道由 13 个段组成，最多可以有 3 层共享这些段等信息。

以下参数适用于 ISDB-T：

-  :ref:`DTV_API_VERSION <DTV-API-VERSION>`

-  :ref:`DTV_DELIVERY_SYSTEM <DTV-DELIVERY-SYSTEM>`

-  :ref:`DTV_TUNE <DTV-TUNE>`

-  :ref:`DTV_CLEAR <DTV-CLEAR>`

-  :ref:`DTV_FREQUENCY <DTV-FREQUENCY>`

-  :ref:`DTV_BANDWIDTH_HZ <DTV-BANDWIDTH-HZ>`

-  :ref:`DTV_INVERSION <DTV-INVERSION>`

-  :ref:`DTV_GUARD_INTERVAL <DTV-GUARD-INTERVAL>`

-  :ref:`DTV_TRANSMISSION_MODE <DTV-TRANSMISSION-MODE>`

-  :ref:`DTV_ISDBT_LAYER_ENABLED <DTV-ISDBT-LAYER-ENABLED>`

-  :ref:`DTV_ISDBT_PARTIAL_RECEPTION <DTV-ISDBT-PARTIAL-RECEPTION>`

-  :ref:`DTV_ISDBT_SOUND_BROADCASTING <DTV-ISDBT-SOUND-BROADCASTING>`

-  :ref:`DTV_ISDBT_SB_SUBCHANNEL_ID <DTV-ISDBT-SB-SUBCHANNEL-ID>`

-  :ref:`DTV_ISDBT_SB_SEGMENT_IDX <DTV-ISDBT-SB-SEGMENT-IDX>`

-  :ref:`DTV_ISDBT_SB_SEGMENT_COUNT <DTV-ISDBT-SB-SEGMENT-COUNT>`

-  :ref:`DTV_ISDBT_LAYERA_FEC <DTV-ISDBT-LAYER-FEC>`

-  :ref:`DTV_ISDBT_LAYERA_MODULATION <DTV-ISDBT-LAYER-MODULATION>`

-  :ref:`DTV_ISDBT_LAYERA_SEGMENT_COUNT <DTV-ISDBT-LAYER-SEGMENT-COUNT>`

-  :ref:`DTV_ISDBT_LAYERA_TIME_INTERLEAVING <DTV-ISDBT-LAYER-TIME-INTERLEAVING>`

-  :ref:`DTV_ISDBT_LAYERB_FEC <DTV-ISDBT-LAYER-FEC>`

-  :ref:`DTV_ISDBT_LAYERB_MODULATION <DTV-ISDBT-LAYER-MODULATION>`

-  :ref:`DTV_ISDBT_LAYERB_SEGMENT_COUNT <DTV-ISDBT-LAYER-SEGMENT-COUNT>`

-  :ref:`DTV_ISDBT_LAYERB_TIME_INTERLEAVING <DTV-ISDBT-LAYER-TIME-INTERLEAVING>`

-  :ref:`DTV_ISDBT_LAYERC_FEC <DTV-ISDBT-LAYER-FEC>`

-  :ref:`DTV_ISDBT_LAYERC_MODULATION <DTV-ISDBT-LAYER-MODULATION>`

-  :ref:`DTV_ISDBT_LAYERC_SEGMENT_COUNT <DTV-ISDBT-LAYER-SEGMENT-COUNT>`

-  :ref:`DTV_ISDBT_LAYERC_TIME_INTERLEAVING <DTV-ISDBT-LAYER-TIME-INTERLEAVING>`

此外，:ref:`DTV QoS 统计信息 <frontend-stat-properties>` 也适用。

.. _atsc-params:

ATSC 传输系统
====================

以下参数适用于 ATSC：

-  :ref:`DTV_API_VERSION <DTV-API-VERSION>`

-  :ref:`DTV_DELIVERY_SYSTEM <DTV-DELIVERY-SYSTEM>`

-  :ref:`DTV_TUNE <DTV-TUNE>`

-  :ref:`DTV_CLEAR <DTV-CLEAR>`

-  :ref:`DTV_FREQUENCY <DTV-FREQUENCY>`

-  :ref:`DTV_MODULATION <DTV-MODULATION>`

-  :ref:`DTV_BANDWIDTH_HZ <DTV-BANDWIDTH-HZ>`

此外，:ref:`DTV QoS 统计信息 <frontend-stat-properties>` 也适用。

.. _atscmh-params:

ATSC-MH 传输系统
=======================

以下参数适用于 ATSC-MH：

-  :ref:`DTV_API_VERSION <DTV-API-VERSION>`

-  :ref:`DTV_DELIVERY_SYSTEM <DTV-DELIVERY-SYSTEM>`

-  :ref:`DTV_TUNE <DTV-TUNE>`

-  :ref:`DTV_CLEAR <DTV-CLEAR>`

-  :ref:`DTV_FREQUENCY <DTV-FREQUENCY>`

-  :ref:`DTV_BANDWIDTH_HZ <DTV-BANDWIDTH-HZ>`

-  :ref:`DTV_ATSCMH_FIC_VER <DTV-ATSCMH-FIC-VER>`

-  :ref:`DTV_ATSCMH_PARADE_ID <DTV-ATSCMH-PARADE-ID>`

-  :ref:`DTV_ATSCMH_NOG <DTV-ATSCMH-NOG>`

-  :ref:`DTV_ATSCMH_TNOG <DTV-ATSCMH-TNOG>`

-  :ref:`DTV_ATSCMH_SGN <DTV-ATSCMH-SGN>`

-  :ref:`DTV_ATSCMH_PRC <DTV-ATSCMH-PRC>`

-  :ref:`DTV_ATSCMH_RS_FRAME_MODE <DTV-ATSCMH-RS-FRAME-MODE>`

-  :ref:`DTV_ATSCMH_RS_FRAME_ENSEMBLE <DTV-ATSCMH-RS-FRAME-ENSEMBLE>`

-  :ref:`DTV_ATSCMH_RS_CODE_MODE_PRI <DTV-ATSCMH-RS-CODE-MODE-PRI>`

-  :ref:`DTV_ATSCMH_RS_CODE_MODE_SEC <DTV-ATSCMH-RS-CODE-MODE-SEC>`

-  :ref:`DTV_ATSCMH_SCCC_BLOCK_MODE <DTV-ATSCMH-SCCC-BLOCK-MODE>`

-  :ref:`DTV_ATSCMH_SCCC_CODE_MODE_A <DTV-ATSCMH-SCCC-CODE-MODE-A>`

-  :ref:`DTV_ATSCMH_SCCC_CODE_MODE_B <DTV-ATSCMH-SCCC-CODE-MODE-B>`

-  :ref:`DTV_ATSCMH_SCCC_CODE_MODE_C <DTV-ATSCMH-SCCC-CODE-MODE-C>`

-  :ref:`DTV_ATSCMH_SCCC_CODE_MODE_D <DTV-ATSCMH-SCCC-CODE-MODE-D>`

此外，:ref:`DTV QoS 统计信息 <frontend-stat-properties>` 也适用。
.. _dtmb-参数:

DTMB传输系统
============

以下参数适用于DTMB：

-  :ref:`DTV_API_VERSION <DTV-API-版本>`

-  :ref:`DTV_DELIVERY_SYSTEM <DTV-传输系统>`

-  :ref:`DTV_TUNE <DTV-调谐>`

-  :ref:`DTV_CLEAR <DTV-清除>`

-  :ref:`DTV_FREQUENCY <DTV-频率>`

-  :ref:`DTV_MODULATION <DTV-调制方式>`

-  :ref:`DTV_BANDWIDTH_HZ <DTV-带宽-Hz>`

-  :ref:`DTV_INVERSION <DTV-倒置>`

-  :ref:`DTV_INNER_FEC <DTV-内部FEC>`

-  :ref:`DTV_GUARD_INTERVAL <DTV-保护间隔>`

-  :ref:`DTV_TRANSMISSION_MODE <DTV-传输模式>`

-  :ref:`DTV_INTERLEAVING <DTV-交织>`

-  :ref:`DTV_LNA <DTV-LNA>`

此外，:ref:`DTV QoS统计信息 <前端统计属性>` 也是有效的。
