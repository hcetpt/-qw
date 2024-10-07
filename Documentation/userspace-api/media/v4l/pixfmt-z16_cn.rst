SPDX 许可证标识符: GFDL-1.1-no-invariants-or-later

.. _V4L2-PIX-FMT-Z16:

*************************
V4L2_PIX_FMT_Z16 ('Z16 ')
*************************

这是一种每像素包含距离值的 16 位深度数据格式。

描述
===========

这是一个 16 位格式，表示深度数据。每个像素代表图像坐标中相应点的距离。距离单位可以不同，并且需要与设备单独协商。每个像素以小端字节序存储在一个 16 位字中。
**字节序：**
每个单元是一个字节。

.. flat-table::
    :header-rows:  0
    :stub-columns: 0

    * - 起始位置 + 0:
      - Z\ :sub:`00low`
      - Z\ :sub:`00high`
      - Z\ :sub:`01low`
      - Z\ :sub:`01high`
      - Z\ :sub:`02low`
      - Z\ :sub:`02high`
      - Z\ :sub:`03low`
      - Z\ :sub:`03high`
    * - 起始位置 + 8:
      - Z\ :sub:`10low`
      - Z\ :sub:`10high`
      - Z\ :sub:`11low`
      - Z\ :sub:`11high`
      - Z\ :sub:`12low`
      - Z\ :sub:`12high`
      - Z\ :sub:`13low`
      - Z\ :sub:`13high`
    * - 起始位置 + 16:
      - Z\ :sub:`20low`
      - Z\ :sub:`20high`
      - Z\ :sub:`21low`
      - Z\ :sub:`21high`
      - Z\ :sub:`22low`
      - Z\ :sub:`22high`
      - Z\ :sub:`23low`
      - Z\ :sub:`23high`
    * - 起始位置 + 24:
      - Z\ :sub:`30low`
      - Z\ :sub:`30high`
      - Z\ :sub:`31low`
      - Z\ :sub:`31high`
      - Z\ :sub:`32low`
      - Z\ :sub:`32high`
      - Z\ :sub:`33low`
      - Z\ :sub:`33high`
