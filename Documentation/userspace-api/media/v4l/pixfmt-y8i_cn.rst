SPDX 许可证标识符: GFDL-1.1-no-invariants-or-later

.. _V4L2-PIX-FMT-Y8I:

*************************
V4L2_PIX_FMT_Y8I ('Y8I ')
*************************

交错的灰度图像，例如来自立体对

描述
===========

这是一种灰度图像，每个像素的深度为 8 位，但两个来源的像素以交错方式存储。每个像素存储在一个 16 位字中。例如，R200 RealSense 相机将左侧传感器的像素存储在较低的 8 位中，右侧传感器的像素存储在较高的 8 位中。
**字节顺序：**
每个单元格为一个字节
.. flat-table::
    :header-rows:  0
    :stub-columns: 0

    * - 起始位置 + 0:
      - Y'\ :sub:`00left`
      - Y'\ :sub:`00right`
      - Y'\ :sub:`01left`
      - Y'\ :sub:`01right`
      - Y'\ :sub:`02left`
      - Y'\ :sub:`02right`
      - Y'\ :sub:`03left`
      - Y'\ :sub:`03right`
    * - 起始位置 + 8:
      - Y'\ :sub:`10left`
      - Y'\ :sub:`10right`
      - Y'\ :sub:`11left`
      - Y'\ :sub:`11right`
      - Y'\ :sub:`12left`
      - Y'\ :sub:`12right`
      - Y'\ :sub:`13left`
      - Y'\ :sub:`13right`
    * - 起始位置 + 16:
      - Y'\ :sub:`20left`
      - Y'\ :sub:`20right`
      - Y'\ :sub:`21left`
      - Y'\ :sub:`21right`
      - Y'\ :sub:`22left`
      - Y'\ :sub:`22right`
      - Y'\ :sub:`23left`
      - Y'\ :sub:`23right`
    * - 起始位置 + 24:
      - Y'\ :sub:`30left`
      - Y'\ :sub:`30right`
      - Y'\ :sub:`31left`
      - Y'\ :sub:`31right`
      - Y'\ :sub:`32left`
      - Y'\ :sub:`32right`
      - Y'\ :sub:`33left`
      - Y'\ :sub:`33right`
