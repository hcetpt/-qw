SPDX 许可声明标识符: GFDL-1.1-no-invariants-or-later
.. c:namespace:: CEC

.. _CEC_DQEVENT:

*****************
ioctl CEC_DQEVENT
*****************

名称
====

CEC_DQEVENT - 取消队列中的 CEC 事件

概述
========

.. c:macro:: CEC_DQEVENT

``int ioctl(int fd, CEC_DQEVENT, struct cec_event *argp)``

参数
=========

``fd``
    由 :c:func:`open()` 返回的文件描述符
``argp``

描述
===========

CEC 设备可以发送异步事件。这些事件可以通过调用 :c:func:`CEC_DQEVENT` 获取。如果文件描述符处于非阻塞模式且没有待处理的事件，则返回 -1 并将 errno 设置为 ``EAGAIN`` 错误码。
内部事件队列是按文件句柄和按事件类型划分的。如果队列中没有更多空间，则最后的事件将被新的事件覆盖。这意味着中间结果可能会被丢弃，但最新的事件始终可用。这也意味着有可能读取两个连续的具有相同值的事件（例如两个 :ref:`CEC_EVENT_STATE_CHANGE <CEC-EVENT-STATE-CHANGE>` 事件具有相同的状态）。在这种情况下，中间的状态变化丢失了，但可以保证在这两个事件之间状态确实发生了变化。

.. tabularcolumns:: |p{1.2cm}|p{2.9cm}|p{13.2cm}|

.. c:type:: cec_event_state_change

.. flat-table:: struct cec_event_state_change
    :header-rows:  0
    :stub-columns: 0
    :widths:       1 1 8

    * - __u16
      - ``phys_addr``
      - 当前物理地址。如果没有有效的物理地址设置，则为 ``CEC_PHYS_ADDR_INVALID``
    * - __u16
      - ``log_addr_mask``
      - 当前声称的逻辑地址集合。如果没有声称任何逻辑地址或 ``phys_addr`` 是 ``CEC_PHYS_ADDR_INVALID``，则为 0
        如果位 15 被设置（``1 << CEC_LOG_ADDR_UNREGISTERED``），则表示该设备具有未注册的逻辑地址。在这种情况下，其他所有位都为 0
    * - __u16
      - ``have_conn_info``
      - 如果非零，则表示 HDMI 连接器信息可用
        该字段仅在设置了 ``CEC_CAP_CONNECTOR_INFO`` 的情况下有效。如果该功能已设置且 ``have_conn_info`` 为零，则表示 HDMI 连接器设备尚未实例化，原因可能是 HDMI 驱动程序仍在配置设备，或者 HDMI 设备已被解绑

.. c:type:: cec_event_lost_msgs

.. tabularcolumns:: |p{1.0cm}|p{2.0cm}|p{14.3cm}|

.. flat-table:: struct cec_event_lost_msgs
    :header-rows:  0
    :stub-columns: 0
    :widths:       1 1 16

    * - __u32
      - ``lost_msgs``
      - 设置为自文件句柄打开以来或上次为此文件句柄取消队列此事件以来丢失的消息数量
        丢失的消息是最旧的消息。因此，当有新消息到达且没有更多空间时，最旧的消息将被丢弃以腾出空间给新消息。消息队列的内部大小保证存储过去两秒内收到的所有消息。根据 CEC 规范，消息应在一秒内回复，因此这是足够的。
