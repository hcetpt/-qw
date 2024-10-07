SPDX 许可证标识符: GFDL-1.1-no-invariants-or-later

.. planar-yuv:

******************
平面 YUV 格式
******************

平面格式将亮度和色度数据分开存储在不同的内存区域。它们有两种变体：

- 半平面格式使用两个平面。第一个平面是亮度平面，存储 Y 分量。第二个平面是色度平面，存储交错的 Cb 和 Cr 分量。
- 完全平面格式使用三个平面分别存储 Y、Cb 和 Cr 分量。
在一个平面内，分量按照像素顺序存储，可能是线性的也可能是块状的。可以在行尾添加填充，并且色度平面的行跨度可能受到亮度平面行跨度的约束。
一些平面格式允许平面放置在独立的内存位置。它们在名称中以 'M' 后缀来标识（例如 `V4L2_PIX_FMT_NV12M`）。这些格式仅用于支持多平面 API 的驱动程序和应用程序，该 API 在 :ref:`planar-apis` 中描述。除非明确文档支持非连续平面，否则格式要求平面在内存中连续排列。

半平面 YUV 格式
=======================

这些格式通常称为 NV 格式（如 NV12、NV16 等）。它们使用两个平面，亮度分量存储在第一个平面中，色度分量存储在第二个平面中。Cb 和 Cr 分量在色度平面中交错存储，Cb 和 Cr 总是以对的形式存储。色度顺序以不同的格式表示。
对于内存连续格式，色度行末尾的填充像素数量与亮度行的填充相同。没有水平子采样时，色度行跨度（以字节为单位）等于亮度行跨度的两倍。水平子采样为 2 时，色度行跨度等于亮度行跨度。垂直子采样不影响行跨度。
对于非连续格式，格式不对亮度和色度行的填充和跨度之间的关系施加任何限制。
所有分量都以相同的位数存储。

.. raw:: latex

    \footnotesize

.. tabularcolumns:: |p{5.2cm}|p{1.0cm}|p{1.5cm}|p{1.9cm}|p{1.2cm}|p{1.8cm}|p{2.7cm}|

.. flat-table:: 半平面 YUV 格式概述
    :header-rows:  1
    :stub-columns: 0

    * - 标识符
      - 代码
      - 每个分量的位数
      - 子采样
      - 色度顺序 [1]_
      - 连续 [2]_
      - 块状 [3]_
    * - V4L2_PIX_FMT_NV12
      - 'NV12'
      - 8
      - 4:2:0
      - Cb, Cr
      - 是
      - 线性
    * - V4L2_PIX_FMT_NV21
      - 'NV21'
      - 8
      - 4:2:0
      - Cr, Cb
      - 是
      - 线性
    * - V4L2_PIX_FMT_NV12M
      - 'NM12'
      - 8
      - 4:2:0
      - Cb, Cr
      - 否
      - 线性
    * - V4L2_PIX_FMT_NV21M
      - 'NM21'
      - 8
      - 4:2:0
      - Cr, Cb
      - 否
      - 线性
    * - V4L2_PIX_FMT_NV12MT
      - 'TM12'
      - 8
      - 4:2:0
      - Cb, Cr
      - 否
      - 64x32 块
    * - V4L2_PIX_FMT_NV12MT_16X16
      - 'VM12'
      - 8
      - 4:2:2
      - Cb, Cr
      - 否
      - 16x16 块
    * - V4L2_PIX_FMT_P010
      - 'P010'
      - 10
      - 4:2:0
      - Cb, Cr
      - 是
      - 线性
    * - V4L2_PIX_FMT_P010_4L4
      - 'T010'
      - 10
      - 4:2:0
      - Cb, Cr
      - 是
      - 4x4 块
    * - V4L2_PIX_FMT_P012
      - 'P012'
      - 12
      - 4:2:0
      - Cb, Cr
      - 是
      - 线性
    * - V4L2_PIX_FMT_P012M
      - 'PM12'
      - 12
      - 4:2:0
      - Cb, Cr
      - 否
      - 线性
    * - V4L2_PIX_FMT_NV15_4L4
      - 'VT15'
      - 15
      - 4:2:0
      - Cb, Cr
      - 是
      - 4x4 块
    * - V4L2_PIX_FMT_NV16
      - 'NV16'
      - 8
      - 4:2:2
      - Cb, Cr
      - 是
      - 线性
    * - V4L2_PIX_FMT_NV61
      - 'NV61'
      - 8
      - 4:2:2
      - Cr, Cb
      - 是
      - 线性
    * - V4L2_PIX_FMT_NV16M
      - 'NM16'
      - 8
      - 4:2:2
      - Cb, Cr
      - 否
      - 线性
    * - V4L2_PIX_FMT_NV61M
      - 'NM61'
      - 8
      - 4:2:2
      - Cr, Cb
      - 否
      - 线性
    * - V4L2_PIX_FMT_NV24
      - 'NV24'
      - 8
      - 4:4:4
      - Cb, Cr
      - 是
      - 线性
    * - V4L2_PIX_FMT_NV42
      - 'NV42'
      - 8
      - 4:4:4
      - Cr, Cb
      - 是
      - 线性

