SPDX 许可证标识符: GFDL-1.1-no-invariants-or-later

.. _image-process-controls:

**************************************
图像处理控制参考
**************************************

图像处理控制类旨在对图像处理功能进行低级控制。与 ``V4L2_CID_IMAGE_SOURCE_CLASS`` 不同，此类中的控制影响图像的处理，而不是控制图像的捕获。
.. _image-process-control-id:

图像处理控制ID
=========================

``V4L2_CID_IMAGE_PROC_CLASS (class)``
    图像处理类描述符
.. _v4l2-cid-link-freq:

``V4L2_CID_LINK_FREQ (integer menu)``
    数据总线（例如并行或CSI-2）的频率
.. _v4l2-cid-pixel-rate:

``V4L2_CID_PIXEL_RATE (64-bit integer)``
    设备像素阵列中的像素采样率。此控制是只读的，其单位为像素/秒
某些设备使用水平和垂直消隐来配置帧率。帧率可以从像素率、模拟裁剪矩形以及水平和垂直消隐计算得出。像素率控制可能出现在与消隐控制和模拟裁剪矩形配置不同的子设备中
帧率的配置通过选择所需的水平和垂直消隐来完成。此控制的单位为Hz
``V4L2_CID_TEST_PATTERN (menu)``
    某些捕获/显示/传感器设备具有生成测试图案图像的能力。这些硬件特定的测试图案可用于测试设备是否正常工作
``V4L2_CID_DEINTERLACING_MODE (menu)``
    视频去交织模式（例如Bob、Weave等）。菜单项是驱动程序特定的，并在 :ref:`uapi-v4l-drivers` 中进行了记录
``V4L2_CID_DIGITAL_GAIN (integer)``
    数字增益是所有颜色分量乘以的值。通常应用的数字增益是控制值除以例如0x100，这意味着要获得无数字增益，控制值需要为0x100。无增益配置通常是默认配置
