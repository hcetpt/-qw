.. SPDX 许可证标识符: GFDL-1.1-no-invariants-or-later

.. _common:

###################
通用 API 元素
###################
编程一个 V4L2 设备包括以下步骤：

- 打开设备

- 更改设备属性，选择视频和音频输入，视频标准，图片亮度等
- 协商数据格式

- 协商输入/输出方法

- 实际的输入/输出循环

- 关闭设备

在实际操作中，大多数步骤是可选的，并且可以按任意顺序执行。这取决于 V4L2 设备类型，详细信息可以在 :ref:`devices` 中阅读。在本章中，我们将讨论适用于所有设备的基本概念。

.. toctree::
    :maxdepth: 1

    open
    querycap
    app-pri
    video
    audio
    tuner
    standard
    dv-timings
    control
    extended-controls
    ext-ctrls-camera
    ext-ctrls-flash
    ext-ctrls-image-source
    ext-ctrls-image-process
    ext-ctrls-codec
    ext-ctrls-codec-stateless
    ext-ctrls-jpeg
    ext-ctrls-dv
    ext-ctrls-rf-tuner
    ext-ctrls-fm-tx
    ext-ctrls-fm-rx
    ext-ctrls-detect
    ext-ctrls-colorimetry
    fourcc
    format
    planar-apis
    selection-api
    crop
    streaming-par
