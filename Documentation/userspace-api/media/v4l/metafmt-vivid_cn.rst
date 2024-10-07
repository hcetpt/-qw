.. SPDX 许可证标识符: GPL-2.0 或 GFDL-1.1-no-invariants-or-later

.. _v4l2-meta-fmt-vivid:

*******************************
V4L2_META_FMT_VIVID ('VIVD')
*******************************

VIVID 元数据格式

描述
===========

这描述了由 vivid 驱动程序使用的元数据格式。
它设置了亮度、饱和度、对比度和色调，每个参数都对应于 vivid 驱动程序的相应控制，范围和默认值也相对应。
它包含以下字段：

.. flat-table:: VIVID 元数据
    :widths: 1 4
    :header-rows:  1
    :stub-columns: 0

    * - 字段
      - 描述
    * - u16 brightness;
      - 图像亮度，值的范围为 0 到 255，默认值为 128
    * - u16 contrast;
      - 图像对比度，值的范围为 0 到 255，默认值为 128
    * - u16 saturation;
      - 图像色彩饱和度，值的范围为 0 到 255，默认值为 128
    * - s16 hue;
      - 图像色彩平衡，值的范围为 -128 到 128，默认值为 0
