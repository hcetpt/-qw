.. SPDX 许可证标识符: GFDL-1.1-no-invariants-or-later

.. _dvb_demux:

##############################
数字电视解复用设备
##############################

数字电视解复用设备控制数字电视的 MPEG-TS 过滤器。如果驱动程序和硬件支持，这些过滤器将在硬件上实现。否则，内核提供软件仿真。
它可以通过 ``/dev/adapter?/demux?`` 访问。数据类型和 ioctl 定义可以通过在应用程序中包含 ``linux/dvb/dmx.h`` 来访问。

.. toctree::
    :maxdepth: 1

    dmx_types
    dmx_fcalls
