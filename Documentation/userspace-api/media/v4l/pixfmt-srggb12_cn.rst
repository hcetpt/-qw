``SPDX 许可证标识符: GFDL-1.1-no-invariants-or-later``

``V4L2-PIX-FMT-SRGGB12``
``v4l2-pix-fmt-sbggr12``
``v4l2-pix-fmt-sgbrg12``
``v4l2-pix-fmt-sgrbg12``

***************************************************************************************************************************
``V4L2_PIX_FMT_SRGGB12 ('RG12')``, ``V4L2_PIX_FMT_SGRBG12 ('BA12')``, ``V4L2_PIX_FMT_SGBRG12 ('GB12')``, ``V4L2_PIX_FMT_SBGGR12 ('BG12')``
***************************************************************************************************************************

``V4L2_PIX_FMT_SGRBG12``
``V4L2_PIX_FMT_SGBRG12``
``V4L2_PIX_FMT_SBGGR12``
12位 Bayer 格式扩展到 16 位

描述
====

这四种像素格式是带有 12 位颜色的原始 sRGB / Bayer 格式。每个颜色分量存储在一个 16 位字中，其中 4 个高位未使用的位填充为零。每行 n 个像素包含 n/2 个绿色样本和 n/2 个蓝色或红色样本，并且红色和蓝色行交替出现。字节以小端字节序存储在内存中。它们通常表示为 GRGR... BGBG..., RGRG... GBGB... 等。下面是一个小的 V4L2_PIX_FMT_SBGGR12 图像示例：

**字节顺序。**
每个单元格是一个字节，高字节的 4 个最高有效位为零。
.. flat-table::
    :header-rows:  0
    :stub-columns: 0

    * - 起始 + 0：
      - B\ :sub:`00low`
      - B\ :sub:`00high`
      - G\ :sub:`01low`
      - G\ :sub:`01high`
      - B\ :sub:`02low`
      - B\ :sub:`02high`
      - G\ :sub:`03low`
      - G\ :sub:`03high`
    * - 起始 + 8：
      - G\ :sub:`10low`
      - G\ :sub:`10high`
      - R\ :sub:`11low`
      - R\ :sub:`11high`
      - G\ :sub:`12low`
      - G\ :sub:`12high`
      - R\ :sub:`13low`
      - R\ :sub:`13high`
    * - 起始 + 16：
      - B\ :sub:`20low`
      - B\ :sub:`20high`
      - G\ :sub:`21low`
      - G\ :sub:`21high`
      - B\ :sub:`22low`
      - B\ :sub:`22high`
      - G\ :sub:`23low`
      - G\ :sub:`23high`
    * - 起始 + 24：
      - G\ :sub:`30low`
      - G\ :sub:`30high`
      - R\ :sub:`31low`
      - R\ :sub:`31high`
      - G\ :sub:`32low`
      - G\ :sub:`32high`
      - R\ :sub:`33low`
      - R\ :sub:`33high`
