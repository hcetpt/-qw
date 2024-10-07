SPDX 许可证标识符: GFDL-1.1-no-invariants-or-later

.. _packed-yuv:

******************
打包的 YUV 格式
******************

与打包的 RGB 格式类似，打包的 YUV 格式将 Y、Cb 和 Cr 组件依次存储在内存中。它们可能对色度分量应用下采样，因此这些格式在交织三个分量的方式上有所不同。
.. note::

   - 在以下所有表格中，位 7 是字节中的最高有效位。
   - 'Y'、'Cb' 和 'Cr' 分别表示亮度、蓝色色度（也称为 'U'）和红色色度（也称为 'V'）分量的位。'A' 表示 alpha 分量（如果格式支持的话）的位，而 'X' 表示填充位。

4:4:4 下采样
=================

这些格式不对其色度分量进行下采样，并以完整的 Y、Cb 和 Cr 值三元组形式存储每个像素。
下表列出了每个分量少于 8 位的打包 YUV 4:4:4 格式。这些格式基于 Y、Cb 和 Cr 组件在 16 位字中的顺序命名，该字按小端字节顺序存储在内存中，并基于每个分量的位数。例如，YUV565 格式在一个 16 位字 [15:0] 中布局为 [Y'\ :sub:`4-0` Cb\ :sub:`5-0` Cr\ :sub:`4-0` ]，并在内存中存储为两个字节，[Cb\ :sub:`2-0` Cr\ :sub:`4-0` ] 接着是 [Y'\ :sub:`4-0` Cb\ :sub:`5-3` ]。
.. raw:: latex

    \begingroup
    \scriptsize
    \setlength{\tabcolsep}{2pt}

.. tabularcolumns:: |p{3.5cm}|p{0.96cm}|p{0.52cm}|p{0.52cm}|p{0.52cm}|p{0.52cm}|p{0.52cm}|p{0.52cm}|p{0.52cm}|p{0.52cm}|p{0.52cm}|p{0.52cm}|p{0.52cm}|p{0.52cm}|p{0.52cm}|p{0.52cm}|p{0.52cm}|p{0.52cm}|

.. flat-table:: 打包的 YUV 4:4:4 图像格式（少于 8 位/分量）
    :header-rows:  2
    :stub-columns: 0

    * - 标识符
      - 代码

      - :cspan:`7` 内存中的第 0 字节

      - :cspan:`7` 第 1 字节

    * -
      -
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

    * .. _V4L2-PIX-FMT-YUV444:

      - ``V4L2_PIX_FMT_YUV444``
      - 'Y444'

      - Cb\ :sub:`3`
      - Cb\ :sub:`2`
      - Cb\ :sub:`1`
      - Cb\ :sub:`0`
      - Cr\ :sub:`3`
      - Cr\ :sub:`2`
      - Cr\ :sub:`1`
      - Cr\ :sub:`0`

      - a\ :sub:`3`
      - a\ :sub:`2`
      - a\ :sub:`1`
      - a\ :sub:`0`
      - Y'\ :sub:`3`
      - Y'\ :sub:`2`
      - Y'\ :sub:`1`
      - Y'\ :sub:`0`

    * .. _V4L2-PIX-FMT-YUV555:

      - ``V4L2_PIX_FMT_YUV555``
      - 'YUVO'

      - Cb\ :sub:`2`
      - Cb\ :sub:`1`
      - Cb\ :sub:`0`
      - Cr\ :sub:`4`
      - Cr\ :sub:`3`
      - Cr\ :sub:`2`
      - Cr\ :sub:`1`
      - Cr\ :sub:`0`

      - a
      - Y'\ :sub:`4`
      - Y'\ :sub:`3`
      - Y'\ :sub:`2`
      - Y'\ :sub:`1`
      - Y'\ :sub:`0`
      - Cb\ :sub:`4`
      - Cb\ :sub:`3`

    * .. _V4L2-PIX-FMT-YUV565:

      - ``V4L2_PIX_FMT_YUV565``
      - 'YUVP'

      - Cb\ :sub:`2`
      - Cb\ :sub:`1`
      - Cb\ :sub:`0`
      - Cr\ :sub:`4`
      - Cr\ :sub:`3`
      - Cr\ :sub:`2`
      - Cr\ :sub:`1`
      - Cr\ :sub:`0`

      - Y'\ :sub:`4`
      - Y'\ :sub:`3`
      - Y'\ :sub:`2`
      - Y'\ :sub:`1`
      - Y'\ :sub:`0`
      - Cb\ :sub:`5`
      - Cb\ :sub:`4`
      - Cb\ :sub:`3`

