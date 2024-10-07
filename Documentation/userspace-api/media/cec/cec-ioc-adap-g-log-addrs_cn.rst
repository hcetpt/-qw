.. SPDX 许可证标识符: GFDL-1.1 或之后版本无不变部分
.. c:命名空间:: CEC

.. _CEC_ADAP_LOG_ADDRS:
.. _CEC_ADAP_G_LOG_ADDRS:
.. _CEC_ADAP_S_LOG_ADDRS:

****************************************************
ioctl 命令 CEC_ADAP_G_LOG_ADDRS 和 CEC_ADAP_S_LOG_ADDRS
****************************************************

名称
====

CEC_ADAP_G_LOG_ADDRS, CEC_ADAP_S_LOG_ADDRS - 获取或设置逻辑地址

概览
========

.. c:宏:: CEC_ADAP_G_LOG_ADDRS

``int ioctl(int fd, CEC_ADAP_G_LOG_ADDRS, struct cec_log_addrs *argp)``

.. c:宏:: CEC_ADAP_S_LOG_ADDRS

``int ioctl(int fd, CEC_ADAP_S_LOG_ADDRS, struct cec_log_addrs *argp)``

参数
=========

``fd``
    由 :c:func:`open()` 返回的文件描述符
``argp``
    指向结构体 :c:type:`cec_log_addrs` 的指针

描述
===========

为了查询当前的 CEC 逻辑地址，应用程序应调用 :ref:`ioctl CEC_ADAP_G_LOG_ADDRS <CEC_ADAP_G_LOG_ADDRS>` 并提供一个指向结构体 :c:type:`cec_log_addrs` 的指针，驱动程序会将逻辑地址存储在这个结构体中。要设置新的逻辑地址，应用程序需要填充结构体 :c:type:`cec_log_addrs` 并通过指向该结构体的指针调用 :ref:`ioctl CEC_ADAP_S_LOG_ADDRS <CEC_ADAP_S_LOG_ADDRS>`。只有在设置了 ``CEC_CAP_LOG_ADDRS`` 的情况下才能使用 :ref:`ioctl CEC_ADAP_S_LOG_ADDRS <CEC_ADAP_S_LOG_ADDRS>`（否则返回 ``ENOTTY`` 错误码）。:ref:`ioctl CEC_ADAP_S_LOG_ADDRS <CEC_ADAP_S_LOG_ADDRS>` 只能被处于发起者模式下的文件描述符调用（参见 :ref:`CEC_S_MODE`），如果不是，则返回 ``EBUSY`` 错误码。
要清除现有的逻辑地址，可以将 ``num_log_addrs`` 设置为 0。在这种情况下，其他所有字段将被忽略。适配器将进入未配置状态，并且 ``cec_version``、``vendor_id`` 和 ``osd_name`` 字段都将重置为其默认值（CEC 版本 2.0，没有厂商 ID 和空的 OSD 名称）。
如果物理地址有效（参见 :ref:`ioctl CEC_ADAP_S_PHYS_ADDR <CEC_ADAP_S_PHYS_ADDR>`），则此 ioctl 将阻塞直到所有请求的逻辑地址都被占用。如果文件描述符处于非阻塞模式，则不会等待逻辑地址被占用，而是直接返回 0。
当逻辑地址被占用或清除时，将发送 :ref:`CEC_EVENT_STATE_CHANGE <CEC-EVENT-STATE-CHANGE>` 事件。
尝试在逻辑地址类型已定义的情况下调用 :ref:`ioctl CEC_ADAP_S_LOG_ADDRS <CEC_ADAP_S_LOG_ADDRS>` 时，将返回 ``EBUSY`` 错误。

.. c:type:: cec_log_addrs

.. tabularcolumns:: |p{1.0cm}|p{8.0cm}|p{8.0cm}|

.. cssclass:: longtable

