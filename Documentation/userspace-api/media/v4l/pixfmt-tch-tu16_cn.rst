``SPDX 许可证标识符: GFDL-1.1-no-invariants-or-later``

.. _V4L2-TCH-FMT-TU16:

********************************
V4L2_TCH_FMT_TU16 ('TU16')
********************************

*man V4L2_TCH_FMT_TU16(2)*

16位无符号小端字节序的原始触摸数据

描述
===========

此格式表示来自触摸控制器的无符号16位数据。
这可用于输出原始数据和参考数据。值的范围可以从0到65535。
**字节序。**
每个单元格为一个字节
.. flat-table::
    :header-rows:  0
    :stub-columns: 0
    :widths:       2 1 1 1 1 1 1 1 1

    * - 起始位置 + 0:
      - R'\ :sub:`00low`
      - R'\ :sub:`00high`
      - R'\ :sub:`01low`
      - R'\ :sub:`01high`
      - R'\ :sub:`02low`
      - R'\ :sub:`02high`
      - R'\ :sub:`03low`
      - R'\ :sub:`03high`
    * - 起始位置 + 8:
      - R'\ :sub:`10low`
      - R'\ :sub:`10high`
      - R'\ :sub:`11low`
      - R'\ :sub:`11high`
      - R'\ :sub:`12low`
      - R'\ :sub:`12high`
      - R'\ :sub:`13low`
      - R'\ :sub:`13high`
    * - 起始位置 + 16:
      - R'\ :sub:`20low`
      - R'\ :sub:`20high`
      - R'\ :sub:`21low`
      - R'\ :sub:`21high`
      - R'\ :sub:`22low`
      - R'\ :sub:`22high`
      - R'\ :sub:`23low`
      - R'\ :sub:`23high`
    * - 起始位置 + 24:
      - R'\ :sub:`30low`
      - R'\ :sub:`30high`
      - R'\ :sub:`31low`
      - R'\ :sub:`31high`
      - R'\ :sub:`32low`
      - R'\ :sub:`32high`
      - R'\ :sub:`33low`
      - R'\ :sub:`33high`