.. raw:: latex

    \normalsize

.. [1] 第二平面上色度样本的顺序
.. [2] 表明平面是否需要在内存中连续或可以分离
.. [3] 宏块大小（以像素为单位）

**颜色样本位置：**
色度样本水平上位于 :ref:`interstitially sited<yuv-chroma-centered>`。
NV12、NV21、NV12M 和 NV21M
------------------------------

半平面YUV 4:2:0格式。色度平面在每个方向上都下采样了2倍。色度行包含的像素数是亮度行的一半，字节数与亮度行相同，并且色度平面包含的行数是亮度平面的一半。

.. flat-table:: 示例 4x4 NV12 图像
    :header-rows:  0
    :stub-columns: 0

    * - start + 0:
      - Y'\ :sub:`00`
      - Y'\ :sub:`01`
      - Y'\ :sub:`02`
      - Y'\ :sub:`03`
    * - start + 4:
      - Y'\ :sub:`10`
      - Y'\ :sub:`11`
      - Y'\ :sub:`12`
      - Y'\ :sub:`13`
    * - start + 8:
      - Y'\ :sub:`20`
      - Y'\ :sub:`21`
      - Y'\ :sub:`22`
      - Y'\ :sub:`23`
    * - start + 12:
      - Y'\ :sub:`30`
      - Y'\ :sub:`31`
      - Y'\ :sub:`32`
      - Y'\ :sub:`33`
    * - start + 16:
      - Cb\ :sub:`00`
      - Cr\ :sub:`00`
      - Cb\ :sub:`01`
      - Cr\ :sub:`01`
    * - start + 20:
      - Cb\ :sub:`10`
      - Cr\ :sub:`10`
      - Cb\ :sub:`11`
      - Cr\ :sub:`11`

.. flat-table:: 示例 4x4 NV12M 图像
    :header-rows:  0
    :stub-columns: 0

    * - start0 + 0:
      - Y'\ :sub:`00`
      - Y'\ :sub:`01`
      - Y'\ :sub:`02`
      - Y'\ :sub:`03`
    * - start0 + 4:
      - Y'\ :sub:`10`
      - Y'\ :sub:`11`
      - Y'\ :sub:`12`
      - Y'\ :sub:`13`
    * - start0 + 8:
      - Y'\ :sub:`20`
      - Y'\ :sub:`21`
      - Y'\ :sub:`22`
      - Y'\ :sub:`23`
    * - start0 + 12:
      - Y'\ :sub:`30`
      - Y'\ :sub:`31`
      - Y'\ :sub:`32`
      - Y'\ :sub:`33`
    * -
    * - start1 + 0:
      - Cb\ :sub:`00`
      - Cr\ :sub:`00`
      - Cb\ :sub:`01`
      - Cr\ :sub:`01`
    * - start1 + 4:
      - Cb\ :sub:`10`
      - Cr\ :sub:`10`
      - Cb\ :sub:`11`
      - Cr\ :sub:`11`

.. _V4L2-PIX-FMT-NV12MT:
.. _V4L2-PIX-FMT-NV12MT-16X16:
.. _V4L2-PIX-FMT-NV12-4L4:
.. _V4L2-PIX-FMT-NV12-16L16:
.. _V4L2-PIX-FMT-NV12-32L32:
.. _V4L2-PIX-FMT-NV12M-8L128:
.. _V4L2-PIX-FMT-NV12-8L128:
.. _V4L2-PIX-FMT-NV12M-10BE-8L128:
.. _V4L2-PIX-FMT-NV12-10BE-8L128:
.. _V4L2-PIX-FMT-MM21:

分块 NV12
---------

使用宏块分块的半平面YUV 4:2:0格式。色度平面在每个方向上都下采样了2倍。色度行包含的像素数是亮度行的一半，字节数与亮度行相同，并且色度平面包含的行数是亮度平面的一半。每个分块在内存中按顺序线性排列（从左到右，从上到下）。

``V4L2_PIX_FMT_NV12MT_16X16`` 类似于 ``V4L2_PIX_FMT_NV12M``，但以2D 16x16分块存储像素，并将分块线性存储在内存中。行跨度和图像高度必须对齐为16的倍数。亮度平面和色度平面的布局相同。

``V4L2_PIX_FMT_NV12MT`` 类似于 ``V4L2_PIX_FMT_NV12M``，但以2D 64x32分块存储像素，并将2x2分块组以Z顺序存储在内存中，横向交替使用Z和镜像Z形状。行跨度必须是128像素的倍数以确保整数个Z形状。图像高度必须是32像素的倍数。如果垂直分辨率是奇数个分块，则最后一行分块以线性顺序存储。亮度平面和色度平面的布局相同。

