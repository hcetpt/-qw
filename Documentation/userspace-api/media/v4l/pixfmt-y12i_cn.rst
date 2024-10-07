SPDX 许可证标识符: GFDL-1.1-no-invariants-or-later

.. _V4L2-PIX-FMT-Y12I:

**************************
V4L2_PIX_FMT_Y12I ('Y12I')
**************************

交错的灰度图像，例如来自立体对

描述
===========

这是一种每个像素深度为 12 位的灰度图像，但两个来源的像素交错并位打包。每个像素以小端字节序存储在一个 24 位的字中。在小端字节序机器上，可以使用以下方法解交织这些像素：

.. code-block:: c

    __u8 *buf;
    left0 = 0xfff & *(__u16 *)buf;
    right0 = *(__u16 *)(buf + 1) >> 4;

**位打包表示。**
像素跨越字节边界，并且每组交错像素占用 3 字节
.. flat-table::
    :header-rows:  0
    :stub-columns: 0

    * - Y'\ :sub:`0left[7:0]`
      - Y'\ :sub:`0right[3:0]`\ Y'\ :sub:`0left[11:8]`
      - Y'\ :sub:`0right[11:4]`
