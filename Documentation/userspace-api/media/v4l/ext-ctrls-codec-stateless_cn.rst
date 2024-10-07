```spdx
许可协议标识符: GFDL-1.1-no-invariants-or-later

.. _无状态编解码器状态控制:

*********************************
无状态编解码器控制参考
*********************************

无状态编解码器控制类旨在支持无状态的解码器和编码器（即硬件加速器）。
这些驱动通常由 :ref:`无状态解码器` 支持，并处理解析后的像素格式，如 V4L2_PIX_FMT_H264_SLICE
无状态编解码器控制ID
==========================

.. _无状态编解码器控制ID:

``V4L2_CID_CODEC_STATELESS_CLASS (class)``
    无状态编解码器类描述符
.. _v4l2-codec-stateless-h264:

``V4L2_CID_STATELESS_H264_SPS (struct)``
    指定与关联的H264切片数据相关的序列参数集（从比特流中提取）。这包括配置无状态硬件解码流水线所需的必要参数。比特流参数根据 :ref:`h264` 第 7.4.2.1.1 节 "序列参数集数据语义" 定义。对于进一步的文档，请参阅上述规范，除非有明确的注释说明。
.. c:type:: v4l2_ctrl_h264_sps

.. raw:: latex

    \small

.. tabularcolumns:: |p{1.2cm}|p{8.6cm}|p{7.5cm}|

.. flat-table:: struct v4l2_ctrl_h264_sps
    :header-rows:  0
    :stub-columns: 0
    :widths:       1 1 2

    * - __u8
      - ``profile_idc``
      -
    * - __u8
      - ``constraint_set_flags``
      - 参见 :ref:`序列参数集约束标志 <h264_sps_constraints_set_flags>`
    * - __u8
      - ``level_idc``
      -
    * - __u8
      - ``seq_parameter_set_id``
      -
    * - __u8
      - ``chroma_format_idc``
      -
    * - __u8
      - ``bit_depth_luma_minus8``
      -
    * - __u8
      - ``bit_depth_chroma_minus8``
      -
    * - __u8
      - ``log2_max_frame_num_minus4``
      -
    * - __u8
      - ``pic_order_cnt_type``
      -
    * - __u8
      - ``log2_max_pic_order_cnt_lsb_minus4``
      -
    * - __u8
      - ``max_num_ref_frames``
      -
    * - __u8
      - ``num_ref_frames_in_pic_order_cnt_cycle``
      -
    * - __s32
      - ``offset_for_ref_frame[255]``
      -
    * - __s32
      - ``offset_for_non_ref_pic``
      -
    * - __s32
      - ``offset_for_top_to_bottom_field``
      -
    * - __u16
      - ``pic_width_in_mbs_minus1``
      -
    * - __u16
      - ``pic_height_in_map_units_minus1``
      -
    * - __u32
      - ``flags``
      - 参见 :ref:`序列参数集标志 <h264_sps_flags>`

.. raw:: latex

    \normalsize

.. _h264_sps_constraints_set_flags:

``序列参数集约束标志``

.. cssclass:: longtable

.. flat-table::
    :header-rows:  0
    :stub-columns: 0
    :widths:       1 1 2

    * - ``V4L2_H264_SPS_CONSTRAINT_SET0_FLAG``
      - 0x00000001
      -
    * - ``V4L2_H264_SPS_CONSTRAINT_SET1_FLAG``
      - 0x00000002
      -
    * - ``V4L2_H264_SPS_CONSTRAINT_SET2_FLAG``
      - 0x00000004
      -
    * - ``V4L2_H264_SPS_CONSTRAINT_SET3_FLAG``
      - 0x00000008
      -
    * - ``V4L2_H264_SPS_CONSTRAINT_SET4_FLAG``
      - 0x00000010
      -
    * - ``V4L2_H264_SPS_CONSTRAINT_SET5_FLAG``
      - 0x00000020
      -

.. _h264_sps_flags:

``序列参数集标志``

.. cssclass:: longtable

.. flat-table::
    :header-rows:  0
    :stub-columns: 0
    :widths:       1 1 2

    * - ``V4L2_H264_SPS_FLAG_SEPARATE_COLOUR_PLANE``
      - 0x00000001
      -
    * - ``V4L2_H264_SPS_FLAG_QPPRIME_Y_ZERO_TRANSFORM_BYPASS``
      - 0x00000002
      -
    * - ``V4L2_H264_SPS_FLAG_DELTA_PIC_ORDER_ALWAYS_ZERO``
      - 0x00000004
      -
    * - ``V4L2_H264_SPS_FLAG_GAPS_IN_FRAME_NUM_VALUE_ALLOWED``
      - 0x00000008
      -
    * - ``V4L2_H264_SPS_FLAG_FRAME_MBS_ONLY``
      - 0x00000010
      -
    * - ``V4L2_H264_SPS_FLAG_MB_ADAPTIVE_FRAME_FIELD``
      - 0x00000020
      -
    * - ``V4L2_H264_SPS_FLAG_DIRECT_8X8_INFERENCE``
      - 0x00000040
      -

``V4L2_CID_STATELESS_H264_PPS (struct)``
    指定与关联的H264切片数据相关的图片参数集（从比特流中提取）。这包括配置无状态硬件解码流水线所需的必要参数。比特流参数根据 :ref:`h264` 第 7.4.2.2 节 "图片参数集RBSP语义" 定义。对于进一步的文档，请参阅上述规范，除非有明确的注释说明。
.. c:type:: v4l2_ctrl_h264_pps

.. raw:: latex

    \small

.. flat-table:: struct v4l2_ctrl_h264_pps
    :header-rows:  0
    :stub-columns: 0
    :widths:       1 1 2

    * - __u8
      - ``pic_parameter_set_id``
      -
    * - __u8
      - ``seq_parameter_set_id``
      -
    * - __u8
      - ``num_slice_groups_minus1``
      -
    * - __u8
      - ``num_ref_idx_l0_default_active_minus1``
      -
    * - __u8
      - ``num_ref_idx_l1_default_active_minus1``
      -
    * - __u8
      - ``weighted_bipred_idc``
      -
    * - __s8
      - ``pic_init_qp_minus26``
      -
    * - __s8
      - ``pic_init_qs_minus26``
      -
    * - __s8
      - ``chroma_qp_index_offset``
      -
    * - __s8
      - ``second_chroma_qp_index_offset``
      -
    * - __u16
      - ``flags``
      - 参见 :ref:`图片参数集标志 <h264_pps_flags>`

.. raw:: latex

    \normalsize

.. _h264_pps_flags:

``图片参数集标志``

.. raw:: latex

    \begingroup
    \scriptsize
    \setlength{\tabcolsep}{2pt}

.. tabularcolumns:: |p{9.8cm}|p{1.0cm}|p{6.5cm}|

.. flat-table::
    :header-rows:  0
    :stub-columns: 0
    :widths:       10 1 4

    * - ``V4L2_H264_PPS_FLAG_ENTROPY_CODING_MODE``
      - 0x0001
      -
    * - ``V4L2_H264_PPS_FLAG_BOTTOM_FIELD_PIC_ORDER_IN_FRAME_PRESENT``
      - 0x0002
      -
    * - ``V4L2_H264_PPS_FLAG_WEIGHTED_PRED``
      - 0x0004
      -
    * - ``V4L2_H264_PPS_FLAG_DEBLOCKING_FILTER_CONTROL_PRESENT``
      - 0x0008
      -
    * - ``V4L2_H264_PPS_FLAG_CONSTRAINED_INTRA_PRED``
      - 0x0010
      -
    * - ``V4L2_H264_PPS_FLAG_REDUNDANT_PIC_CNT_PRESENT``
      - 0x0020
      -
    * - ``V4L2_H264_PPS_FLAG_TRANSFORM_8X8_MODE``
      - 0x0040
      -
    * - ``V4L2_H264_PPS_FLAG_SCALING_MATRIX_PRESENT``
      - 0x0080
      - 必须使用 ``V4L2_CID_STATELESS_H264_SCALING_MATRIX`` 来处理该图片
.. raw:: latex

    \endgroup

``V4L2_CID_STATELESS_H264_SCALING_MATRIX (struct)``
    指定与关联的H264切片数据相关的缩放矩阵（从比特流中提取）。比特流参数根据 :ref:`h264` 第 7.4.2.1.1.1 节 "缩放列表语义" 定义。对于进一步的文档，请参阅上述规范，除非有明确的注释说明。
.. c:type:: v4l2_ctrl_h264_scaling_matrix

.. raw:: latex

    \small

.. tabularcolumns:: |p{0.6cm}|p{4.8cm}|p{11.9cm}|

.. flat-table:: struct v4l2_ctrl_h264_scaling_matrix
    :header-rows:  0
    :stub-columns: 0
    :widths:       1 1 2

    * - __u8
      - ``scaling_list_4x4[6][16]``
      - 应用逆扫描过程后的缩放矩阵。预期的列表顺序为 Intra Y、Intra Cb、Intra Cr、Inter Y、Inter Cb、Inter Cr。每个缩放列表中的值预期以光栅扫描顺序排列。
    * - __u8
      - ``scaling_list_8x8[6][64]``
      - 应用逆扫描过程后的缩放矩阵。
```
期望的列表顺序是：Intra Y、Inter Y、Intra Cb、Inter Cb、Intra Cr、Inter Cr。每个缩放列表中的值应按照光栅扫描顺序排列。

``V4L2_CID_STATELESS_H264_SLICE_PARAMS (struct)``
    指定与H264片数据相关的片参数（从比特流中提取）。这包括配置H264无状态硬件解码流水线所需的必要参数。比特流参数根据 :ref:`h264`，第7.4.3节“Slice Header Semantics”定义。进一步的文档请参考上述规范，除非有明确说明。

.. c:type:: v4l2_ctrl_h264_slice_params

.. raw:: latex

    \small

.. tabularcolumns:: |p{4.0cm}|p{5.9cm}|p{7.4cm}|

.. flat-table:: struct v4l2_ctrl_h264_slice_params
    :header-rows:  0
    :stub-columns: 0
    :widths:       1 1 2

    * - __u32
      - ``header_bit_size``
      - 从该片开始到slice_data()的位偏移量
* - __u32
      - ``first_mb_in_slice``
      -
    * - __u8
      - ``slice_type``
      -
    * - __u8
      - ``colour_plane_id``
      -
    * - __u8
      - ``redundant_pic_cnt``
      -
    * - __u8
      - ``cabac_init_idc``
      -
    * - __s8
      - ``slice_qp_delta``
      -
    * - __s8
      - ``slice_qs_delta``
      -
    * - __u8
      - ``disable_deblocking_filter_idc``
      -
    * - __s8
      - ``slice_alpha_c0_offset_div2``
      -
    * - __s8
      - ``slice_beta_offset_div2``
      -
    * - __u8
      - ``num_ref_idx_l0_active_minus1``
      - 如果num_ref_idx_active_override_flag未设置，则该字段必须设置为num_ref_idx_l0_default_active_minus1的值
    * - __u8
      - ``num_ref_idx_l1_active_minus1``
      - 如果num_ref_idx_active_override_flag未设置，则该字段必须设置为num_ref_idx_l1_default_active_minus1的值
    * - __u8
      - ``reserved``
      - 应用程序和驱动程序必须将其设置为零
* - struct :c:type:`v4l2_h264_reference`
      - ``ref_pic_list0[32]``
      - 应用每片修改后的参考图片列表
    * - struct :c:type:`v4l2_h264_reference`
      - ``ref_pic_list1[32]``
      - 应用每片修改后的参考图片列表
    * - __u32
      - ``flags``
      - 参见 :ref:`Slice Parameter Flags <h264_slice_flags>`

.. raw:: latex

    \normalsize

.. _h264_slice_flags:

``Slice Parameter Set Flags``

.. cssclass:: longtable

.. flat-table::
    :header-rows:  0
    :stub-columns: 0
    :widths:       1 1 2

    * - ``V4L2_H264_SLICE_FLAG_DIRECT_SPATIAL_MV_PRED``
      - 0x00000001
      -
    * - ``V4L2_H264_SLICE_FLAG_SP_FOR_SWITCH``
      - 0x00000002
      -

``V4L2_CID_STATELESS_H264_PRED_WEIGHTS (struct)``
    预测权值表根据 :ref:`h264`，第7.4.3.2节“Prediction Weight Table Semantics”定义。
    应用程序在7.3.3节“Slice header syntax”解释的条件下必须传递预测权值表。
.. c:type:: v4l2_ctrl_h264_pred_weights

.. raw:: latex

    \small

.. tabularcolumns:: |p{4.9cm}|p{4.9cm}|p{7.5cm}|

.. flat-table:: struct v4l2_ctrl_h264_pred_weights
    :header-rows:  0
    :stub-columns: 0
    :widths:       1 1 2

    * - __u16
      - ``luma_log2_weight_denom``
      -
    * - __u16
      - ``chroma_log2_weight_denom``
      -
    * - struct :c:type:`v4l2_h264_weight_factors`
      - ``weight_factors[2]``
      - 索引0处的权重因子为参考列表0的权重因子，索引1处的权重因子为参考列表1的权重因子
.. raw:: latex

    \normalsize

.. c:type:: v4l2_h264_weight_factors

.. raw:: latex

    \small

.. tabularcolumns:: |p{1.0cm}|p{4.5cm}|p{11.8cm}|

.. flat-table:: struct v4l2_h264_weight_factors
    :header-rows:  0
    :stub-columns: 0
    :widths:       1 1 2

    * - __s16
      - ``luma_weight[32]``
      -
    * - __s16
      - ``luma_offset[32]``
      -
    * - __s16
      - ``chroma_weight[32][2]``
      -
    * - __s16
      - ``chroma_offset[32][2]``
      -

.. raw:: latex

    \normalsize

``Picture Reference``

.. c:type:: v4l2_h264_reference

.. cssclass:: longtable

.. flat-table:: struct v4l2_h264_reference
    :header-rows:  0
    :stub-columns: 0
    :widths:       1 1 2

    * - __u8
      - ``fields``
      - 指定如何引用图片。参见 :ref:`Reference Fields <h264_ref_fields>`
    * - __u8
      - ``index``
      - 索引到 :c:type:`v4l2_ctrl_h264_decode_params`.dpb 数组

.. _h264_ref_fields:

``Reference Fields``

.. raw:: latex

    \small

.. tabularcolumns:: |p{5.4cm}|p{0.8cm}|p{11.1cm}|

.. flat-table::
    :header-rows:  0
    :stub-columns: 0
    :widths:       1 1 2

    * - ``V4L2_H264_TOP_FIELD_REF``
      - 0x1
      - 场对中的顶部场用于短期参考
* - ``V4L2_H264_BOTTOM_FIELD_REF``
      - 0x2
      - 场对中的底部场用于短期参考
* - ``V4L2_H264_FRAME_REF``
  - 0x3
  - 帧（或顶/底场，如果是场对）用于短期参考
.. raw:: latex

    \normalsize

``V4L2_CID_STATELESS_H264_DECODE_PARAMS (struct)``
    指定与H264片数据相关的解码参数（从比特流中提取）。这包括配置H264无状态硬件解码流水线所需的必要参数。比特流参数根据 :ref:`h264` 定义。对于进一步的文档，请参阅上述规范，除非有明确注释说明其他情况。
.. c:type:: v4l2_ctrl_h264_decode_params

.. raw:: latex

    \small

.. tabularcolumns:: |p{4.0cm}|p{5.9cm}|p{7.4cm}|

.. flat-table:: struct v4l2_ctrl_h264_decode_params
    :header-rows:  0
    :stub-columns: 0
    :widths:       1 1 2

    * - struct :c:type:`v4l2_h264_dpb_entry`
      - ``dpb[16]``
      -
    * - __u16
      - ``nal_ref_idc``
      - 来自NAL单元头的NAL参考ID值
    * - __u16
      - ``frame_num``
      -
    * - __s32
      - ``top_field_order_cnt``
      - 编码顶场的图像顺序计数
    * - __s32
      - ``bottom_field_order_cnt``
      - 编码底场的图像顺序计数
    * - __u16
      - ``idr_pic_id``
      -
    * - __u16
      - ``pic_order_cnt_lsb``
      -
    * - __s32
      - ``delta_pic_order_cnt_bottom``
      -
    * - __s32
      - ``delta_pic_order_cnt0``
      -
    * - __s32
      - ``delta_pic_order_cnt1``
      -
    * - __u32
      - ``dec_ref_pic_marking_bit_size``
      - dec_ref_pic_marking()语法元素的位大小
* - __u32
      - ``pic_order_cnt_bit_size``
      - 图像顺序计数相关语法元素的组合位大小：pic_order_cnt_lsb、delta_pic_order_cnt_bottom、delta_pic_order_cnt0 和 delta_pic_order_cnt1
* - __u32
      - ``slice_group_change_cycle``
      -
    * - __u32
      - ``reserved``
      - 应用程序和驱动程序必须将其设置为零
* - __u32
      - ``flags``
      - 参见 :ref:`Decode Parameters Flags <h264_decode_params_flags>`

.. raw:: latex

    \normalsize

.. _h264_decode_params_flags:

``解码参数标志``

.. raw:: latex

    \small

.. tabularcolumns:: |p{8.3cm}|p{2.1cm}|p{6.9cm}|

.. flat-table::
    :header-rows:  0
    :stub-columns: 0
    :widths:       1 1 2

    * - ``V4L2_H264_DECODE_PARAM_FLAG_IDR_PIC``
      - 0x00000001
      - 该图像是一个IDR图像
    * - ``V4L2_H264_DECODE_PARAM_FLAG_FIELD_PIC``
      - 0x00000002
      -
    * - ``V4L2_H264_DECODE_PARAM_FLAG_BOTTOM_FIELD``
      - 0x00000004
      -
    * - ``V4L2_H264_DECODE_PARAM_FLAG_PFRAME``
      - 0x00000008
      -
    * - ``V4L2_H264_DECODE_PARAM_FLAG_BFRAME``
      - 0x00000010
      -

.. raw:: latex

    \normalsize

.. c:type:: v4l2_h264_dpb_entry

.. raw:: latex

    \small

.. tabularcolumns:: |p{1.0cm}|p{4.9cm}|p{11.4cm}|

.. flat-table:: struct v4l2_h264_dpb_entry
    :header-rows:  0
    :stub-columns: 0
    :widths:       1 1 2

    * - __u64
      - ``reference_ts``
      - 作为参考使用的V4L2捕获缓冲区的时间戳，用于B编码和P编码帧。时间戳指的是 :c:type:`v4l2_buffer` 结构中的 ``timestamp`` 字段。使用 :c:func:`v4l2_timeval_to_ns()` 函数将 :c:type:`v4l2_buffer` 结构中的 :c:type:`timeval` 结构转换为 __u64