``V4L2_PIX_FMT_NV12_4L4`` 以4x4分块存储像素，并将分块线性存储在内存中。行跨度和图像高度必须对齐为4的倍数。亮度平面和色度平面的布局相同。

``V4L2_PIX_FMT_NV12_16L16`` 以16x16分块存储像素，并将分块线性存储在内存中。行跨度和图像高度必须对齐为16的倍数。亮度平面和色度平面的布局相同。
``V4L2_PIX_FMT_NV12_32L32`` 将像素存储在 32x32 的瓦片中，并将瓦片线性地存储在内存中。行跨度和图像高度必须对齐到 32 的倍数。亮度平面和色度平面的布局相同。

``V4L2_PIX_FMT_NV12M_8L128`` 与 ``V4L2_PIX_FMT_NV12M`` 类似，但将像素存储在 2D 8x128 的瓦片中，并将瓦片线性地存储在内存中。图像高度必须对齐到 128 的倍数。亮度平面和色度平面的布局相同。

``V4L2_PIX_FMT_NV12_8L128`` 与 ``V4L2_PIX_FMT_NV12M_8L128`` 类似，但将两个平面存储在一个内存中。

``V4L2_PIX_FMT_NV12M_10BE_8L128`` 与 ``V4L2_PIX_FMT_NV12M`` 类似，但将 10 位像素存储在 2D 8x128 的瓦片中，并将瓦片线性地存储在内存中，数据以大端字节序排列。图像高度必须对齐到 128 的倍数。亮度平面和色度平面的布局相同。

请注意，瓦片大小是 8 字节乘以 128 字节，这意味着一个像素的低位和高位可能位于不同的瓦片中。
10位像素是压缩存储的，因此5个字节包含4个10位像素（亮度）的布局如下：
- 字节0：Y0（位9-2）
- 字节1：Y0（位1-0） Y1（位9-4）
- 字节2：Y1（位3-0） Y2（位9-6）
- 字节3：Y2（位5-0） Y3（位9-8）
- 字节4：Y3（位7-0）

``V4L2_PIX_FMT_NV12_10BE_8L128`` 类似于 ``V4L2_PIX_FMT_NV12M_10BE_8L128``，但将两个平面存储在一个内存中。

``V4L2_PIX_FMT_MM21`` 将亮度像素存储在16x32的块中，并将色度像素存储在16x16的块中。行步长必须对齐到16的倍数，图像高度必须对齐到32的倍数。亮度和色度块的数量相同，尽管块大小不同。图像由两个不连续的平面组成。
.. _nv12mt:

.. kernel-figure:: nv12mt.svg
    :alt:    nv12mt.svg
    :align:  center

    V4L2_PIX_FMT_NV12MT 宏块Z形内存布局

.. _nv12mt_ex:

.. kernel-figure:: nv12mt_example.svg
    :alt:    nv12mt_example.svg
    :align:  center

    V4L2_PIX_FMT_NV12MT 块内存布局示例

.. _V4L2-PIX-FMT-NV15-4L4:

带块的NV15
----------

半平面10位YUV 4:2:0格式，使用4x4块
所有组件都紧密排列，没有填充
作为副作用，每组4个组件占用5个字节（YYYY或UVUV = 4 * 10位 = 40位 = 5字节）
.. _V4L2-PIX-FMT-NV16:
.. _V4L2-PIX-FMT-NV61:
.. _V4L2-PIX-FMT-NV16M:
.. _V4L2-PIX-FMT-NV61M:

NV16、NV61、NV16M 和 NV61M
---------------------------

半平面YUV 4:2:2格式。色度平面在水平方向上进行了2倍下采样。色度行包含亮度行一半的像素数且字节数相同，色度平面包含与亮度平面相同的行数
.. flat-table:: 示例4x4 NV16图像
    :header-rows:  0
    :stub-columns: 0

    * - 起始+0:
      - Y'\ :sub:`00`
      - Y'\ :sub:`01`
      - Y'\ :sub:`02`
      - Y'\ :sub:`03`
    * - 起始+4:
      - Y'\ :sub:`10`
      - Y'\ :sub:`11`
      - Y'\ :sub:`12`
      - Y'\ :sub:`13`
    * - 起始+8:
      - Y'\ :sub:`20`
      - Y'\ :sub:`21`
      - Y'\ :sub:`22`
      - Y'\ :sub:`23`
    * - 起始+12:
      - Y'\ :sub:`30`
      - Y'\ :sub:`31`
      - Y'\ :sub:`32`
      - Y'\ :sub:`33`
    * - 起始+16:
      - Cb\ :sub:`00`
      - Cr\ :sub:`00`
      - Cb\ :sub:`01`
      - Cr\ :sub:`01`
    * - 起始+20:
      - Cb\ :sub:`10`
      - Cr\ :sub:`10`
      - Cb\ :sub:`11`
      - Cr\ :sub:`11`
    * - 起始+24:
      - Cb\ :sub:`20`
      - Cr\ :sub:`20`
      - Cb\ :sub:`21`
      - Cr\ :sub:`21`
    * - 起始+28:
      - Cb\ :sub:`30`
      - Cr\ :sub:`30`
      - Cb\ :sub:`31`
      - Cr\ :sub:`31`

