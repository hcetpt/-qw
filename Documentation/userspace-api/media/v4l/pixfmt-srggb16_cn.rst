``SPDX 许可证标识符: GFDL-1.1-no-invariants-or-later``

.. _V4L2-PIX-FMT-SRGGB16:
.. _v4l2-pix-fmt-sbggr16:
.. _v4l2-pix-fmt-sgbrg16:
.. _v4l2-pix-fmt-sgrbg16:

***************************************************************************************************************************
V4L2_PIX_FMT_SRGGB16 ('RG16'), V4L2_PIX_FMT_SGRBG16 ('GR16'), V4L2_PIX_FMT_SGBRG16 ('GB16'), V4L2_PIX_FMT_SBGGR16 ('BYR2')
***************************************************************************************************************************

====================
16位Bayer格式
====================

描述
===========

这四种像素格式是具有16位每样本的原始sRGB/Bayer格式。每个样本存储在一个16位字中。每个n像素行包含n/2个绿色样本和n/2个蓝色或红色样本，交替排列红色和蓝色行。字节在内存中以小端字节序存储。这些格式通常描述为GRGR... BGBG..., RGRG... GBGB...等。以下是一个小的V4L2_PIX_FMT_SBGGR16图像示例：

**字节顺序：**
每个单元格为一个字节
.. flat-table::
    :header-rows:  0
    :stub-columns: 0

    * - 起始 + 0:
      - B\ :sub:`00low`
      - B\ :sub:`00high`
      - G\ :sub:`01low`
      - G\ :sub:`01high`
      - B\ :sub:`02low`
      - B\ :sub:`02high`
      - G\ :sub:`03low`
      - G\ :sub:`03high`
    * - 起始 + 8:
      - G\ :sub:`10low`
      - G\ :sub:`10high`
      - R\ :sub:`11low`
      - R\ :sub:`11high`
      - G\ :sub:`12low`
      - G\ :sub:`12high`
      - R\ :sub:`13low`
      - R\ :sub:`13high`
    * - 起始 + 16:
      - B\ :sub:`20low`
      - B\ :sub:`20high`
      - G\ :sub:`21low`
      - G\ :sub:`21high`
      - B\ :sub:`22low`
      - B\ :sub:`22high`
      - G\ :sub:`23low`
      - G\ :sub:`23high`
    * - 起始 + 24:
      - G\ :sub:`30low`
      - G\ :sub:`30high`
      - R\ :sub:`31low`
      - R\ :sub:`31high`
      - G\ :sub:`32low`
      - G\ :sub:`32high`
      - R\ :sub:`33low`
      - R\ :sub:`33high`
