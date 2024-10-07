SPDX 许可声明：GFDL-1.1-no-invariants-or-later

.. _V4L2-TCH-FMT-TU08:

**************************
V4L2_TCH_FMT_TU08 ('TU08')
**************************

*man V4L2_TCH_FMT_TU08(2)*

8 位无符号原始触摸数据

描述
====

此格式表示来自触摸控制器的 8 位无符号数据。
这可用于输出原始数据和参考数据。值范围从 0 到 255。
**字节顺序。**
每个单元格为一个字节。

.. flat-table::
    :header-rows:  0
    :stub-columns: 0
    :widths:       2 1 1 1 1

    * - start + 0:
      - R'\ :sub:`00`
      - R'\ :sub:`01`
      - R'\ :sub:`02`
      - R'\ :sub:`03`
    * - start + 4:
      - R'\ :sub:`10`
      - R'\ :sub:`11`
      - R'\ :sub:`12`
      - R'\ :sub:`13`
    * - start + 8:
      - R'\ :sub:`20`
      - R'\ :sub:`21`
      - R'\ :sub:`22`
      - R'\ :sub:`23`
    * - start + 12:
      - R'\ :sub:`30`
      - R'\ :sub:`31`
      - R'\ :sub:`32`
      - R'\ :sub:`33`