.. flat-table:: 结构体 cec_log_addrs
    :header-rows:  0
    :stub-columns: 0
    :widths:       1 1 16

    * - __u8
      - ``log_addr[CEC_MAX_LOG_ADDRS]``
      - 实际上被占用的逻辑地址。这由驱动程序设置。如果没有逻辑地址可以被占用，则设置为 ``CEC_LOG_ADDR_INVALID``。如果此适配器未注册，则 ``log_addr[0]`` 被设置为 0xf，其余均设置为 ``CEC_LOG_ADDR_INVALID``。
    * - __u16
      - ``log_addr_mask``
      - 此适配器所占用的所有逻辑地址的位掩码。如果此适配器未注册，则 ``log_addr_mask`` 设置第 15 位并清空所有其他位。如果此适配器完全未配置，则 ``log_addr_mask`` 被设置为 0。由驱动程序设置。
* - __u8
  - ``cec_version``
  - 该适配器应使用的CEC版本。详见 :ref:`cec-versions`。用于实现 ``CEC_MSG_CEC_VERSION`` 和 ``CEC_MSG_REPORT_FEATURES`` 消息。
  注意：:ref:`CEC_OP_CEC_VERSION_1_3A <CEC-OP-CEC-VERSION-1-3A>` 不被CEC框架允许。
* - __u8
  - ``num_log_addrs``
  - 要设置的逻辑地址数量。必须≤由 :ref:`CEC_ADAP_G_CAPS` 返回的 ``available_log_addrs``。此结构中的所有数组仅填充到索引 ``available_log_addrs``-1。剩余的数组元素将被忽略。注意CEC 2.0标准允许的最大逻辑地址数为2个，尽管某些硬件支持更多。
  ``CEC_MAX_LOG_ADDRS`` 是4。驱动程序将返回其实际能够声明的逻辑地址数量，这可能少于请求的数量。如果此字段设置为0，则CEC适配器应清除所有已声明的逻辑地址，并忽略其他所有字段。
* - __u32
  - ``vendor_id``
  - 厂商ID是一个24位的数字，用于标识特定的厂商或实体。基于这个ID，可以定义特定厂商的命令。如果您不需要厂商ID，请将其设置为 ``CEC_VENDOR_ID_NONE``。
* - __u32
  - ``flags``
  - 标志。参见 :ref:`cec-log-addrs-flags` 获取可用标志列表。
* - char
  - ``osd_name[15]``
  - 通过 ``CEC_MSG_SET_OSD_NAME`` 消息返回的屏幕显示名称。
* - __u8
  - ``primary_device_type[CEC_MAX_LOG_ADDRS]``
  - 每个逻辑地址的主要设备类型。参见 :ref:`cec-prim-dev-types` 获取可能的类型。
* - __u8
  - ``log_addr_type[CEC_MAX_LOG_ADDRS]``
  - 逻辑地址类型。参见 :ref:`cec-log-addr-types` 获取可能的类型。驱动程序将更新此字段，以反映其实际声明的逻辑地址类型（例如，它可能需要回退到 :ref:`CEC_LOG_ADDR_TYPE_UNREGISTERED <CEC-LOG-ADDR-TYPE-UNREGISTERED>`）。
* - __u8
  - ``all_device_types[CEC_MAX_LOG_ADDRS]``
  - CEC 2.0专用：所有设备类型的位掩码。参见 :ref:`cec-all-dev-types-flags`。它用于CEC 2.0的 ``CEC_MSG_REPORT_FEATURES`` 消息。对于CEC 1.4，您可以将此字段留空，或者根据CEC 2.0指南填写，以便向CEC框架提供有关设备类型的信息，尽管框架不会直接在CEC消息中使用它。
* - `__u8`
  - ``features[CEC_MAX_LOG_ADDRS][12]``
  - 每个逻辑地址的特性。在CEC 2.0的`CEC_MSG_REPORT_FEATURES`消息中使用。这12字节包括RC Profile和设备特性。对于CEC 1.4，您可以将此字段全部设置为0，或者根据CEC 2.0指南填写，以向CEC框架提供更多关于设备类型的信息，尽管框架不会直接在CEC消息中使用它。

.. tabularcolumns:: |p{7.8cm}|p{1.0cm}|p{8.5cm}|

.. _cec-log-addrs-flags:

