SPDX 许可声明标识符: GFDL-1.1-no-invariants-or-later

.. _V4L2-TCH-FMT-DELTA-TD16:

********************************
V4L2_TCH_FMT_DELTA_TD16 ('TD16')
********************************

*man V4L2_TCH_FMT_DELTA_TD16(2)*

16位小端字节序触摸差值

描述
===========

此格式表示来自触摸控制器的差值数据。
差值范围可以从 -32768 到 32767。通常情况下，这些值会根据传感器是否被触摸而在一个小范围内变化。如果触摸屏节点之一出现故障或线路未连接，则可能会看到完整值。
**字节顺序：**
每个单元格为一个字节
.. flat-table::
    :header-rows:  0
    :stub-columns: 0
    :widths:       2 1 1 1 1 1 1 1 1

    * - 起始位置 + 0:
      - D'\ :sub:`00low`
      - D'\ :sub:`00high`
      - D'\ :sub:`01low`
      - D'\ :sub:`01high`
      - D'\ :sub:`02low`
      - D'\ :sub:`02high`
      - D'\ :sub:`03low`
      - D'\ :sub:`03high`
    * - 起始位置 + 8:
      - D'\ :sub:`10low`
      - D'\ :sub:`10high`
      - D'\ :sub:`11low`
      - D'\ :sub:`11high`
      - D'\ :sub:`12low`
      - D'\ :sub:`12high`
      - D'\ :sub:`13low`
      - D'\ :sub:`13high`
    * - 起始位置 + 16:
      - D'\ :sub:`20low`
      - D'\ :sub:`20high`
      - D'\ :sub:`21low`
      - D'\ :sub:`21high`
      - D'\ :sub:`22low`
      - D'\ :sub:`22high`
      - D'\ :sub:`23low`
      - D'\ :sub:`23high`
    * - 起始位置 + 24:
      - D'\ :sub:`30low`
      - D'\ :sub:`30high`
      - D'\ :sub:`31low`
      - D'\ :sub:`31high`
      - D'\ :sub:`32low`
      - D'\ :sub:`32high`
      - D'\ :sub:`33low`
      - D'\ :sub:`33high`
