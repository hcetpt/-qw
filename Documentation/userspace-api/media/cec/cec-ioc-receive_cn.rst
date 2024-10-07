SPDX 许可证标识符: GFDL-1.1-no-invariants-or-later
.. c:namespace:: CEC

.. _CEC_TRANSMIT:
.. _CEC_RECEIVE:

***********************************
ioctl 命令 CEC_RECEIVE 和 CEC_TRANSMIT
***********************************

名称
====

CEC_RECEIVE, CEC_TRANSMIT - 接收或发送一个 CEC 消息

概要
========

.. c:macro:: CEC_RECEIVE

``int ioctl(int fd, CEC_RECEIVE, struct cec_msg *argp)``

.. c:macro:: CEC_TRANSMIT

``int ioctl(int fd, CEC_TRANSMIT, struct cec_msg *argp)``

参数
=========

``fd``
    由 :c:func:`open()` 返回的文件描述符
``argp``
    指向 struct cec_msg 的指针
描述
===========

为了接收一个 CEC 消息，应用程序需要填充 struct :c:type:`cec_msg` 的 ``timeout`` 字段，并将其传递给 :ref:`ioctl CEC_RECEIVE <CEC_RECEIVE>`。
如果文件描述符处于非阻塞模式且没有待处理的接收消息，则会返回 -1 并将 errno 设置为 ``EAGAIN`` 错误码。如果文件描述符处于阻塞模式且 ``timeout`` 非零，并且在 ``timeout`` 毫秒内没有接收到消息，则会返回 -1 并将 errno 设置为 ``ETIMEDOUT`` 错误码。

接收到的消息可以是：

1. 来自另一个 CEC 设备的消息（``sequence`` 字段为 0，``tx_status`` 为 0，``rx_status`` 非零）
2. 早先非阻塞发送的结果（``sequence`` 字段非零，``tx_status`` 非零，``rx_status`` 为 0）
3. 对早先非阻塞发送的回复（``sequence`` 字段非零，``tx_status`` 为 0，``rx_status`` 非零）

为了发送一个 CEC 消息，应用程序需要填充 struct :c:type:`cec_msg` 并将其传递给 :ref:`ioctl CEC_TRANSMIT <CEC_TRANSMIT>`。
:ref:`ioctl CEC_TRANSMIT <CEC_TRANSMIT>` 只有在设置了 ``CEC_CAP_TRANSMIT`` 时才可用。如果发送队列已满，则会返回 -1 并将 errno 设置为 ``EBUSY`` 错误码。

发送队列有足够的空间来容纳 18 条消息（大约相当于 1 秒钟的 2 字节消息）。需要注意的是，CEC 内核框架还会回复核心消息（参见 :ref:`cec-core-processing`），因此不建议完全填满发送队列。
如果文件描述符处于非阻塞模式，则发送操作将返回0，并且一旦发送完成，可以通过 :ref:`ioctl CEC_RECEIVE <CEC_RECEIVE>` 获取发送结果。如果非阻塞发送还指定了等待回复，则回复将在稍后的消息中到达。可以使用 ``sequence`` 字段将发送结果和回复与原始发送关联起来。

通常，在物理地址无效（例如由于断开连接）时调用 :ref:`ioctl CEC_TRANSMIT <CEC_TRANSMIT>` 将返回 ``ENONET``。然而，CEC规范允许在物理地址无效的情况下从“未注册”向“电视”发送消息，因为某些电视在进入待机状态或切换到其他输入时会将HDMI连接器的热插拔检测引脚拉低。当热插拔检测引脚被拉低时，EDID消失，从而导致物理地址无效，但电缆仍然连接着并且CEC仍然有效。为了检测/唤醒设备，允许从发起者0xf（“未注册”）向目的地0（“电视”）发送轮询和“图像/文本视图打开”消息。

.. tabularcolumns:: |p{1.0cm}|p{3.5cm}|p{12.8cm}|

.. c:type:: cec_msg

.. cssclass:: longtable

.. flat-table:: struct cec_msg
    :header-rows:  0
    :stub-columns: 0
    :widths:       1 1 16

    * - __u64
      - ``tx_ts``
      - 消息最后一字节发送的时间戳（纳秒）
时间戳取自 ``CLOCK_MONOTONIC`` 时钟。要从用户空间访问相同的时钟，请使用 :c:func:`clock_gettime`
* - __u64
      - ``rx_ts``
      - 消息最后一字节接收的时间戳（纳秒）