* - __u32
      - ``pic_num``
      - 对于短期参考，此值必须匹配派生值 PicNum (8-28)，而对于长期参考，它必须匹配派生值 LongTermPicNum (8-29)。在解码帧（而非场）时，pic_num 等同于 FrameNumWrap
* - __u16
      - ``frame_num``
      - 对于短期参考，此值必须匹配片头语法中的 frame_num 值（如果需要，驱动程序会处理这个值）。对于长期参考，此值必须设置为 dec_ref_pic_marking() 语法中描述的 long_term_frame_idx 的值
* - __u8
      - ``fields``
      - 指定如何引用DPB条目。参见 :ref:`Reference Fields <h264_ref_fields>`
    * - __u8
      - ``reserved[5]``
      - 应用程序和驱动程序必须将其设置为零
* - __s32
      - ``top_field_order_cnt``
      -
    * - __s32
      - ``bottom_field_order_cnt``
      -
    * - __u32
      - ``flags``
      - 参见 :ref:`DPB Entry Flags <h264_dpb_flags>`

.. raw:: latex

    \normalsize

.. _h264_dpb_flags:

``DPB条目标志``

.. raw:: latex

    \small

.. tabularcolumns:: |p{7.7cm}|p{2.1cm}|p{7.5cm}|

.. flat-table::
    :header-rows:  0
    :stub-columns: 0
    :widths:       1 1 2

    * - ``V4L2_H264_DPB_ENTRY_FLAG_VALID``
      - 0x00000001
      - DPB条目有效（非空），应考虑其有效性
* - ``V4L2_H264_DPB_ENTRY_FLAG_ACTIVE``
  - 0x00000002
  - DPB 入口用于参考
* - ``V4L2_H264_DPB_ENTRY_FLAG_LONG_TERM``
  - 0x00000004
  - DPB 入口用于长期参考
* - ``V4L2_H264_DPB_ENTRY_FLAG_FIELD``
  - 0x00000008
  - DPB 入口是一个单独的场或互补场对

.. raw:: latex

    \normalsize

``V4L2_CID_STATELESS_H264_DECODE_MODE (枚举类型)``
    指定要使用的解码模式。目前支持基于片（slice）和基于帧（frame）的解码，但将来可能会添加新的模式。
此控制用于修改 V4L2_PIX_FMT_H264_SLICE 像素格式。支持 V4L2_PIX_FMT_H264_SLICE 的应用程序必须设置此控制以指定预期的缓冲区解码模式。
驱动程序可以根据其支持的情况暴露单个或多个解码模式。

.. c:type:: v4l2_stateless_h264_decode_mode

.. raw:: latex

    \scriptsize

.. tabularcolumns:: |p{7.4cm}|p{0.3cm}|p{9.6cm}|

.. flat-table::
    :header-rows:  0
    :stub-columns: 0
    :widths:       1 1 2

    * - ``V4L2_STATELESS_H264_DECODE_MODE_SLICE_BASED``
      - 0
      - 解码在片级别进行
输出缓冲区必须包含一个片
当选择此模式时，应设置 ``V4L2_CID_STATELESS_H264_SLICE_PARAMS`` 控制。当多个片组成一帧时，
需要使用 ``V4L2_BUF_CAP_SUPPORTS_M2M_HOLD_CAPTURE_BUF`` 标志
* - ``V4L2_STATELESS_H264_DECODE_MODE_FRAME_BASED``
      - 1
      - 解码在帧级别进行
输出缓冲区必须包含解码所需的所有片。输出缓冲区还必须包含两个场
此模式将由在硬件中解析片元（slice）头部的设备支持。当选择此模式时，不应设置 ``V4L2_CID_STATELESS_H264_SLICE_PARAMS`` 控制。

.. raw:: latex

    \normalsize

``V4L2_CID_STATELESS_H264_START_CODE (枚举)``
    指定每个片元预期的H264片元起始码。
    
此控制用于修改V4L2_PIX_FMT_H264_SLICE像素格式。支持V4L2_PIX_FMT_H264_SLICE的应用程序必须设置此控制以指定缓冲区中预期的起始码。
驱动程序可以暴露一个或多个起始码，具体取决于它们能够支持的情况。

.. c:type:: v4l2_stateless_h264_start_code

.. raw:: latex

    \small

.. tabularcolumns:: |p{7.9cm}|p{0.4cm}|p{9.0cm}|

.. flat-table::
    :header-rows:  0
    :stub-columns: 0
    :widths:       4 1 4

    * - ``V4L2_STATELESS_H264_START_CODE_NONE``
      - 0
      - 选择此值指定H264片元在没有任何起始码的情况下传递给驱动程序。比特流数据应符合 :ref:`h264` 7.3.1 NAL单元语法，因此在需要时包含防止模拟的字节。
* - ``V4L2_STATELESS_H264_START_CODE_ANNEX_B``
      - 1
      - 选择此值指定H264片元预期带有Annex B起始码。根据 :ref:`h264`，有效的起始码可以是3字节的0x000001或4字节的0x00000001。

.. raw:: latex

    \normalsize

.. _codec-stateless-fwht:

``V4L2_CID_STATELESS_FWHT_PARAMS (结构体)``
    指定与FWHT（快速Walsh-Hadamard变换）数据相关的FWHT参数（从比特流中提取）。这包括配置无状态硬件解码流水线所需的参数。
    
此编解码器特定于vicodec测试驱动程序。

.. c:type:: v4l2_ctrl_fwht_params

.. raw:: latex

    \small

.. tabularcolumns:: |p{1.4cm}|p{3.9cm}|p{12.0cm}|

.. flat-table:: struct v4l2_ctrl_fwht_params
    :header-rows:  0
    :stub-columns: 0
    :widths:       1 1 2

    * - __u64
      - ``backward_ref_ts``
      - 用于作为后向参考的V4L2捕获缓冲区的时间戳，用于P编码帧。时间戳指的是 :c:type:`v4l2_buffer` 结构中的 ``timestamp`` 字段。使用 :c:func:`v4l2_timeval_to_ns()` 函数将 :c:type:`timeval` 结构转换为 __u64。
* - __u32
      - ``version``
      - 编码器版本。设置为 ``V4L2_FWHT_VERSION``。
* - `__u32`
  - `width`
  - 帧的宽度
* - `__u32`
  - `height`
  - 帧的高度
* - `__u32`
  - `flags`
  - 帧的标志，参见 :ref:`fwht-flags`
* - `__u32`
  - `colorspace`
  - 帧的颜色空间，来自枚举 :c:type:`v4l2_colorspace`
* - `__u32`
  - `xfer_func`
  - 转换函数，来自枚举 :c:type:`v4l2_xfer_func`
* - `__u32`
  - `ycbcr_enc`
  - Y'CbCr 编码，来自枚举 :c:type:`v4l2_ycbcr_encoding`
* - `__u32`
  - `quantization`
  - 量化范围，来自枚举 :c:type:`v4l2_quantization`

.. raw:: latex

    \normalsize

.. _fwht-flags:

FWHT 标志
==========

.. raw:: latex

    \small

.. tabularcolumns:: |p{7.0cm}|p{2.3cm}|p{8.0cm}|

.. flat-table::
    :header-rows:  0
    :stub-columns: 0
    :widths:       3 1 4

    * - `V4L2_FWHT_FL_IS_INTERLACED`
      - 0x00000001
      - 如果是交错格式，则设置此标志
* - `V4L2_FWHT_FL_IS_BOTTOM_FIRST`
      - 0x00000002
      - 如果是底部优先（NTSC）的交错格式，则设置此标志
* - `V4L2_FWHT_FL_IS_ALTERNATE`
      - 0x00000004
      - 如果每个“帧”只包含一个场，则设置此标志
* - ``V4L2_FWHT_FL_IS_BOTTOM_FIELD``
      - 0x00000008
      - 如果设置了 V4L2_FWHT_FL_IS_ALTERNATE，则表示该“帧”是下场，否则是上场
* - ``V4L2_FWHT_FL_LUMA_IS_UNCOMPRESSED``
      - 0x00000010
      - 表示 Y'（亮度）平面未压缩
* - ``V4L2_FWHT_FL_CB_IS_UNCOMPRESSED``
      - 0x00000020
      - 表示 Cb 平面未压缩
* - ``V4L2_FWHT_FL_CR_IS_UNCOMPRESSED``
      - 0x00000040
      - 表示 Cr 平面未压缩
* - ``V4L2_FWHT_FL_CHROMA_FULL_HEIGHT``
      - 0x00000080
      - 表示色度平面的高度与亮度平面相同，否则色度平面的高度为亮度平面的一半
* - ``V4L2_FWHT_FL_CHROMA_FULL_WIDTH``
      - 0x00000100
      - 表示色度平面的宽度与亮度平面相同，否则色度平面的宽度为亮度平面的一半
* - ``V4L2_FWHT_FL_ALPHA_IS_UNCOMPRESSED``
      - 0x00000200
      - 表示 alpha 平面未压缩
* - ``V4L2_FWHT_FL_I_FRAME``
      - 0x00000400
      - 表示这是一个 I 帧
* - ``V4L2_FWHT_FL_COMPONENTS_NUM_MSK``
      - 0x00070000
      - 颜色组件数量减一后的值
* - ``V4L2_FWHT_FL_PIXENC_MSK``
      - 0x00180000
      - 像素编码的掩码
* - ``V4L2_FWHT_FL_PIXENC_YUV``
  - 0x00080000
  - 如果像素编码为 YUV，则设置此标志
* - ``V4L2_FWHT_FL_PIXENC_RGB``
  - 0x00100000
  - 如果像素编码为 RGB，则设置此标志
* - ``V4L2_FWHT_FL_PIXENC_HSV``
  - 0x00180000
  - 如果像素编码为 HSV，则设置此标志

.. raw:: latex

    \normalsize

.. _v4l2-codec-stateless-vp8:

``V4L2_CID_STATELESS_VP8_FRAME (struct)``
    指定与 VP8 解析帧数据相关的帧参数
这包括配置无状态硬件解码流水线所需的必要参数
比特流参数根据 :ref:`vp8` 定义

.. c:type:: v4l2_ctrl_vp8_frame

.. raw:: latex

    \small

.. tabularcolumns:: |p{7.0cm}|p{4.6cm}|p{5.7cm}|

.. cssclass:: longtable

.. flat-table:: struct v4l2_ctrl_vp8_frame
    :header-rows:  0
    :stub-columns: 0
    :widths:       1 1 2

    * - struct :c:type:`v4l2_vp8_segment`
      - ``segment``
      - 包含基于段的调整元数据的结构
* - struct :c:type:`v4l2_vp8_loop_filter`
      - ``lf``
      - 包含环路滤波器级别调整元数据的结构
* - struct :c:type:`v4l2_vp8_quantization`
      - ``quant``
      - 包含 VP8 去量化索引元数据的结构
* - struct :c:type:`v4l2_vp8_entropy`
      - ``entropy``
      - 包含 VP8 熵编码概率元数据的结构
* - 结构体 :c:type:`v4l2_vp8_entropy_coder_state`
      - ``coder_state``
      - 包含VP8熵编码器状态的结构体
* - __u16
      - ``width``
      - 帧的宽度。所有帧都必须设置
* - __u16
      - ``height``
      - 帧的高度。所有帧都必须设置
* - __u8
      - ``horizontal_scale``
      - 水平缩放因子
* - __u8
      - ``vertical_scale``
      - 垂直缩放因子
* - __u8
      - ``version``
      - 码流版本
* - __u8
      - ``prob_skip_false``
      - 表示宏块未被跳过的概率
* - __u8
      - ``prob_intra``
      - 表示宏块为帧内预测的概率
* - __u8
      - ``prob_last``
      - 表示使用最后一个参考帧进行帧间预测的概率
* - __u8
      - ``prob_gf``
      - 表示使用金色参考帧进行帧间预测的概率
* - __u8
      - ``num_dct_parts``
      - DCT系数分区的数量。必须是以下之一：1、2、4 或 8
* - __u32
      - ``first_part_size``
      - 第一个分区的大小，即控制分区的大小
* - __u32
      - ``first_part_header_bits``
      - 第一个分区头部分的位大小
* - __u32
      - ``dct_part_sizes[8]``
      - DCT 系数大小
* - __u64
      - ``last_frame_ts``
      - 用于作为最后一个参考帧的 V4L2 捕获缓冲区的时间戳，与帧间编码帧一起使用。时间戳指的是 struct :c:type:`v4l2_buffer` 中的 ``timestamp`` 字段。使用 :c:func:`v4l2_timeval_to_ns()` 函数将 struct :c:type:`v4l2_buffer` 中的 struct :c:type:`timeval` 转换为 __u64
* - __u64
      - ``golden_frame_ts``
      - 用于作为最后一个参考帧的 V4L2 捕获缓冲区的时间戳，与帧间编码帧一起使用。时间戳指的是 struct :c:type:`v4l2_buffer` 中的 ``timestamp`` 字段。使用 :c:func:`v4l2_timeval_to_ns()` 函数将 struct :c:type:`v4l2_buffer` 中的 struct :c:type:`timeval` 转换为 __u64
* - __u64
      - ``alt_frame_ts``
      - 用于作为备选参考帧的 V4L2 捕获缓冲区的时间戳，与帧间编码帧一起使用。时间戳指的是 struct :c:type:`v4l2_buffer` 中的 ``timestamp`` 字段。使用 :c:func:`v4l2_timeval_to_ns()` 函数将 struct :c:type:`v4l2_buffer` 中的 struct :c:type:`timeval` 转换为 __u64
* - __u64
      - ``flags``
      - 参见 :ref:`Frame Flags <vp8_frame_flags>`

.. raw:: latex

    \normalsize

.. _vp8_frame_flags:

``Frame Flags``

.. tabularcolumns:: |p{9.8cm}|p{0.8cm}|p{6.7cm}|

.. cssclass:: longtable

.. flat-table::
    :header-rows:  0
    :stub-columns: 0
    :widths:       1 1 2

    * - ``V4L2_VP8_FRAME_FLAG_KEY_FRAME``
      - 0x01
      - 表示该帧是否是关键帧
* - ``V4L2_VP8_FRAME_FLAG_EXPERIMENTAL``
      - 0x02
      - 实验性比特流
* - ``V4L2_VP8_FRAME_FLAG_SHOW_FRAME``
      - 0x04
      - 显示帧标志，表示该帧是否用于显示
* - ``V4L2_VP8_FRAME_FLAG_MB_NO_SKIP_COEFF``
      - 0x08
      - 启用/禁用无非零系数宏块的跳过
* - ``V4L2_VP8_FRAME_FLAG_SIGN_BIAS_GOLDEN``
      - 0x10
      - 引用黄金帧时运动矢量的符号
* - ``V4L2_VP8_FRAME_FLAG_SIGN_BIAS_ALT``
  - 0x20
  - 当参考备用帧时，运动矢量的符号

.. c:type:: v4l2_vp8_entropy_coder_state

.. cssclass:: longtable

.. tabularcolumns:: |p{1.0cm}|p{2.0cm}|p{14.3cm}|

.. flat-table:: struct v4l2_vp8_entropy_coder_state
    :header-rows:  0
    :stub-columns: 0
    :widths:       1 1 2

    * - __u8
      - ``range``
      - "Range" 的编码器状态值
    * - __u8
      - ``value``
      - "Value" 的编码器状态值
    * - __u8
      - ``bit_count``
      - 剩余比特数

* - __u8
      - ``padding``
      - 应用程序和驱动程序必须将其设置为零

.. c:type:: v4l2_vp8_segment

.. cssclass:: longtable

.. tabularcolumns:: |p{1.2cm}|p{4.0cm}|p{12.1cm}|

.. flat-table:: struct v4l2_vp8_segment
    :header-rows:  0
    :stub-columns: 0
    :widths:       1 1 2

    * - __s8
      - ``quant_update[4]``
      - 量化值更新（带符号）
    * - __s8
      - ``lf_update[4]``
      - 环路滤波器级别值更新（带符号）
    * - __u8
      - ``segment_probs[3]``
      - 段概率
    * - __u8
      - ``padding``
      - 应用程序和驱动程序必须将其设置为零
    * - __u32
      - ``flags``
      - 参见 :ref:`Segment Flags <vp8_segment_flags>`

.. _vp8_segment_flags:

``段标志 (Segment Flags)``

.. raw:: latex

    \small

.. tabularcolumns:: |p{10cm}|p{1.0cm}|p{6.3cm}|

.. flat-table::
    :header-rows:  0
    :stub-columns: 0
    :widths:       1 1 2

    * - ``V4L2_VP8_SEGMENT_FLAG_ENABLED``
      - 0x01
      - 启用/禁用基于段的调整
    * - ``V4L2_VP8_SEGMENT_FLAG_UPDATE_MAP``
      - 0x02
      - 表示宏块分割图是否在本帧中更新
    * - ``V4L2_VP8_SEGMENT_FLAG_UPDATE_FEATURE_DATA``
      - 0x04
      - 表示段特征数据是否在本帧中更新
* - ``V4L2_VP8_SEGMENT_FLAG_DELTA_VALUE_MODE``
  - 0x08
  - 如果设置，则段特性数据模式为增量值；如果未设置，则为绝对值
.. raw:: latex

    \normalsize

.. c:type:: v4l2_vp8_loop_filter

.. cssclass:: longtable

.. tabularcolumns:: |p{1.5cm}|p{3.9cm}|p{11.9cm}|

.. flat-table:: struct v4l2_vp8_loop_filter
    :header-rows:  0
    :stub-columns: 0
    :widths:       1 1 2

    * - __s8
      - ``ref_frm_delta[4]``
      - 参考帧调整（带符号）增量值
    * - __s8
      - ``mb_mode_delta[4]``
      - 宏块预测模式调整（带符号）增量值
    * - __u8
      - ``sharpness_level``
      - 锐度等级
    * - __u8
      - ``level``
      - 滤波器等级
    * - __u16
      - ``padding``
      - 应用程序和驱动程序必须将其设置为零
    * - __u32
      - ``flags``
      - 请参阅 :ref:`环路滤波器标志 <vp8_loop_filter_flags>`

.. _vp8_loop_filter_flags:

``环路滤波器标志``

.. tabularcolumns:: |p{7.0cm}|p{1.2cm}|p{9.1cm}|

