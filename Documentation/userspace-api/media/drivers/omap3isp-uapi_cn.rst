SPDX许可证标识符: GPL-2.0

包含: <isonum.txt>

OMAP 3 图像信号处理器（ISP）驱动程序
==========================================

版权所有 |copy| 2010 诺基亚公司

版权所有 |copy| 2009 德州仪器公司
联系人: Laurent Pinchart <laurent.pinchart@ideasonboard.com>，
Sakari Ailus <sakari.ailus@iki.fi>，David Cohen <dacohen@gmail.com>

事件
------

OMAP 3 ISP 驱动程序支持 V4L2 事件接口在 CCDC 和统计子设备（AEWB、AF 和直方图）上。
CCDC 子设备在 HS_VS 中断时生成 V4L2_EVENT_FRAME_SYNC 类型的事件，用于指示帧的开始。早期版本的驱动程序使用 V4L2_EVENT_OMAP3ISP_HS_VS 来实现这一目的。该事件在 CCDC 模块接收帧的第一行数据时准确触发。可以在 CCDC 子设备上订阅此事件（当使用并行接口时，必须注意正确配置 VS 信号极性。使用串行接收器时，这是自动正确的）。

每个统计子设备都能够生成事件。每当用户空间应用程序可以使用 VIDIOC_OMAP3ISP_STAT_REQ IOCTL 解队列一个统计缓冲区时，就会生成一个事件。可用的事件包括：

- V4L2_EVENT_OMAP3ISP_AEWB
- V4L2_EVENT_OMAP3ISP_AF
- V4L2_EVENT_OMAP3ISP_HIST

这些 ioctl 的事件数据类型为 struct omap3isp_stat_event_status。如果计算统计数据时出错，则会像往常一样生成事件，但没有相关的统计数据缓冲区。此时 omap3isp_stat_event_status.buf_err 被设置为非零值。

私有 IOCTL
--------------

OMAP 3 ISP 驱动程序尽可能地支持标准的 V4L2 IOCTL 和控制。然而，ISP 提供的许多功能并不属于标准 IOCTL 的范畴——伽玛表和统计收集配置就是这样的例子。
一般来说，每个包含硬件相关功能的模块都有一个私有的 ioctl 进行配置。
支持的私有 IOCTL 包括：

- VIDIOC_OMAP3ISP_CCDC_CFG
- VIDIOC_OMAP3ISP_PRV_CFG
- VIDIOC_OMAP3ISP_AEWB_CFG
- VIDIOC_OMAP3ISP_HIST_CFG
- VIDIOC_OMAP3ISP_AF_CFG
- VIDIOC_OMAP3ISP_STAT_REQ
- VIDIOC_OMAP3ISP_STAT_EN

这些 ioctl 使用的参数结构在 include/linux/omap3isp.h 中定义。与特定 ISP 模块相关的 ISP 功能详细描述在技术参考手册（TRMs）中——请参阅文档末尾部分。
虽然可以不使用这些私有 ioctl 就使用 ISP 驱动程序，但这样无法获得最佳图像质量。如果不使用相应的私有 ioctl 进行配置，将无法使用 AEWB、AF 和直方图模块。

CCDC 和预览块 IOCTL
--------------------------

