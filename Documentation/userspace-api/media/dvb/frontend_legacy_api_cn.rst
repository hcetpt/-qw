.. SPDX 许可证标识符: GFDL-1.1-no-invariants-or-later

.. _frontend_legacy_types:

前端遗留数据类型
==========================

.. toctree::
    :maxdepth: 1

    fe-type-t
    fe-bandwidth-t
    dvb-frontend-parameters
    dvb-frontend-event

.. _frontend_legacy_fcalls:

前端遗留函数调用
==============================

这些函数定义于 DVB 版本 3。内核中保留了对它们的支持，仅为了兼容性问题。强烈不建议使用这些函数。

.. toctree::
    :maxdepth: 1

    fe-read-ber
    fe-read-snr
    fe-read-signal-strength
    fe-read-uncorrected-blocks
    fe-set-frontend
    fe-get-frontend
    fe-get-event
    fe-dishnetwork-send-legacy-cmd