.. flat-table::
    :header-rows:  0
    :stub-columns: 0
    :widths:       1 1 2

    * - ``V4L2_VP8_LF_ADJ_ENABLE``
      - 0x01
      - 启用/禁用宏块级别的环路滤波器调整
    * - ``V4L2_VP8_LF_DELTA_UPDATE``
      - 0x02
      - 指示在调整中使用的增量值是否已更新
    * - ``V4L2_VP8_LF_FILTER_TYPE_SIMPLE``
      - 0x04
      - 如果设置，表示滤波器类型为简单型；如果未设置，则为普通型
.. c:type:: v4l2_vp8_quantization

.. tabularcolumns:: |p{1.5cm}|p{3.5cm}|p{12.3cm}|

.. flat-table:: struct v4l2_vp8_quantization
    :header-rows:  0
    :stub-columns: 0
    :widths:       1 1 2

    * - __u8
      - ``y_ac_qi``
      - 亮度AC系数表索引
* - `__s8`
  - `y_dc_delta`
  - 亮度 DC 偏移值
* - `__s8`
  - `y2_dc_delta`
  - Y2 块 DC 偏移值
* - `__s8`
  - `y2_ac_delta`
  - Y2 块 AC 偏移值
* - `__s8`
  - `uv_dc_delta`
  - 色度 DC 偏移值
* - `__s8`
  - `uv_ac_delta`
  - 色度 AC 偏移值
* - `__u16`
  - `padding`
  - 应用程序和驱动程序必须将其设置为零

.. c:type:: v4l2_vp8_entropy

.. cssclass:: longtable

.. tabularcolumns:: |p{1.5cm}|p{5.8cm}|p{10.0cm}|

.. flat-table:: struct v4l2_vp8_entropy
    :header-rows:  0
    :stub-columns: 0
    :widths:       1 1 2

    * - `__u8`
      - `coeff_probs[4][8][3][11]`
      - 系数更新概率
* - `__u8`
  - `y_mode_probs[4]`
  - 亮度模式更新概率
* - `__u8`
  - `uv_mode_probs[3]`
  - 色度模式更新概率
* - `__u8`
  - `mv_probs[2][19]`
  - 运动矢量解码更新概率
* - `__u8`
  - ``padding[3]``
  - 应用程序和驱动程序必须将其设置为零
.. _v4l2-codec-stateless-mpeg2:

`V4L2_CID_STATELESS_MPEG2_SEQUENCE (struct)`
    指定与关联的MPEG-2片数据相关的序列参数（从比特流中提取）。这包括匹配比特流中序列头和序列扩展部分语法元素的字段，具体如 :ref:`mpeg2part2` 所述
.. c:type:: v4l2_ctrl_mpeg2_sequence

.. raw:: latex

    \small

.. cssclass:: longtable

.. tabularcolumns:: |p{1.4cm}|p{6.5cm}|p{9.4cm}|

.. flat-table:: struct v4l2_ctrl_mpeg2_sequence
    :header-rows:  0
    :stub-columns: 0
    :widths:       1 1 2

    * - `__u16`
      - `horizontal_size`
      - 帧亮度组件可显示部分的宽度
    * - `__u16`
      - `vertical_size`
      - 帧亮度组件可显示部分的高度
    * - `__u32`
      - `vbv_buffer_size`
      - 用于计算视频缓冲验证器所需的大小（以比特为单位），定义为：16 * 1024 * vbv_buffer_size
    * - `__u16`
      - `profile_and_level_indication`
      - 从比特流中提取的当前配置文件和级别指示
    * - `__u8`
      - `chroma_format`
      - 色度子采样格式（1: 4:2:0, 2: 4:2:2, 3: 4:4:4）
    * - `__u8`
      - `flags`
      - 参见 :ref:`MPEG-2 Sequence Flags <mpeg2_sequence_flags>`
.. _mpeg2_sequence_flags:

`MPEG-2 Sequence Flags`

.. cssclass:: longtable

.. flat-table::
    :header-rows:  0
    :stub-columns: 0
    :widths:       1 1 2

    * - `V4L2_MPEG2_SEQ_FLAG_PROGRESSIVE`
      - 0x01
      - 表明序列中的所有帧是逐行的而不是隔行的
.. raw:: latex

    \normalsize

`V4L2_CID_STATELESS_MPEG2_PICTURE (struct)`
    指定与关联的MPEG-2片数据相关的图像参数（从比特流中提取）。这包括匹配比特流中图像头和图像编码扩展部分语法元素的字段，具体如 :ref:`mpeg2part2` 所述
```markdown
.. c:type:: v4l2_ctrl_mpeg2_picture

.. raw:: latex

    \small

.. cssclass:: longtable

.. tabularcolumns:: |p{1.0cm}|p{5.6cm}|p{10.7cm}|

.. flat-table:: 结构体 v4l2_ctrl_mpeg2_picture
    :header-rows:  0
    :stub-columns: 0
    :widths:       1 1 2

    * - __u64
      - ``backward_ref_ts``
      - 用作向后参考的 V4L2 捕获缓冲区的时间戳，用于 B 帧编码和 P 帧编码。时间戳指的是结构体 :c:type:`v4l2_buffer` 中的 ``timestamp`` 字段。使用 :c:func:`v4l2_timeval_to_ns()` 函数将结构体 :c:type:`timeval` 转换为 __u64。
    * - __u64
      - ``forward_ref_ts``
      - 用作向前参考的 V4L2 捕获缓冲区的时间戳，用于 B 帧编码。时间戳指的是结构体 :c:type:`v4l2_buffer` 中的 ``timestamp`` 字段。使用 :c:func:`v4l2_timeval_to_ns()` 函数将结构体 :c:type:`timeval` 转换为 __u64。
    * - __u32
      - ``flags``
      - 请参见 :ref:`MPEG-2 图像标志 <mpeg2_picture_flags>`
    * - __u8
      - ``f_code[2][2]``
      - 运动矢量代码
    * - __u8
      - ``picture_coding_type``
      - 当前片覆盖帧的图像编码类型（V4L2_MPEG2_PIC_CODING_TYPE_I、V4L2_MPEG2_PIC_CODING_TYPE_P 或 V4L2_MPEG2_PIC_CODING_TYPE_B）
    * - __u8
      - ``picture_structure``
      - 图像结构（1：逐行顶部场，2：逐行底部场，3：逐行帧）
    * - __u8
      - ``intra_dc_precision``
      - 离散余弦变换精度（0：8 位精度，1：9 位精度，2：10 位精度，3：11 位精度）
    * - __u8
      - ``reserved[5]``
      - 应用程序和驱动程序必须将其设置为零

.. _mpeg2_picture_flags:

``MPEG-2 图像标志``

.. cssclass:: longtable

.. flat-table::
    :header-rows:  0
    :stub-columns: 0
    :widths:       1 1 2

    * - ``V4L2_MPEG2_PIC_FLAG_TOP_FIELD_FIRST``
      - 0x00000001
      - 如果设置了该标志且为逐行流，则首先输出顶部场
    * - ``V4L2_MPEG2_PIC_FLAG_FRAME_PRED_DCT``
      - 0x00000002
      - 如果设置了该标志，则仅使用帧-DCT 和帧预测
```
* - ``V4L2_MPEG2_PIC_FLAG_CONCEALMENT_MV``
      - 0x00000004
      - 如果设置，则为帧内宏块编码运动矢量
* - ``V4L2_MPEG2_PIC_FLAG_Q_SCALE_TYPE``
      - 0x00000008
      - 此标志影响反量化过程
* - ``V4L2_MPEG2_PIC_FLAG_INTRA_VLC``
      - 0x00000010
      - 此标志影响变换系数数据的解码
* - ``V4L2_MPEG2_PIC_FLAG_ALT_SCAN``
      - 0x00000020
      - 此标志影响变换系数数据的解码
* - ``V4L2_MPEG2_PIC_FLAG_REPEAT_FIRST``
      - 0x00000040
      - 此标志影响逐行帧的解码过程
* - ``V4L2_MPEG2_PIC_FLAG_PROGRESSIVE``
      - 0x00000080
      - 表示当前帧是否为逐行扫描帧
.. raw:: latex

    \normalsize

``V4L2_CID_STATELESS_MPEG2_QUANTISATION (struct)``
    指定与MPEG-2片数据相关的量化矩阵，按Z字形扫描顺序排列。此控制由内核初始化为矩阵的默认值。如果比特流传输用户定义的量化矩阵加载，应用程序应使用此控制。
    应用程序还应在需要重置量化矩阵时（例如在序列头处）通过加载默认值来设置此控制。此过程在规范的第6.3.7节“量化矩阵扩展”中进行了规定。
.. c:type:: v4l2_ctrl_mpeg2_quantisation

.. tabularcolumns:: |p{0.8cm}|p{8.0cm}|p{8.5cm}|

.. cssclass:: longtable

.. raw:: latex

    \small

.. flat-table:: struct v4l2_ctrl_mpeg2_quantisation
    :header-rows:  0
    :stub-columns: 0
    :widths:       1 1 2

    * - __u8
      - ``intra_quantiser_matrix[64]``
      - 帧内编码帧的量化矩阵系数，按Z字形扫描顺序排列。它适用于亮度和色度分量，尽管对于非4:2:0 YUV格式，它可以被特定于色度的矩阵覆盖
* - `__u8`
  - `non_intra_quantiser_matrix[64]`
  - 非帧内编码帧的量化矩阵系数，采用之字形扫描顺序。这适用于亮度和色度分量，尽管在非 4:2:0 YUV 格式中可以被特定于色度的矩阵覆盖。
* - `__u8`
  - `chroma_intra_quantiser_matrix[64]`
  - 帧内编码帧的色度分量量化矩阵系数，采用之字形扫描顺序。仅适用于非 4:2:0 YUV 格式。
* - `__u8`
  - `chroma_non_intra_quantiser_matrix[64]`
  - 非帧内编码帧的色度分量量化矩阵系数，采用之字形扫描顺序。仅适用于非 4:2:0 YUV 格式。

.. raw:: latex

    \normalsize

.. _v4l2-codec-stateless-vp9:

`V4L2_CID_STATELESS_VP9_COMPRESSED_HDR (struct)`
    存储从当前压缩帧头解析出的 VP9 概率更新。数组元素中的零值表示不更新相关概率。与运动向量相关的更新包含新值或零值。所有其他更新包含使用 inv_map_table[]（参见 :ref:`vp9` 中的 6.3.5 节）转换后的值。

.. c:type:: v4l2_ctrl_vp9_compressed_hdr

.. tabularcolumns:: |p{1cm}|p{4.8cm}|p{11.4cm}|

.. cssclass:: longtable

.. flat-table:: struct v4l2_ctrl_vp9_compressed_hdr
    :header-rows:  0
    :stub-columns: 0
    :widths:       1 1 2

    * - `__u8`
      - `tx_mode`
      - 指定 TX 模式。更多详细信息请参阅 :ref:`TX Mode <vp9_tx_mode>`
    * - `__u8`
      - `tx8[2][1]`
      - TX 8x8 概率差值
    * - `__u8`
      - `tx16[2][2]`
      - TX 16x16 概率差值
    * - `__u8`
      - `tx32[2][3]`
      - TX 32x32 概率差值
    * - `__u8`
      - `coef[4][2][2][6][6][3]`
      - 系数概率差值
    * - `__u8`
      - `skip[3]`
      - 跳过概率差值
* - __u8
  - ``inter_mode[7][3]``
  - 交错预测模式概率差值

* - __u8
  - ``interp_filter[4][2]``
  - 插值滤波器概率差值

* - __u8
  - ``is_inter[4]``
  - 是否为交错块的概率差值

* - __u8
  - ``comp_mode[5]``
  - 复合预测模式概率差值

* - __u8
  - ``single_ref[5][2]``
  - 单参考概率差值

* - __u8
  - ``comp_ref[5]``
  - 复合参考概率差值

* - __u8
  - ``y_mode[4][9]``
  - Y 预测模式概率差值

* - __u8
  - ``uv_mode[10][9]``
  - UV 预测模式概率差值

* - __u8
  - ``partition[16][3]``
  - 分区概率差值

* - __u8
  - ``mv.joint[3]``
  - 运动矢量联合概率差值
* - `__u8`
  - `mv.sign[2]`
  - 运动矢量符号概率增量
* - `__u8`
  - `mv.classes[2][10]`
  - 运动矢量类别概率增量
* - `__u8`
  - `mv.class0_bit[2]`
  - 运动矢量类别0比特概率增量
* - `__u8`
  - `mv.bits[2][10]`
  - 运动矢量比特概率增量
* - `__u8`
  - `mv.class0_fr[2][2][3]`
  - 运动矢量类别0分数比特概率增量
* - `__u8`
  - `mv.fr[2][3]`
  - 运动矢量分数比特概率增量
* - `__u8`
  - `mv.class0_hp[2]`
  - 运动矢量类别0高精度分数比特概率增量
* - `__u8`
  - `mv.hp[2]`
  - 运动矢量高精度分数比特概率增量

.. _vp9_tx_mode:

``TX 模式``

.. tabularcolumns:: |p{6.5cm}|p{0.5cm}|p{10.3cm}|

.. flat-table::
    :header-rows:  0
    :stub-columns: 0
    :widths:       1 1 2

    * - `V4L2_VP9_TX_MODE_ONLY_4X4`
      - 0
      - 变换大小为 4x4
* - `V4L2_VP9_TX_MODE_ALLOW_8X8`
      - 1
      - 变换大小可以达到 8x8
* - ``V4L2_VP9_TX_MODE_ALLOW_16X16``
      - 2
      - 变换大小可达到 16x16
* - ``V4L2_VP9_TX_MODE_ALLOW_32X32``
      - 3
      - 变换大小可达到 32x32
* - ``V4L2_VP9_TX_MODE_SELECT``
      - 4
      - 每个块的变换大小包含在比特流中

更多详细信息，请参阅 :ref:`vp9` 规范中的 '7.3.1 Tx 模式语义' 部分。

``V4L2_CID_STATELESS_VP9_FRAME (struct)``
    指定与 VP9 帧解码请求相关的帧参数。
    这包括配置 VP9 的无状态硬件解码流水线所需的参数。比特流参数根据 :ref:`vp9` 定义。

.. c:type:: v4l2_ctrl_vp9_frame

.. raw:: latex

    \small

.. tabularcolumns:: |p{4.7cm}|p{5.5cm}|p{7.1cm}|

.. cssclass:: longtable

.. flat-table:: struct v4l2_ctrl_vp9_frame
    :header-rows:  0
    :stub-columns: 0
    :widths:       1 1 2

    * - struct :c:type:`v4l2_vp9_loop_filter`
      - ``lf``
      - 环路滤波器参数。更多详细信息请参见 struct :c:type:`v4l2_vp9_loop_filter`
* - struct :c:type:`v4l2_vp9_quantization`
      - ``quant``
      - 量化参数。更多详细信息请参见 :c:type:`v4l2_vp9_quantization`
* - struct :c:type:`v4l2_vp9_segmentation`
      - ``seg``
      - 分段参数。更多详细信息请参见 :c:type:`v4l2_vp9_segmentation`
* - __u32
      - ``flags``
      - V4L2_VP9_FRAME_FLAG_* 标志的组合。更多详细信息请参见 :ref:`Frame Flags<vp9_frame_flags>`
* - __u16
      - ``compressed_header_size``
      - 压缩头大小（以字节为单位）
* - __u16
      - ``uncompressed_header_size``
      - 未压缩头大小（以字节为单位）
* - __u16
      - ``frame_width_minus_1``
      - 加上 1 可得到以像素表示的帧宽度。详见 :ref:`vp9` 中的 7.2.3 节
* - __u16
      - ``frame_height_minus_1``
      - 加上 1 可得到以像素表示的帧高度。详见 :ref:`vp9` 中的 7.2.3 节
* - __u16
      - ``render_width_minus_1``
      - 加上 1 可得到以像素表示的预期渲染宽度。这在解码过程中不会用到，但可能会被硬件缩放器用来准备一个准备好扫描输出的帧。详见 :ref:`vp9` 中的 7.2.4 节
* - __u16
      - ``render_height_minus_1``
      - 加上 1 可得到以像素表示的预期渲染高度。这在解码过程中不会用到，但可能会被硬件缩放器用来准备一个准备好扫描输出的帧。详见 :ref:`vp9` 中的 7.2.4 节
* - __u64
      - ``last_frame_ts``
      - “最后”参考缓冲区的时间戳
时间戳指的是 struct :c:type:`v4l2_buffer` 中的 ``timestamp`` 字段。使用 :c:func:`v4l2_timeval_to_ns()` 函数将 struct :c:type:`v4l2_buffer` 中的 struct :c:type:`timeval` 转换为 __u64
* - __u64
      - ``golden_frame_ts``
      - “黄金”参考缓冲区的时间戳
时间戳指的是 struct :c:type:`v4l2_buffer` 中的 ``timestamp`` 字段。使用 :c:func:`v4l2_timeval_to_ns()` 函数将 struct :c:type:`v4l2_buffer` 中的 struct :c:type:`timeval` 转换为 __u64
* - __u64
      - ``alt_frame_ts``
      - “备用”参考缓冲区时间戳
  时间戳指的是结构体 :c:type:`v4l2_buffer` 中的 ``timestamp`` 字段。使用 :c:func:`v4l2_timeval_to_ns()` 函数将结构体 :c:type:`timeval` 转换为 __u64。
* - __u8
      - ``ref_frame_sign_bias``
      - 位字段，指定给定参考帧是否设置了符号偏移。更多细节请参见 :ref:`参考帧符号偏移 <vp9_ref_frame_sign_bias>`。
* - __u8
      - ``reset_frame_context``
      - 指定是否应将帧上下文重置为默认值。更多细节请参见 :ref:`重置帧上下文 <vp9_reset_frame_context>`。
* - __u8
      - ``frame_context_idx``
      - 应该使用/更新的帧上下文索引。
* - __u8
      - ``profile``
      - VP9 档案。可以是 0、1、2 或 3。
* - __u8
      - ``bit_depth``
      - 组件深度（以比特为单位）。可以是 8、10 或 12。请注意，并非所有档案都支持 10 和/或 12 比特深度。
* - __u8
      - ``interpolation_filter``
      - 指定用于执行帧间预测的滤波器选择。更多细节请参见 :ref:`插值滤波器 <vp9_interpolation_filter>`。
* - __u8
      - ``tile_cols_log2``
      - 指定每个瓦片宽度的以2为底的对数（其中宽度以 8x8 块为单位）。应当小于或等于 6。
* - __u8
      - ``tile_rows_log2``
      - 指定每个瓦片高度的以2为底的对数（其中高度以 8x8 块为单位）。