VIDIOC_OMAP3ISP_CCDC_CFG 和 VIDIOC_OMAP3ISP_PRV_CFG IOCTL 用于配置、启用和禁用 CCDC 和预览块中的功能。这两个 ioctl 控制它们所控制的块中的多个功能。VIDIOC_OMAP3ISP_CCDC_CFG ioctl 接受指向 struct omap3isp_ccdc_update_config 的指针作为参数。同样，VIDIOC_OMAP3ISP_PRV_CFG ioctl 接受指向 struct omap3isp_prev_update_config 的指针。这两个结构的定义可在 [#]_ 中找到。
结构中的 update 字段告诉是否更新特定功能的配置，而 flag 告诉是否启用或禁用该功能。
更新和标志位掩码接受以下值。CCDC 和预览模块中的每个单独功能都与一个标志（禁用或启用；结构中标志字段的一部分）和指向该功能配置数据的指针相关联。
对于 `VIDIOC_OMAP3ISP_CCDC_CFG`，更新和标志字段的有效值如下所示。这些值可以进行或运算，以便在同一个 IOCTL 调用中配置多个功能：
- OMAP3ISP_CCDC_ALAW
- OMAP3ISP_CCDC_LPF
- OMAP3ISP_CCDC_BLCLAMP
- OMAP3ISP_CCDC_BCOMP
- OMAP3ISP_CCDC_FPC
- OMAP3ISP_CCDC_CULL
- OMAP3ISP_CCDC_CONFIG_LSC
- OMAP3ISP_CCDC_TBL_LSC

对于 `VIDIOC_OMAP3ISP_PRV_CFG` 的相应值如下：
- OMAP3ISP_PREV_LUMAENH
- OMAP3ISP_PREV_INVALAW
- OMAP3ISP_PREV_HRZ_MED
- OMAP3ISP_PREV_CFA
- OMAP3ISP_PREV_CHROMA_SUPP
- OMAP3ISP_PREV_WB
- OMAP3ISP_PREV_BLKADJ
- OMAP3ISP_PREV_RGB2RGB
- OMAP3ISP_PREV_COLOR_CONV
- OMAP3ISP_PREV_YC_LIMIT
- OMAP3ISP_PREV_DEFECT_COR
- OMAP3ISP_PREV_GAMMABYPASS
- OMAP3ISP_PREV_DRK_FRM_CAPTURE
- OMAP3ISP_PREV_DRK_FRM_SUBTRACT
- OMAP3ISP_PREV_LENS_SHADING
- OMAP3ISP_PREV_NF
- OMAP3ISP_PREV_GAMMA

当启用某个功能时，其关联的配置指针不得为 NULL。当禁用某个功能时，配置指针将被忽略。

统计模块 IOCTLs
-----------------------

统计子设备提供的动态配置选项比其他子设备更多。它们可以在流水线处于流式传输状态时被启用、禁用和重新配置。
统计模块始终从 CCDC 获取输入图像数据（因为直方图内存读取尚未实现）。用户可以通过私有 IOCTL 从统计子设备节点中获取统计数据。
AEWB、AF 和直方图子设备提供的私有 IOCTL 与 ISP 硬件提供的寄存器级接口密切相关。以下内容主要涉及驱动程序实现的方面。

`VIDIOC_OMAP3ISP_STAT_EN`
-----------------------

这个私有 IOCTL 用于启用或禁用一个统计模块。如果此请求在开始流式传输之前发出，则会在流水线开始流式传输时生效。如果流水线已经在流式传输，则会在 CCDC 变为空闲时生效。

`VIDIOC_OMAP3ISP_AEWB_CFG`, `VIDIOC_OMAP3ISP_HIST_CFG` 和 `VIDIOC_OMAP3ISP_AF_CFG`
-----------------------------------------------------------------------------

这些 IOCTL 用于配置各个模块。它们要求用户应用程序对硬件有深入了解。大多数字段的解释可以在 OMAP 的 TRM 中找到。以下两个字段是所有上述私有 IOCTL 共有的，需要进一步解释，因为它们不属于 TRM 的一部分：
`omap3isp_[h3a_af/h3a_aewb/hist]\_config.buf_size`：

模块内部处理其缓冲区。模块的数据输出所需的缓冲区大小取决于请求的配置。尽管驱动程序支持在流式传输过程中进行重新配置，但不支持在启用模块时进行需要更大缓冲区大小的重新配置。在这种情况下，它会返回 `-EBUSY`。为了避免这种情况，要么先禁用/重新配置/再启用模块，要么在模块首次配置时请求必要的缓冲区大小，此时模块处于禁用状态。
内部缓冲区大小分配考虑了请求配置的最小缓冲区大小和 `buf_size` 字段设置的值。如果 `buf_size` 字段超出 `[最小值, 最大值]` 缓冲区大小范围，则将其调整到该范围内。
驾驶员然后选择最大的值。修正后的 `buf_size` 值被写回到用户应用程序中：
`omap3isp_[h3a_af/h3a_aewb/hist]_config.config_counter`：

由于配置不是与请求同步生效的，因此驱动程序必须提供一种跟踪此信息的方法，以便提供更准确的数据。在请求配置后，返回到用户空间应用程序的 `config_counter` 将是一个与该请求关联的独特值。当用户应用程序接收到缓冲区可用事件或请求新缓冲区时，使用此 `config_counter` 来匹配缓冲区数据和配置。
`VIDIOC_OMAP3ISP_STAT_REQ`
------------------------

将内部缓冲队列中最旧的数据发送到用户空间，并在此之后丢弃该缓冲区。字段 `omap3isp_stat_data.frame_number` 与视频缓冲区的 `field_count` 字段相匹配。
参考文献
----------

.. [#] include/linux/omap3isp.h
