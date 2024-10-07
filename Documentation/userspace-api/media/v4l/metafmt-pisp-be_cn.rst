SPDX 许可声明标识符: GPL-2.0

.. _v4l2-meta-fmt-rpi-be-cfg:

************************
V4L2_META_FMT_RPI_BE_CFG
************************

树莓派 PiSP 后端配置格式
===============================================

树莓派 PiSP 后端是一个内存到内存的图像信号处理器，用户空间通过向 `pispbe-config` 输出视频设备节点提供一个配置参数缓冲区来对其进行配置，使用 :c:type:`v4l2_meta_format` 接口。PiSP 后端以块（tiles）的形式处理图像，并且其配置需要通过填充在 ``pisp_be_config.h`` 头文件中定义的 :c:type:`pisp_be_tiles_config` 成员来指定两组不同的参数。`树莓派 PiSP 技术规范 <https://datasheets.raspberrypi.com/camera/raspberry-pi-image-signal-processor-specification.pdf>`_ 提供了详细的 ISP 后端配置和编程模型描述。

全局配置数据
-------------------------

全局配置数据描述了如何处理特定图像中的像素，因此这些数据在整个图像的所有块中是共享的。例如，镜头阴影校正（LSC）或降噪参数将对同一帧中的所有块通用。
全局配置数据通过填充 :c:type:`pisp_be_config` 的成员传递给 ISP。

块参数
---------------

由于 ISP 以块的方式处理图像，每组块参数描述了图像中的单个块将如何被处理。一组块参数由 160 字节的数据组成，并且为了处理一批块，需要多组块参数。
块参数通过填充 :c:type:`pisp_be_tiles_config` 中的 ``pisp_tile`` 和 ``num_tiles`` 字段传递给 ISP。

树莓派 PiSP 后端 uAPI 数据类型
==========================================

本节描述了树莓派 PiSP 后端暴露给用户空间的数据类型。该部分仅供参考，对于每个字段的详细描述，请参见 `树莓派 PiSP 技术规范 <https://datasheets.raspberrypi.com/camera/raspberry-pi-image-signal-processor-specification.pdf>`_。

.. kernel-doc:: include/uapi/linux/media/raspberrypi/pisp_be_config.h