* - `__u8`
  - `reference_mode`
  - 指定要使用的帧间预测类型。更多详细信息，请参阅 :ref:`Reference Mode<vp9_reference_mode>`。请注意，这是在解析压缩头的过程中得出的，因此本应作为可选控制 :c:type:`v4l2_ctrl_vp9_compressed_hdr` 的一部分。如果驱动程序不需要压缩头，则将此值设置为零是安全的。
* - `__u8`
  - `reserved[7]`
  - 应用程序和驱动程序必须将其设置为零

.. raw:: latex

    \normalsize

.. _vp9_frame_flags:

`帧标志`

.. tabularcolumns:: |p{10.0cm}|p{1.2cm}|p{6.1cm}|

.. flat-table::
    :header-rows:  0
    :stub-columns: 0
    :widths:       1 1 2

    * - `V4L2_VP9_FRAME_FLAG_KEY_FRAME`
      - 0x001
      - 帧是一个关键帧
* - `V4L2_VP9_FRAME_FLAG_SHOW_FRAME`
      - 0x002
      - 帧应该被显示
* - `V4L2_VP9_FRAME_FLAG_ERROR_RESILIENT`
      - 0x004
      - 解码应该是容错的
* - `V4L2_VP9_FRAME_FLAG_INTRA_ONLY`
      - 0x008
      - 帧不引用其他帧
* - `V4L2_VP9_FRAME_FLAG_ALLOW_HIGH_PREC_MV`
      - 0x010
      - 帧可以使用高精度运动向量
* - `V4L2_VP9_FRAME_FLAG_REFRESH_FRAME_CTX`
      - 0x020
      - 解码后应更新帧上下文
* - `V4L2_VP9_FRAME_FLAG_PARALLEL_DEC_MODE`
      - 0x040
      - 使用并行解码
* - `V4L2_VP9_FRAME_FLAG_X_SUBSAMPLING`
      - 0x080
      - 启用了垂直子采样
* - ``V4L2_VP9_FRAME_FLAG_Y_SUBSAMPLING``
      - 0x100
      - 启用水平子采样
* - ``V4L2_VP9_FRAME_FLAG_COLOR_RANGE_FULL_SWING``
      - 0x200
      - 使用完整的UV范围

.. _vp9_ref_frame_sign_bias:

``参考帧符号偏置``

.. tabularcolumns:: |p{7.0cm}|p{1.2cm}|p{9.1cm}|

.. flat-table::
    :header-rows:  0
    :stub-columns: 0
    :widths:       1 1 2

    * - ``V4L2_VP9_SIGN_BIAS_LAST``
      - 0x1
      - 对最后一个参考帧设置符号偏置
* - ``V4L2_VP9_SIGN_BIAS_GOLDEN``
      - 0x2
      - 对金色参考帧设置符号偏置
* - ``V4L2_VP9_SIGN_BIAS_ALT``
      - 0x2
      - 对备用参考帧设置符号偏置

.. _vp9_reset_frame_context:

``重置帧上下文``

.. tabularcolumns:: |p{7.0cm}|p{1.2cm}|p{9.1cm}|

.. flat-table::
    :header-rows:  0
    :stub-columns: 0
    :widths:       1 1 2

    * - ``V4L2_VP9_RESET_FRAME_CTX_NONE``
      - 0
      - 不重置任何帧上下文
* - ``V4L2_VP9_RESET_FRAME_CTX_SPEC``
      - 1
      - 重置由 :c:type:`v4l2_ctrl_vp9_frame`.frame_context_idx 指向的帧上下文
* - ``V4L2_VP9_RESET_FRAME_CTX_ALL``
      - 2
      - 重置所有帧上下文

更多详细信息请参见 :ref:`vp9` 规范中的 '7.2 未压缩头语义' 部分

.. _vp9_interpolation_filter:

``插值滤波器``

.. tabularcolumns:: |p{9.0cm}|p{1.2cm}|p{7.1cm}|

.. flat-table::
    :header-rows:  0
    :stub-columns: 0
    :widths:       1 1 2

    * - ``V4L2_VP9_INTERP_FILTER_EIGHTTAP``
      - 0
      - 八抽头滤波器
* - ``V4L2_VP9_INTERP_FILTER_EIGHTTAP_SMOOTH``
  - 1
  - 八点平滑滤波器
* - ``V4L2_VP9_INTERP_FILTER_EIGHTTAP_SHARP``
  - 2
  - 八点锐化滤波器
* - ``V4L2_VP9_INTERP_FILTER_BILINEAR``
  - 3
  - 双线性滤波器
* - ``V4L2_VP9_INTERP_FILTER_SWITCHABLE``
  - 4
  - 滤波器选择在块级别进行信号传输

更多详细信息，请参阅 :ref:`vp9` 规范的“7.2.7 插值滤波器语义”部分。

.. _vp9_reference_mode:

``参考模式``

.. tabularcolumns:: |p{9.6cm}|p{0.5cm}|p{7.2cm}|

.. flat-table::
    :header-rows:  0
    :stub-columns: 0
    :widths:       1 1 2

    * - ``V4L2_VP9_REFERENCE_MODE_SINGLE_REFERENCE``
      - 0
      - 表示所有帧间块仅使用单个参考帧生成运动补偿预测
* - ``V4L2_VP9_REFERENCE_MODE_COMPOUND_REFERENCE``
      - 1
      - 要求所有帧间块必须使用复合模式。不允许使用单个参考帧预测
* - ``V4L2_VP9_REFERENCE_MODE_SELECT``
      - 2
      - 允许每个单独的帧间块在单个和复合预测模式之间选择

更多详细信息，请参阅 :ref:`vp9` 规范的“7.3.6 帧参考模式语义”部分。

.. c:type:: v4l2_vp9_segmentation

编码量化参数。更多详细信息，请参阅 :ref:`vp9` 规范的“7.2.10 分段参数语法”部分。
```markdown
.. tabularcolumns:: |p{0.8cm}|p{5cm}|p{11.4cm}|

.. cssclass:: longtable

.. flat-table:: struct v4l2_vp9_segmentation
    :header-rows:  0
    :stub-columns: 0
    :widths:       1 1 2

    * - __u8
      - ``feature_data[8][4]``
      - 每个特性附带的数据。如果启用了该特性，则数据项有效。数组应使用段号作为第一维（0..7），并使用其中一个 V4L2_VP9_SEG_* 作为第二维。
见 :ref:`段特性 ID <vp9_segment_feature>`
* - __u8
      - ``feature_enabled[8]``
      - 定义每个段中哪些特性被启用的位掩码。每个段的值是 V4L2_VP9_SEGMENT_FEATURE_ENABLED(id) 的组合，其中 id 是 V4L2_VP9_SEG_* 中的一个。
见 :ref:`段特性 ID <vp9_segment_feature>`
* - __u8
      - ``tree_probs[7]``
      - 指定解码 Segment-ID 时要使用的概率值。
见 :ref:`vp9` 中的“5.15 段映射”部分以获取更多详细信息
* - __u8
      - ``pred_probs[3]``
      - 指定解码 Predicted-Segment-ID 时要使用的概率值。
见 :ref:`vp9` 中的“6.4.14 获取段 ID 语法”部分以获取更多详细信息
* - __u8
      - ``flags``
      - V4L2_VP9_SEGMENTATION_FLAG_* 标志的组合。
见 :ref:`段标志 <vp9_segmentation_flags>`
* - __u8
      - ``reserved[5]``
      - 应用程序和驱动程序必须将其设置为零
.. _vp9_segment_feature:

``段特性 ID``

.. tabularcolumns:: |p{6.0cm}|p{1cm}|p{10.3cm}|

.. flat-table::
    :header-rows:  0
    :stub-columns: 0
    :widths:       1 1 2

    * - ``V4L2_VP9_SEG_LVL_ALT_Q``
      - 0
      - 量化器段特性
* - ``V4L2_VP9_SEG_LVL_ALT_L``
      - 1
      - 环路滤波器段特性
```
* - ``V4L2_VP9_SEG_LVL_REF_FRAME``
  - 2
  - 引用帧段特性
* - ``V4L2_VP9_SEG_LVL_SKIP``
  - 3
  - 跳过段特性
* - ``V4L2_VP9_SEG_LVL_MAX``
  - 4
  - 段特性数量
.. _vp9_segmentation_flags:

``分割标志``

.. tabularcolumns:: |p{10.6cm}|p{0.8cm}|p{5.9cm}|

.. flat-table::
    :header-rows:  0
    :stub-columns: 0
    :widths:       1 1 2

    * - ``V4L2_VP9_SEGMENTATION_FLAG_ENABLED``
      - 0x01
      - 表示该帧使用了分割工具
* - ``V4L2_VP9_SEGMENTATION_FLAG_UPDATE_MAP``
      - 0x02
      - 表示在解码该帧时应更新分割图
* - ``V4L2_VP9_SEGMENTATION_FLAG_TEMPORAL_UPDATE``
      - 0x04
      - 表示分割图的更新是相对于现有分割图进行编码的
* - ``V4L2_VP9_SEGMENTATION_FLAG_UPDATE_DATA``
      - 0x08
      - 表示将为每个段指定新的参数
* - ``V4L2_VP9_SEGMENTATION_FLAG_ABS_OR_DELTA_UPDATE``
      - 0x10
      - 表示分割参数表示要使用的实际值
.. c:type:: v4l2_vp9_quantization

编码量化参数。有关更多详细信息，请参阅VP9规范中的“7.2.9 量化参数语法”部分。
.. tabularcolumns:: |p{0.8cm}|p{4cm}|p{12.4cm}|

.. cssclass:: longtable

.. flat-table:: struct v4l2_vp9_quantization
    :header-rows:  0
    :stub-columns: 0
    :widths:       1 1 2

    * - __u8
      - ``base_q_idx``
      - 表示基本帧qindex
```markdown
* - __s8
  - ``delta_q_y_dc``
  - 表示相对于 base_q_idx 的 Y DC 量化器
* - __s8
  - ``delta_q_uv_dc``
  - 表示相对于 base_q_idx 的 UV DC 量化器
* - __s8
  - ``delta_q_uv_ac``
  - 表示相对于 base_q_idx 的 UV AC 量化器
* - __u8
  - ``reserved[4]``
  - 应用程序和驱动程序必须将其设置为零
.. c:type:: v4l2_vp9_loop_filter

此结构包含所有与环路滤波器相关的参数。更多详细信息请参阅 :ref:`vp9` 规范中的 '7.2.8 环路滤波器语义' 部分
.. tabularcolumns:: |p{0.8cm}|p{4cm}|p{12.4cm}|

.. cssclass:: longtable

.. flat-table:: struct v4l2_vp9_loop_filter
    :header-rows:  0
    :stub-columns: 0
    :widths:       1 1 2

    * - __s8
      - ``ref_deltas[4]``
      - 包含基于所选参考帧所需的滤波器级别调整值
* - __s8
      - ``mode_deltas[2]``
      - 包含基于所选模式所需的滤波器级别调整值
* - __u8
      - ``level``
      - 表示环路滤波器的强度
* - __u8
      - ``sharpness``
      - 表示锐度级别
* - __u8
      - ``flags``
      - V4L2_VP9_LOOP_FILTER_FLAG_* 标志的组合
```
参见：:ref:`Loop Filter Flags <vp9_loop_filter_flags>`
* - __u8
      - ``reserved[7]``
      - 应用程序和驱动程序必须将其设置为零
.. _vp9_loop_filter_flags:

``Loop Filter Flags``

.. tabularcolumns:: |p{9.6cm}|p{0.5cm}|p{7.2cm}|

.. flat-table::
    :header-rows:  0
    :stub-columns: 0
    :widths:       1 1 2

    * - ``V4L2_VP9_LOOP_FILTER_FLAG_DELTA_ENABLED``
      - 0x1
      - 当设置时，滤波器级别取决于用于预测块的模式和参考帧
* - ``V4L2_VP9_LOOP_FILTER_FLAG_DELTA_UPDATE``
      - 0x2
      - 当设置时，比特流包含额外的语法元素，这些元素指定了哪些模式和参考帧增量需要更新
.. _v4l2-codec-stateless-hevc:

``V4L2_CID_STATELESS_HEVC_SPS (struct)``
    指定与HEVC切片数据关联的序列参数集字段（从比特流中提取）
这些比特流参数根据 :ref:`hevc` 定义
在规范的第7.4.3.2节“Sequence parameter set RBSP语义”中有详细描述
.. c:type:: v4l2_ctrl_hevc_sps

.. raw:: latex

    \small

.. tabularcolumns:: |p{1.2cm}|p{9.2cm}|p{6.9cm}|

.. cssclass:: longtable

.. flat-table:: struct v4l2_ctrl_hevc_sps
    :header-rows:  0
    :stub-columns: 0
    :widths:       1 1 2

    * - __u8
      - ``video_parameter_set_id``
      - 指定活动VPS的vps_video_parameter_set_id的值，如H.265规范中的“7.4.3.2.1 General sequence parameter set RBSP semantics”部分所述
* - __u8
      - ``seq_parameter_set_id``
      - 提供一个标识符供其他语法元素引用SPS，如H.265规范中的“7.4.3.2.1 General sequence parameter set RBSP semantics”部分所述
* - __u16
      - ``pic_width_in_luma_samples``
      - 指定每个解码图片的宽度，单位为亮度样本数
* - `__u16`
  - `pic_height_in_luma_samples`
  - 指定每个解码图像的高度，单位为亮度样本

* - `__u8`
  - `bit_depth_luma_minus8`
  - 此值加上 8 指定亮度数组样本的位深度

* - `__u8`
  - `bit_depth_chroma_minus8`
  - 此值加上 8 指定色度数组样本的位深度

* - `__u8`
  - `log2_max_pic_order_cnt_lsb_minus4`
  - 指定变量 MaxPicOrderCntLsb 的值

* - `__u8`
  - `sps_max_dec_pic_buffering_minus1`
  - 此值加上 1 指定编码视频序列（CVS）所需的解码图像缓冲区的最大大小

* - `__u8`
  - `sps_max_num_reorder_pics`
  - 指示允许的最大重排序图像数量

* - `__u8`
  - `sps_max_latency_increase_plus1`
  - 用于指示 MaxLatencyPictures，该值表示在输出顺序中任何图像之前且在解码顺序中紧随其后的最大图像数量

* - `__u8`
  - `log2_min_luma_coding_block_size_minus3`
  - 此值加上 3 指定最小亮度编码块大小

* - `__u8`
  - `log2_diff_max_min_luma_coding_block_size`
  - 指定最大和最小亮度编码块大小之间的差值

* - `__u8`
  - `log2_min_luma_transform_block_size_minus2`
  - 此值加上 2 指定最小亮度变换块大小
* - __u8
  - ``log2_diff_max_min_luma_transform_block_size``
  - 指定最大亮度变换块大小与最小亮度变换块大小之间的差值

* - __u8
  - ``max_transform_hierarchy_depth_inter``
  - 指定采用帧间预测模式编码的编码单元中变换单元的最大层次深度

* - __u8
  - ``max_transform_hierarchy_depth_intra``
  - 指定采用帧内预测模式编码的编码单元中变换单元的最大层次深度

* - __u8
  - ``pcm_sample_bit_depth_luma_minus1``
  - 此值加1指定表示每个PCM样本值（亮度分量）所使用的位数

* - __u8
  - ``pcm_sample_bit_depth_chroma_minus1``
  - 指定表示每个PCM样本值（色度分量）所使用的位数

* - __u8
  - ``log2_min_pcm_luma_coding_block_size_minus3``
  - 加3后指定编码块的最小尺寸

* - __u8
  - ``log2_diff_max_min_pcm_luma_coding_block_size``
  - 指定编码块的最大尺寸与最小尺寸之间的差值

* - __u8
  - ``num_short_term_ref_pic_sets``
  - 指定包含在SPS中的短期参考图片集（st_ref_pic_set()）语法结构的数量

* - __u8
  - ``num_long_term_ref_pics_sps``
  - 指定在SPS中指定的候选长期参考图片的数量

* - __u8
  - ``chroma_format_idc``
  - 指定色度采样格式
* - `__u8`
  - `sps_max_sub_layers_minus1`
  - 此值加1指定了最大数量的时间子层

* - `__u64`
  - `flags`
  - 请参见 :ref:`Sequence Parameter Set Flags <hevc_sps_flags>`

.. raw:: latex

    \normalsize

.. _hevc_sps_flags:

`Sequence Parameter Set Flags`

.. raw:: latex

    \small

.. cssclass:: longtable

.. flat-table::
    :header-rows:  0
    :stub-columns: 0
    :widths:       1 1 2

    * - `V4L2_HEVC_SPS_FLAG_SEPARATE_COLOUR_PLANE`
      - 0x00000001
      -
    * - `V4L2_HEVC_SPS_FLAG_SCALING_LIST_ENABLED`
      - 0x00000002
      -
    * - `V4L2_HEVC_SPS_FLAG_AMP_ENABLED`
      - 0x00000004
      -
    * - `V4L2_HEVC_SPS_FLAG_SAMPLE_ADAPTIVE_OFFSET`
      - 0x00000008
      -
    * - `V4L2_HEVC_SPS_FLAG_PCM_ENABLED`
      - 0x00000010
      -
    * - `V4L2_HEVC_SPS_FLAG_PCM_LOOP_FILTER_DISABLED`
      - 0x00000020
      -
    * - `V4L2_HEVC_SPS_FLAG_LONG_TERM_REF_PICS_PRESENT`
      - 0x00000040
      -
    * - `V4L2_HEVC_SPS_FLAG_SPS_TEMPORAL_MVP_ENABLED`
      - 0x00000080
      -
    * - `V4L2_HEVC_SPS_FLAG_STRONG_INTRA_SMOOTHING_ENABLED`
      - 0x00000100
      -

.. raw:: latex

    \normalsize

`V4L2_CID_STATELESS_HEVC_PPS (struct)`
    指定与HEVC片数据相关的图片参数集字段（从比特流中提取）
这些比特流参数根据 :ref:`hevc` 定义
在规范的第7.4.3.3节“图片参数集RBSP语义”中有描述
.. c:type:: v4l2_ctrl_hevc_pps

.. tabularcolumns:: |p{1.2cm}|p{8.6cm}|p{7.5cm}|

.. cssclass:: longtable

