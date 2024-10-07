.. SPDX 许可证标识符: GFDL-1.1 或之后版本无不变部分
.. c:namespace:: CEC

.. _CEC_ADAP_G_CAPS:

**************************
ioctl CEC_ADAP_G_CAPS
**************************

名称
====

CEC_ADAP_G_CAPS - 查询设备功能

概要
========

.. c:macro:: CEC_ADAP_G_CAPS

``int ioctl(int fd, CEC_ADAP_G_CAPS, struct cec_caps *argp)``

参数
=========

``fd``
    由 :c:func:`open()` 返回的文件描述符
``argp``

描述
===========

所有 CEC 设备必须支持 :ref:`ioctl CEC_ADAP_G_CAPS <CEC_ADAP_G_CAPS>`。为了查询设备信息，应用程序调用 ioctl 并传入一个指向 :c:type:`cec_caps` 结构体的指针。驱动程序填充该结构体并将信息返回给应用程序。ioctl 永远不会失败。
.. tabularcolumns:: |p{1.2cm}|p{2.5cm}|p{13.6cm}|

.. c:type:: cec_caps

.. flat-table:: struct cec_caps
    :header-rows:  0
    :stub-columns: 0
    :widths:       1 1 16

    * - char
      - ``driver[32]``
      - CEC 适配器驱动程序的名称
* - char
      - ``name[32]``
      - 此 CEC 适配器的名称。组合 ``driver`` 和 ``name`` 必须是唯一的
* - __u32
      - ``available_log_addrs``
      - 可以配置的最大逻辑地址数
* - __u32
      - ``capabilities``
      - CEC 适配器的功能，请参阅 :ref:`cec-capabilities`
* - __u32
      - ``version``
      - CEC 框架 API 版本，使用 ``KERNEL_VERSION()`` 宏格式化
.. tabularcolumns:: |p{4.4cm}|p{2.5cm}|p{10.4cm}|

.. _cec-capabilities:

.. flat-table:: CEC 功能标志
    :header-rows:  0
    :stub-columns: 0
    :widths:       3 1 8

    * .. _`CEC-CAP-PHYS-ADDR`:

      - ``CEC_CAP_PHYS_ADDR``
      - 0x00000001
      - 用户空间必须通过调用 :ref:`ioctl CEC_ADAP_S_PHYS_ADDR <CEC_ADAP_S_PHYS_ADDR>` 来配置物理地址。如果未设置此功能，则在设置 EDID（对于 HDMI 接收器）或读取 EDID（对于 HDMI 发射器）时，内核将处理物理地址的设置
* .. _`CEC-CAP-LOG-ADDRS`:

      - ``CEC_CAP_LOG_ADDRS``
      - 0x00000002
      - 用户空间必须通过调用 :ref:`ioctl CEC_ADAP_S_LOG_ADDRS <CEC_ADAP_S_LOG_ADDRS>` 来配置逻辑地址。如果未设置此功能，则内核将负责配置这些地址
* .. _`CEC-CAP-TRANSMIT`:

      - ``CEC_CAP_TRANSMIT``
      - 0x00000004
      - 用户空间可以通过调用 :ref:`ioctl CEC_TRANSMIT <CEC_TRANSMIT>` 发送 CEC 消息。这意味着用户空间也可以成为跟随者，因为能够发送消息是成为跟随者的前提条件。如果未设置此功能，则内核将处理所有的 CEC 发送并处理接收到的所有 CEC 消息
* .. _`CEC-CAP-PASSTHROUGH`:

      - ``CEC_CAP_PASSTHROUGH``
      - 0x00000008
      - 用户空间可以通过调用 :ref:`ioctl CEC_S_MODE <CEC_S_MODE>` 使用直通模式

* .. _`CEC-CAP-RC`:

      - ``CEC_CAP_RC``
      - 0x00000010
      - 此适配器支持遥控协议

* .. _`CEC-CAP-MONITOR-ALL`:

      - ``CEC_CAP_MONITOR_ALL``
      - 0x00000020
      - CEC 硬件可以监控所有消息，而不仅仅是定向和广播消息

* .. _`CEC-CAP-NEEDS-HPD`:

      - ``CEC_CAP_NEEDS_HPD``
      - 0x00000040
      - 只有在 HDMI 热插拔检测引脚为高电平时，CEC 硬件才处于活动状态。这使得无法使用 CEC 唤醒那些在待机模式下将 HPD 引脚设为低电平但保持 CEC 总线活跃的显示器

* .. _`CEC-CAP-MONITOR-PIN`:

      - ``CEC_CAP_MONITOR_PIN``
      - 0x00000080
      - CEC 硬件可以监控 CEC 引脚从低电压到高电压以及相反的变化。当处于引脚监控模式时，应用程序会收到 ``CEC_EVENT_PIN_CEC_LOW`` 和 ``CEC_EVENT_PIN_CEC_HIGH`` 事件

* .. _`CEC-CAP-CONNECTOR-INFO`:

      - ``CEC_CAP_CONNECTOR_INFO``
      - 0x00000100
      - 如果设置了此功能，则可以使用 :ref:`CEC_ADAP_G_CONNECTOR_INFO`

返回值
======

成功时返回 0，错误时返回 -1 并且设置 ``errno`` 变量。通用错误代码在 :ref:`通用错误代码 <gen-errors>` 章节中描述。
