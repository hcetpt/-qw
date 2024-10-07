.. SPDX-License-Identifier: GFDL-1.1-no-invariants-or-later

.. _v4l2-selection-targets:

*****************
选择目标
*****************

选择目标的确切含义可能取决于它们是在两个接口中的哪一个中使用。
.. _v4l2-selection-targets-table:

.. raw:: latex

   \small

.. tabularcolumns:: |p{6.2cm}|p{1.4cm}|p{7.3cm}|p{1.2cm}|p{0.8cm}|

.. cssclass:: longtable

.. flat-table:: 选择目标定义
    :header-rows:  1
    :stub-columns: 0

    * - 目标名称
      - ID
      - 定义
      - V4L2有效
      - V4L2子设备有效
    * - ``V4L2_SEL_TGT_CROP``
      - 0x0000
      - 裁剪矩形。定义裁剪区域
- 是
      - 是
    * - ``V4L2_SEL_TGT_CROP_DEFAULT``
      - 0x0001
      - 建议的覆盖“整个画面”的裁剪矩形
这仅包括活动像素，排除其他非活动像素（如黑色像素）
- 是
      - 是
    * - ``V4L2_SEL_TGT_CROP_BOUNDS``
      - 0x0002
      - 裁剪矩形的边界。所有有效的裁剪矩形都必须在裁剪边界内
- 是
      - 是
    * - ``V4L2_SEL_TGT_NATIVE_SIZE``
      - 0x0003
      - 设备的本机尺寸，例如传感器的像素阵列
此目标的“left”和“top”字段为零
- 是
      - 是
    * - ``V4L2_SEL_TGT_COMPOSE``
      - 0x0100
      - 组合矩形。用于配置缩放和平铺
- 是
      - 是
    * - ``V4L2_SEL_TGT_COMPOSE_DEFAULT``
      - 0x0101
      - 建议的覆盖“整个画面”的组合矩形
- 是
      - 否
    * - ``V4L2_SEL_TGT_COMPOSE_BOUNDS``
      - 0x0102
      - 组合矩形的边界。所有有效的组合矩形都必须在组合边界内
是
- 是
* - ``V4L2_SEL_TGT_COMPOSE_PADDED``
  - 0x0103
  - 由硬件插入或修改的活动区域和所有填充像素
- 是
  - 否

.. raw:: latex

   \normalsize