.. flat-table:: 结构体`cec_log_addrs`中的标志
    :header-rows:  0
    :stub-columns: 0
    :widths:       3 1 4

    * .. _`CEC-LOG-ADDRS-FL-ALLOW-UNREG-FALLBACK`:

      - ``CEC_LOG_ADDRS_FL_ALLOW_UNREG_FALLBACK``
      - 1
      - 默认情况下，如果无法声明请求类型的逻辑地址，则会返回到未配置状态。如果设置了此标志，则会回退到未注册的逻辑地址。请注意，如果显式请求了未注册的逻辑地址，则此标志无效。
    * .. _`CEC-LOG-ADDRS-FL-ALLOW-RC-PASSTHRU`:

      - ``CEC_LOG_ADDRS_FL_ALLOW_RC_PASSTHRU``
      - 2
      - 默认情况下，只有当有跟随者时，`CEC_MSG_USER_CONTROL_PRESSED`和`CEC_MSG_USER_CONTROL_RELEASED`消息才会传递给它们。如果设置了此标志，则这些消息还会传递给远程控制输入子系统，并显示为按键。此功能需要显式启用。如果使用CEC输入密码等信息，则可能不希望启用此功能，以避免轻易窃听按键。
    * .. _`CEC-LOG-ADDRS-FL-CDC-ONLY`:

      - ``CEC_LOG_ADDRS_FL_CDC_ONLY``
      - 4
      - 如果设置了此标志，则设备是CDC-Only。CDC-Only CEC设备只能处理CDC消息，其他所有消息都会被忽略。

.. tabularcolumns:: |p{7.8cm}|p{1.0cm}|p{8.5cm}|

.. _cec-versions:

.. flat-table:: CEC版本
    :header-rows:  0
    :stub-columns: 0
    :widths:       3 1 4

    * .. _`CEC-OP-CEC-VERSION-1-3A`:

      - ``CEC_OP_CEC_VERSION_1_3A``
      - 4
      - 根据HDMI 1.3a标准的CEC版本
    * .. _`CEC-OP-CEC-VERSION-1-4B`:

      - ``CEC_OP_CEC_VERSION_1_4B``
      - 5
      - 根据HDMI 1.4b标准的CEC版本
    * .. _`CEC-OP-CEC-VERSION-2-0`:

      - ``CEC_OP_CEC_VERSION_2_0``
      - 6
      - 根据HDMI 2.0标准的CEC版本

.. tabularcolumns:: |p{6.6cm}|p{2.2cm}|p{8.5cm}|

.. _cec-prim-dev-types:

.. flat-table:: CEC主要设备类型
    :header-rows:  0
    :stub-columns: 0
    :widths:       3 1 4

    * .. _`CEC-OP-PRIM-DEVTYPE-TV`:

      - ``CEC_OP_PRIM_DEVTYPE_TV``
      - 0
      - 用于电视
```markdown
.. _`CEC-OP-PRIM-DEVTYPE-RECORD`:

      - ``CEC_OP_PRIM_DEVTYPE_RECORD``
      - 1
      - 用于录音设备

.. _`CEC-OP-PRIM-DEVTYPE-TUNER`:

      - ``CEC_OP_PRIM_DEVTYPE_TUNER``
      - 3
      - 用于带有调谐器的设备

.. _`CEC-OP-PRIM-DEVTYPE-PLAYBACK`:

      - ``CEC_OP_PRIM_DEVTYPE_PLAYBACK``
      - 4
      - 用于播放设备

.. _`CEC-OP-PRIM-DEVTYPE-AUDIOSYSTEM`:

      - ``CEC_OP_PRIM_DEVTYPE_AUDIOSYSTEM``
      - 5
      - 用于音频系统（例如，音频/视频接收器）

.. _`CEC-OP-PRIM-DEVTYPE-SWITCH`:

      - ``CEC_OP_PRIM_DEVTYPE_SWITCH``
      - 6
      - 用于CEC切换器

.. _`CEC-OP-PRIM-DEVTYPE-VIDEOPROC`:

      - ``CEC_OP_PRIM_DEVTYPE_VIDEOPROC``
      - 7
      - 用于视频处理器设备

.. tabularcolumns:: |p{6.6cm}|p{2.2cm}|p{8.5cm}|

.. _cec-log-addr-types:

.. flat-table:: CEC 逻辑地址类型
    :header-rows:  0
    :stub-columns: 0
    :widths:       3 1 16

    * .. _`CEC-LOG-ADDR-TYPE-TV`:

      - ``CEC_LOG_ADDR_TYPE_TV``
      - 0
      - 用于电视

* .. _`CEC-LOG-ADDR-TYPE-RECORD`:

      - ``CEC_LOG_ADDR_TYPE_RECORD``
      - 1
      - 用于录音设备

* .. _`CEC-LOG-ADDR-TYPE-TUNER`:

      - ``CEC_LOG_ADDR_TYPE_TUNER``
      - 2
      - 用于调谐器设备

* .. _`CEC-LOG-ADDR-TYPE-PLAYBACK`:

      - ``CEC_LOG_ADDR_TYPE_PLAYBACK``
      - 3
      - 用于播放设备
```
* .. _`CEC-LOG-ADDR-TYPE-AUDIOSYSTEM`:

      - ``CEC_LOG_ADDR_TYPE_AUDIOSYSTEM``
      - 4
      - 用于音频系统设备