.. flat-table:: struct v4l2_ctrl_hevc_pps
    :header-rows:  0
    :stub-columns: 0
    :widths:       1 1 2

    * - `__u8`
      - `pic_parameter_set_id`
      - 用于其他语法元素引用的PPS标识符
    * - `__u8`
      - `num_extra_slice_header_bits`
      - 指定在片头RBSP中存在多少额外的片头位，对于引用该PPS的编码图像
    * - `__u8`
      - `num_ref_idx_l0_default_active_minus1`
      - 此值加1指定了推断的num_ref_idx_l0_active_minus1值
    * - `__u8`
      - `num_ref_idx_l1_default_active_minus1`
      - 此值加1指定了推断的num_ref_idx_l1_active_minus1值
    * - `__s8`
      - `init_qp_minus26`
      - 此值加26指定了每个引用该PPS的片的SliceQp Y的初始值
    * - `__u8`
      - `diff_cu_qp_delta_depth`
      - 指定亮度编码树块大小和携带cu_qp_delta_abs及cu_qp_delta_sign_flag的编码单元的最小亮度编码块大小之间的差异
* - `__s8`
      - `pps_cb_qp_offset`
      - 指定亮度量化参数 Cb 的偏移量
* - `__s8`
      - `pps_cr_qp_offset`
      - 指定亮度量化参数 Cr 的偏移量
* - `__u8`
      - `num_tile_columns_minus1`
      - 此值加 1 指定划分图像的瓷砖列数
* - `__u8`
      - `num_tile_rows_minus1`
      - 此值加 1 指定划分图像的瓷砖行数
* - `__u8`
      - `column_width_minus1[20]`
      - 此值加 1 指定第 i 个瓷砖列的宽度，单位为编码树块
* - `__u8`
      - `row_height_minus1[22]`
      - 此值加 1 指定第 i 个瓷砖行的高度，单位为编码树块
* - `__s8`
      - `pps_beta_offset_div2`
      - 指定除以 2 后的默认去块滤波参数偏移量 beta
* - `__s8`
      - `pps_tc_offset_div2`
      - 指定除以 2 后的默认去块滤波参数偏移量 tC
* - `__u8`
      - `log2_parallel_merge_level_minus2`
      - 此值加 2 指定变量 Log2ParMrgLevel 的值
* - `__u8`
      - `padding[4]`
      - 应用程序和驱动程序必须将其设置为零
* - `__u64`
  - ``flags``
  - 参见 :ref:`Picture Parameter Set Flags <hevc_pps_flags>`

.. _hevc_pps_flags:

``Picture Parameter Set Flags``

.. raw:: latex

    \small

.. flat-table::
    :header-rows:  0
    :stub-columns: 0
    :widths:       1 1 2

    * - ``V4L2_HEVC_PPS_FLAG_DEPENDENT_SLICE_SEGMENT_ENABLED``
      - 0x00000001
      -
    * - ``V4L2_HEVC_PPS_FLAG_OUTPUT_FLAG_PRESENT``
      - 0x00000002
      -
    * - ``V4L2_HEVC_PPS_FLAG_SIGN_DATA_HIDING_ENABLED``
      - 0x00000004
      -
    * - ``V4L2_HEVC_PPS_FLAG_CABAC_INIT_PRESENT``
      - 0x00000008
      -
    * - ``V4L2_HEVC_PPS_FLAG_CONSTRAINED_INTRA_PRED``
      - 0x00000010
      -
    * - ``V4L2_HEVC_PPS_FLAG_TRANSFORM_SKIP_ENABLED``
      - 0x00000020
      -
    * - ``V4L2_HEVC_PPS_FLAG_CU_QP_DELTA_ENABLED``
      - 0x00000040
      -
    * - ``V4L2_HEVC_PPS_FLAG_PPS_SLICE_CHROMA_QP_OFFSETS_PRESENT``
      - 0x00000080
      -
    * - ``V4L2_HEVC_PPS_FLAG_WEIGHTED_PRED``
      - 0x00000100
      -
    * - ``V4L2_HEVC_PPS_FLAG_WEIGHTED_BIPRED``
      - 0x00000200
      -
    * - ``V4L2_HEVC_PPS_FLAG_TRANSQUANT_BYPASS_ENABLED``
      - 0x00000400
      -
    * - ``V4L2_HEVC_PPS_FLAG_TILES_ENABLED``
      - 0x00000800
      -
    * - ``V4L2_HEVC_PPS_FLAG_ENTROPY_CODING_SYNC_ENABLED``
      - 0x00001000
      -
    * - ``V4L2_HEVC_PPS_FLAG_LOOP_FILTER_ACROSS_TILES_ENABLED``
      - 0x00002000
      -
    * - ``V4L2_HEVC_PPS_FLAG_PPS_LOOP_FILTER_ACROSS_SLICES_ENABLED``
      - 0x00004000
      -
    * - ``V4L2_HEVC_PPS_FLAG_DEBLOCKING_FILTER_OVERRIDE_ENABLED``
      - 0x00008000
      -
    * - ``V4L2_HEVC_PPS_FLAG_PPS_DISABLE_DEBLOCKING_FILTER``
      - 0x00010000
      -
    * - ``V4L2_HEVC_PPS_FLAG_LISTS_MODIFICATION_PRESENT``
      - 0x00020000
      -
    * - ``V4L2_HEVC_PPS_FLAG_SLICE_SEGMENT_HEADER_EXTENSION_PRESENT``
      - 0x00040000
      -
    * - ``V4L2_HEVC_PPS_FLAG_DEBLOCKING_FILTER_CONTROL_PRESENT``
      - 0x00080000
      - 指定PPS中存在去块滤波器控制语法元素
    * - ``V4L2_HEVC_PPS_FLAG_UNIFORM_SPACING``
      - 0x00100000
      - 指定图像中的切片列边界和切片行边界均匀分布

.. raw:: latex

    \normalsize

``V4L2_CID_STATELESS_HEVC_SLICE_PARAMS (struct)``
    指定各种切片特定参数，特别是来自NAL单元头、一般切片段头和加权预测参数部分的比特流参数。
这些比特流参数根据 :ref:`hevc` 定义，在规范的第7.4.7节“一般切片段头语义”中有描述。
此控制是一个动态大小的一维数组，使用时必须设置 `V4L2_CTRL_FLAG_DYNAMIC_ARRAY` 标志。

.. c:type:: v4l2_ctrl_hevc_slice_params

.. raw:: latex

    \scriptsize

.. tabularcolumns:: |p{5.4cm}|p{6.8cm}|p{5.1cm}|

.. cssclass:: longtable

.. flat-table:: struct v4l2_ctrl_hevc_slice_params
    :header-rows:  0
    :stub-columns: 0
    :widths:       1 1 2

    * - `__u32`
      - ``bit_size``
      - 当前切片数据的大小（以比特为单位）
    * - `__u32`
      - ``data_byte_offset``
      - 当前切片数据中视频数据的偏移量（以字节为单位）
    * - `__u32`
      - ``num_entry_point_offsets``
      - 指定切片头中入口点偏移语法元素的数量
当驱动支持时，必须设置 `V4L2_CID_STATELESS_HEVC_ENTRY_POINT_OFFSETS`
    * - `__u8`
      - ``nal_unit_type``
      - 指定切片的编码类型（B, P 或 I）
    * - `__u8`
      - ``nuh_temporal_id_plus1``
      - 减1后指定NAL单元的时间标识符
* - __u8
      - ``slice_type``
      - （V4L2_HEVC_SLICE_TYPE_I, V4L2_HEVC_SLICE_TYPE_P 或 V4L2_HEVC_SLICE_TYPE_B）
* - __u8
      - ``colour_plane_id``
      - 指定与当前片相关的颜色平面
* - __s32
      - ``slice_pic_order_cnt``
      - 指定图像顺序计数
* - __u8
      - ``num_ref_idx_l0_active_minus1``
      - 此值加 1 指定用于解码该片的参考图片列表 0 的最大引用索引
* - __u8
      - ``num_ref_idx_l1_active_minus1``
      - 此值加 1 指定用于解码该片的参考图片列表 1 的最大引用索引
* - __u8
      - ``collocated_ref_idx``
      - 指定用于时域运动矢量预测的共位置图片的引用索引
* - __u8
      - ``five_minus_max_num_merge_cand``
      - 指定在该片中支持的最大合并运动矢量预测候选数量减去 5 的值
* - __s8
      - ``slice_qp_delta``
      - 指定用于该片编码块的初始 QpY 值
* - __s8
      - ``slice_cb_qp_offset``
      - 指定要加到 pps_cb_qp_offset 值上的差值
* - __s8
      - ``slice_cr_qp_offset``
      - 指定要加到 pps_cr_qp_offset 值上的差值
* - __s8
      - ``slice_act_y_qp_offset``
      - 指定在第 8.6.2 节中推导出的量化参数 qP 的亮度偏移
    * - __s8
      - ``slice_act_cb_qp_offset``
      - 指定在第 8.6.2 节中推导出的量化参数 qP 的Cb偏移
    * - __s8
      - ``slice_act_cr_qp_offset``
      - 指定在第 8.6.2 节中推导出的量化参数 qP 的Cr偏移
    * - __s8
      - ``slice_beta_offset_div2``
      - 指定去块滤波参数偏移量（beta除以2）
* - __s8
      - ``slice_tc_offset_div2``
      - 指定去块滤波参数偏移量（tC除以2）
* - __u8
      - ``pic_struct``
      - 指示图片是否应作为帧或一个或多个场显示
* - __u32
      - ``slice_segment_addr``
      - 指定片段中的第一个编码树块的地址
* - __u8
      - ``ref_idx_l0[V4L2_HEVC_DPB_ENTRIES_NUM_MAX]``
      - L0参考元素列表，作为DPB中的索引
* - __u8
      - ``ref_idx_l1[V4L2_HEVC_DPB_ENTRIES_NUM_MAX]``
      - L1参考元素列表，作为DPB中的索引
* - __u16
      - ``short_term_ref_pic_set_size``
      - 指定短期参考图片集的大小（比特数），在规范中描述为st_ref_pic_set()，包含在片头或SPS（第 7.3.6.1 节）中
* - __u16
      - ``long_term_ref_pic_set_size``
      - 指定长期参考图片集的大小（比特数），包含在片头或SPS中。这是if(long_term_ref_pics_present_flag)条件块中的比特数，如规范第 7.3.6.1 节所述
* - __u8
      - ``padding``
      - 应用程序和驱动程序必须将其设置为零
* - 结构体 :c:type:`v4l2_hevc_pred_weight_table`
      - ``pred_weight_table``
      - 用于帧间预测的预测权重系数
* - `__u64`
  - `flags`
  - 参见 :ref:`Slice Parameters Flags <hevc_slice_params_flags>`

.. raw:: latex

    \normalsize

.. _hevc_slice_params_flags:

`Slice Parameters Flags`

.. raw:: latex

    \scriptsize

.. flat-table::
    :header-rows:  0
    :stub-columns: 0
    :widths:       1 1 2

    * - `V4L2_HEVC_SLICE_PARAMS_FLAG_SLICE_SAO_LUMA`
      - 0x00000001
      -
    * - `V4L2_HEVC_SLICE_PARAMS_FLAG_SLICE_SAO_CHROMA`
      - 0x00000002
      -
    * - `V4L2_HEVC_SLICE_PARAMS_FLAG_SLCE_TEMPORAL_MVP_ENABLED`
      - 0x00000004
      -
    * - `V4L2_HEVC_SLICE_PARAMS_FLAG_MVD_L1_ZERO`
      - 0x00000008
      -
    * - `V4L2_HEVC_SLICE_PARAMS_FLAG_CABAC_INIT`
      - 0x00000010
      -
    * - `V4L2_HEVC_SLICE_PARAMS_FLAG_COLLOCATED_FROM_L0`
      - 0x00000020
      -
    * - `V4L2_HEVC_SLICE_PARAMS_FLAG_USE_INTEGER_MV`
      - 0x00000040
      -
    * - `V4L2_HEVC_SLICE_PARAMS_FLAG_SLICE_DEBLOCKING_FILTER_DISABLED`
      - 0x00000080
      -
    * - `V4L2_HEVC_SLICE_PARAMS_FLAG_SLICE_LOOP_FILTER_ACROSS_SLICES_ENABLED`
      - 0x00000100
      -
    * - `V4L2_HEVC_SLICE_PARAMS_FLAG_DEPENDENT_SLICE_SEGMENT`
      - 0x00000200
      -

.. raw:: latex

    \normalsize

`V4L2_CID_STATELESS_HEVC_ENTRY_POINT_OFFSETS (integer)`
    指定字节单位的入口点偏移量。
此控制是一个动态大小的数组。入口点偏移量的数量由 `elems` 字段报告。
此比特流参数根据 :ref:`hevc` 定义。
它们在规范的第 7.4.7.1 节“一般片段头语义”中描述。
当一个请求中提交多个片时，该数组的长度必须是请求中所有片的 num_entry_point_offsets 之和。

`V4L2_CID_STATELESS_HEVC_SCALING_MATRIX (struct)`
    指定用于变换系数缩放过程的 HEVC 缩放矩阵参数。
这些矩阵和参数根据 :ref:`hevc` 定义。
它们在规范的第 7.4.5 节“缩放列表数据语义”中描述。

.. c:type:: v4l2_ctrl_hevc_scaling_matrix

.. raw:: latex

    \scriptsize

.. tabularcolumns:: |p{5.4cm}|p{6.8cm}|p{5.1cm}|

.. cssclass:: longtable

.. flat-table:: struct v4l2_ctrl_hevc_scaling_matrix
    :header-rows:  0
    :stub-columns: 0
    :widths:       1 1 2

    * - `__u8`
      - `scaling_list_4x4[6][16]`
      - 用于变换系数缩放过程的缩放列表。每个缩放列表上的值应按光栅扫描顺序排列。
    * - `__u8`
      - `scaling_list_8x8[6][64]`
      - 用于变换系数缩放过程的缩放列表。每个缩放列表上的值应按光栅扫描顺序排列。
* - __u8
      - ``scaling_list_16x16[6][64]``
      - 缩放列表用于变换系数的缩放过程。每个缩放列表中的值应按光栅扫描顺序排列。
* - __u8
      - ``scaling_list_32x32[2][64]``
      - 缩放列表用于变换系数的缩放过程。每个缩放列表中的值应按光栅扫描顺序排列。
* - __u8
      - ``scaling_list_dc_coef_16x16[6]``
      - 缩放列表用于变换系数的缩放过程。每个缩放列表中的值应按光栅扫描顺序排列。
* - __u8
      - ``scaling_list_dc_coef_32x32[2]``
      - 缩放列表用于变换系数的缩放过程。每个缩放列表中的值应按光栅扫描顺序排列。

.. raw:: latex

    \normalsize

.. c:type:: v4l2_hevc_dpb_entry

.. raw:: latex

    \small

.. tabularcolumns:: |p{1.0cm}|p{4.2cm}|p{12.1cm}|

.. flat-table:: struct v4l2_hevc_dpb_entry
    :header-rows:  0
    :stub-columns: 0
    :widths:       1 1 2

    * - __u64
      - ``timestamp``
      - 用作参考的 V4L2 捕获缓冲区的时间戳，用于 B 帧和 P 帧。时间戳指的是 :c:type:`v4l2_buffer` 结构体中的 ``timestamp`` 字段。使用 :c:func:`v4l2_timeval_to_ns()` 函数将 :c:type:`v4l2_buffer` 结构体中的 :c:type:`timeval` 转换为 __u64。
* - __u8
      - ``flags``
      - 长期参考帧标志（V4L2_HEVC_DPB_ENTRY_LONG_TERM_REFERENCE）。该标志的设置如 ITU HEVC 规范第 "8.3.2 参考图像集解码过程" 章节所述。
* - __u8
      - ``field_pic``
      - 参考图像是场图像还是帧图像。详见 :ref:`HEVC dpb field pic Flags <hevc_dpb_field_pic_flags>`。
* - __s32
      - ``pic_order_cnt_val``
      - 当前图像的图像顺序计数。
* - __u8
      - ``padding[2]``
      - 应用程序和驱动程序必须将其设置为零。

.. raw:: latex

    \normalsize

.. _hevc_dpb_field_pic_flags:

``HEVC dpb field pic Flags``

.. raw:: latex

    \scriptsize

.. flat-table::
    :header-rows:  0
    :stub-columns: 0
    :widths:       1 1 2

    * - ``V4L2_HEVC_SEI_PIC_STRUCT_FRAME``
      - 0
      - （逐行）帧
    * - ``V4L2_HEVC_SEI_PIC_STRUCT_TOP_FIELD``
      - 1
      - 上半场
    * - ``V4L2_HEVC_SEI_PIC_STRUCT_BOTTOM_FIELD``
      - 2
      - 下半场
    * - ``V4L2_HEVC_SEI_PIC_STRUCT_TOP_BOTTOM``
      - 3
      - 上半场，下半场，依次出现
    * - ``V4L2_HEVC_SEI_PIC_STRUCT_BOTTOM_TOP``
      - 4
      - 下半场，上半场，依次出现
    * - ``V4L2_HEVC_SEI_PIC_STRUCT_TOP_BOTTOM_TOP``
      - 5
      - 上半场，下半场，上半场重复，依次出现
    * - ``V4L2_HEVC_SEI_PIC_STRUCT_BOTTOM_TOP_BOTTOM``
      - 6
      - 下半场，上半场，下半场重复，依次出现
    * - ``V4L2_HEVC_SEI_PIC_STRUCT_FRAME_DOUBLING``
      - 7
      - 帧加倍
    * - ``V4L2_HEVC_SEI_PIC_STRUCT_FRAME_TRIPLING``
      - 8
      - 帧三倍化
    * - ``V4L2_HEVC_SEI_PIC_STRUCT_TOP_PAIRED_PREVIOUS_BOTTOM``
      - 9
      - 输出顺序中上半场与前一个下半场配对
    * - ``V4L2_HEVC_SEI_PIC_STRUCT_BOTTOM_PAIRED_PREVIOUS_TOP``
      - 10
      - 输出顺序中下半场与前一个上半场配对
    * - ``V4L2_HEVC_SEI_PIC_STRUCT_TOP_PAIRED_NEXT_BOTTOM``
      - 11
      - 输出顺序中上半场与下一个下半场配对
    * - ``V4L2_HEVC_SEI_PIC_STRUCT_BOTTOM_PAIRED_NEXT_TOP``
      - 12
      - 输出顺序中下半场与下一个上半场配对

.. c:type:: v4l2_hevc_pred_weight_table

.. raw:: latex

    \footnotesize

.. tabularcolumns:: |p{0.8cm}|p{10.6cm}|p{5.9cm}|

.. flat-table:: struct v4l2_hevc_pred_weight_table
    :header-rows:  0
    :stub-columns: 0
    :widths:       1 1 2

    * - __s8
      - ``delta_luma_weight_l0[V4L2_HEVC_DPB_ENTRIES_NUM_MAX]``
      - 对列表 0 的亮度预测值应用的加权因子的差异。
