.. SPDX 许可证标识符: GFDL-1.1-no-invariants-or-later

****************************
在 V4L2 中定义色彩空间
****************************

在 V4L2 中，色彩空间由四个值定义。第一个是色彩空间标识符（枚举 :c:type:`v4l2_colorspace`），它定义了色度、默认的传输函数、默认的 Y'CbCr 编码和默认的量化方法。第二个是传输函数标识符（枚举 :c:type:`v4l2_xfer_func`），用于指定非标准传输函数。第三个是 Y'CbCr 编码标识符（枚举 :c:type:`v4l2_ycbcr_encoding`），用于指定非标准的 Y'CbCr 编码。第四个是量化标识符（枚举 :c:type:`v42_quantization`），用于指定非标准量化方法。大多数情况下，只需填写结构体 :c:type:`v4l2_pix_format` 或结构体 :c:type:`v4l2_pix_format_mplane` 的色彩空间字段。

.. _hsv-colorspace:

对于 :ref:`HSV 格式 <hsv-formats>`，*色调* 被定义为圆柱色彩表示中的角度。通常这个角度是以度数测量的，即 0-360 度。当我们把这个角度值映射到 8 位时，有两种基本的方法：将角度值除以 2（0-179），或者使用整个范围 0-255，将角度值除以 1.41。枚举 :c:type:`v4l2_hsv_encoding` 指定了使用的编码方式。
.. note:: 默认的 R'G'B' 量化对所有色彩空间都是全范围的。HSV 格式总是全范围的。

.. tabularcolumns:: |p{6.7cm}|p{10.8cm}|

.. c:type:: v4l2_colorspace

.. flat-table:: V4L2 色彩空间
    :header-rows:  1
    :stub-columns: 0

    * - 标识符
      - 详情
    * - ``V4L2_COLORSPACE_DEFAULT``
      - 默认色彩空间。应用程序可以使用此值让驱动程序填充色彩空间。
    * - ``V4L2_COLORSPACE_SMPTE170M``
      - 参见 :ref:`col-smpte-170m`
    * - ``V4L2_COLORSPACE_REC709``
      - 参见 :ref:`col-rec709`
    * - ``V4L2_COLORSPACE_SRGB``
      - 参见 :ref:`col-srgb`
    * - ``V4L2_COLORSPACE_OPRGB``
      - 参见 :ref:`col-oprgb`
    * - ``V4L2_COLORSPACE_BT2020``
      - 参见 :ref:`col-bt2020`
    * - ``V4L2_COLORSPACE_DCI_P3``
      - 参见 :ref:`col-dcip3`
* - ``V4L2_COLORSPACE_SMPTE240M``
      - 详见 :ref:`col-smpte-240m`
* - ``V4L2_COLORSPACE_470_SYSTEM_M``
      - 详见 :ref:`col-sysm`
* - ``V4L2_COLORSPACE_470_SYSTEM_BG``
      - 详见 :ref:`col-sysbg`
* - ``V4L2_COLORSPACE_JPEG``
      - 详见 :ref:`col-jpeg`
* - ``V4L2_COLORSPACE_RAW``
      - 原始色彩空间。用于原始图像捕获时，图像经过最少的处理，并使用设备内部的色彩空间。使用此“色彩空间”处理图像的软件需要了解捕获设备的内部结构
.. c:type:: v4l2_xfer_func

.. tabularcolumns:: |p{5.5cm}|p{12.0cm}|

.. flat-table:: V4L2 转移函数
    :header-rows:  1
    :stub-columns: 0

    * - 标识符
      - 详情
    * - ``V4L2_XFER_FUNC_DEFAULT``
      - 使用由色彩空间定义的默认转移函数
    * - ``V4L2_XFER_FUNC_709``
      - 使用 Rec. 709 转移函数
    * - ``V4L2_XFER_FUNC_SRGB``
      - 使用 sRGB 转移函数
    * - ``V4L2_XFER_FUNC_OPRGB``
      - 使用 opRGB 转移函数
    * - ``V4L2_XFER_FUNC_SMPTE240M``
      - 使用 SMPTE 240M 转移函数
* - ``V4L2_XFER_FUNC_NONE``
      - 不使用传输函数（即使用线性RGB值）
* - ``V4L2_XFER_FUNC_DCI_P3``
      - 使用DCI-P3传输函数
* - ``V4L2_XFER_FUNC_SMPTE2084``
      - 使用SMPTE 2084传输函数。详见 :ref:`xf-smpte-2084`

.. c:type:: v4l2_ycbcr_encoding

.. tabularcolumns:: |p{7.2cm}|p{10.3cm}|

.. flat-table:: V4L2 Y'CbCr 编码
    :header-rows:  1
    :stub-columns: 0

    * - 标识符
      - 详细信息
    * - ``V4L2_YCBCR_ENC_DEFAULT``
      - 使用由颜色空间定义的默认Y'CbCr编码
    * - ``V4L2_YCBCR_ENC_601``
      - 使用BT.601 Y'CbCr编码
    * - ``V4L2_YCBCR_ENC_709``
      - 使用Rec. 709 Y'CbCr编码
    * - ``V4L2_YCBCR_ENC_XV601``
      - 使用扩展色域xvYCC BT.601编码
    * - ``V4L2_YCBCR_ENC_XV709``
      - 使用扩展色域xvYCC Rec. 709编码
    * - ``V4L2_YCBCR_ENC_BT2020``
      - 使用默认的非恒定亮度BT.2020 Y'CbCr编码
    * - ``V4L2_YCBCR_ENC_BT2020_CONST_LUM``
      - 使用恒定亮度BT.2020 Yc'CbcCrc编码
* - ``V4L2_YCBCR_ENC_SMPTE_240M``
  - 使用 SMPTE 240M 的 Y'CbCr 编码
.. c:type:: v4l2_hsv_encoding

.. tabularcolumns:: |p{6.5cm}|p{11.0cm}|

.. flat-table:: V4L2 HSV 编码
    :header-rows:  1
    :stub-columns: 0

    * - 标识符
      - 详情
    * - ``V4L2_HSV_ENC_180``
      - 对于色相，每个最低有效位（LSB）表示两度
    * - ``V4L2_HSV_ENC_256``
      - 对于色相，360度被映射到8位中，即每个最低有效位大约为1.41度
.. c:type:: v4l2_quantization

.. tabularcolumns:: |p{6.5cm}|p{11.0cm}|

.. flat-table:: V4L2 量化方法
    :header-rows:  1
    :stub-columns: 0

    * - 标识符
      - 详情
    * - ``V4L2_QUANTIZATION_DEFAULT``
      - 使用由颜色空间定义的默认量化编码。对于 R'G'B' 和 HSV 总是使用全范围。对于 Y'CbCr 通常使用有限范围
    * - ``V4L2_QUANTIZATION_FULL_RANGE``
      - 使用全范围量化编码。即范围 [0…1] 映射到 [0…255]（可能裁剪到 [1…254] 以避免 0x00 和 0xff 值）。Cb 和 Cr 从 [-0.5…0.5] 映射到 [0…255]（可能裁剪到 [1…254] 以避免 0x00 和 0xff 值）
    * - ``V4L2_QUANTIZATION_LIM_RANGE``
      - 使用有限范围量化编码。即范围 [0…1] 映射到 [16…235]。Cb 和 Cr 从 [-0.5…0.5] 映射到 [16…240]。有限范围不能与 HSV 一起使用
