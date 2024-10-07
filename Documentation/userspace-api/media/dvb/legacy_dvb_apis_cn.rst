.. SPDX 许可证标识符: GFDL-1.1-no-invariants-or-later

.. _legacy_dvb_apis:

***************************
废弃的数字电视 API
***************************

此处描述的 API **不应** 在新的驱动程序或应用程序中使用。
DVBv3 前端 API 在处理新的传输系统时存在问题，包括 DVB-S2、DVB-T2、ISDB 等。
.. 注意::

   此处描述的 API 并不一定反映当前代码实现，因为该文档部分是为 DVB 版本 1 编写的，而代码反映了 DVB 版本 3 的实现。
.. toctree::
    :maxdepth: 1

    frontend_legacy_dvbv3_api
    legacy_dvb_decoder_api
