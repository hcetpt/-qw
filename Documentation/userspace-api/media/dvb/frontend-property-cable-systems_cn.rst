SPDX 许可证标识符: GFDL-1.1-no-invariants-or-later

.. _frontend-property-cable-systems:

**************************************************
用于电缆传输系统的属性
**************************************************

.. _dvbc-params:

DVB-C 传输系统
==============

DVB-C 附录 A 是广泛使用的电缆标准。传输使用 QAM 调制。
DVB-C 附录 C 专为 6 MHz 设计，并在日本使用。它支持附录 A 中一部分调制类型，并且滚降系数为 0.13，而不是 0.15。

以下参数适用于 DVB-C 附录 A/C：

-  :ref:`DTV_API_VERSION <DTV-API-VERSION>`

-  :ref:`DTV_DELIVERY_SYSTEM <DTV-DELIVERY-SYSTEM>`

-  :ref:`DTV_TUNE <DTV-TUNE>`

-  :ref:`DTV_CLEAR <DTV-CLEAR>`

-  :ref:`DTV_FREQUENCY <DTV-FREQUENCY>`

-  :ref:`DTV_MODULATION <DTV-MODULATION>`

-  :ref:`DTV_INVERSION <DTV-INVERSION>`

-  :ref:`DTV_SYMBOL_RATE <DTV-SYMBOL-RATE>`

-  :ref:`DTV_INNER_FEC <DTV-INNER-FEC>`

-  :ref:`DTV_LNA <DTV-LNA>`

此外，:ref:`DTV QoS 统计数据 <frontend-stat-properties>` 也适用。

.. _dvbc-annex-b-params:

DVB-C 附录 B 传输系统
============================

DVB-C 附录 B 只在少数国家（如美国）使用。以下参数适用于 DVB-C 附录 B：

-  :ref:`DTV_API_VERSION <DTV-API-VERSION>`

-  :ref:`DTV_DELIVERY_SYSTEM <DTV-DELIVERY-SYSTEM>`

-  :ref:`DTV_TUNE <DTV-TUNE>`

-  :ref:`DTV_CLEAR <DTV-CLEAR>`

-  :ref:`DTV_FREQUENCY <DTV-FREQUENCY>`

-  :ref:`DTV_MODULATION <DTV-MODULATION>`

-  :ref:`DTV_INVERSION <DTV-INVERSION>`

-  :ref:`DTV_LNA <DTV-LNA>`

此外，:ref:`DTV QoS 统计数据 <frontend-stat-properties>` 也适用。