.. flat-table:: 示例4x4 NV16M图像
    :header-rows:  0
    :stub-columns: 0

    * - start0 + 0:
      - Y'\ :sub:`00`
      - Y'\ :sub:`01`
      - Y'\ :sub:`02`
      - Y'\ :sub:`03`
    * - start0 + 4:
      - Y'\ :sub:`10`
      - Y'\ :sub:`11`
      - Y'\ :sub:`12`
      - Y'\ :sub:`13`
    * - start0 + 8:
      - Y'\ :sub:`20`
      - Y'\ :sub:`21`
      - Y'\ :sub:`22`
      - Y'\ :sub:`23`
    * - start0 + 12:
      - Y'\ :sub:`30`
      - Y'\ :sub:`31`
      - Y'\ :sub:`32`
      - Y'\ :sub:`33`
    * -
    * - start1 + 0:
      - Cb\ :sub:`00`
      - Cr\ :sub:`00`
      - Cb\ :sub:`02`
      - Cr\ :sub:`02`
    * - start1 + 4:
      - Cb\ :sub:`10`
      - Cr\ :sub:`10`
      - Cb\ :sub:`12`
      - Cr\ :sub:`12`
    * - start1 + 8:
      - Cb\ :sub:`20`
      - Cr\ :sub:`20`
      - Cb\ :sub:`22`
      - Cr\ :sub:`22`
    * - start1 + 12:
      - Cb\ :sub:`30`
      - Cr\ :sub:`30`
      - Cb\ :sub:`32`
      - Cr\ :sub:`32`

.. _V4L2-PIX-FMT-NV24:
.. _V4L2-PIX-FMT-NV42:

NV24 和 NV42
------------

半平面YUV 4:4:4格式。色度平面未进行下采样。色度行包含与亮度行相同的像素数且字节数为亮度行的两倍，色度平面包含与亮度平面相同的行数
.. flat-table:: 示例4x4 NV24图像
    :header-rows:  0
    :stub-columns: 0

    * - 起始+0:
      - Y'\ :sub:`00`
      - Y'\ :sub:`01`
      - Y'\ :sub:`02`
      - Y'\ :sub:`03`
    * - 起始+4:
      - Y'\ :sub:`10`
      - Y'\ :sub:`11`
      - Y'\ :sub:`12`
      - Y'\ :sub:`13`
    * - 起始+8:
      - Y'\ :sub:`20`
      - Y'\ :sub:`21`
      - Y'\ :sub:`22`
      - Y'\ :sub:`23`
    * - 起始+12:
      - Y'\ :sub:`30`
      - Y'\ :sub:`31`
      - Y'\ :sub:`32`
      - Y'\ :sub:`33`
    * - 起始+16:
      - Cb\ :sub:`00`
      - Cr\ :sub:`00`
      - Cb\ :sub:`01`
      - Cr\ :sub:`01`
      - Cb\ :sub:`02`
      - Cr\ :sub:`02`
      - Cb\ :sub:`03`
      - Cr\ :sub:`03`
    * - 起始+24:
      - Cb\ :sub:`10`
      - Cr\ :sub:`10`
      - Cb\ :sub:`11`
      - Cr\ :sub:`11`
      - Cb\ :sub:`12`
      - Cr\ :sub:`12`
      - Cb\ :sub:`13`
      - Cr\ :sub:`13`
    * - 起始+32:
      - Cb\ :sub:`20`
      - Cr\ :sub:`20`
      - Cb\ :sub:`21`
      - Cr\ :sub:`21`
      - Cb\ :sub:`22`
      - Cr\ :sub:`22`
      - Cb\ :sub:`23`
      - Cr\ :sub:`23`
    * - 起始+40:
      - Cb\ :sub:`30`
      - Cr\ :sub:`30`
      - Cb\ :sub:`31`
      - Cr\ :sub:`31`
      - Cb\ :sub:`32`
      - Cr\ :sub:`32`
      - Cb\ :sub:`33`
      - Cr\ :sub:`33`

.. _V4L2_PIX_FMT_P010:
.. _V4L2-PIX-FMT-P010-4L4:

P010 和带块的P010
-------------------