* - `__s8`
      - `luma_offset_l0[V4L2_HEVC_DPB_ENTRIES_NUM_MAX]`
      - 应用于列表0的亮度预测值的加性偏移量
* - `__s8`
      - `delta_chroma_weight_l0[V4L2_HEVC_DPB_ENTRIES_NUM_MAX][2]`
      - 应用于列表0的色度预测值的加权因子差异
* - `__s8`
      - `chroma_offset_l0[V4L2_HEVC_DPB_ENTRIES_NUM_MAX][2]`
      - 应用于列表0的色度预测值的加性偏移量差异
* - `__s8`
      - `delta_luma_weight_l1[V4L2_HEVC_DPB_ENTRIES_NUM_MAX]`
      - 应用于列表1的亮度预测值的加权因子差异
* - `__s8`
      - `luma_offset_l1[V4L2_HEVC_DPB_ENTRIES_NUM_MAX]`
      - 应用于列表1的亮度预测值的加性偏移量
* - `__s8`
      - `delta_chroma_weight_l1[V4L2_HEVC_DPB_ENTRIES_NUM_MAX][2]`
      - 应用于列表1的色度预测值的加权因子差异
* - `__s8`
      - `chroma_offset_l1[V4L2_HEVC_DPB_ENTRIES_NUM_MAX][2]`
      - 应用于列表1的色度预测值的加性偏移量差异
* - `__u8`
      - `luma_log2_weight_denom`
      - 所有亮度加权因子分母的以2为底的对数
* - `__s8`
      - `delta_chroma_log2_weight_denom`
      - 所有色度加权因子分母的以2为底的对数的差异
* - `__u8`
      - `padding[6]`
      - 应用程序和驱动程序必须将其设置为零
```raw:: latex

    \normalsize

``V4L2_CID_STATELESS_HEVC_DECODE_MODE (枚举类型)``
    指定要使用的解码模式。目前暴露了基于切片和基于帧的解码，但将来可能会添加新的模式。
此控制用于修改 `V4L2_PIX_FMT_HEVC_SLICE` 像素格式。支持 `V4L2_PIX_FMT_HEVC_SLICE` 的应用程序必须设置此控制以指定缓冲区预期的解码模式。
驱动程序可能暴露单个或多个解码模式，具体取决于它们所能支持的模式。
.. c:type:: v4l2_stateless_hevc_decode_mode

.. raw:: latex

    \small

.. tabularcolumns:: |p{9.4cm}|p{0.6cm}|p{7.3cm}|

.. flat-table::
    :header-rows:  0
    :stub-columns: 0
    :widths:       1 1 2

    * - ``V4L2_STATELESS_HEVC_DECODE_MODE_SLICE_BASED``
      - 0
      - 解码在切片粒度上进行。OUTPUT 缓冲区必须包含一个切片。
* - ``V4L2_STATELESS_HEVC_DECODE_MODE_FRAME_BASED``
      - 1
      - 解码在帧粒度上进行。OUTPUT 缓冲区必须包含解码帧所需的所有切片。
.. raw:: latex

    \normalsize

``V4L2_CID_STATELESS_HEVC_START_CODE (枚举类型)``
    指定每个 HEVC 切片预期的起始码。
此控制用于修改 `V4L2_PIX_FMT_HEVC_SLICE` 像素格式。支持 `V4L2_PIX_FMT_HEVC_SLICE` 的应用程序必须设置此控制以指定缓冲区预期的起始码。
驱动程序可能暴露单个或多个起始码，具体取决于它们所能支持的起始码。
```markdown
.. c:type:: v4l2_stateless_hevc_start_code

.. tabularcolumns:: |p{9.2cm}|p{0.6cm}|p{7.5cm}|

.. flat-table::
    :header-rows:  0
    :stub-columns: 0
    :widths:       1 1 2

    * - ``V4L2_STATELESS_HEVC_START_CODE_NONE``
      - 0
      - 选择此值指定 HEVC 片段传递给驱动程序时不带任何起始码。比特流数据应符合 :ref:`hevc` 7.3.1.1 通用 NAL 单元语法，因此在需要时包含仿真防止字节。
    * - ``V4L2_STATELESS_HEVC_START_CODE_ANNEX_B``
      - 1
      - 选择此值指定 HEVC 片段预期带有 Annex B 起始码。根据 :ref:`hevc`，有效的起始码可以是 3 字节的 0x000001 或 4 字节的 0x00000001。

.. raw:: latex

    \normalsize

``V4L2_CID_MPEG_VIDEO_BASELAYER_PRIORITY_ID (integer)``
    指定一个优先级标识符，该标识符将应用于基础层的 NAL 单元。默认情况下，基础层的值设置为 0，而下一层将被分配优先级 ID 为 1、2、3 等等。
视频编码器无法决定应用于某一层的优先级 ID，因此这个值必须由客户端提供。
这适用于 H264，并且有效范围是从 0 到 63。
来源：Rec. ITU-T H.264 (06/2019); G.7.4.1.1, G.8.8.1

``V4L2_CID_MPEG_VIDEO_LTR_COUNT (integer)``
    指定编码器在任何时候可以保留的最大长时参考（LTR）帧数。
这适用于 H264 和 HEVC 编码器。

``V4L2_CID_MPEG_VIDEO_FRAME_LTR_INDEX (integer)``
    设置此控制后，下一个排队的帧将被标记为长时参考（LTR）帧，并赋予从 0 到 LTR_COUNT-1 的 LTR 索引。
这适用于 H264 和 HEVC 编码器。
```
源 ITU-T H.264 (06/2019)；表 7.9

``V4L2_CID_MPEG_VIDEO_USE_LTR_FRAMES (位掩码)``
    指定用于编码下一个队列帧的长期参考（LTR）帧。
这提供了一个位掩码，其由比特 [0, LTR_COUNT-1] 组成。
这适用于 H264 和 HEVC 编码器。
``V4L2_CID_STATELESS_HEVC_DECODE_PARAMS (结构体)``
    指定各种解码参数，特别是所有列表（短、长、之前、当前、之后）的参考图片序号（POC）以及它们各自的条目数量。
这些参数根据 :ref:`hevc` 定义。
它们在规范的第 8.3 节“片解码过程”中描述。
.. c:type:: v4l2_ctrl_hevc_decode_params

.. cssclass:: longtable

.. flat-table:: 结构体 v4l2_ctrl_hevc_decode_params
    :header-rows:  0
    :stub-columns: 0
    :widths:       1 1 2

    * - __s32
      - ``pic_order_cnt_val``
      - 规范第 8.3.1 节“图片序号解码过程”中描述的 PicOrderCntVal
* - __u16
      - ``short_term_ref_pic_set_size``
      - 指定第一个片的短期参考图片集的大小（以比特为单位）。该集在规范中描述为 st_ref_pic_set()，包含在片头或 SPS (第 7.3.6.1 节) 中。
* - __u16
      - ``long_term_ref_pic_set_size``
      - 指定第一个片的长期参考图片集的大小（以比特为单位），包含在片头或 SPS 中。这是条件块 if(long_term_ref_pics_present_flag) 在规范第 7.3.6.1 节中的比特数。
* - __u8
      - ``num_active_dpb_entries``
      - ``dpb`` 中的条目数量
* - `__u8`
      - `num_poc_st_curr_before`
      - 短期参考图片集中在当前帧之前的参考图片数量
* - `__u8`
      - `num_poc_st_curr_after`
      - 短期参考图片集中在当前帧之后的参考图片数量
* - `__u8`
      - `num_poc_lt_curr`
      - 长期参考图片集中的参考图片数量
* - `__u8`
      - `poc_st_curr_before[V4L2_HEVC_DPB_ENTRIES_NUM_MAX]`
      - 如8.3.2节“参考图片集解码过程”所述，提供DPB数组中短期前参考图片的索引
* - `__u8`
      - `poc_st_curr_after[V4L2_HEVC_DPB_ENTRIES_NUM_MAX]`
      - 如8.3.2节“参考图片集解码过程”所述，提供DPB数组中短期后参考图片的索引
* - `__u8`
      - `poc_lt_curr[V4L2_HEVC_DPB_ENTRIES_NUM_MAX]`
      - 如8.3.2节“参考图片集解码过程”所述，提供DPB数组中长期参考图片的索引
* - `__u8`
      - `num_delta_pocs_of_ref_rps_idx`
      - 当slice header中的short_term_ref_pic_set_sps_flag等于0时，它与派生值NumDeltaPocs[RefRpsIdx]相同。可用于解析slice header中的RPS数据，而不是使用@short_term_ref_pic_set_size跳过它。当short_term_ref_pic_set_sps_flag的值等于1时，num_delta_pocs_of_ref_rps_idx应设置为0
* - 结构体 :c:type:`v4l2_hevc_dpb_entry`
      - `dpb[V4L2_HEVC_DPB_ENTRIES_NUM_MAX]`
      - 解码图片缓冲区，用于存储参考帧的元数据
* - `__u64`
      - `flags`
      - 参见 :ref:`Decode Parameters Flags <hevc_decode_params_flags>`

.. _hevc_decode_params_flags:

``解码参数标志``

.. cssclass:: longtable

.. flat-table::
    :header-rows:  0
    :stub-columns: 0
    :widths:       1 1 2

    * - `V4L2_HEVC_DECODE_PARAM_FLAG_IRAP_PIC`
      - 0x00000001
      -
    * - `V4L2_HEVC_DECODE_PARAM_FLAG_IDR_PIC`
      - 0x00000002
      -
    * - `V4L2_HEVC_DECODE_PARAM_FLAG_NO_OUTPUT_OF_PRIOR`
      - 0x00000004
      -

.. _v4l2-codec-stateless-av1:

``V4L2_CID_STATELESS_AV1_SEQUENCE (结构体)``
    代表一个AV1序列OBU（开放比特流单元）。参见 :ref:`av1` 中的5.5节“序列头OBU语法”以获取更多详细信息
```markdown
.. c:type:: v4l2_ctrl_av1_sequence

.. cssclass:: longtable

.. tabularcolumns:: |p{5.8cm}|p{4.8cm}|p{6.6cm}|

.. flat-table:: struct v4l2_ctrl_av1_sequence
    :header-rows:  0
    :stub-columns: 0
    :widths:       1 1 2

    * - __u32
      - ``flags``
      - 参见 :ref:`AV1 序列标志 <av1_sequence_flags>`
    * - __u8
      - ``seq_profile``
      - 指定编码视频序列中可以使用的功能
    * - __u8
      - ``order_hint_bits``
      - 指定每个帧的 order_hint 字段所用的位数
    * - __u8
      - ``bit_depth``
      - 指定序列的位深度，具体描述参见 :ref:`av1` 中第 5.5.2 节 “颜色配置语法” 的更多详细信息
    * - __u8
      - ``reserved``
      - 应用程序和驱动程序必须将其设置为零
    * - __u16
      - ``max_frame_width_minus_1``
      - 指定由该序列头表示的帧的最大宽度减 1

.. _av1_sequence_flags:

``AV1 序列标志``

.. cssclass:: longtable

.. flat-table::
    :header-rows:  0
    :stub-columns: 0
    :widths:       1 1 2

    * - ``V4L2_AV1_SEQUENCE_FLAG_STILL_PICTURE``
      - 0x00000001
      - 如果设置，则指定编码视频序列仅包含一个编码帧。如果没有设置，则指定编码视频序列包含一个或多个编码帧
    * - ``V4L2_AV1_SEQUENCE_FLAG_USE_128X128_SUPERBLOCK``
      - 0x00000002
      - 如果设置，则表示超级块包含 128x128 亮度样本。如果等于 0，则表示超级块包含 64x64 亮度样本。包含的色度样本数量取决于 subsampling_x 和 subsampling_y
    * - ``V4L2_AV1_SEQUENCE_FLAG_ENABLE_FILTER_INTRA``
      - 0x00000004
      - 如果设置，则指定 use_filter_intra 语法元素可能在场。如果没有设置，则指定 use_filter_intra 语法元素不会在场
```
* - ``V4L2_AV1_SEQUENCE_FLAG_ENABLE_INTRA_EDGE_FILTER``
      - 0x00000008
      - 指定是否启用帧内边缘滤波过程

* - ``V4L2_AV1_SEQUENCE_FLAG_ENABLE_INTERINTRA_COMPOUND``
      - 0x00000010
      - 如果设置，指定帧间块的模式信息中可以包含语法元素 interintra。如果未设置，则指定语法元素 interintra 不会出现

* - ``V4L2_AV1_SEQUENCE_FLAG_ENABLE_MASKED_COMPOUND``
      - 0x00000020
      - 如果设置，指定帧间块的模式信息中可以包含语法元素 compound_type。如果未设置，则指定语法元素 compound_type 不会出现

* - ``V4L2_AV1_SEQUENCE_FLAG_ENABLE_WARPED_MOTION``
      - 0x00000040
      - 如果设置，表示允许使用 allow_warped_motion 语法元素。如果未设置，则表示 allow_warped_motion 语法元素不会出现

* - ``V4L2_AV1_SEQUENCE_FLAG_ENABLE_DUAL_FILTER``
      - 0x00000080
      - 如果设置，表示可以在水平和垂直方向上独立指定帧间预测滤波类型。如果该标志为 0，则只能指定一种滤波类型，并在两个方向上都使用该类型

* - ``V4L2_AV1_SEQUENCE_FLAG_ENABLE_ORDER_HINT``
      - 0x00000100
      - 如果设置，表示可以根据顺序提示值使用相关工具。如果未设置，则表示基于顺序提示的相关工具被禁用

* - ``V4L2_AV1_SEQUENCE_FLAG_ENABLE_JNT_COMP``
      - 0x00000200
      - 如果设置，表示帧间预测过程中可以使用距离权重过程

* - ``V4L2_AV1_SEQUENCE_FLAG_ENABLE_REF_FRAME_MVS``
      - 0x00000400
      - 如果设置，表示可以使用 use_ref_frame_mvs 语法元素。如果未设置，则表示 use_ref_frame_mvs 语法元素不会出现

* - ``V4L2_AV1_SEQUENCE_FLAG_ENABLE_SUPERRES``
      - 0x00000800
      - 如果设置，指定 use_superres 语法元素将出现在未压缩头中。如果未设置，则指定 use_superres 语法元素不会出现（取而代之的是在未压缩头中将 use_superres 设置为 0 而不读取）

* - ``V4L2_AV1_SEQUENCE_FLAG_ENABLE_CDEF``
      - 0x00001000
      - 如果设置，指定可以启用 cdef 滤波。如果未设置，则指定 cdef 滤波被禁用
* - ``V4L2_AV1_SEQUENCE_FLAG_ENABLE_RESTORATION``
      - 0x00002000
      - 如果设置，则表示可以启用环路恢复滤波。如果没有设置，则表示禁用环路恢复滤波。
* - ``V4L2_AV1_SEQUENCE_FLAG_MONO_CHROME``
      - 0x00004000
      - 如果设置，则表示视频不包含 U 和 V 色度平面。如果没有设置，则表示视频包含 Y、U 和 V 色度平面。
* - ``V4L2_AV1_SEQUENCE_FLAG_COLOR_RANGE``
      - 0x00008000
      - 如果设置，则表示全范围表示，即“全范围量化”。如果没有设置，则表示演播室范围表示，即“有限范围量化”。
* - ``V4L2_AV1_SEQUENCE_FLAG_SUBSAMPLING_X``
      - 0x00010000
      - 指定色度子采样格式。
* - ``V4L2_AV1_SEQUENCE_FLAG_SUBSAMPLING_Y``
      - 0x00020000
      - 指定色度子采样格式。
* - ``V4L2_AV1_SEQUENCE_FLAG_FILM_GRAIN_PARAMS_PRESENT``
      - 0x00040000
      - 指定编码视频序列中是否包含胶片颗粒参数。
* - ``V4L2_AV1_SEQUENCE_FLAG_SEPARATE_UV_DELTA_Q``
      - 0x00080000
      - 如果设置，则表示 U 和 V 平面可以有不同的增量量化值。如果没有设置，则表示 U 和 V 平面将共享相同的增量量化值。

``V4L2_CID_STATELESS_AV1_TILE_GROUP_ENTRY (struct)``
    表示 AV1 Tile Group 内的一个单独的 AV1 Tile。注意，MiRowStart、MiRowEnd、MiColStart 和 MiColEnd 可以从 struct v4l2_ctrl_av1_frame 中的 struct v4l2_av1_tile_info 使用 tile_row 和 tile_col 获取。更多详细信息请参阅 :ref:`av1` 中的第 6.10.1 节 “General tile group OBU semantics”。
```markdown
.. c:type:: v4l2_ctrl_av1_tile_group_entry

.. cssclass:: longtable

.. tabularcolumns:: |p{5.8cm}|p{4.8cm}|p{6.6cm}|

.. flat-table:: struct v4l2_ctrl_av1_tile_group_entry
    :header-rows:  0
    :stub-columns: 0
    :widths:       1 1 2

    * - __u32
      - ``tile_offset``
      - 相对于OBU数据的偏移量，即编码瓷砖数据的实际起始位置
    * - __u32
      - ``tile_size``
      - 指定编码瓷砖的大小（以字节为单位）。等同于:ref:`av1`中的“TileSize”
    * - __u32
      - ``tile_row``
      - 指定当前瓷砖所在的行。等同于:ref:`av1`中的“TileRow”
    * - __u32
      - ``tile_col``
      - 指定当前瓷砖所在的列。等同于:ref:`av1`中的“TileColumn”

.. c:type:: v4l2_av1_warp_model

AV1 Warp Model 如:ref:`av1`中第3节“符号和缩写术语”所述

.. raw:: latex

    \scriptsize

.. tabularcolumns:: |p{7.4cm}|p{0.3cm}|p{9.6cm}|

.. flat-table::
    :header-rows:  0
    :stub-columns: 0
    :widths:       1 1 2

    * - ``V4L2_AV1_WARP_MODEL_IDENTITY``
      - 0
      - Warp模型只是一个恒等变换
    * - ``V4L2_AV1_WARP_MODEL_TRANSLATION``
      - 1
      - Warp模型是一个纯平移
    * - ``V4L2_AV1_WARP_MODEL_ROTZOOM``
      - 2
      - Warp模型是一个旋转+对称缩放+平移
    * - ``V4L2_AV1_WARP_MODEL_AFFINE``
      - 3
      - Warp模型是一个一般的仿射变换

.. c:type:: v4l2_av1_reference_frame

AV1 参考帧 如:ref:`av1`中第6.10.24节“参考帧语义”所述
```
以下是你提供的文本的中文翻译：

```latex
\scriptsize
```

```plaintext
.. tabularcolumns:: |p{7.4cm}|p{0.3cm}|p{9.6cm}|