.. raw:: latex

    \endgroup

.. note::

    对于 YUV444 和 YUV555 格式，在从驱动程序读取时 alpha 位的值是未定义的，在写入驱动程序时会被忽略，除非已协商使用 alpha 融合的 :ref:`视频覆盖 <overlay>` 或 :ref:`视频输出覆盖 <osd>`。

下表列出了每个分量具有 8 位的打包 YUV 4:4:4 格式。这些格式基于 Y、Cb 和 Cr 组件在内存中的存储顺序以及每像素总位数来命名。例如，VUYX32 格式将 Cr\ :sub:`7-0` 存储在第一个字节，Cb\ :sub:`7-0` 存储在第二个字节，Y'\ :sub:`7-0` 存储在第三个字节。
.. flat-table:: 打包的 YUV 图像格式（8 位/分量）
    :header-rows: 1
    :stub-columns: 0

    * - 标识符
      - 代码
      - 第 0 字节
      - 第 1 字节
      - 第 2 字节
      - 第 3 字节

    * .. _V4L2-PIX-FMT-YUV32:

      - ``V4L2_PIX_FMT_YUV32``
      - 'YUV4'

      - A\ :sub:`7-0`
      - Y'\ :sub:`7-0`
      - Cb\ :sub:`7-0`
      - Cr\ :sub:`7-0`

    * .. _V4L2-PIX-FMT-AYUV32:

      - ``V4L2_PIX_FMT_AYUV32``
      - 'AYUV'

      - A\ :sub:`7-0`
      - Y'\ :sub:`7-0`
      - Cb\ :sub:`7-0`
      - Cr\ :sub:`7-0`

    * .. _V4L2-PIX-FMT-XYUV32:

      - ``V4L2_PIX_FMT_XYUV32``
      - 'XYUV'

      - X\ :sub:`7-0`
      - Y'\ :sub:`7-0`
      - Cb\ :sub:`7-0`
      - Cr\ :sub:`7-0`

    * .. _V4L2-PIX-FMT-VUYA32:

      - ``V4L2_PIX_FMT_VUYA32``
      - 'VUYA'

      - Cr\ :sub:`7-0`
      - Cb\ :sub:`7-0`
      - Y'\ :sub:`7-0`
      - A\ :sub:`7-0`

    * .. _V4L2-PIX-FMT-VUYX32:

      - ``V4L2_PIX_FMT_VUYX32``
      - 'VUYX'

      - Cr\ :sub:`7-0`
      - Cb\ :sub:`7-0`
      - Y'\ :sub:`7-0`
      - X\ :sub:`7-0`

    * .. _V4L2-PIX-FMT-YUVA32:

      - ``V4L2_PIX_FMT_YUVA32``
      - 'YUVA'

      - Y'\ :sub:`7-0`
      - Cb\ :sub:`7-0`
      - Cr\ :sub:`7-0`
      - A\ :sub:`7-0`

    * .. _V4L2-PIX-FMT-YUVX32:

      - ``V4L2_PIX_FMT_YUVX32``
      - 'YUVX'

      - Y'\ :sub:`7-0`
      - Cb\ :sub:`7-0`
      - Cr\ :sub:`7-0`
      - X\ :sub:`7-0`

    * .. _V4L2-PIX-FMT-YUV24:

      - ``V4L2_PIX_FMT_YUV24``
      - 'YUV3'

      - Y'\ :sub:`7-0`
      - Cb\ :sub:`7-0`
      - Cr\ :sub:`7-0`
      - -\