时间戳取自 ``CLOCK_MONOTONIC`` 时钟。要从用户空间访问相同的时钟，请使用 :c:func:`clock_gettime`
* - __u32
      - ``len``
      - 消息的长度。对于 :ref:`ioctl CEC_TRANSMIT <CEC_TRANSMIT>`，这个字段由应用程序填充。驱动程序将为 :ref:`ioctl CEC_RECEIVE <CEC_RECEIVE>` 填充此字段。对于 :ref:`ioctl CEC_TRANSMIT <CEC_TRANSMIT>`，如果设置了 ``reply``，则驱动程序会用回复消息的长度填充该字段。

* - __u32
      - ``timeout``
      - 超时时间（毫秒）。这是设备在超时前等待接收消息的时间。如果设置为 0，则当调用 :ref:`ioctl CEC_RECEIVE <CEC_RECEIVE>` 时会无限期地等待。如果调用 :ref:`ioctl CEC_TRANSMIT <CEC_TRANSMIT>` 并且 ``timeout`` 为 0，则在 ``reply`` 非零时将其替换为 1000，或在 ``reply`` 为 0 时忽略。

* - __u32
      - ``sequence``
      - 所有发送的消息都会自动分配一个非零的序列号，这由 CEC 框架完成。当 CEC 框架排队发送结果以进行非阻塞发送时，它会使用这个序列号。这样应用程序可以将接收到的消息与原始发送消息关联起来。
      此外，如果非阻塞发送将等待回复（即 ``timeout`` 不为 0），则回复消息的 ``sequence`` 字段将被设置为原始发送消息的序列值。这样应用程序可以将接收到的消息与原始发送消息关联起来。

* - __u32
      - ``flags``
      - 标志。参见 :ref:`cec-msg-flags` 获取可用标志列表。

* - __u8
      - ``msg[16]``
      - 消息的有效负载。对于 :ref:`ioctl CEC_TRANSMIT <CEC_TRANSMIT>`，这个字段由应用程序填充。驱动程序将为 :ref:`ioctl CEC_RECEIVE <CEC_RECEIVE>` 填充此字段。对于 :ref:`ioctl CEC_TRANSMIT <CEC_TRANSMIT>`，如果设置了 ``timeout``，则驱动程序会用回复消息的有效负载填充该字段。

* - __u8
      - ``reply``
      - 等待直到该消息收到回复。如果 ``reply`` 为 0 且 ``timeout`` 为 0，则不等待回复，在发送消息后返回。 :ref:`ioctl CEC_RECEIVE <CEC_RECEIVE>` 忽略此字段。
      允许 ``reply`` 为 0（这是 Feature Abort 消息的操作码）且 ``timeout`` 非零的情况，以便能够发送消息并等待最多 ``timeout`` 毫秒的 Feature Abort 回复。在这种情况下，``rx_status`` 将被设置为 :ref:`CEC_RX_STATUS_TIMEOUT <CEC-RX-STATUS-TIMEOUT>` 或 :ref:`CEC_RX_STATUS_FEATURE_ABORT <CEC-RX-STATUS-FEATURE-ABORT>`。
如果发送的消息是 `CEC_MSG_INITIATE_ARC`，则 `reply` 值 `CEC_MSG_REPORT_ARC_INITIATED` 和 `CEC_MSG_REPORT_ARC_TERMINATED` 的处理方式不同：这两个值都将匹配所有可能的回复。

原因是 `CEC_MSG_INITIATE_ARC` 消息是唯一具有两个可能回复（除了特征中止）的 CEC 消息。`reply` 字段将更新为实际的回复，以便与接收到的消息内容同步。

* - `__u8`
  - `rx_status`
  - 接收消息的状态位。请参见 :ref:`cec-rx-status` 了解可能的状态值。
* - `__u8`
  - `tx_status`
  - 发送消息的状态位。请参见 :ref:`cec-tx-status` 了解可能的状态值。
  在非阻塞模式下调用 :ref:`ioctl CEC_TRANSMIT <CEC_TRANSMIT>` 时，如果发送开始，则该字段为 0；如果发送结果立即已知，则为非零。后一种情况发生在尝试向自己发送 Poll 消息时，这会导致一个 :ref:`CEC_TX_STATUS_NACK <CEC-TX-STATUS-NACK>` 状态，而实际上并没有发送 Poll 消息。
