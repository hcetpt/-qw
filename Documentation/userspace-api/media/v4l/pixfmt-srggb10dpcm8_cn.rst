.. SPDX 许可证标识符: GFDL-1.1-no-invariants-or-later

.. _V4L2-PIX-FMT-SBGGR10DPCM8:
.. _v4l2-pix-fmt-sgbrg10dpcm8:
.. _v4l2-pix-fmt-sgrbg10dpcm8:
.. _v4l2-pix-fmt-srggb10dpcm8:

***********************************************************************************************************************************************
V4L2_PIX_FMT_SBGGR10DPCM8 ('bBA8'), V4L2_PIX_FMT_SGBRG10DPCM8 ('bGA8'), V4L2_PIX_FMT_SGRBG10DPCM8 ('BD10'), V4L2_PIX_FMT_SRGGB10DPCM8 ('bRA8'),
***********************************************************************************************************************************************

*man V4L2_PIX_FMT_SBGGR10DPCM8(2)*

V4L2_PIX_FMT_SGBRG10DPCM8
V4L2_PIX_FMT_SGRBG10DPCM8
V4L2_PIX_FMT_SRGGB10DPCM8
10 位 Bayer 格式压缩到 8 位

描述
=====

这四种像素格式是原始的 sRGB/Bayer 格式，每种颜色使用 10 位压缩到 8 位，采用 DPCM 压缩。DPCM（差分脉冲编码调制）是有损的。每个颜色分量占用 8 位内存。在其他方面，这种格式类似于 :ref:`V4L2-PIX-FMT-SRGGB10`
