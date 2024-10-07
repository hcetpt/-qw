SPDX 许可证标识符: GFDL-1.1-no-invariants-or-later

.. _packed-hsv:

******************
压缩的 HSV 格式
******************

描述
====

*色调*（h）以度为单位进行测量，度数与最低有效位（LSB）之间的等效关系取决于所使用的 hsv 编码方式，请参阅 :ref:`colorspaces`
*饱和度*（s）和 *值*（v）以柱体的百分比来测量：0 是最小值，255 是最大值
这些值被压缩到 24 位或 32 位格式中
.. raw:: latex

    \begingroup
    \tiny
    \setlength{\tabcolsep}{2pt}

.. tabularcolumns:: |p{2.6cm}|p{0.8cm}|p{0.22cm}|p{0.22cm}|p{0.22cm}|p{0.22cm}|p{0.22cm}|p{0.22cm}|p{0.22cm}|p{0.22cm}|p{0.22cm}|p{0.22cm}|p{0.22cm}|p{0.22cm}|p{0.22cm}|p{0.22cm}|p{0.22cm}|p{0.22cm}|p{0.22cm}|p{0.22cm}|p{0.22cm}|p{0.22cm}|p{0.22cm}|p{0.22cm}|p{0.22cm}|p{0.22cm}|p{0.22cm}|p{0.22cm}|p{0.22cm}|p{0.22cm}|p{0.22cm}|p{0.22cm}|p{0.22cm}|p{0.22cm}|p{0.22cm}|

.. _packed-hsv-formats:

.. flat-table:: 压缩的 HSV 图像格式
    :header-rows:  2
    :stub-columns: 0

    * - 标识符
      - 代码
      -
      - :cspan:`7` 内存中的字节 0
      - :cspan:`7` 字节 1
      - :cspan:`7` 字节 2
      - :cspan:`7` 字节 3
    * -
      -
      - 位
      - 7
      - 6
      - 5
      - 4
      - 3
      - 2
      - 1
      - 0

      - 7
      - 6
      - 5
      - 4
      - 3
      - 2
      - 1
      - 0

      - 7
      - 6
      - 5
      - 4
      - 3
      - 2
      - 1
      - 0

      - 7
      - 6
      - 5
      - 4
      - 3
      - 2
      - 1
      - 0
    * .. _V4L2-PIX-FMT-HSV32:

      - ``V4L2_PIX_FMT_HSV32``
      - 'HSV4'
      -
      -
      -
      -
      -
      -
      -
      -

      - h\ :sub:`7`
      - h\ :sub:`6`
      - h\ :sub:`5`
      - h\ :sub:`4`
      - h\ :sub:`3`
      - h\ :sub:`2`
      - h\ :sub:`1`
      - h\ :sub:`0`

      - s\ :sub:`7`
      - s\ :sub:`6`
      - s\ :sub:`5`
      - s\ :sub:`4`
      - s\ :sub:`3`
      - s\ :sub:`2`
      - s\ :sub:`1`
      - s\ :sub:`0`

      - v\ :sub:`7`
      - v\ :sub:`6`
      - v\ :sub:`5`
      - v\ :sub:`4`
      - v\ :sub:`3`
      - v\ :sub:`2`
      - v\ :sub:`1`
      - v\ :sub:`0`
    * .. _V4L2-PIX-FMT-HSV24:

      - ``V4L2_PIX_FMT_HSV24``
      - 'HSV3'
      -
      - h\ :sub:`7`
      - h\ :sub:`6`
      - h\ :sub:`5`
      - h\ :sub:`4`
      - h\ :sub:`3`
      - h\ :sub:`2`
      - h\ :sub:`1`
      - h\ :sub:`0`

      - s\ :sub:`7`
      - s\ :sub:`6`
      - s\ :sub:`5`
      - s\ :sub:`4`
      - s\ :sub:`3`
      - s\ :sub:`2`
      - s\ :sub:`1`
      - s\ :sub:`0`

      - v\ :sub:`7`
      - v\ :sub:`6`
      - v\ :sub:`5`
      - v\ :sub:`4`
      - v\ :sub:`3`
      - v\ :sub:`2`
      - v\ :sub:`1`
      - v\ :sub:`0`
      -

.. raw:: latex

    \endgroup

位 7 是最高有效位
