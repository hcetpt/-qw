.. SPDX 许可证标识符: GFDL-1.1-no-invariants-or-later

.. _V4L2-TCH-FMT-DELTA-TD08:

********************************
V4L2_TCH_FMT_DELTA_TD08 ('TD08')
********************************

*man V4L2_TCH_FMT_DELTA_TD08(2)*

8 位带符号的触摸差值

描述
===========

此格式表示来自触摸控制器的差值数据。
差值范围可能从 -128 到 127。通常，这些值会根据传感器是否被触摸而在一个小范围内变化。如果触摸屏节点之一出现故障或线路未连接，则可能会看到完整值。
**字节顺序。**
每个单元格为一个字节
.. flat-table::
    :header-rows:  0
    :stub-columns: 0
    :widths:       2 1 1 1 1

    * - start + 0:
      - D'\ :sub:`00`
      - D'\ :sub:`01`
      - D'\ :sub:`02`
      - D'\ :sub:`03`
    * - start + 4:
      - D'\ :sub:`10`
      - D'\ :sub:`11`
      - D'\ :sub:`12`
      - D'\ :sub:`13`
    * - start + 8:
      - D'\ :sub:`20`
      - D'\ :sub:`21`
      - D'\ :sub:`22`
      - D'\ :sub:`23`
    * - start + 12:
      - D'\ :sub:`30`
      - D'\ :sub:`31`
      - D'\ :sub:`32`
      - D'\ :sub:`33`
