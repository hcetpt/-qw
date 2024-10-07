``SPDX 许可证标识符: GFDL-1.1-no-invariants-or-later``

.. _V4L2-PIX-FMT-SRGGB10:
.. _v4l2-pix-fmt-sbggr10:
.. _v4l2-pix-fmt-sgbrg10:
.. _v4l2-pix-fmt-sgrbg10:

***************************************************************************************************************************
V4L2_PIX_FMT_SRGGB10 ('RG10')，V4L2_PIX_FMT_SGRBG10 ('BA10')，V4L2_PIX_FMT_SGBRG10 ('GB10')，V4L2_PIX_FMT_SBGGR10 ('BG10')
***************************************************************************************************************************

V4L2_PIX_FMT_SGRBG10  
V4L2_PIX_FMT_SGBRG10  
V4L2_PIX_FMT_SBGGR10  
10位 Bayer 格式扩展到 16 位

描述
====

这四种像素格式是具有每样本 10 位的原始 sRGB/Bayer 格式。每个样本存储在一个 16 位的字中，未使用的高 6 位填充为零。每行 n 个像素包含 n/2 个绿色样本和 n/2 个蓝色或红色样本，红色和蓝色行交替出现。字节在内存中以小端序存储。它们通常被描述为 GRGR... BGBG...，RGRG... GBGB... 等。下面是一个这些格式的例子：

**字节顺序。**
每个单元格表示一个字节，高位字节中的最高 6 位为 0。
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
