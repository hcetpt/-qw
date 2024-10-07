.. SPDX 许可证标识符: GFDL-1.1-no-invariants-or-later

*************
前端类型
*************

由于历史原因，前端类型的命名基于传输中使用的调制类型。前端类型由 `fe_type_t` 类型定义：

.. c:type:: fe_type

.. tabularcolumns:: |p{6.6cm}|p{2.2cm}|p{8.5cm}|

.. flat-table:: 前端类型
    :header-rows:  1
    :stub-columns: 0
    :widths:       3 1 4

    -  .. row 1

       -  fe_type

       -  描述

       -  :ref:`DTV_DELIVERY_SYSTEM <DTV-DELIVERY-SYSTEM>` 等效类型

    -  .. row 2

       -  .. _FE-QPSK:

          ``FE_QPSK``

       -  用于 DVB-S 标准

       -  ``SYS_DVBS``

    -  .. row 3

       -  .. _FE-QAM:

          ``FE_QAM``

       -  用于 DVB-C 附录 A 标准

       -  ``SYS_DVBC_ANNEX_A``

    -  .. row 4

       -  .. _FE-OFDM:

          ``FE_OFDM``

       -  用于 DVB-T 标准

       -  ``SYS_DVBT``

    -  .. row 5

       -  .. _FE-ATSC:

          ``FE_ATSC``

       -  用于 ATSC 标准（地面）或在美国使用的 DVB-C 附录 B（有线）

       -  ``SYS_ATSC``（地面）或 ``SYS_DVBC_ANNEX_B``（有线）

较新的格式如 DVB-S2、ISDB-T、ISDB-S 和 DVB-T2 没有在上面列出，因为它们是通过新的 :ref:`FE_GET_PROPERTY/FE_GET_SET_PROPERTY <FE_GET_PROPERTY>` ioctl 使用 :ref:`DTV_DELIVERY_SYSTEM <DTV-DELIVERY-SYSTEM>` 参数来支持的。

在过去，结构体 :c:type:`dvb_frontend_info` 中包含一个 `fe_type_t` 字段来指示传输系统，该字段被填充为 `FE_QPSK`、`FE_QAM`、`FE_OFDM` 或 `FE_ATSC`。虽然为了保持向后兼容性仍然会填充这个字段，但该字段的使用已被弃用，因为它只能报告一个传输系统，而有些设备支持多个传输系统。请改用 :ref:`DTV_ENUM_DELSYS <DTV-ENUM-DELSYS>`。

对于支持多个传输系统的设备，结构体 :c:type:`dvb_frontend_info` 的 `fe_type_t` 字段会被填充为当前选定的标准，该标准由最后一次调用 :ref:`FE_SET_PROPERTY <FE_GET_PROPERTY>` 时使用的 :ref:`DTV_DELIVERY_SYSTEM <DTV-DELIVERY-SYSTEM>` 属性确定。
