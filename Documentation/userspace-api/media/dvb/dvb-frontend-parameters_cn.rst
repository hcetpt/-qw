SPDX 许可证标识符: GFDL-1.1-no-invariants-or-later

.. c:type:: dvb_frontend_parameters

**************************
前端参数
**************************

传递给前端设备的参数类型取决于您使用的硬件类型。结构 ``dvb_frontend_parameters`` 使用了特定于系统的参数联合。然而，随着新的传输系统需要更多的数据，原有的结构大小不足以容纳这些数据，并且仅仅扩展其大小会破坏现有的应用程序。因此，这些参数被替换为使用 :ref:`FE_GET_PROPERTY/FE_SET_PROPERTY <FE_GET_PROPERTY>` ioctl 的方法。新 API 足够灵活，可以向现有的传输系统添加新参数，并支持新的传输系统。因此，新的应用程序应使用 :ref:`FE_GET_PROPERTY/FE_SET_PROPERTY <FE_GET_PROPERTY>` 来支持更新的传输系统，如 DVB-S2、DVB-T2、DVB-C2、ISDB 等。

所有类型的参数都作为联合包含在 ``dvb_frontend_parameters`` 结构中：

.. code-block:: c

    struct dvb_frontend_parameters {
        uint32_t frequency;     /* QAM/OFDM 的绝对频率（赫兹），QPSK 的中频（千赫兹）*/
        fe_spectral_inversion_t inversion;
        union {
            struct dvb_qpsk_parameters qpsk;
            struct dvb_qam_parameters  qam;
            struct dvb_ofdm_parameters ofdm;
            struct dvb_vsb_parameters  vsb;
        } u;
    };

对于 QPSK 前端，“frequency” 字段指定了中频，即实际加到低噪声块（LNB）本振频率（LOF）上的偏移量。中频以千赫兹为单位。对于 QAM 和 OFDM 前端，“frequency” 指定的是绝对频率，并以赫兹为单位。

.. c:type:: dvb_qpsk_parameters

QPSK 参数
=========

对于卫星 QPSK 前端，您需要使用 ``dvb_qpsk_parameters`` 结构：

.. code-block:: c

     struct dvb_qpsk_parameters {
         uint32_t        symbol_rate;  /* 符号率（每秒符号数）*/
         fe_code_rate_t  fec_inner;    /* 前向纠错（参见上文）*/
     };

.. c:type:: dvb_qam_parameters

QAM 参数
========

对于有线 QAM 前端，您需要使用 ``dvb_qam_parameters`` 结构：

.. code-block:: c

     struct dvb_qam_parameters {
         uint32_t         symbol_rate; /* 符号率（每秒符号数）*/
         fe_code_rate_t   fec_inner;   /* 前向纠错（参见上文）*/
         fe_modulation_t  modulation;  /* 调制类型（参见上文）*/
     };

.. c:type:: dvb_vsb_parameters

VSB 参数
========

ATSC 前端由 ``dvb_vsb_parameters`` 结构支持：

.. code-block:: c

    struct dvb_vsb_parameters {
        fe_modulation_t modulation; /* 调制类型（参见上文）*/
    };

.. c:type:: dvb_ofdm_parameters

OFDM 参数
=========

DVB-T 前端由 ``dvb_ofdm_parameters`` 结构支持：

.. code-block:: c

     struct dvb_ofdm_parameters {
         fe_bandwidth_t      bandwidth;
         fe_code_rate_t      code_rate_HP;  /* 高优先级流编码率 */
         fe_code_rate_t      code_rate_LP;  /* 低优先级流编码率 */
         fe_modulation_t     constellation; /* 调制类型（参见上文）*/
         fe_transmit_mode_t  transmission_mode;
         fe_guard_interval_t guard_interval;
         fe_hierarchy_t      hierarchy_information;
     };
