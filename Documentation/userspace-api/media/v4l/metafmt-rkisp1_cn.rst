SPDX 许可声明标识符: GPL-2.0

.. _v4l2-meta-fmt-rk-isp1-params:

.. _v4l2-meta-fmt-rk-isp1-stat-3a:

*****************************************************************************
V4L2_META_FMT_RK_ISP1_PARAMS ('rk1p') 和 V4L2_META_FMT_RK_ISP1_STAT_3A ('rk1s')
*****************************************************************************

配置参数
========================

配置参数通过 :c:type:`v4l2_meta_format` 接口传递给 :ref:`rkisp1_params <rkisp1_params>` 元数据输出视频节点。缓冲区包含在 ``rkisp1-config.h`` 中定义的 C 结构 :c:type:`rkisp1_params_cfg` 的单个实例。因此，可以通过以下方式从缓冲区获取该结构：

.. code-block:: c

    struct rkisp1_params_cfg *params = (struct rkisp1_params_cfg*) buffer;

.. rkisp1_stat_buffer

3A 和直方图统计信息
===========================

ISP1 设备会收集输入 Bayer 帧的不同统计信息。这些统计信息通过 :c:type:`v4l2_meta_format` 接口从 :ref:`rkisp1_stats <rkisp1_stats>` 元数据捕获视频节点获得。缓冲区包含在 ``rkisp1-config.h`` 中定义的 C 结构 :c:type:`rkisp1_stat_buffer` 的单个实例。因此，可以通过以下方式从缓冲区获取该结构：

.. code-block:: c

    struct rkisp1_stat_buffer *stats = (struct rkisp1_stat_buffer*) buffer;

收集的统计信息包括曝光、AWB（自动白平衡）、直方图和 AF（自动对焦）。有关统计信息的详细信息，请参阅 :c:type:`rkisp1_stat_buffer`。这里描述的 3A 统计信息和配置参数通常由专用用户空间库消费和生成，这些库包含了使用软件控制环的重要调优工具。

rkisp1 用户API数据类型
======================

.. kernel-doc:: include/uapi/linux/rkisp1-config.h
