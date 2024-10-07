SPDX 许可声明标识符: GFDL-1.1-no-invariants-or-later
.. c:namespace:: CEC

.. _CEC_MODE:
.. _CEC_G_MODE:
.. _CEC_S_MODE:

********************************
ioctl 命令 CEC_G_MODE 和 CEC_S_MODE
********************************

CEC_G_MODE, CEC_S_MODE - 获取或设置 CEC 适配器的独占使用

概览
========

.. c:macro:: CEC_G_MODE

``int ioctl(int fd, CEC_G_MODE, __u32 *argp)``

.. c:macro:: CEC_S_MODE

``int ioctl(int fd, CEC_S_MODE, __u32 *argp)``

参数
=========

``fd``
    由 :c:func:`open()` 返回的文件描述符
``argp``
    指向 CEC 模式的指针
描述
===========

默认情况下，任何文件句柄都可以使用 :ref:`CEC_TRANSMIT`，但为了防止应用程序相互干扰，必须能够获得对 CEC 适配器的独占访问。这个 ioctl 命令将文件句柄设置为发起者和/或跟随者的模式，具体取决于所选择的模式。发起者是用于发起消息的文件句柄，即它命令其他 CEC 设备。跟随者是接收发送到 CEC 适配器的消息并处理它们的文件句柄。同一个文件句柄可以同时作为发起者和跟随者，或者这两个角色可以由两个不同的文件句柄承担。当接收到一个 CEC 消息时，CEC 框架将决定如何处理该消息。如果消息是对先前传输消息的回复，则回复将被发送回正在等待它的文件句柄。此外，CEC 框架也会处理它。如果消息不是回复，则 CEC 框架会先处理它。如果没有跟随者，则消息将被丢弃，并且如果框架无法处理它，则会向发起者发送功能中止。如果有跟随者，则消息会被传递给跟随者，跟随者将使用 :ref:`ioctl CEC_RECEIVE <CEC_RECEIVE>` 来取消排队新的消息。框架期望跟随者做出正确的决策。
除非跟随者另有请求，否则 CEC 框架会处理核心消息。跟随者可以启用直通模式。在这种情况下，CEC 框架将不处理大多数核心消息并将其传递给跟随者，跟随者需要实现这些消息。有一些消息核心始终会处理，无论是否处于直通模式。详情请参阅 :ref:`cec-core-processing`。
如果没有发起者，则任何 CEC 文件句柄都可以使用 :ref:`ioctl CEC_TRANSMIT <CEC_TRANSMIT>`。如果有独占发起者，则只有那个发起者可以调用 :ref:`CEC_TRANSMIT`。当然，跟随者始终可以调用 :ref:`ioctl CEC_TRANSMIT <CEC_TRANSMIT>`。

可用的发起者模式如下：

.. tabularcolumns:: |p{5.6cm}|p{0.9cm}|p{10.8cm}|

.. _cec-mode-initiator_e:

.. flat-table:: 发起者模式
    :header-rows:  0
    :stub-columns: 0
    :widths:       3 1 16

    * .. _`CEC-MODE-NO-INITIATOR`:

      - ``CEC_MODE_NO_INITIATOR``
      - 0x0
      - 这不是一个发起者，即它不能传输 CEC 消息或对 CEC 适配器进行任何其他更改
* .. _`CEC-MODE-INITIATOR`:

      - ``CEC_MODE_INITIATOR``
      - 0x1
      - 这是一个发起者（设备打开时的默认值），它可以传输 CEC 消息并对 CEC 适配器进行更改，除非存在一个独占发起者
* .. _`CEC-MODE-EXCL-INITIATOR`:

      - ``CEC_MODE_EXCL_INITIATOR``
      - 0x2
      - 这是一个独占发起者，并且此文件描述符是唯一可以传输CEC消息并更改CEC适配器的。
        如果已经有其他独占发起者，则尝试成为独占发起者将返回``EBUSY``错误代码。

可用的跟随者模式如下：

.. tabularcolumns:: |p{6.6cm}|p{0.9cm}|p{9.8cm}|

.. _cec-mode-follower_e:

.. cssclass:: longtable

.. flat-table:: 跟随者模式
    :header-rows:  0
    :stub-columns: 0
    :widths:       3 1 16

    * .. _`CEC-MODE-NO-FOLLOWER`:

      - ``CEC_MODE_NO_FOLLOWER``
      - 0x00
      - 这不是跟随者（当设备打开时的默认状态）

