### SPDX 许可证标识符：GPL-2.0 或 GFDL-1.1-no-invariants-or-later

********************************************************************************************************************************************************************************************************************************************************************************
V4L2_META_FMT_GENERIC_8 ('MET8')，V4L2_META_FMT_GENERIC_CSI2_10 ('MC1A')，V4L2_META_FMT_GENERIC_CSI2_12 ('MC1C')，V4L2_META_FMT_GENERIC_CSI2_14 ('MC1E')，V4L2_META_FMT_GENERIC_CSI2_16 ('MC1G')，V4L2_META_FMT_GENERIC_CSI2_20 ('MC1K')，V4L2_META_FMT_GENERIC_CSI2_24 ('MC1O')
********************************************************************************************************************************************************************************************************************************************************************************

#### 基于行的通用元数据格式

##### 描述
这些基于行的通用元数据格式定义了数据在内存中的布局，但不定义元数据本身的格式或含义。

#### V4L2_META_FMT_GENERIC_8
V4L2_META_FMT_GENERIC_8 格式是一个简单的 8 位元数据格式。此格式用于 CSI-2 的每个数据单元 (Data Unit) 为 8 位的情况。
此外，当两个字节的元数据被打包到一个 16 位的数据单元时，也使用此格式。否则，每像素 16 位的数据格式是 [V4L2_META_FMT_GENERIC_CSI2_16](#v4l2-meta-fmt-generic-csi2-16)。

**V4L2_META_FMT_GENERIC_8 的字节顺序：**
每个单元格为一个字节。“M”表示一个元数据字节。

|     | M₀₀ | M₁₀ | M₂₀ | M₃₀ |
|-----|-----|-----|-----|-----|
| start + 0: | M₀₀ | M₁₀ | M₂₀ | M₃₀ |
| start + 4: | M₀₁ | M₁₁ | M₂₁ | M₃₁ |

#### V4L2_META_FMT_GENERIC_CSI2_10
V4L2_META_FMT_GENERIC_CSI2_10 包含打包在 10 位数据单元中的 8 位通用元数据，在每四个元数据字节之后有一个填充字节。这种格式通常由接收来自发送 MEDIA_BUS_FMT_META_10 数据源的 CSI-2 接收器使用，并将接收到的数据原样写入内存。
数据的打包遵循 MIPI CSI-2 规范，而数据的填充则定义在 MIPI CCS 规范中。
此格式还与每个数据单元 20 位的格式一起使用，其中将两个字节的元数据打包到一个数据单元中。否则，每像素 20 位的数据格式是 [V4L2_META_FMT_GENERIC_CSI2_20](#v4l2-meta-fmt-generic-csi2-20)。
此格式采用小端字节序。

**V4L2_META_FMT_GENERIC_CSI2_10 的字节顺序：**
每个单元格为一个字节。“M”表示一个元数据字节，“x”表示一个填充字节。

|     | M₀₀ | M₁₀ | M₂₀ | M₃₀ | x |
|-----|-----|-----|-----|-----|---|
| start + 0: | M₀₀ | M₁₀ | M₂₀ | M₃₀ | x |
| start + 5: | M₀₁ | M₁₁ | M₂₁ | M₃₁ | x |

#### V4L2_META_FMT_GENERIC_CSI2_12
V4L2_META_FMT_GENERIC_CSI2_12 包含打包在 12 位数据单元中的 8 位通用元数据，在每两个元数据字节之后有一个填充字节。这种格式通常由接收来自发送 MEDIA_BUS_FMT_META_12 数据源的 CSI-2 接收器使用，并将接收到的数据原样写入内存。

|     | M₀₀ | M₁₀ | M₂₀ | M₃₀ | x |
|-----|-----|-----|-----|-----|---|
| start + 0: | M₀₀ | M₁₀ | M₂₀ | M₃₀ | x |
| start + 5: | M₀₁ | M₁₁ | M₂₁ | M₃₁ | x |
数据的打包遵循MIPI CSI-2规范，而数据的填充则在MIPI CCS规范中定义。

此格式还与每 :term:`Data Unit` 24位的数据格式一起使用，该格式将两个字节的元数据打包到一个Data Unit中。否则，每像素24位的数据格式是 :ref:`V4L2_META_FMT_GENERIC_CSI2_24 <v4l2-meta-fmt-generic-csi2-24>`。

此格式为小端模式。

**V4L2_META_FMT_GENERIC_CSI2_12 的字节顺序。**

每个单元格代表一个字节。“M”表示一个元数据字节，“x”表示一个填充字节。

.. tabularcolumns:: |p{2.4cm}|p{1.2cm}|p{1.2cm}|p{1.2cm}|p{1.2cm}|p{.8cm}|p{.8cm}|

.. flat-table:: 示例 4x2 元数据帧
    :header-rows:  0
    :stub-columns: 0
    :widths: 12 8 8 8 8 8 8

    * - start + 0:
      - M\ :sub:`00`
      - M\ :sub:`10`
      - x
      - M\ :sub:`20`
      - M\ :sub:`30`
      - x
    * - start + 6:
      - M\ :sub:`01`
      - M\ :sub:`11`
      - x
      - M\ :sub:`21`
      - M\ :sub:`31`
      - x

.. _v4l2-meta-fmt-generic-csi2-14:

V4L2_META_FMT_GENERIC_CSI2_14
-----------------------------

V4L2_META_FMT_GENERIC_CSI2_14 包含以14位Data Unit打包的8位通用元数据，并且每四个元数据字节之后有三个填充字节。此格式通常由接收14位元数据（MEDIA_BUS_FMT_META_14）的CSI-2接收器使用，并且CSI-2接收器会将接收到的数据原样写入内存。

数据的打包遵循MIPI CSI-2规范，而数据的填充则在MIPI CCS规范中定义。

此格式为小端模式。

**V4L2_META_FMT_GENERIC_CSI2_14 的字节顺序。**

每个单元格代表一个字节。“M”表示一个元数据字节，“x”表示一个填充字节。

.. tabularcolumns:: |p{2.4cm}|p{1.2cm}|p{1.2cm}|p{1.2cm}|p{1.2cm}|p{.8cm}|p{.8cm}|p{.8cm}|

.. flat-table:: 示例 4x2 元数据帧
    :header-rows:  0
    :stub-columns: 0
    :widths: 12 8 8 8 8 8 8 8

    * - start + 0:
      - M\ :sub:`00`
      - M\ :sub:`10`
      - M\ :sub:`20`
      - M\ :sub:`30`
      - x
      - x
      - x
    * - start + 7:
      - M\ :sub:`01`
      - M\ :sub:`11`
      - M\ :sub:`21`
      - M\ :sub:`31`
      - x
      - x
      - x

.. _v4l2-meta-fmt-generic-csi2-16:

V4L2_META_FMT_GENERIC_CSI2_16
-----------------------------

V4L2_META_FMT_GENERIC_CSI2_16 包含以16位Data Unit打包的8位通用元数据，并且每字节元数据之后有一个填充字节。此格式通常由接收16位元数据（MEDIA_BUS_FMT_META_16）的CSI-2接收器使用，并且CSI-2接收器会将接收到的数据原样写入内存。

数据的打包遵循MIPI CSI-2规范，而数据的填充则在MIPI CCS规范中定义。
一些设备支持与16位图像数据结合使用的更高效的元数据打包方式。在这种情况下，数据格式为
:ref:`V4L2_META_FMT_GENERIC_8 <v4l2-meta-fmt-generic-8>`
此格式为小端字节序。

**V4L2_META_FMT_GENERIC_CSI2_16 的字节序。**

每个单元格为一个字节。“M”表示一个元数据字节，“x”表示填充字节。
.. tabularcolumns:: |p{2.4cm}|p{1.2cm}|p{.8cm}|p{1.2cm}|p{.8cm}|p{1.2cm}|p{.8cm}|p{1.2cm}|p{.8cm}|

.. flat-table:: 示例 4x2 元数据帧
    :header-rows:  0
    :stub-columns: 0
    :widths: 12 8 8 8 8 8 8 8 8

    * - 起始 + 0:
      - M\ :sub:`00`
      - x
      - M\ :sub:`10`
      - x
      - M\ :sub:`20`
      - x
      - M\ :sub:`30`
      - x
    * - 起始 + 8:
      - M\ :sub:`01`
      - x
      - M\ :sub:`11`
      - x
      - M\ :sub:`21`
      - x
      - M\ :sub:`31`
      - x

.. _v4l2-meta-fmt-generic-csi2-20:

V4L2_META_FMT_GENERIC_CSI2_20
-----------------------------

V4L2_META_FMT_GENERIC_CSI2_20 包含在20位数据单元中打包的8位通用元数据，在每个元数据字节之后交替使用一个或两个填充字节。此格式通常由接收来自传输 MEDIA_BUS_FMT_META_20 源的 CSI-2 接收器使用，并且 CSI-2 接收器将接收到的数据原样写入内存。
数据的打包遵循 MIPI CSI-2 规范，数据的填充定义在 MIPI CCS 规范中。
一些设备支持与16位图像数据结合使用的更高效的元数据打包方式。在这种情况下，数据格式为
:ref:`V4L2_META_FMT_GENERIC_CSI2_10 <v4l2-meta-fmt-generic-csi2-10>`
此格式为小端字节序。

**V4L2_META_FMT_GENERIC_CSI2_20 的字节序。**

每个单元格为一个字节。“M”表示一个元数据字节，“x”表示填充字节。
.. tabularcolumns:: |p{2.4cm}|p{1.2cm}|p{.8cm}|p{1.2cm}|p{.8cm}|p{.8cm}|p{1.2cm}|p{.8cm}|p{1.2cm}|p{.8cm}|p{.8cm}|

.. flat-table:: 示例 4x2 元数据帧
    :header-rows:  0
    :stub-columns: 0
    :widths: 12 8 8 8 8 8 8 8 8 8 8

    * - 起始 + 0:
      - M\ :sub:`00`
      - x
      - M\ :sub:`10`
      - x
      - x
      - M\ :sub:`20`
      - x
      - M\ :sub:`30`
      - x
      - x
    * - 起始 + 10:
      - M\ :sub:`01`
      - x
      - M\ :sub:`11`
      - x
      - x
      - M\ :sub:`21`
      - x
      - M\ :sub:`31`
      - x
      - x

.. _v4l2-meta-fmt-generic-csi2-24:

V4L2_META_FMT_GENERIC_CSI2_24
-----------------------------

V4L2_META_FMT_GENERIC_CSI2_24 包含在24位数据单元中打包的8位通用元数据，在每个元数据字节之后有两个填充字节。此格式通常由接收来自传输 MEDIA_BUS_FMT_META_24 源的 CSI-2 接收器使用，并且 CSI-2 接收器将接收到的数据原样写入内存。
数据的打包遵循 MIPI CSI-2 规范，数据的填充定义在 MIPI CCS 规范中。
一些设备支持更高效的元数据打包，与16位图像数据结合使用。在这种情况下，数据格式为
:ref:`V4L2_META_FMT_GENERIC_CSI2_12 <v4l2-meta-fmt-generic-csi2-12>`
此格式采用小端字节序
**V4L2_META_FMT_GENERIC_CSI2_24 的字节序。**

每个单元格代表一个字节。“M”表示一个元数据字节，“x”表示填充字节。

.. tabularcolumns:: |p{2.4cm}|p{1.2cm}|p{.8cm}|p{.8cm}|p{1.2cm}|p{.8cm}|p{.8cm}|p{1.2cm}|p{.8cm}|p{.8cm}|p{1.2cm}|p{.8cm}|p{.8cm}|

.. flat-table:: 示例 4x2 元数据帧
    :header-rows:  0
    :stub-columns: 0
    :widths: 12 8 8 8 8 8 8 8 8 8 8 8 8

    * - start + 0:
      - M\ :sub:`00`
      - x
      - x
      - M\ :sub:`10`
      - x
      - x
      - M\ :sub:`20`
      - x
      - x
      - M\ :sub:`30`
      - x
      - x
    * - start + 12:
      - M\ :sub:`01`
      - x
      - x
      - M\ :sub:`11`
      - x
      - x
      - M\ :sub:`21`
      - x
      - x
      - M\ :sub:`31`
      - x
      - x