```markdown
.. tabularcolumns:: |p{1.0cm}|p{4.4cm}|p{2.5cm}|p{9.2cm}|

.. c:type:: cec_event

.. flat-table:: struct cec_event
    :header-rows:  0
    :stub-columns: 0
    :widths:       1 1 8

    * - __u64
      - ``ts``
      - 事件的时间戳（纳秒）
时间戳取自 ``CLOCK_MONOTONIC`` 时钟
从用户空间访问相同的时钟，请使用 :c:func:`clock_gettime`
* - __u32
      - ``event``
      - CEC 事件类型，参见 :ref:`cec-events`
* - __u32
      - ``flags``
      - 事件标志，参见 :ref:`cec-event-flags`
* - union {
      - (匿名)
    * - struct cec_event_state_change
      - ``state_change``
      - 新的适配器状态，由 :ref:`CEC_EVENT_STATE_CHANGE <CEC-EVENT-STATE-CHANGE>` 事件发送
* - struct cec_event_lost_msgs
      - ``lost_msgs``
      - 丢失的消息数量，由 :ref:`CEC_EVENT_LOST_MSGS <CEC-EVENT-LOST-MSGS>` 事件发送
* - }
      -

.. tabularcolumns:: |p{5.6cm}|p{0.9cm}|p{10.8cm}|

.. _cec-events:

.. flat-table:: CEC 事件类型
    :header-rows:  0
    :stub-columns: 0
    :widths:       3 1 16

    * .. _`CEC-EVENT-STATE-CHANGE`:

      - ``CEC_EVENT_STATE_CHANGE``
      - 1
      - 当 CEC 适配器的状态发生变化时生成。当调用 open() 时，会为该文件句柄生成一个初始事件，包含当前时刻的 CEC 适配器状态
* .. _`CEC-EVENT-LOST-MSGS`:

      - ``CEC_EVENT_LOST_MSGS``
      - 2
      - 如果由于应用程序未能及时处理 CEC 消息而导致一个或多个 CEC 消息丢失时生成
* .. _`CEC-EVENT-PIN-CEC-LOW`:

      - ``CEC_EVENT_PIN_CEC_LOW``
      - 3
      - 当 CEC 引脚电压从高电平变为低电平时生成
```
仅适用于设置了 ``CEC_CAP_MONITOR_PIN`` 功能的适配器
* .. _`CEC-EVENT-PIN-CEC-HIGH`:

      - ``CEC_EVENT_PIN_CEC_HIGH``
      - 4
      - 当 CEC 引脚从低电压变为高电压时生成
仅适用于设置了 ``CEC_CAP_MONITOR_PIN`` 功能的适配器
* .. _`CEC-EVENT-PIN-HPD-LOW`:

      - ``CEC_EVENT_PIN_HPD_LOW``
      - 5
      - 当 HPD 引脚从高电压变为低电压时生成
仅适用于设置了 ``CEC_CAP_MONITOR_PIN`` 功能的适配器。当调用 open() 时，可以读取 HPD 引脚，并且如果 HPD 为低电平，则会为该文件句柄生成初始事件
* .. _`CEC-EVENT-PIN-HPD-HIGH`:

      - ``CEC_EVENT_PIN_HPD_HIGH``
      - 6
      - 当 HPD 引脚从低电压变为高电压时生成
仅适用于设置了 ``CEC_CAP_MONITOR_PIN`` 功能的适配器。当调用 open() 时，可以读取 HPD 引脚，并且如果 HPD 为高电平，则会为该文件句柄生成初始事件
* .. _`CEC-EVENT-PIN-5V-LOW`:

      - ``CEC_EVENT_PIN_5V_LOW``
      - 6
      - 当 5V 引脚从高电压变为低电压时生成
仅适用于设置了 ``CEC_CAP_MONITOR_PIN`` 功能的适配器。当调用 open() 时，可以读取 5V 引脚，并且如果 5V 为低电平，则会为该文件句柄生成初始事件
* .. _`CEC-EVENT-PIN-5V-HIGH`:

      - ``CEC_EVENT_PIN_5V_HIGH``
      - 7
      - 当 5V 引脚从低电压变为高电压时生成
仅适用于设置了 ``CEC_CAP_MONITOR_PIN`` 功能的适配器。当调用 open() 时，可以读取 5V 引脚，并且如果 5V 为高电平，则会为该文件句柄生成初始事件。

.. tabularcolumns:: |p{6.0cm}|p{0.6cm}|p{10.7cm}|

.. _cec-event-flags:

.. flat-table:: CEC 事件标志
    :header-rows:  0
    :stub-columns: 0
    :widths:       3 1 8

    * .. _`CEC-EVENT-FL-INITIAL-STATE`:

      - ``CEC_EVENT_FL_INITIAL_STATE``
      - 1
      - 在设备打开时生成的初始事件将设置此标志。参见上表以了解哪些事件会这样做。这允许应用程序在 open() 时了解 CEC 适配器的初始状态。
* .. _`CEC-EVENT-FL-DROPPED-EVENTS`:

      - ``CEC_EVENT_FL_DROPPED_EVENTS``
      - 2
      - 如果丢弃了一个或多个指定类型的事件，则设置此标志。这是应用程序无法跟上的指示。

返回值
======

成功时返回 0，出错时返回 -1 并且 ``errno`` 变量会被适当设置。通用错误代码在 :ref:`通用错误代码 <gen-errors>` 章节中描述。

:ref:`ioctl CEC_DQEVENT <CEC_DQEVENT>` 可能返回以下错误代码：

EAGAIN
    当文件句柄处于非阻塞模式且没有待处理事件时返回此错误。
ERESTARTSYS
    在阻塞模式下等待事件到达时，中断（例如 Ctrl-C）到达。