P010 类似于每个组件有10位的NV12，扩展到16位
数据位于高10位，低6位为零，按小端字节序排列。
... 平面表格:: 4x4 P010 图像样本
    :header-rows:  0
    :stub-columns: 0

    * - start + 0:
      - Y'\ :sub:`00`
      - Y'\ :sub:`01`
      - Y'\ :sub:`02`
      - Y'\ :sub:`03`
    * - start + 8:
      - Y'\ :sub:`10`
      - Y'\ :sub:`11`
      - Y'\ :sub:`12`
      - Y'\ :sub:`13`
    * - start + 16:
      - Y'\ :sub:`20`
      - Y'\ :sub:`21`
      - Y'\ :sub:`22`
      - Y'\ :sub:`23`
    * - start + 24:
      - Y'\ :sub:`30`
      - Y'\ :sub:`31`
      - Y'\ :sub:`32`
      - Y'\ :sub:`33`
    * - start + 32:
      - Cb\ :sub:`00`
      - Cr\ :sub:`00`
      - Cb\ :sub:`01`
      - Cr\ :sub:`01`
    * - start + 40:
      - Cb\ :sub:`10`
      - Cr\ :sub:`10`
      - Cb\ :sub:`11`
      - Cr\ :sub:`11`

.. _V4L2-PIX-FMT-P012:
.. _V4L2-PIX-FMT-P012M:

P012 和 P012M
--------------

P012 类似于 NV12，每个组件有 12 位，并扩展到 16 位。
数据位于高 12 位，低 4 位为零，按小端字节序排列。

.. 平面表格:: 4x4 P012 图像样本
    :header-rows:  0
    :stub-columns: 0

    * - start + 0:
      - Y'\ :sub:`00`
      - Y'\ :sub:`01`
      - Y'\ :sub:`02`
      - Y'\ :sub:`03`
    * - start + 8:
      - Y'\ :sub:`10`
      - Y'\ :sub:`11`
      - Y'\ :sub:`12`
      - Y'\ :sub:`13`
    * - start + 16:
      - Y'\ :sub:`20`
      - Y'\ :sub:`21`
      - Y'\ :sub:`22`
      - Y'\ :sub:`23`
    * - start + 24:
      - Y'\ :sub:`30`
      - Y'\ :sub:`31`
      - Y'\ :sub:`32`
      - Y'\ :sub:`33`
    * - start + 32:
      - Cb\ :sub:`00`
      - Cr\ :sub:`00`
      - Cb\ :sub:`01`
      - Cr\ :sub:`01`
    * - start + 40:
      - Cb\ :sub:`10`
      - Cr\ :sub:`10`
      - Cb\ :sub:`11`
      - Cr\ :sub:`11`

.. 平面表格:: 4x4 P012M 图像样本
    :header-rows:  0
    :stub-columns: 0

    * - start0 + 0:
      - Y'\ :sub:`00`
      - Y'\ :sub:`01`
      - Y'\ :sub:`02`
      - Y'\ :sub:`03`
    * - start0 + 8:
      - Y'\ :sub:`10`
      - Y'\ :sub:`11`
      - Y'\ :sub:`12`
      - Y'\ :sub:`13`
    * - start0 + 16:
      - Y'\ :sub:`20`
      - Y'\ :sub:`21`
      - Y'\ :sub:`22`
      - Y'\ :sub:`23`
    * - start0 + 24:
      - Y'\ :sub:`30`
      - Y'\ :sub:`31`
      - Y'\ :sub:`32`
      - Y'\ :sub:`33`
    * -
    * - start1 + 0:
      - Cb\ :sub:`00`
      - Cr\ :sub:`00`
      - Cb\ :sub:`01`
      - Cr\ :sub:`01`
    * - start1 + 8:
      - Cb\ :sub:`10`
      - Cr\ :sub:`10`
      - Cb\ :sub:`11`
      - Cr\ :sub:`11`

全平面 YUV 格式
=================

这些格式将 Y、Cb 和 Cr 组件存储在三个独立的平面上。亮度平面首先出现，两个色度平面的顺序因格式而异。两个色度平面始终使用相同的子采样。
对于内存连续格式，色度行末尾的填充像素数与亮度行的填充相同。因此，色度行步长（以字节为单位）等于亮度行步长除以水平子采样因子。垂直子采样不影响行步长。
对于非连续格式，该格式不对亮度和色度行的填充和步长之间的关系施加任何约束。
所有组件都以相同数量的位存储。
``V4L2_PIX_FMT_P010_4L4`` 在内存中以 4x4 瓦片的形式线性存储像素。行步长必须对齐到 8 的倍数且图像高度为 4 的倍数。亮度和平面的布局是相同的。

.. raw:: latex

    \small

.. tabularcolumns:: |p{5.0cm}|p{1.1cm}|p{1.5cm}|p{2.2cm}|p{1.2cm}|p{3.7cm}|

