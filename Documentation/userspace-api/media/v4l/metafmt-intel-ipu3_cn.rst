SPDX 许可声明标识符：GPL-2.0 或 GFDL-1.1-no-invariants-or-later

.. _v4l2-meta-fmt-params:
.. _v4l2-meta-fmt-stat-3a:

******************************************************************
V4L2_META_FMT_IPU3_PARAMS ('ip3p'), V4L2_META_FMT_IPU3_3A ('ip3s')
******************************************************************

.. ipu3_uapi_stats_3a

3A 统计信息
=============

IPU3 ImgU 3A 统计加速器会收集输入的 Bayer 帧的不同统计信息。这些统计信息通过 "ipu3-imgu [01] 3a stat" 元数据捕获视频节点，使用 :c:type:`v4l2_meta_format` 接口获取。它们按照 :c:type:`ipu3_uapi_stats_3a` 结构体描述的方式格式化。
收集的统计信息包括 AWB（自动白平衡）RGBS（红、绿、蓝和饱和度测量）单元格、AWB 滤波器响应、AF（自动对焦）滤波器响应以及 AE（自动曝光）直方图。
结构体 :c:type:`ipu3_uapi_4a_config` 保存了所有可配置参数。

.. code-block:: c

    struct ipu3_uapi_stats_3a {
        struct ipu3_uapi_awb_raw_buffer awb_raw_buffer;
        struct ipu3_uapi_ae_raw_buffer_aligned ae_raw_buffer[IPU3_UAPI_MAX_STRIPES];
        struct ipu3_uapi_af_raw_buffer af_raw_buffer;
        struct ipu3_uapi_awb_fr_raw_buffer awb_fr_raw_buffer;
        struct ipu3_uapi_4a_config stats_4a_config;
        __u32 ae_join_buffers;
        __u8 padding[28];
        struct ipu3_uapi_stats_3a_bubble_info_per_stripe stats_3a_bubble_per_stripe;
        struct ipu3_uapi_ff_status stats_3a_status;
    };

.. ipu3_uapi_params

管道参数
===================

管道参数通过 :c:type:`v4l2_meta_format` 接口传递给 "ipu3-imgu [01] parameters" 元数据输出视频节点。它们按照 :c:type:`ipu3_uapi_params` 结构体描述的方式格式化。
这里描述的 3A 统计信息和管道参数与底层相机子系统（CSS）API 密切相关。通常由专用的用户空间库消费和生成，这些库包含重要的调优工具，从而让开发者无需关心低级别的硬件和算法细节。

.. code-block:: c

    struct ipu3_uapi_params {
        /* 标记下面哪些设置需要应用 */
        struct ipu3_uapi_flags use;

        /* 加速器集群参数 */
        struct ipu3_uapi_acc_param acc_param;

        /* ISP 向量地址空间参数 */
        struct ipu3_uapi_isp_lin_vmem_params lin_vmem_params;
        struct ipu3_uapi_isp_tnr3_vmem_params tnr3_vmem_params;
        struct ipu3_uapi_isp_xnr3_vmem_params xnr3_vmem_params;

        /* ISP 数据内存（DMEM）参数 */
        struct ipu3_uapi_isp_tnr3_params tnr3_dmem_params;
        struct ipu3_uapi_isp_xnr3_params xnr3_dmem_params;

        /* 光学黑电平补偿 */
        struct ipu3_uapi_obgrid_param obgrid_param;
    };

Intel IPU3 ImgU 用户 API 数据类型
===============================

.. kernel-doc:: drivers/staging/media/ipu3/include/uapi/intel-ipu3.h
