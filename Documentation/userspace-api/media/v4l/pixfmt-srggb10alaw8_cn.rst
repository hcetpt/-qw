SPDX 许可证标识符: GFDL-1.1-no-invariants-or-later

.. _V4L2-PIX-FMT-SBGGR10ALAW8:
.. _v4l2-pix-fmt-sgbrg10alaw8:
.. _v4l2-pix-fmt-sgrbg10alaw8:
.. _v4l2-pix-fmt-srggb10alaw8:

***********************************************************************************************************************************************
V4L2_PIX_FMT_SBGGR10ALAW8 ('aBA8')，V4L2_PIX_FMT_SGBRG10ALAW8 ('aGA8')，V4L2_PIX_FMT_SGRBG10ALAW8 ('agA8')，V4L2_PIX_FMT_SRGGB10ALAW8 ('aRA8')
***********************************************************************************************************************************************

V4L2_PIX_FMT_SGBRG10ALAW8
V4L2_PIX_FMT_SGRBG10ALAW8
V4L2_PIX_FMT_SRGGB10ALAW8
10 位 Bayer 格式压缩到 8 位

描述
===========

这四种像素格式是原始的 sRGB/Bayer 格式，每种颜色使用 10 位并压缩到 8 位，采用 A-LAW 算法。每个颜色分量占用 8 位内存。在其他方面，这种格式类似于 :ref:`V4L2-PIX-FMT-SRGGB8`
