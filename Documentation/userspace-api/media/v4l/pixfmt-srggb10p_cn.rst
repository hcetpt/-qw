``SPDX 许可证标识符: GFDL-1.1-no-invariants-or-later``

.. _V4L2-PIX-FMT-SRGGB10P:
.. _v4l2-pix-fmt-sbggr10p:
.. _v4l2-pix-fmt-sgbrg10p:
.. _v4l2-pix-fmt-sgrbg10p:

*******************************************************************************************************************************
V4L2_PIX_FMT_SRGGB10P ('pRAA'), V4L2_PIX_FMT_SGRBG10P ('pgAA'), V4L2_PIX_FMT_SGBRG10P ('pGAA'), V4L2_PIX_FMT_SBGGR10P ('pBAA'),
*******************************************************************************************************************************

V4L2_PIX_FMT_SGRBG10P  
V4L2_PIX_FMT_SGBRG10P  
V4L2_PIX_FMT_SBGGR10P  
10 位打包 Bayer 格式

描述
===========

这四种像素格式是带有 10 位每样本的打包原始 sRGB/Bayer 格式。每四个连续的样本被打包到 5 字节中。前四个字节包含每个像素的高 8 位，第五个字节包含每个像素的低两位，顺序相同。

每一行包含 n/2 个绿色样本和 n/2 个蓝色或红色样本，交替出现绿色-红色和绿色-蓝色行。它们通常被描述为 GRGR... BGBG..., RGRG... GBGB... 等等。下面是一个小型 V4L2_PIX_FMT_SBGGR10P 图像的例子：

**字节顺序。**
每个单元格是一个字节。
.. tabularcolumns:: |p{2.4cm}|p{1.4cm}|p{1.2cm}|p{1.2cm}|p{1.2cm}|p{9.3cm}|

.. flat-table::
    :header-rows:  0
    :stub-columns: 0
    :widths: 12 8 8 8 8 68

    * - 起始 + 0:
      - B\ :sub:`00high`
      - G\ :sub:`01high`
      - B\ :sub:`02high`
      - G\ :sub:`03high`
      - G\ :sub:`03low`（位 7--6） B\ :sub:`02low`（位 5--4）

	G\ :sub:`01low`（位 3--2） B\ :sub:`00low`（位 1--0）
    * - 起始 + 5:
      - G\ :sub:`10high`
      - R\ :sub:`11high`
      - G\ :sub:`12high`
      - R\ :sub:`13high`
      - R\ :sub:`13low`（位 7--6） G\ :sub:`12low`（位 5--4）

	R\ :sub:`11low`（位 3--2） G\ :sub:`10low`（位 1--0）
    * - 起始 + 10:
      - B\ :sub:`20high`
      - G\ :sub:`21high`
      - B\ :sub:`22high`
      - G\ :sub:`23high`
      - G\ :sub:`23low`（位 7--6） B\ :sub:`22low`（位 5--4）

	G\ :sub:`21low`（位 3--2） B\ :sub:`20low`（位 1--0）
    * - 起始 + 15:
      - G\ :sub:`30high`
      - R\ :sub:`31high`
      - G\ :sub:`32high`
      - R\ :sub:`33high`
      - R\ :sub:`33low`（位 7--6） G\ :sub:`32low`（位 5--4）

	R\ :sub:`31low`（位 3--2） G\ :sub:`30low`（位 1--0）