.. note::

    - Alpha 分量应包含有意义的值，可供驱动程序和应用程序使用。
    - 填充位包含未定义的值，必须由所有应用程序和驱动程序忽略。
下表列出了每个分量为12位的打包YUV 4:4:4格式。将每个分量的位数扩展到16位，高位数据在高字节，低位数据为零填充，并以小端序排列，存储一个像素需要6个字节。
.. flat-table:: 打包的YUV 4:4:4图像格式（12位/每分量）
    :header-rows: 1
    :stub-columns: 0

    * - 标识符
      - 编码
      - 字节0-1
      - 字节2-3
      - 字节4-5
      - 字节6-7
      - 字节8-9
      - 字节10-11

    * .. _V4L2-PIX-FMT-YUV48-12:

      - ``V4L2_PIX_FMT_YUV48_12``
      - 'Y312'

      - Y'\ :sub:`0`
      - Cb\ :sub:`0`
      - Cr\ :sub:`0`
      - Y'\ :sub:`1`
      - Cb\ :sub:`1`
      - Cr\ :sub:`1`

4:2:2 下采样
=============

这些格式通常被称为YUYV或YUY2，在水平方向上对色度分量进行2倍下采样，并将其存储在一个容器中。对于8位格式，该容器是32位；对于10+位格式，该容器是64位。每个分量大于8位的打包YUYV格式存储为四个小端序的16位字。每个字的最高有效位包含一个分量，最低有效位是零填充。
.. raw:: latex

    \footnotesize

.. tabularcolumns:: |p{3.4cm}|p{1.2cm}|p{0.8cm}|p{0.8cm}|p{0.8cm}|p{0.8cm}|p{0.8cm}|p{0.8cm}|p{0.8cm}|p{0.8cm}|

.. flat-table:: 打包的YUV 4:2:2格式（32位容器）
    :header-rows: 1
    :stub-columns: 0

    * - 标识符
      - 编码
      - 字节0
      - 字节1
      - 字节2
      - 字节3
      - 字节4
      - 字节5
      - 字节6
      - 字节7
    * .. _V4L2-PIX-FMT-UYVY:

      - ``V4L2_PIX_FMT_UYVY``
      - 'UYVY'

      - Cb\ :sub:`0`
      - Y'\ :sub:`0`
      - Cr\ :sub:`0`
      - Y'\ :sub:`1`
      - Cb\ :sub:`2`
      - Y'\ :sub:`2`
      - Cr\ :sub:`2`
      - Y'\ :sub:`3`
    * .. _V4L2-PIX-FMT-VYUY:

      - ``V4L2_PIX_FMT_VYUY``
      - 'VYUY'

      - Cr\ :sub:`0`
      - Y'\ :sub:`0`
      - Cb\ :sub:`0`
      - Y'\ :sub:`1`
      - Cr\ :sub:`2`
      - Y'\ :sub:`2`
      - Cb\ :sub:`2`
      - Y'\ :sub:`3`
    * .. _V4L2-PIX-FMT-YUYV:

      - ``V4L2_PIX_FMT_YUYV``
      - 'YUYV'

      - Y'\ :sub:`0`
      - Cb\ :sub:`0`
      - Y'\ :sub:`1`
      - Cr\ :sub:`0`
      - Y'\ :sub:`2`
      - Cb\ :sub:`2`
      - Y'\ :sub:`3`
      - Cr\ :sub:`2`
    * .. _V4L2-PIX-FMT-YVYU:

      - ``V4L2_PIX_FMT_YVYU``
      - 'YVYU'

      - Y'\ :sub:`0`
      - Cr\ :sub:`0`
      - Y'\ :sub:`1`
      - Cb\ :sub:`0`
      - Y'\ :sub:`2`
      - Cr\ :sub:`2`
      - Y'\ :sub:`3`
      - Cb\ :sub:`2`

