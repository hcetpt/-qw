SPDX 许可证标识符: GFDL-1.1-no-invariants-or-later

.. _jpeg-controls:

**************************
JPEG 控制参考
**************************

JPEG 类包含 JPEG 编码器和解码器的常用功能控制。目前，它包括实现渐进式基线 DCT 压缩过程与霍夫曼熵编码的编解码器的功能。
.. _jpeg-control-id:

JPEG 控制 ID
=================

``V4L2_CID_JPEG_CLASS (class)``
    JPEG 类描述符。调用此控制的 :ref:`VIDIOC_QUERYCTRL` 将返回该控制类的描述。
``V4L2_CID_JPEG_CHROMA_SUBSAMPLING (menu)``
    色度子采样因子描述了输入图像中每个组件相对于每个空间维度的最大采样率是如何采样的。更多详情请参阅 :ref:`itu-t81`，条款 A.1.1。``V4L2_CID_JPEG_CHROMA_SUBSAMPLING`` 控制确定在将输入图像从 RGB 转换为 Y'CbCr 色彩空间后，Cb 和 Cr 组件如何进行下采样。
.. tabularcolumns:: |p{7.5cm}|p{10.0cm}|

.. flat-table::
    :header-rows:  0
    :stub-columns: 0

    * - ``V4L2_JPEG_CHROMA_SUBSAMPLING_444``
      - 不进行色度子采样，每个像素具有 Y、Cr 和 Cb 值
    * - ``V4L2_JPEG_CHROMA_SUBSAMPLING_422``
      - 水平方向上以 2 的比例对 Cr 和 Cb 组件进行子采样
    * - ``V4L2_JPEG_CHROMA_SUBSAMPLING_420``
      - 在水平和垂直方向上以 2 的比例对 Cr 和 Cb 组件进行子采样
    * - ``V4L2_JPEG_CHROMA_SUBSAMPLING_411``
      - 水平方向上以 4 的比例对 Cr 和 Cb 组件进行子采样
    * - ``V4L2_JPEG_CHROMA_SUBSAMPLING_410``
      - 在水平方向上以 4 的比例，在垂直方向上以 2 的比例对 Cr 和 Cb 组件进行子采样
    * - ``V4L2_JPEG_CHROMA_SUBSAMPLING_GRAY``
      - 只使用亮度分量
``V4L2_CID_JPEG_RESTART_INTERVAL (integer)``
    重启间隔决定了插入 RSTm 标记（m = 0..7）的间隔。这些标记的目的是为了额外重置编码过程，以便独立处理图像块。对于有损压缩过程，重启间隔单位是 MCU（最小编码单元），其值包含在 DRI（定义重启间隔）标记中。如果将 ``V4L2_CID_JPEG_RESTART_INTERVAL`` 控制设置为 0，则不会插入 DRI 和 RSTm 标记。
.. _jpeg-quality-control:

``V4L2_CID_JPEG_COMPRESSION_QUALITY (整数)``
    确定图像质量和大小之间的权衡。
它为应用程序提供了一种更简单的方法来控制图像质量，而无需直接重新配置亮度和色度量化表。在驱动程序使用应用程序通过其他接口定义的量化表的情况下，应由驱动程序将 ``V4L2_CID_JPEG_COMPRESSION_QUALITY`` 控制设置为 0。
此控制的值范围取决于具体的驱动程序。只有正数且非零的值才有意义。推荐的范围是 1 - 100，其中较大的值对应更好的图像质量。

.. _jpeg-active-marker-control:

``V4L2_CID_JPEG_ACTIVE_MARKER (位掩码)``
    指定压缩流中包含哪些JPEG标记。此控制仅对编码器有效。
.. flat-table::
    :header-rows:  0
    :stub-columns: 0

    * - ``V4L2_JPEG_ACTIVE_MARKER_APP0``
      - 应用数据段 APP\ :sub:`0`
    * - ``V4L2_JPEG_ACTIVE_MARKER_APP1``
      - 应用数据段 APP\ :sub:`1`
    * - ``V4L2_JPEG_ACTIVE_MARKER_COM``
      - 注释段
    * - ``V4L2_JPEG_ACTIVE_MARKER_DQT``
      - 量化表段
    * - ``V4L2_JPEG_ACTIVE_MARKER_DHT``
      - 霍夫曼表段

有关JPEG规范的更多详细信息，请参阅 :ref:`itu-t81`，:ref:`jfif`，:ref:`w3c-jpeg-jfif`。
当然，请提供您需要翻译的文本。
