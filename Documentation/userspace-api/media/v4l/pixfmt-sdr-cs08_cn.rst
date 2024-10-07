.. SPDX-License-Identifier: GFDL-1.1-no-invariants-or-later

.. _v4l2-sdr-fmt-cs8:

*************************
V4L2_SDR_FMT_CS8 ('CS08')
*************************

复数8位有符号IQ样本

描述
===========

此格式包含一系列复数样本。每个复数由两部分组成，称为同相和正交分量（IQ）。I和Q都表示为8位有符号数。I值在前，Q值随后。
**字节顺序。**
每个单元格为一个字节
.. flat-table::
    :header-rows:  0
    :stub-columns: 0

    * - 起始 + 0:
      - I\ :sub:`0`
    * - 起始 + 1:
      - Q\ :sub:`0`
