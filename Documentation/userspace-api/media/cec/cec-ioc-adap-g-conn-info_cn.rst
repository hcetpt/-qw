SPDX 许可声明标识符: GPL-2.0

版权所有 2019 Google LLC

命名空间: CEC

_CEC_ADAP_G_CONNECTOR_INFO_

=============================
ioctl CEC_ADAP_G_CONNECTOR_INFO
=============================

名称
====

CEC_ADAP_G_CONNECTOR_INFO - 查询 HDMI 连接器信息

概述
========

.. c:macro:: CEC_ADAP_G_CONNECTOR_INFO

``int ioctl(int fd, CEC_ADAP_G_CONNECTOR_INFO, struct cec_connector_info *argp)``

参数
=========

``fd``
    由 :c:func:`open()` 返回的文件描述符
``argp``
    指向 `cec_connector_info` 结构体的指针，该结构体将由内核填充适配器驱动程序提供的信息

描述
===========

使用此 ioctl 命令，应用程序可以了解此 CEC 设备对应的 HDMI 连接器。在调用此 ioctl 命令时，应用程序应提供一个指向 `cec_connector_info` 结构体的指针，该结构体将被内核填充适配器驱动程序提供的信息。此 ioctl 只有在设置了 `CEC_CAP_CONNECTOR_INFO` 功能时才可用。

.. tabularcolumns:: |p{1.0cm}|p{4.4cm}|p{2.5cm}|p{9.2cm}|

.. c:type:: cec_connector_info

.. flat-table:: struct cec_connector_info
    :header-rows:  0
    :stub-columns: 0
    :widths:       1 1 8

    * - __u32
      - ``type``
      - 此适配器关联的连接器类型
* - union {
      - ``(匿名)``
    * - ``struct cec_drm_connector_info``
      - drm
      - :ref:`cec-drm-connector-info`
    * - }
      -

.. tabularcolumns:: |p{4.4cm}|p{2.5cm}|p{10.4cm}|

.. _connector-type:

.. flat-table:: 连接器类型
    :header-rows:  0
    :stub-columns: 0
    :widths:       3 1 8

    * .. _`CEC-CONNECTOR-TYPE-NO-CONNECTOR`:

      - ``CEC_CONNECTOR_TYPE_NO_CONNECTOR``
      - 0
      - 无连接器与适配器关联/驱动程序未提供信息
* .. _`CEC-CONNECTOR-TYPE-DRM`:

      - ``CEC_CONNECTOR_TYPE_DRM``
      - 1
      - 表示与该适配器关联的是一个 DRM 连接器
有关连接器的信息可以在 :ref:`cec-drm-connector-info` 中找到

.. tabularcolumns:: |p{4.4cm}|p{2.5cm}|p{10.4cm}|

.. c:type:: cec_drm_connector_info

.. _cec-drm-connector-info:

.. flat-table:: struct cec_drm_connector_info
    :header-rows:  0
    :stub-columns: 0
    :widths:       3 1 8

    * .. _`CEC-DRM-CONNECTOR-TYPE-CARD-NO`:

      - __u32
      - ``card_no``
      - DRM 卡号：卡路径中的数字，例如 `/dev/card0` 中的 0
* .. _`CEC-DRM-CONNECTOR-TYPE-CONNECTOR_ID`:

      - __u32
      - ``connector_id``
      - DRM 连接器 ID
当然，请提供您需要翻译的文本。