.. 平面表格:: 全平面 YUV 格式概览
    :header-rows:  1
    :stub-columns: 0

    * - 标识符
      - 代码
      - 每个组件的位数
      - 子采样
      - 平面顺序 [4]_
      - 连续 [5]_

    * - V4L2_PIX_FMT_YUV410
      - 'YUV9'
      - 8
      - 4:1:0
      - Y, Cb, Cr
      - 是
    * - V4L2_PIX_FMT_YVU410
      - 'YVU9'
      - 8
      - 4:1:0
      - Y, Cr, Cb
      - 是
    * - V4L2_PIX_FMT_YUV411P
      - '411P'
      - 8
      - 4:1:1
      - Y, Cb, Cr
      - 是
    * - V4L2_PIX_FMT_YUV420M
      - 'YM12'
      - 8
      - 4:2:0
      - Y, Cb, Cr
      - 否
    * - V4L2_PIX_FMT_YVU420M
      - 'YM21'
      - 8
      - 4:2:0
      - Y, Cr, Cb
      - 否
    * - V4L2_PIX_FMT_YUV420
      - 'YU12'
      - 8
      - 4:2:0
      - Y, Cb, Cr
      - 是
    * - V4L2_PIX_FMT_YVU420
      - 'YV12'
      - 8
      - 4:2:0
      - Y, Cr, Cb
      - 是
    * - V4L2_PIX_FMT_YUV422P
      - '422P'
      - 8
      - 4:2:2
      - Y, Cb, Cr
      - 是
    * - V4L2_PIX_FMT_YUV422M
      - 'YM16'
      - 8
      - 4:2:2
      - Y, Cb, Cr
      - 否
    * - V4L2_PIX_FMT_YVU422M
      - 'YM61'
      - 8
      - 4:2:2
      - Y, Cr, Cb
      - 否
    * - V4L2_PIX_FMT_YUV444M
      - 'YM24'
      - 8
      - 4:4:4
      - Y, Cb, Cr
      - 否
    * - V4L2_PIX_FMT_YVU444M
      - 'YM42'
      - 8
      - 4:4:4
      - Y, Cr, Cb
      - 否

.. raw:: latex

    \normalsize

.. [4] 亮度和平面的顺序
.. [5] 表示平面是否需要在内存中连续或可以分离

**颜色样本位置：**
色度样本在水平方向上是 :ref:`交错放置<yuv-chroma-centered>` 的。

.. _V4L2-PIX-FMT-YUV410:
.. _V4L2-PIX-FMT-YVU410:

YUV410 和 YVU410
-----------------

平面 YUV 4:1:0 格式。色度平面在各个方向上被子采样 4 倍。色度行包含亮度行四分之一的像素数和字节数，色度平面包含亮度平面四分之一的行数。

.. 平面表格:: 4x4 YUV410 图像样本
    :header-rows:  0
    :stub-columns: 0

    * - start + 0:
      - Y'\ :sub:`00`
      - Y'\ :sub:`01`
      - Y'\ :sub:`02`
      - Y'\ :sub:`03`
    * - start + 4:
      - Y'\ :sub:`10`
      - Y'\ :sub:`11`
      - Y'\ :sub:`12`
      - Y'\ :sub:`13`
    * - start + 8:
      - Y'\ :sub:`20`
      - Y'\ :sub:`21`
      - Y'\ :sub:`22`
      - Y'\ :sub:`23`
    * - start + 12:
      - Y'\ :sub:`30`
      - Y'\ :sub:`31`
      - Y'\ :sub:`32`
      - Y'\ :sub:`33`
    * - start + 16:
      - Cr\ :sub:`00`
    * - start + 17:
      - Cb\ :sub:`00`

.. _V4L2-PIX-FMT-YUV411P:

YUV411P
-------

