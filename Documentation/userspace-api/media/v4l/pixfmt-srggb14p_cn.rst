SPDX 许可证标识符: GFDL-1.1-no-invariants-or-later

.. _V4L2-PIX-FMT-SRGGB14P:
.. _v4l2-pix-fmt-sbggr14p:
.. _v4l2-pix-fmt-sgbrg14p:
.. _v4l2-pix-fmt-sgrbg14p:

*******************************************************************************************************************************
V4L2_PIX_FMT_SRGGB14P ('pREE'), V4L2_PIX_FMT_SGRBG14P ('pgEE'), V4L2_PIX_FMT_SGBRG14P ('pGEE'), V4L2_PIX_FMT_SBGGR14P ('pBEE')
*******************************************************************************************************************************

*man V4L2_PIX_FMT_SRGGB14P(2)*

V4L2_PIX_FMT_SGRBG14P  
V4L2_PIX_FMT_SGBRG14P  
V4L2_PIX_FMT_SBGGR14P  
14位压缩的 Bayer 格式

描述
====

这四种像素格式是压缩的原始 sRGB / Bayer 格式，每种颜色有 14 位。每四个连续的样本被压缩到七个字节中。前四个字节分别包含每个像素的高八位，随后的三个字节包含每个像素的低六位，顺序相同。
每个 n 像素行包含 n/2 个绿色样本和 n/2 个蓝色或红色样本，交替排列绿色-红色和绿色-蓝色的行。它们通常被描述为 GRGR... BGBG..., RGRG... GBGB..., 等等。以下是一个这样的格式示例：

**字节顺序。**
每个单元格是一个字节
.. raw:: latex

    \begingroup
    \footnotesize
    \setlength{\tabcolsep}{2pt}

.. tabularcolumns:: |p{1.6cm}|p{1.0cm}|p{1.0cm}|p{1.0cm}|p{1.0cm}|p{3.5cm}|p{3.5cm}|p{3.5cm}|

.. flat-table::
    :header-rows:  0
    :stub-columns: 0
    :widths:       2 1 1 1 1 3 3 3


    -  .. row 1

       -  start + 0

       -  B\ :sub:`00high`

       -  G\ :sub:`01high`

       -  B\ :sub:`02high`

       -  G\ :sub:`03high`

       -  G\ :sub:`01low bits 1--0`\ (bits 7--6)

	  B\ :sub:`00low bits 5--0`\ (bits 5--0)

       -  B\ :sub:`02low bits 3--0`\ (bits 7--4)

	  G\ :sub:`01low bits 5--2`\ (bits 3--0)

       -  G\ :sub:`03low bits 5--0`\ (bits 7--2)

	  B\ :sub:`02low bits 5--4`\ (bits 1--0)

    -  .. row 2

       -  start + 7

       -  G\ :sub:`10high`

       -  R\ :sub:`11high`

       -  G\ :sub:`12high`

       -  R\ :sub:`13high`

       -  R\ :sub:`11low bits 1--0`\ (bits 7--6)

	  G\ :sub:`10low bits 5--0`\ (bits 5--0)

       -  G\ :sub:`12low bits 3--0`\ (bits 7--4)

	  R\ :sub:`11low bits 5--2`\ (bits 3--0)

       -  R\ :sub:`13low bits 5--0`\ (bits 7--2)

	  G\ :sub:`12low bits 5--4`\ (bits 1--0)

    -  .. row 3

       -  start + 14

       -  B\ :sub:`20high`

       -  G\ :sub:`21high`

       -  B\ :sub:`22high`

       -  G\ :sub:`23high`

       -  G\ :sub:`21low bits 1--0`\ (bits 7--6)

	  B\ :sub:`20low bits 5--0`\ (bits 5--0)

       -  B\ :sub:`22low bits 3--0`\ (bits 7--4)

	  G\ :sub:`21low bits 5--2`\ (bits 3--0)

       -  G\ :sub:`23low bits 5--0`\ (bits 7--2)

	  B\ :sub:`22low bits 5--4`\ (bits 1--0)

    -  .. row 4

       -  start + 21

       -  G\ :sub:`30high`

       -  R\ :sub:`31high`

       -  G\ :sub:`32high`

       -  R\ :sub:`33high`

       -  R\ :sub:`31low bits 1--0`\ (bits 7--6)
	  G\ :sub:`30low bits 5--0`\ (bits 5--0)

       -  G\ :sub:`32low bits 3--0`\ (bits 7--4)
	  R\ :sub:`31low bits 5--2`\ (bits 3--0)

       -  R\ :sub:`33low bits 5--0`\ (bits 7--2)
	  G\ :sub:`32low bits 5--4`\ (bits 1--0)

.. raw:: latex

    \endgroup
