.. SPDX-License-Identifier: GFDL-1.1-no-invariants-or-later

.. _V4L2-PIX-FMT-UV8:

************************
V4L2_PIX_FMT_UV8 ('UV8')
************************

UV平面交错

描述
===========

在此格式中，没有Y平面，只有CbCr平面（即UV交错）。

**字节顺序。**
每个单元格为一个字节
.. flat-table::
    :header-rows:  0
    :stub-columns: 0

    * - 起始 + 0:
      - Cb\ :sub:`00`
      - Cr\ :sub:`00`
      - Cb\ :sub:`01`
      - Cr\ :sub:`01`
    * - 起始 + 4:
      - Cb\ :sub:`10`
      - Cr\ :sub:`10`
      - Cb\ :sub:`11`
      - Cr\ :sub:`11`
    * - 起始 + 8:
      - Cb\ :sub:`20`
      - Cr\ :sub:`20`
      - Cb\ :sub:`21`
      - Cr\ :sub:`21`
    * - 起始 + 12:
      - Cb\ :sub:`30`
      - Cr\ :sub:`30`
      - Cb\ :sub:`31`
      - Cr\ :sub:`31`