* .. _`CEC-LOG-ADDR-TYPE-SPECIFIC`:

      - ``CEC_LOG_ADDR_TYPE_SPECIFIC``
      - 5
      - 用于第二台电视或视频处理设备
* .. _`CEC-LOG-ADDR-TYPE-UNREGISTERED`:

      - ``CEC_LOG_ADDR_TYPE_UNREGISTERED``
      - 6
      - 如果只想保持未注册状态，请使用此选项。用于纯 CEC 切换器或仅 CDC 设备（CDC：功能发现与控制）

.. tabularcolumns:: |p{6.6cm}|p{2.2cm}|p{8.5cm}|

.. _cec-all-dev-types-flags:

.. flat-table:: CEC 所有设备类型标志
    :header-rows:  0
    :stub-columns: 0
    :widths:       3 1 4

    * .. _`CEC-OP-ALL-DEVTYPE-TV`:

      - ``CEC_OP_ALL_DEVTYPE_TV``
      - 0x80
      - 支持电视类型
* .. _`CEC-OP-ALL-DEVTYPE-RECORD`:

      - ``CEC_OP_ALL_DEVTYPE_RECORD``
      - 0x40
      - 支持录像机类型
* .. _`CEC-OP-ALL-DEVTYPE-TUNER`:

      - ``CEC_OP_ALL_DEVTYPE_TUNER``
      - 0x20
      - 支持调谐器类型
* .. _`CEC-OP-ALL-DEVTYPE-PLAYBACK`:

      - ``CEC_OP_ALL_DEVTYPE_PLAYBACK``
      - 0x10
      - 支持播放器类型
* .. _`CEC-OP-ALL-DEVTYPE-AUDIOSYSTEM`:

      - ``CEC_OP_ALL_DEVTYPE_AUDIOSYSTEM``
      - 0x08
      - 支持音频系统类型
* .. _`CEC-OP-ALL-DEVTYPE-SWITCH`:

      - ``CEC_OP_ALL_DEVTYPE_SWITCH``
      - 0x04
      - 支持 CEC 切换器或视频处理类型

返回值
======

成功时返回 0，错误时返回 -1 并且设置适当的 ``errno`` 变量。通用错误代码在 :ref:`通用错误代码 <gen-errors>` 章节中描述。
`:ref:`ioctl CEC_ADAP_S_LOG_ADDRS <CEC_ADAP_S_LOG_ADDRS>` 可以返回以下错误代码：

ENOTTY
    未设置 `CEC_CAP_LOG_ADDRS` 能力，因此此 ioctl 不受支持

EBUSY
    CEC 适配器当前正在配置自身，或者已经配置完毕且 `num_log_addrs` 非零，或者另一个文件句柄处于独占跟随者或发起者模式，或者文件句柄处于 `CEC_MODE_NO_INITIATOR` 模式

EINVAL
    `struct cec_log_addrs` 的内容无效
