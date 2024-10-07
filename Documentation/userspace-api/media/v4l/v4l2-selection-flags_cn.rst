.. SPDX-License-Identifier: GFDL-1.1-no-invariants-or-later

.. _v4l2-selection-flags:

***************
选择标志
***************

.. _v4l2-selection-flags-table:

.. raw:: latex

   \small

.. tabularcolumns:: |p{5.6cm}|p{2.0cm}|p{6.5cm}|p{1.2cm}|p{1.2cm}|

.. cssclass:: longtable

.. flat-table:: 选择标志定义
    :header-rows:  1
    :stub-columns: 0

    * - 标志名称
      - ID
      - 定义
      - 对V4L2有效
      - 对V4L2子设备有效
    * - ``V4L2_SEL_FLAG_GE``
      - (1 << 0)
      - 建议驱动程序选择大于或等于请求大小的矩形。尽管驱动程序可能会选择较小的大小，但仅是由于硬件限制所致。如果没有此标志（和``V4L2_SEL_FLAG_LE``），行为将是选择尽可能接近的矩形。
      - 是
      - 是
    * - ``V4L2_SEL_FLAG_LE``
      - (1 << 1)
      - 建议驱动程序选择小于或等于请求大小的矩形。尽管驱动程序可能会选择较大的大小，但仅是由于硬件限制所致。
      - 是
      - 是
    * - ``V4L2_SEL_FLAG_KEEP_CONFIG``
      - (1 << 2)
      - 配置不得传播到任何进一步的处理步骤。如果未指定此标志，则配置将在子设备内传播到所有进一步的处理步骤。
      - 否
      - 是

.. raw:: latex

   \normalsize
