SPDX 许可证标识符: GFDL-1.1-no-invariants-or-later

.. _V4L2-PIX-FMT-SRGGB12P:
.. _v4l2-pix-fmt-sbggr12p:
.. _v4l2-pix-fmt-sgbrg12p:
.. _v4l2-pix-fmt-sgrbg12p:

*******************************************************************************************************************************
V4L2_PIX_FMT_SRGGB12P ('pRCC'), V4L2_PIX_FMT_SGRBG12P ('pgCC'), V4L2_PIX_FMT_SGBRG12P ('pGCC'), V4L2_PIX_FMT_SBGGR12P ('pBCC')
*******************************************************************************************************************************

12位压缩 Bayer 格式
---------------------------

描述
====

这四种像素格式是压缩的原始 sRGB/Bayer 格式，每个颜色通道有12位。每两个连续的样本被压缩到三个字节中。前两个字节分别包含像素的高八位，第三个字节包含每个像素的低四位，顺序相同。

每一行 n 个像素包含 n/2 个绿色样本和 n/2 个蓝色或红色样本，绿色和红色交替排列，绿色和蓝色交替排列。它们通常表示为 GRGR... BGBG..., RGRG... GBGB... 等等。

下面是一个小的 V4L2_PIX_FMT_SBGGR12P 图像示例：

**字节顺序：**
每个单元格是一个字节

.. tabularcolumns:: |p{2.2cm}|p{1.2cm}|p{1.2cm}|p{3.1cm}|p{1.2cm}|p{1.2cm}|p{6.4cm}|


.. flat-table::
    :header-rows:  0
    :stub-columns: 0
    :widths:       2 1 1 1 1 1 1


    -  -  start + 0:
       -  B\ :sub:`00high`
       -  G\ :sub:`01high`
       -  G\ :sub:`01low`\ (bits 7--4)

          B\ :sub:`00low`\ (bits 3--0)
       -  B\ :sub:`02high`
       -  G\ :sub:`03high`
       -  G\ :sub:`03low`\ (bits 7--4)

          B\ :sub:`02low`\ (bits 3--0)

    -  -  start + 6:
       -  G\ :sub:`10high`
       -  R\ :sub:`11high`
       -  R\ :sub:`11low`\ (bits 7--4)

          G\ :sub:`10low`\ (bits 3--0)
       -  G\ :sub:`12high`
       -  R\ :sub:`13high`
       -  R\ :sub:`13low`\ (bits 7--4)

          G\ :sub:`12low`\ (bits 3--0)
    -  -  start + 12:
       -  B\ :sub:`20high`
       -  G\ :sub:`21high`
       -  G\ :sub:`21low`\ (bits 7--4)

          B\ :sub:`20low`\ (bits 3--0)
       -  B\ :sub:`22high`
       -  G\ :sub:`23high`
       -  G\ :sub:`23low`\ (bits 7--4)

          B\ :sub:`22low`\ (bits 3--0)
    -  -  start + 18:
       -  G\ :sub:`30high`
       -  R\ :sub:`31high`
       -  R\ :sub:`31low`\ (bits 7--4)

          G\ :sub:`30low`\ (bits 3--0)
       -  G\ :sub:`32high`
       -  R\ :sub:`33high`
       -  R\ :sub:`33low`\ (bits 7--4)

          G\ :sub:`32low`\ (bits 3--0)