.. flat-table::
    :header-rows:  0
    :stub-columns: 0
    :widths:       1 1 2

    * - ``V4L2_AV1_REF_INTRA_FRAME``
      - 0
      - Intra Frame Reference
    * - ``V4L2_AV1_REF_LAST_FRAME``
      - 1
      - Last Frame Reference
    * - ``V4L2_AV1_REF_LAST2_FRAME``
      - 2
      - Last2 Frame Reference
    * - ``V4L2_AV1_REF_LAST3_FRAME``
      - 3
      - Last3 Frame Reference
    * - ``V4L2_AV1_REF_GOLDEN_FRAME``
      - 4
      - Golden Frame Reference
    * - ``V4L2_AV1_REF_BWDREF_FRAME``
      - 5
      - BWD Frame Reference
    * - ``V4L2_AV1_REF_ALTREF2_FRAME``
      - 6
      - ALTREF2 Frame Reference
    * - ``V4L2_AV1_REF_ALTREF_FRAME``
      - 7
      - ALTREF Frame Reference
```

```plaintext
.. c:type:: v4l2_av1_global_motion

AV1全局运动参数，如在 :ref:`av1` 的第6.8.17节 "Global motion params semantics" 中所述。
```

```plaintext
.. cssclass:: longtable

.. tabularcolumns:: |p{1.5cm}|p{5.8cm}|p{10.0cm}|

.. flat-table:: struct v4l2_av1_global_motion
    :header-rows:  0
    :stub-columns: 0
    :widths:       1 1 2

    * - __u8
      - ``flags[V4L2_AV1_TOTAL_REFS_PER_FRAME]``
      - 包含每个参考帧标志位的位字段。更多详细信息请参见 :ref:`AV1 全局运动标志位 <av1_global_motion_flags>`
```

希望这个翻译对你有帮助！如果你有任何进一步的问题或需要调整，请告诉我。
* - 枚举 :c:type:`v4l2_av1_warp_model`
  - ``type[V4L2_AV1_TOTAL_REFS_PER_FRAME]``
  - 使用的全局运动变换类型
* - __s32
  - ``params[V4L2_AV1_TOTAL_REFS_PER_FRAME][6]``
  - 此字段与 :ref:`av1` 中的 "gm_params" 具有相同含义
* - __u8
  - ``invalid``
  - 位字段，指示给定参考帧的全局运动参数是否无效。参见第 7.11.3.6 节 Setup shear process 和变量 "warpValid"。使用 V4L2_AV1_GLOBAL_MOTION_IS_INVALID(ref) 创建合适的掩码
* - __u8
  - ``reserved[3]``
  - 应用程序和驱动程序必须将其设置为零

.. _av1_global_motion_flags:

``AV1 全局运动标志``

.. cssclass:: longtable

.. flat-table::
    :header-rows:  0
    :stub-columns: 0
    :widths:       1 1 2

    * - ``V4L2_AV1_GLOBAL_MOTION_FLAG_IS_GLOBAL``
      - 0x00000001
      - 指定特定参考帧是否包含全局运动参数
* - ``V4L2_AV1_GLOBAL_MOTION_FLAG_IS_ROT_ZOOM``
      - 0x00000002
      - 指定特定参考帧是否使用旋转和缩放全局运动
* - ``V4L2_AV1_GLOBAL_MOTION_FLAG_IS_TRANSLATION``
      - 0x00000004
      - 指定特定参考帧是否使用平移全局运动

.. c:type:: v4l2_av1_frame_restoration_type

AV1 帧恢复类型
.. raw:: latex

    \scriptsize

.. tabularcolumns:: |p{7.4cm}|p{0.3cm}|p{9.6cm}|

.. flat-table::
    :header-rows:  0
    :stub-columns: 0
    :widths:       1 1 2

    * - ``V4L2_AV1_FRAME_RESTORE_NONE``
      - 0
      - 不应用任何滤波器
* - ``V4L2_AV1_FRAME_RESTORE_WIENER``
      - 1
      - 调用维纳滤波器过程
* - ``V4L2_AV1_FRAME_RESTORE_SGRPROJ``
      - 2
      - 调用自引导滤波器过程
* - ``V4L2_AV1_FRAME_RESTORE_SWITCHABLE``
  - 3
  - 修复滤波器可切换
.. c:type:: v4l2_av1_loop_restoration

AV1 Loop Restoration 如 :ref:`av1` 中第 6.10.15 节 "Loop restoration params semantics" 所描述
.. cssclass:: longtable

.. tabularcolumns:: |p{1.5cm}|p{5.8cm}|p{10.0cm}|

.. flat-table:: struct v4l2_av1_loop_restoration
    :header-rows:  0
    :stub-columns: 0
    :widths:       1 1 2

    * - __u8
      - ``flags``
      - 参见 :ref:`AV1 Loop Restoration Flags <av1_loop_restoration_flags>`
* - __u8
      - ``lr_unit_shift``
      - 指定亮度修复尺寸是否应减半
* - __u8
      - ``lr_uv_shift``
      - 指定色度尺寸是否为亮度尺寸的一半
* - __u8
      - ``reserved``
      - 应用程序和驱动程序必须将其设置为零
* - :c:type:`v4l2_av1_frame_restoration_type`
      - ``frame_restoration_type[V4L2_AV1_NUM_PLANES_MAX]``
      - 指定每个平面使用的修复类型
* - __u8
      - ``loop_restoration_size[V4L2_AV1_MAX_NUM_PLANES]``
      - 指定当前平面上循环修复单元的大小，单位为样本数
.. _av1_loop_restoration_flags:

``AV1 Loop Restoration Flags``

.. cssclass:: longtable

.. flat-table::
    :header-rows:  0
    :stub-columns: 0
    :widths:       1 1 2

    * - ``V4L2_AV1_LOOP_RESTORATION_FLAG_USES_LR``
      - 0x00000001
      - 保留与 :ref:`av1` 中 UsesLr 相同的含义
* - ``V4L2_AV1_LOOP_RESTORATION_FLAG_USES_CHROMA_LR``
      - 0x00000002
      - 保留与 :ref:`av1` 中 UsesChromaLr 相同的含义
```markdown
.. c:type:: v4l2_av1_cdef

AV1 CDEF 参数语义如 :ref:`av1` 中第 6.10.14 节 “CDEF 参数语义” 所述。
.. cssclass:: longtable

.. tabularcolumns:: |p{1.5cm}|p{5.8cm}|p{10.0cm}|

.. flat-table:: struct v4l2_av1_cdef
    :header-rows:  0
    :stub-columns: 0
    :widths:       1 1 2

    * - __u8
      - ``damping_minus_3``
      - 控制去环滤波器中的阻尼量
* - __u8
      - ``bits``
      - 指定用于指定要应用的 CDEF 滤波器所需的位数
* - __u8
      - ``y_pri_strength[V4L2_AV1_CDEF_MAX]``
      - 指定主要滤波器的强度
* - __u8
      - ``y_sec_strength[V4L2_AV1_CDEF_MAX]``
      - 指定次要滤波器的强度
* - __u8
      - ``uv_pri_strength[V4L2_AV1_CDEF_MAX]``
      - 指定主要滤波器的强度
* - __u8
      - ``uv_secondary_strength[V4L2_AV1_CDEF_MAX]``
      - 指定次要滤波器的强度
.. c:type:: v4l2_av1_segment_feature

AV1 分段特性如 :ref:`av1` 中第 3 节 “符号和缩略语” 所述。
.. raw:: latex

    \scriptsize

.. tabularcolumns:: |p{7.4cm}|p{0.3cm}|p{9.6cm}|

.. flat-table::
    :header-rows:  0
    :stub-columns: 0
    :widths:       1 1 2

    * - ``V4L2_AV1_SEG_LVL_ALT_Q``
      - 0
      - 量化分段特性的索引
* - ``V4L2_AV1_SEG_LVL_ALT_LF_Y_V``
      - 1
      - 垂直亮度环路滤波器分段特性的索引
```
* - ``V4L2_AV1_SEG_LVL_REF_FRAME``
  - 5
  - 引用帧段特征的索引
* - ``V4L2_AV1_SEG_LVL_REF_SKIP``
  - 6
  - 跳过段特征的索引
* - ``V4L2_AV1_SEG_LVL_REF_GLOBALMV``
  - 7
  - 全局运动矢量特征的索引
* - ``V4L2_AV1_SEG_LVL_MAX``
  - 8
  - 段特征的数量
.. c:type:: v4l2_av1_segmentation

根据 AV1 规范第 6.8.13 节 “Segmentation params semantics” 定义的 AV1 分割参数
.. cssclass:: longtable

.. tabularcolumns:: |p{1.5cm}|p{5.8cm}|p{10.0cm}|

.. flat-table:: struct v4l2_av1_segmentation
    :header-rows:  0
    :stub-columns: 0
    :widths:       1 1 2

    * - __u8
      - ``flags``
      - 参见 :ref:`AV1 分割标志 <av1_segmentation_flags>`
    * - __u8
      - ``last_active_seg_id``
      - 表示具有启用功能的最高编号段 ID。在解码段 ID 时，仅解码与已使用段对应的选项
* - __u8
      - ``feature_enabled[V4L2_AV1_MAX_SEGMENTS]``
      - 位掩码定义了每个段中启用的特征。使用 V4L2_AV1_SEGMENT_FEATURE_ENABLED 构建合适的掩码
* - __u16
      - ``feature_data[V4L2_AV1_MAX_SEGMENTS][V4L2_AV1_SEG_LVL_MAX]``
      - 附加到每个特征的数据。数据项仅在特征启用时有效
.. _av1_segmentation_flags:

``AV1 分割标志``

.. cssclass:: longtable

.. flat-table::
    :header-rows:  0
    :stub-columns: 0
    :widths:       1 1 2

    * - ``V4L2_AV1_SEGMENTATION_FLAG_ENABLED``
      - 0x00000001
      - 如果设置，表示该帧使用了分割工具。如果未设置，表示该帧不使用分割
* - ``V4L2_AV1_SEGMENTATION_FLAG_UPDATE_MAP``
      - 0x00000002
      - 如果设置，表示在解码此帧期间更新了分割图。如果未设置，表示使用前一帧的分割图
* - ``V4L2_AV1_SEGMENTATION_FLAG_TEMPORAL_UPDATE``
  - 0x00000004
  - 如果设置，表示分割图的更新是相对于现有分割图编码的。如果没有设置，则表示新的分割图是不参考现有分割图进行编码的。
* - ``V4L2_AV1_SEGMENTATION_FLAG_UPDATE_DATA``
  - 0x00000008
  - 如果设置，表示分割图的更新是相对于现有分割图编码的。如果没有设置，则表示新的分割图是不参考现有分割图进行编码的。
* - ``V4L2_AV1_SEGMENTATION_FLAG_SEG_ID_PRE_SKIP``
  - 0x00000010
  - 如果设置，表示段 ID 将在跳过（skip）语法元素之前读取。如果没有设置，则表示跳过（skip）语法元素将首先被读取。

.. c:type:: v4l2_av1_loop_filter

AV1 环路滤波器参数如 :ref:`av1` 中第 6.8.10 节“环路滤波器语义”所定义。

.. cssclass:: longtable

.. tabularcolumns:: |p{1.5cm}|p{5.8cm}|p{10.0cm}|

.. flat-table:: struct v4l2_av1_global_motion
    :header-rows:  0
    :stub-columns: 0
    :widths:       1 1 2

    * - __u8
      - ``flags``
      - 详见 :ref:`AV1 环路滤波器标志 <av1_loop_filter_flags>` 以获取更多详细信息
* - __u8
      - ``level[4]``
      - 包含环路滤波器强度值的数组。根据要滤波的图像平面和滤波的边缘方向（垂直或水平），使用数组中不同的环路滤波器强度值。
* - __u8
      - ``sharpness``
      - 表示锐度级别。环路滤波器强度（loop_filter_level）和环路滤波器锐度（loop_filter_sharpness）共同决定了何时对块边缘进行滤波以及滤波可以改变样本值的程度。环路滤波过程在 :ref:`av1` 的第 7.14 节中有描述。
* - __u8
      - ``ref_deltas[V4L2_AV1_TOTAL_REFS_PER_FRAME]``
      - 包含基于选定参考帧所需的滤波器级别调整。如果此语法元素不存在，则保持其先前值。
* - __u8
      - ``mode_deltas[2]``
      - 包含基于选定模式所需的滤波器级别调整。如果此语法元素不存在，则保持其先前值。
* - __u8
      - ``delta_lf_res``
      - 指定应应用于解码环路滤波器增量值的左移位数。
``AV1 环路滤波器标志``

.. cssclass:: longtable

.. flat-table::
    :header-rows:  0
    :stub-columns: 0
    :widths:       1 1 2

    * - ``V4L2_AV1_LOOP_FILTER_FLAG_DELTA_ENABLED``
      - 0x00000001
      - 如果设置，则表示滤波级别取决于用于预测块的模式和参考帧。如果没有设置，则表示滤波级别不依赖于模式和参考帧。
    * - ``V4L2_AV1_LOOP_FILTER_FLAG_DELTA_UPDATE``
      - 0x00000002
      - 如果设置，则表示存在额外的语法元素，用于指定哪些模式和参考帧差值需要更新。如果没有设置，则表示这些语法元素不存在。
    * - ``V4L2_AV1_LOOP_FILTER_FLAG_DELTA_LF_PRESENT``
      - 0x00000004
      - 指定环路滤波器差值是否存在。
    * - ``V4L2_AV1_LOOP_FILTER_FLAG_DELTA_LF_MULTI``
      - 0x00000008
      - 值等于 1 表示分别发送水平亮度边缘、垂直亮度边缘、U 边缘和 V 边缘的环路滤波器差值。值等于 0 表示所有边缘使用相同的环路滤波器差值。

.. c:type:: v4l2_av1_quantization

AV1 量化参数如 :ref:`av1` 第 6.8.11 节“量化参数语义”中定义的那样。
.. cssclass:: longtable

.. tabularcolumns:: |p{1.5cm}|p{5.8cm}|p{10.0cm}|

.. flat-table:: struct v4l2_av1_quantization
    :header-rows:  0
    :stub-columns: 0
    :widths:       1 1 2

    * - __u8
      - ``flags``
      - 详见 :ref:`AV1 环路滤波器标志 <av1_quantization_flags>`
    * - __u8
      - ``base_q_idx``
      - 指示基础帧 qindex。这用于 Y AC 系数，并作为其他量化器的基础值。
    * - __u8
      - ``delta_q_y_dc``
      - 指示相对于 base_q_idx 的 Y DC 量化器。
    * - __u8
      - ``delta_q_u_dc``
      - 指示相对于 base_q_idx 的 U DC 量化器。
    * - __u8
      - ``delta_q_u_ac``
      - 指示相对于 base_q_idx 的 U AC 量化器。
    * - __u8
      - ``delta_q_v_dc``
      - 指示相对于 base_q_idx 的 V DC 量化器。
* - __u8
      - ``delta_q_v_ac``
      - 表示相对于 base_q_idx 的 V AC 量化器
* - __u8
      - ``qm_y``
      - 指定在亮度平面解码时应使用的量化矩阵中的级别
* - __u8
      - ``qm_u``
      - 指定在色度 U 平面解码时应使用的量化矩阵中的级别
* - __u8
      - ``qm_v``
      - 指定在色度 V 平面解码时应使用的量化矩阵中的级别
* - __u8
      - ``delta_q_res``
      - 指定应应用于解码量化索引差值的左移位数

.. _av1_quantization_flags:

``AV1 量化标志``

.. cssclass:: longtable

.. flat-table::
    :header-rows:  0
    :stub-columns: 0
    :widths:       1 1 2

    * - ``V4L2_AV1_QUANTIZATION_FLAG_DIFF_UV_DELTA``
      - 0x00000001
      - 如果设置，表示 U 和 V 的量化差值分别编码。如果未设置，表示 U 和 V 的量化差值共享一个共同的值
* - ``V4L2_AV1_QUANTIZATION_FLAG_USING_QMATRIX``
      - 0x00000002
      - 如果设置，指定将使用量化矩阵来计算量化器
* - ``V4L2_AV1_QUANTIZATION_FLAG_DELTA_Q_PRESENT``
      - 0x00000004
      - 指定量化索引差值是否存在

.. c:type:: v4l2_av1_tile_info

AV1 Tile 信息如 ref:`av1` 中第 6.8.14 节“Tile 信息语义”所定义

.. cssclass:: longtable

.. tabularcolumns:: |p{1.5cm}|p{5.8cm}|p{10.0cm}|

.. flat-table:: struct v4l2_av1_tile_info
    :header-rows:  0
    :stub-columns: 0
    :widths:       1 1 2

    * - __u8
      - ``flags``
      - 更多详细信息请参见 :ref:`AV1 Tile Info flags <av1_tile_info_flags>`
* - `__u8`
  - `context_update_tile_id`
  - 指定用于CDF更新的瓦片编号
* - `__u8`
  - `tile_cols`
  - 指定帧中水平方向的瓦片数量
* - `__u8`
  - `tile_rows`
  - 指定帧中垂直方向的瓦片数量
* - `__u32`
  - `mi_col_starts[V4L2_AV1_MAX_TILE_COLS + 1]`
  - 一个数组，指定每个瓦片在图像中的起始列（以4x4亮度样本为单位）
* - `__u32`
  - `mi_row_starts[V4L2_AV1_MAX_TILE_ROWS + 1]`
  - 一个数组，指定每个瓦片在图像中的起始行（以4x4亮度样本为单位）
* - `__u32`
  - `width_in_sbs_minus_1[V4L2_AV1_MAX_TILE_COLS]`
  - 指定每个瓦片的宽度减1（以超级块为单位）
* - `__u32`
  - `height_in_sbs_minus_1[V4L2_AV1_MAX_TILE_ROWS]`
  - 指定每个瓦片的高度减1（以超级块为单位）
* - `__u8`
  - `tile_size_bytes`
  - 指定编码每个瓦片大小所需的字节数
* - `__u8`
  - `reserved[3]`
  - 应用程序和驱动程序必须将其设置为零

.. _av1_tile_info_flags:

`AV1 瓦片信息标志`

.. cssclass:: longtable

.. flat-table::
    :header-rows:  0
    :stub-columns: 0
    :widths:       1 1 2

    * - `V4L2_AV1_TILE_INFO_FLAG_UNIFORM_TILE_SPACING`
      - 0x00000001
      - 如果设置，则表示瓦片在整个帧中均匀分布（换句话说，所有瓦片大小相同，除了右侧和底部边缘的瓦片可能较小）。如果未设置，则表示瓦片大小是编码的
``c:type:: v4l2_av1_frame_type``

AV1 帧类型

.. raw:: latex

    \scriptsize

.. tabularcolumns:: |p{7.4cm}|p{0.3cm}|p{9.6cm}|

.. flat-table::
    :header-rows:  0
    :stub-columns: 0
    :widths:       1 1 2

    * - ``V4L2_AV1_KEY_FRAME``
      - 0
      - 关键帧
* - ``V4L2_AV1_INTER_FRAME``
      - 1
      - 交错帧
* - ``V4L2_AV1_INTRA_ONLY_FRAME``
      - 2
      - 帧内编码帧
* - ``V4L2_AV1_SWITCH_FRAME``
      - 3
      - 切换帧

``c:type:: v4l2_av1_interpolation_filter``

AV1 插值滤波器

.. raw:: latex

    \scriptsize

.. tabularcolumns:: |p{7.4cm}|p{0.3cm}|p{9.6cm}|

.. flat-table::
    :header-rows:  0
    :stub-columns: 0
    :widths:       1 1 2

    * - ``V4L2_AV1_INTERPOLATION_FILTER_EIGHTTAP``
      - 0
      - 八点滤波器
* - ``V4L2_AV1_INTERPOLATION_FILTER_EIGHTTAP_SMOOTH``
      - 1
      - 平滑八点滤波器
* - ``V4L2_AV1_INTERPOLATION_FILTER_EIGHTTAP_SHARP``
      - 2
      - 锐化八点滤波器
* - ``V4L2_AV1_INTERPOLATION_FILTER_BILINEAR``
      - 3
      - 双线性滤波器
* - ``V4L2_AV1_INTERPOLATION_FILTER_SWITCHABLE``
      - 4
      - 在块级别上信号选择的滤波器

``c:type:: v4l2_av1_tx_mode``

如 :ref:`av1` 中第 6.8.21 节“TX 模式语义”所描述的 AV1 Tx 模式
```latex
\scriptsize