* - `__u8`
  - `tx_arb_lost_cnt`
  - 发送尝试导致仲裁丢失错误的数量计数器。只有在硬件支持的情况下才会设置此值，否则始终为 0。此计数器仅在 :ref:`CEC_TX_STATUS_ARB_LOST <CEC-TX-STATUS-ARB-LOST>` 状态位被设置时有效。
* - `__u8`
  - `tx_nack_cnt`
  - 发送尝试导致未被确认错误的数量计数器。只有在硬件支持的情况下才会设置此值，否则始终为 0。此计数器仅在 :ref:`CEC_TX_STATUS_NACK <CEC-TX-STATUS-NACK>` 状态位被设置时有效。
* - `__u8`
  - `tx_low_drive_cnt`
  - 发送尝试导致仲裁丢失错误的数量计数器。只有在硬件支持的情况下才会设置此值，否则始终为 0。此计数器仅在 :ref:`CEC_TX_STATUS_LOW_DRIVE <CEC-TX-STATUS-LOW-DRIVE>` 状态位被设置时有效。
* - `__u8`
  - `tx_error_cnt`
  - 发送错误数量计数器（除仲裁丢失或未被确认之外）。只有在硬件支持的情况下才会设置此值，否则始终为 0。此计数器仅在 :ref:`CEC_TX_STATUS_ERROR <CEC-TX-STATUS-ERROR>` 状态位被设置时有效。

.. tabularcolumns:: |p{6.2cm}|p{1.0cm}|p{10.1cm}|

.. _cec-msg-flags:

.. flat-table:: struct cec_msg 的标志
    :header-rows:  0
    :stub-columns: 0
    :widths:       3 1 4

    * .. _`CEC-MSG-FL-REPLY-TO-FOLLOWERS`:

      - `CEC_MSG_FL_REPLY_TO_FOLLOWERS`
      - 1
      - 如果 CEC 发送期望一个回复，默认情况下，这个回复只会发送给调用 :ref:`ioctl CEC_TRANSMIT <CEC_TRANSMIT>` 的文件句柄。如果设置了此标志，则回复也会发送给所有跟随者（如果有）。如果调用 :ref:`ioctl CEC_TRANSMIT <CEC_TRANSMIT>` 的文件句柄也是一个跟随者，则该文件句柄会收到两次回复：一次作为 :ref:`ioctl CEC_TRANSMIT <CEC_TRANSMIT>` 的结果，另一次通过 :ref:`ioctl CEC_RECEIVE <CEC_RECEIVE>`。
* .. _`CEC-MSG-FL-RAW`:

      - ``CEC_MSG_FL_RAW``
      - 2
      - 通常情况下，CEC 消息在传输前会被验证。如果在调用 :ref:`ioctl CEC_TRANSMIT <CEC_TRANSMIT>` 时设置了此标志，则不会进行验证，并且消息将按原样传输。
这在调试 CEC 问题时非常有用。
此标志仅在进程具有 ``CAP_SYS_RAWIO`` 权限时才允许使用。如果没有设置该权限，则返回 ``EPERM`` 错误码。
.. tabularcolumns:: |p{5.6cm}|p{0.9cm}|p{10.8cm}|

.. _cec-tx-status:

.. flat-table:: CEC 传输状态
    :header-rows:  0
    :stub-columns: 0
    :widths:       3 1 16

    * .. _`CEC-TX-STATUS-OK`:

      - ``CEC_TX_STATUS_OK``
      - 0x01
      - 消息成功传输。此状态与 :ref:`CEC_TX_STATUS_MAX_RETRIES <CEC-TX-STATUS-MAX-RETRIES>` 互斥。
如果在最终成功传输之前有早期尝试失败的情况，其他位仍可被设置。
* .. _`CEC-TX-STATUS-ARB-LOST`:

      - ``CEC_TX_STATUS_ARB_LOST``
      - 0x02
      - CEC 线路仲裁失败，即另一个更高优先级的传输同时开始。这是一个可选状态，并非所有硬件都能检测到此错误条件。
* .. _`CEC-TX-STATUS-NACK`:

      - ``CEC_TX_STATUS_NACK``
      - 0x04
      - 消息未被确认。需要注意的是，一些硬件无法区分“未确认”状态和其他错误条件，即传输结果只是成功或失败。在这种情况下，当传输失败时会返回此状态。
* .. _`CEC-TX-STATUS-LOW-DRIVE`:

      - ``CEC_TX_STATUS_LOW_DRIVE``
      - 0x08
      - 在 CEC 总线上检测到低驱动。这表明跟随者在总线上检测到错误并请求重新传输。这是一个可选状态，并非所有硬件都能检测到此错误条件。
