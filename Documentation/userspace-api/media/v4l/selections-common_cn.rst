.. SPDX 许可证标识符: GFDL-1.1-no-invariants-or-later

.. _v4l2-selections-common:

通用的选择定义
============================

虽然 :ref:`V4L2 选择 API <selection-api>` 和 :ref:`V4L2 子设备选择 API <v4l2-subdev-selections>` 非常相似，但两者之间有一个根本的区别。在子设备 API 中，选择矩形指的是媒体总线格式，并且与子设备的端口绑定。而在 V4L2 接口中，选择矩形指的是内存中的像素格式。本节定义了这两个 API 的选择接口的通用定义。
.. toctree::
    :maxdepth: 1

    v4l2-selection-targets
    v4l2-selection-flags
