```
SPDX 许可证标识符: GFDL-1.1-no-invariants-or-later

.. _dvb_frontend:

#######################
数字电视前端 API
#######################

数字电视前端 API 被设计来支持三类传输系统：地面、有线和卫星。目前，支持的传输系统包括：

- 地面系统：DVB-T, DVB-T2, ATSC, ATSC M/H, ISDB-T, DVB-H, DTMB, CMMB
- 有线系统：DVB-C 附录 A/C, ClearQAM (DVB-C 附录 B)
- 卫星系统：DVB-S, DVB-S2, DVB Turbo, ISDB-S, DSS

数字电视前端控制多个子设备，包括：

- 调谐器
- 数字电视解调器
- 低噪声放大器（LNA）
- 卫星设备控制（SEC）[#f1]_

前端可以通过 `/dev/dvb/adapter?/frontend?` 访问。
数据类型和 ioctl 定义可以通过在应用程序中包含 `linux/dvb/frontend.h` 来访问。

.. note::

   通过互联网传输（DVB-IP）和 MMT（MPEG 媒体传输）尚未由该 API 处理，但未来可能会扩展。

.. [#f1]

   在卫星系统中，API 对卫星设备控制（SEC）的支持允许进行电源控制，并发送/接收信号以控制天线子系统，选择极化方式并选择低噪声块转换馈源喇叭（LNBf）的中间频率（IF）。它支持 DiSEqC 和 V-SEC 协议。DiSEqC（数字 SEC）规范可在 `Eutelsat <http://www.eutelsat.com/satellites/4_5_5.html>`__ 获取。

.. toctree::
    :maxdepth: 1

    query-dvb-frontend-info
    dvb-fe-read-status
    dvbproperty
    frontend_fcalls
```
