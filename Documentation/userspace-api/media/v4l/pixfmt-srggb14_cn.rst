``SPDX 许可证标识符: GFDL-1.1-no-invariants-or-later``

``V4L2-PIX-FMT-SRGGB14``
``v4l2-pix-fmt-sbggr14``
``v4l2-pix-fmt-sgbrg14``
``v4l2-pix-fmt-sgrbg14``

***************************************************************************************************************************
``V4L2_PIX_FMT_SRGGB14 ('RG14')``, ``V4L2_PIX_FMT_SGRBG14 ('GR14')``, ``V4L2_PIX_FMT_SGBRG14 ('GB14')``, ``V4L2_PIX_FMT_SBGGR14 ('BG14')``
***************************************************************************************************************************

========================================
扩展为 16 位的 14 位 Bayer 格式
========================================

描述
===========

这四种像素格式是具有每种颜色 14 位的原始 sRGB / Bayer 格式。每个样本存储在一个 16 位字中，两个未使用的高位用零填充。每个 n 像素行包含 n/2 个绿色样本和 n/2 个蓝色或红色样本，交替排列红蓝行。字节以小端字节序存储在内存中。它们通常被描述为 GRGR... BGBG..., RGRG... GBGB..., 等等。下面是一个小的 V4L2_PIX_FMT_SBGGR14 图像示例：

**字节顺序：**
每个单元格表示一个字节，高字节中的两个最高位为零。
.. flat-table::
    :header-rows:  0
    :stub-columns: 0
    :widths:       2 1 1 1 1 1 1 1 1

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