平面 YUV 4:1:1 格式。色度平面在水平方向上被子采样 4 倍。色度行包含亮度行四分之一的像素数和字节数，色度平面包含与亮度平面相同的行数。
```
.. 平面表格:: 4x4 YUV411P 图像示例
    :header-rows:  0
    :stub-columns: 0

    * - 起始 + 0:
      - Y'\ :sub:`00`
      - Y'\ :sub:`01`
      - Y'\ :sub:`02`
      - Y'\ :sub:`03`
    * - 起始 + 4:
      - Y'\ :sub:`10`
      - Y'\ :sub:`11`
      - Y'\ :sub:`12`
      - Y'\ :sub:`13`
    * - 起始 + 8:
      - Y'\ :sub:`20`
      - Y'\ :sub:`21`
      - Y'\ :sub:`22`
      - Y'\ :sub:`23`
    * - 起始 + 12:
      - Y'\ :sub:`30`
      - Y'\ :sub:`31`
      - Y'\ :sub:`32`
      - Y'\ :sub:`33`
    * - 起始 + 16:
      - Cb\ :sub:`00`
    * - 起始 + 17:
      - Cb\ :sub:`10`
    * - 起始 + 18:
      - Cb\ :sub:`20`
    * - 起始 + 19:
      - Cb\ :sub:`30`
    * - 起始 + 20:
      - Cr\ :sub:`00`
    * - 起始 + 21:
      - Cr\ :sub:`10`
    * - 起始 + 22:
      - Cr\ :sub:`20`
    * - 起始 + 23:
      - Cr\ :sub:`30`


.. _V4L2-PIX-FMT-YUV420:
.. _V4L2-PIX-FMT-YVU420:
.. _V4L2-PIX-FMT-YUV420M:
.. _V4L2-PIX-FMT-YVU420M:

YUV420、YVU420、YUV420M 和 YVU420M
-----------------------------------

平面 YUV 4:2:0 格式。色度平面在每个方向上都下采样了 2 倍。色度行包含亮度行一半的像素数和字节数，色度平面包含亮度平面上一半的行数。
.. 平面表格:: 4x4 YUV420 图像示例
    :header-rows:  0
    :stub-columns: 0

    * - 起始 + 0:
      - Y'\ :sub:`00`
      - Y'\ :sub:`01`
      - Y'\ :sub:`02`
      - Y'\ :sub:`03`
    * - 起始 + 4:
      - Y'\ :sub:`10`
      - Y'\ :sub:`11`
      - Y'\ :sub:`12`
      - Y'\ :sub:`13`
    * - 起始 + 8:
      - Y'\ :sub:`20`
      - Y'\ :sub:`21`
      - Y'\ :sub:`22`
      - Y'\ :sub:`23`
    * - 起始 + 12:
      - Y'\ :sub:`30`
      - Y'\ :sub:`31`
      - Y'\ :sub:`32`
      - Y'\ :sub:`33`
    * - 起始 + 16:
      - Cr\ :sub:`00`
      - Cr\ :sub:`01`
    * - 起始 + 18:
      - Cr\ :sub:`10`
      - Cr\ :sub:`11`
    * - 起始 + 20:
      - Cb\ :sub:`00`
      - Cb\ :sub:`01`
    * - 起始 + 22:
      - Cb\ :sub:`10`
      - Cb\ :sub:`11`

.. 平面表格:: 4x4 YUV420M 图像示例
    :header-rows:  0
    :stub-columns: 0

    * - start0 + 0:
      - Y'\ :sub:`00`
      - Y'\ :sub:`01`
      - Y'\ :sub:`02`
      - Y'\ :sub:`03`
    * - start0 + 4:
      - Y'\ :sub:`10`
      - Y'\ :sub:`11`
      - Y'\ :sub:`12`
      - Y'\ :sub:`13`
    * - start0 + 8:
      - Y'\ :sub:`20`
      - Y'\ :sub:`21`
      - Y'\ :sub:`22`
      - Y'\ :sub:`23`
    * - start0 + 12:
      - Y'\ :sub:`30`
      - Y'\ :sub:`31`
      - Y'\ :sub:`32`
      - Y'\ :sub:`33`
    * -
    * - start1 + 0:
      - Cb\ :sub:`00`
      - Cb\ :sub:`01`
    * - start1 + 2:
      - Cb\ :sub:`10`
      - Cb\ :sub:`11`
    * -
    * - start2 + 0:
      - Cr\ :sub:`00`
      - Cr\ :sub:`01`
    * - start2 + 2:
      - Cr\ :sub:`10`
      - Cr\ :sub:`11`


.. _V4L2-PIX-FMT-YUV422P:
.. _V4L2-PIX-FMT-YUV422M:
.. _V4L2-PIX-FMT-YVU422M:

YUV422P、YUV422M 和 YVU422M
----------------------------

平面 YUV 4:2:2 格式。色度平面在水平方向上下采样了 2 倍。色度行包含亮度行一半的像素数和字节数，色度平面包含与亮度平面相同的行数。
.. 平面表格:: 4x4 YUV422P 图像示例
    :header-rows:  0
    :stub-columns: 0

    * - 起始 + 0:
      - Y'\ :sub:`00`
      - Y'\ :sub:`01`
      - Y'\ :sub:`02`
      - Y'\ :sub:`03`
    * - 起始 + 4:
      - Y'\ :sub:`10`
      - Y'\ :sub:`11`
      - Y'\ :sub:`12`
      - Y'\ :sub:`13`
    * - 起始 + 8:
      - Y'\ :sub:`20`
      - Y'\ :sub:`21`
      - Y'\ :sub:`22`
      - Y'\ :sub:`23`
    * - 起始 + 12:
      - Y'\ :sub:`30`
      - Y'\ :sub:`31`
      - Y'\ :sub:`32`
      - Y'\ :sub:`33`
    * - 起始 + 16:
      - Cb\ :sub:`00`
      - Cb\ :sub:`01`
    * - 起始 + 18:
      - Cb\ :sub:`10`
      - Cb\ :sub:`11`
    * - 起始 + 20:
      - Cb\ :sub:`20`
      - Cb\ :sub:`21`
    * - 起始 + 22:
      - Cb\ :sub:`30`
      - Cb\ :sub:`31`
    * - 起始 + 24:
      - Cr\ :sub:`00`
      - Cr\ :sub:`01`
    * - 起始 + 26:
      - Cr\ :sub:`10`
      - Cr\ :sub:`11`
    * - 起始 + 28:
      - Cr\ :sub:`20`
      - Cr\ :sub:`21`
    * - 起始 + 30:
      - Cr\ :sub:`30`
      - Cr\ :sub:`31`

.. 平面表格:: 4x4 YUV422M 图像示例
    :header-rows:  0
    :stub-columns: 0

    * - start0 + 0:
      - Y'\ :sub:`00`
      - Y'\ :sub:`01`
      - Y'\ :sub:`02`
      - Y'\ :sub:`03`
    * - start0 + 4:
      - Y'\ :sub:`10`
      - Y'\ :sub:`11`
      - Y'\ :sub:`12`
      - Y'\ :sub:`13`
    * - start0 + 8:
      - Y'\ :sub:`20`
      - Y'\ :sub:`21`
      - Y'\ :sub:`22`
      - Y'\ :sub:`23`
    * - start0 + 12:
      - Y'\ :sub:`30`
      - Y'\ :sub:`31`
      - Y'\ :sub:`32`
      - Y'\ :sub:`33`
    * -
    * - start1 + 0:
      - Cb\ :sub:`00`
      - Cb\ :sub:`01`
    * - start1 + 2:
      - Cb\ :sub:`10`
      - Cb\ :sub:`11`
    * - start1 + 4:
      - Cb\ :sub:`20`
      - Cb\ :sub:`21`
    * - start1 + 6:
      - Cb\ :sub:`30`
      - Cb\ :sub:`31`
    * -
    * - start2 + 0:
      - Cr\ :sub:`00`
      - Cr\ :sub:`01`
    * - start2 + 2:
      - Cr\ :sub:`10`
      - Cr\ :sub:`11`
    * - start2 + 4:
      - Cr\ :sub:`20`
      - Cr\ :sub:`21`
    * - start2 + 6:
      - Cr\ :sub:`30`
      - Cr\ :sub:`31`


.. _V4L2-PIX-FMT-YUV444M:
.. _V4L2-PIX-FMT-YVU444M:

YUV444M 和 YVU444M
-------------------

平面 YUV 4:4:4 格式。色度平面没有下采样。色度行包含与亮度行相同数量的像素数和字节数，色度平面包含与亮度平面相同的行数。
.. 平面表格:: 4x4 YUV444M 图像示例
    :header-rows:  0
    :stub-columns: 0

    * - start0 + 0:
      - Y'\ :sub:`00`
      - Y'\ :sub:`01`
      - Y'\ :sub:`02`
      - Y'\ :sub:`03`
    * - start0 + 4:
      - Y'\ :sub:`10`
      - Y'\ :sub:`11`
      - Y'\ :sub:`12`
      - Y'\ :sub:`13`
    * - start0 + 8:
      - Y'\ :sub:`20`
      - Y'\ :sub:`21`
      - Y'\ :sub:`22`
      - Y'\ :sub:`23`
    * - start0 + 12:
      - Y'\ :sub:`30`
      - Y'\ :sub:`31`
      - Y'\ :sub:`32`
      - Y'\ :sub:`33`
    * -
    * - start1 + 0:
      - Cb\ :sub:`00`
      - Cb\ :sub:`01`
      - Cb\ :sub:`02`
      - Cb\ :sub:`03`
    * - start1 + 4:
      - Cb\ :sub:`10`
      - Cb\ :sub:`11`
      - Cb\ :sub:`12`
      - Cb\ :sub:`13`
    * - start1 + 8:
      - Cb\ :sub:`20`
      - Cb\ :sub:`21`
      - Cb\ :sub:`22`
      - Cb\ :sub:`23`
    * - start1 + 12:
      - Cb\ :sub:`20`
      - Cb\ :sub:`21`
      - Cb\ :sub:`32`
      - Cb\ :sub:`33`
    * -
    * - start2 + 0:
      - Cr\ :sub:`00`
      - Cr\ :sub:`01`
      - Cr\ :sub:`02`
      - Cr\ :sub:`03`
    * - start2 + 4:
      - Cr\ :sub:`10`
      - Cr\ :sub:`11`
      - Cr\ :sub:`12`
      - Cr\ :sub:`13`
    * - start2 + 8:
      - Cr\ :sub:`20`
      - Cr\ :sub:`21`
      - Cr\ :sub:`22`
      - Cr\ :sub:`23`
    * - start2 + 12:
      - Cr\ :sub:`30`
      - Cr\ :sub:`31`
      - Cr\ :sub:`32`
      - Cr\ :sub:`33`
```