* .. _`CEC-MODE-FOLLOWER`:

      - ``CEC_MODE_FOLLOWER``
      - 0x10
      - 这是一个跟随者，它会接收CEC消息，除非有独占跟随者。
        如果未设置 :ref:`CEC_CAP_TRANSMIT <CEC-CAP-TRANSMIT>` 或指定了 :ref:`CEC_MODE_NO_INITIATOR <CEC-MODE-NO-INITIATOR>`，
        则会返回 ``EINVAL`` 错误代码。

* .. _`CEC-MODE-EXCL-FOLLOWER`:

      - ``CEC_MODE_EXCL_FOLLOWER``
      - 0x20
      - 这是一个独占跟随者，只有这个文件描述符会接收CEC消息进行处理。
        如果已经有其他独占跟随者，则尝试成为独占跟随者将返回 ``EBUSY`` 错误代码。
        如果未设置 :ref:`CEC_CAP_TRANSMIT <CEC-CAP-TRANSMIT>` 或指定了 :ref:`CEC_MODE_NO_INITIATOR <CEC-MODE-NO-INITIATOR>`，
        则会返回 ``EINVAL`` 错误代码。

* .. _`CEC-MODE-EXCL-FOLLOWER-PASSTHRU`:

      - ``CEC_MODE_EXCL_FOLLOWER_PASSTHRU``
      - 0x30
      - 这是一个独占跟随者，只有这个文件描述符会接收CEC消息进行处理。
        此外，它还会将CEC设备置于直通模式，允许独占跟随者处理大多数核心消息，而不是依赖CEC框架。
        如果已经有其他独占跟随者，则尝试成为独占跟随者将返回 ``EBUSY`` 错误代码。
        如果未设置 :ref:`CEC_CAP_TRANSMIT <CEC-CAP-TRANSMIT>` 或指定了 :ref:`CEC_MODE_NO_INITIATOR <CEC-MODE-NO-INITIATOR>`，
        则会返回 ``EINVAL`` 错误代码。

* .. _`CEC-MODE-MONITOR-PIN`:

      - ``CEC_MODE_MONITOR_PIN``
      - 0xd0
      - 将文件描述符置于引脚监控模式。只能与 :ref:`CEC_MODE_NO_INITIATOR <CEC-MODE-NO-INITIATOR>` 结合使用，
        否则将返回 ``EINVAL`` 错误代码。
        此模式要求设置 :ref:`CEC_CAP_MONITOR_PIN <CEC-CAP-MONITOR-PIN>` 功能，
        否则将返回 ``EINVAL`` 错误代码。
        在引脚监控模式下，此文件描述符可以接收 ``CEC_EVENT_PIN_CEC_LOW`` 和 ``CEC_EVENT_PIN_CEC_HIGH`` 事件，
        以查看低级别的CEC引脚转换。这对于调试非常有用。
        此模式仅在进程具有 ``CAP_NET_ADMIN`` 权限时才允许使用。
        如果没有设置该权限，则返回 ``EPERM`` 错误代码。

* .. _`CEC-MODE-MONITOR`:

      - ``CEC_MODE_MONITOR``
      - 0xe0
      - 将文件描述符置于监控模式。只能与 :ref:`CEC_MODE_NO_INITIATOR <CEC-MODE-NO-INITIATOR>` 结合使用，
        否则将返回 ``EINVAL`` 错误代码。
在监视模式下，此CEC设备发送的所有消息以及它接收到的所有消息（包括广播消息和针对其逻辑地址之一的定向消息）都会被报告。这对于调试非常有用。只有当进程具有`CAP_NET_ADMIN`权限时才允许这样做。如果没有设置该权限，则返回`EPERM`错误代码。

* .. _`CEC-MODE-MONITOR-ALL`:

      - `CEC_MODE_MONITOR_ALL`
      - 0xf0
      - 将文件描述符置于“监视所有”模式。只能与 :ref:`CEC_MODE_NO_INITIATOR <CEC-MODE-NO-INITIATOR>` 结合使用，否则将返回`EINVAL`错误代码。在“监视所有”模式下，此CEC设备发送的所有消息以及它接收的所有消息（包括指向其他CEC设备的定向消息）都会被报告。这对调试非常有用，但并非所有设备都支持此功能。此模式要求设置 :ref:`CEC_CAP_MONITOR_ALL <CEC-CAP-MONITOR-ALL>` 权限，否则返回`EINVAL`错误代码。只有当进程具有`CAP_NET_ADMIN`权限时才允许这样做。如果没有设置该权限，则返回`EPERM`错误代码。

