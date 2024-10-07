SPDX 许可证标识符: GFDL-1.1-no-invariants-or-later

.. _色彩控制:

*******************************
色彩控制参考
*******************************

色彩类包括用于在数字图像和视频中表示颜色的高动态范围（HDR）成像控制。这些控制应用于视频和图像的编码与解码，以及 HDMI 接收器和发射器中。

色彩控制 ID
-----------------------

.. _色彩控制ID:

``V4L2_CID_COLORIMETRY_CLASS (类)``
    色彩类描述符。调用此控制的 :ref:`VIDIOC_QUERYCTRL` 将返回此类控制的描述。
``V4L2_CID_COLORIMETRY_HDR10_CLL_INFO (结构体)``
    内容光亮度级别定义了图片的标称目标亮度光亮度上限。
.. c:type:: v4l2_ctrl_hdr10_cll_info

.. cssclass:: longtable

.. flat-table:: 结构体 v4l2_ctrl_hdr10_cll_info
    :header-rows:  0
    :stub-columns: 0
    :widths:       1 1 2

    * - __u16
      - ``max_content_light_level``
      - 视频序列中所有图片的样本中的最大光亮度级别的上限，单位为 cd/m\ :sup:`2`
当等于 0 时，表示没有这样的上限
* - __u16
      - ``max_pic_average_light_level``
      - 视频序列中任何单独图片样本的最大平均光亮度级别的上限，单位为 cd/m\ :sup:`2` 
当等于 0 时，表示没有这样的上限
``V4L2_CID_COLORIMETRY_HDR10_MASTERING_DISPLAY (结构体)``
    校准显示定义了被视为当前视频内容校准显示的色彩体积（色彩基色、白点和亮度范围）。
.. c:type:: v4l2_ctrl_hdr10_mastering_display

.. cssclass:: longtable

.. flat-table:: 结构体 v4l2_ctrl_hdr10_mastering_display
    :header-rows:  0
    :stub-columns: 0
    :widths:       1 1 2

    * - __u16
      - ``display_primaries_x[3]``
      - 指定校准显示的颜色基色组件 c 的归一化 x 色度坐标，增量为 0.00002
对于使用红色、绿色和蓝色作为基色的校准显示，索引值 c 等于 0 对应绿色基色，c 等于 1 对应蓝色基色，c 等于 2 对应红色基色
* - __u16
      - ``display_primaries_y[3]``
      - 指定校准显示的颜色基色组件 c 的归一化 y 色度坐标，增量为 0.00002
为了描述使用红（Red）、绿（Green）和蓝（Blue）色彩基的母版显示设备，索引值 c 等于 0 对应绿色彩基，c 等于 1 对应蓝色彩基，c 等于 2 对应红色彩基。

* - __u16
      - ``white_point_x``
      - 指定母版显示设备白点的归一化 x 色度坐标，以 0.00002 的增量表示
* - __u16
      - ``white_point_y``
      - 指定母版显示设备白点的归一化 y 色度坐标，以 0.00002 的增量表示
* - __u32
      - ``max_luminance``
      - 指定母版显示设备的标称最大亮度，单位为 0.0001 cd/m²
* - __u32
      - ``min_luminance``
      - 指定母版显示设备的标称最小亮度，单位为 0.0001 cd/m²