* .. _`CEC-TX-STATUS-ERROR`:

      - ``CEC_TX_STATUS_ERROR``
      - 0x10
      - 发生了某些错误。此状态用于任何不符合 ``CEC_TX_STATUS_ARB_LOST`` 或 ``CEC_TX_STATUS_LOW_DRIVE`` 的错误情况，可能是因为硬件无法判断发生了哪种错误，或者因为硬件测试了除这两种之外的其他条件。这是一个可选状态。
* .. _`CEC-TX-STATUS-MAX-RETRIES`:

      - ``CEC_TX_STATUS_MAX_RETRIES``
      - 0x20
      - 经过一次或多次重试后传输失败。此状态位与 :ref:`CEC_TX_STATUS_OK <CEC-TX-STATUS-OK>` 互斥。
其他位仍可被设置以解释发生了哪些故障
* .. _`CEC-TX-STATUS-ABORTED`:

      - ``CEC_TX_STATUS_ABORTED``
      - 0x40
      - 发送因HDMI断开连接、适配器未配置、发送被中断或驱动程序在尝试开始发送时返回错误而中止
* .. _`CEC-TX-STATUS-TIMEOUT`:

      - ``CEC_TX_STATUS_TIMEOUT``
      - 0x80
      - 发送超时。这通常不应该发生，表明存在驱动程序问题
.. tabularcolumns:: |p{5.6cm}|p{0.9cm}|p{10.8cm}|

.. _cec-rx-status:

.. flat-table:: CEC接收状态
    :header-rows:  0
    :stub-columns: 0
    :widths:       3 1 16

    * .. _`CEC-RX-STATUS-OK`:

      - ``CEC_RX_STATUS_OK``
      - 0x01
      - 消息接收成功
* .. _`CEC-RX-STATUS-TIMEOUT`:

      - ``CEC_RX_STATUS_TIMEOUT``
      - 0x02
      - 对先前发送的消息的回复超时
* .. _`CEC-RX-STATUS-FEATURE-ABORT`:

      - ``CEC_RX_STATUS_FEATURE_ABORT``
      - 0x04
      - 消息接收成功，但回复为``CEC_MSG_FEATURE_ABORT``。此状态仅在该消息是先前发送的消息的回复时才设置
* .. _`CEC-RX-STATUS-ABORTED`:

      - ``CEC_RX_STATUS_ABORTED``
      - 0x08
      - 等待对先前发送的消息的回复因HDMI线缆断开连接、适配器未配置或等待回复的:ref:`CEC_TRANSMIT <CEC_RECEIVE>` 被中断而中止

返回值
======

成功时返回0，出错时返回-1，并且设置适当的 ``errno`` 变量。通用错误代码在:ref:`Generic Error Codes <gen-errors>`章节中有描述。
:ref:`ioctl CEC_RECEIVE <CEC_RECEIVE>` 可能返回以下错误代码：

EAGAIN
    接收队列中没有消息，并且文件句柄处于非阻塞模式
ETIMEDOUT
    在等待消息时达到了 ``timeout``
ERESTARTSYS
    等待消息时被中断（例如，通过Ctrl-C）

`:ref:`ioctl CEC_TRANSMIT <CEC_TRANSMIT>` 可以返回以下错误代码：

ENOTTY
    未设置 ``CEC_CAP_TRANSMIT`` 能力，因此此ioctl不受支持
EPERM
    CEC适配器未配置，即未调用过 `:ref:`ioctl CEC_ADAP_S_LOG_ADDRS <CEC_ADAP_S_LOG_ADDRS>`
    或者从没有 `CAP_SYS_RAWIO` 能力的进程使用了 ``CEC_MSG_FL_RAW``
ENONET
    CEC适配器未配置，即 `:ref:`ioctl CEC_ADAP_S_LOG_ADDRS <CEC_ADAP_S_LOG_ADDRS>`
    已被调用，但物理地址无效，因此没有声明逻辑地址。在这种情况下，从发起者 0xf（'未注册'）到目标 0（'电视'）的传输将照常进行。
EBUSY
    其他文件句柄处于独占跟随者或发起者模式，或者文件句柄处于 ``CEC_MODE_NO_INITIATOR`` 模式。如果传输队列已满也会返回此错误。
EINVAL
    结构体 :c:type:`cec_msg` 的内容无效
ERESTARTSYS
    等待成功传输时被中断（例如，通过Ctrl-C）