核心消息处理细节：

.. tabularcolumns:: |p{6.6cm}|p{10.9cm}|

.. _cec-core-processing:

.. flat-table:: 核心消息处理
    :header-rows:  0
    :stub-columns: 0
    :widths: 1 8

    * .. _`CEC-MSG-GET-CEC-VERSION`:

      - `CEC_MSG_GET_CEC_VERSION`
      - 核心将返回通过 :ref:`ioctl CEC_ADAP_S_LOG_ADDRS <CEC_ADAP_S_LOG_ADDRS>` 设置的CEC版本，除非处于直通模式。在直通模式下，核心不执行任何操作，此消息必须由跟随者处理。
* .. _`CEC-MSG-GIVE-DEVICE-VENDOR-ID`:

      - `CEC_MSG_GIVE_DEVICE_VENDOR_ID`
      - 核心将返回通过 :ref:`ioctl CEC_ADAP_S_LOG_ADDRS <CEC_ADAP_S_LOG_ADDRS>` 设置的供应商ID，除非处于直通模式。在直通模式下，核心不执行任何操作，此消息必须由跟随者处理。
* .. _`CEC-MSG-ABORT`:

      - `CEC_MSG_ABORT`
      - 核心将返回一个带有规范中指定的“特性拒绝”原因的特性中止消息，除非处于直通模式。在直通模式下，核心不执行任何操作，此消息必须由跟随者处理。
* .. _`CEC-MSG-GIVE-PHYSICAL-ADDR`:

      - `CEC_MSG_GIVE_PHYSICAL_ADDR`
      - 核心将报告当前的物理地址，除非处于直通模式。在直通模式下，核心不执行任何操作，此消息必须由跟随者处理。
* .. _`CEC-MSG-GIVE-OSD-NAME`:

      - `CEC_MSG_GIVE_OSD_NAME`
      - 核心将报告通过 :ref:`ioctl CEC_ADAP_S_LOG_ADDRS <CEC_ADAP_S_LOG_ADDRS>` 设置的当前OSD名称，除非处于直通模式。在直通模式下，核心不执行任何操作，此消息必须由跟随者处理。
* .. _`CEC-MSG-GIVE-FEATURES`:

      - `CEC_MSG_GIVE_FEATURES`
      - 如果CEC版本早于2.0，则核心将不做任何操作；否则，它将报告通过 :ref:`ioctl CEC_ADAP_S_LOG_ADDRS <CEC_ADAP_S_LOG_ADDRS>` 设置的当前特性，除非处于直通模式。在直通模式下，核心不做任何操作（对于任何CEC版本），此消息必须由跟随者处理。
* .. _`CEC-MSG-USER-CONTROL-PRESSED`:

      - `CEC_MSG_USER_CONTROL_PRESSED`
      - 如果设置了 :ref:`CEC_CAP_RC <CEC-CAP-RC>` 并且设置了 :ref:`CEC_LOG_ADDRS_FL_ALLOW_RC_PASSTHRU <CEC-LOG-ADDRS-FL-ALLOW-RC-PASSTHRU>` ，则生成遥控键按下。此消息始终传递给跟随者。
* .. _`CEC-MSG-USER-CONTROL-RELEASED`:

      - `CEC_MSG_USER_CONTROL_RELEASED`
      - 如果设置了 :ref:`CEC_CAP_RC <CEC-CAP-RC>` 并且设置了 :ref:`CEC_LOG_ADDRS_FL_ALLOW_RC_PASSTHRU <CEC-LOG-ADDRS-FL-ALLOW-RC-PASSTHRU>` ，则生成遥控键释放。此消息始终传递给跟随者。
* .. _`CEC-MSG-REPORT-PHYSICAL-ADDR`:

      - ``CEC_MSG_REPORT_PHYSICAL_ADDR``
      - CEC 框架将记录报告的物理地址，并将消息传递给跟随者

返回值
======

成功时返回 0，出错时返回 -1 并设置相应的 ``errno`` 变量。通用错误代码在
:ref:`通用错误代码 <gen-errors>` 章节中描述。
:ref:`ioctl CEC_S_MODE <CEC_S_MODE>` 可能返回以下错误代码：

EINVAL
    请求的模式无效
EPERM
    请求了监视器模式，但进程没有 ``CAP_NET_ADMIN`` 权限
EBUSY
    其他人已经是独占跟随者或发起者