\begin{tabular}{|p{7.4cm}|p{0.3cm}|p{9.6cm}|}
\hline
\texttt{V4L2\_AV1\_TX\_MODE\_ONLY\_4X4} & 0 & 逆变换将仅使用 4x4 变换 \\
\hline
\texttt{V4L2\_AV1\_TX\_MODE\_LARGEST} & 1 & 逆变换将使用适合该块的最大变换尺寸 \\
\hline
\texttt{V4L2\_AV1\_TX\_MODE\_SELECT} & 2 & 变换尺寸的选择将为每个块显式指定 \\
\hline
\end{tabular}

\texttt{V4L2\_CID\_STATELESS\_AV1\_FRAME (struct)} 表示一个 Frame Header OBU。更多详细信息请参见 :ref:`av1` 中的 6.8 节 “Frame Header OBU 语义”。

.. c:type:: v4l2_ctrl_av1_frame

.. cssclass:: longtable

\begin{tabular}{|p{5.8cm}|p{4.8cm}|p{6.6cm}|}
\hline
struct :c:type:`v4l2_av1_tile_info` & \texttt{tile_info} & 瓦片信息 \\
\hline
struct :c:type:`v4l2_av1_quantization` & \texttt{quantization} & 量化参数 \\
\hline
struct :c:type:`v4l2_av1_segmentation` & \texttt{segmentation} & 分段参数 \\
\hline
\_\_u8 & \texttt{superres\_denom} & 上采样比例的分母 \\
\hline
struct :c:type:`v4l2_av1_loop_filter` & \texttt{loop\_filter} & 环路滤波器参数 \\
\hline
struct :c:type:`v4l2_av1_cdef` & \texttt{cdef} & CDEF 参数 \\
\hline
\_\_u8 & \texttt{skip\_mode\_frame[2]} & 当 skip\_mode 等于 1 时，用于复合预测的帧 \\
\hline
\_\_u8 & \texttt{primary\_ref\_frame} & 指定包含应在帧开始时加载的 CDF 值和其他状态的参考帧 \\
\hline
struct :c:type:`v4l2_av1_loop_restoration` & \texttt{loop\_restoration} & 环路恢复参数 \\
\hline
\end{tabular}
```
* - 结构体 :c:type:`v4l2_av1_loop_global_motion`
      - ``global_motion``
      - 全局运动参数
* - __u32
      - ``flags``
      - 详细信息请参见 :ref:`AV1帧标志<av1_frame_flags>`
* - 枚举 :c:type:`v4l2_av1_frame_type`
      - ``frame_type``
      - 指定 AV1 帧类型
    * - __u32
      - ``order_hint``
      - 指定该帧预期输出顺序的OrderHintBits最低有效位
* - __u32
      - ``upscaled_width``
      - 放大后的宽度
* - 枚举 :c:type:`v4l2_av1_interpolation_filter`
      - ``interpolation_filter``
      - 指定用于执行帧间预测的滤波器选择
* - 枚举 :c:type:`v4l2_av1_tx_mode`
      - ``tx_mode``
      - 指定变换大小的确定方式
* - __u32
      - ``frame_width_minus_1``
      - 加 1 可得帧的宽度
* - __u32
      - ``frame_height_minus_1``
      - 加 1 可得帧的高度
* - __u16
      - ``render_width_minus_1``
      - 加 1 可得帧在亮度样本中的渲染宽度
* - __u16
      - ``render_height_minus_1``
      - 加 1 可得帧在亮度样本中的渲染高度
* - `__u32`
  - `current_frame_id`
  - 指定当前帧的帧 ID 号。帧 ID 号是附加信息，不会影响解码过程，但为解码器提供了一种检测缺失参考帧的方法，以便采取适当的措施。
* - `__u8`
  - `buffer_removal_time[V4L2_AV1_MAX_OPERATING_POINTS]`
  - 指定从最后一个随机访问点的移除时间开始计数的帧移除时间（以DecCT时钟滴答为单位），针对操作点 `opNum`。
* - `__u8`
  - `reserved[4]`
  - 应用程序和驱动程序必须将其设置为零。
* - `__u32`
  - `order_hints[V4L2_AV1_TOTAL_REFS_PER_FRAME]`
  - 指定每个参考帧的预期输出顺序提示。该字段对应于规范中的 `OrderHints` 变量（第 5.9.2 节“未压缩头语法”）。因此，仅用于非帧内帧，并在其他情况下被忽略。 `order_hints[0]` 总是被忽略。
* - `__u64`
  - `reference_frame_ts[V4L2_AV1_TOTAL_REFS_PER_FRAME]`
  - 列表中每个参考帧的 V4L2 时间戳，从枚举类型 `v4l2_av1_reference_frame` 的 `V4L2_AV1_REF_LAST_FRAME` 开始。这表示规范中描述的状态，并通过用户空间通过第 7.20 节中的“参考帧更新过程”进行更新。该时间戳指的是结构体 `v4l2_buffer` 中的 `timestamp` 字段。使用函数 `v4l2_timeval_to_ns()` 将结构体 `v4l2_buffer` 中的 `timeval` 类型转换为 `__u64`。
* - `__s8`
  - `ref_frame_idx[V4L2_AV1_REFS_PER_FRAME]`
  - 一个索引到 `reference_frame_ts`，代表由帧间预测使用的有序参考列表。与同名的比特流语法元素匹配。
* - `__u8`
  - `refresh_frame_flags`
  - 包含一个位掩码，指定哪些参考帧槽将在当前帧解码后进行更新。

.. _av1_frame_flags:

`AV1 帧标志`

.. cssclass:: longtable

.. flat-table::
    :header-rows:  0
    :stub-columns: 0
    :widths:       1 1 2

    * - `V4L2_AV1_FRAME_FLAG_SHOW_FRAME`
      - 0x00000001
      - 如果设置，则指定此帧应立即输出。如果没有设置，则指定此帧不应立即输出；如果稍后的未压缩头使用 `show_existing_frame` 等于 1，则可能会在稍后输出。
* - `V4L2_AV1_FRAME_FLAG_SHOWABLE_FRAME`
      - 0x00000002
      - 如果设置，则指定可以使用 `show_existing_frame` 机制输出该帧。如果没有设置，则指定该帧将不会使用 `show_existing_frame` 机制输出。
* - ``V4L2_AV1_FRAME_FLAG_ERROR_RESILIENT_MODE``
      - 0x00000004
      - 指定是否启用了错误恢复模式
* - ``V4L2_AV1_FRAME_FLAG_DISABLE_CDF_UPDATE``
      - 0x00000008
      - 指定是否禁用符号解码过程中的CDF更新
* - ``V4L2_AV1_FRAME_FLAG_ALLOW_SCREEN_CONTENT_TOOLS``
      - 0x00000010
      - 如果设置，则表示帧内块可以使用调色板编码。如果未设置，则表示从不使用调色板编码
* - ``V4L2_AV1_FRAME_FLAG_FORCE_INTEGER_MV``
      - 0x00000020
      - 如果设置，则指定运动矢量总是整数。如果未设置，则指定运动矢量可以包含分数位
* - ``V4L2_AV1_FRAME_FLAG_ALLOW_INTRABC``
      - 0x00000040
      - 如果设置，则表示此帧中可以使用帧内块复制。如果未设置，则表示此帧中不允许使用帧内块复制
* - ``V4L2_AV1_FRAME_FLAG_USE_SUPERRES``
      - 0x00000080
      - 如果设置，则表示需要上采样
* - ``V4L2_AV1_FRAME_FLAG_ALLOW_HIGH_PRECISION_MV``
      - 0x00000100
      - 如果设置，则指定运动矢量精度为八分之一像素。如果未设置，则指定运动矢量精度为四分之一像素
* - ``V4L2_AV1_FRAME_FLAG_IS_MOTION_MODE_SWITCHABLE``
      - 0x00000200
      - 如果未设置，则指定仅使用SIMPLE运动模式
* - ``V4L2_AV1_FRAME_FLAG_USE_REF_FRAME_MVS``
      - 0x00000400
      - 如果设置，则指定在解码当前帧时可以使用前一帧的运动矢量信息。如果未设置，则指定不使用该信息
* - ``V4L2_AV1_FRAME_FLAG_DISABLE_FRAME_END_UPDATE_CDF``
      - 0x00000800
      - 如果设置，则表示禁用了帧末尾的CDF更新。如果未设置，则表示启用了帧末尾的CDF更新
* - ``V4L2_AV1_FRAME_FLAG_ALLOW_WARPED_MOTION``
      - 0x00001000
      - 如果设置，则表示语法元素motion_mode可能在场，如果未设置，则表示语法元素motion_mode不会在场
* - ``V4L2_AV1_FRAME_FLAG_REFERENCE_SELECT``
      - 0x00002000
      - 如果设置，则指定帧间块的模式信息包含指示是否使用单参考或复合参考预测的语法元素comp_mode。如果未设置，则指定所有帧间块都使用单预测
* - ``V4L2_AV1_FRAME_FLAG_REDUCED_TX_SET``
      - 0x00004000
      - 如果设置，表示该帧仅限于完整变换类型集的一个缩减子集。
* - ``V4L2_AV1_FRAME_FLAG_SKIP_MODE_ALLOWED``
      - 0x00008000
      - 此标志保留了 :ref:`av1` 中 SkipModeAllowed 的含义。
* - ``V4L2_AV1_FRAME_FLAG_SKIP_MODE_PRESENT``
      - 0x00010000
      - 如果设置，表示语法元素 skip_mode 将出现；如果没有设置，则表示该帧不会使用 skip_mode。
* - ``V4L2_AV1_FRAME_FLAG_FRAME_SIZE_OVERRIDE``
      - 0x00020000
      - 如果设置，表示帧大小将被指定为参考帧之一的大小，或者根据 frame_width_minus_1 和 frame_height_minus_1 语法元素计算得出。如果没有设置，则表示帧大小等于序列头中的大小。
* - ``V4L2_AV1_FRAME_FLAG_BUFFER_REMOVAL_TIME_PRESENT``
      - 0x00040000
      - 如果设置，表示 buffer_removal_time 出现。如果没有设置，则表示 buffer_removal_time 不出现。
* - ``V4L2_AV1_FRAME_FLAG_FRAME_REFS_SHORT_SIGNALING``
      - 0x00080000
      - 如果设置，表示仅显式信号两个参考帧。如果没有设置，则表示所有参考帧都显式信号。

``V4L2_CID_STATELESS_AV1_FILM_GRAIN (struct)``
    表示可选的胶片颗粒参数。更多详细信息请参见 :ref:`av1` 中的第 6.8.20 节 “Film grain params semantics”。

.. c:type:: v4l2_ctrl_av1_film_grain

.. cssclass:: longtable

.. tabularcolumns:: |p{1.5cm}|p{5.8cm}|p{10.0cm}|

.. flat-table:: struct v4l2_ctrl_av1_film_grain
    :header-rows:  0
    :stub-columns: 0
    :widths:       1 1 2

    * - __u8
      - ``flags``
      - 请参见 :ref:`AV1 Film Grain Flags <av1_film_grain_flags>`
* - __u8
      - ``cr_mult``
      - 代表用于推导 cr 组件缩放函数输入索引的 cr 组件乘数。
* - __u16
      - ``grain_seed``
      - 指定在胶片颗粒合成过程中使用的伪随机数的起始值。
* - __u8
      - ``film_grain_params_ref_idx``
      - 指示包含用于本帧的胶片颗粒参数的参考帧
* - __u8
      - ``num_y_points``
      - 指定亮度分量的分段线性缩放函数的点数
* - __u8
      - ``point_y_value[V4L2_AV1_MAX_NUM_Y_POINTS]``
      - 表示亮度分量分段线性缩放函数中第 i 个点的 x（亮度值）坐标。这些值按 0..255 的比例传递。对于 10 位视频，这些值对应于亮度值除以 4。对于 12 位视频，这些值对应于亮度值除以 16。
* - __u8
      - ``point_y_scaling[V4L2_AV1_MAX_NUM_Y_POINTS]``
      - 表示亮度分量分段线性缩放函数中第 i 个点的缩放（输出）值
* - __u8
      - ``num_cb_points``
      - 指定色度分量 cb 的分段线性缩放函数的点数
* - __u8
      - ``point_cb_value[V4L2_AV1_MAX_NUM_CB_POINTS]``
      - 表示色度分量 cb 分段线性缩放函数中第 i 个点的 x 坐标。这些值按 0..255 的比例传递。
* - __u8
      - ``point_cb_scaling[V4L2_AV1_MAX_NUM_CB_POINTS]``
      - 表示色度分量 cb 分段线性缩放函数中第 i 个点的缩放（输出）值
* - __u8
      - ``num_cr_points``
      - 表示色度分量 cr 的分段线性缩放函数的点数
* - __u8
      - ``point_cr_value[V4L2_AV1_MAX_NUM_CR_POINTS]``
      - 表示色度分量 cr 分段线性缩放函数中第 i 个点的 x 坐标。这些值按 0..255 的比例传递。
* - __u8
      - ``point_cr_scaling[V4L2_AV1_MAX_NUM_CR_POINTS]``
      - 表示色度分量 cr 分段线性缩放函数中第 i 个点的缩放（输出）值
* - `__u8`
      - `grain_scaling_minus_8`
      - 表示应用于色度分量值的偏移 -8
`grain_scaling_minus_8` 的取值范围是 0~3，并确定了胶片颗粒标准差的范围和量化步长

* - `__u8`
      - `ar_coeff_lag`
      - 指定用于亮度和色度的自回归系数的数量

* - `__u8`
      - `ar_coeffs_y_plus_128[V4L2_AV1_AR_COEFFS_SIZE]`
      - 指定用于 Y 平面的自回归系数

* - `__u8`
      - `ar_coeffs_cb_plus_128[V4L2_AV1_AR_COEFFS_SIZE]`
      - 指定用于 U 平面的自回归系数

* - `__u8`
      - `ar_coeffs_cr_plus_128[V4L2_AV1_AR_COEFFS_SIZE]`
      - 指定用于 V 平面的自回归系数

* - `__u8`
      - `ar_coeff_shift_minus_6`
      - 指定自回归系数的范围。值 0、1、2 和 3 分别对应自回归系数的范围 [-2, 2)、[-1, 1)、[-0.5, 0.5) 和 [-0.25, 0.25)

* - `__u8`
      - `grain_scale_shift`
      - 指定在颗粒合成过程中高斯随机数应缩小的程度

* - `__u8`
      - `cb_mult`
      - 表示用于计算输入索引到色度分量缩放函数时所用的 cb 分量乘数

* - `__u8`
      - `cb_luma_mult`
      - 表示用于计算输入索引到色度分量缩放函数时所用的平均亮度分量乘数
* - `__u8`
  - `cr_luma_mult`
  - 表示用于计算输入索引以推导 CR 分量缩放函数时使用的亮度分量的乘数
* - `__u16`
  - `cb_offset`
  - 表示用于计算输入索引以推导 CB 分量缩放函数时使用的偏移量
* - `__u16`
  - `cr_offset`
  - 表示用于计算输入索引以推导 CR 分量缩放函数时使用的偏移量
* - `__u8`
  - `reserved[4]`
  - 应用程序和驱动程序必须将其设置为零

.. _av1_film_grain_flags:

`AV1 电影颗粒标志`

.. cssclass:: longtable

.. flat-table::
    :header-rows:  0
    :stub-columns: 0
    :widths:       1 1 2

    * - `V4L2_AV1_FILM_GRAIN_FLAG_APPLY_GRAIN`
      - 0x00000001
      - 如果设置，表示应在此帧上添加电影颗粒。如果没有设置，则表示不应添加电影颗粒
* - `V4L2_AV1_FILM_GRAIN_FLAG_UPDATE_GRAIN`
      - 0x00000002
      - 如果设置，表示应发送一组新的参数。如果没有设置，则表示应使用前一组参数
* - `V4L2_AV1_FILM_GRAIN_FLAG_CHROMA_SCALING_FROM_LUMA`
      - 0x00000004
      - 如果设置，表示色度缩放是从亮度缩放推断出来的
* - `V4L2_AV1_FILM_GRAIN_FLAG_OVERLAP`
      - 0x00000008
      - 如果设置，表示应应用电影颗粒块之间的重叠。如果没有设置，则表示不应应用电影颗粒块之间的重叠
* - `V4L2_AV1_FILM_GRAIN_FLAG_CLIP_TO_RESTRICTED_RANGE`
      - 0x00000010
      - 如果设置，表示应在添加电影颗粒后对样本值应用受限（即工作室范围）裁剪（有关工作室摆动的解释，请参见 color_range 的语义）。如果没有设置，则表示应在添加电影颗粒后对样本值应用全范围裁剪
当然，请提供您需要翻译的文本。