.. tabularcolumns:: |p{3.4cm}|p{1.2cm}|p{0.8cm}|p{0.8cm}|p{0.8cm}|p{0.8cm}|p{0.8cm}|p{0.8cm}|p{0.8cm}|p{0.8cm}|

.. flat-table:: 打包的YUV 4:2:2格式（64位容器）
    :header-rows: 1
    :stub-columns: 0

    * - 标识符
      - 编码
      - 字0
      - 字1
      - 字2
      - 字3
    * .. _V4L2-PIX-FMT-Y210:

      - ``V4L2_PIX_FMT_Y210``
      - 'Y210'

      - Y'\ :sub:`0`（位15-6）
      - Cb\ :sub:`0`（位15-6）
      - Y'\ :sub:`1`（位15-6）
      - Cr\ :sub:`0`（位15-6）
    * .. _V4L2-PIX-FMT-Y212:

      - ``V4L2_PIX_FMT_Y212``
      - 'Y212'

      - Y'\ :sub:`0`（位15-4）
      - Cb\ :sub:`0`（位15-4）
      - Y'\ :sub:`1`（位15-4）
      - Cr\ :sub:`0`（位15-4）
    * .. _V4L2-PIX-FMT-Y216:

      - ``V4L2_PIX_FMT_Y216``
      - 'Y216'

      - Y'\ :sub:`0`（位15-0）
      - Cb\ :sub:`0`（位15-0）
      - Y'\ :sub:`1`（位15-0）
      - Cr\ :sub:`0`（位15-0）

.. raw:: latex

    \normalsize

**颜色样本位置：**
色度样本水平方向上位于 :ref:`interstitially sited<yuv-chroma-centered>`。

4:1:1 下采样
=============

这种格式在水平方向上对色度分量进行4倍下采样，并在12个字节中存储8个像素。
.. raw:: latex

    \scriptsize

.. tabularcolumns:: |p{2.9cm}|p{0.8cm}|p{0.5cm}|p{0.5cm}|p{0.5cm}|p{0.5cm}|p{0.5cm}|p{0.5cm}|p{0.5cm}|p{0.5cm}|p{0.5cm}|p{0.5cm}|p{0.5cm}|p{0.5cm}|

.. flat-table:: 打包的YUV 4:1:1格式
    :header-rows: 1
    :stub-columns: 0

    * - 标识符
      - 编码
      - 字节0
      - 字节1
      - 字节2
      - 字节3
      - 字节4
      - 字节5
      - 字节6
      - 字节7
      - 字节8
      - 字节9
      - 字节10
      - 字节11
    * .. _V4L2-PIX-FMT-Y41P:

      - ``V4L2_PIX_FMT_Y41P``
      - 'Y41P'

      - Cb\ :sub:`0`
      - Y'\ :sub:`0`
      - Cr\ :sub:`0`
      - Y'\ :sub:`1`
      - Cb\ :sub:`4`
      - Y'\ :sub:`2`
      - Cr\ :sub:`4`
      - Y'\ :sub:`3`
      - Y'\ :sub:`4`
      - Y'\ :sub:`5`
      - Y'\ :sub:`6`
      - Y'\ :sub:`7`

.. raw:: latex

    \normalsize

.. note::

    不要将 ``V4L2_PIX_FMT_Y41P`` 与 :ref:`V4L2_PIX_FMT_YUV411P <V4L2-PIX-FMT-YUV411P>` 混淆。Y41P 来自“YUV 4:1:1 **打包**”，而 YUV411P 表示“YUV 4:1:1 **平面**”。

**颜色样本位置：**
色度样本水平方向上位于 :ref:`interstitially sited<yuv-chroma-centered>`。
