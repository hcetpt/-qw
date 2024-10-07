.. SPDX 许可证标识符: GFDL-1.1-no-invariants-or-later

.. _pixfmt:

#############
图像格式
#############
V4L2 API 主要为与应用程序交换图像数据的设备设计。结构体 :c:type:`v4l2_pix_format` 和结构体 :c:type:`v4l2_pix_format_mplane` 定义了图像在内存中的格式和布局。前者用于单平面 API，而后者用于多平面版本（参见 :ref:`planar-apis`）。图像格式通过 :ref:`VIDIOC_S_FMT <VIDIOC_G_FMT>` ioctl 进行协商。（这里的解释主要集中在视频捕获和输出上，对于覆盖帧缓冲区格式，请参见 :ref:`VIDIOC_G_FBUF <VIDIOC_G_FBUF>`。）

.. toctree::
    :maxdepth: 1

    pixfmt-v4l2
    pixfmt-v4l2-mplane
    pixfmt-intro
    pixfmt-indexed
    pixfmt-rgb
    pixfmt-bayer
    yuv-formats
    hsv-formats
    depth-formats
    pixfmt-compressed
    sdr-formats
    tch-formats
    meta-formats
    pixfmt-reserved
    colorspaces
    colorspaces-defs
    colorspaces-details
